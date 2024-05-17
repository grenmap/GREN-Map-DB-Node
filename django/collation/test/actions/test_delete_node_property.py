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

MATCH_NODE_BY_ID_CLASS_NAME = 'MatchNodesByID'
DELETE_NODE_PROPERTY_CLASS_NAME = 'DeleteNodeProperty'
DELETE_NODE_PROPERTY_ACTION_TYPE_NAME = 'Delete Node Property'


@pytest.mark.django_db
class TestDeleteNodeProperty:

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
            - one property in the node
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

        node1.property('nodeproperty', value='Test')

    @pytest.fixture
    def property_name_with_capital_letters(self):
        """
        Populates the database with a few GRENML records for testing:
            - one node,
            - one property in the node
              (The property name has capital letters)
        """
        node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )

        node1.property('NodePropertyUPPERCASE', value='Test')

    @pytest.fixture
    def node_with_three_properties(self):
        """
        Populates the database with a few GRENML records for testing:
            - one node,
            - three property in the node
        """
        node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )

        node1.property('nodeproperty_1', value='Value_1')
        node1.property('nodeproperty_2', value='Value_2')
        node1.property('nodeproperty_3', value='Value_3')

    @pytest.fixture
    def node_with_ten_properties_five_same_name(self):
        """
        Populates the database with a few GRENML records for testing:
            - one node,
            - ten properties in the node,
            five of which have the same name
        """
        node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )

        grenml.Property.objects.create(
            name='nodeproperty_same_name',
            value='Value_1',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_same_name',
            value='Value_2',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_same_name',
            value='Value_3',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_same_name',
            value='Value_4',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_same_name',
            value='Value_5',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_6',
            value='Value_6',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_7',
            value='Value_7',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_8',
            value='Value_8',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_9',
            value='Value_9',
            property_for=node1,
        )

        grenml.Property.objects.create(
            name='nodeproperty_10',
            value='Value_10',
            property_for=node1,
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
        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )
        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type,
        )
        assert delete_node_prop_action.action_type.name == DELETE_NODE_PROPERTY_ACTION_TYPE_NAME

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
        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value='node1-id',
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='nodeproperty'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

    def test_action_value_with_uppercase_letters(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the action value has uppercase letters.
        """
        target_node_id = 'node1-id'

        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_node_id,
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='NodeProperty'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Valid that target property was deleted
        target_node = grenml.Node.objects.all().filter(grenml_id=target_node_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_node, name='nodeproperty', value='Test')

        assert target_property.exists() is False

    def test_property_name_with_uppercase_letters(
        self,
        load_match_and_action_types,
        property_name_with_capital_letters,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the property name has uppercase letters.
        """
        target_node_id = 'node1-id'

        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_node_id,
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='NodePropertyUPPERCASE'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Valid that target property was deleted
        target_node = grenml.Node.objects.all().filter(grenml_id=target_node_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_node, name='NodePropertyUPPERCASE', value='Test')

        assert target_property.exists() is False

    def test_name_value_as_criteria(
        self,
        load_match_and_action_types,
        node_with_three_properties,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the name and value of the property is provided.
        """
        target_node_id = 'node1-id'

        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_node_id,
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='nodeproperty_2'
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='value',
            value='Value_2'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Valid that target property was deleted
        target_node = grenml.Node.objects.all().filter(grenml_id=target_node_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_node, name='nodeproperty_2', value='Value_2')

        assert target_property.exists() is False

        # Valid that no other properties have been deleted
        other_properties = grenml.Property.objects.all().filter(
            property_for=target_node)

        assert len(other_properties) == 2

    def test_name_value_as_criteria_same_names(
        self,
        load_match_and_action_types,
        node_with_ten_properties_five_same_name,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the name and value of the property is provided.
        """
        target_node_id = 'node1-id'

        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_node_id,
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='nodeproperty_same_name'
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='value',
            value='Value_2'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Valid that target property was deleted
        target_node = grenml.Node.objects.all().filter(grenml_id=target_node_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_node, name='nodeproperty_same_name', value='Value_2')

        assert target_property.exists() is False

        # Valid that no other properties have been deleted
        other_properties = grenml.Property.objects.all().filter(
            property_for=target_node)

        assert len(other_properties) == 9

    def test_same_names(
        self,
        load_match_and_action_types,
        node_with_ten_properties_five_same_name,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when the name and value of the property is provided.
        """
        target_node_id = 'node1-id'

        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_node_id,
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='nodeproperty_same_name'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 1
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0

        # Valid that target property was deleted
        target_node = grenml.Node.objects.all().filter(grenml_id=target_node_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_node, name='nodeproperty_same_name')

        assert target_property.exists() is False

        # Valid that no other properties have been deleted
        other_properties = grenml.Property.objects.all().filter(
            property_for=target_node)

        assert len(other_properties) == 5

    def test_no_corresponding_property(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule
    ):
        """
        Confirm the apply method returns the correct count for affected
        elements when there is no matching property that was fetched.
        """
        target_node_id = 'node1-id'

        node_by_id_match_type = MatchType.objects.get(
            class_name=MATCH_NODE_BY_ID_CLASS_NAME,
        )

        match_by_id = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_by_id_match_type,
        )

        MatchInfo.objects.create(
            match_criterion=match_by_id,
            key='ID',
            value=target_node_id,
        )

        delete_node_prop_action_type = ActionType.objects.get(
            class_name=DELETE_NODE_PROPERTY_CLASS_NAME,
        )

        delete_node_prop_action = Action.objects.create(
            rule=simple_rule,
            action_type=delete_node_prop_action_type
        )

        ActionInfo.objects.create(
            action=delete_node_prop_action,
            key='name',
            value='nonexistent_name'
        )

        rule_log = simple_rule.apply()

        assert len(rule_log.action_logs[0].affected_nodes_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_links_primary_keys) == 0
        assert len(rule_log.action_logs[0].affected_institutions_primary_keys) == 0

        # Valid that no properties were deleted
        target_node = grenml.Node.objects.all().filter(grenml_id=target_node_id)[0]

        target_property = grenml.Property.objects.all().filter(
            property_for=target_node, name='nodeproperty', value='Test')

        assert target_property.exists() is True
