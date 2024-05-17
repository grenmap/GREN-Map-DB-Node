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
from network_topology.models import Link
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from . import BaseActionType


import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Replaces all matched Links with the Link added to
    the DB most recently (inferred by autoincrement primary key).
    The kept Link will NOT belong to the union of all Topologies from
    discarded Links; this can be altered with the UNION_TOPOLOGIES
    class constant.
    """
))
class KeepNewestLink(BaseActionType):
    name = gettext_noop('Keep Newest Link')

    element_type = ElementTypes.LINK

    required_info = []

    ACTION_MESSAGE_TEMPLATE = 'Delete Link {} in favour of newest {}.'

    # Include the Link we're keeping in the same Topologies
    # as the ones we're deleting
    UNION_TOPOLOGIES = True
    # Include the full set of owner Institutions from deleted Links
    # in the one we're keeping
    UNION_OWNERS = True

    def apply(self, element):
        """
        Implements the action. Finds all elements with similar IDs,
        keeps the newest, deletes the others.
        """
        action_log = ActionLog(
            self.action,
            element,
        )
        action_messages = []

        links_deleted = []

        duplicates = Link.objects.filter(grenml_id=element.grenml_id).order_by('-pk')

        newest = duplicates.first()
        elements_to_delete = list(duplicates)[1:]

        for link in elements_to_delete:
            action_message = self.ACTION_MESSAGE_TEMPLATE.format(
                link.log_str,
                newest.log_str,
            )
            log.debug(action_message)
            action_messages.append(action_message)

            link.replace_with(
                newest,
                union_topologies=self.UNION_TOPOLOGIES,
                union_owners=self.UNION_OWNERS,
            )
            links_deleted.append(link)

        action_log.result(
            '\n'.join(action_messages),
            [],
            [],
            links_deleted + [newest],
        )
        return (newest, action_log)
