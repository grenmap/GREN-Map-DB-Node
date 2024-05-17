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
    Merges the matched Institution (A) into the Institution specified
    by ID on the Action (B).  A merge target Institution may be further
    identified by Topology.  Fields in A will be transferred to B if
    they don't already exist in B.  All properties of and tag on A
    will be added to B.  Ownership of Nodes and Link by A will be
    transferred to B.  B will inherit all Topology memberships from A.
    A will be permanently deleted.
    """
))
class MergeInstitution(BaseActionType, DeduplicationActionMixin):
    name = gettext_noop('Merge into Institution')

    element_type = ElementTypes.INSTITUTION

    required_info = ['ID']
    optional_info = ['Topology ID']

    ACTION_MESSAGE_TEMPLATE = 'Merge Institution {} into {}.'

    def apply(self, element):
        """
        Implements the action. Finds the nodes and links that belong
        to the match institution, associates them to the merge into
        institution and deletes the match. Requires an ActionInfo
        containing the id of the merge into institution.
        """
        self.action_log = ActionLog(
            self.action,
            element,
        )

        merge_target_institution = self.identify_substitute_element(element)
        if merge_target_institution is None:
            # Returning None aborts the Action chain.
            # Avoids unexpected results if the chain continues.
            return (None, self.action_log)

        action_message = self.ACTION_MESSAGE_TEMPLATE.format(
            element.log_str,
            merge_target_institution.log_str,
        )
        log.debug(action_message)

        # Obtain the Nodes and Links attached to the given Institution,
        # for the ActionLog
        owned_nodes = NetworkElement.objects.filter(
            owners__in=[element],
            node__isnull=False,
        )
        owned_links = NetworkElement.objects.filter(
            owners__in=[element],
            link__isnull=False,
        )

        self.merge_model_fields(element, merge_target_institution)
        self.merge_properties(element, merge_target_institution)

        element.replace_with(
            merge_target_institution,
            union_topologies=True,
        )

        self.action_log.result(
            action_message,
            [element, merge_target_institution],
            owned_nodes,
            owned_links,
        )
        return (merge_target_institution, self.action_log)
