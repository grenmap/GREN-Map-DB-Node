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
from collation.models import Ruleset, Rule


MATCH_INST_BY_TOPOLOGY_CLASS_NAME = 'MatchInstitutionsByTopology'
MATCH_NODE_BY_TOPOLOGY_CLASS_NAME = 'MatchNodesByTopology'
MATCH_LINK_BY_TOPOLOGY_CLASS_NAME = 'MatchLinksByTopology'
TOPOLOGY_ID_KEY = 'Topology ID'


@pytest.mark.django_db
class TestMatchByTopology:
    """
    This class contains tests for all of the by-Topology MatchTypes.
    """

    @pytest.fixture
    def load_match_and_action_types(self):
        synchronize_match_and_action_type_tables(None)

    @pytest.fixture
    def two_topologies(self):
        """
        Populates the database with a few GRENML records for testing:
            - two topologies (one a child of the other),
            - one institution per topology,
            - two nodes per topology, and
            - two links per topology.
        """

        # Topology 1

        topology_one = grenml.Topology.objects.create(
            grenml_id='topology-1',
            name='Topology 1',
            parent=None,
        )

        topo_one_institution = grenml.Institution.objects.create(
            grenml_id='institution-id',
            name='TestREN',
            latitude=10,
            longitude=10,
        )
        topo_one_institution.topologies.add(topology_one)

        topo_one_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )
        topo_one_node1.topologies.add(topology_one)
        topo_one_node1.owners.add(topo_one_institution)

        topo_one_node2 = grenml.Node.objects.create(
            grenml_id='node2-id',
            name='TestNode2',
            latitude=30,
            longitude=30,
        )
        topo_one_node2.topologies.add(topology_one)
        topo_one_node2.owners.add(topo_one_institution)

        topo_one_link1 = grenml.Link.objects.create(
            grenml_id='link1-id',
            name='TestLink1',
            node_a=topo_one_node1,
            node_b=topo_one_node2,
        )
        topo_one_link1.topologies.add(topology_one)
        topo_one_link1.owners.add(topo_one_institution)

        topo_one_link2 = grenml.Link.objects.create(
            grenml_id='link2-id',
            name='TestLink2',
            node_a=topo_one_node1,
            node_b=topo_one_node2,
        )
        topo_one_link2.topologies.add(topology_one)
        topo_one_link2.owners.add(topo_one_institution)

        # Topology 2

        topology_two = grenml.Topology.objects.create(
            grenml_id='topology-2',
            name='Topology 2',
            parent=topology_one,
        )

        topo_two_institution = grenml.Institution.objects.create(
            grenml_id='institution-id',
            name='TestREN',
            latitude=10,
            longitude=10,
        )
        topo_two_institution.topologies.add(topology_two)

        topo_two_node1 = grenml.Node.objects.create(
            grenml_id='node1-id',
            name='TestNode1',
            latitude=20,
            longitude=20,
        )
        topo_two_node1.topologies.add(topology_two)
        topo_two_node1.owners.add(topo_two_institution)

        topo_two_node2 = grenml.Node.objects.create(
            grenml_id='node2-id',
            name='TestNode2',
            latitude=30,
            longitude=30,
        )
        topo_two_node2.topologies.add(topology_two)
        topo_two_node2.owners.add(topo_two_institution)

        topo_two_link1 = grenml.Link.objects.create(
            grenml_id='link1-id',
            name='TestLink1',
            node_a=topo_two_node1,
            node_b=topo_two_node2,
        )
        topo_two_link1.topologies.add(topology_two)
        topo_two_link1.owners.add(topo_two_institution)

        topo_two_link2 = grenml.Link.objects.create(
            grenml_id='link2-id',
            name='TestLink2',
            node_a=topo_two_node1,
            node_b=topo_two_node2,
        )
        topo_two_link2.topologies.add(topology_two)
        topo_two_link2.owners.add(topo_two_institution)

        return (topology_one, topology_two)

    @pytest.fixture
    def simple_rule(self):
        """
        Populates the database with a sample rule infrastructure:
            - one Ruleset, and
            - one Rule.
        The Rule has no matches or actions; these get added by tests
        as appropriate.
        """
        ruleset = Ruleset.objects.create(
            name='Test Ruleset',
        )
        rule = Rule.objects.create(
            name='Test Rule',
            ruleset=ruleset,
        )
        return rule

    def test_node_by_topology_filter_method(
        self,
        two_topologies,
        simple_rule,
    ):
        """
        Unit test the actual MatchType class's filter method.
        """
        topo1 = two_topologies[0]
        simple_rule.add_match_criterion(
            MATCH_INST_BY_TOPOLOGY_CLASS_NAME,
            infos=[(TOPOLOGY_ID_KEY, topo1.grenml_id)],
        )

        topo = grenml.Topology.objects.first()

        # Confirm there are two Nodes in this Topology
        assert grenml.Node.objects.filter(topologies=topo).count() == 2

        # Confirm there are four total Nodes
        assert grenml.Node.objects.count() == 4

        match_nodes_by_topo_criterion = simple_rule.add_match_criterion(
            MATCH_NODE_BY_TOPOLOGY_CLASS_NAME,
            infos=[(TOPOLOGY_ID_KEY, topo.grenml_id)],
        )

        filtered_elements = match_nodes_by_topo_criterion.filter(grenml.Node.objects.all())

        # After filtration, only the Nodes in the Topology should remain
        assert filtered_elements.count() == 2

    def test_inst_by_topology_input_validation(
        self,
        two_topologies,
        simple_rule,
    ):
        """
        Unit test the validation of a properly-configured Match-by-ID
        Match Criterion.
        """
        topo1 = two_topologies[0]
        match_inst_by_topo = simple_rule.add_match_criterion(
            MATCH_INST_BY_TOPOLOGY_CLASS_NAME,
            infos=[(TOPOLOGY_ID_KEY, topo1.grenml_id)],
        )

        match_inst_by_topo_klass = match_inst_by_topo.match_type.get_class_instance(
            match_inst_by_topo,
        )

        # This Match Criterion is properly configured
        assert match_inst_by_topo_klass.validate_input(match_inst_by_topo.info_tuples)

    def test_inst_by_topology_input_validation_missing_key(
        self,
        two_topologies,
        simple_rule,
    ):
        """
        Unit test the validation of a Match-by-ID Match Criterion
        missing the required ID info.
        """
        match_inst_by_topo = simple_rule.add_match_criterion(
            MATCH_INST_BY_TOPOLOGY_CLASS_NAME,
        )

        match_inst_by_topo_klass = match_inst_by_topo.match_type.get_class_instance(
            match_inst_by_topo,
        )

        # This Match Criterion is properly configured
        assert not match_inst_by_topo_klass.validate_input(match_inst_by_topo.info_tuples)

    def test_inst_by_topology_input_validation_incorrect_key(
        self,
        two_topologies,
        simple_rule,
    ):
        """
        Unit test the validation of a Match-by-ID Match Criterion
        missing the required ID info (case mismatch).
        """
        match_inst_by_topo = simple_rule.add_match_criterion(
            MATCH_INST_BY_TOPOLOGY_CLASS_NAME,
            # Note the incorrect case
            infos=[('topology id', 'foo')],
        )

        match_inst_by_topo_klass = match_inst_by_topo.match_type.get_class_instance(
            match_inst_by_topo,
        )

        # This Match Criterion is properly configured
        assert not match_inst_by_topo_klass.validate_input(match_inst_by_topo.info_tuples)

    def test_inst_by_id_input_validation_duplicate_key(
        self,
        two_topologies,
        simple_rule,
    ):
        """
        Unit test the validation of a Match-by-ID Match Criterion
        with duplicate ID info keys.
        """
        match_inst_by_topo = simple_rule.add_match_criterion(
            MATCH_INST_BY_TOPOLOGY_CLASS_NAME,
            infos=[(TOPOLOGY_ID_KEY, 'foo'), (TOPOLOGY_ID_KEY, 'bar')],
        )

        match_inst_by_topo_klass = match_inst_by_topo.match_type.get_class_instance(
            match_inst_by_topo,
        )

        # This Match Criterion is properly configured
        assert not match_inst_by_topo_klass.validate_input(match_inst_by_topo.info_tuples)
