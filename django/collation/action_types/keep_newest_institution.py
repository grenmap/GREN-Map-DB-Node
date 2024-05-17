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
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from . import BaseActionType
from network_topology.models import Institution, NetworkElement


import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Replaces all matched Institutions with the Institution added to
    the DB most recently (inferred by autoincrement primary key).
    Ownership of Nodes and Links and Topologies by all deleted
    Institutions will be transferred to the remaining Institution.
    The kept Institution will NOT belong to the union of all
    Topologies from discarded Institutions; this can be altered
    with the UNION_TOPOLOGIES class constant.
    """
))
class KeepNewestInstitution(BaseActionType):
    name = gettext_noop('Keep Newest Institution')

    element_type = ElementTypes.INSTITUTION

    required_info = []

    ACTION_MESSAGE_TEMPLATE = 'Delete Institution {} in favour of newest {}.'

    # Include the Institution we're keeping in the same Topologies
    # as the ones we're deleting
    UNION_TOPOLOGIES = True

    def apply(self, element):
        """
        Implements the action. Finds all elements with similar IDs,
        keeps the newest, deletes the others, and updates all
        node and link references to the kept institution.
        """
        action_log = ActionLog(
            self.action,
            element,
        )
        action_messages = []

        institutions_deleted = []
        nodes_affected = []
        links_affected = []

        duplicates = Institution.objects.filter(grenml_id=element.grenml_id).order_by('-pk')

        newest = duplicates.first()
        elements_to_delete = list(duplicates)[1:]

        for institution in elements_to_delete:
            action_message = self.ACTION_MESSAGE_TEMPLATE.format(
                institution.log_str,
                newest.log_str,
            )
            log.debug(action_message)
            action_messages.append(action_message)

            # Obtain the Nodes and Links attached to the matched
            # Institution, for the ActionLog
            nodes_affected += NetworkElement.objects.filter(
                owners__in=[institution],
                node__isnull=False,
            )
            links_affected += NetworkElement.objects.filter(
                owners__in=[institution],
                link__isnull=False,
            )

            institution.replace_with(
                newest,
                union_topologies=self.UNION_TOPOLOGIES,
            )
            institutions_deleted.append(institution)

        action_log.result(
            '\n'.join(action_messages),
            institutions_deleted + [newest],
            nodes_affected,
            links_affected,
        )
        return (newest, action_log)
