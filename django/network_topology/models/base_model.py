"""
Copyright 2023 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.core.exceptions import ValidationError


import logging
log = logging.getLogger('network_topology')


def get_subclasses(cls):
    """
    Recursively finds all subclasses of a given class
    """
    for subclass in cls.__subclasses__():
        yield from get_subclasses(subclass)
        yield subclass


def auto_uuid():
    """
    Return an unique UUID
    """
    unique_id = uuid4()
    # guarantee uniqueness
    while BaseModel.objects.filter(grenml_id=unique_id).exists():
        unique_id = uuid4()
    return unique_id


def truncate_id_for_display(id):
    """
    For long IDs (often UUIDs), show just first six and last six chars:
    "03c5a18e28e4085dd27e21cd86b0c661f9653d3cb42c407b94f8eac2ecb2755f"
    becomes "03c5a1...b2755f"
    """
    id = str(id)
    if len(id) > 15:
        id = id[0:6] + '...' + id[-6:]
    return id


class ModelUtils:
    """
    Injects some common utility functions into GRENML element models.
    """
    # For any model objects composed of this class,
    # Set this class constant to include the names of all fields that
    # ought to be trimmed if they exceed the maximum character length
    TRIMMED_FIELDS = []

    def _init_trimmed_fields(self, **kwargs):
        """
        Runs the string trim function on values supplied during object
        instantiation via kwargs.  All final models should call this
        in their __init__ methods.  Returns a potentially-modified
        dictionary of kwargs, to be passed up the __init__ chain.
        """
        for (kwarg, val) in kwargs.items():
            if kwarg in self.TRIMMED_FIELDS:
                potentially_trimmed_value = self._set_trimmed_field(
                    kwarg,
                    kwargs[kwarg],
                    log_enabled=False,
                )
                kwargs[kwarg], _ = potentially_trimmed_value
        return kwargs

    def _set_trimmed_field(self, fieldname, value, log_enabled=True):
        """
        If a given string value destined for a specified model field
        is greater than the max noted in the model field's max_length
        parameter, trims the string and appends an ellipsis suffix to
        indicate the trim.
        The 'log_enabled' parameter allows disabling message creation
        and logging to avoid problems with the log_str method trying
        to operate on the not-yet-fully-created object.  Note that
        this means that trimming during direct object instantiation
        or manager object instantiation will occur silently.

        Returns a tuple of:
            - the trimmed value
            - an appropriate message string, if applicable
        """
        msg = None
        if not isinstance(value, str):
            if value is None:
                value = ''
            else:
                value = str(value)

        max_length = self._meta.get_field(fieldname).max_length

        if len(value) > max_length:
            trimmed_value = str(value)[0:max_length - 3] + '...'
            if log_enabled:
                msg = '{} {} truncated from "{}" to correct length as "{}"'.format(
                    self.log_str,
                    fieldname,
                    value,
                    trimmed_value,
                )
                log.debug(msg)
            value = trimmed_value

        setattr(self, fieldname, value)
        return (value, msg)


class BaseModel(models.Model, ModelUtils):
    """
    Base model for representing data in GRENML
    """
    # External (GRENML) ID
    # Duplicates are possible, to allow control over deduplication,
    # but it is discouraged to maintain elements with duplicate IDs
    # in the database indefinitely.
    grenml_id = models.CharField(
        max_length=128,
        null=False, blank=True,
        default=auto_uuid,
        verbose_name=_('GRENML ID'),
        help_text=_(
            'Supply a unique ID for this item.<br />'
            'Minimum: UUID or hash.<br />'
            'Good: ID consistent with your REN records, (beware publishing sensitive data).<br />'
            'Best: namespace-prefix the above somehow to avoid collisions.<br />'
            'Example: "myren-sunlighttransatlantic47"<br />'
            'Ideally co-ordinate with other RENs for common IDs of shared infrastructure.<br />'
            'If omitted, an ID will be auto-generated for this object.'
        ),
    )

    # Descriptive name of the element
    # Python code should use .set_name('<name>') to set
    name = models.CharField(
        max_length=128,
        verbose_name=_('Name'),
    )

    # Version of the element
    version = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Version'),
        default=now,
    )

    dirty = models.BooleanField(
        null=False,
        default=False,
        verbose_name=_('dirty'),
    )

    def __str__(self):
        return f'{self.name} <{truncate_id_for_display(self.grenml_id)}> [{self.pk}]'

    @property
    def log_str(self):
        """
        Identifying string suitable for inclusion in a log message.
        """
        return f'{self.name} <{self.grenml_id}> [{self.pk}]'

    def clean(self):
        """
        This prevents assigning the the same ID in the Django Admin
        interface.  This is discouraged even though it is technically
        allowed, to avoid confusion and encourage best practices.
        """
        self.validate_id()
        super().clean()

    def validate_id(self):
        """
        Detects duplication of an existing GRENML ID among Topology,
        Institution, Node, and Link objects.  Raises a
        ValidationError if the ID would conflict.
        """
        log.debug('Validating ID %s has no existing duplicates.', self.grenml_id)
        cls_list = get_subclasses(BaseModel)
        for cls in cls_list:
            if self.pk is not None:
                # Object exists in DB already; this is an update
                # Omit the object itself from the search for conflicts
                query = cls.objects.exclude(pk=self.pk)
            else:
                # Object does not exist in DB already; this is a create
                # We just need to look for other elements with this ID
                query = cls.objects.all()
            if query.filter(grenml_id=self.grenml_id).exists():
                raise ValidationError(
                    # Translators: {} is the name of a database record created by the user  # noqa
                    _('This ID already exists in {}'.format(cls.__name__)),

                    # Translators: {} is the name of a database record created by the user  # noqa
                    code=_('This ID already exists in {}'.format(cls.__name__)),
                )

    def set_name(self, name):
        """
        Sets the name field, trimming to max length if necessary.
        """
        return self._set_trimmed_field('name', name)

    def property(self, name, value=None, deduplicate=True):
        """
        Getter/setter for related Properties.
        If 'value' is not provided, returns all related Properties
        with the specified key, as a Django QuerySet.
        If 'value' is provided, attempts to set a property as follows:
            - If a single Property with that key is found:
                - If deduplicate is True, updates its value.
                - Else, creates a new one.
            - If no Property with that key is found,
                creates one with the specified value.
            - If more than one Property with that key is found:
                - If 'deduplicate' is True, throws a
                    Property.MultipleObjectsReturned error
                - Else, just makes a new one with the specified key.
        Note: Deduplciate is often disabled for tag.
        If a request to write a Property occurs before this object
        is saved, Django cannot make the connection; this method will
        fail silently.
        """
        properties = self.properties.filter(name=name)

        # Read
        if value is None:
            return properties

        # Write
        else:
            # If this model has not yet been saved, we cannot make
            # the relationship connection.  Fail silently, similar to
            # how native Django would if the objects were built and
            # connected individually.
            if not self.pk:
                return None

            if deduplicate:
                if not properties.exists():
                    p = Property.objects.create(name=name, value=value, property_for=self)
                    return p
                elif properties.count() > 1:
                    raise Property.MultipleObjectsReturned(
                        f'More than one Property with key "{name}" found.',
                    )
                else:
                    p = properties.get()
                    p.value = value
                    p.save()
                    return p
            else:
                p = Property.objects.create(name=name, value=value, property_for=self)
                return p


class Property(models.Model, ModelUtils):
    """
    Represents additional custom defined values for a GRENML element
    """
    TRIMMED_FIELDS = ['value']

    # The descriptive name of the property
    # Like a key in key-val pairs
    name = models.CharField(
        max_length=32,
        verbose_name=_('Name'),
        help_text=_('Will be converted to all lower case when saved'),
    )
    # The value given to the property
    value = models.CharField(
        max_length=512,
        verbose_name=_('Value'),
    )
    # The element this property is for
    property_for = models.ForeignKey(
        BaseModel,
        null=False,
        on_delete=models.CASCADE,
        related_name='properties',
        verbose_name=_('property for'),
    )

    def __init__(self, *args, **kwargs):
        kwargs = self._init_trimmed_fields(**kwargs)
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super(Property, self).save(*args, **kwargs)

    def set_value(self, value):
        """
        Sets the value field, trimming to max length if necessary.
        """
        return self._set_trimmed_field('value', value)

    def __str__(self):
        return f'{self.name}={self.value}'

    class Meta:
        verbose_name = _('Property')
        verbose_name_plural = _('Properties')
