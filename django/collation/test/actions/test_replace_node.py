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

from network_topology import models as tm
from collation import models as cm


MATCH_TYPE_CLASS_NAME = 'MatchNodesByID'
ACTION_TYPE_CLASS_NAME = 'ReplaceNode'
ID_KEY = 'ID'
TOPOLOGY_ID_KEY = 'Topology ID'


@pytest.fixture
def replace_rule():
    """
    Sets up a Ruleset and a Rule, with a Match By ID MatchCriterion
    and a Replace Action based on constants at the top of the file.
    """
    ruleset = cm.Ruleset.objects.create(name='Test Ruleset')
    rule = cm.Rule.objects.create(ruleset=ruleset, name='Test Replace Rule')
    match_type = cm.MatchType.objects.get(class_name=MATCH_TYPE_CLASS_NAME)
    cm.MatchCriterion.objects.create(match_type=match_type, rule=rule)
    action_type = cm.ActionType.objects.get(class_name=ACTION_TYPE_CLASS_NAME)
    cm.Action.objects.create(action_type=action_type, rule=rule)
    return rule


@pytest.fixture
def normal_usage_fixture():
    """
    Sets up four nodes for testing the replace node action type.
    The target is connected to two neighbor nodes and has one property.
    """
    target_node_name = 'target_node'
    target_node = tm.Node.objects.create(
        name=target_node_name,
        latitude=10, longitude=10
    )
    target_node_property = tm.Property.objects.create(
        name='tag',
        value='target_node_property',
        property_for=target_node,
    )
    target_node_property.save()
    neighbor1 = tm.Node.objects.create(
        name='neighbor1',
        latitude=10, longitude=20
    )
    tm.Link.objects.create(
        grenml_id='1', name='link1',
        node_a=target_node, node_b=neighbor1,
    )
    neighbor2 = tm.Node.objects.create(
        name='neighbor2',
        latitude=20, longitude=10
    )
    tm.Link.objects.create(
        grenml_id='2', name='link1',
        node_a=neighbor2, node_b=target_node,
    )
    replacement_node = tm.Node.objects.create(
        name='replacement_node',
        latitude=20, longitude=20
    )
    return (target_node, replacement_node)


@pytest.fixture
def two_topologies():
    """
    Populates the database with a child Topology and some basic data.
    """
    topology_one = tm.Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    parent_institution = tm.Institution.objects.create(
        name='Parent Inst',
        short_name='ParentInst',
        latitude=10,
        longitude=10,
    )
    parent_institution.topologies.add(topology_one)
    node_a = tm.Node.objects.create(name='node_a', latitude=80, longitude=80)
    node_a.owners.add(parent_institution)
    node_a.topologies.add(topology_one)
    node_b = tm.Node.objects.create(name='node_b', latitude=90, longitude=90)
    node_b.owners.add(parent_institution)
    node_b.topologies.add(topology_one)
    parent_link = tm.Link.objects.create(
        grenml_id='1',
        name='link',
        node_a=node_a,
        node_b=node_b,
    )
    parent_link.owners.add(parent_institution)
    parent_link.topologies.add(topology_one)

    topology_two = tm.Topology.objects.create(
        grenml_id='Topo2',
        name='Topology 2',
        parent=topology_one,
    )
    child_institution = tm.Institution.objects.create(
        name='Child Inst',
        short_name='ChildInst',
        latitude=30,
        longitude=30,
    )
    child_institution.topologies.add(topology_two)
    node_c = tm.Node.objects.create(name='node_c', latitude=60, longitude=60)
    node_c.owners.add(child_institution)
    node_c.topologies.add(topology_two)
    node_d = tm.Node.objects.create(name='node_d', latitude=70, longitude=70)
    node_d.owners.add(child_institution)
    node_d.topologies.add(topology_two)
    child_link = tm.Link.objects.create(
        grenml_id='2',
        name='another link',
        node_a=node_c,
        node_b=node_d,
    )
    child_link.owners.add(child_institution)
    child_link.topologies.add(topology_two)

    return (topology_one, topology_two)


