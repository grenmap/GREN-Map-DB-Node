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


MATCH_TYPE_CLASS_NAME = 'MatchLinksByID'
ACTION_TYPE_CLASS_NAME = 'MergeLink'
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
def basic_data():
    """
    Creates two links between the same nodes.
    """
    node_a = tm.Node.objects.create(
        name='node_a__Link1',
        latitude=10,
        longitude=10,
    )
    node_b = tm.Node.objects.create(
        name='node_b__Link1',
        latitude=20,
        longitude=20,
    )
    duplicate_link = tm.Link.objects.create(
        grenml_id='Link1',
        name='Link 1',
        short_name='Link1',
        node_a=node_a,
        node_b=node_b,
    )
    target_link = tm.Link.objects.create(
        grenml_id='Link2',
        name='Link 2',
        # Same endpoints as Link1 above
        node_a=node_a,
        node_b=node_b,
    )
    return (duplicate_link, target_link)


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
def test_merge_link(basic_data, merge_rule):
    """
    Executes a rule
    to merge the first link with the second. Then verifies that
    the first link disappeared.
    """
    match_link, merge_into_link = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    merge_rule.ruleset.apply()

    # There should be only one link after running the rule.
    assert tm.Link.objects.count() == 1

    # The one that remains should be the merge_into link.
    assert str(tm.Link.objects.first().grenml_id) == str(merge_into_link.grenml_id)


@pytest.mark.django_db
def test_merge_link_from_child_topology(two_topologies, merge_rule):
    """
    Runs the merge-link Rule merging a Link with another
    Link in its parent Topology, identified by ID and Topology,
    where the IDs remain distinct.
    Verifies that the matched Link is no longer in the database.
    """
    parent_topology, child_topology = two_topologies
    primary_link = parent_topology.links.first()
    duplicate_link = child_topology.links.first()

    # The Links have to have the same endpoints
    # for the Action to proceed.
    duplicate_link.node_a = primary_link.node_a
    duplicate_link.node_b = primary_link.node_b
    duplicate_link.save()

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=primary_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    merge_rule.apply()

    # The duplicate Link should be gone
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(pk=duplicate_link.pk)


@pytest.mark.django_db
def test_merge_link_topology_mismatch(two_topologies, merge_rule):
    """
    Tries to runs the merge-link Rule to merge
    Links, but supplies an incorrect Topology ID to the
    Action, so the Rule should abort.
    """
    parent_topology, child_topology = two_topologies
    primary_link = parent_topology.links.first()
    duplicate_link = child_topology.links.first()

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=primary_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        # Wrong Topology!
        value=child_topology.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded

    # The duplicate Link should still be around
    tm.Link.objects.get(pk=duplicate_link.pk)


@pytest.mark.django_db
def test_merge_link_from_child_topology_same_id(two_topologies, merge_rule):
    """
    Runs the merge-link rule merging a Link with another
    Link in its child Topology, identified by ID and Topology,
    where the IDs are identical.
    Verifies that the matched Link is no longer in the database.
    """
    parent_topology, child_topology = two_topologies
    primary_link = parent_topology.links.first()
    duplicate_link = child_topology.links.first()

    # The Links have to have the same endpoints
    # for the Action to proceed.
    duplicate_link.node_a = primary_link.node_a
    duplicate_link.node_b = primary_link.node_b
    duplicate_link.save()

    # Create another Link in the child Topology with the same
    # GRENML ID as the primary one in the parent Topology,
    # to challenge the Action's topology discrimination
    extra_link = tm.Link.objects.create(
        grenml_id=primary_link.grenml_id,
        name='Another Link',
        short_name='AnotherLink',
        node_a=duplicate_link.node_a,
        node_b=duplicate_link.node_b,
    )
    extra_link.topologies.add(child_topology)

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=primary_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    merge_rule.apply()

    # The duplicate Link should be gone
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(pk=duplicate_link.pk)


