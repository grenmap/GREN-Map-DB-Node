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


MATCH_TYPE_CLASS_NAME = 'MatchInstitutionsByID'
ACTION_TYPE_CLASS_NAME = 'ReplaceInstitution'
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
    Sets up some network elements for testing the replace institution
    action type.
    Creates target and substitute institutions, then creates two nodes
    and a link. Associates them to the target.
    """
    target_institution_name = 'target'
    target_institution = tm.Institution.objects.create(
        name=target_institution_name,
        latitude=10,
        longitude=10,
    )
    target_institution_property = tm.Property.objects.create(
        name='tag',
        value='target_institution_property',
        property_for=target_institution,
    )
    target_institution_property.save()
    node_a = tm.Node.objects.create(name='node_a', latitude=80, longitude=80)
    node_a.owners.add(target_institution)
    node_b = tm.Node.objects.create(name='node_b', latitude=90, longitude=90)
    node_b.owners.add(target_institution)
    link = tm.Link.objects.create(
        grenml_id='1',
        name='link',
        node_a=node_a,
        node_b=node_b,
    )
    link.owners.add(target_institution)

    substitute_institution_name = 'substitute'
    substitute_institution = tm.Institution.objects.create(
        name=substitute_institution_name,
        latitude=20,
        longitude=20,
    )

    return (target_institution, substitute_institution)


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
def test_replace_institution(normal_usage_fixture, replace_rule):
    """
    Runs a rule containing a replace institution action type.
    Prepares the database with the normal usage fixture.
    Verifies that the target institution is no longer in the database
    and that the nodes and link are associated to the substitute.
    """
    target_institution, substitute_institution = normal_usage_fixture

    # Check the target institution's property is present..
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 1

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=target_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=substitute_institution.grenml_id,
    )
    replace_rule.ruleset.apply()

    # It should not be possible to find the target institution.
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(name=target_institution.name)

    # The two nodes and the link should be associated
    # to the substitute institution.
    for node in tm.Node.objects.all():
        owners = node.owners.all()
        assert len(owners) == 1
        assert owners[0].name == substitute_institution.name
    for link in tm.Link.objects.all():
        owners = link.owners.all()
        assert len(owners) == 1
        assert owners[0].name == substitute_institution.name

    # The property should have been deleted.
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 0


@pytest.mark.django_db
def test_replace_institution_with_parent_version(two_topologies, replace_rule):
    """
    Runs the replace-institution Rule replacing an Institution
    with another Institution from its parent Topology, identified
    by ID and Topology, where the IDs remain distinct.
    Verifies that the matched Institution is no longer in the
    database and that the Node and Link associations are moved.
    """
    parent_topology, child_topology = two_topologies
    primary_institution = parent_topology.institutions.first()
    duplicate_institution = child_topology.institutions.first()

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=primary_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    replace_rule.apply()

    # The duplicate Institution should be gone
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(grenml_id=duplicate_institution.grenml_id)

    # The two Nodes and one Link should be associated with the primary
    # institution now.
    for node in child_topology.nodes.all():
        assert node.owners.count() == 1
        assert str(node.owners.first().grenml_id) == str(primary_institution.grenml_id)
    for link in child_topology.links.all():
        assert link.owners.count() == 1
        assert str(link.owners.first().grenml_id) == str(primary_institution.grenml_id)


@pytest.mark.django_db
def test_replace_institution_topology_mismatch(two_topologies, replace_rule):
    """
    Tries to runs the replace-institution Rule to replace an
    Institution, but supplies an incorrect Topology ID to the
    Action, so the Rule should abort.
    """
    parent_topology, child_topology = two_topologies
    primary_institution = parent_topology.institutions.first()
    duplicate_institution = child_topology.institutions.first()

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=primary_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        # Wrong Topology!
        value=child_topology.grenml_id,
    )
    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded

    # The duplicate Institution should still be around
    tm.Institution.objects.get(grenml_id=duplicate_institution.grenml_id)


@pytest.mark.django_db
def test_replace_institution_with_parent_version_same_id(two_topologies, replace_rule):
    """
    Runs the replace-institution Rule replacing an Institution
    with another Institution from its parent Topology, identified
    by ID and Topology, where the IDs are identical.
    Verifies that the matched Institution is no longer in the
    database and that the Node and Link associations are moved.
    """
    parent_topology, child_topology = two_topologies
    primary_institution = parent_topology.institutions.first()
    duplicate_institution = child_topology.institutions.first()

    # Create another Institution in the child Topology with the same
    # GRENML ID as the primary one in the parent Topology,
    # to challenge the Action's topology discrimination
    extra_institution = tm.Institution.objects.create(
        grenml_id=primary_institution.grenml_id,
        name='Another Inst',
        short_name='AnotherInst',
        latitude=-10,
        longitude=-10,
    )
    extra_institution.topologies.add(child_topology)

    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=primary_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    replace_rule.apply()

    # The duplicate Institution should be gone
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(grenml_id=duplicate_institution.grenml_id)

    # The two Nodes and one Link should be associated with the primary
    # institution now.
    for node in child_topology.nodes.all():
        assert node.owners.count() == 1
        assert node.owners.first().pk == primary_institution.pk
    for link in child_topology.links.all():
        assert link.owners.count() == 1
        assert link.owners.first().pk == primary_institution.pk


@pytest.mark.django_db
def test_no_institutions_no_exception(replace_rule):
    """
    Runs a replace institution rule in an empty database.
    The Rule should execute silently.
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
def test_no_institutions_no_exception_in_ruleset(replace_rule):
    """
    Runs a replace institution rule in an empty database.
    Expects no exception when run a ruleset.
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
def single_institution():
    """
    Creates a single institution to verify an exception happens
    when we configure a replace institution rule with the same target
    and substitute.
    """
    return tm.Institution.objects.create(
        name='target',
        latitude=10,
        longitude=10,
    )


@pytest.mark.django_db
def test_match_equal_to_replacement_with_exception(single_institution, replace_rule):
    """
    Calls a replace institution rule in which the target and replacement
    elements have the same id. Expects an exception when run a rule.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=single_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=single_institution.grenml_id,
    )
    rule_log = replace_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_match_equal_to_replacement_no_exception(single_institution, replace_rule):
    """
    Calls a replace institution rule in which the target and replacement
    elements have the same id. Expects no exception when run a ruleset.
    """
    cm.MatchInfo.objects.create(
        match_criterion=replace_rule.match_criteria.first(),
        key=ID_KEY,
        value=single_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=replace_rule.actions.first(),
        key=ID_KEY,
        value=single_institution.grenml_id,
    )
    replace_rule.ruleset.apply()
