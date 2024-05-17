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
"""

import logging

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

log = logging.getLogger('collation')


class RuleApplyError(Exception):
    """
    Base class for errors that may happen when we apply a Rule.

    Subclasses should set message_template, in English, wrapped in
    gettext_noop.  It will be used in English for logs, and localized
    when shown in the UI.

    They should also provide an implementation for the create_message
    method, which will interpolate the message_template's variables.
    """
    def __init__(self):
        super().__init__(self.create_message(self.message_template))

    def create_message(self, template):
        raise NotImplementedError('Subclasses must implement create_message')

    def translated_message(self):
        translated_message_template = _(self.message_template)
        return self.create_message(translated_message_template)


class ConflictingElementTypesValidationError(ValidationError):
    """
    Validation clean/klean raises this error if the element_types of all
    Rule's Components (MatchCriteria & Actions) don't share a
    common element_type.
    """
    def __init__(self, rule):
        message = _('MatchCriteria and Actions with different element types')
        super().__init__(message)


class ConflictingElementTypesError(RuleApplyError):
    """
    Rule.element_types (called by .apply) raises this error if the
    element_types of all Rule's Components (MatchCriteria & Actions)
    don't share a common element_type.
    """
    def __init__(self, rule):
        self.rule = rule
        self.message_template = _(
            # Translators: {} is the name of a database record created by the user  # noqa
            'Rule {} has MatchCriteria and Actions with different element_types'
        )
        super().__init__()

    def create_message(self, template):
        return template.format(self.rule)


class IncorrectMatchInfosError(RuleApplyError):
    """
    Rule.element_types (called by .apply) raises this error if there
    is a missing or incompatible MatchInfo encountered.
    """
    def __init__(self, rule):
        self.rule = rule
        # Translators: {} is the name of a database record created by the user  # noqa
        self.message_template = _('Incompatible Match Info for Rule {}')
        super().__init__()

    def create_message(self, template):
        return template.format(self.rule)


class IncorrectActionInfosError(RuleApplyError):
    """
    Rule.element_types (called by .apply) raises this error if there
    is a missing or incompatible ActionInfo encountered.
    """
    def __init__(self, rule):
        self.rule = rule
        # Translators: {} is the name of a database record created by the user  # noqa
        self.message_template = _('Incompatible Action Info for Rule {}')
        super().__init__()

    def create_message(self, template):
        return template.format(self.rule)


class IncorrectMatchInfosValidationError(ValidationError):
    """
    Validation clean/klean raises this error if the MatchInfo keys
    don't align perfectly with the MatchType's required_info.
    """
    def __init__(self, match_criterion, match_info_keys, required_match_info_keys):
        message = _(
            # Translators: {}'s are the names of database records created by the user  # noqa
            'This Rule\'s {} Match Criterion must include exactly one Match Info '
            'for each of these keys: {}'
        ).format(
            _(match_criterion.match_type.name),
            ', '.join(required_match_info_keys),
        )
        super().__init__(message)


class IncorrectActionInfosValidationError(ValidationError):
    """
    Validation clean/klean raises this error if the ActionInfo keys
    don't align perfectly with the ActionType's required_info.
    """
    def __init__(self, action_criterion, action_info_keys, required_action_info_keys):
        message = _(
            # Translators: {}'s are the names of database records created by the user  # noqa
            'This Rule\'s {} Action must include exactly one Action Info '
            'for each of these keys: {}'
        ).format(
            _(action_criterion.action_type.name),
            ', '.join(required_action_info_keys),
        ),
        super().__init__(message)


class NoMatchCriteriaError(ValidationError):
    """
    Rule.apply raises this error if the rule
    doesn't have any MatchCriteria.
    """
    def __init__(self, rule):
        self.rule = rule
        super().__init__(_(
            # Translators: {} is the name of a database record created by the user  # noqa
            'No MatchCriteria associated to Rule {}.'
        ).format(self.rule))


class NoActionsError(ValidationError):
    """
    Rule.apply raises this error if the rule
    doesn't have any Actions.
    """
    def __init__(self, rule):
        self.rule = rule
        super().__init__(_(
            # Translators: {} is the name of a database record created by the user  # noqa
            'No Actions associated to Rule {}.'
        ).format(self.rule))


class UnsupportedMatchTypeError(ValidationError):
    """
    Raised for MatchCriteria whose MatchTypes
    are not yet implemented.
    """
    def __init__(self, match_criterion):
        self.match_criterion = match_criterion
        super().__init__(_(
            # Translators: {}'s are the names of database records created by the user  # noqa
            'MatchCriterion {} has unsupported MatchType with name "{}"'
        ).format(
            self.match_criterion,
            self.match_criterion.match_type.name,
        ))


class UnsupportedActionTypeError(ValidationError):
    """
    Raised for Actions whose ActionTypes
    are not yet implemented.
    """
    def __init__(self, action):
        self.action = action
        super().__init__(_(
            # Translators: {}'s are the names of database records created by the user  # noqa
            'Action {} has unsupported ActionType with name "{}"'
        ).format(
            self.action,
            self.action.action_type.name,
        ))
