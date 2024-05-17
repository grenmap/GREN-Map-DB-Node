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

from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from collation.action_types.deduplication_action_mixin import DeduplicationActionMixin
from collation.action_types.deduplication_action_mixin import DifferentEndpointsError
from . import BaseActionType


import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Replaces the matched Link (A) with the Link specified by ID on the
    Action (B).  A replacement Link may be further identified by
    Topology.  A, and all of A's fields, properties, and tag, will be
    permanently deleted.  B inherits A's Topology memberships.
    """
))
class ReplaceLink(BaseActionType, DeduplicationActionMixin):
    name = gettext_noop('Replace with Link')

    element_type = ElementTypes.LINK

    required_info = ['ID']
    optional_info = ['Topology ID']

    ACTION_MESSAGE_TEMPLATE = 'Delete Link {} and replace with {}.'

    def apply(self, element):
        """
        If the given Link has the same endpoints as the substitute
        specified via ActionInfos, it deletes it.
        """
        self.action_log = ActionLog(
            self.action,
            element,
        )

        replacement_link = self.identify_substitute_element(element)
        if replacement_link is None:
            # Returning None aborts the Action chain.
            # Avoids unexpected results if the chain continues.
            return (None, self.action_log)

        action_message = self.ACTION_MESSAGE_TEMPLATE.format(
            element.log_str,
            replacement_link.log_str,
        )
        log.debug(action_message)

        # Verify endpoints are equal
        target_endpoints = {element.node_a, element.node_b}
        replacement_endpoints = {replacement_link.node_a, replacement_link.node_b}
        if target_endpoints != replacement_endpoints:
            self.action_log.abort(DifferentEndpointsError(
                element.log_str,
                replacement_link.log_str,
            ).translated_message())
            return (None, self.action_log)

        element.replace_with(
            replacement_link,
            union_topologies=True,
            union_owners=False,
        )

        self.action_log.result(
            action_message,
            [],
            [],
            [element, replacement_link],
        )
        return (replacement_link, self.action_log)
