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

Types of matches that identify elements by their GRENML ID.  (Not to be
confused with their primary key -- ID may not be unique.)
"""
from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from . import BaseMatchType, exceptions as e
from collation.constants import ElementTypes

import logging
log = logging.getLogger('collation')


class MatchByID:
    """
    Base class for DRY.  Since the filter(...) method of each of the
    BaseMatchType classes below is identical, and they all required the
    same info (['ID']), they can now inherit via multiple inheritance.

    We cannot simply subclass BaseMatchType here and let the real
    classes below single-inherit it because of the way BaseMatchType
    objects are automatically synchronized and initialized.

    Note that, for the above-mentioned automatic syncrhonization and
    initialization to be able to find these via simple .__subclasses__()
    the BaseMatchType class must be the last one in each list of
    inherited classes.
    """
    required_info = ['ID']

    def filter(self, elements_query):
        """
        Filters input elements_query Django QuerySet to just
        the Elements (Nodes, Links or Institutions) with a specified
        GRENML ID, if found.
        """
        info_tuples = self.match_criterion.info_tuples
        info_dict = self.match_criterion.info_dict
        rule = self.match_criterion.rule
        if len(info_tuples) > 1:
            raise e.MatchFilterExtraInfoError(rule)
        try:
            id = info_dict[self.required_info[0]]
        except KeyError:
            raise e.MatchFilterMissingInfoError(rule)
        filtered = elements_query.filter(grenml_id=id)
        return filtered


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Institutions with a specified
    GRENML ID.
    """
))
class MatchInstitutionsByID(MatchByID, BaseMatchType):
    name = gettext_noop('Match Institutions by ID')

    element_type = ElementTypes.INSTITUTION


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Nodes with a specified GRENML
    ID.
    """
))
class MatchNodesByID(MatchByID, BaseMatchType):
    name = gettext_noop('Match Nodes by ID')

    element_type = ElementTypes.NODE


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Links with a specified GRENML
    ID.
    """
))
class MatchLinksByID(MatchByID, BaseMatchType):
    name = gettext_noop('Match Links by ID')

    element_type = ElementTypes.LINK
