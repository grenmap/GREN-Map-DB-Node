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
ACTION_TYPE_CLASS_NAME = 'MergeNode'
ID_KEY = 'ID'
TOPOLOGY_ID_KEY = 'Topology ID'


@pytest.fixture
def merge_rule():
    """
    Sets up a Ruleset and a Rule, with a Match By ID MatchCriterion
    and a Merge Action based on constants at the top of the file.
    """
    ruleset = cm.Ruleset.objects.create(name='Test Ruleset')
    rule = cm.Rule.objects.create(ruleset=ruleset, name='Test Replace Rule')
    match_type = cm.MatchType.objects.get(class_name=MATCH_TYPE_CLASS_NAME)
    cm.MatchCriterion.objects.create(match_type=match_type, rule=rule)
    action_type = cm.ActionType.objects.get(class_name=ACTION_TYPE_CLASS_NAME)
    cm.Action.objects.create(action_type=action_type, rule=rule)
    return rule


@pytest.fixture
def basic_data(merge_rule):
    """
    Creates four nodes in the database. One of the first three
    connects to the other two. The fourth is the merge_into node
    """
    duplicate_node = tm.Node.objects.create(
        name='Dupe Node',
        short_name='DupeNode',
        latitude=10,
        longitude=10
    )
    neighbor1 = tm.Node.objects.create(
        name='neighbor1',
        latitude=10, longitude=20
    )
    tm.Link.objects.create(
        grenml_id='1', name='link1',
        node_a=duplicate_node, node_b=neighbor1,
    )
    neighbor2 = tm.Node.objects.create(
        name='neighbor2',
        latitude=20, longitude=10
    )
    tm.Link.objects.create(
        grenml_id='2', name='link1',
        node_a=neighbor2, node_b=duplicate_node,
    )
    target_node = tm.Node.objects.create(
        name='Target Node',
        # different from duplicate_node's
        latitude=20,
        longitude=20
    )
    return (duplicate_node, target_node)


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
def test_merge_node(basic_data, merge_rule):
    """
    Runs the merge-node rule.
    Verifies that the match node is no longer in the database
    and that the links are associated to the merge_into node
    """
    match_node, merge_into_node = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_node.grenml_id,
    )
    merge_rule.ruleset.apply()

    # The match node should no longer be in the database.
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(grenml_id=match_node.grenml_id)

    # The links connecting the match node to its neighbors
    # should now have the merge_into node as an endpoint.
    link1 = tm.Link.objects.get(grenml_id='1')
    assert link1.node_a.grenml_id == str(merge_into_node.grenml_id)
    link2 = tm.Link.objects.get(grenml_id='2')
    assert link2.node_b.grenml_id == str(merge_into_node.grenml_id)


@pytest.mark.django_db
def test_merge_node_from_parent_topology(two_topologies, merge_rule):
    """
    Runs the merge-node rule merging a Node with another
    Node in its child Topology, identified by ID and Topology,
    where the IDs remain distinct.
    Verifies that the matched Node is no longer in the database
    and that the Link endpoint associations are moved.
    """
    parent_topology, child_topology = two_topologies
    good_node = parent_topology.nodes.get(name='node_a')
    better_node = child_topology.nodes.get(name='node_c')

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=good_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=better_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=child_topology.grenml_id,
    )
    merge_rule.apply()

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
def test_merge_node_topology_mismatch(two_topologies, merge_rule):
    """
    Tries to runs the merge-node Rule to merge
    Nodes, but supplies an incorrect Topology ID to the
    Action, so the Rule should abort.
    """
    parent_topology, child_topology = two_topologies
    good_node = parent_topology.nodes.get(name='node_a')
    better_node = child_topology.nodes.get(name='node_c')

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=good_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=better_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        # Wrong Topology!
        value=parent_topology.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded

    # The duplicate Node should still be around
    tm.Node.objects.get(pk=good_node.pk)


