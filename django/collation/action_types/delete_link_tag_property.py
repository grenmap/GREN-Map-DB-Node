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

A type of action that permanently deletes all matched Properties
Tag in Rules.
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
    Permanently deletes matched Links' tag properties.
    """
))
class DeleteLinkTagProperty (BaseActionType):
    name = gettext_noop('Delete Link Tag Property')
    element_type = ElementTypes.LINK
    required_info = ["value"]

    ACTION_MESSAGE_TEMPLATE = 'Delete property {} at link {}.'
    ACTION_MESSAGE_NOT_FOUND = 'The given property {} was not found at link {}.'
    ACTION_MESSAGE_VALUE_REQUIRED = 'Property "value" is required.'

    def apply(self, link):
        """
        Deletes the 'tag' Property tag with the specified
        tag value from the given Link.
        """
        action_log = ActionLog(
            self.action,
            link,
        )

        property_name = "tag"
        property_value = self.action.info_dict[self.required_info[0]]
        deleted_property = None
        links_affected = []
        action_message = self.ACTION_MESSAGE_VALUE_REQUIRED

        if property_value is not None:
            message = f'with Name={property_name} and with Value={property_value}'
            deleted_property = Property.objects.all().filter(
                property_for=link, name=property_name, value=property_value)

            if deleted_property.exists():
                deleted_property.delete()
                links_affected.append(link)

                action_message = self.ACTION_MESSAGE_TEMPLATE.format(message, link.log_str)
            else:
                action_message = self.ACTION_MESSAGE_NOT_FOUND.format(message, link.log_str)

        log.info(action_message)

        action_log.result(
            action_message,
            [],
            [],
            links_affected,
        )

        return (None, action_log)
