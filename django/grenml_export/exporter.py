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

Synopsis: This file contains functionality to export a Topology in the
    DB node to an XML string.
"""

import io
import logging
from typing import Optional
from time import time

from grenml import GRENMLManager
from grenml.models import Topology as GRENMLTopology
from grenml.models import Institution as GRENMLInstitution
from grenml.models import Node as GRENMLNode
from grenml.models import Link as GRENMLLink
from grenml.models.topologies import GLOBAL_INSTITUTION_ID

from network_topology.exceptions import (
    MissingRootTopologyException,
)
from network_topology.models import Topology, Institution, Node, Link, Property
from network_topology.exceptions import MoreThanOneMainTopologyError
from .exceptions import NoTopologyOwnerError
from .constants import (
    EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER,
)


# Produces a DEBUG-level log for each exported element
EXTRA_DEV_LOGGING = True

# Maps Django ORM model fields to their GRENML entity counterparts
INSTITUTION_EXPORT_FIELD_MAP = {
    'grenml_id': 'id',
    'name': 'name',
    'short_name': 'short_name',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'altitude': 'altitude',
    'address': 'address',
    'unlocode': 'unlocode',
    'version': 'version',
}
NODE_EXPORT_FIELD_MAP = {
    'grenml_id': 'id',
    'name': 'name',
    'short_name': 'short_name',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'altitude': 'altitude',
    'address': 'address',
    'unlocode': 'unlocode',
    'version': 'version',
    'start': 'lifetime_start',
    'end': 'lifetime_end',
}
LINK_EXPORT_FIELD_MAP = {
    'grenml_id': 'id',
    'name': 'name',
    'short_name': 'short_name',
    'version': 'version',
    'start': 'lifetime_start',
    'end': 'lifetime_end',
}


logger = logging.getLogger(__name__)


class GRENMLExporter:
    """
    Exports a database Topology tree to either GRENML or a GRENML
    Manager object, starting at a root supplied during instantiation.
    Defers export of each Topology to a GRENMLTopologyExporter.
    """
    def __init__(self, root_topology: Optional[Topology] = None):
        """
        Supply the 'root_topology' argument to specify where to start
        traversing the Topology tree.  If omitted, defaults to the
        'main' Topology.
        """
        if root_topology is None:
            try:
                root_topology = Topology.objects.get_main_topology()
            except MoreThanOneMainTopologyError:
                raise MissingRootTopologyException()
            if root_topology is None:
                raise MissingRootTopologyException()
        self.root_topology = root_topology

    def _topology(self, topology: Topology, grenml_topology: GRENMLTopology):
        """
        Takes a database Topology instance as well as a GRENML Manager
        Topology instance as arguments and exports all data
        from the database instance to the Manager instance.
        """
        # Fill in child topologies that are under the current one
        self._topology_children(topology, grenml_topology)
        # Fill in network elements that belong to this Topology,
        # using a GRENMLTopologyExporter
        GRENMLTopologyExporter(topology, grenml_topology).export()

    def _topology_children(self, topology: Topology, grenml_topology: GRENMLTopology):
        """
        Takes a database Topology instance as well as a GRENML Manager
        Topology instance as arguments and recurses bottom up,
        calling _topology on each one and building the Topology tree.
        """
        for child in topology.children.all():
            child_grenml_topology = GRENMLTopology(
                id=child.grenml_id,
                name=child.name,
                version=child.version,
            )
            self._topology(child, child_grenml_topology)
            grenml_topology.add_topology(child_grenml_topology)

    def to_manager(self):
        """
        Exports the Topology tree, starting at the root given during
        class instantiation, to a GRENML Manager Topology.
        Logs the elapsed time for the Manager population.
        """
        logger.info(f'Exporting {self.root_topology.log_str} tree to a GRENML Manager.')
        start = time()

        manager = GRENMLManager(
            id=self.root_topology.grenml_id,
            name=self.root_topology.name,
            version=self.root_topology.version,
        )
        self._topology(self.root_topology, manager.topology)

        end = time()
        time_taken = end - start
        logger.info(f'Export of {self.root_topology.log_str} took {time_taken} seconds.')

        return manager

    def to_stream(self):
        """
        Exports the Topology tree, starting at the root given during
        class instantiation, to a GRENML StringIO stream.
        """
        logger.info(f'Exporting {self.root_topology.log_str} tree to a StringIO stream of GRENML.')
        manager = self.to_manager()
        output_stream = io.StringIO()
        manager.write_to_output_stream(stream=output_stream)
        return output_stream


class GRENMLTopologyExporter:
    """
    Exports a single database Topology to a GRENML Manager object,
    both of which must be supplied during instantiation.
    """
    def __init__(self, topology: Topology, grenml_topology: GRENMLTopology):
        self.topology = topology
        self.grenml_topology = grenml_topology

        # The queries below are fetched once to support external checks
        self.institutions = self.topology.institutions.all()
        self.nodes = self.topology.nodes.all()

        # Tracks Institutions, Nodes, and Links already exported
        # to avoid duplication.  Primary keys should be unique among
        # all three element types in the schema since they all inherit
        # from network_topology's BaseModel.
        self._exported_primary_keys = []

    def export(self):
        """
        Exports all child network elements of the database
        Topology into the GRENML Manager Topology model, each given
        when the class was instantiated.
        Includes the owner Institution of the Topology even if it does
        not belong directly to the Topology (marked as 'external').
        """
        logger.debug(f'Exporting Topology: {self.topology.log_str}')
        if self.topology.owner:
            owner_inst = self.topology.owner
            self.grenml_topology.primary_owner = owner_inst.grenml_id

            # If the Topology's owner Institution belongs in another
            # Topology, include it, appropriately marked so this
            # relationship can be properly rebuilt when this GRENML is
            # imported.
            if self.topology not in owner_inst.topologies.all():
                self._export_institution(owner_inst, external=True)

        else:
            raise NoTopologyOwnerError(
                f'Topology {self.topology.log_str} must have at least one owner to export.'
            )
        self._export_institutions()
        self._export_nodes()
        self._export_links()

    def _generate_external_topology_property(self, element):
        """
        Adds a Property with a particular key/name and value to
        a given Institution or Node.  (Theoretically could be added
        to a Link, but this wouldn't normally arise.)
            - name: .constants.EXTERNAL_TOPOLOGY_PROPERTY_KEY
            - value: [list of Topology IDs as string]
        Explanation: When exporting some elements, they may be 'owned'
        by Institutions in other Topologies, or have endpoint
        Nodes in other Topologies.  To keep each GRENML Topology
        self-contained and consistent, these elements are included,
        but they must be marked as not belonging to the Topology
        so that they are not blindly added to Topologies where they
        don't belong when the GRENML Topology is re-imported.
        The Property added here is a special one that is recognized
        by the importer to resolve the duplication when possible.
        """
        inst_topology_ids = [topo.grenml_id for topo in element.topologies.all()]
        external_property = Property(
            name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
            value=EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER.join(inst_topology_ids)
        )
        return external_property

    def _generate_grenml_institution(self, institution: Institution, external=False):
        """
        Given a Django ORM Institution, creates a corresponding GRENML
        Institution
        If the 'external' flag argument is provided, adds a Property
        marking it as originating outside the Topology, including
        a list of Topologies' GRENML IDs to which it did originally
        belong as the Property value.
        """
        institution_info = {}

        # Add basic fields
        for model_field, grenml_field in INSTITUTION_EXPORT_FIELD_MAP.items():
            institution_info[grenml_field] = getattr(institution, model_field)

        # Add tags and properties.
        # Extra properties may include a special reserved property that
        # identifies the Topologies to which the Institution belongs,
        # if not the one currently being exported.
        if external:
            extra_properties = [self._generate_external_topology_property(institution)]
        else:
            extra_properties = []
        institution_info = self._add_properties(institution_info, institution, extra_properties)

        if EXTRA_DEV_LOGGING:
            logger.debug(f'Prepared Institution: {institution_info}')

        return GRENMLInstitution(**institution_info)

    def _export_institution(self, institution: Institution, external=False):
        """
        Exports a single given Institution to the GRENML Manager
        Topology.  First checks that the Institution has not yet
        been exported, and skips it if so.
        If the 'external' argument is provided, passes it on to
        the _generate_* helper to append an appropriate Property.
        """
        if external:
            logger.debug('Exporting owner Institution {} from Topology/ies {}'.format(
                institution.log_str,
                ','.join(t.log_str for t in institution.topologies.all()),
            ))
        elif EXTRA_DEV_LOGGING:
            logger.debug(f'Exporting Institution: {institution.log_str}')
        if institution.pk not in self._exported_primary_keys:
            self.grenml_topology.add_institution(
                self._generate_grenml_institution(institution, external=external)
            )
            self._exported_primary_keys.append(institution.pk)
        else:
            logger.debug(f'Skipping Institution already exported: {institution.log_str}')

    def _export_institutions(self):
        """
        Exports institutions that are directly in the database Topology
        into the GRENML Manager Topology.
        Excludes the "global" institution, as that is prepared
        automatically by the Manager anyway.
        """
        institutions = self.topology.institutions.exclude(grenml_id=GLOBAL_INSTITUTION_ID)
        institutions = institutions.prefetch_related('properties')
        logger.debug(f'Exporting {len(institutions)} Institutions in {self.topology.log_str}')

        for institution in institutions:
            self._export_institution(institution)

        logger.debug(f'Exported {len(institutions)} Institutions.')

    def _generate_grenml_node(self, node: Node, external=False):
        """
        Given a Django ORM Node, creates a corresponding GRENML Node.
        If the 'external' flag argument is provided, adds a Property
        marking it as originating outside the Topology, including
        a list of Topologies' GRENML IDs to which it did originally
        belong as the Property value.
        Exports the Node's owner Institutions even if they do not
        belong directly to this Topology, marked as 'external'.
        """
        node_info = {}

        # Add basic fields
        for model_field, grenml_field in NODE_EXPORT_FIELD_MAP.items():
            node_info[grenml_field] = getattr(node, model_field)

        # Add tags and properties.
        # Extra properties may include a special reserved property that
        # identifies the Topologies to which the Institution belongs,
        # if not the one currently being exported.
        if external:
            extra_properties = [self._generate_external_topology_property(node)]
        else:
            extra_properties = []
        node_info = self._add_properties(node_info, node, extra_properties)

        # Add owners
        node_info['owners'] = []
        for owner in node.owners.all():
            # If the owner Institution does not belong to the same
            # Topology as this Node, include the Institution to
            # preserve the relationship, but mark it as external
            # so that the structure may be better rebuilt upon import.
            if owner not in self.institutions:
                self._export_institution(owner, external=True)
            node_info['owners'].append(owner.grenml_id)

        if EXTRA_DEV_LOGGING:
            logger.debug('Prepared Node: %s' % node_info)

        return GRENMLNode(**node_info)

    def _export_node(self, node: Node, external=False):
        """
        Exports a single given Node to the GRENML Manager Topology.
        First checks that the Node has not yet been exported,
        and skips it if so.
        If the 'external' argument is provided, passes it on to
        the _generate_* helper to append an appropriate Property.
        """
        if external:
            logger.debug('Exporting endpoint Node {} from Topology/ies {}'.format(
                node.log_str,
                ','.join(t.log_str for t in node.topologies.all()),
            ))
        elif EXTRA_DEV_LOGGING:
            logger.debug(f'Exporting Node: {node.log_str}')
        if node.pk not in self._exported_primary_keys:
            self.grenml_topology.add_node(
                self._generate_grenml_node(node, external=external)
            )
            self._exported_primary_keys.append(node.pk)
        else:
            logger.debug(f'Skipping Node already exported: {node.log_str}')

    def _export_nodes(self):
        """
        Exports Nodes that are directly in the database Topology
        into the GRENML Manager Topology.
        """
        nodes = self.topology.nodes.all()
        nodes = nodes.prefetch_related('owners').prefetch_related('properties')
        logger.debug(f'Exporting {nodes.count()} Nodes in {self.topology.log_str}')

        for node in nodes:
            self._export_node(node)

        logger.debug(f'Exported {len(nodes)} Nodes.')

    def _generate_grenml_link(self, link: Link):
        """
        Given a Django ORM Link, creates a corresponding GRENML Link.
        Exports the Link's owner Institutions and endpoint Nodes
        even if they do not belong directly to this Topology,
        marked as 'external'.
        """
        link_info = {}

        # Add basic fields
        for model_field, grenml_field in LINK_EXPORT_FIELD_MAP.items():
            link_info[grenml_field] = getattr(link, model_field)

        # Add Node endpoints
        # If they are not Nodes in the current Topology,
        # add them as "external".
        if link.node_a not in self.nodes:
            self._export_node(link.node_a, external=True)
        if link.node_b not in self.nodes:
            self._export_node(link.node_b, external=True)
        link_info['nodes'] = [link.node_a.grenml_id, link.node_b.grenml_id]

        # Add tags and properties
        link_info = self._add_properties(link_info, link)

        # Add owners
        link_info['owners'] = []
        for owner in link.owners.all():
            # If the owner Institution does not belong to the same
            # Topology as this Link, include the Institution to
            # preserve the relationship, but mark it as external
            # so that the structure may be better rebuilt upon import.
            if owner not in self.institutions:
                self._export_institution(owner, external=True)
            link_info['owners'].append(owner.grenml_id)

        if EXTRA_DEV_LOGGING:
            logger.debug('Prepared Link: %s' % link_info)

        return GRENMLLink(**link_info)

    def _export_link(self, link: Link):
        """
        Exports a single given Link to the GRENML Manager Topology.
        First checks that the Link has not yet been exported,
        and skips it if so.
        """
        if EXTRA_DEV_LOGGING:
            logger.debug(f'Exporting Link: {link.log_str}')
        if link.pk not in self._exported_primary_keys:
            self.grenml_topology.add_link(
                self._generate_grenml_link(link)
            )
            self._exported_primary_keys.append(link.pk)
        else:
            logger.debug(f'Skipping Link already exported: {link.log_str}')

    def _export_links(self):
        """
        Exports Links that are directly in the database Topology
        into the GRENML Manager Topology.
        """
        links = self.topology.links.all()
        links = links.select_related('node_a', 'node_b')
        links = links.prefetch_related('owners').prefetch_related('properties')
        logger.debug(f'Exporting {links.count()} Links in {self.topology.log_str}')

        for link in links:
            self._export_link(link)

        logger.debug(f'Exported {len(links)} Links.')

    def _add_properties(self, element_info, element, extras=[]):
        """
        Gets all the properties for a network element
        The property value is a list including all the
        values with the same name in the Property model.
        """
        if not extras:
            extras = []
        for property in list(element.properties.all()) + extras:
            if property.name in element_info.keys():
                element_info[property.name].append(property.value)
            else:
                element_info[property.name] = [property.value]
        return element_info
