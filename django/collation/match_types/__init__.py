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

Match type classes define the possible matches that Rules can use to
identify elements in the map database to which actions can be applied.
This module defines these match types, by subclassing BaseMatchType.
"""

from os import listdir, path
import importlib
from sys import modules

from .match_type import BaseMatchType

import logging
log = logging.getLogger('collation.rule_types')


current_dirname = path.dirname(__file__)
match_type_class_files = [f for f in listdir(current_dirname) if (
    f.endswith('.py') and not f.endswith('__init__.py') and not f.endswith('match_type.py')
)]
for f in match_type_class_files:
    log.debug(f'Import match type module {str(f)}')
    importlib.import_module('collation.match_types.' + f[:-3])


def init_match_type(match_type_class_name, match_criterion):
    """
    Returns a class implementing the abstract base class
    BaseMatchType, based on the class name string parameter.
    Passes along the MatchCriterion object; the MatchType needs it.
    """
    klass = None
    for match_type_class in list_match_types():
        if match_type_class.__name__ == match_type_class_name:
            klass = match_type_class
            break
    if klass is None:
        raise NotImplementedError(
            'Module does not contain the class specified: "{}".'.format(match_type_class_name)
        )
    return klass(match_criterion)


def list_match_types():
    """
    List all MatchTypes (subclasses of BaseMatchType) defined in this
    module.
    """
    return BaseMatchType.__subclasses__()
