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

import datetime
import json

from django.core.management.base import BaseCommand
from base_app.utils.build_info import BuildInfo, FILE_PATH


class Command(BaseCommand):
    """
    This writes a file containing the build metadata.
    Django reads the file when it renders the home admin page.
    """
    help = 'Writes the build information file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'git_hash',
            help=(
                'Hash for the top commit in the branch from which '
                'we are building GRENMap.'
            ),
            metavar='GIT_HASH',
        )
        parser.add_argument(
            'git_tag',
            help='Git tag identifying the commit we are using to build GRENMap.',
            metavar='GIT_TAG',
        )

    def handle(self, *args, **options):
        git_hash = options.get('git_hash')

        # truncate to the first 8 chars
        if git_hash is not None:
            git_hash = git_hash[:8]

        info = BuildInfo(
            date=datetime.datetime.now().strftime('%Y-%m-%d'),
            git_hash=git_hash,
            git_tag=options.get('git_tag'),
            grenml=None,
            vis=None,
        )
        info_dict = info._asdict()
        file_contents = json.dumps(info_dict)
        with open(FILE_PATH, 'w') as f:
            f.write(file_contents)
