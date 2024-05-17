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

Synopsis: Definitions for a Link model, similar to GRENML Link.
"""

import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .grenml import Lifetime
from .network_element import NetworkElement
from .node import Node


log = logging.getLogger(__file__)


class LinkManager(models.Manager):

    def create(self, grenml_id, name, node_a, node_b, *args, **kwargs):
        """
        Override the create function to allow for upon Link validation
        """
        link = super().create(
            grenml_id=grenml_id, name=name,
            node_a=node_a, node_b=node_b,
            *args, **kwargs
        )
        link.validate_nodes()
        return link


class Link(NetworkElement, Lifetime):
    """
    Represents a link between 2 nodes on the map
    """
    TRIMMED_FIELDS = ['name', 'short_name']

    topologies = models.ManyToManyField(
        'Topology',
        related_name='links',
        verbose_name=_('topologies'),
    )

    # The first node in the link
    node_a = models.ForeignKey(
        Node, null=False, on_delete=models.CASCADE,
        related_name='links_a',
        verbose_name=_('Link Node A'),
    )
    # The second node in the link
    node_b = models.ForeignKey(
        Node, null=False, on_delete=models.CASCADE,
        related_name='links_b',
        verbose_name=_('Link Node B'),
    )

    objects = LinkManager()

    def __str__(self):
        return '{}({} - {}) <{}>'.format(
            self.name, self.node_a.name, self.node_b.name, self.id
        )

    def clean(self):
        # This prevents assigning the the same node on both ends
        # in the admin interface
        self.validate_nodes()
        super().clean()

    def save(self, *args, allow_exceptions=False, **kwargs):
        # Prevent a link from being saved if its 2 nodes are
        # the same. We do not allow self linking a node.
        try:
            self.validate_nodes()
        except ValidationError:
            if allow_exceptions:
                raise
            else:
                # The Link will not be saved.
                # If it previously existed, it will be deleted.
                return

        super().save(*args, **kwargs)

    def validate_nodes(self):
        if not hasattr(self, 'node_a') or not hasattr(self, 'node_b'):
            raise ValidationError(
                _('The nodes of a link cannot be null'),
                code=_("Invalid node configuration"),
            )
        elif self.node_a == self.node_b:
            raise ValidationError(
                _('The nodes of a link cannot be the same'),
                code=_("Invalid node configuration"),
            )

    def replace_with(self, replacement_link, union_topologies=True, union_owners=False):
        """
        Deletes this Link in favour of another.
        Consolidates Topology belonging relationships (unless
        overridden with the union_topologies flag), and the ownership
        relationships (if requested with the union_owners flag).
        """
        # Include the replacement Link in the same
        # Topologies as this one (the one we're replacing)
        if union_topologies:
            for topology in self.topologies.all():
                # Django's ManyToManyField auto-deduplicates
                replacement_link.topologies.add(topology)

        if union_owners:
            for owner in self.owners.all():
                # Django's ManyToManyField auto-deduplicates
                replacement_link.owners.add(owner)

        # Now delete this Node; it has been replaced
        self.delete()

    def replace_with_newest(self, **kwargs):
        """
        Looks for a newer version of this element (by GRENML ID),
        chooses the newest, and calls .replace_with to delete this
        element in favour of the newer version.  Commonly used by
        the delete propagation routine.
        """
        newer = Link.objects.filter(
            pk__gt=self.pk,
            grenml_id=self.grenml_id,
        ).order_by('-pk')
        if len(newer):
            newest = newer.first()
            self.replace_with(newest, **kwargs)
        else:
            raise Link.DoesNotExist(f'No newer version of {self.log_str} found.')

    class Meta:
        verbose_name = _('Network Link')
        verbose_name_plural = _('Network Links')
