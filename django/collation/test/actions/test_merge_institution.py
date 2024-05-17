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
ACTION_TYPE_CLASS_NAME = 'MergeInstitution'
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
    Populates the database with a few GRENML records for testing:
        - two Institutions,
        - two Nodes, and
        - one Link.
    """
    topology_one = tm.Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    duplicate_institution = tm.Institution.objects.create(
        name='Dupe Inst',
        short_name='DupeInst',
        latitude=10,
        longitude=10,
    )
    duplicate_institution.topologies.add(topology_one)
    node_a = tm.Node.objects.create(name='node_a', latitude=80, longitude=80)
    node_a.owners.add(duplicate_institution)
    node_a.topologies.add(topology_one)
    node_b = tm.Node.objects.create(name='node_b', latitude=90, longitude=90)
    node_b.owners.add(duplicate_institution)
    node_b.topologies.add(topology_one)
    link = tm.Link.objects.create(
        grenml_id='1',
        name='link',
        node_a=node_a,
        node_b=node_b,
    )
    link.owners.add(duplicate_institution)
    link.topologies.add(topology_one)

    target_institution = tm.Institution.objects.create(
        name='Target Inst',
        # different from duplicate_institution's
        latitude=20,
        longitude=20,
    )
    target_institution.topologies.add(topology_one)

    return (duplicate_institution, target_institution)


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
def test_merge_institution(basic_data, merge_rule):
    """
    Runs the merge-institution rule.
    Verifies that the match institution is no longer in the
    database and that the nodes and link are associated to
    the merge_into
    """
    match_institution, merge_into_institution = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_institution.grenml_id,
    )
    merge_rule.apply()

    # It should not be possible to find the match institution
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(grenml_id=match_institution.grenml_id)

    # The two nodes and the link should be associated
    # to the merge_into institution.
    for node in tm.Node.objects.all():
        assert node.owners.count() == 1
        assert str(node.owners.first().grenml_id) == str(merge_into_institution.grenml_id)
    for link in tm.Link.objects.all():
        assert link.owners.count() == 1
        assert str(link.owners.first().grenml_id) == str(merge_into_institution.grenml_id)


@pytest.mark.django_db
def test_merge_institution_from_child_topology(two_topologies, merge_rule):
    """
    Runs the merge-institution Rule merging an Institution
    with another Institution in its parent Topology, identified
    by ID and Topology, where the IDs remain distinct.
    Verifies that the matched Institution is no longer in the
    database and that the Node and Link associations are moved.
    """
    parent_topology, child_topology = two_topologies
    primary_institution = parent_topology.institutions.first()
    duplicate_institution = child_topology.institutions.first()

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=primary_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    merge_rule.apply()

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
def test_merge_institution_topology_mismatch(two_topologies, merge_rule):
    """
    Tries to runs the merge-institution Rule to merge
    Institutions, but supplies an incorrect Topology ID to the
    Action, so the Rule should abort.
    """
    parent_topology, child_topology = two_topologies
    primary_institution = parent_topology.institutions.first()
    duplicate_institution = child_topology.institutions.first()

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=primary_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        # Wrong Topology!
        value=child_topology.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded

    # The duplicate Institution should still be around
    tm.Institution.objects.get(grenml_id=duplicate_institution.grenml_id)


@pytest.mark.django_db
def test_merge_institution_from_child_topology_same_id(two_topologies, merge_rule):
    """
    Runs the merge-institution Rule merging an Institution
    with another Institution in its parent Topology, identified
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
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=duplicate_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=primary_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=TOPOLOGY_ID_KEY,
        value=parent_topology.grenml_id,
    )
    merge_rule.apply()

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
def test_no_institutions_no_exception_in_ruleset(basic_data, merge_rule):
    """
    Runs a merge institution rule that doesn't match an Institution.
    Expects no exception when run in a Ruleset.
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
def test_no_institutions_no_exception(basic_data, merge_rule):
    """
    Runs a merge institution rule that doesn't match an Institution.
    The Rule should proceed silently.
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
def test_match_equal_to_merge_into_no_exception(basic_data, merge_rule):
    """
    Calls a merge institution rule in which the match and
    merge_into elements have the same id. Expects no exception
    when run in a Ruleset
    """
    match_institution, _ = basic_data
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    merge_rule.ruleset.apply()


