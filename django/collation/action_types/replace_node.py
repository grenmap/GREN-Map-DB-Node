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
from . import BaseActionType


import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Replaces the matched Node (A) with the Node specified by ID on the
    Action (B).  A replacement Node may be further identified by
    Topology.  Link endpoints of A will be updated to B.  A, and all
    of A's fields, properties, and tag, will be permanently deleted.
    """
))
class ReplaceNode(BaseActionType, DeduplicationActionMixin):
    name = gettext_noop('Replace with Node')

    element_type = ElementTypes.NODE

    required_info = ['ID']
    optional_info = ['Topology ID']

    ACTION_MESSAGE_TEMPLATE = 'Delete Node {} and replace with {}.'

    def apply(self, element):
        """
        For all Links with the given Node as an endpoint, replaces
        the Node endpoint with the substitute specified in the
        ActionInfo, then deletes it.
        """
        self.action_log = ActionLog(
            self.action,
            element,
        )

        replacement_node = self.identify_substitute_element(element)
        if replacement_node is None:
            # Returning None aborts the Action chain.
            # Avoids unexpected results if the chain continues.
            return (None, self.action_log)

        action_message = self.ACTION_MESSAGE_TEMPLATE.format(
            element.log_str,
            replacement_node.log_str,
        )
        log.debug(action_message)

        affected_links = element.links.all()

        element.replace_with(
            replacement_node,
            union_topologies=True,
            union_owners=False,
        )

        self.action_log.result(
            action_message,
            [],
            [element, replacement_node],
            affected_links,
        )
        return (replacement_node, self.action_log)
