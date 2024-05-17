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

Types of matches that identify single elements by ID.
"""
from django.utils.translation import gettext_noop

from django.db.models import Count

from base_app.utils.decorators import translated_docstring
from . import BaseMatchType
from collation.constants import ElementTypes


class MatchByIDDuplicate:
    """
    Base class for DRY.  Since the filter(...) method of each of the
    BaseMatchType classes below is identical, they can now inherit via
    multiple inheritance.

    We cannot simply subclass BaseMatchType here and let the real
    classes below single-inherit it because of the way BaseMatchType
    objects are automatically synchronized and initialized.

    Note that, for the above-mentioned automatic syncrhonization and
    initialization to be able to find these via simple .__subclasses__()
    the BaseMatchType class must be the last one in each list of
    inherited classes.
    """
    required_info = []

    def filter(self, elements_query):
        """
        Filters input elements_query Django QuerySet to just
        the Elements (Node, Link or Institution) that share IDs with
        other Elements of the same type in the database.
        """
        # Query should return a list of dictionaries including only IDs
        # where the ID is duplicated within the input list of elements.
        # The duplicates remain.
        duplicate_ids = elements_query.values(
            'grenml_id',
        ).annotate(
            Count('grenml_id')
        ).order_by(
        ).filter(
            grenml_id__count__gt=1
        )
        deduplicated_duplicate_ids = set([x['grenml_id'] for x in duplicate_ids])
        filtered = elements_query.filter(grenml_id__in=deduplicated_duplicate_ids)
        return filtered


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Institution with a specified ID.
    """
))
class MatchInstitutionsByIDDuplicate(MatchByIDDuplicate, BaseMatchType):
    name = gettext_noop('Match Duplicate Institutions')

    element_type = ElementTypes.INSTITUTION


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Node with a specified ID.
    """
))
class MatchNodesByIDDuplicate(MatchByIDDuplicate, BaseMatchType):
    name = gettext_noop('Match Duplicate Nodes')

    element_type = ElementTypes.NODE


@translated_docstring(gettext_noop(
    """
    Filters input elements to just the Link with a specified ID.
    """
))
class MatchLinksByIDDuplicate(MatchByIDDuplicate, BaseMatchType):
    name = gettext_noop('Match Duplicate Links')

    element_type = ElementTypes.LINK
