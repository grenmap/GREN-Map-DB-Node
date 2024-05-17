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

Contains a function that provides values for template variables
in the home admin page.

See TEMPLATES in base_app/settings.py.
"""

import json
import logging
import re
from functools import cache
from base_app.utils.build_info import BuildInfo, FILE_PATH

DEFAULT_BUILD_ATTRIBUTES = BuildInfo(
    date='DATE NOT AVAILABLE',
    git_hash='HASH NOT AVAILABLE',
    git_tag='TAG NOT AVAILABLE',

    # These are called git-refs because they can be
    # tags, branches or commit hashes.
    grenml='VERSION NOT AVAILABLE',
    vis='VERSION NOT AVAILABLE',
)
logger = logging.getLogger()


def get_with_regex_from_file(
        file_path, d, *regex_attr_name_pairs
):
    """
    This function reads a text file and uses regular expressions
    to extract values from its contents.

    The argument d is a dictionary.

    The remaining arguments are a list of pairs. The first item
    in a pair is the name of the attribute added to the dictionary.
    The second item is a regular expression. The value of the attribute
    will be the result of applying the regular expression
    to the file contents.
    """
    with open(file_path, 'r') as f:
        file_contents = f.read()

    while regex_attr_name_pairs:
        attr_name = regex_attr_name_pairs[0]
        regex = regex_attr_name_pairs[1]
        regex_attr_name_pairs = regex_attr_name_pairs[2:]
        match = re.search(regex, file_contents)
        if match is not None:
            attr_value = match.group(1)
        else:
            attr_value = None
        d[attr_name] = attr_value

    return d


@cache
def load_attributes():
    """ Loads the build attributes for the home admin page. """

    default_attributes = DEFAULT_BUILD_ATTRIBUTES._asdict()

    # read build info file
    try:
        with open(FILE_PATH) as f:
            lines = f.readlines()
        file_contents = ''.join(lines)
    except FileNotFoundError:
        logger.exception('build_attributes: could not read file %s', FILE_PATH)

    # parse json
    try:
        attributes = json.loads(file_contents)
    except json.decoder.JSONDecodeError:
        logger.exception('build_attributes: could not parse JSON')

    # read component versions from dependency files
    try:
        get_with_regex_from_file(
            './requirements.txt',
            attributes,

            # GRENML library version
            'grenml',
            r'grenml[=~ ]+([0-9.]+)\n',

        )

        get_with_regex_from_file(
            './package.json',
            attributes,

            # web front-end bundle version
            'vis',
            r'"@grenmap/gren-map-visualization": "([0-9.]+)"'
        )
    except Exception:
        logger.exception('build_attributes: could not read dependency files')

    # use default values for missing attributes
    for k in default_attributes:
        if k not in attributes or not bool(attributes[k]):
            attributes[k] = default_attributes[k]

    build_info = BuildInfo(**attributes)

    # values for the template variables
    build_attributes = {
        'build_date': build_info.date,
        'build_tag': build_info.git_tag,
        'build_short_sha': build_info.git_hash,
        'build_grenml': build_info.grenml,
        'build_vis': build_info.vis,
    }

    # print attributes on the log
    logger.info('build_attributes: %s', build_attributes)

    return build_attributes


def build_attributes(request):
    """
    Context processor function. Simply returns the dictionary it obtains
    from load_attributes.
    """
    return load_attributes()
