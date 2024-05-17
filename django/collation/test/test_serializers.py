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

------------------------------------------------------------------------

Leverages the fact that this file is run on the equivalent to
application startup, to ensure some required fixtures are loaded.
This is a common Django pattern.
"""

import json
import pytest

import collation.models as m
import collation.serializers as s

from collation.action_types.delete_link import DeleteLink
from collation.constants import ElementTypes


@pytest.fixture
def action_type():
    records = m.ActionType.objects.all()
    result = None
    if records:
        result = records[0]
    else:
        result = m.ActionType.objects.create(
            class_name=DeleteLink.__name__,
            name='test_action_type',
            element_type=ElementTypes.LINK,
        )
    return result


@pytest.fixture
def match_type():
    records = m.MatchType.objects.all()
    result = None
    if records:
        result = records[0]
    else:
        result = m.MatchType.objects.create(
            class_name='test_class_match_type',
            name='test_match_type',
            element_type=ElementTypes.LINK,
        )
    return result


@pytest.fixture
def rulesets_fixture(action_type, match_type):
    def make_ruleset(matchinfo_value, match_type_name=match_type.name):
        return [{
            'name': 'test_ruleset',
            'rules': [{
                'actions': [{
                    'action_type': action_type.name,
                    'actioninfo_set': [],
                }],
                'match_criteria': [{
                    'match_type': match_type_name,
                    'matchinfo_set': [{
                        'key': 'id',
                        'value': matchinfo_value,
                    }],
                }],
                'name': 'test_del_link_id',
                'enabled': True,
                'priority': 1000,
            }],
            'enabled': True,
            'priority': 1000,
        }]

    return make_ruleset


@pytest.mark.django_db
def test_import_export(rulesets_fixture):
    rulesets = rulesets_fixture('1')
    ruleset_bytes = json.dumps(rulesets).encode()
    s.bytes_to_rulesets(ruleset_bytes)
    exported_ruleset_bytes = s.rulesets_to_bytes(
        [m.Ruleset.objects.get(name='test_ruleset')],
    )
    exported_rulesets = json.loads(exported_ruleset_bytes.decode())
    print(rulesets)
    print(exported_rulesets)
    assert rulesets == exported_rulesets


def get_matchinfo_value():
    return (
        m.Ruleset
        .objects.get(name='test_ruleset')
        .rules.get()
        .match_criteria.get()
        .matchinfo_set.get()
        .value
    )


@pytest.mark.django_db
def test_import_existing_ruleset(rulesets_fixture):
    # create a ruleset by importing it
    matchinfo_value = '1'
    fixture = rulesets_fixture(matchinfo_value)
    ruleset_bytes = json.dumps(fixture).encode()
    import_result = s.bytes_to_rulesets(ruleset_bytes)
    assert len(import_result['created_rulesets']) == 1
    assert len(import_result['invalid_rulesets']) == 0
    assert get_matchinfo_value() == matchinfo_value

    # modify the ruleset then import again
    matchinfo_value = '2'
    fixture = rulesets_fixture(matchinfo_value)
    ruleset_bytes = json.dumps(fixture).encode()
    import_result = s.bytes_to_rulesets(ruleset_bytes)
    assert len(import_result['created_rulesets']) == 1
    assert len(import_result['invalid_rulesets']) == 0
    assert get_matchinfo_value() == matchinfo_value


@pytest.mark.django_db
def test_import_invalid_ruleset(rulesets_fixture):
    match_type_name = 'invalid_match_type'
    fixture = rulesets_fixture('1', match_type_name)
    ruleset_bytes = json.dumps(fixture).encode()
    import_result = s.bytes_to_rulesets(ruleset_bytes)
    assert len(import_result['created_rulesets']) == 0
    assert len(import_result['invalid_rulesets']) == 1


@pytest.mark.django_db
def test_import_empty_byte_array():
    with pytest.raises(s.RulesetParseError):
        s.bytes_to_rulesets(b'')


@pytest.mark.django_db
def test_import_malformed_ruleset():
    ruleset_bytes = json.dumps(['test', 'malformed']).encode()
    with pytest.raises(s.RulesetParseError):
        s.bytes_to_rulesets(ruleset_bytes)


@pytest.fixture
def two_match_criteria_rulesets_fixture(action_type, match_type):
    return [{
        'name': 'test_ruleset',
        'rules': [{
            'actions': [{
                'action_type': action_type.name,
                'actioninfo_set': [],
            }],
            'match_criteria': [
                {
                    'match_type': match_type.name,
                    'matchinfo_set': [{
                        'key': 'id',
                        'value': '1',
                    }],
                },
                {
                    'match_type': match_type.name,
                    'matchinfo_set': [{
                        'key': 'id',
                        'value': '2',
                    }],
                }
            ],
            'name': 'test_del_link_id',
            'enabled': True,
            'priority': 1000,
        }],
        'enabled': True,
        'priority': 1000,
    }]


@pytest.mark.django_db
def test_import_ruleset_with_two_match_criteria(
        two_match_criteria_rulesets_fixture
):
    """
    Imports then exports a ruleset containing a rule that has
    two match criteria with the same match type.
    """
    ruleset_bytes = json.dumps(two_match_criteria_rulesets_fixture).encode()
    s.bytes_to_rulesets(ruleset_bytes)
    exported_ruleset_bytes = s.rulesets_to_bytes(
        [m.Ruleset.objects.get(name='test_ruleset')],
    )
    exported_rulesets = json.loads(exported_ruleset_bytes.decode())
    assert two_match_criteria_rulesets_fixture == exported_rulesets