@pytest.mark.django_db
def test_replace_node(normal_usage_fixture, replace_rule):
    """
    The normal usage fixture prepares the database for this test,
    which uses a rule containing a replace node action type.
    The test succeeds if the rule removes the target node
    from the database and if it reconnects the target's neighbors
    to the replacement.
    """
    target_node, replacement_node = normal_usage_fixture

    # Check for the presence of the property associated to the node.
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 1

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=target_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=replacement_node.grenml_id,
    )
    replace_rule.apply()

    # The target node should no longer be in the database.
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(name=target_node.name)

    # The links connecting the target node to its neighbors
    # should now have the substitute node as an endpoint.
    link1 = tm.Link.objects.get(grenml_id='1')
    assert link1.node_a.grenml_id == str(replacement_node.grenml_id)
    link2 = tm.Link.objects.get(grenml_id='2')
    assert link2.node_b.grenml_id == str(replacement_node.grenml_id)

    # The property should have been deleted.
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 0


@pytest.mark.django_db
def test_replace_node_with_child_version(two_topologies, replace_rule):
    """
    Runs the replace-node rule replacing a Node with another
    Node in its child Topology, identified by ID and Topology,
    where the IDs remain distinct.
    Verifies that the matched Node is no longer in the database
    and that the Link endpoint associations are moved.
    """
    parent_topology, child_topology = two_topologies
    good_node = parent_topology.nodes.get(name='node_a')
    better_node = child_topology.nodes.get(name='node_c')

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=good_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=better_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=child_topology.grenml_id,
    )
    replace_rule.apply()

    # The duplicate Node should be gone
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(pk=good_node.pk)

    # The Link previously connecting to good_node should now connect
    # to better_node.
    link1 = parent_topology.links.first()
    assert link1.node_a == better_node
    # (The one below should not have changed)
    link2 = child_topology.links.first()
    assert link2.node_a == better_node


@pytest.mark.django_db
def test_replace_node_topology_mismatch(two_topologies, replace_rule):
    """
    Tries to runs the replace-node Rule to replace a
    Node, but supplies an incorrect Topology ID to the
    Action, so the Rule should abort.
    """
    parent_topology, child_topology = two_topologies
    good_node = parent_topology.nodes.get(name='node_a')
    better_node = child_topology.nodes.get(name='node_c')

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=good_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=better_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        # Wrong Topology!
        value=parent_topology.grenml_id,
    )
    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded

    # The duplicate Node should still be around
    tm.Node.objects.get(pk=good_node.pk)


@pytest.mark.django_db
def test_replace_node_with_child_version_same_id(two_topologies, replace_rule):
    """
    Runs the replace-node rule merging a Node with another
    Node from its child Topology, identified by ID and Topology,
    where the IDs are identical.
    Verifies that the matched Node is no longer in the database
    and that the Link endpoint associations are moved.
    """
    parent_topology, child_topology = two_topologies
    good_node = parent_topology.nodes.get(name='node_a')
    better_node = child_topology.nodes.get(name='node_c')

    # Set an otherwise-uninvolved Node's GRENML ID to match the
    # target, to challenge the Action's topology discrimination.
    extra_node = parent_topology.nodes.get(name='node_b')
    extra_node.grenml_id = better_node.grenml_id
    extra_node.save()

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=good_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=better_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=child_topology.grenml_id,
    )
    replace_rule.apply()

    # The duplicate Node should be gone
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(pk=good_node.pk)


@pytest.mark.django_db
def test_no_nodes_no_exception(replace_rule):
    """
    Attempts to execute a replace-node rule that doesn't match
    any nodes. The Rule should execute silently.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value='1',
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value='2',
    )
    replace_rule.apply()


@pytest.mark.django_db
def test_no_nodes_no_exception_in_ruleset(replace_rule):
    """
    Attempts to execute a replace-node Rule that doesn't match
    any nodes. Expects no exception when run in a Ruleset.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value='1',
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value='2',
    )
    replace_rule.ruleset.apply()


@pytest.fixture
def single_node():
    """
    Creates a single node for testing the behaviour of replace node
    when target and substitute are the same.
    """
    return tm.Node.objects.create(
        name='target',
        latitude=10,
        longitude=10,
    )


@pytest.mark.django_db
def test_match_equal_to_replacement_with_exception(single_node, replace_rule):
    """
    The execution of a rule that contains a replace node action type
    and matches a node which is also the replacement should return
    None (after an internal Exception is intercepted).
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=single_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=single_node.grenml_id,
    )
    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_match_equal_to_replacement_no_exception(single_node, replace_rule):
    """
    The execution of a rule that contains a replace node action type
    and matches a node which is also the replacement should not raise
    an exception when apply a ruleset.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=single_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=single_node.grenml_id,
    )
    replace_rule.ruleset.apply()
