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

import logging
import sys
from ..match_types import list_match_types
from ..action_types import list_action_types
from ..models import MatchType, ActionType


log = logging.getLogger('collation.rule_types')
DEBUG = getattr(logging, 'DEBUG')
INFO = getattr(logging, 'INFO')
WARNING = getattr(logging, 'WARNING')
ERROR = getattr(logging, 'ERROR')
CRITICAL = getattr(logging, 'CRITICAL')
DEFAULT_LOG_LEVEL = DEBUG


def synchronize_match_and_action_type_tables(sender, **kwargs):
    """
    Runs both class-to-model synchronization functions below,
    mostly as a convenience.  Signature suitable for invocation
    by either a Django Signal or AppConfig.
    Running during management scripts is redundant and can interfere,
    so this is generally detected and the operation is skipped.
    Optional boolean arguments:
        read_only: passes through to synchronize_*_types_table calls
        force: run despite being in a management command;
                suitable for migrations
    """
    force = 'force' in kwargs and kwargs['force']
    if 'manage.py' in sys.argv and not force:
        log.debug('Skipping match and action type synchronization for management scripts.')
        return
    read_only = 'read_only' in kwargs and kwargs['read_only']
    synchronize_match_types_table(read_only=read_only)
    synchronize_action_types_table(read_only=read_only)


def log_output(message, level=DEFAULT_LOG_LEVEL):
    log.log(level, message)
    return (level, message)


def synchronize_match_types_table(read_only=False, collect_and_return_log_output=False):
    """
    Ensures there is a database entry for each of the MatchType
    subclasses, so that they may be selected by the Data
    Administrator.  Warn in the logs if there are database records
    referring to subclasses that have not been imported.
    Set the read_only parameter to True if no database manipulation is
    desired (appropriate for AppConfig.ready).
    Set the collect_and_return_log_output parameter to True if output
    target is preferred to be STDOUT/STDERR or similar.  Function will
    then return a list of two-tuples:
        [
            (log_level_as_integer, message_string),
            ...
        ]
    """
    log_roll = []

    match_type_classes = list_match_types()
    for klass in match_type_classes:
        try:
            log_roll.append(log_output(
                f'Checking match type {klass.__name__}',
                DEBUG,
            ))
            MatchType.objects.get(class_name=klass.__name__)
        except MatchType.DoesNotExist:
            if read_only:
                log_roll.append(log_output(
                    f'DB object for MatchType {klass.__name__} does not exist.',
                    WARNING,
                ))
            else:
                log_roll.append(log_output(
                    f'Adding match type {klass.__name__}',
                    DEBUG,
                ))
                MatchType.objects.create(
                    class_name=klass.__name__,
                    name=klass.name,
                    element_type=klass.element_type,
                    # Convert Python quotes to JSON
                    required_info=str(klass.required_info).replace("'", '"'),
                    optional_info=str(klass.optional_info).replace("'", '"'),
                )

    for match_type_object in MatchType.objects.all():
        if match_type_object.class_name not in [c.__name__ for c in match_type_classes]:
            log_roll.append((
                f'Deprecated MatchType {match_type_object.name} detected.',
                WARNING,
            ))

    if collect_and_return_log_output:
        return log_roll


def synchronize_action_types_table(read_only=False, collect_and_return_log_output=False):
    """
    Ensures there is a database entry for each of the ActionType
    subclasses, so that they may be selected by the Data
    Administrator.  Warn in the logs if there are database records
    referring to subclasses that have not been imported.
    Set the read_only parameter to True if no database manipulation is
    desired (appropriate for AppConfig.ready).
    Set the collect_and_return_log_output parameter to True if output
    target is preferred to be STDOUT/STDERR or similar.  Function will
    then return a list of two-tuples:
        [
            (log_level_as_integer, message_string),
            ...
        ]
    """
    log_roll = []

    action_type_classes = list_action_types()
    for klass in action_type_classes:
        try:
            log_roll.append(log_output(
                f'Checking action type {klass.__name__}',
                DEBUG,
            ))
            ActionType.objects.get(class_name=klass.__name__)
        except ActionType.DoesNotExist:
            if read_only:
                log_roll.append(log_output(
                    f'DB object for ActionType {klass.__name__} does not exist.',
                    WARNING,
                ))
            else:
                log_roll.append(log_output(
                    f'Adding action type {klass.__name__}',
                    DEBUG,
                ))
                ActionType.objects.create(
                    class_name=klass.__name__,
                    name=klass.name,
                    element_type=klass.element_type,
                    # Convert Python quotes to JSON
                    required_info=str(klass.required_info).replace("'", '"'),
                    optional_info=str(klass.optional_info).replace("'", '"'),
                )

    for action_type_object in ActionType.objects.all():
        if action_type_object.class_name not in [c.__name__ for c in action_type_classes]:
            log_roll.append((
                f'Deprecated ActionType {action_type_object.name} detected.',
                WARNING,
            ))

    if collect_and_return_log_output:
        return log_roll
