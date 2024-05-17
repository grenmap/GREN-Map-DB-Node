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
from collation.utils.synchronize_models import synchronize_match_and_action_type_tables
from collation.models import (
    Ruleset, Rule,
    MatchType, MatchCriterion, MatchInfo,
)


MATCH_NODE_BY_ID_CLASS_NAME = 'MatchNodesByID'
NODE_BY_ID_MATCH_TYPE_NAME = 'Match Nodes by ID'
MATCH_LINK_BY_ID_CLASS_NAME = 'MatchLinksByID'
LINK_BY_ID_MATCH_TYPE_NAME = 'Match Links by ID'
MATCH_INST_BY_ID_CLASS_NAME = 'MatchInstitutionsByID'
INST_BY_ID_MATCH_TYPE_NAME = 'Match Institutions by ID'


@pytest.mark.django_db
class TestMatchByID:
    """
    This class contains tests for all of the by-ID MatchTypes.
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

    def test_build_match_node_rule_element(self, load_match_and_action_types, simple_rule):
        """
        Simply builds up the Rule with a MatchType
        to confirm it's possible and correct.
        """
        node_match_type = MatchType.objects.get(class_name=MATCH_NODE_BY_ID_CLASS_NAME)
        node_match = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=node_match_type
        )
        assert node_match.match_type.name == NODE_BY_ID_MATCH_TYPE_NAME

    def test_node_by_id_filter_method(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule,
    ):
        """
        Unit test the actual MatchType class's filter method.
        """
        # Confirm there are two Nodes to start the test
        assert grenml.Node.objects.count() == 2

        # Set up the supporting Rule element DB entries
        match_node_by_id_type = MatchType.objects.get(class_name=MATCH_NODE_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_node_by_id_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='ID',
            value='node1-id',
        )
        match_node_by_id_klass = match_node_by_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = match_node_by_id_klass.filter(grenml.Node.objects.all())

        # After filtration, only the single identified Node
        # should remain.
        assert elements_query.count() == 1

    def test_build_match_link_rule_element(self, load_match_and_action_types, simple_rule):
        """
        Simply builds up the Rule with a MatchType
        to confirm it's possible and correct.
        """
        link_match_type = MatchType.objects.get(class_name=MATCH_LINK_BY_ID_CLASS_NAME)
        link_match = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=link_match_type
        )
        assert link_match.match_type.name == LINK_BY_ID_MATCH_TYPE_NAME

    def test_link_by_id_filter_method(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule,
    ):
        """
        Unit test the actual MatchType class's filter method.
        """
        # Confirm there are two Links to start the test
        assert grenml.Link.objects.count() == 2

        # Set up the supporting Rule element DB entries
        match_link_by_id_type = MatchType.objects.get(class_name=MATCH_LINK_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_link_by_id_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='ID',
            value='link1-id',
        )
        match_link_by_id_klass = match_link_by_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = match_link_by_id_klass.filter(grenml.Link.objects.all())

        # After filtration, only the single identified Link
        # should remain.
        assert elements_query.count() == 1

    def test_build_match_inst_rule_element(self, load_match_and_action_types, simple_rule):
        """
        Simply builds up the Rule with a MatchType
        to confirm it's possible and correct.
        """
        inst_match_type = MatchType.objects.get(class_name=MATCH_INST_BY_ID_CLASS_NAME)
        inst_match = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=inst_match_type
        )
        assert inst_match.match_type.name == INST_BY_ID_MATCH_TYPE_NAME

    def test_inst_by_id_input_validation(
        self,
        load_match_and_action_types,
        simple_rule,
    ):
        """
        Unit test the validation of a properly-configured Match-by-ID
        Match Criterion.
        """
        # Set up the supporting Rule element DB entries
        match_inst_by_id_type = MatchType.objects.get(class_name=MATCH_INST_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_inst_by_id_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='ID',
            value='institution-id',
        )
        match_inst_by_id_klass = match_inst_by_id_type.get_class_instance(match_criterion)

        # This Match Criterion is properly configured
        assert match_inst_by_id_klass.validate_input(match_criterion.info_tuples)

    def test_inst_by_id_input_validation_missing_key(
        self,
        load_match_and_action_types,
        simple_rule,
    ):
        """
        Unit test the validation of a Match-by-ID Match Criterion
        missing the required ID info.
        """
        # Set up the supporting Rule element DB entries
        match_inst_by_id_type = MatchType.objects.get(class_name=MATCH_INST_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_inst_by_id_type,
        )
        match_inst_by_id_klass = match_inst_by_id_type.get_class_instance(match_criterion)

        assert not match_inst_by_id_klass.validate_input(match_criterion.info_tuples)

    def test_inst_by_id_input_validation_incorrect_key(
        self,
        load_match_and_action_types,
        simple_rule,
    ):
        """
        Unit test the validation of a Match-by-ID Match Criterion
        missing the required ID info (case mismatch).
        """
        # Set up the supporting Rule element DB entries
        match_inst_by_id_type = MatchType.objects.get(class_name=MATCH_INST_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_inst_by_id_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='id',
            value='institution-id',
        )
        match_inst_by_id_klass = match_inst_by_id_type.get_class_instance(match_criterion)

        assert not match_inst_by_id_klass.validate_input(match_criterion.info_tuples)

    def test_inst_by_id_input_validation_duplicate_key(
        self,
        load_match_and_action_types,
        simple_rule,
    ):
        """
        Unit test the validation of a Match-by-ID Match Criterion
        with duplicate ID info keys.
        """
        # Set up the supporting Rule element DB entries
        match_inst_by_id_type = MatchType.objects.get(class_name=MATCH_INST_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_inst_by_id_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='ID',
            value='institution-id',
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='ID',
            value='another-id',
        )
        match_inst_by_id_klass = match_inst_by_id_type.get_class_instance(match_criterion)

        assert not match_inst_by_id_klass.validate_input(match_criterion.info_tuples)

    def test_inst_by_id_filter_method(
        self,
        load_match_and_action_types,
        two_nodes_and_links,
        simple_rule,
    ):
        """
        Unit test the actual MatchType class's filter method.
        """
        # Create a second Institution
        grenml.Institution.objects.create(
            grenml_id='inst2-id',
            name='Second Institution',
            latitude=0,
            longitude=0,
        )
        # Confirm there are two Institutions to start the test
        assert grenml.Institution.objects.count() == 2

        # Set up the supporting Rule element DB entries
        match_inst_by_id_type = MatchType.objects.get(class_name=MATCH_INST_BY_ID_CLASS_NAME)
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_inst_by_id_type,
        )
        MatchInfo.objects.create(
            match_criterion=match_criterion,
            key='ID',
            value='institution-id',
        )
        match_inst_by_id_klass = match_inst_by_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = match_inst_by_id_klass.filter(grenml.Institution.objects.all())

        # After filtration, only the single identified Institution
        # should remain.
        assert elements_query.count() == 1
