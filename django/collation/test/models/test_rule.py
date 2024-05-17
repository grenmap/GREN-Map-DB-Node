"""
Copyright 2022 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import pytest

import network_topology.models as grenml
import collation.exceptions as exc
import collation.models as collation
from collation.utils.synchronize_models import synchronize_match_and_action_type_tables


MATCH_LINK_BY_ID_CLASS_NAME = 'MatchLinksByID'
LINK_BY_ID_MATCH_TYPE_NAME = 'Match Single Link by ID'
DELETE_LINK_CLASS_NAME = 'DeleteLink'


@pytest.fixture
def load_action_types():
    synchronize_match_and_action_type_tables(None)


@pytest.fixture
def sparse_grenml():
    """
    Populates the database with a few GRENML records for testing:
    one institution, two nodes and two links.
    """
    institution = grenml.Institution()
    institution.name = 'TestREN'
    institution.latitude = 10
    institution.longitude = 10
    institution.id = 'institution-id'
    institution.save()

    node1 = grenml.Node()
    node1.name = 'TestNode1'
    node1.latitude = 20
    node1.longitude = 20
    node1.id = 'node1-id'
    node1.save()
    node1.owners.add(institution)

    node2 = grenml.Node()
    node2.name = 'TestNode2'
    node2.latitude = 30
    node2.longitude = 30
    node2.id = 'node2-id'
    node2.save()
    node2.owners.add(institution)

    link1 = grenml.Link()
    link1.name = 'TestLink1'
    link1.id = 'link1-id'
    link1.save()
    link1.node_a = node1
    link1.node_b = node2
    link1.save()
    link1.owners.add(institution)

    link2 = grenml.Link()
    link2.name = 'TestLink2'
    link2.id = 'link2-id'
    link2.save()
    link2.node_a = node1
    link2.node_b = node2
    link2.save()
    link2.owners.add(institution)

    return [institution, node1, node2, link1, link2]


@pytest.fixture
def delete_link_by_id_rule():
    """
    Creates a Rule that matches a Link by ID and deletes it.
    The ID field in the MatchInfo is left as a placeholder for now.
    """
    ruleset = collation.Ruleset.objects.create(name='Ruleset')
    rule = collation.Rule.objects.create(name='Rule', ruleset=ruleset)
    match_link_by_id = collation.MatchType.objects.get(class_name=MATCH_LINK_BY_ID_CLASS_NAME)
    criterion = collation.MatchCriterion.objects.create(rule=rule, match_type=match_link_by_id)
    collation.MatchInfo.objects.create(match_criterion=criterion, key='ID', value='id')
    delete_link = collation.ActionType.objects.get(class_name=DELETE_LINK_CLASS_NAME)
    collation.Action.objects.create(rule=rule, action_type=delete_link)
    return rule


@pytest.mark.django_db
class TestApply:
    """ This class contains tests for the Rule.apply method. """

    def test_rule_without_match_criteria(self, delete_link_by_id_rule):
        """
        Verifies that it is not possible to apply a Rule
        that doesn't have MatchCriteria.
        """
        delete_link_by_id_rule.match_criteria.all().delete()
        with pytest.raises(exc.NoMatchCriteriaError):
            delete_link_by_id_rule.apply()

    def test_rule_without_actions(self, delete_link_by_id_rule):
        """
        Verifies that it is not possible to apply a Rule
        that doesn't have Actions.
        """
        delete_link_by_id_rule.actions.all().delete()
        with pytest.raises(exc.NoActionsError):
            delete_link_by_id_rule.apply()

    def test_rule_without_value(self, delete_link_by_id_rule):
        """
        Checks that it is not possible to run the delete-link-by-id rule
        without a link id.
        """
        delete_link_by_id_rule.match_criteria.first().matchinfo_set.all().delete()
        with pytest.raises(exc.IncorrectMatchInfosValidationError):
            delete_link_by_id_rule.apply()

    def test_rule_matching_unknown_field(self, delete_link_by_id_rule):
        """
        A Rule should fail if it has a MatchCriterion bound to Links,
        with a MatchInfo record that doesn't refer to an existing
        Link field.
        """
        match_info = delete_link_by_id_rule.match_criteria.first().matchinfo_set.first()
        match_info.key = 'not-a-field'
        match_info.save()
        with pytest.raises(exc.IncorrectMatchInfosValidationError):
            delete_link_by_id_rule.apply()

    def test_rule_with_unsupported_action(self, delete_link_by_id_rule):
        """
        It should not be possible to apply a rule containing an action
        that is not supported.
        """
        action = delete_link_by_id_rule.actions.get()
        action.action_type.class_name = 'unsupported-action'
        action.action_type.save()
        with pytest.raises(exc.UnsupportedActionTypeError):
            delete_link_by_id_rule.apply()


@pytest.mark.django_db
class TestClone():
    """ Tests for the Rule.clone method. """

    def test_related_entities_copied(self, load_action_types):
        """
        Verifies that a rule's clone is associated to copies
        of the original instance's related entities.
        """
        ruleset = collation.Ruleset.objects.create(
            name='Test Ruleset',
        )
        rule = collation.Rule.objects.create(
            name='Test Rule',
            ruleset=ruleset,
        )
        delete_link_action_type = collation.ActionType.objects.get(
            class_name=DELETE_LINK_CLASS_NAME,
        )
        collation.Action.objects.create(
            rule=rule,
            action_type=delete_link_action_type,
        )
        assert collation.Rule.objects.filter(
            name__startswith='Test Rule',
        ).count() == 1
        # TODO #88 create MatchCriterion and MatchInfo

        rule.clone()

        assert collation.Rule.objects.filter(
            name__startswith='Test Rule',
        ).count() == 2
        # TODO #88 create MatchCriterion and MatchInfo
        assert collation.Action.objects.filter(
            action_type__name=delete_link_action_type,
        ).count() == 2