@pytest.mark.django_db
def test_merge_into_with_different_endpoints_with_exception(basic_data, merge_rule):
    """
    Creates two links between different nodes. Executes a rule
    to merge the first link with the second. Expects an exception
    when apply a rule
    """
    match_link, _ = basic_data

    # New endpoints, different from Link1/match_link
    node_c = tm.Node.objects.create(
        name='node_c__Link3',
        latitude=30,
        longitude=30,
    )
    node_d = tm.Node.objects.create(
        name='node_d__Link3',
        latitude=40,
        longitude=40,
    )
    merge_into_link = tm.Link.objects.create(
        grenml_id='Link3',
        name='Link 3',
        node_a=node_c,
        node_b=node_d,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_merge_into_with_different_endpoints_no_exception(basic_data, merge_rule):
    """
    Creates two links between different nodes. Executes a rule
    to merge the first link with the second. Expects no exception
    when applied as part of a Ruleset
    """
    match_link, _ = basic_data

    # New endpoints, different from Link1/match_link
    node_c = tm.Node.objects.create(
        name='node_c__Link3',
        latitude=30,
        longitude=30,
    )
    node_d = tm.Node.objects.create(
        name='node_d__Link3',
        latitude=40,
        longitude=40,
    )
    merge_into_link = tm.Link.objects.create(
        grenml_id='Link3',
        name='Link 3',
        node_a=node_c,
        node_b=node_d,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    merge_rule.ruleset.apply()


@pytest.mark.django_db
def test_no_links_no_exception(basic_data, merge_rule):
    """
    Attempts to execute a merge-link Rule that doesn't match
    any links. The Rule should proceed silently.
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
def test_no_links_no_exception_in_ruleset(basic_data, merge_rule):
    """
    Attempts to execute a merge-link Rule that doesn't match
    any links. Expects no exception when run in Ruleset
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
    Calls a merge-link rule in which the matched link and
    the merge_into link are the same. Expects an exception
    when run in rule
    """
    match_link, merge_into_link = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_match_equal_to_merge_into_no_exception(basic_data, merge_rule):
    """
    Calls a merge-link rule in which the matched link and
    the merge_into link are the same. Expects no exception
    when run in a ruleset
    """
    match_link, merge_into_link = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    merge_rule.ruleset.apply()


@pytest.mark.django_db
def test_merge_link_extra_fields(basic_data, merge_rule):
    """
    Runs the merge_link rule.
    Verifies that the match link is no longer in the
    database and that the extra informations are associated
    to the merge_into link
    """
    match_link, merge_into_link = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the match_link anymore
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(grenml_id=match_link.grenml_id)

    merge_into_link_updated = tm.Link.objects.get(
        grenml_id=merge_into_link.grenml_id,
    )

    # The short name should be associated to the
    # merge_into link
    assert merge_into_link_updated.short_name == match_link.short_name


@pytest.mark.django_db
def test_merge_link_with_owner(basic_data, merge_rule):
    """
    Runs the merge_link rule.
    Verifies that the match link is no longer in the
    database and that its owner is associated
    to the merge_into link
    """
    match_link, merge_into_link = basic_data

    # Owner of the Link
    match_link_owner = tm.Institution.objects.create(
        grenml_id='Inst1',
        name='Inst 1',
        latitude=0,
        longitude=0,
    )
    match_link.owners.add(match_link_owner)

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find match_link anymore
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(grenml_id=match_link.grenml_id)

    merge_into_link_updated = tm.Link.objects.get(
        grenml_id=merge_into_link.grenml_id,
    )

    # The match link owner should be associated to the
    # merge_into link
    assert merge_into_link_updated.owners.count() == 1
    assert str(merge_into_link_updated.owners.first().grenml_id) == str(match_link_owner.grenml_id)


@pytest.mark.django_db
def test_merge_link_with_properties_not_tags(basic_data, merge_rule):
    """
    Runs the merge_link rule.
    Verifies that properties in the match link is no longer
    in the database and that the properties in the match
    link are merged into the merge_into link
    """
    match_link, merge_into_link = basic_data

    tm.Property.objects.create(
        name='url',
        value='http://localhost',
        property_for=match_link,
    )
    tm.Property.objects.create(
        name='description',
        value='This is a description',
        property_for=match_link,
    )
    tm.Property.objects.create(
        name='url',
        value='http://mytest.ca',
        property_for=merge_into_link,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the duplicated
    # property of the match link
    with pytest.raises(tm.Property.DoesNotExist):
        tm.Property.objects.get(
            name='url',
            value='http://localhost',
        )

    # The non-duplicated property should be associated with
    # merge_into link
    assert str(tm.Property.objects.get(
        name='description',
    ).property_for.grenml_id) == str(merge_into_link.grenml_id)

    # The duplicated property should still be associated with
    # merge_into link
    assert str(tm.Property.objects.get(
        name='url',
    ).property_for.grenml_id) == str(merge_into_link.grenml_id)


@pytest.mark.django_db
def test_merge_link_with_properties_tags(basic_data, merge_rule):
    """
    Runs the merge_link rule.
    Verifies that properties in the match link is no longer
    in the database and that the properties for tag in the match
    link are merged into the merge_into link
    """
    match_link, merge_into_link = basic_data

    tm.Property.objects.create(
        name='tag',
        value='NREN',
        property_for=match_link,
    )
    tm.Property.objects.create(
        name='tag',
        value='MyISP',
        property_for=match_link,
    )
    tm.Property.objects.create(
        name='tag',
        value='NREN',
        property_for=merge_into_link,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_link.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the duplicated property
    # of the match link
    with pytest.raises(tm.Property.DoesNotExist):
        tm.Property.objects.get(
            name='tag',
            value='NREN',
            property_for=match_link,
        )

    # The non-duplicated property should be associated with
    # the merge_into link
    assert str(tm.Property.objects.get(
        name='tag', value='MyISP',
    ).property_for.grenml_id) == str(merge_into_link.grenml_id)

    # The duplicated property should still be associated with
    # the merge_into link
    assert str(tm.Property.objects.get(
        name='tag', value='NREN',
    ).property_for.grenml_id) == str(merge_into_link.grenml_id)
