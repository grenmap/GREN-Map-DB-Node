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

A type of Action that deduplicates elements with conflicting IDs by
selecting the most-recently-added version and removing the rest.
"""

from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from network_topology.models import Node
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from . import BaseActionType
from .deduplication_action_mixin import DeduplicationActionMixin


import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Replaces all matched Nodes with the Node added to
    the DB most recently (inferred by autoincrement primary key).
    Link endpoints represented by all deleted Nodes will be updated to
    refer to the remaining Node.  The kept Node will NOT belong to the
    union of all Topologies from discarded Institutions; this can be
    altered with the UNION_TOPOLOGIES class constant.
    """
))
class KeepNewestNode(BaseActionType, DeduplicationActionMixin):
    name = gettext_noop('Keep Newest Node')

    element_type = ElementTypes.NODE

    required_info = []

    ACTION_MESSAGE_TEMPLATE = 'Delete Node {} in favour of newest {}.'

    # Include the Node we're keeping in the same Topologies
    # as the ones we're deleting
    UNION_TOPOLOGIES = True
    # Include the full set of owner Institutions from deleted Nodes
    # in the one we're keeping
    UNION_OWNERS = True

    def apply(self, element):
        """
        Implements the action. Finds all elements with similar IDs,
        keeps the newest, deletes the others, and updates all
        Link references to the kept Node.
        """
        action_log = ActionLog(
            self.action,
            element,
        )
        action_messages = []

        nodes_deleted = []
        links_affected = []

        duplicates = Node.objects.filter(grenml_id=element.grenml_id).order_by('-pk')

        newest = duplicates.first()
        elements_to_delete = list(duplicates)[1:]

        for node in elements_to_delete:
            action_message = self.ACTION_MESSAGE_TEMPLATE.format(
                node.log_str,
                newest.log_str,
            )
            log.debug(action_message)
            action_messages.append(action_message)

            # Obtain the list of Links attached to
            # the matched Node, for the ActionLog
            links_affected += node.links.all()

            node.replace_with(
                newest,
                union_topologies=self.UNION_TOPOLOGIES,
                union_owners=self.UNION_OWNERS,
            )
            nodes_deleted.append(node)

        action_log.result(
            '\n'.join(action_messages),
            [],
            nodes_deleted + [newest],
            links_affected,
        )
        return (newest, action_log)
