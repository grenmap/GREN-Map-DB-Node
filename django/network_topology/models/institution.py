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

    popup_summary = models.TextField(
        null=False, blank=True, default='',
        verbose_name=_('Popup Summary'),
        help_text=_(
            'Short text shown in the map popup for this institution\'s nodes. '
            'Also used as the source text for automatic translation.'
        ),
    )
    popup_content = models.TextField(
        null=False, blank=True, default='',
        verbose_name=_('Popup Content'),
        help_text=_(
            'Full HTML content shown in the expanded map popup for this '
            'institution\'s nodes. Also used as the source text for '
            'automatic translation.'
        ),
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

        self.carry_popup_over(replacement_institution)

        # Now delete this Institution; it has been replaced
        self.delete()

    # Reverse accessors of the cached popup translation tables
    # (visualization and chameleon_api apps). Looked up by name so this
    # model doesn't import those apps, which import it.
    POPUP_FIELDS = ('popup_summary', 'popup_content')
    POPUP_TRANSLATION_ACCESSORS = ('visualization_popup_translations', 'popup_translations')

    def carry_popup_over(self, replacement_institution):
        """
        Popup texts are entered by hand in the admin and are not part
        of GRENML, so a re-import creates the replacement Institution
        without them. Copy them over when the replacement has none,
        and move the cached translations along when the texts match,
        so deleting this Institution doesn't lose either.
        """
        copied = []
        for field in self.POPUP_FIELDS:
            if getattr(self, field) and not getattr(replacement_institution, field):
                setattr(replacement_institution, field, getattr(self, field))
                copied.append(field)
        if copied:
            replacement_institution.save(update_fields=copied)

        same_texts = all(
            getattr(self, field) == getattr(replacement_institution, field)
            for field in self.POPUP_FIELDS
        )
        if not same_texts:
            # The replacement has its own popup; these translations
            # don't belong to it.
            return
        for accessor in self.POPUP_TRANSLATION_ACCESSORS:
            translations = getattr(self, accessor, None)
            if translations is None:
                continue
            existing_languages = list(
                getattr(replacement_institution, accessor).values_list('language_code', flat=True)
            )
            translations.exclude(language_code__in=existing_languages).update(
                institution=replacement_institution,
            )

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
