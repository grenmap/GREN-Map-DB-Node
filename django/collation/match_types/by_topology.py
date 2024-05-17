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

Types of matches that identify elements based on what Topology they are
    in, by Topology GRENML ID.
"""

import logging

from django.utils.translation import gettext_noop

from base_app.utils.decorators import translated_docstring
from . import BaseMatchType, exceptions as e
from collation.constants import ElementTypes


log = logging.getLogger('collation')


class MatchByTopology:
    """
    Base class for DRY.  Since the filter(...) method of each of the
    BaseMatchType classes below is identical, and they all required the
    same info (['Topology ID']), they can inherit via multiple
    inheritance/composition.

    We cannot simply subclass BaseMatchType here and let the real
    classes below single-inherit it because of the way BaseMatchType
    objects are automatically synchronized and initialized.

    Note that, for the above-mentioned automatic syncrhonization and
    initialization to be able to find these via simple .__subclasses__()
    the BaseMatchType class must be the last one in each list of
    inherited classes.
    """
    required_info = ['Topology ID']

    def filter(self, elements_query):
        """
        Filters input elements_query Django QuerySet to just
        the Elements (Nodes, Links or Institutions) within a specified
        Topology (by the Topology's ID), if found.

        Note that Topologies, unlike the elements within them, are
        guaranteed to have unique GRENML IDs.
        """
        info_tuples = self.match_criterion.info_tuples
        info_dict = self.match_criterion.info_dict
        rule = self.match_criterion.rule
        if len(info_tuples) > 1:
            raise e.MatchFilterExtraInfoError(rule)
        try:
            topology_id = info_dict[self.required_info[0]]
        except KeyError:
            raise e.MatchFilterMissingInfoError(rule)
        filtered = elements_query.filter(topologies__grenml_id=topology_id)
        return filtered


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Institutions within a
    specified Topology (by its ID).

    Often likely combined with other MatchType filters in Rules.
    """
))
class MatchInstitutionsByTopology(MatchByTopology, BaseMatchType):
    name = gettext_noop('Match Institutions by Topology')

    element_type = ElementTypes.INSTITUTION


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Nodes within a specified
    Topology (by its ID).

    Often likely combined with other MatchType filters in Rules.
    """
))
class MatchNodesByTopology(MatchByTopology, BaseMatchType):
    name = gettext_noop('Match Nodes by Topology')

    element_type = ElementTypes.NODE


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Links within a specified
    Topology (by its ID).

    Often likely combined with other MatchType filters in Rules.
    """
))
class MatchLinksByTopology(MatchByTopology, BaseMatchType):
    name = gettext_noop('Match Links by Topology')

    element_type = ElementTypes.LINK
