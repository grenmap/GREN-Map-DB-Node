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

import network_topology.models as m
from grenml.managers import GRENMLManager
from grenml.models import INSTITUTIONS, NODES, LINKS, TOPOLOGIES


def make_grenml_id(topology_id, entity, sequential):
    """
    This creates a GRENML ID for an object we will import.
    IDs for institutions, links and nodes will have the topology ID
    as a prefix, then the kind of object, then a sequence number
    which will correspond to the number of existing objects of that kind
    in the GRENML manager.
    """
    if entity == TOPOLOGIES:
        result = topology_id
    else:
        result = '.'.join([topology_id, entity, str(sequential)])
    return result


def add_institution_nodes_and_link(manager, topology_id, latitude, longitude):
    """
    This function populates a GRENML manager with an institution,
    two nodes and a link between the nodes.
    """
    def make_grenml_id_with_manager(entity):
        num_elements = len(manager.topology.get_elements(entity) or [])
        if entity == INSTITUTIONS:
            sequential = num_elements
        else:
            sequential = num_elements + 1
        return make_grenml_id(topology_id, entity, sequential)

    institution_id = make_grenml_id_with_manager(INSTITUTIONS)
    institution = manager.add_institution(
        id=institution_id,
        name=institution_id,
        latitude=latitude,
        longitude=longitude,
        institution_property='institution_property_value',
    )

    node1_id = make_grenml_id_with_manager(NODES)
    manager.add_node(
        id=node1_id,
        name=node1_id,
        owners=[institution],
        latitude=latitude,
        longitude=longitude - 10,
        node_property='node_property_value',
    )

    node2_id = make_grenml_id_with_manager(NODES)
    manager.add_node(
        id=node2_id,
        name=node2_id,
        owners=[institution],
        latitude=latitude,
        longitude=longitude + 10,
    )

    link_id = make_grenml_id_with_manager(LINKS)
    manager.add_link(
        id=link_id,
        name=link_id,
        owners=[institution],
        nodes=manager.get_nodes(id__in=[node1_id, node2_id]),
        link_property='link_property_value',
    )

    return {
        'id': institution_id,
        'nodes': [node1_id, node2_id],
        'links': [link_id],
    }


DEFAULT_TOPOLOGY_ID = 'topo'


def make_topology_fixture(topology_id=DEFAULT_TOPOLOGY_ID, latitude=0):
    """
    This populates a GRENML manager with one topology containing
    two institutions, four nodes and two links. One of the institutions
    will be the owner of the topology. The four nodes form two pairs,
    with each pair of nodes having one of the links between them.
    """
    manager = GRENMLManager(id=topology_id, name=topology_id)
    manager.topology.add_property('topology_property', 'topology_property_value')

    institution1_dict = add_institution_nodes_and_link(
        manager,
        topology_id,
        latitude,
        -20,
    )
    manager.set_primary_owner(institution1_dict['id'])

    add_institution_nodes_and_link(
        manager,
        topology_id,
        latitude,
        20,
    )
    return {
        'import_manager': manager,
        'delete_manager': manager,
    }


def make_nested_topology_fixture():
    """
    This makes two topologies and associates them
    as parent and child.
    """
    fixture = make_topology_fixture('parent_topo', 0)
    parent_manager = fixture['import_manager']
    parent_topology = parent_manager.topology

    fixture = make_topology_fixture('child_topo', 20)
    child_manager = fixture['import_manager']
    child_topology = child_manager.topology

    parent_topology.add_topology(child_topology)
    return {
        'import_manager': parent_manager,
        'delete_manager': child_manager,
    }


def make_delete_topology_fixture():
    """
    This builds the fixture for the test that creates parent and
    child topology, then removes the latter.
    """
    fixture = make_nested_topology_fixture()
    fixture['delete_manager'] = fixture['import_manager']
    return fixture


MODEL_CLASSES = {
    INSTITUTIONS: m.Institution,
    LINKS: m.Link,
    NODES: m.Node,
    TOPOLOGIES: m.Topology,
}


