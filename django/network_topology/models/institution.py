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

------------------------------------------------------------------------

Synopsis: Definitions for an Institution model, similar to GRENML.
"""

import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base_model import BaseModel
from .grenml import Location, ShortNamed


log = logging.getLogger(__file__)


class Institution(BaseModel, Location, ShortNamed):
    """
    Institution may be: RENs (PREN, NREN, SREN), connected institutions
    (universities, …), or any other organization participating in the
    topology.
    """
    TRIMMED_FIELDS = ['name', 'short_name', 'address', 'unlocode']

    topologies = models.ManyToManyField(
        'Topology',
        related_name='institutions',
        verbose_name=_('topologies'),
    )

    def replace_with(self, replacement_institution, union_topologies=True):
        """
        Deletes this Institution in favour of another.
        Transfers ownership of Nodes, Links, and Topologies to the
        replacement Institution, along with Topology belonging
        relationships (unless overridden with the union_topologies
        flag).
        """
        # Update all ownership relationships from this Institution
        # (the one we're replacing) to its replacement.
        # Topologies (each can only have one owner)
        for topology in self.owned_topologies.all():
            topology.owner = replacement_institution
            topology.save()
        # Nodes and Links
        for element in self.elements.all():
            element.owners.remove(self)
            element.owners.add(replacement_institution)

        # Include the replacement Institution in the same
        # Topologies as this one (the one we're replacing)
        if union_topologies:
            for topology in self.topologies.all():
                # Django's ManyToManyField auto-deduplicates
                replacement_institution.topologies.add(topology)

        # Now delete this Institution; it has been replaced
        self.delete()

    def replace_with_newest(self, **kwargs):
        """
        Looks for a newer version of this element (by GRENML ID),
        chooses the newest, and calls .replace_with to delete this
        element in favour of the newer version.  Commonly used by
        the delete propagation routine.
        """
        newer = Institution.objects.filter(
            pk__gt=self.pk,
            grenml_id=self.grenml_id,
        ).order_by('-pk')
        if len(newer):
            newest = newer.first()
            self.replace_with(newest, **kwargs)
        else:
            raise Institution.DoesNotExist(f'No newer version of {self.log_str} found.')

    class Meta:
        verbose_name = _('Institution')
        verbose_name_plural = _('Institutions')
