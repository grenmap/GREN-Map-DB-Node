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
    Merges the matched Link (A) into the Link specified by ID on the
    Action (B).  A merge target Link may be further identified by
    Topology.  Fields in A will be transferred to B if they don't
    already exist in B.  All properties of and tag on A will be added
    to B.  B will inherit all Topology memberships from A.
    A will be permanently deleted.
    """
))
class MergeLink(BaseActionType, DeduplicationActionMixin):
    name = gettext_noop('Merge into Link')

    element_type = ElementTypes.LINK

    required_info = ['ID']
    optional_info = ['Topology ID']

    ACTION_MESSAGE_TEMPLATE = 'Merge Link {} into {}.'

    def apply(self, element):
        """
        Deletes the Link in the elements list. Finds the Link
        identified by the action_info parameter. Checks that
        the matched Link has the same endpoints as the merge target.
        """
        self.action_log = ActionLog(
            self.action,
            element,
        )

        merge_target_link = self.identify_substitute_element(element)
        if merge_target_link is None:
            # Returning None aborts the Action chain.
            # Avoids unexpected results if the chain continues.
            return (None, self.action_log)

        action_message = self.ACTION_MESSAGE_TEMPLATE.format(
            element.log_str,
            merge_target_link.log_str,
        )
        log.debug(action_message)

        # Verify endpoints are equal
        match_endpoints = {element.node_a, element.node_b}
        merge_into_endpoints = {merge_target_link.node_a, merge_target_link.node_b}
        if match_endpoints != merge_into_endpoints:
            self.action_log.abort(DifferentEndpointsError(
                element.log_str,
                merge_target_link.log_str,
            ).translated_message())
            return (None, self.action_log)

        self.merge_model_fields(element, merge_target_link)
        self.merge_properties(element, merge_target_link)

        element.replace_with(
            merge_target_link,
            union_topologies=True,
            union_owners=True,
        )

        self.action_log.result(
            action_message,
            [],
            [],
            [element, merge_target_link],
        )
        return (merge_target_link, self.action_log)
