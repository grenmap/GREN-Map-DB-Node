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

Synopsis: Definitions for a Node model, similar to GRENML Node.
"""

import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .network_element import NetworkElement
from .grenml import Lifetime, Location


log = logging.getLogger(__file__)


class NodeQuerySet(models.query.QuerySet):
    """
    This queryset allows for getting links attached to all nodes in the
    queryset.
    """

    def links(self) -> QuerySet:
        from .link import Link
        return (
            Link.objects.filter(node_a__in=self) | Link.objects.filter(node_b__in=self)
        ).distinct()


class NodeManager(models.Manager):
    """
    This manager provides an overriden queryset that can get all
    links attached to a set of nodes
    """

    def get_queryset(self):
        return NodeQuerySet(self.model, using=self._db)


class Node(NetworkElement, Lifetime, Location):
    """
    Represents a point with extendable attributes on the map
    """
    TRIMMED_FIELDS = ['name', 'short_name', 'address', 'unlocode']

    topologies = models.ManyToManyField(
        'Topology',
        related_name='nodes',
        verbose_name=_('topologies'),
    )

    objects = NodeManager()

    @property
    def links(self) -> QuerySet:
        """Gets the links that connect to this node"""
        return (self.links_a.all() | self.links_b.all()).distinct()

    @property
    def connected_nodes(self):
        """Gets the nodes that are connected to this node"""
        links = self.links
        return Node.objects.filter(Q(links_a__in=links) | Q(links_b__in=links)).distinct()

    @property
    def connected_owners(self):
        """Institutions of nodes connected to this node"""
        owners_sum = set(())
        for node in self.connected_nodes.prefetch_related('owners'):
            owners_sum.update(node.owners.all())
        return owners_sum

    def replace_with(self, replacement_node, union_topologies=True, union_owners=False):
        """
        Deletes this Node in favour of another.
        Transfers Link endpoint relationships to the replacement
        Node, along with Topology belonging relationships (unless
        overridden with the union_topologies flag), and the ownership
        relationships (if requested with the union_owners flag).

        Note that if a Link ends up with two endpoint Nodes being
        the same Node, a ValidationError will be raised.
        """
        # Update all Link endpoint relationships from the
        # external Node to the original one
        for link in self.links_a.all():
            link.node_a = replacement_node
            try:
                link.save(allow_exceptions=True)
            except ValidationError:
                log.error(f'Link {link.log_str} has been deleted due to a Node endpoint conflict!')
        for link in self.links_b.all():
            link.node_b = replacement_node
            try:
                link.save(allow_exceptions=True)
            except ValidationError:
                log.error(f'Link {link.log_str} has been deleted due to a Node endpoint conflict!')

        # Include the replacement Node in the same
        # Topologies as this one (the one we're replacing)
        if union_topologies:
            for topology in self.topologies.all():
                # Django's ManyToManyField auto-deduplicates
                replacement_node.topologies.add(topology)

        if union_owners:
            for owner in self.owners.all():
                # Django's ManyToManyField auto-deduplicates
                replacement_node.owners.add(owner)

        # Now delete this Node; it has been replaced
        self.delete()

    def replace_with_newest(self, **kwargs):
        """
        Looks for a newer version of this element (by GRENML ID),
        chooses the newest, and calls .replace_with to delete this
        element in favour of the newer version.  Commonly used by
        the delete propagation routine.
        """
        newer = Node.objects.filter(
            pk__gt=self.pk,
            grenml_id=self.grenml_id,
        ).order_by('-pk')
        if len(newer):
            newest = newer.first()
            self.replace_with(newest, **kwargs)
        else:
            raise Node.DoesNotExist(f'No newer version of {self.log_str} found.')

    class Meta:
        verbose_name = _('Network Node')
        verbose_name_plural = _('Network Nodes')