def make_delete_item_for_topology(topology_id, entity, sequential):
    """
    This is a constructor for a delete_list item that refers to
    an institution, link or node.

    The main test function (test_delete_propagation) uses delete_list
    items to modify the fixture between the first import that populates
    the database and the second import, when the delete propagation
    code executes.
    """
    item_id = make_grenml_id(topology_id, entity, sequential)
    return {
        'entity': entity,
        'id': item_id,
        'model_class': MODEL_CLASSES[entity],
    }


def make_delete_item(entity, sequential):
    """ Returns a delete_list item that refers to a topology.  """
    return make_delete_item_for_topology(
        DEFAULT_TOPOLOGY_ID,
        entity,
        sequential,
    )


def assert_absence(model_class, query_list):
    """
    Assertion to verify that none of the objects in the query_list
    exists in the database. The query_list items should be dictionaries
    with the same attributes as the ones in a delete_list.
    See the docstring for the function test_delete_propagation.
    """
    for item in query_list:
        with pytest.raises(model_class.DoesNotExist):
            model_class.objects.get(grenml_id=item['id'])


TEST_CASES = [
    # In the following cases query_list is None and
    # assertion is assert_absence.
    (fixture, delete_list, None, assert_absence)

    for fixture, delete_list in [
        # delete a link
        (
            make_topology_fixture(),
            [make_delete_item(LINKS, 1)],
        ),

        # delete a node
        (
            make_topology_fixture(),
            [
                make_delete_item(NODES, 1),
                make_delete_item(LINKS, 1),
            ],
        ),

        # delete an institution
        (
            make_topology_fixture(),
            [
                make_delete_item(INSTITUTIONS, 2),
                make_delete_item(NODES, 3),
                make_delete_item(NODES, 4),
                make_delete_item(LINKS, 2),
            ],
        ),

        # delete a link in the child topology
        (
            make_nested_topology_fixture(),
            [make_delete_item_for_topology('child_topo', LINKS, 1)],
        ),

        # delete a node in the child topology
        (
            make_nested_topology_fixture(),
            [
                make_delete_item_for_topology('child_topo', NODES, 1),
                make_delete_item_for_topology('child_topo', LINKS, 1),
            ],
        ),

        # Delete an institution in the child topology:
        # all elements in the delete_list (and also the query_list)
        # belong to the institution to be deleted;
        # if we leave any of these elements in the manager, the import
        # will fail because the manager is invalid.
        (
            make_nested_topology_fixture(),
            [
                make_delete_item_for_topology('child_topo', INSTITUTIONS, 2),
                make_delete_item_for_topology('child_topo', NODES, 3),
                make_delete_item_for_topology('child_topo', NODES, 4),
                make_delete_item_for_topology('child_topo', LINKS, 2),
            ],
        ),
    ]
]

# Disabled: delete propagation currently handles institutions,
# links and nodes but not topologies.
CHILD_TOPOLOGY_TEST_CASE = [
    # delete an entire topology
    (
        # fixture
        make_delete_topology_fixture(),

        # delete_list: one element representing the child topology
        [make_delete_item_for_topology('child_topo', TOPOLOGIES, None)],

        # query_list: everything under the child topology
        [
            make_delete_item_for_topology('child_topo', TOPOLOGIES, None),
            make_delete_item_for_topology('child_topo', INSTITUTIONS, 1),
            make_delete_item_for_topology('child_topo', INSTITUTIONS, 2),
            make_delete_item_for_topology('child_topo', NODES, 1),
            make_delete_item_for_topology('child_topo', NODES, 2),
            make_delete_item_for_topology('child_topo', NODES, 3),
            make_delete_item_for_topology('child_topo', NODES, 4),
            make_delete_item_for_topology('child_topo', LINKS, 1),
            make_delete_item_for_topology('child_topo', LINKS, 2),
        ],

        # assertion
        assert_absence,
    ),
]