@pytest.mark.django_db
def test_merge_node_from_child_topology_same_id(two_topologies, merge_rule):
    """
    Runs the merge-node rule merging a Node with another
    Node in its child Topology, identified by ID and Topology,
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
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=good_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=better_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=child_topology.grenml_id,
    )
    merge_rule.apply()

    # The duplicate Node should be gone
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(pk=good_node.pk)


@pytest.mark.django_db
def test_no_nodes_no_exception(basic_data, merge_rule):
    """
    Attempts to execute a merge-node rule that doesn't match
    any nodes. The Rule should proceed silently.
    """
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value='foo',
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value='bar',
    )
    merge_rule.apply()


@pytest.mark.django_db
def test_no_nodes_no_exception_in_ruleset(basic_data, merge_rule):
    """
    Attempts to execute a merge-node Rule that doesn't match
    any nodes. Expects no exception when run in a Ruleset.
    """
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value='foo',
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value='bar',
    )
    merge_rule.ruleset.apply()


@pytest.mark.django_db
def test_match_equal_to_merge_into_with_exception(basic_data, merge_rule):
    """
    Checks that the merge-node Rule does not run when the matched
    node and the merge_into node are the same. Expects the Rule to
    fail and reflect this in the log.
    """
    match_node, _ = basic_data
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_match_equal_to_merge_into_no_exception(basic_data, merge_rule):
    """
    Checks that the merge-node Rule does not run when the matched
    node and the merge_into node are the same. Expect silent failure
    when run in a Ruleset.
    """
    match_node, _ = basic_data
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    merge_rule.ruleset.apply()


@pytest.mark.django_db
def test_merge_node_extra_fields(basic_data, merge_rule):
    """
    Runs the merge_node rule.
    Verifies that the match node is no longer in the
    database and that the extra informations are associated
    to the merge_into node
    """
    match_node, merge_into_node = basic_data
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_node.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the match
    # node.
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(grenml_id=match_node.grenml_id)

    merge_into_node_updated = tm.Node.objects.get(
        grenml_id=merge_into_node.grenml_id,
    )

    # The short name should be associated to the
    # merge_into node
    assert merge_into_node_updated.short_name == match_node.short_name

    # The latitude should not be changed for the
    # merge_into node
    assert merge_into_node_updated.latitude == merge_into_node.latitude


@pytest.mark.django_db
def test_merge_node_with_owner(basic_data, merge_rule):
    """
    Runs the merge_node rule.
    Verifies that the match node is no longer in the
    database and that its owner is associated
    to the merge_into node
    """
    match_node, merge_into_node = basic_data

    # Set up an owner
    match_node_owner_id = '123'
    match_node_owner = tm.Institution.objects.create(
        grenml_id=match_node_owner_id,
        name='owner 1',
        latitude=10,
        longitude=20,
    )
    match_node.owners.add(match_node_owner)

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_node.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the match node
    with pytest.raises(tm.Node.DoesNotExist):
        tm.Node.objects.get(grenml_id=match_node.grenml_id)

    merge_into_node_updated = tm.Node.objects.get(
        grenml_id=merge_into_node.grenml_id,
    )

    # The match node owner should be associated to the
    # merge_into node
    assert merge_into_node_updated.owners.count() == 1
    assert str(merge_into_node_updated.owners.first().grenml_id) == match_node_owner_id


@pytest.mark.django_db
def test_merge_node_with_properties_not_tags(basic_data, merge_rule):
    """
    Runs the merge_node Rule.
    Verifies that properties in the match node is no longer
    in the database and that the properties in the match
    node are merged into the merge_into node
    """
    match_node, merge_into_node = basic_data

    tm.Property.objects.create(
        name='url',
        value='http://localhost',
        property_for=match_node,
    )
    tm.Property.objects.create(
        name='description',
        value='This is a description',
        property_for=match_node,
    )
    tm.Property.objects.create(
        name='url',
        value='http://mytest.ca',
        property_for=merge_into_node,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_node.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the duplicated
    # property of the match node
    with pytest.raises(tm.Property.DoesNotExist):
        tm.Property.objects.get(
            name='url',
            value='http://localhost',
        )

    # The non-duplicated property should be associated with
    # the merge_into node
    assert str(tm.Property.objects.get(
        name='description'
    ).property_for.grenml_id) == str(merge_into_node.grenml_id)

    # The duplicated property should still be associated with
    # the merge_into node
    assert str(tm.Property.objects.get(
        name='url'
    ).property_for.grenml_id) == str(merge_into_node.grenml_id)


@pytest.mark.django_db
def test_merge_node_with_properties_tags(basic_data, merge_rule):
    """
    Runs the merge_node Rule.
    Verifies that properties in the match node is no longer
    in the database and that the properties for tag in the match
    node are merged into the merge_into node
    """
    match_node, merge_into_node = basic_data

    tm.Property.objects.create(
        name='tag',
        value='NREN',
        property_for=match_node,
    )
    tm.Property.objects.create(
        name='tag',
        value='MyISP',
        property_for=match_node,
    )
    tm.Property.objects.create(
        name='tag',
        value='NREN',
        property_for=merge_into_node,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_node.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_node.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the duplicated property
    # of the match node
    with pytest.raises(tm.Property.DoesNotExist):
        tm.Property.objects.get(
            name='tag',
            value='NREN',
            property_for=match_node,
        )

    # The non-duplicated property should be associated with
    # the merge_into node
    assert str(tm.Property.objects.get(
        name='tag', value='MyISP',
    ).property_for.grenml_id) == str(merge_into_node.grenml_id)

    # The duplicated property should still be associated with
    # the merge_into node
    assert str(tm.Property.objects.get(
        name='tag', value='NREN',
    ).property_for.grenml_id) == str(merge_into_node.grenml_id)
