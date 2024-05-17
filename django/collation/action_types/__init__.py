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

Action type classes define the possible actions that Rules can apply on
matched elements in the map database.  This module defines these
action types, by subclassing BaseActionType.
"""

from os import listdir, path
import importlib
from sys import modules

from .action_type import BaseActionType

import logging
log = logging.getLogger('collation.rule_types')


current_dirname = path.dirname(__file__)
action_type_class_files = [f for f in listdir(current_dirname) if (
    f.endswith('.py') and not f.endswith('__init__.py') and not f.endswith('action_type.py')
)]
for f in action_type_class_files:
    log.debug(f'Import action type module {str(f)}')
    importlib.import_module('collation.action_types.' + f[:-3])


def init_action_type(action_type_class_name, action):
    """
    Returns a class implementing the abstract base class
    BaseActionType, based on the class name string parameter.
    """
    klass = None
    for action_type_class in list_action_types():
        if action_type_class.__name__ == action_type_class_name:
            klass = action_type_class
            break
    if klass is None:
        raise NotImplementedError(
            'Module does not contain the class specified: "{}".'.format(action_type_class_name)
        )
    return klass(action)


def list_action_types():
    """
    List all ActionTypes (subclasses of BaseActionType) defined in this
    module.
    """
    return BaseActionType.__subclasses__()
