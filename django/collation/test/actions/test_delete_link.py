"""
Copyright 2021 GRENMap Authors

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
from collation.utils.synchronize_models import synchronize_match_and_action_type_tables
from collation.models import (
    Ruleset, Rule,
    MatchType, MatchCriterion, MatchInfo,
    ActionType, Action,
)


MATCH_LINK_BY_ID_CLASS_NAME = 'MatchLinksByID'
DELETE_LINK_CLASS_NAME = 'DeleteLink'
DELETE_LINK_ACTION_TYPE_NAME = 'Delete Link'


@pytest.mark.django_db()
class TestDeleteLink:
    """
    This class contains tests for the Delete Link action.
    Relies on the MatchType specified in MATCH_LINK_BY_ID_CLASS_NAME.
    """
    @pytest.fixture
    def load_match_and_action_types(self):
        synchronize_match_and_action_type_tables(None)

    @pytest.fixture
    def two_nodes_and_links(self):
        """
        Populates the database with a few GRENML records for testing:
            - one institution,
            - two nodes, and
            - two links.
        Also adds a sample rule infrastructure:
            - one Ruleset, and
            - one Rule.
        The Rule has no matches or actions; these get added by tests.
        """
        institution = grenml.Institution.objects.create(
            grenml_id='institution-id',
            name='TestREN',
            latitude=10,
            longitude=10,
        )

        node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )
        node1.owners.add(institution)

        node2 = grenml.Node.objects.create(
            grenml_id='node2-id',
            name='TestNode2',
            latitude=30,
            longitude=30,
        )
        node2.owners.add(institution)

        link1 = grenml.Link.objects.create(
            grenml_id='link1-id',
            name='TestLink1',
            node_a=node1,
            node_b=node2,
        )
        link1.owners.add(institution)

        link2 = grenml.Link.objects.create(
            grenml_id='link2-id',
            name='TestLink2',
            node_a=node1,
            node_b=node2,
        )
        link2.owners.add(institution)

    @pytest.fixture
    def simple_rule(self):
        ruleset = Ruleset.objects.create(
            name='Test Ruleset',
        )
        rule = Rule.objects.create(
            name='Test Rule',
            ruleset=ruleset,
        )
        return rule

    def test_build_rule(self, load_match_and_action_types, two_nodes_and_links, simple_rule):
        """
        Simply builds up the Rule with an ActionType
        to confirm it's possible and correct.
        """
        delete_link_action_type = ActionType.objects.get(class_name=DELETE_LINK_CLASS_NAME)
        delete_link_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_link_action_type,
        )
        assert delete_link_action.action_type.name == DELETE_LINK_ACTION_TYPE_NAME

    @pytest.mark.skip(reason='Currently no MatchType to match all elements of a particular type.')
    def test_delete_all_links(self, load_match_and_action_types, two_nodes_and_links, simple_rule):
        """
        Sets up a topology in which two Nodes are connected
        by two Links, applies the Rule with the DeleteLink Action,
        then verifies that the database has no Links left.
        """
        # Confirm there are two Links to start the test
        links = grenml.Link.objects.all()
        assert len(links) == 2

        delete_link_action_type = ActionType.objects.get(class_name=DELETE_LINK_CLASS_NAME)
        Action.objects.create(
            rule=simple_rule,
            action_type=delete_link_action_type,
        )
        simple_rule.apply()

        # Before calling apply, there were two Links.
        # There should be no links now.
        links = grenml.Link.objects.all()
        assert len(links) == 0

        # Before calling apply, there were two Nodes.
        # There should still be two Nodes.
        nodes = grenml.Node.objects.all()
        assert len(nodes) == 2

        # Before calling apply, there was one Institution.
        # There should still be one Institution.
        institutions = grenml.Institution.objects.all()
        assert len(institutions) == 1

    def test_affected_element_counts(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule,
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements.
        """
        link_by_id_match_type = MatchType.objects.get(class_name=MATCH_LINK_BY_ID_CLASS_NAME)
        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=link_by_id_match_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value='link2-id',
        )
        delete_link_action_type = ActionType.objects.get(class_name=DELETE_LINK_CLASS_NAME)
        Action.objects.create(
            rule=simple_rule,
            action_type=delete_link_action_type,
        )
        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
