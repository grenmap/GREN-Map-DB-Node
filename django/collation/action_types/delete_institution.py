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

A type of action that permanently deletes all matched Institutions in
Rules.
"""
from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from network_topology.models import NetworkElement
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from . import BaseActionType

import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Permanently deletes matched Institutions.
    Removes these Institutions as owners of Nodes and Links.
    """
))
class DeleteInstitution(BaseActionType):
    name = gettext_noop('Delete Institution')

    element_type = ElementTypes.INSTITUTION

    required_info = []

    ACTION_MESSAGE_TEMPLATE = 'Delete Institution {}.'

    def apply(self, element):
        """
        Deletes the given Institution element.  Does not cascade to
        attached Nodes and Links implicitly.
        """
        action_log = ActionLog(
            self.action,
            element,
        )
        action_message = self.ACTION_MESSAGE_TEMPLATE.format(element.log_str)

        # Obtain the Nodes and Links attached to the matched
        # Institution, for the ActionLog
        nodes_affected = NetworkElement.objects.filter(
            owners__in=[element],
            node__isnull=False,
        )
        links_affected = NetworkElement.objects.filter(
            owners__in=[element],
            link__isnull=False,
        )

        log.debug(action_message)
        element.delete()

        action_log.result(
            action_message,
            [element],
            nodes_affected,
            links_affected,
        )
        return (None, action_log)
