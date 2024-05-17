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
    MatchType, MatchCriterion,
)


MATCH_DUPLICATE_NODES_CLASS_NAME = 'MatchNodesByIDDuplicate'
# DUPLICATE_NODES_MATCH_TYPE_NAME = 'Match Duplicate Nodes'
MATCH_DUPLICATE_LINKS_CLASS_NAME = 'MatchLinksByIDDuplicate'
# DUPLICATE_LINKS_MATCH_TYPE_NAME = 'Match Duplicate Links'
MATCH_DUPLICATE_INSTS_CLASS_NAME = 'MatchInstitutionsByIDDuplicate'
# DUPLICATE_INSTS_MATCH_TYPE_NAME = 'Match Duplicate Institutions'


@pytest.mark.django_db
class TestMatchByID:
    """
    Tests for all of the by-duplicate-ID MatchTypes.
    """
    @pytest.fixture
    def load_match_and_action_types(self):
        synchronize_match_and_action_type_tables(None)

    @pytest.fixture
    def simple_topology(self):
        """
        Populates the database with a few GRENML records for testing:
            - one topology,
            - one institution,
            - two nodes, and
            - two links.
        """
        topology = grenml.Topology.objects.create(
            grenml_id='topology1-id',
            name='Topology 1',
            parent=None,
        )

        institution = grenml.Institution.objects.create(
            grenml_id='institution1-id',
            name='TestREN',
            latitude=10,
            longitude=10,
        )
        institution.topologies.add(topology)

        node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )
        node1.topologies.add(topology)
        node1.owners.add(institution)

        node2 = grenml.Node.objects.create(
            grenml_id='node2-id',
            name='TestNode2',
            latitude=30,
            longitude=30,
        )
        node2.topologies.add(topology)
        node2.owners.add(institution)

        link1 = grenml.Link.objects.create(
            grenml_id='link1-id',
            name='TestLink1',
            node_a=node1,
            node_b=node2,
        )
        link1.topologies.add(topology)
        link1.owners.add(institution)

        link2 = grenml.Link.objects.create(
            grenml_id='link2-id',
            name='TestLink2',
            node_a=node1,
            node_b=node2,
        )
        link2.topologies.add(topology)
        link2.owners.add(institution)

        return topology

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

    def test_duplicate_nodes_by_id_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Confirm there are two Nodes to start the test
        assert grenml.Node.objects.count() == 2

        # Add a duplicate Node in the same topology
        duplicate_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='DuplicateTestNode1',
            latitude=40,
            longitude=40,
        )
        duplicate_node1.topologies.add(simple_topology)

        # Set up the supporting Rule element DB entries
        match_node_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_NODES_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_node_by_duplicate_id_type,
        )
        klass = match_node_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Node.objects.all())

        # After filtration, it should identify both node1-id Nodes.
        assert elements_query.count() == 2
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['node1-id'])

    def test_multiple_duplicate_nodes_by_id_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Confirm there are two Nodes to start the test
        assert grenml.Node.objects.count() == 2

        # Add two duplicate Nodes in the same topology
        duplicate_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='DuplicateTestNode1',
            latitude=40,
            longitude=40,
        )
        duplicate_node1.topologies.add(simple_topology)
        duplicate_node1_again = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='AnotherDuplicateTestNode1',
            latitude=50,
            longitude=50,
        )
        duplicate_node1_again.topologies.add(simple_topology)

        # Set up the supporting Rule element DB entries
        match_node_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_NODES_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_node_by_duplicate_id_type,
        )
        klass = match_node_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Node.objects.all())

        # After filtration, it should identify both node1-id Nodes.
        assert elements_query.count() == 3
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['node1-id'])

    def test_multiple_sets_of_duplicate_nodes_by_id_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Confirm there are two Nodes to start the test
        assert grenml.Node.objects.count() == 2

        # Add two sets of duplicate Nodes in the same topology
        duplicate_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='DuplicateTestNode1',
            latitude=40,
            longitude=40,
        )
        duplicate_node1.topologies.add(simple_topology)
        duplicate_node2 = grenml.Node.objects.create(
            grenml_id='node2-id',
            name='DuplicateTestNode2',
            latitude=50,
            longitude=50,
        )
        duplicate_node2.topologies.add(simple_topology)

        # Set up the supporting Rule element DB entries
        match_node_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_NODES_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_node_by_duplicate_id_type,
        )
        klass = match_node_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Node.objects.all())

        # After filtration, it should identify both node1-id Nodes.
        assert elements_query.count() == 4
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['node1-id', 'node2-id'])

    def test_duplicate_nodes_by_id_across_related_topologies_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Create another Topology
        child_topology = grenml.Topology.objects.create(
            grenml_id='topology2-id',
            name='Child Topology',
            parent=simple_topology,
        )

        # Add a duplicate Node in the new Topology
        duplicate_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='DuplicateTestNode1',
            latitude=40,
            longitude=40,
        )
        duplicate_node1.topologies.add(child_topology)

        # Set up the supporting Rule element DB entries
        match_node_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_NODES_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_node_by_duplicate_id_type,
        )
        klass = match_node_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Node.objects.all())

        # After filtration, it should identify both node1-id Nodes.
        assert elements_query.count() == 2
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['node1-id'])

    def test_duplicate_nodes_by_id_across_unrelated_topologies_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Create another Topology
        unrelated_topology = grenml.Topology.objects.create(
            grenml_id='topology2-id',
            name='Topology 2',
            parent=None,
        )

        # Add a duplicate Node in the new Topology
        duplicate_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='DuplicateTestNode1',
            latitude=40,
            longitude=40,
        )
        duplicate_node1.topologies.add(unrelated_topology)

        # Set up the supporting Rule element DB entries
        match_node_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_NODES_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_node_by_duplicate_id_type,
        )
        klass = match_node_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Node.objects.all())

        # After filtration, it should identify both node1-id Nodes.
        assert elements_query.count() == 2
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['node1-id'])

    def test_duplicate_links_by_id_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Confirm there are two Links to start the test
        assert grenml.Link.objects.count() == 2

        # Add a duplicate Link in the same topology
        node1 = simple_topology.nodes.first()
        node2 = simple_topology.nodes.last()
        duplicate_link1 = grenml.Link.objects.create(
            grenml_id='link1-id',
            name='TestLink1',
            node_a=node1,
            node_b=node2,
        )
        duplicate_link1.topologies.add(simple_topology)

        # Set up the supporting Rule element DB entries
        match_link_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_LINKS_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_link_by_duplicate_id_type,
        )
        klass = match_link_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Link.objects.all())

        # After filtration, it should identify both link1-id Links.
        assert elements_query.count() == 2
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['link1-id'])

    def test_duplicate_insts_by_id_filter_method(
        self,
        load_match_and_action_types,
        simple_topology,
        simple_rule,
    ):
        # Confirm there is one Institution to start the test
        assert grenml.Institution.objects.count() == 1

        # Add a duplicate Institution in the same topology
        duplicate_inst1 = grenml.Institution.objects.create(
            grenml_id='institution1-id',
            name='DuplicateTestInst1',
            latitude=40,
            longitude=40,
        )
        duplicate_inst1.topologies.add(simple_topology)

        # Set up the supporting Rule element DB entries
        match_inst_by_duplicate_id_type = MatchType.objects.get(
            class_name=MATCH_DUPLICATE_INSTS_CLASS_NAME,
        )
        match_criterion = MatchCriterion.objects.create(
            rule=simple_rule,
            match_type=match_inst_by_duplicate_id_type,
        )
        klass = match_inst_by_duplicate_id_type.get_class_instance(match_criterion)

        # Apply the filter method to be tested here
        elements_query = klass.filter(grenml.Institution.objects.all())

        # After filtration, it should identify both inst1-id Insts.
        assert elements_query.count() == 2
        elements_query_grenml_ids = [e.grenml_id for e in elements_query]
        assert set(elements_query_grenml_ids) == set(['institution1-id'])
