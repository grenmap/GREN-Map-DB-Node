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

------------------------------------------------------------------------

Django management command to synchronize MatchType and Action type DB
entries with available classes.
"""

import logging

from django.core.management.base import BaseCommand, no_translations

from collation.utils.synchronize_models import (
    synchronize_match_types_table,
    synchronize_action_types_table,
)


class Command(BaseCommand):
    """
    Django management command to synchronize MatchType and ActionType
    DB entries with available classes.

    Usage example:
        python manage.py ruletypes
    """
    help = "Synchronizes MatchType and ActionType selections with available classes."

    LOG_RULE_TYPE_MODEL_SYNCHRONIZATION_DEBUG_STATEMENTS = True

    def _write(self, message, err=False):
        """
        Writes log lines to STDOUT/STDERR if self.LOG_..._STATEMENTS
        is set to True, and always it's intended for STDERR.
        """
        if err:
            self.stderr.write(message)
        else:
            if self.LOG_RULE_TYPE_MODEL_SYNCHRONIZATION_DEBUG_STATEMENTS:
                self.stdout.write(message)

    @no_translations
    def handle(self, *args, **options):
        self._write('Synchronizing MatchTypes...')
        output = synchronize_match_types_table(collect_and_return_log_output=True)
        for (level, message) in output:
            if level > getattr(logging, 'INFO'):
                self._write(message, err=True)
            else:
                self._write(message)
        self._write('MatchTypes synchronized.')

        self._write('Synchronizing ActionTypes...')
        output = synchronize_action_types_table(collect_and_return_log_output=True)
        for (level, message) in output:
            if level > getattr(logging, 'INFO'):
                self._write(message, err=True)
            else:
                self._write(message)
        self._write('ActionTypes synchronized.')
