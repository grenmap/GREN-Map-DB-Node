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

------------------------------------------------------------------------

Synopsis: unit tests for the external- or cross-topology utility
    methods on the GRENMLImporter class.
"""

import pytest

from grenml_export.constants import (
    EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER,
)
from grenml_import.importer import GRENMLImporter
from network_topology.models import Topology, Institution, Node, Link, Property


@pytest.mark.django_db
def test_identify_cross_topology_elements():
    topo1 = Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    topo2 = Topology.objects.create(
        grenml_id='Topo2',
        name='Topology 2',
    )

    original_inst_1 = Institution.objects.create(
        grenml_id='Inst1',
        name='Institution 1',
        latitude=0.0,
        longitude=0.0,
    )
    original_inst_1.topologies.add(topo1)
    original_inst_2 = Institution.objects.create(
        grenml_id='Inst2',
        name='Institution 2',
        latitude=0.0,
        longitude=0.0,
    )
    original_inst_2.topologies.add(topo2)

    ext_inst_1 = Institution.objects.create(
        grenml_id='Inst1',
        name='Institution 1 Copy',
        latitude=0.0,
        longitude=0.0,
    )
    ext_inst_1.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value='Topo1',
    )
    ext_inst_2 = Institution.objects.create(
        grenml_id='Inst2',
        name='Institution 2 Copy in Nonexistent Topology',
        latitude=0.0,
        longitude=0.0,
    )
    # This external Property should be left alone;
    # the element should be identified by the method,
    # but the original Topology will be null as this
    # Topology does not exist in the DB.
    ext_inst_2.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value='NonexistentTopo',
    )

    original_node_1 = Node.objects.create(
        grenml_id='Node1',
        name='Node 1',
        latitude=0.0,
        longitude=0.0,
    )
    original_node_1.topologies.add(topo1)
    original_node_2 = Node.objects.create(
        grenml_id='Node2',
        name='Node 2',
        latitude=0.0,
        longitude=0.0,
    )
    original_node_2.topologies.add(topo2)

    ext_node_1 = Node.objects.create(
        grenml_id='Node1',
        name='Node 1 Copy',
        latitude=0.0,
        longitude=0.0,
    )
    ext_node_1.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value='Topo1',
    )
    ext_node_2 = Node.objects.create(
        grenml_id='Node2',
        name='Node 2 Copy',
        latitude=0.0,
        longitude=0.0,
    )
    # The element should be identified by the method,
    # but the original Topology will only contain the
    # Topo2 Topology since it is the only one of the two
    # to actually exist in the DB.
    ext_node_2.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value=EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER.join(['NonexistentTopo', 'Topo2']),
    )

    importer = GRENMLImporter()

    cross_topo_insts = importer._identify_cross_topology_elements(Institution)
    assert len(cross_topo_insts) == 2
    original_inst_lists = [inst[1] for inst in cross_topo_insts]
    original_insts_flat = [inst for orig_list in original_inst_lists for inst in orig_list]
    assert set([inst.pk for inst in original_insts_flat]) == set([original_inst_1.pk])

    cross_topo_nodes = importer._identify_cross_topology_elements(Node)
    assert len(cross_topo_nodes) == 2
    original_node_lists = [node[1] for node in cross_topo_nodes]
    original_nodes_flat = [node for orig_list in original_node_lists for node in orig_list]
    assert set([node.pk for node in original_nodes_flat]) \
        == set([original_node_1.pk, original_node_2.pk])


@pytest.mark.django_db
def test_resolve_cross_topology_institutions():
    topo1 = Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    topo2 = Topology.objects.create(
        grenml_id='Topo2',
        name='Topology 2',
    )

    original_inst_1 = Institution.objects.create(
        grenml_id='Inst1',
        name='Institution 1',
        latitude=0.0,
        longitude=0.0,
    )
    original_inst_1.topologies.add(topo1)
    original_inst_2 = Institution.objects.create(
        grenml_id='Inst2',
        name='Institution 2',
        latitude=0.0,
        longitude=0.0,
    )
    original_inst_2.topologies.add(topo2)

    ext_inst_1 = Institution.objects.create(
        grenml_id='Inst1',
        name='Institution 1 Copy',
        latitude=0.0,
        longitude=0.0,
    )
    ext_inst_1.topologies.add(topo2)
    ext_inst_1.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value='Topo1',
    )
    ext_inst_2 = Institution.objects.create(
        grenml_id='Inst2',
        name='Institution 2 Copy in Nonexistent Topology',
        latitude=0.0,
        longitude=0.0,
    )
    # This external Property should be left alone;
    # the element should be identified by the method,
    # but the original Topology will be null as this
    # Topology does not exist in the DB.
    ext_inst_2.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value='NonexistentTopo',
    )
    ext_inst_2.topologies.add(topo2)

    # Some elements and relationships to test that ownership
    # is correctly transferred.

    topo1.owner = original_inst_1
    topo1.save()
    topo2.owner = ext_inst_1
    topo2.save()

    node_1 = Node.objects.create(
        grenml_id='Node1',
        name='Node 1',
        latitude=0.0,
        longitude=0.0,
    )
    node_1.topologies.add(topo2)
    node_1.owners.add(ext_inst_1)

    node_2 = Node.objects.create(
        grenml_id='Node2',
        name='Node 2',
        latitude=0.0,
        longitude=0.0,
    )
    node_2.topologies.add(topo2)
    node_2.owners.add(original_inst_2)

    link_1 = Link.objects.create(
        grenml_id='Link1',
        name='Link 1',
        node_a=node_1,
        node_b=node_2,
    )
    link_1.topologies.add(topo2)
    link_1.owners.add(ext_inst_1)

    importer = GRENMLImporter()
    importer._resolve_cross_topology_elements_by_type(Institution)

    # Confirm deduplication
    assert Institution.objects.count() == 3
    assert Institution.objects.filter(grenml_id='Inst1').count() == 1
    assert Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).count() == 1
    assert Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).get().value \
        == 'NonexistentTopo'

    # Confirm ownership relationships have been transferred
    # from ext_inst_1 to original_inst_1 in topo2.
    # First refresh our copy of original_inst_1 to get the newest PK.
    original_inst_1 = Institution.objects.get(grenml_id='Inst1')
    oi1_pk = original_inst_1.pk
    assert Topology.objects.get(grenml_id='Topo1').owner.pk == oi1_pk
    assert Topology.objects.get(grenml_id='Topo2').owner.pk == oi1_pk
    assert oi1_pk in [owner.pk for owner in Node.objects.get(grenml_id='Node1').owners.all()]
    assert oi1_pk not in [owner.pk for owner in Node.objects.get(grenml_id='Node2').owners.all()]
    assert oi1_pk in [owner.pk for owner in Link.objects.get(grenml_id='Link1').owners.all()]


@pytest.mark.django_db
def test_resolve_cross_topology_nodes():
    topo1 = Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    topo2 = Topology.objects.create(
        grenml_id='Topo2',
        name='Topology 2',
    )

    original_inst_1 = Institution.objects.create(
        grenml_id='Inst1',
        name='Institution 1',
        latitude=0.0,
        longitude=0.0,
    )
    original_inst_1.topologies.add(topo1)
    original_inst_2 = Institution.objects.create(
        grenml_id='Inst2',
        name='Institution 2',
        latitude=0.0,
        longitude=0.0,
    )
    original_inst_2.topologies.add(topo2)

    original_node_1 = Node.objects.create(
        grenml_id='Node1',
        name='Node 1',
        latitude=0.0,
        longitude=0.0,
    )
    original_node_1.topologies.add(topo1)
    original_node_2 = Node.objects.create(
        grenml_id='Node2',
        name='Node 2',
        latitude=0.0,
        longitude=0.0,
    )
    original_node_2.topologies.add(topo2)

    ext_node_1 = Node.objects.create(
        grenml_id='Node1',
        name='Node 1 Copy',
        latitude=0.0,
        longitude=0.0,
    )
    ext_node_1.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value='Topo1',
    )
    ext_node_1.topologies.add(topo2)
    ext_node_2 = Node.objects.create(
        grenml_id='Node2',
        name='Node 2 Copy',
        latitude=0.0,
        longitude=0.0,
    )
    # The element should be identified by the method,
    # but the original Topology will only contain the
    # Topo2 Topology since it is the only one of the two
    # to actually exist in the DB.
    ext_node_2.property(
        EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        value=EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER.join(['NonexistentTopo', 'Topo2']),
    )
    ext_node_2.topologies.add(topo1)

    # Some elements and relationships to test that endpoints
    # are correctly transferred.

    link_1 = Link.objects.create(
        grenml_id='Link1',
        name='Link 1',
        node_a=original_node_1,
        node_b=ext_node_2,
    )
    link_1.topologies.add(topo1)

    link_2 = Link.objects.create(
        grenml_id='Link2',
        name='Link 2',
        node_a=ext_node_1,
        node_b=original_node_2,
    )
    link_2.topologies.add(topo2)

    importer = GRENMLImporter()
    importer._resolve_cross_topology_elements_by_type(Node)

    # Confirm deduplication
    assert Node.objects.count() == 2
    assert Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).count() == 0

    # Confirm endpoint relationships have been transferred.
    # First refresh our copies of the Nodes and Links to get
    # updated PKs.
    node_1 = Node.objects.get(grenml_id='Node1')
    node_2 = Node.objects.get(grenml_id='Node2')
    link_1 = Link.objects.get(grenml_id='Link1')
    link_2 = Link.objects.get(grenml_id='Link2')
    assert link_1.node_a.pk == node_1.pk
    assert link_1.node_b.pk == node_2.pk
    assert link_2.node_a.pk == node_1.pk
    assert link_2.node_b.pk == node_2.pk
