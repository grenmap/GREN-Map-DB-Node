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

import network_topology.models as m
from grenml.managers import GRENMLManager
from grenml.models import INSTITUTIONS, NODES, LINKS
from grenml.validation import TopologyValidator


def add_owner_institution(manager):
    """
    Creates an institution in the GRENML manager, makes it the owner
    of the manager's topology.
    """
    institution_id = manager.topology.id + '.institution'
    institution = manager.add_institution(
        id=institution_id,
        name=institution_id,
        latitude=0,
        longitude=0,
    )
    manager.set_primary_owner(institution_id)
    return institution


def add_single_node_to_topology(manager):
    """ Creates one node in the GRENML manager. """

    institution = add_owner_institution(manager)
    node_id = 'N'
    manager.add_node(
        id=node_id,
        name=node_id,
        owners=[institution],
        latitude=0,
        longitude=0,
    )


def add_single_link_to_topology(manager):
    """
    Creates one link in the GRENML manager.

    The manager will not be valid if the link doesn't refer to
    any nodes, so this function makes two nodes first, then uses
    their ids to make the link.
    """
    institution = add_owner_institution(manager)

    def add_node(node_id, longitude):
        return manager.add_node(
            id=node_id,
            name=node_id,
            owners=[institution],
            latitude=0,
            longitude=-10,
        )

    node1_id = add_node('N1', -10)
    node2_id = add_node('N2', 10)

    link_id = 'L'
    manager.add_link(
        id=link_id,
        name=link_id,
        owners=[institution],
        nodes=manager.get_nodes(id__in=[node1_id, node2_id]),
    )


def add_test_institution_to_topology(manager):
    """
    Adds one institution to the manager, different from the institution
    that owns the manager's topology.
    """
    add_owner_institution(manager)

    institution_id = 'test_institution'
    manager.add_institution(
        id=institution_id,
        name=institution_id,
        latitude=0,
        longitude=0,
    )


def shared_object_fixture(add_object_to_topology):
    """
    Creates fixtures for tests in which an object is associated to two
    topologies (parent and child) in the first import, then to one
    topology in the second import.

    Returns a dictionary containing two GRENML managers. One for the
    parent, one for the child topologies.
    """
    topology_id = 'parent_topo'

    parent_validator = TopologyValidator()
    parent_manager = GRENMLManager(
        id=topology_id,
        name=topology_id,
        validator=parent_validator,
    )
    parent_topology = parent_manager.topology
    add_object_to_topology(parent_manager)

    topology_id = 'child_topo'
    child_validator = TopologyValidator()
    child_manager = GRENMLManager(
        id=topology_id,
        name=topology_id,
        validator=child_validator,
    )
    child_topology = child_manager.topology
    add_object_to_topology(child_manager)

    parent_topology.add_topology(child_topology)
    return {
        'parent_manager': parent_manager,
        'child_manager': child_manager,
    }


def shared_object_deleted_from_parent_topo_fixture(add_object_to_topology):
    """
    This combines the shared_object_topology function with another that
    creates a node, link or institution. Shared_object_topology provides
    parent and child managers (each manager contains a topology).

    This function returns an import-delete dictionary in which both
    import and delete managers are the parent.
    """
    fixture = shared_object_fixture(add_object_to_topology)
    return {
        'import_manager': fixture['parent_manager'],
        'delete_manager': fixture['parent_manager'],
    }


def shared_object_deleted_from_child_topo_fixture(add_object_to_topology):
    """
    This combines the shared_object_topology function with another that
    creates a node, link or institution. Shared_object_topology provides
    parent and child managers (each manager contains a topology).

    This function returns a dictionary in which the import manager
    is the parent and the delete manager is the child.
    """
    fixture = shared_object_fixture(add_object_to_topology)
    return {
        'import_manager': fixture['parent_manager'],
        'delete_manager': fixture['child_manager'],
    }


def assert_shared_object_in_single_topo(model_class, query_list):
    """
    Verifies an object is associated to a single topology.
    The query_list should contain two strings. The first is the id
    of the object, the second is the id of the topology.
    """
    obj_id = query_list[0]
    obj = model_class.objects.get(grenml_id=obj_id)
    assert obj

    topo_id = query_list[1]

    # obj.topologies.get() will raise an exception
    # if there are two or more topologies associated to obj
    assert obj.topologies.get().grenml_id == topo_id


SINGLE_INSTITUTION_DELETE_LIST = [{
    'entity': INSTITUTIONS,
    'id': 'test_institution',
    'model_class': m.Institution,
}]
SINGLE_LINK_DELETE_LIST = [{'entity': LINKS, 'id': 'L', 'model_class': m.Link}]
SINGLE_NODE_DELETE_LIST = [{'entity': NODES, 'id': 'N', 'model_class': m.Node}]

TEST_CASES = [
    # import two topologies with the same institution,
    # then remove the institution from the parent topo
    (
        # fixture:
        # the delete_manager contains the parent topology
        shared_object_deleted_from_parent_topo_fixture(
            add_test_institution_to_topology,
        ),

        # delete_list
        SINGLE_INSTITUTION_DELETE_LIST,

        # query_list:
        # the test function removes the institution from
        # the parent topology; it should still exist in the child
        ['test_institution', 'child_topo'],

        # assertion
        assert_shared_object_in_single_topo,
    ),

    # import two topologies with the same institution,
    # then remove the institution from the child topo
    (
        shared_object_deleted_from_child_topo_fixture(
            add_test_institution_to_topology,
        ),
        SINGLE_INSTITUTION_DELETE_LIST,
        ['test_institution', 'parent_topo'],
        assert_shared_object_in_single_topo,
    ),

    # import two topologies with the same link,
    # then remove the link from the parent topo
    (
        shared_object_deleted_from_parent_topo_fixture(
            add_single_link_to_topology,
        ),
        SINGLE_LINK_DELETE_LIST,
        ['L', 'child_topo'],
        assert_shared_object_in_single_topo,
    ),

    # import two topologies with the same link,
    # then remove the link from the child topo
    (
        shared_object_deleted_from_child_topo_fixture(
            add_single_link_to_topology,
        ),
        SINGLE_LINK_DELETE_LIST,
        ['L', 'parent_topo'],
        assert_shared_object_in_single_topo,
    ),

    # import two topologies with the same node,
    # then remove the node from the parent topo
    (
        shared_object_deleted_from_parent_topo_fixture(
            add_single_node_to_topology,
        ),
        SINGLE_NODE_DELETE_LIST,
        ['N', 'child_topo'],
        assert_shared_object_in_single_topo,
    ),

    # import two topologies with the same node,
    # then remove the node from the child topo
    (
        shared_object_deleted_from_child_topo_fixture(
            add_single_node_to_topology,
        ),
        SINGLE_NODE_DELETE_LIST,
        ['N', 'parent_topo'],
        assert_shared_object_in_single_topo,
    ),
]
