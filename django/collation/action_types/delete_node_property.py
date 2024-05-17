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

------------------------------------------------------------------------

A type of action that permanently deletes all matched
Properties in Rules.
"""

from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from network_topology.models import Property
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from . import BaseActionType

import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Permanently deletes matched Nodes' properties.
    """
))
class DeleteNodeProperty (BaseActionType):
    name = gettext_noop('Delete Node Property')
    element_type = ElementTypes.NODE
    required_info = ["name"]
    optional_info = ["value"]

    ACTION_MESSAGE_TEMPLATE = 'Delete property {} at node {}.'
    ACTION_MESSAGE_NOT_FOUND = 'The given property {} was not found at node {}.'

    def apply(self, node):
        """
        Deletes Properties with the specified name (optionally also
        matching value) from the given Node.
        """
        action_log = ActionLog(
            self.action,
            node,
        )

        id_key = self.required_info[0]
        property_name = self.action.info_dict[id_key].lower()
        property_value = None
        deleted_property = None
        nodes_affected = []
        action_message = ''

        # If the 'Value' of the property is provided,
        # a property matching 'Name' and 'Value' will be searched.
        if (self.optional_info[0] in self.action.info_dict):
            property_value = self.action.info_dict[self.optional_info[0]]

        if property_value is not None:
            message = f'with Name={property_name} and with Value={property_value}'
            deleted_property = Property.objects.all().filter(
                property_for=node, name=property_name, value=property_value)
        else:
            message = f'with Name={property_name}'
            deleted_property = Property.objects.filter(property_for=node, name=property_name)

        if deleted_property.exists():
            deleted_property.delete()
            nodes_affected.append(node)

            action_message = self.ACTION_MESSAGE_TEMPLATE.format(message, node.log_str)
        else:
            action_message = self.ACTION_MESSAGE_NOT_FOUND.format(message, node.log_str)

        log.debug(action_message)

        action_log.result(
            action_message,
            [],
            nodes_affected,
            [],
        )

        return (None, action_log)
