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

Synopsis: unit tests for importing elements that are marked as
    "external", or originally belonging exclusively to topologies
    other than the ones in which they are included.
    Elements may be included in topologies this way in order to
    ensure that ownership relationships can be correctly preserved
    even if the owning institutions have not (yet) been imported,
    and links' endpoint nodes are present in similar conditions.
"""

import pytest

from grenml import GRENMLManager
from grenml.models import Topology as GRENMLTopology
from grenml.models import Institution as GRENMLInstitution
from grenml.models import Node as GRENMLNode
from grenml.models import Link as GRENMLLink

from grenml_export.constants import (
    EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER,
)
from grenml_import.importer import GRENMLImporter
from network_topology.models import Institution, Link, Node, Topology, Property
from collation.models import Rule, Ruleset


@pytest.fixture
def clear_rules():
    """
    Removes all Rules from the database, including default ID
    collision Rules, to allow unrestricted import.  Because
    exports are tested by re-importing their contents and using
    DB queries to examine them, Rules could tarnish the raw import
    required to support this method.
    """
    Rule.objects.all().delete()
    Ruleset.objects.all().delete()


@pytest.fixture
def manager():
    """
    Supplies a basic GRENMLManager.
    """
    manager = GRENMLManager(
        id='RootTopo',
        name='Root Topology',
    )
    root_inst = GRENMLInstitution(
        id='RootTopoInst',
        name='Root Owner',
    )
    manager.topology.add_institution(root_inst)
    manager.topology.primary_owner = root_inst
    return manager


def create_basic_topology(id, name):
    """
    Creates a simple GRENML Topology with a primary owner.
    """
    topo = GRENMLTopology(
        id=id,
        name=name,
    )
    owner_inst = GRENMLInstitution(
        id=id + 'Inst',
        name=name + ' Owner',
    )
    topo.add_institution(owner_inst)
    topo.primary_owner = owner_inst
    return topo


@pytest.mark.django_db
def test_import_link_with_endpoint_in_grandparent(clear_rules, manager):
    """
    A Link has one of its endpoint Nodes in a Topology
    two levels up in the hierarchy tree.  Ensure the 'external'
    copy in the grandchild is deduplicated and the Link
    relationships are resolved correctly.
    """
    # Topologies
    root_topo = manager.topology
    child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(child_topo)
    grandchild_topo = create_basic_topology('GrandchildTopo', 'Grandchild Topology')
    child_topo.add_topology(grandchild_topo)

    # Nodes
    root_node = GRENMLNode(
        id='NodeA',
        name='Root Level Node',
        latitude=0.0,
        longitude=0.0,
    )
    root_topo.add_node(root_node)
    grandchild_node = GRENMLNode(
        id='NodeB',
        name='Grandchild Level Node',
        latitude=0.0,
        longitude=0.0,
    )
    grandchild_topo.add_node(grandchild_node)

    # External Node copy simulating how exported GRENML might look
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: root_topo.id,
    }
    root_node_external_copy = GRENMLNode(
        # Same ID as the main root_node
        id='NodeA',
        name='Root Level Node Copy',
        latitude=0.0,
        longitude=0.0,
        **external_property,
    )
    grandchild_topo.add_node(root_node_external_copy)

    # Link
    grandchild_link = GRENMLLink(
        id='Link',
        name='Grandchild Level Link',
        # Endpoint is the copy;
        # it should be re-linked to the original upon import.
        nodes=[root_node_external_copy.id, grandchild_node.id],
    )
    grandchild_topo.add_link(grandchild_link)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    # Assert link is rebuilt with the original version of the Node
    # in the root Topology, and the external Node copy is gone
    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert Node.objects.count() == 2
    assert not Node.objects.filter(name='Root Level Node Copy').exists()
    link = Link.objects.get()
    endpoints = set([link.node_a.grenml_id, link.node_b.grenml_id])
    assert endpoints == set([root_node.id, grandchild_node.id])
    endpoint_topologies = set([
        link.node_a.topologies.get().grenml_id,
        link.node_b.topologies.get().grenml_id,
    ])
    assert endpoint_topologies == set([root_topo.id, grandchild_topo.id])


@pytest.mark.django_db
def test_import_link_with_endpoint_in_grandchild(clear_rules, manager):
    """
    A Link has one of its endpoint Nodes in a Topology
    two levels down in the hierarchy tree.  Ensure the 'external'
    copy in the grandparent is deduplicated and the Link
    relationships are resolved correctly.
    """
    # Topologies
    root_topo = manager.topology
    child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(child_topo)
    grandchild_topo = create_basic_topology('GrandchildTopo', 'Grandchild Topology')
    child_topo.add_topology(grandchild_topo)

    # Nodes
    root_node = GRENMLNode(
        id='NodeA',
        name='Root Level Node',
        latitude=0.0,
        longitude=0.0,
    )
    root_topo.add_node(root_node)
    grandchild_node = GRENMLNode(
        id='NodeB',
        name='Grandchild Level Node',
        latitude=0.0,
        longitude=0.0,
    )
    grandchild_topo.add_node(grandchild_node)

    # External Node copy simulating how exported GRENML might look
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: grandchild_topo.id,
    }
    grandchild_node_external_copy = GRENMLNode(
        # Same ID as the main grandchild_node
        id='NodeB',
        name='Grandchild Level Node Copy',
        latitude=0.0,
        longitude=0.0,
        **external_property,
    )
    root_topo.add_node(grandchild_node_external_copy)

    # Link
    root_link = GRENMLLink(
        id='Link',
        name='Root Level Link',
        # Endpoint is the copy;
        # it should be re-linked to the original upon import.
        nodes=[root_node.id, grandchild_node_external_copy.id],
    )
    root_topo.add_link(root_link)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    # Assert link is rebuilt with the original version of the Node
    # in the grandchild Topology, and the external Node copy is gone
    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert Node.objects.count() == 2
    assert not Node.objects.filter(name='Grandchild Level Node Copy').exists()
    link = Link.objects.get()
    endpoints = set([link.node_a.grenml_id, link.node_b.grenml_id])
    assert endpoints == set([root_node.id, grandchild_node.id])
    endpoint_topologies = set([
        link.node_a.topologies.get().grenml_id,
        link.node_b.topologies.get().grenml_id,
    ])
    assert endpoint_topologies == set([root_topo.id, grandchild_topo.id])


@pytest.mark.django_db
def test_import_topology_with_owner_in_grandparent(clear_rules, manager):
    """
    Three levels of Topology are set up.  The grandchild Topo
    has its primary owner set to an Institution in the root level.
    Ensure the 'external' copy in the grandchild is deduplicated
    and the owner relationships are resolved correctly.
    """
    # Topologies
    root_topo = manager.topology
    child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(child_topo)
    grandchild_topo = create_basic_topology('GrandchildTopo', 'Grandchild Topology')
    child_topo.add_topology(grandchild_topo)

    # External Institution copy simulating exported GRENML
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: root_topo.id,
    }
    root_inst_external_copy = GRENMLInstitution(
        id=root_topo.primary_owner,
        name='Root Level Owner Institution Copy',
        **external_property,
    )
    grandchild_topo.add_institution(root_inst_external_copy)
    grandchild_topo.primary_owner = (root_inst_external_copy)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert not Institution.objects.filter(name='Root Level Owner Institution Copy').exists()
    db_root_topo = Topology.objects.get(grenml_id='RootTopo')
    db_grandchild_topo = Topology.objects.get(grenml_id='GrandchildTopo')
    assert db_grandchild_topo.owner == db_root_topo.owner
    assert db_root_topo.owner.topologies.get() == db_root_topo


@pytest.mark.django_db
def test_import_topology_with_owner_in_grandchild(clear_rules, manager):
    """
    Three levels of Topology are set up.  The root level Topo
    has its primary owner set to an Institution in the grandchild.
    Ensure the 'external' copy in the root is deduplicated
    and the owner relationships are resolved correctly.
    """
    # Topologies
    root_topo = manager.topology
    child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(child_topo)
    grandchild_topo = create_basic_topology('GrandchildTopo', 'Grandchild Topology')
    child_topo.add_topology(grandchild_topo)

    # External Institution copy simulating exported GRENML
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: grandchild_topo.id,
    }
    grandchild_inst_external_copy = GRENMLInstitution(
        id=grandchild_topo.primary_owner,
        name='Grandchild Topology Owner Copy',
        **external_property,
    )
    root_topo.add_institution(grandchild_inst_external_copy)
    root_topo.primary_owner = (grandchild_inst_external_copy)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert not Institution.objects.filter(name='Grandchild Topology Owner Copy').exists()
    db_root_topo = Topology.objects.get(grenml_id='RootTopo')
    db_grandchild_topo = Topology.objects.get(grenml_id='GrandchildTopo')
    assert db_root_topo.owner == db_grandchild_topo.owner
    assert db_grandchild_topo.owner.topologies.get() == db_grandchild_topo


@pytest.mark.django_db
def test_import_link_with_owner_in_grandparent(clear_rules, manager):
    """
    Three levels of Topology are set up.  A Link in the grandchild
    Topo has its owner set to an Institution in the root level.
    Ensure the 'external' copy in the grandchild is deduplicated
    and the owner relationships are resolved correctly.
    """
    # Topologies
    root_topo = manager.topology
    child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(child_topo)
    grandchild_topo = create_basic_topology('GrandchildTopo', 'Grandchild Topology')
    child_topo.add_topology(grandchild_topo)

    # External Institution copy simulating exported GRENML
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: root_topo.id,
    }
    root_inst_external_copy = GRENMLInstitution(
        id=root_topo.primary_owner,
        name='Root Level Owner Institution Copy',
        **external_property,
    )
    grandchild_topo.add_institution(root_inst_external_copy)

    # Nodes
    node_a = GRENMLNode(
        id='NodeA',
        name='Node A',
        latitude=0.0,
        longitude=0.0,
    )
    grandchild_topo.add_node(node_a)
    node_b = GRENMLNode(
        id='NodeB',
        name='Node B',
        latitude=0.0,
        longitude=0.0,
    )
    grandchild_topo.add_node(node_b)

    # Link
    grandchild_link = GRENMLLink(
        id='Link',
        name='Grandchild Level Link',
        nodes=[node_a.id, node_b.id],
        owners=[root_inst_external_copy.id],
    )
    grandchild_topo.add_link(grandchild_link)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert not Institution.objects.filter(name='Root Level Owner Institution Copy').exists()
    db_root_topo = Topology.objects.get(grenml_id='RootTopo')
    link_owner_inst = Institution.objects.get(grenml_id='RootTopoInst')
    assert link_owner_inst.topologies.get() == db_root_topo
    link = Link.objects.get()
    # Currently, the GRENML library adds an element's Topology's
    # primary owner as an owner of the element.  We expect that here.
    link_owner_ids = set(link.owners.values_list('grenml_id', flat=True))
    assert link_owner_ids == set([link_owner_inst.grenml_id, grandchild_topo.primary_owner])


@pytest.mark.django_db
def test_import_node_with_owner_in_grandchild(clear_rules, manager):
    """
    Three levels of Topology are set up.  A Node in the root level
    Topo has its owner set to an Institution in the grandchild.
    Ensure the 'external' copy in the root level is deduplicated
    and the owner relationships are resolved correctly.
    """
    # Topologies
    root_topo = manager.topology
    child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(child_topo)
    grandchild_topo = create_basic_topology('GrandchildTopo', 'Grandchild Topology')
    child_topo.add_topology(grandchild_topo)

    # External Institution copy simulating exported GRENML
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: grandchild_topo.id,
    }
    grandchild_inst_external_copy = GRENMLInstitution(
        id=grandchild_topo.primary_owner,
        name='Grandchild Owner Institution Copy',
        **external_property,
    )
    root_topo.add_institution(grandchild_inst_external_copy)

    # Node
    node = GRENMLNode(
        id='Node',
        name='Node',
        latitude=0.0,
        longitude=0.0,
        owners=[grandchild_inst_external_copy.id],
    )
    root_topo.add_node(node)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert not Institution.objects.filter(name='Grandchild Owner Institution Copy').exists()
    db_grandchild_topo = Topology.objects.get(grenml_id='GrandchildTopo')
    node_owner_inst = Institution.objects.get(grenml_id='GrandchildTopoInst')
    assert node_owner_inst.topologies.get() == db_grandchild_topo
    node = Node.objects.get()
    # Currently, the GRENML library adds an element's Topology's
    # primary owner as an owner of the element.  We expect that here.
    node_owner_ids = set(node.owners.values_list('grenml_id', flat=True))
    assert node_owner_ids == set([node_owner_inst.grenml_id, root_topo.primary_owner])


@pytest.mark.django_db
def test_import_link_with_endpoint_node_in_same_and_unrelated_topo(clear_rules, manager):
    """
    A Link has two endpoint Nodes in the same Topology.
    One of these endpoint Nodes also belongs to an unrelated
    Topology.  Ensure import reflects this without duplicates,
    in two scenarios:
        1. unrelated Topology is imported first
        2. unrelated Topology is imported second
    """
    # Topologies
    topo = manager.topology

    another_manager = GRENMLManager(
        id='UnrelatedTopo',
        name='Unrelated Topology',
    )
    unrelated_topo = another_manager.topology
    another_inst = GRENMLInstitution(
        id='UnrelatedTopoInst',
        name='Another Inst',
    )
    unrelated_topo.add_institution(another_inst)
    unrelated_topo.primary_owner = another_inst

    # Institution "external" copy
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: unrelated_topo.id,
    }
    another_inst_copy = GRENMLInstitution(
        id=another_inst.id,
        name='Another Inst Copy',
        **external_property,
    )
    topo.add_institution(another_inst_copy)

    # Nodes
    node = GRENMLNode(
        id='SimpleNode',
        name='Simple Node',
        latitude=0.0,
        longitude=0.0,
        owners=[topo.primary_owner],
    )
    topo.add_node(node)
    interesting_node = GRENMLNode(
        id='InterestingNode',
        name='Interesting Node',
        latitude=0.0,
        longitude=0.0,
        owners=[topo.primary_owner, another_inst_copy.id],
    )
    topo.add_node(interesting_node)

    # Link
    link = GRENMLLink(
        id='Link',
        name='Link',
        nodes=[node.id, interesting_node.id],
        owners=[topo.primary_owner],
    )
    topo.add_link(link)

    # Import unrelated Topology first!
    importer = GRENMLImporter()
    importer.from_grenml_manager(another_manager)
    importer.from_grenml_manager(manager)

    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert not Institution.objects.filter(name='Another Inst Copy').exists()
    link = Link.objects.get()
    if link.node_a.grenml_id == 'InterestingNode':
        node_of_interest = link.node_a
    else:
        node_of_interest = link.node_b
    assert node_of_interest.owners.count() == 2
    db_root_inst = node_of_interest.owners.get(grenml_id='RootTopoInst')
    assert db_root_inst.topologies.count() == 1
    assert db_root_inst.topologies.get().grenml_id == 'RootTopo'
    db_unrelated_inst = node_of_interest.owners.get(grenml_id='UnrelatedTopoInst')
    assert db_unrelated_inst.topologies.count() == 1
    assert db_unrelated_inst.topologies.get().grenml_id == 'UnrelatedTopo'

    # Clear Topologies and try second scenario
    Topology.objects.all().delete()
    importer.from_grenml_manager(manager)

    # Confirm the external item is still around and pending
    assert Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert Institution.objects.filter(name='Another Inst Copy').exists()
    link = Link.objects.get()
    if link.node_a.grenml_id == 'InterestingNode':
        node_of_interest = link.node_a
    else:
        node_of_interest = link.node_b
    assert node_of_interest.owners.count() == 2
    link = Link.objects.get()
    if link.node_a.grenml_id == 'InterestingNode':
        node_of_interest = link.node_a
    else:
        node_of_interest = link.node_b
    assert node_of_interest.owners.count() == 2
    db_root_inst = node_of_interest.owners.get(grenml_id='RootTopoInst')
    assert db_root_inst.topologies.count() == 1
    assert db_root_inst.topologies.get().grenml_id == 'RootTopo'
    db_unrelated_inst_copy = node_of_interest.owners.get(grenml_id='UnrelatedTopoInst')
    assert db_unrelated_inst_copy.name == 'Another Inst Copy'
    assert db_unrelated_inst_copy.topologies.count() == 1
    assert db_unrelated_inst_copy.topologies.get().grenml_id == 'RootTopo'

    # Now import the unrelated Topology and expect the external
    # element to be resolved and deduplicated.
    importer.from_grenml_manager(another_manager)

    assert not Property.objects.filter(name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).exists()
    assert not Institution.objects.filter(name='Another Inst Copy').exists()
    link = Link.objects.get()
    if link.node_a.grenml_id == 'InterestingNode':
        node_of_interest = link.node_a
    else:
        node_of_interest = link.node_b
    assert node_of_interest.owners.count() == 2
    db_root_inst = node_of_interest.owners.get(grenml_id='RootTopoInst')
    assert db_root_inst.topologies.count() == 1
    assert db_root_inst.topologies.get().grenml_id == 'RootTopo'
    db_unrelated_inst = node_of_interest.owners.get(grenml_id='UnrelatedTopoInst')
    assert db_unrelated_inst.topologies.count() == 1
    assert db_unrelated_inst.topologies.get().grenml_id == 'UnrelatedTopo'


@pytest.mark.django_db
def test_import_node_with_conflicting_originals(clear_rules, manager):
    """
    Simulate a scenario where it is ambiguous which "original" element
    an imported "external" element points to during import.  This
    situation should be rare in practice, as GRENML IDs are supposed
    to be unique except during import before ID collision resolution
    (and external element resolution of course), but it can occur.
    This situation cannot be automatically resolved, so we expect
    no resolution from the post-import processes.
    """
    root_topo = manager.topology
    first_child_topo = create_basic_topology('ChildTopo', 'Child Topology')
    root_topo.add_topology(first_child_topo)
    second_child_topo = create_basic_topology('AnotherChildTopo', 'Another Child Topology')
    root_topo.add_topology(second_child_topo)

    node_in_first_child = GRENMLNode(
        id='Node',
        name='Original Node in Child',
        latitude=0.0,
        longitude=0.0,
        owners=[first_child_topo.primary_owner],
    )
    first_child_topo.add_node(node_in_first_child)

    node_in_second_child = GRENMLNode(
        id='Node',
        name='Another Original Node in Another Child',
        latitude=0.0,
        longitude=0.0,
        owners=[second_child_topo.primary_owner],
    )
    second_child_topo.add_node(node_in_second_child)

    # External Institution copy simulating exported GRENML
    external_property = {
        EXTERNAL_TOPOLOGY_PROPERTY_KEY: '{}{}{}'.format(
            first_child_topo.id,
            EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER,
            second_child_topo.id,
        )
    }
    node_external_copy = GRENMLNode(
        id='Node',
        name='Node Copy',
        latitude=0.0,
        longitude=0.0,
        **external_property,
    )
    root_topo.add_node(node_external_copy)

    # Import!
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    assert Node.objects.count() == 3
