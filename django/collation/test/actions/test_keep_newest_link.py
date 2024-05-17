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


MATCH_TYPE_CLASS_NAME = 'MatchLinksByIDDuplicate'
ACTION_TYPE_CLASS_NAME = 'KeepNewestLink'
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
    Sets up some network elements for testing the KeepNewestLink
    ActionType.  Creates three Links:
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
        name='Node 2',
        grenml_id='1122',
        latitude=20,
        longitude=20,
    )

    # Add two links
    link_1 = tm.Link.objects.create(
        grenml_id='1',
        name='link',
        node_a=node_1,
        node_b=node_2,
    )

    newest = tm.Link.objects.create(
        grenml_id='1',
        name='link new',
        node_a=node_1,
        node_b=node_2,
    )

    # Add a Property to one of the Links
    tm.Property.objects.create(
        name='tag',
        value='link_1_property',
        property_for=link_1,
    )

    return (link_1, newest)


@pytest.mark.django_db
def test_keep_newest_link(normal_usage_fixture, keep_newest_rule):
    """
    Runs a rule containing a KeepNewestLink Action.
    Prepares the database with the normal usage fixture.
    Verifies that the link_1 is no longer in the database.
    """
    link_1, newest = normal_usage_fixture

    # Check the first link's property is present..
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 1

    keep_newest_rule.ruleset.apply()

    # It should not be possible to find link_1
    with pytest.raises(tm.Link.DoesNotExist):
        tm.Link.objects.get(name=link_1.name)

    # The only link should be the newest link.
    for link in tm.Link.objects.all():
        assert link.pk == newest.pk

    # The property should have been deleted
    all_properties = tm.Property.objects.all()
    assert len(all_properties) == 0
