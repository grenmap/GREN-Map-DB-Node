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

from network_topology import models as tm
from collation import models as cm


MATCH_TYPE_CLASS_NAME = 'MatchNodesByIDDuplicate'
ACTION_TYPE_CLASS_NAME = 'KeepNewestNode'
ID_KEY = 'ID'
TOPOLOGY_ID_KEY = 'Topology ID'


@pytest.fixture
def keep_newest_rule():
    """
    Sets up a Ruleset and a Rule, with a Match By ID MatchCriterion
    and a keep_newest Action based on constants at the top of the file.
    """
    ruleset = cm.Ruleset.objects.create(name='Test Ruleset')
    rule = cm.Rule.objects.create(ruleset=ruleset, name='Test KeepNewest Rule')
    match_type = cm.MatchType.objects.get(class_name=MATCH_TYPE_CLASS_NAME)
    cm.MatchCriterion.objects.create(match_type=match_type, rule=rule)
    action_type = cm.ActionType.objects.get(class_name=ACTION_TYPE_CLASS_NAME)
    cm.Action.objects.create(action_type=action_type, rule=rule)
    return rule


@pytest.fixture
def normal_usage_fixture():
    """
    Sets up some network elements for testing the KeepNewestNode
    ActionType.  Creates three Nodes:
        - node 1
        - node 2
        - newest node 1
    Creates a link between node 1 and node 2.
    Does not establish any Topologies.
    """
    node_1 = tm.Node.objects.create(
        name='node 1',
        grenml_id='1234',
        latitude=10,
        longitude=10,
    )
    node_2 = tm.Node.objects.create(
        name='node 2',
        grenml_id='1122',
        latitude=20,
        longitude=20,
    )
    newest = tm.Node.objects.create(
        name='newest node 1',
        grenml_id='1234',
        latitude=30,
        longitude=30,
    )

    # Add a Property to one of the Nodes
    tm.Property.objects.create(
        name='tag',
        value='node_1_property',
        property_for=node_1,
    )

    # Add a link
    tm.Link.objects.create(
        grenml_id='1',
        name='link',
        node_a=node_1,
        node_b=node_2,
    )

    return (node_1, node_2, newest)


@pytest.fixture
def two_topologies(normal_usage_fixture):
    """
    Populates the database with the contents of normal_usage_fixture
    placed into a Topology, and also a child Topology with an
    additional Node that will become the "newest" (by PK).
    """
    topology_one = tm.Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    # Place contents of normal_usage_fixture into Topology 1
    for node in tm.Node.objects.all():
        node.topologies.add(topology_one)
    for link in tm.Link.objects.all():
        link.topologies.add(topology_one)

    topology_two = tm.Topology.objects.create(
        grenml_id='Topo2',
        name='Topology 2',
        parent=topology_one,
    )
    new_node = tm.Node.objects.create(
        name='new newest',
        grenml_id='1234',
        latitude=40,
        longitude=40,
    )
    new_node.topologies.add(topology_two)

    return (topology_one, topology_two)


@pytest.mark.django_db
def test_keep_newest_node(normal_usage_fixture, keep_newest_rule):
    """
    Runs a rule containing a KeepNewestNode Action.
    Prepares the database with the normal usage fixture.
    Verifies that the target node is no longer in the database
    and that the nodes and link are associated to the newest.
    """
    node_1, node_2, newest = normal_usage_fixture

    # Check the first node's property is present..
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 1

    keep_newest_rule.ruleset.apply()

    # It should not be possible to find node_1
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(name=node_1.name)

    # The link should be associated
    # to the newest node.
    for link in tm.Link.objects.all():
        assert link.node_a.name == newest.name

    # The property should have been deleted
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 0


@pytest.mark.django_db
def test_keep_newest_node_with_topologies(two_topologies, keep_newest_rule):
    """
    Runs the KeepNewestNode Rule replacing all Nodes
    in the parent Topology with the newest one in the child.
    """
    parent_topology, child_topology = two_topologies
    newest_node = child_topology.nodes.first()

    keep_newest_rule.apply()

    # Only two Nodes should be left
    nodes = tm.Node.objects.all()
    assert nodes.count() == 2

    # The Link in parent_topology should be associated
    # with the newest node now.
    parent_topology = tm.Topology.objects.get(pk=parent_topology.pk)
    for link in parent_topology.links.all():
        assert link.node_a.pk == newest_node.pk
