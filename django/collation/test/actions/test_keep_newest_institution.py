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


MATCH_TYPE_CLASS_NAME = 'MatchInstitutionsByIDDuplicate'
ACTION_TYPE_CLASS_NAME = 'KeepNewestInstitution'
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
    Sets up some network elements for testing the KeepNewestInstitution
    ActionType.  Creates three Institutions, all with ID '1234':
        - inst 1
        - inst 2
        - newest
    Creates two nodes and a link, and assigns inst_1 as owner.
    Does not establish any Topologies.
    """
    inst_1 = tm.Institution.objects.create(
        name='inst 1',
        grenml_id='1234',
        latitude=10,
        longitude=10,
    )
    inst_2 = tm.Institution.objects.create(
        name='inst 2',
        grenml_id='1234',
        latitude=20,
        longitude=20,
    )
    newest = tm.Institution.objects.create(
        name='newest',
        grenml_id='1234',
        latitude=30,
        longitude=30,
    )

    # Add a Property to one of the Institutions
    tm.Property.objects.create(
        name='tag',
        value='inst_1_property',
        property_for=inst_1,
    )

    # Add some network infrastructure owned by inst_1
    node_a = tm.Node.objects.create(
        grenml_id='11',
        name='node_a', latitude=80, longitude=80)
    node_a.owners.add(inst_1)
    node_b = tm.Node.objects.create(
        grenml_id='22',
        name='node_b', latitude=90, longitude=90)
    node_b.owners.add(inst_1)
    link = tm.Link.objects.create(
        grenml_id='1',
        name='link',
        node_a=node_a,
        node_b=node_b,
    )
    link.owners.add(inst_1)

    return (inst_1, inst_2, newest)


@pytest.fixture
def two_topologies(normal_usage_fixture):
    """
    Populates the database with the contents of normal_usage_fixture
    placed into a Topology, and also a child Topology with an
    additional Institution that will become the "newest" (by PK).
    """
    topology_one = tm.Topology.objects.create(
        grenml_id='Topo1',
        name='Topology 1',
    )
    # Place contents of normal_usage_fixture into Topology 1
    for inst in tm.Institution.objects.all():
        inst.topologies.add(topology_one)
    for node in tm.Node.objects.all():
        node.topologies.add(topology_one)
    for link in tm.Link.objects.all():
        link.topologies.add(topology_one)
    # Set the owner of the parent Topology to be one of its Institutions
    topology_one.owner = normal_usage_fixture[0]
    topology_one.save()

    topology_two = tm.Topology.objects.create(
        grenml_id='Topo2',
        name='Topology 2',
        parent=topology_one,
    )
    child_institution = tm.Institution.objects.create(
        name='new newest',
        grenml_id='1234',
        short_name='ChildInst',
        latitude=40,
        longitude=40,
    )
    child_institution.topologies.add(topology_two)

    return (topology_one, topology_two)


@pytest.mark.django_db
def test_keep_newest_institution(normal_usage_fixture, keep_newest_rule):
    """
    Runs a rule containing a KeepNewestInstitution Action.
    Prepares the database with the normal usage fixture.
    Verifies that the target institution is no longer in the database
    and that the nodes and link are associated to the newest.
    """
    inst_1, inst_2, newest = normal_usage_fixture

    # Check the first institution's property is present..
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 1

    keep_newest_rule.ruleset.apply()

    # It should not be possible to find either inst_1 or inst_2
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(name=inst_1.name)
    with pytest.raises(tm.Institution.DoesNotExist):
        tm.Institution.objects.get(name=inst_2.name)

    # The two nodes and the link should be associated
    # to the newest institution.
    for node in tm.Node.objects.all():
        owners = node.owners.all()
        assert len(owners) == 1
        assert owners[0].name == newest.name
    for link in tm.Link.objects.all():
        owners = link.owners.all()
        assert len(owners) == 1
        assert owners[0].name == newest.name

    # The property should have been deleted
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 0


@pytest.mark.django_db
def test_keep_newest_institution_with_topologies(two_topologies, keep_newest_rule):
    """
    Runs the KeepNewestInstitution Rule replacing all Institutions
    in the parent Topology with the newest one in the child.
    """
    parent_topology, child_topology = two_topologies
    newest_institution = child_topology.institutions.first()

    keep_newest_rule.apply()

    # Only one Institution should be left
    institutions = tm.Institution.objects.all()
    assert institutions.count() == 1
    assert institutions.first().name == newest_institution.name

    # The two Nodes, one Link and parent_topology should be associated
    # with the newest institution now.
    for node in parent_topology.nodes.all():
        assert node.owners.count() == 1
        assert node.owners.first().name == newest_institution.name
    for link in parent_topology.links.all():
        assert link.owners.count() == 1
        assert link.owners.first().name == newest_institution.name
    # Reload parent_topology to get the latest DB version
    parent_topology = tm.Topology.objects.get(pk=parent_topology.pk)
    assert parent_topology.owner.pk == newest_institution.pk
