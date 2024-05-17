"""
Copyright 2020 GRENMap Authors

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

import string

from django import forms
from django.utils.translation import gettext as _
from base_app.utils.custom_configuration import CustomConfiguration


class VisualizationEnabledSetting(CustomConfiguration):

    name = 'GREN_MAP_VISUALIZATION_ENABLED'
    display_name = 'GREN Map Visualization Enabled'
    default_value = 'True'
    description = _(
        # Translators: 'True' and 'False' should remain in English, do not translate  # noqa
        'Value must be \'True\' or \'False\''
    )

    def clean(self, value):
        """
        Checks that the value is either true or false
        """
        if value == 'True' or value == 'False':
            return
        raise forms.ValidationError(self.description, code='invalid')


COORDS_FORMAT = _(
    'Please enter latitude and longitude '
    'between parentheses: (latitude, longitude).'
)
LATITUDE_RANGE = _(
    'The valid range for latitude is '
    'from -90 (South Pole) to 90 (North Pole).'
)
LONGITUDE_RANGE = _(
    'The valid range for longitude is '
    'from -180 to 180.'
)


class InitialCoordinatesSetting(CustomConfiguration):

    name = 'GREN_MAP_INITIAL_COORDINATES'
    display_name = 'GREN Map Initial Coordinates'
    default_value = (0, 0)
    description = '{} {} {}'.format(
        COORDS_FORMAT,
        LATITUDE_RANGE,
        LONGITUDE_RANGE,
    )

    def clean(self, value):
        """
        This method checks if its argument is a valid pair of
        geographical coordinates represented as a string.

        It returns a latitude, longitude pair formatted as a string.
        It raises ValidationError if the argument is not a string, or
        if it is not a pair of numbers separated by a comma.
        The method accepts a pair of number with missing parentheses.
        """
        try:
            # remove whitespace and parentheses
            numbers_separated_by_comma = value.translate(
                {ord(ch): '' for ch in (string.whitespace + '()')},
            )
            # remove comma
            numbers_as_str = numbers_separated_by_comma.split(',')
            # convert to numeric values
            numbers = [float(n) for n in numbers_as_str]

            if len(numbers) == 2:
                format_ok = True

                latitude = numbers[0]
                latitude_ok = (-90 <= latitude) and (latitude <= 90)
                longitude = numbers[1]
                longitude_ok = (-180 <= longitude) and (longitude <= 180)
            else:
                format_ok = False
        except Exception:
            format_ok = False

        if not format_ok:
            raise forms.ValidationError(COORDS_FORMAT, code='invalid')

        if not latitude_ok:
            raise forms.ValidationError(LATITUDE_RANGE, code='invalid')

        if not longitude_ok:
            raise forms.ValidationError(LONGITUDE_RANGE, code='invalid')

        return '({}, {})'.format(latitude, longitude)


class InitialMapZoomSetting(CustomConfiguration):

    name = 'GREN_MAP_INITIAL_MAP_ZOOM'
    display_name = 'GREN Map Initial Zoom'
    default_value = 3
    description = _('The zoom setting must be a positive number')

    def clean(self, value):
        try:
            numeric_value = float(value)
            valid = numeric_value > 0
        except Exception:
            valid = False

        if not valid:
            raise forms.ValidationError(self.description, code='invalid')


class VisualizationCachedSetting(CustomConfiguration):

    name = 'GREN_MAP_VISUALIZATION_CACHED'
    display_name = 'GREN Map Visualization Data Caching Enabled'
    default_value = 'False'
    description = _(
        # Translators: 'True' and 'False' should remain in English, do not translate  # noqa
        'Value must be \'True\' or \'False\''
    )

    def clean(self, value):
        """
        Checks that the value is either true or false
        """
        if value == 'True' or value == 'False':
            return
        raise forms.ValidationError(self.description, code='invalid')
