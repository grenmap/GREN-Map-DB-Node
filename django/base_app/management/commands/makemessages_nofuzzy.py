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

import argparse

from django.core.management.commands.makemessages \
    import Command as MakeMessagesCommand


class Command(MakeMessagesCommand):
    """ MakeMessages command that doesn't generate fuzzy matches. """

    help = (
        'This works in the same way as makemessages except that it adds '
        'an option to msgmerge (part of gettext) that disables generation '
        'of fuzzy matches.\n\n'
        'The help text for the makemessages command follows:\n\n'
    ) + '"' + MakeMessagesCommand.help + '"'

    msgmerge_options = MakeMessagesCommand.msgmerge_options + ['--no-fuzzy-matching']

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.formatter_class = argparse.RawTextHelpFormatter
        return parser
