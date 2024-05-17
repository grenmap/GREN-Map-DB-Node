"""
Copyright 2021 GRENMap Authors

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

from collation.serializers import dict_list_to_rulesets
from collation.utils.synchronize_models import synchronize_match_and_action_type_tables


def make_ruleset(match_type, action_type, actioninfo_key, target_id, replacement_id):
    """
    Utility function for testing the replace actions.
    Creates a dictionary that represents a ruleset whose match and
    action types take element ids. The caller passes the names of the
    types as parameters.
    """
    return {
        'name': 'replace_test_ruleset',
        'rule_set': [{
            'name': 'replace_test',
            'matchcriterion_set': [{
                'match_type': match_type,
                'matchinfo_set': [{'key': 'ID', 'value': target_id}]
            }],
            'action_set': [
                {
                    'action_type': action_type,
                    'actioninfo_set': [{
                        'key': actioninfo_key,
                        'value': replacement_id,
                    }]
                }
            ],
        }]
    }


def apply_ruleset(ruleset_dict):
    """
    Executes the ruleset represented by the dictionary
    passed as parameter.
    """
    synchronize_match_and_action_type_tables(None)
    rulesets_dict = dict_list_to_rulesets([ruleset_dict])
    replace_test_ruleset = rulesets_dict['created_rulesets'][0]
    replace_test_ruleset.apply()


def apply_rule(ruleset_dict):
    """
    Executes the rule in the ruleset represented by the dictionary
    passed as parameter.
    """
    synchronize_match_and_action_type_tables(None)
    rulesets_dict = dict_list_to_rulesets([ruleset_dict])
    replace_test_ruleset = rulesets_dict['created_rulesets'][0]
    for rule in replace_test_ruleset.rules.all():
        rule.apply()
