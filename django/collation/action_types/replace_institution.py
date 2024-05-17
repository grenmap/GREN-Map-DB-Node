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
from network_topology.models import NetworkElement
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from collation.action_types.deduplication_action_mixin import DeduplicationActionMixin
from . import BaseActionType


import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Replaces the matched Institution (A) with the Institution specified
    by ID on the Action (B).  A replacement Institution may be further
    identified by Topology.  Ownership of Nodes and Links by A will be
    transferred to B.  A, and all of A's fields, properties, and tag,
    will be permanently deleted.  The target Institution will inherit
    Topology membership from the discarded Institution.
    """
))
class ReplaceInstitution(BaseActionType, DeduplicationActionMixin):
    name = gettext_noop('Replace with Institution')

    element_type = ElementTypes.INSTITUTION

    required_info = ['ID']
    optional_info = ['Topology ID']

    ACTION_MESSAGE_TEMPLATE = 'Delete Institution {} and replace with {}.'

    def apply(self, element):
        """
        Implements the action. Finds the Nodes and Links that belong
        to the target Institution, associates them to the substitute
        and deletes the target. Requires an ActionInfo containing the ID
        of the substitute.
        """
        self.action_log = ActionLog(
            self.action,
            element,
        )

        replacement_institution = self.identify_substitute_element(element)
        if replacement_institution is None:
            # Returning None aborts the Action chain.
            # Avoids unexpected results if the chain continues.
            return (None, self.action_log)

        action_message = self.ACTION_MESSAGE_TEMPLATE.format(
            element.log_str,
            replacement_institution.log_str,
        )
        log.debug(action_message)

        # Obtain the Nodes and Links attached to the target
        # Institution, for the ActionLog
        owned_nodes = NetworkElement.objects.filter(
            owners__in=[element],
            node__isnull=False,
        )
        owned_links = NetworkElement.objects.filter(
            owners__in=[element],
            link__isnull=False,
        )

        element.replace_with(
            replacement_institution,
            union_topologies=True,
        )

        self.action_log.result(
            action_message,
            [element, replacement_institution],
            owned_nodes,
            owned_links,
        )
        return (replacement_institution, self.action_log)
