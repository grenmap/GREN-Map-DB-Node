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

Custom Exceptions for use with MatchTypes.
"""
from django.utils.translation import gettext_noop
from ..exceptions import RuleApplyError


class MatchFilterExtraInfoError(RuleApplyError):
    """
    Raised when a Rule is applied but one of its MatchCriteria is
    misconfigured with a MatchInfo that does not belong.
    """
    def __init__(self, rule):
        self.rule = rule
        super().__init__(
            # Translators: {} is the name of a database record created by the user  # noqa
            gettext_noop('Rule {} Match by ID expects exactly one MatchInfo'),
        )

    def create_message(self, template):
        return template.format(self.rule)


class MatchFilterMissingInfoError(RuleApplyError):
    """
    Raised when a Rule is applied but one of its MatchCriteria is
    missing a required MatchInfo.
    """
    def __init__(self, rule):
        self.rule = rule
        super().__init__(
            # Translators: {} is the name of a database record created by the user  # noqa
            gettext_noop("Rule {} Match by ID expects MatchInfo with key 'ID'"),
        )

    def create_message(self, template):
        return template.format(self.rule)
