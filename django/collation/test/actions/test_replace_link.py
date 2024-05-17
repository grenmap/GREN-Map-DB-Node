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
ACTION_TYPE_CLASS_NAME = 'ReplaceLink'
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
    """ Creates two links between the same nodes. """

    replaced_link_name = 'link_to_be_replaced'
    replaced_link_id = '1'
    node_a = tm.Node.objects.create(
        name='node_a__' + replaced_link_name,
        latitude=10,
        longitude=20,
    )
    node_b = tm.Node.objects.create(
        name='node_b__' + replaced_link_name,
        latitude=30,
        longitude=40,
    )
    target_link = tm.Link.objects.create(
        grenml_id=replaced_link_id,
        name=replaced_link_name,
        node_a=node_a,
        node_b=node_b,
    )
    target_link_property = tm.Property.objects.create(
        name='tag',
        value='target_link_property',
        property_for=target_link,
    )
    target_link_property.save()

    substitute_link_name = 'substitute_link'
    substitute_link_id = '2'
    substitute_link = tm.Link.objects.create(
        grenml_id=substitute_link_id,
        name=substitute_link_name,
        node_a=node_a,
        node_b=node_b,
    )

    return (target_link, substitute_link)


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
def test_replace_link(normal_usage_fixture, replace_rule):
    """
    The normal usage fixture provides target and replacement links.
    This test executes a replace link rule on them, then it verifies
    the target is no longer in the database.
    """
    # Check for two links before running the rule.
    all_links = tm.Link.objects.all()
    assert len(all_links) == 2

    # Check that one property exists.
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 1

    target_link, replacement_link = normal_usage_fixture

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=target_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=replacement_link.grenml_id,
    )
    replace_rule.ruleset.apply()

    # There should be only one link after running the rule.
    all_links = tm.Link.objects.all()
    assert len(all_links) == 1

    # The one that remains should be the substitute link.
    link = all_links[0]
    assert link.grenml_id == replacement_link.grenml_id

    # There should not be any properties.
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 0


@pytest.mark.django_db
def test_replace_link_with_parent_version(two_topologies, replace_rule):
    """
    Runs the replace-link Rule replacing a Link with another
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
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=primary_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    replace_rule.apply()

    # The duplicate Link should be gone
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(pk=duplicate_link.pk)


@pytest.mark.django_db
def test_replace_link_topology_mismatch(two_topologies, replace_rule):
    """
    Tries to runs the replace-link Rule to replace a
    Link, but supplies an incorrect Topology ID to the
    Action, so the Rule should abort.
    """
    parent_topology, child_topology = two_topologies
    primary_link = parent_topology.links.first()
    duplicate_link = child_topology.links.first()

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=primary_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        # Wrong Topology!
        value=child_topology.grenml_id,
    )
    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded

    # The duplicate Link should still be around
    tm.Link.objects.get(pk=duplicate_link.pk)


@pytest.mark.django_db
def test_replace_link_with_parent_version_same_id(two_topologies, replace_rule):
    """
    Runs the replace-link rule replacing a Link with another
    Link from its parent Topology, identified by ID and Topology,
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
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=primary_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    replace_rule.apply()

    # The duplicate Link should be gone
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(pk=duplicate_link.pk)


@pytest.fixture
def different_endpoints_fixture():
    """ Creates two links between different nodes. """

    replaced_link_name = 'link_to_be_replaced'
    replaced_link_id = '1'
    node_a = tm.Node.objects.create(
        name='node_a__' + replaced_link_name,
        latitude=10,
        longitude=20,
    )
    node_b = tm.Node.objects.create(
        name='node_b__' + replaced_link_name,
        latitude=30,
        longitude=40,
    )
    target_link = tm.Link.objects.create(
        grenml_id=replaced_link_id,
        name=replaced_link_name,
        node_a=node_a,
        node_b=node_b,
    )

    substitute_link_name = 'substitute_link'
    substitute_link_id = '2'
    node_a = tm.Node.objects.create(
        name='node_a__' + substitute_link_name,
        latitude=90,
        longitude=80,
    )
    node_b = tm.Node.objects.create(
        name='node_b__' + substitute_link_name,
        latitude=70,
        longitude=60,
    )
    replacement_link = tm.Link.objects.create(
        grenml_id=substitute_link_id,
        name=substitute_link_name,
        node_a=node_a,
        node_b=node_b,
    )

    return (target_link, replacement_link)


@pytest.mark.django_db
def test_substitute_with_different_endpoints(different_endpoints_fixture, replace_rule):
    """
    Verifies a rule containing a replace Link action raises an exception
    (internally) when the target and replacement links do not have the
    same endpoints; this exception should be reflected in the log.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=different_endpoints_fixture[0].grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=different_endpoints_fixture[1].grenml_id,
    )

    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_no_links_no_exception(replace_rule):
    """
    Attempts to execute a replace-link rule that doesn't match
    any links.  The Rule should execute silently.
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
def test_no_links_no_exception_in_ruleset(replace_rule):
    """
    Attempts to execute a replace-link rule that doesn't match
    any links. Expects no exception when run a ruleset.
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
def single_link():
    """ Creates a single link. """

    node_a = tm.Node.objects.create(name='node_a', latitude=10, longitude=10)
    node_b = tm.Node.objects.create(name='node_b', latitude=20, longitude=20)

    link_id = 'unique_link'
    return tm.Link.objects.create(
        grenml_id=link_id,
        name='link',
        node_a=node_a,
        node_b=node_b,
    )


@pytest.mark.django_db
def test_match_equal_to_replacement_with_exception(single_link, replace_rule):
    """
    Sets up a rule with a Replace Link action in which the replacement
    Link and the target coincide.  Verifies that executing this Rule
    fails with a log entry.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=single_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=single_link.grenml_id,
    )
    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_match_equal_to_replacement_no_exception(single_link, replace_rule):
    """
    Sets up a rule with a replace link action in which the replacement
    link and the target coincide. Verifies that executing this ruleset
    does not raise an exception.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=single_link.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=single_link.grenml_id,
    )
    replace_rule.ruleset.apply()
