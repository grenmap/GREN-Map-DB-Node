"""
Copyright 2023 GRENMap Authors

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
    MatchType, MatchCriterion, MatchInfo, ActionInfo,
    ActionType, Action,
)

MATCH_INSTITUTION_BY_ID_CLASS_NAME = 'MatchInstitutionsByID'
DELETE_INSTITUTION_TAG_PROPERTY_CLASS_NAME = 'DeleteInstitutionTagProperty'
DELETE_INST_TAG_PROPERTY_ACTION_TYPE_NAME = 'Delete Institution Tag Property'


@pytest.mark.django_db
class TestDeleteInstitutionTagProperty:

    @pytest.fixture
    def load_match_and_action_types(self):
        synchronize_match_and_action_type_tables(None)

    @pytest.fixture
    def two_nodes_and_links(self):
        """
        Populates the database with a few GRENML records for testing:
            - one institution,
            - two nodes,
            - two links, and
            - one property of type 'tag' in the institution
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

        institution.property('tag', value='Test')

    @pytest.fixture
    def institution_with_ten_properties_five_same_name(self):
        """
        Populates the database with a few GRENML records for testing:
            - one institution,
            - ten properties of type 'tag' in the institution,
              five of which have the same name
        """
        institution = grenml.Institution.objects.create(
            grenml_id='institution-id',
            name='TestREN',
            latitude=10,
            longitude=10,
        )

        grenml.Property.objects.create(
            name='tag',
            value='Value_1',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='tag',
            value='Value_2',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='tag',
            value='Value_3',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='tag',
            value='Value_4',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='tag',
            value='Value_5',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='institutionproperty_6',
            value='Value_6',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='institutionproperty_7',
            value='Value_7',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='institutionproperty_8',
            value='Value_8',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='institutionproperty_9',
            value='Value_9',
            property_for=institution,
        )

        grenml.Property.objects.create(
            name='institutionproperty_10',
            value='Value_10',
            property_for=institution,
        )

    @pytest.fixture
    def simple_rule(self):
        """
        Adds a sample rule infrastructure:
            - one Ruleset, and
            - one Rule.
        The Rule has no matches or actions; these get added by tests.
        """
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
        delete_institution_tag_prop_action_type = ActionType.objects.get(
            class_name=DELETE_INSTITUTION_TAG_PROPERTY_CLASS_NAME,
        )
        delete_inst_tag_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_institution_tag_prop_action_type,
        )
        assert (
            delete_inst_tag_prop_action.action_type.name
            == DELETE_INST_TAG_PROPERTY_ACTION_TYPE_NAME
        )

    def test_affected_element_counts(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the action value has only lowercase letters.
        """
        inst_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_INSTITUTION_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=inst_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value='institution-id',
        )

        delete_institution_tag_prop_action_type = ActionType.objects.get(
            class_name=DELETE_INSTITUTION_TAG_PROPERTY_CLASS_NAME,
        )

        delete_institution_tag_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_institution_tag_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_institution_tag_prop_action,
            key='value',
            value='Test'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

    def test_same_names(
        self,
        load_match_and_action_types,
        institution_with_ten_properties_five_same_name,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the name and value of the property is provided.
        """
        target_inst_id = 'institution-id'

        inst_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_INSTITUTION_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=inst_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_inst_id,
        )

        delete_institution_tag_prop_action_type = ActionType.objects.get(
            class_name=DELETE_INSTITUTION_TAG_PROPERTY_CLASS_NAME,
        )

        delete_institution_tag_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_institution_tag_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_institution_tag_prop_action,
            key='value',
            value='Value_2'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Valid that target property was deleted
        target_inst = grenml.Institution.objects.all().filter(grenml_id=target_inst_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_inst, name='tag', value='Value_2')

        assert target_property.exists() is False

        # Valid that no other properties have been deleted
        other_properties = grenml.Property.objects.all().filter(
            property_for=target_inst)

        assert len(other_properties) == 9

    def test_no_corresponding_property(
        self,
        load_match_and_action_types,
        institution_with_ten_properties_five_same_name,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when there is no matching property that was fetched.
        """
        target_inst_id = 'institution-id'

        inst_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_INSTITUTION_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=inst_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_inst_id,
        )

        delete_institution_tag_prop_action_type = ActionType.objects.get(
            class_name=DELETE_INSTITUTION_TAG_PROPERTY_CLASS_NAME,
        )

        delete_institution_tag_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_institution_tag_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_institution_tag_prop_action,
            key='value',
            value='nonexistent_value'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Validates that no properties were detected
        target_inst = grenml.Institution.objects.all().filter(
            grenml_id=target_inst_id)[0]

        all_properties = grenml.Property.objects.all().filter(
            property_for=target_inst)

        assert len(all_properties) == 10
