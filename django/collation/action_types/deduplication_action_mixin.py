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

import logging

from django.utils.translation import gettext_noop as _noop

from network_topology import models
from collation.constants import ElementTypes
from collation.exceptions import RuleApplyError


log = logging.getLogger('collation')


class DeduplicationActionMixin:
    """
    A mixin to add common functionality to deduplication ActionTypes
    such as Replace* and Merge*.

    Relies on the following in the class with which it mixes:
        - self.element_type
        - self.action_log
        - self.action (for its info_dict)
    """

    def _fetch_deduplication_target_element(
        self,
        starting_element,
        replacement_id,
        topology_id=None,
    ):
        """
        Queries for an element matching the parameters specified in a
        deduplication ActionType's ActionInfos.

        Raises exceptions if it is not possible to find a distinct
        substitute element.

        Returns the target substitute element.
        """
        model = None
        if self.element_type == ElementTypes.LINK:
            model = models.Link
        if self.element_type == ElementTypes.NODE:
            model = models.Node
        if self.element_type == ElementTypes.INSTITUTION:
            model = models.Institution

        # Filter by GRENML ID
        query = model.objects.filter(grenml_id=replacement_id)

        # Further filter by Topology, if specified
        if topology_id is not None:
            try:
                topology = models.Topology.objects.get(grenml_id=topology_id)
            except models.Topology.DoesNotExist:
                raise NoSubstituteElementError(self.element_type)
            query = query.filter(topologies=topology)

        if not query.exists():
            raise NoSubstituteElementError(self.element_type)

        if query.count() > 1:
            raise MultipleSubstituteElementsError(self.element_type)

        target_element = query.get()
        return target_element

    def _validate_deduplication_target_element(self, starting_element, target_element):
        """
        Validates that the identified target substitute element is
        not the same element as the Action is starting with.
        """
        if target_element == starting_element:
            raise SourceIsTargetError(self.element_type.label, starting_element.name)
        return True

    def identify_substitute_element(self, element):
        """
        Helper function to identify the substitute element.
        Requires: input element, and a pointer to the ActionLog
        in case there is an error.

        If there are any issues identifying a distinct suitable
        element, it signals an abort to the ActionLog and returns None,
        intending for the caller to bubble that None return and
        thus abort the chain of Actions.
        """
        id_key = self.required_info[0]
        topology_id_key = self.optional_info[0]

        indicated_substitute_element_id = self.action.info_dict[id_key]
        try:
            indicated_substitute_element_topology_id = self.action.info_dict[topology_id_key]
        except KeyError:
            indicated_substitute_element_topology_id = None

        try:
            target_substitute_element = self._fetch_deduplication_target_element(
                element,
                indicated_substitute_element_id,
                topology_id=indicated_substitute_element_topology_id,
            )
            self._validate_deduplication_target_element(
                element,
                target_substitute_element,
            )
            return target_substitute_element
        except (
            NoSubstituteElementError,
            MultipleSubstituteElementsError,
            SourceIsTargetError,
        ) as e:
            self.action_log.abort(e.translated_message())
            return None

    def merge_properties(self, match_element, merge_into_element):
        """
        Merge extra properties from match element to merge_into element:
            1. The identical property key-value pair already exists on
                both match and merge-into element, it is not duplicated
                on the target.
            2. If a key "tag" is key matches, but value is different it
                is added as another property on the target.
            3. If the key matches (and is not tag) the property is not
                added to nor overwritten. e.g. key is 'description'.
                i.e. Prefer the original.
        """
        try:
            match_properties = match_element.properties.all()
            merge_into_properties = merge_into_element.properties.all()
            merge_into_properties_names = [property.name for property in merge_into_properties]
            merge_into_tags = [
                property.value for property in merge_into_properties if property.name == 'tag']
            for match_property in match_properties:
                if match_property.name in merge_into_properties_names:
                    if (
                        match_property.name == 'tag'
                        and match_property.value not in merge_into_tags
                    ):
                        match_property.property_for = merge_into_element
                        match_property.save()
                    else:
                        match_property.delete()
                else:
                    match_property.property_for = merge_into_element
                    match_property.save()
        except:  # noqa: E722
            log.exception('Unable to merge properties for  ' + merge_into_element.id)
            raise

    def merge_model_fields(self, match_element, merge_into_element):
        """
        Merge the model fields from match element to merge_into element
        """
        try:
            for field in match_element._meta.fields:
                if getattr(merge_into_element, field.name) is None:
                    new_value = getattr(match_element, field.name)
                    if new_value is not None:
                        setattr(merge_into_element, field.name, new_value)

            merge_into_element.save()
        except:  # noqa: E722
            log.exception('Unable to merge model fields for  ' + merge_into_element.id)
            raise


class NoSubstituteElementError(RuleApplyError):
    """
    Error raised by the replace action types when it is not possible
    to find the substitute element.
    """
    def __init__(self, element_type):
        self.element_type = element_type
        # Translators: {} is the name of a database record created by the user  # noqa
        self.message_template = _noop('Could not find the substitute {}.')
        super().__init__()

    def create_message(self, template):
        return template.format(self.element_type)


class MultipleSubstituteElementsError(RuleApplyError):
    """
    Error raised by the replace action types when it is not possible
    to identify a distinct substitute element among similar elements.
    """
    def __init__(self, element_type):
        self.element_type = element_type
        # Translators: {} is the name of a database record created by the user  # noqa
        self.message_template = _noop('Found too many substitute {} elements.')
        super().__init__()

    def create_message(self, template):
        return template.format(self.element_type)


class SourceIsTargetError(RuleApplyError):
    """ The substitute element and the target should be different. """

    def __init__(self, element_type, element_name):
        self.element_type = element_type
        self.element_name = element_name
        self.message_template = _noop('{type} "{name}" is both target and replacement/merge_into.')
        super().__init__()

    def create_message(self, template):
        return template.format(type=self.element_type, name=self.element_name)


class DifferentEndpointsError(RuleApplyError):
    """
    The replacement link should have the same endpoints
    as the target link.
    """
    def __init__(self, target_name, replacement_name):
        self.target_name = target_name
        self.replacement_name = replacement_name
        self.message_template = _noop(
            'Links "{target}" and "{replacement}" '
            'have different endpoints.'
        )
        super().__init__()

    def create_message(self, template):
        return template.format(
            target=self.target_name,
            replacement=self.replacement_name,
        )
