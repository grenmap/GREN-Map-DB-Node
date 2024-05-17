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

A type of action that permanently deletes all matched Links in Rules.
"""
from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from collation.constants import ElementTypes
from collation.rule_log import ActionLog
from . import BaseActionType

import logging
log = logging.getLogger('collation')


@translated_docstring(gettext_noop(
    """
    Permanently deletes matched Links.
    """
))
class DeleteLink(BaseActionType):
    name = gettext_noop('Delete Link')

    element_type = ElementTypes.LINK

    required_info = []

    ACTION_MESSAGE_TEMPLATE = 'Delete Link {}.'

    def apply(self, element):
        """
        Deletes the given Link element.
        """
        action_log = ActionLog(
            self.action,
            element,
        )
        action_message = self.ACTION_MESSAGE_TEMPLATE.format(element.log_str)

        log.debug(action_message)
        element.delete()

        action_log.result(
            action_message,
            [],
            [],
            [element],
        )
        return (None, action_log)
