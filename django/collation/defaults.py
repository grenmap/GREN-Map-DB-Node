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

Synopsis: Contains a function to populate default Rulesets for ID
collision resolution.
"""

import logging
from .utils.synchronize_models import synchronize_match_and_action_type_tables


log = logging.getLogger('collation')


CUSTOM_RULESET_NAME = 'Custom ID Collision Resolution'
DEFAULT_RULESET_NAME = 'Default ID Collision Resolution'
DEFAULT_ELEMENT_TYPE_RULE_NAME = 'Default {element_type} ID Collision Resolution'


def _populate_default_id_collision_rulesets(
    Ruleset,  # noqa: N803
    Rule,  # noqa: N803
    MatchType,  # noqa: N803
    MatchCriterion,  # noqa: N803
    ActionType,  # noqa: N803
    Action,  # noqa: N803
):
    """
    Not meant to be called directly.  See *_from_migrations and
    *_from_normal_django help pass-through functions below.

    Creates two Rulesets including the following Rules:
        1. Custom ID collision resolutions
            - [empty; space for administrators to make more]
        2. Catch-all fallback (default) ID collision resolutions
            - duplicate Institutions
            - duplicate Nodes
            - duplicate Links
    """
    log.info('Populating default ID collision Rulesets')

    try:
        custom_id_collision_resolution = Ruleset.objects.create(
            name=CUSTOM_RULESET_NAME,
            enabled=True,
            priority=-1,
        )
    except Exception:
        log.debug('Custom ID Collision Resolution Ruleset already exists; skipping auto-creation')
        pass

    try:
        default_id_collision_resolution = Ruleset.objects.create(
            name=DEFAULT_RULESET_NAME,
            enabled=True,
            priority=0,
        )
    except Exception:
        log.error('Unable to populate default ID collision Ruleset: it may already exist')
        return []

    # Default Institution ID collision resolution Rule
    inst_collision_rule = Rule.objects.create(
        ruleset=default_id_collision_resolution,
        name=DEFAULT_ELEMENT_TYPE_RULE_NAME.format(element_type='Institution'),
        enabled=True,
        priority=0,
    )
    inst_match_type = MatchType.objects.get(class_name='MatchInstitutionsByIDDuplicate')
    MatchCriterion.objects.create(
        rule=inst_collision_rule,
        match_type=inst_match_type,
    )
    inst_action_type = ActionType.objects.get(class_name='KeepNewestInstitution')
    Action.objects.create(
        rule=inst_collision_rule,
        action_type=inst_action_type,
    )

    # Default Node ID collision resolution Rule
    node_collision_rule = Rule.objects.create(
        ruleset=default_id_collision_resolution,
        name=DEFAULT_ELEMENT_TYPE_RULE_NAME.format(element_type='Node'),
        enabled=True,
        priority=0,
    )
    node_match_type = MatchType.objects.get(class_name='MatchNodesByIDDuplicate')
    MatchCriterion.objects.create(
        rule=node_collision_rule,
        match_type=node_match_type,
    )
    node_action_type = ActionType.objects.get(class_name='KeepNewestNode')
    Action.objects.create(
        rule=node_collision_rule,
        action_type=node_action_type,
    )

    # Default Link ID collision resolution Rule
    link_collision_rule = Rule.objects.create(
        ruleset=default_id_collision_resolution,
        name=DEFAULT_ELEMENT_TYPE_RULE_NAME.format(element_type='Link'),
        enabled=True,
        priority=0,
    )
    link_match_type = MatchType.objects.get(class_name='MatchLinksByIDDuplicate')
    MatchCriterion.objects.create(
        rule=link_collision_rule,
        match_type=link_match_type,
    )
    link_action_type = ActionType.objects.get(class_name='KeepNewestLink')
    Action.objects.create(
        rule=link_collision_rule,
        action_type=link_action_type,
    )

    return [default_id_collision_resolution, custom_id_collision_resolution]


def populate_default_id_collision_rulesets_from_migrations(apps, schema_editor):
    """
    Pass-through function for populate_default_id_collision_rulesets
    that gets model references from the 'apps' parameter
    (an instance of django.apps.registry.Apps) instead of directly,
    for compatibility with migrations.
    It also ensures that MatchType and ActionType DB models have been
    adequately synched.
    """
    log.info('Migration populating default ID collision Rulesets')
    synchronize_match_and_action_type_tables(None, force=True)
    Ruleset = apps.get_model('collation', 'Ruleset')  # noqa: N806
    Rule = apps.get_model('collation', 'Rule')  # noqa: N806
    MatchType = apps.get_model('collation', 'MatchType')  # noqa: N806
    MatchCriterion = apps.get_model('collation', 'MatchCriterion')  # noqa: N806
    ActionType = apps.get_model('collation', 'ActionType')  # noqa: N806
    Action = apps.get_model('collation', 'Action')  # noqa: N806
    return _populate_default_id_collision_rulesets(
        Ruleset,
        Rule,
        MatchType,
        MatchCriterion,
        ActionType,
        Action,
    )


def populate_default_id_collision_rulesets_from_normal_django():
    """
    Pass-through function for populate_default_id_collision_rulesets
    that gets model references directly from imports.
    """
    from .models import Ruleset, Rule, MatchType, MatchCriterion, ActionType, Action
    return _populate_default_id_collision_rulesets(
        Ruleset,
        Rule,
        MatchType,
        MatchCriterion,
        ActionType,
        Action,
    )


def _unpopulate_default_id_collision_rulesets(Ruleset):  # noqa: N803
    """
    Not meant to be called directly.  See *_from_migrations and
    *_from_normal_django help pass-through functions below.

    Removes Rulesets with the original names as defined in constants.

    Suitable for use in migration reversals, and to clear the slate
    ready for populate_* above.
    """
    try:
        Ruleset.objects.get(name=CUSTOM_RULESET_NAME).delete()
    except Ruleset.DoesNotExist:
        pass
    try:
        Ruleset.objects.get(name=DEFAULT_RULESET_NAME).delete()
    except Ruleset.DoesNotExist:
        pass


def unpopulate_default_id_collision_rulesets_from_migrations(apps, schema_editor):
    """
    Pass-through function for populate_default_id_collision_rulesets
    that gets model references from the 'apps' parameter
    (an instance of django.apps.registry.Apps) instead of directly,
    for compatibility with migrations.
    """
    Ruleset = apps.get_model('collation', 'Ruleset')  # noqa: N806
    return _unpopulate_default_id_collision_rulesets(Ruleset)


def unpopulate_default_id_collision_rulesets_from_normal_django():
    """
    Pass-through function for unpopulate_default_id_collision_rulesets
    that gets model references directly from imports.
    """
    from .models import Ruleset
    return _unpopulate_default_id_collision_rulesets(Ruleset)