@pytest.mark.django_db
def test_match_equal_to_merge_into_with_exception(basic_data, merge_rule):
    """
    Calls a merge institution rule in which the match and
    merge_into elements have the same id. Expects the Rule to
    fail with a message in the log.
    """
    match_institution, _ = basic_data
    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    rule_log = merge_rule.apply()
    assert not rule_log.action_logs[0].succeeded


@pytest.mark.django_db
def test_merge_institution_extra_fields(basic_data, merge_rule):
    """
    Runs the merge-institution rule.
    Verifies that the match institution is no longer in the
    database and that the extra informations are associated
    to the merge_into
    """
    match_institution, merge_into_institution = basic_data

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_institution.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the match
    # institution.
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(grenml_id=match_institution.grenml_id)

    merge_into_institution_updated = tm.Institution.objects.get(
        grenml_id=merge_into_institution.grenml_id,
    )

    # The short name should be associated to the
    # merge_into institution
    assert merge_into_institution_updated.short_name == match_institution.short_name

    # The latitude should not be changed for the
    # merge_into institution
    assert merge_into_institution_updated.latitude != match_institution.latitude


@pytest.mark.django_db
def test_merge_institution_with_properties_not_tags(basic_data, merge_rule):
    """
    Runs the merge-institution rule.
    Verifies that properties in the match institution is no longer
    in the database and that the properties in the match
    institution are merged into merge_into institution
    """
    match_institution, merge_into_institution = basic_data

    tm.Property.objects.create(
        name='url',
        value='http://localhost',
        property_for=match_institution,
    )
    tm.Property.objects.create(
        name='description',
        value='This is a description',
        property_for=match_institution,
    )
    tm.Property.objects.create(
        name='url',
        value='http://mytest.ca',
        property_for=merge_into_institution,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_institution.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the duplicated
    # property of the match institution
    with pytest.raises(tm.Property.DoesNotExist):
        tm.Property.objects.get(
            name='url',
            value='http://localhost',
        )

    # The non-duplicated property should be associated with
    # merge_into institution
    assert str(tm.Property.objects.get(
        name='description',
    ).property_for.grenml_id) == str(merge_into_institution.grenml_id)

    # The duplicated property should still be associated with
    # merge_into institution
    assert str(tm.Property.objects.get(
        name='url',
    ).property_for.grenml_id) == str(merge_into_institution.grenml_id)


@pytest.mark.django_db
def test_merge_institution_with_properties_tags(basic_data, merge_rule):
    """
    Runs the merge-institution rule.
    Verifies that properties in the match institution is no longer
    in the database and that the properties for tag in the match
    institution are merged into merge_into institution
    """
    match_institution, merge_into_institution = basic_data

    tm.Property.objects.create(
        name='tag',
        value='NREN',
        property_for=match_institution,
    )
    tm.Property.objects.create(
        name='tag',
        value='MyISP',
        property_for=match_institution,
    )
    tm.Property.objects.create(
        name='tag',
        value='NREN',
        property_for=merge_into_institution,
    )

    cm.MatchInfo.objects.create(
        match_criterion=merge_rule.match_criteria.first(),
        key=ID_KEY,
        value=match_institution.grenml_id,
    )
    cm.ActionInfo.objects.create(
        action=merge_rule.actions.first(),
        key=ID_KEY,
        value=merge_into_institution.grenml_id,
    )
    merge_rule.ruleset.apply()

    # It should not be possible to find the duplicated property
    # of the match institution
    with pytest.raises(tm.Property.DoesNotExist):
        tm.Property.objects.get(
            name='tag',
            value='NREN',
            property_for=match_institution,
        )

    # The non-duplicated property should be associated with
    # merge_into institution
    assert str(tm.Property.objects.get(
        name='tag', value='MyISP',
    ).property_for.grenml_id) == str(merge_into_institution.grenml_id)

    # The duplicated property should still be associated with
    # merge_into institution
    assert str(tm.Property.objects.get(
        name='tag', value='NREN',
    ).property_for.grenml_id) == str(merge_into_institution.grenml_id)
