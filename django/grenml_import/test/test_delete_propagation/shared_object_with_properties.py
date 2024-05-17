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

from grenml.managers import GRENMLManager
from grenml.validation import TopologyValidator
from .shared_object import (
    add_owner_institution,
    SINGLE_INSTITUTION_DELETE_LIST,
    SINGLE_LINK_DELETE_LIST,
    SINGLE_NODE_DELETE_LIST,
)


def shared_object_with_property_fixture(add_object):
    """
    This function creates a fixture which consists of a parent and
    three child topologies. The add_object argument should be a
    function that will create a network element in each of the children.
    Each occurrence of the element will have a unique property.

    The fixture makes it possible to verify that the server retains the
    properties of an element that appears several times in the imported
    file.

    The return value is a dictionary containing an import manager
    (parent topology) and a delete manager (second child).
    """
    def make_topology(topology_id, parent_topology=None, property_name=None):
        validator = TopologyValidator()
        manager = GRENMLManager(
            id=topology_id,
            name=topology_id,
            validator=validator,
        )
        owner_institution = add_owner_institution(manager)

        if parent_topology:
            add_object(manager, owner_institution, property_name)
            parent_topology.add_topology(manager.topology)

        return manager

    parent_manager = make_topology('parent_topo')
    parent_topology = parent_manager.topology

    make_topology('child1_topo', parent_topology, 'property1')
    child2_manager = make_topology('child2_topo', parent_topology, 'property2')
    make_topology('child3_topo', parent_topology, 'property3')

    return {
        'import_manager': parent_manager,
        'delete_manager': child2_manager,
    }


def shared_node_with_property_fixture():
    """
    Uses shared_object_with_property_fixture with a function
    that creates one node in the child topologies.
    """
    def add_node(manager, owner_institution, property_name):
        node_id = 'N'
        manager.add_node(
            id=node_id,
            name=node_id,
            owners=[owner_institution],
            latitude=0,
            longitude=0,
        )
        property_value = property_name + '_value'
        manager.get_node(id=node_id).add_property(property_name, property_value)

    return shared_object_with_property_fixture(add_node)


def shared_link_with_property_fixture():
    """
    Uses shared_object_with_property_fixture with a function
    that creates one link (along with the two nodes at its endpoints)
    in the child topologies.
    """
    def add_link(manager, owner_institution, property_name):
        node1_id = 'N1'
        manager.add_node(
            id=node1_id,
            name=node1_id,
            owners=[owner_institution],
            latitude=0,
            longitude=-10,
        )

        node2_id = 'N2'
        manager.add_node(
            id=node2_id,
            name=node2_id,
            owners=[owner_institution],
            latitude=0,
            longitude=10,
        )

        link_id = 'L'
        manager.add_link(
            id=link_id,
            name=link_id,
            owners=[owner_institution],
            nodes=manager.get_nodes(id__in=[node1_id, node2_id]),
        )
        property_value = property_name + '_value'
        manager.get_link(id=link_id).add_property(property_name, property_value)

    return shared_object_with_property_fixture(add_link)


def shared_institution_with_property_fixture():
    """
    Uses shared_object_with_property_fixture with a function
    that creates one institution (different from the manager's owner)
    in the child topologies.
    """
    def add_institution(manager, owner_institution, property_name):
        institution_id = 'test_institution'
        manager.add_institution(
            id=institution_id,
            name=institution_id,
            latitude=0,
            longitude=0,
        )
        property_value = property_name + '_value'
        manager.get_institution(
            id=institution_id,
        ).add_property(
            property_name,
            property_value,
        )

    return shared_object_with_property_fixture(add_institution)


def assert_shared_object_properties(model_class, query_list):
    """
    This function asserts that the object associated to the child
    topologies exists in the server and that it has the properties
    we expect. The first item in the query_list is the object id.
    All other items are the properties that must exist.
    """
    obj_id = query_list[0]
    obj = model_class.objects.get(grenml_id=obj_id)
    assert obj

    property_ids = set(query_list[1:])
    assert {p.name for p in obj.properties.all()} == property_ids


TEST_CASES = [
    # import three topologies with the same institution
    # (which has a different property in each topo),
    # delete the institution in the second topo
    (
        shared_institution_with_property_fixture(),
        SINGLE_INSTITUTION_DELETE_LIST,
        ['test_institution', 'property1', 'property3'],
        assert_shared_object_properties,
    ),

    # import three topologies with the same link
    # (which has a different property in each topo),
    # delete the link in the second topo
    (
        shared_link_with_property_fixture(),
        SINGLE_LINK_DELETE_LIST,
        ['L', 'property1', 'property3'],
        assert_shared_object_properties,
    ),

    # import three topologies with the same node
    # (which has a different property in each topo),
    # delete the node in the second topo
    (
        shared_node_with_property_fixture(),
        SINGLE_NODE_DELETE_LIST,
        ['N', 'property1', 'property3'],
        assert_shared_object_properties,
    ),
]

# Disabled: there should be an id collision rule that determines what
# properties an object appearing in two or more topologies will have.
TEST_CASES = []
