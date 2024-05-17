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

Synopsis: This file contains the django ORM models for the
components of a GRENML file
"""

import logging
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


log = logging.getLogger(__file__)


def delete_objects(delete_lists):
    """
    Loop over all of the objects in dict lists and
    delete them in order of relation.
    We explicitly define delete order to simplify the number
    of database calls that occur while deleting, otherwise we may end
    up trying to delete objects that have already been deleted
    """
    for model_type in ['links', 'nodes', 'institutions', 'topologies']:
        for item_to_delete in delete_lists[model_type]:
            item_to_delete.delete()


class CascadeDeleteQuerySet(models.query.QuerySet):
    """
    This queryset allows for deleting many objects that have
    many to many relations that need referenced objects to be
    deleted if the list of references to the current model reaches 0.
    """

    def delete(self):
        # Unique set of things to delete
        delete_sets = {
            'topologies': set(),
            'nodes': set(),
            'links': set(),
            'institutions': set()
        }
        # Loop over all objects slated for deletion in the queryset
        for parent in self:
            # Get the objects that should be deleted if the
            # current object is deleted
            del_objs = parent.get_delete_objects()
            # Then loop over the returned dict
            # and add the values for each model
            # to the set of elements to delete
            for model_type in del_objs:
                delete_sets[model_type].update(del_objs[model_type])

        delete_objects(delete_sets)


class CascadeDeleteManager(models.Manager):
    """
    This manager provides an overriden queryset
    that performs a more in depth delete for models with
    a many to many relationship that can cascade
    """

    def get_queryset(self):
        return CascadeDeleteQuerySet(self.model, using=self._db)


class Location(models.Model):
    """
    A Location is a reference to a geographical location or area.
    Designed to be subclassed with multiple inheritance by any model
    requiring an address.
    """
    # South Pole to North Pole (approximate)
    LATITUDE_RANGE = (-90.0, 90.0)
    # 180th meridian
    LONGITUDE_RANGE = (-180.0, 180.0)
    # Mariana Trench to Mount Everest (approximate)
    ALTITUDE_RANGE = (-11000, 9000)
    # Support satellites
    SUPPORTED_ORBIT_ALTITUDE = None

    # Prefer using coordinates(...) property vs direct field access
    # from Python code, to benefit from automatic truncation.
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        verbose_name=_('WGS84 Latitude, in decimal degrees'),
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        verbose_name=_('WGS84 Longitude, in decimal degrees'),
    )
    altitude = models.DecimalField(
        max_digits=16, decimal_places=6, null=True, blank=True,
        verbose_name=_('Altitude'),
        help_text=_('The height of the location from sea level, in metres'),
    )

    unlocode = models.CharField(
        max_length=5, null=True, blank=True,
        verbose_name=_('UN/LOCODE'),
    )

    address = models.CharField(
        max_length=500, null=True, blank=True,
        verbose_name=_('Address Line'),
    )

    class Meta:
        abstract = True
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')

    def __str__(self):
        return self.get_full_address()

    def get_full_address(self):
        """
        Return a text list of address fields present in the object,
        by line.
        """
        fields_to_display = list()
        if self.address:
            fields_to_display.append(self.address)
        if self.latitude and self.longitude:
            fields_to_display.append('%s, %s' % (self.latitude, self.longitude))
        return '\n'.join(fields_to_display)

    def set_address(self, address):
        """
        Sets the address field; trims to max length automatically.
        """
        return self._set_trimmed_field('address', address)

    def set_unlocode(self, unlocode):
        """
        Sets the UN/LOCODE field; trims to max length automatically.
        """
        return self._set_trimmed_field('unlocode', unlocode)

    @staticmethod
    def _truncate_decimal_value(value, meta, range=None):
        """
        Helper method for the "coordinates" property to ensure
        decimal values for latitude, longitude, and altitude
        are rounded or truncated as well as possible when they
        are outside acceptable ranges (either based on the
        *_RANGE class constants or the model fields themselves)
        or precisions.

        Table for input cases: output modification
            - Within range and field parameters: unmodified
            - None: 0.0
            - Too low for range: capped to range minimum
            - Too high for range: capped to range maximum
            - Too many digits: capped to field maximum
                * respects input sign
                * unlikely to occur if ranges are appropriate
            - Too much precision: rounded appropriately
        """
        if value is None:
            log.debug('Decimal value missing.  Defaulting to 0.0.')
            return 0.0

        # Sanity check on requested range.
        # Proceeds with best effort with with just a log error to
        # avoid halting the program on silly errors that may not be
        # immediately apparent or detected quickly.
        try:
            if range is not None and range[1] <= range[0]:
                log.error(f'Error: incompatible Location range {str(range)}')
                range = None
        except (TypeError, IndexError):
            log.error(f'Error: incorrect Location range {str(range)}')
            range = None

        # Truncate based on adherence to specified value range
        if range is not None:
            if value < range[0]:
                log.debug(f'Capping decimal value {value} to range {range[0]}-{range[1]}.')
                value = range[0]
            if value > range[1]:
                log.debug(f'Capping decimal value {value} to range {range[0]}-{range[1]}.')
                value = range[1]

        whole_digits_length = meta.max_digits - meta.decimal_places

        # Verify that the decimal places aren't more than allowed limit
        places = Decimal(value).as_tuple().exponent
        if places < -meta.decimal_places:
            rounded_value = round(value, meta.decimal_places)
            log.debug(f'{value} is too precise; rounded to {rounded_value}.')
            value = rounded_value

        # Verify the number is not larger than permitted
        if abs(value) > pow(10, whole_digits_length):
            max_value = pow(10, whole_digits_length) - pow(10, -meta.decimal_places)
            # Handle negative "too large" numbers by flipping the sign
            if value < 0:
                max_value *= -1
            log.debug(f'{value} is too large; substituted for a maximum value of {max_value}.')
            value = max_value

        return value

    @property
    def coordinates(self):
        """
        Returns a tuple of co-ordinates like: (lat, long, alt)
        """
        return (self.latitude, self.longitude, self.altitude)

    @coordinates.setter
    def coordinates(self, lat_long_alt_tuple):
        """
        Accepts a tuple of co-ordinates like: (lat, long, alt).
        Truncates values automatically as required for the model field.
        """
        (latitude, longitude, altitude) = lat_long_alt_tuple

        self.latitude = self._truncate_decimal_value(
            latitude,
            self._meta.get_field('latitude'),
            self.LATITUDE_RANGE,
        )

        self.longitude = self._truncate_decimal_value(
            longitude,
            self._meta.get_field('longitude'),
            self.LONGITUDE_RANGE,
        )

        altitude_range = self.ALTITUDE_RANGE
        if self.SUPPORTED_ORBIT_ALTITUDE:
            altitude_range[1] = self.SUPPORTED_ORBIT_ALTITUDE
        self.altitude = self._truncate_decimal_value(
            altitude,
            self._meta.get_field('altitude'),
            altitude_range,
        )


class Lifetime(models.Model):
    """
    An interval between which the object is said to be active.
    The time and date formatted as ISO 8601 calendar date, and should
    be a basic (compact) representation with UTC timezone
    """
    # The start time and date
    start = models.DateTimeField(null=True, blank=True, verbose_name=_('start time and date'))
    # The end time and date
    end = models.DateTimeField(null=True, blank=True, verbose_name=_('end time and date'))

    def __str__(self):
        return f'{self.start} - {self.end}'

    class Meta:
        abstract = True
        verbose_name = _('Lifetime')
        verbose_name_plural = _('Lifetimes')


class ShortNamed(models.Model):
    """
    Simple class for adding a short name to a model
    """
    # Abbreviated label of the element
    # Python code should use .set_short_name('<short name>') to set
    short_name = models.CharField(
        max_length=32, null=True, blank=True,
        verbose_name=_('Short Name'),
    )

    def set_short_name(self, short_name):
        """
        Sets the short_name field, trimming to max length if necessary.
        """
        return self._set_trimmed_field('short_name', short_name)

    def set_names(self, name, short_name):
        """
        Sets the name and short_name fields;
        trims to max length automatically.
        """
        _, name_msg = self.set_name(name)
        _, short_name_msg = self.set_short_name(short_name)
        return (name_msg, short_name_msg)

    class Meta:
        abstract = True
