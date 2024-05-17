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

Synopsis: unit tests to check exporting a database that contains more
than one topology.

Each of the tests:
(1) set up a few objects in the database;
(2) call the export function to obtain an output stream;
(3) clear the database;
(3a) clear the Rules including default ID collision Rules;
(4) pass the contents of that stream to the import function;
(5) verify that the import restored the objects created
in the first step.
"""

import pytest
import uuid
from io import BytesIO

from grenml_export.exporter import GRENMLExporter
from grenml_import.importer import GRENMLImporter
from grenml_export.constants import EXTERNAL_TOPOLOGY_PROPERTY_KEY
from network_topology.models import Institution, Link, Node, Topology
from collation.models import Rule, Ruleset


# Developer's note: During test debugging, to print generated XML:
#   print(str(output_stream.getvalue()))
# To print contents of a Topology succinctly:
#   print(parent_topo.log_str_summary())


@pytest.fixture
def two_related_topologies():
    """
    This function puts two Topologies (parent and child) in the
    database, along with two Institutions, one in each Topology.
    Each Topology references its Institution as its owner.
    """
    parent_topology = Topology.objects.create(name='parent topology')
    parent_institution = Institution.objects.create(
        name='parent institution',
        latitude=0.0,
        longitude=0.0,
    )
    parent_topology.owner = parent_institution
    parent_topology.parent = None
    parent_topology.save()
    parent_institution.topologies.add(parent_topology)

    child_topology = Topology.objects.create(name='child topology')
    child_institution = Institution.objects.create(
        name='child institution',
        latitude=0.0,
        longitude=0.0,
    )
    child_topology.owner = child_institution
    child_topology.parent = parent_topology
    child_topology.save()
    child_institution.topologies.add(child_topology)

    return (parent_topology, child_topology)


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


def clear_database():
    """
    Removes all elements from the database.
    Checks that the tables are empty.
    """
    Topology.objects.all().delete()
    assert len(Node.objects.all()) == 0
    assert len(Link.objects.all()) == 0
    assert len(Institution.objects.all()) == 0
    assert len(Topology.objects.all()) == 0


def import_string_stream(string_stream):
    """
    This imports GRENML contained in a StringIO, via
    GRENMLImporter.from_stream .
    """
    grenml_string = string_stream.getvalue()
    grenml_byte_array = grenml_string.encode()
    importer = GRENMLImporter(test_mode=True)
    importer.from_stream(BytesIO(grenml_byte_array))


def create_element_in_topologies(model_class, topologies, fields):
    """
    Creates an element (node or link) in the database. Associates it to
    the topologies in the list passed as a parameter. The node's owner
    institutions will be the list of the owners of the topologies.
    """
    element = model_class.objects.create(**fields)
    for t in topologies:
        element.topologies.add(t)
        element.owners.add(t.owner)
    return element


def create_node_in_topologies(name, address, topologies):
    """
    Creates a node in the database. It will appear in all topologies
    in the list passed as parameter. Its owners will be the owners of
    those topologies.
    """
    return create_element_in_topologies(
        Node,
        topologies,
        {
            'grenml_id': uuid.uuid4(),
            'name': name,
            'address': address,
            'latitude': 0.0,
            'longitude': 0.0,
        },
    )


def create_link_in_topologies(name, node_a, node_b, topologies):
    """
    Creates a link in the database. It will appear in all topologies
    in the list passed as parameter. Its owners will be the owners of
    those topologies.
    """
    return create_element_in_topologies(
        Link,
        topologies,
        {
            'grenml_id': uuid.uuid4(),
            'node_a': node_a,
            'node_b': node_b,
            'name': name,
        },
    )


@pytest.mark.django_db
def test_export_node_with_two_owners_in_different_topologies(clear_rules, two_related_topologies):
    """
    Puts two topologies, two institutions and one node in the database.
    The topologies are a parent and a child.
    Each contains one institution. Both topologies contain the node.
    The two institutions are owners of the node.
    Verifies that the export function succeeds. Deletes all objects in
    the database, passes the GRENML string to the import function
    to recreate them.  Engages the importer's test mode, so that
    external-Topology elements are kept verbatim as they appear in the
    exported GRENML.  We do this because it is easier and clearer to
    test the database than to test the generated XML. Verifies the
    objects are back similar to how they were before deletion.
    """
    parent_topo, child_topo = two_related_topologies
    parent_inst = parent_topo.institutions.first()
    child_inst = child_topo.institutions.first()

    create_node_in_topologies(
        'test node',
        'test node address',
        [parent_topo, child_topo],
    )

    # This is what we're testing!
    exporter = GRENMLExporter()
    output_stream = exporter.to_stream()

    clear_database()
    import_string_stream(output_stream)

    # Confirm 'global' default Institution exists
    # (there may be two: one in each Topology)
    assert Institution.objects.filter(grenml_id='urn:ogf:networking:global').exists()

    # Confirm parent Topology details
    assert Topology.objects.filter(grenml_id=parent_topo.grenml_id).exists()
    new_db_parent_topo = Topology.objects.get(grenml_id=parent_topo.grenml_id)
    assert new_db_parent_topo.parent is None

    # Confirm parent Institution details.
    # Start by excluding duplicate Institutions marked as 'external'.
    non_external_institutions = Institution.objects.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    )
    assert non_external_institutions.filter(grenml_id=parent_inst.grenml_id).exists()
    new_db_parent_inst = non_external_institutions.get(grenml_id=parent_inst.grenml_id)
    assert new_db_parent_inst.topologies.count() == 1
    assert new_db_parent_topo in list(new_db_parent_inst.topologies.all())

    # Confirm parent Topology ownership by parent Institution
    assert new_db_parent_topo.owner == new_db_parent_inst

    # Confirm child Topology details
    assert Topology.objects.filter(grenml_id=child_topo.grenml_id).exists()
    new_db_child_topo = Topology.objects.get(grenml_id=child_topo.grenml_id)
    assert new_db_child_topo.parent.grenml_id == parent_topo.grenml_id

    # Confirm child Institution details
    assert non_external_institutions.filter(grenml_id=child_inst.grenml_id).exists()
    new_db_child_inst = non_external_institutions.get(grenml_id=child_inst.grenml_id)

    # Confirm child Topology ownership by child Institution
    assert new_db_child_topo.owner == new_db_child_inst

    # Confirm Node exists and is owned by the correct Institution(s)
    # It should be represented twice, once in each Topology
    non_external_nodes = Node.objects.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    )
    assert non_external_nodes.count() == 2
    parent_non_external_nodes = new_db_parent_topo.nodes.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    )
    assert parent_non_external_nodes.count() == 1
    new_db_parent_node = parent_non_external_nodes.first()
    assert new_db_parent_node.owners.count() == 2
    assert new_db_parent_inst in list(new_db_parent_node.owners.all())
    child_non_external_nodes = new_db_child_topo.nodes.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    )
    assert child_non_external_nodes.count() == 1
    new_db_child_node = child_non_external_nodes.first()
    assert new_db_child_node.owners.count() == 2
    assert new_db_child_inst in list(new_db_child_node.owners.all())


@pytest.mark.django_db
def test_export_link_with_two_owners_in_different_topologies(clear_rules, two_related_topologies):
    """
    Creates a link associated to two topologies. Its endpoints are
    also associated to them. The link and the endpoints have two owner
    institutions. Each institution occurs in only one of the topologies.
    Exports the database, removes all elements, imports the serialized
    data to recreate the elements, using test mode so that external-
    Topology duplicates are kept verbatim as they appear in the XML.
    We do this because it is easier and clearer to test the
    database than to test the generated XML.
    Verifies the objects are back similar to how they were before
    deletion, skipping Topology tests because this was tested elsewhere
    in this module.
    """
    parent_topo, child_topo = two_related_topologies
    parent_inst = parent_topo.institutions.first()
    child_inst = child_topo.institutions.first()

    node1 = create_node_in_topologies(
        'test node 1',
        'test node 1 address',
        [parent_topo, child_topo],
    )
    node2 = create_node_in_topologies(
        'test node 2',
        'test node 2 address',
        [parent_topo, child_topo],
    )
    link = create_link_in_topologies('test link', node1, node2, [parent_topo, child_topo])

    # This is what we're testing!
    exporter = GRENMLExporter()
    output_stream = exporter.to_stream()

    clear_database()
    import_string_stream(output_stream)

    new_db_parent_topo = Topology.objects.get(grenml_id=parent_topo.grenml_id)
    new_db_parent_inst = Institution.objects.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY
    ).get(
        grenml_id=parent_inst.grenml_id
    )
    new_db_child_topo = Topology.objects.get(grenml_id=child_topo.grenml_id)
    new_db_child_inst = Institution.objects.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY
    ).get(
        grenml_id=child_inst.grenml_id
    )

    # Confirm Nodes exist
    # Each should be represented twice, once in each Topology
    assert Node.objects.count() == 4
    assert new_db_parent_topo.nodes.count() == 2
    assert new_db_child_topo.nodes.count() == 2

    # Confirm Link exists
    # It should be represented twice, once in each Topology
    assert Link.objects.count() == 2
    new_db_parent_link = new_db_parent_topo.links.get(grenml_id=link.grenml_id)
    new_db_child_link = new_db_child_topo.links.get(grenml_id=link.grenml_id)

    # Confirm each Link's ownership
    assert new_db_parent_link.owners.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    ).count() == 1
    assert new_db_parent_inst in list(new_db_parent_link.owners.all())
    assert new_db_child_link.owners.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    ).count() == 1
    assert new_db_child_inst in list(new_db_child_link.owners.all())

    # Confirm each Link has the correct endpoints
    expected_endpoint_ids = [
        str(node1.grenml_id),
        str(node2.grenml_id),
    ]
    actual_parent_endpoint_ids = [
        str(new_db_parent_link.node_a.grenml_id),
        str(new_db_parent_link.node_b.grenml_id),
    ]
    assert sorted(actual_parent_endpoint_ids) == sorted(expected_endpoint_ids)
    actual_child_endpoint_ids = [
        str(new_db_child_link.node_a.grenml_id),
        str(new_db_child_link.node_b.grenml_id),
    ]
    assert sorted(actual_child_endpoint_ids) == sorted(expected_endpoint_ids)


@pytest.mark.django_db
def test_export_link_between_nodes_in_different_topologies(clear_rules, two_related_topologies):
    """
    This creates two topologies, parent and child. Each topology has
    a distinct node. The parent topology has a link that connects
    the nodes. Verifies that the export function works.
    Clears the database. Takes the exported string and passes it to
    the import function. Verifies the existence of the topologies,
    nodes and link.
    """
    parent_topo, child_topo = two_related_topologies
    parent_inst = parent_topo.institutions.first()
    child_inst = child_topo.institutions.first()

    node_in_parent_topo = create_node_in_topologies(
        'parent topology node',
        'parent topology node address',
        [parent_topo],
    )
    node_in_child_topo = create_node_in_topologies(
        'child topology node',
        'child topology node address',
        [child_topo],
    )
    link = create_link_in_topologies(
        'parent topology link',
        node_in_parent_topo,
        node_in_child_topo,
        [parent_topo],
    )

    # This is what we're testing!
    exporter = GRENMLExporter()
    output_stream = exporter.to_stream()
    print(output_stream.getvalue())  # DEBUG

    clear_database()
    import_string_stream(output_stream)

    new_db_parent_topo = Topology.objects.get(grenml_id=parent_topo.grenml_id)
    new_db_parent_inst = Institution.objects.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY
    ).get(
        grenml_id=parent_inst.grenml_id
    )
    new_db_child_topo = Topology.objects.get(grenml_id=child_topo.grenml_id)
    new_db_child_inst = Institution.objects.exclude(
        properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY
    ).get(
        grenml_id=child_inst.grenml_id
    )

    # Confirm Nodes exist and are owned by the correct Institution(s)
    # The parent Topo should contain both Nodes in the export, so that
    # the Topology can stand alone with all the Link's endpoints,
    # but the child should only contain its own Node.
    assert Node.objects.count() == 3
    assert new_db_parent_topo.nodes.count() == 2
    assert new_db_child_topo.nodes.count() == 1
    new_db_parent_nodes = new_db_parent_topo.nodes.all()
    for n in new_db_parent_nodes:
        assert n.owners.exclude(properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY).count() == 1
        assert new_db_parent_inst in list(n.owners.all())
    new_db_child_node = new_db_child_topo.nodes.first()
    assert new_db_child_node.owners.count() == 1
    assert new_db_child_inst in list(new_db_child_node.owners.all())

    # Confirm Link exists (in the parent Topology) and its ownership
    assert Link.objects.count() == 1
    new_db_link = new_db_parent_topo.links.get(grenml_id=link.grenml_id)
    assert new_db_link.owners.count() == 1
    assert new_db_parent_inst in list(new_db_link.owners.all())

    # Confirm each Link has the correct endpoints
    expected_endpoint_ids = [
        str(node_in_parent_topo.grenml_id),
        str(node_in_child_topo.grenml_id),
    ]
    actual_endpoint_ids = [
        str(new_db_link.node_a.grenml_id),
        str(new_db_link.node_b.grenml_id),
    ]
    assert sorted(actual_endpoint_ids) == sorted(expected_endpoint_ids)
