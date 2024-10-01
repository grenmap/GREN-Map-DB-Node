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

This file contains the definition for a GRENML topology model
"""

import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .base_model import BaseModel
from .grenml import CascadeDeleteManager, delete_objects
from .institution import Institution
from .node import Node
from .link import Link
from ..exceptions import MoreThanOneMainTopologyError


log = logging.getLogger(__file__)


class TopologyManager(CascadeDeleteManager):
    """
    Adds the get_main_topology method, specific to Topology.
    """

    def get_main_topology(self):
        """
        Fetches the Topology marked as 'main' (or None).
        There should be at most one, enforced by Topology.save().
        However, if somehow that is not the case, raises
            MoreThanOneMainTopologyError.
        """
        main_topologies = Topology.objects.filter(main=True)
        num_main_topologies = main_topologies.count()
        if num_main_topologies == 1:
            return main_topologies.first()
        elif num_main_topologies > 1:
            raise MoreThanOneMainTopologyError()
        else:
            return None


class Topology(BaseModel):
    """
    Represents a GRENML topology
    """
    TRIMMED_FIELDS = ['name']

    objects = TopologyManager()

    # The parent topology for this one
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('parent'),
    )

    # The owners of the element
    # NOTE: For now we allow topologies to be unowned
    owner = models.ForeignKey(
        Institution, on_delete=models.SET_NULL,
        related_name='owned_topologies',
        null=True, blank=True,
        verbose_name=_('owner'),
    )

    main = models.BooleanField(
        default=False,
        help_text=_(
            'The root Topology to use for GRENML exports and distributed DB polling.  '
            'Only one Topology may be set as main.'
        ),
        verbose_name=_('main'),
    )

    def __init__(self, *args, **kwargs):
        kwargs = self._init_trimmed_fields(**kwargs)
        super().__init__(*args, **kwargs)

    def get_subtopologies(self):
        """
        A recursive function for retrieving a
        list of topologiesunder this one.
        NOTE: It is important that topologies
        are not allowed to have a circular relation, otherwise
        this function will cause a stack overflow.
        Ex:
        +-- Topology1
        |	+-- Topology2
        |	|   +-- Topology1

        Will cause this method to raise a RecursionError
        """
        objs = Topology.objects.none()
        if self.pk is None:
            return objs

        children = self.children.all()
        # If this topology has no children, then this is the base case
        if children is None:
            return objs
        # Add all children of the children using recursion
        for child in children:
            objs = objs | child.get_subtopologies()
        return children | objs

    def get_delete_objects(self):
        """
        Gets all objects that would be deleted if this one was.
        """
        topologies_to_delete = Topology.objects.filter(id=self.id) | self.get_subtopologies()
        # Invert the list of topologies to delete to have a list of
        # topologies not being deleted. This allows us to exclude all
        # elements that have a parent that isn't being deleted
        exclude_topologies = Topology.objects.exclude(id__in=topologies_to_delete)

        nodes_to_delete = Node.objects.exclude(topologies__in=exclude_topologies).distinct()
        links_to_delete = Link.objects.exclude(topologies__in=exclude_topologies).distinct()

        # This will delete institutions that are not associated
        # to a topology.
        institutions_to_delete = Institution.objects.exclude(
            topologies__in=exclude_topologies
        ).distinct()

        # The links connected to nodes that will be deleted also need
        # to be accounted for
        additional_links_to_delete = Link.objects.filter(
            models.Q(node_a__in=nodes_to_delete) | models.Q(node_b__in=nodes_to_delete)
        ).distinct()

        # Combination of additional links deleted when
        # the nodes are deleted and the ones under the current topology
        links_distinct = (links_to_delete | additional_links_to_delete).distinct()

        return {
            'topologies': topologies_to_delete,
            'nodes': nodes_to_delete,
            'links': links_distinct,
            'institutions': institutions_to_delete
        }

    def validate_non_circular_tree(self):
        """
        Validates that the topology is not being set
        to have a parent that is also a child, or itself
        """
        try:
            # First, check if this is the root topology.
            # If it is, we are done here
            if self.parent is not None:
                # If we are trying to point this topology to itself,
                # or if we are trying to point it to a topology that
                # points to it, then that creates a circular reference
                if self.parent == self or self.parent in self.get_subtopologies():
                    raise ValidationError(
                        _('Cannot create circular Topology reference'),
                        code=_('Invalid Topology Configuration'),
                    )
        except RecursionError:
            raise ValidationError(
                _('Topology tree contains circular Topology reference that caused a fatal error'),
                code=_('Invalid Topology Configuration'),
            )

    def clean(self):
        """
        This attempts to ensure that the Topology tree is hierarchical.
        """
        self.validate_non_circular_tree()
        super().clean()

    def validate_unique(self, exclude=None):
        """
        Re-introduces the requirement for ID uniqueness
        not present in other BaseModels.
        """
        if not self.grenml_id \
                or Topology.objects.exclude(pk=self.pk).filter(grenml_id=self.grenml_id).count():
            raise ValidationError(
                _('Topology GRENML ID must be supplied and unique.')
            )
        super().validate_unique()

    def save(self, *args, **kwargs):
        """
        Confirms the model is clean (per clean method) before saving.
        Also, if this is the only Topology in the database, set it to
        be the "main" Topology, as a convenience.
        """
        try:
            self.full_clean()
        except ValidationError:
            # catch the exception to allow us to exit silently
            return

        # Set only/first Topology to be "main"
        other_topologies = Topology.objects.all()
        if self.pk is not None:
            other_topologies = other_topologies.exclude(pk=self.pk)
        if other_topologies.count() == 0:
            self.main = True

        if self.main:
            other_topologies.update(main=False)
        super().save(*args, **kwargs)

    def delete(self):
        """
        Override deletion of this model to propagate
        deletion to sub models
        """
        delete_lists = self.get_delete_objects()
        # Remove self to prevent infinitely recursive delete
        delete_lists['topologies'] = delete_lists['topologies'].exclude(id=self.id)

        delete_objects(delete_lists)

        super(Topology, self).delete()

    def log_str_summary(self):
        """
        (Supports logging and debugging.)
        Returns a dictionary containing log_str strings for
        all Nodes and Links in the Topology,
        as well as the parent and child Topologies.
        """
        return {
            'self': self.log_str,
            'parent': self.parent.log_str if self.parent else None,
            'children': [child.log_str for child in self.children.all()],
            'nodes': [node.log_str for node in self.nodes.all()],
            'links': [link.log_str for link in self.links.all()],
        }

    def __str__(self):
        output = ''
        if self.parent is not None:
            output = str(self.parent) + ' ==> '
        output += super().__str__()
        return output

    class Meta:
        verbose_name = _('Network Topology')
        verbose_name_plural = _('Network Topologies')
