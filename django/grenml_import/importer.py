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

------------------------------------------------------------------------

Synopsis: Functionality to import a Topology into the DB node
    from to a GRENML/XML string or a grenml.GRENMLManager.
"""

import logging

from django.utils.translation import gettext as _
from django.db import transaction

from grenml import parse
from grenml.models import Topology as GRENMLTopology

from network_topology.models import Topology, Institution, Node, Link
from collation.models import Ruleset
from visualization.cache import (
    post_save_connect,
    post_save_disconnect,
    save_initial_map_data_for_entity,
)
from grenml_export.constants import (
    EXTERNAL_TOPOLOGY_PROPERTY_KEY,
    EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER,
)

from .utils.import_exceptions import ImportWarning, ImportError, StreamParseError
from .utils.import_log import ImportLog
from .utils.delete_propagation import DeleteStale


logger = logging.getLogger(__name__)


class GRENMLImporter:

    def __init__(self, test_mode=False):
        """
        Supply test_mode=True to import verbatim, skipping deduplication
        of elements marked as external.  This may be used to examine
        a GRENML file by importing it and performing DB assertions
        rather than XML parsing and querying, for example.
        """
        self.import_log = ImportLog()
        self._test_mode = test_mode

    def _save_topology(self, grenml_topology: GRENMLTopology, parent: Topology):
        """
        Saves a GRENML Topology element to Topology database model.
        If an existing Topology has the same name and parent, it will
        be updated.  If an existing Topology otherwise has the same ID,
        it will be updated.  If neither of the above, a new one will be
        created.
        """
        messages = []
        warnings = []
        # Left at False if updating an existing record
        # Set to True if a new Topology object is created
        created = False
        try:
            try:
                topology = Topology.objects.get(name=grenml_topology.name, parent=parent)
                topo_updated_message = f'Topology {topology.log_str} exists so it will be updated.'
                topo_updated_message += ' Topology matched by name and parent.'
                messages.append(topo_updated_message)
                logger.info(topo_updated_message)
            except Topology.DoesNotExist:
                topology = Topology.objects.get(grenml_id=grenml_topology.id)
                topo_updated_message = f'Topology {topology.log_str} exists so it will be updated.'
                topo_updated_message += ' Topology matched by ID.'
                messages.append(topo_updated_message)
                logger.info(topo_updated_message)
        except Topology.DoesNotExist:
            created = True
            topology = Topology()
        topology.grenml_id = grenml_topology.id
        messages.append(topology.set_name(grenml_topology.name)[1])
        topology.version = grenml_topology.version
        topology.save()

        # Set the parent as directed, unless the new Topology is set to
        # replace the parent, to avoid a circular FK reference.
        # This has to be done after an initial save or the DB complains
        if parent == topology:
            topology.parent = None
            warnings.append(ImportWarning(_('Circular parent reference detected and avoided.')))
        else:
            topology.parent = parent
        topology.save()

        # We defer this log message until after the basics are set above
        # so that the log message contains the name and ID and PK.
        if created:
            logger.debug(f'Topology {topology.log_str} has been created.')
        messages.append(f'Parent set to {parent.log_str if parent else "None"}.')

        # In case this is an existing Topology, let's make sure to
        # refresh the Properties from scratch, so no stale info
        # remains after a fresh import.
        topology.properties.all().delete()
        for attr, values in grenml_topology.additional_properties.items():
            for value in values:
                logger.debug(f'Adding Property {attr}/{value} to {topology.id}.')
                topology.property(attr, value=value, deduplicate=False)

        # Filter out Nones from the activity report messages,
        # then add a log entry for this Topology.
        messages = [msg for msg in messages if msg]
        self.import_log.topologies.log_imported(
            topology.grenml_id,
            topology.pk,
            messages,
            warnings,
        )
        logger.debug(f'Topology {topology.log_str} imported. ' + ' '.join(messages))

        return topology

    def _save_institutions(self, grenml_topology: GRENMLTopology, topology: Topology):
        """
        Iterates through all Institutions in the parsed GRENML Topology
        directly (does not descend recursively), and stores them to
        Institution database models, including fields and Properties.
        Returns a dictionary of all Institutions added, to guarantee
        the imported Topology is self-contained -- in case of ID
        collision, it is nearly impossible to tell which item is the
        applicable one from a database query, so we store the object
        references during the import and link to those directly.
        """
        if not grenml_topology.institutions:
            logger.debug(f'No Institutions found in Topology {grenml_topology.id}.')
            return
        institutions = {}

        for grenml_institution in grenml_topology.institutions:
            logger.debug(f'Importing Institution {grenml_institution.id}.')
            messages = []
            institution = Institution()
            institution.grenml_id = grenml_institution.id
            messages += institution.set_names(
                grenml_institution.name,
                grenml_institution.short_name,
            )
            institution.version = grenml_institution.version
            institution.coordinates = (
                grenml_institution.latitude,
                grenml_institution.longitude,
                grenml_institution.altitude,
            )
            messages.append(institution.set_address(grenml_institution.address)[1])
            messages.append(institution.set_unlocode(grenml_institution.unlocode)[1])
            institution.save()

            for attr, values in grenml_institution.additional_properties.items():
                for value in values:
                    logger.debug(f'Adding Property {attr}/{value} to {grenml_institution.id}.')
                    institution.property(attr, value=value, deduplicate=False)

            institution.topologies.add(topology)

            # Filter out Nones from the activity report messages,
            # then add a log entry for this Institution.
            messages = [msg for msg in messages if msg]
            self.import_log.institutions.log_imported(
                institution.grenml_id,
                institution.pk,
                messages,
            )
            logger.debug(f'Institution {institution.log_str} imported. ' + ' '.join(messages))

            institutions[grenml_institution.id] = institution
        return institutions

    def _save_nodes(self, grenml_topology: GRENMLTopology, topology: Topology, institutions):
        """
        Iterates through all Nodes in the parsed GRENML Topology
        directly (does not descend recursively), and stores them to
        Node database models, including fields and Properties.
        Accepts a dict of previously-saved institutions (by ID),
        and uses those references instead of querying them from the DB.
        Returns a dictionary of all Nodes added, to reduce DB lookups
        when creating Links.guarantee
        the imported Topology is self-contained -- in case of ID
        collision, it is nearly impossible to tell which item is the
        applicable one from a database query, so we store the object
        references during the import and link to those directly.
        """
        if not grenml_topology.nodes:
            logger.debug(f'No Nodes found in Topology {grenml_topology.id}.')
            return
        nodes = {}

        for grenml_node in grenml_topology.nodes:
            logger.debug(f'Importing Node {grenml_node.id}.')
            messages = []
            node = Node()
            node.grenml_id = grenml_node.id
            messages += node.set_names(
                grenml_node.name,
                grenml_node.short_name,
            )
            node.version = grenml_node.version
            node.coordinates = (
                grenml_node.latitude,
                grenml_node.longitude,
                grenml_node.altitude,
            )
            node.start = grenml_node.lifetime_start
            node.end = grenml_node.lifetime_end
            messages.append(node.set_address(grenml_node.address)[1])
            messages.append(node.set_unlocode(grenml_node.unlocode)[1])
            node.save()

            for attr, values in grenml_node.additional_properties.items():
                for value in values:
                    logger.debug(f'Adding Property {attr}/{value} to {grenml_node.id}.')
                    node.property(attr, value=value, deduplicate=False)

            for owner in grenml_node.owners:
                logger.debug(f'Adding owner Institution <{owner.id}>.')
                node.owners.add(institutions[owner.id])

            node.topologies.add(topology)

            # Filter out Nones from the activity report messages,
            # then add a log entry for this Node.
            messages = [msg for msg in messages if msg]
            self.import_log.nodes.log_imported(
                node.grenml_id,
                node.pk,
                messages,
            )
            logger.debug(f'Node {node.log_str} imported. ' + ' '.join(messages))

            nodes[grenml_node.id] = node
        return nodes

    def _save_links(self, grenml_topology: GRENMLTopology, topology: Topology, insts, nodes):
        """
        Iterates through all Links in the parsed GRENML Topology
        directly (does not descend recursively), and stores them to
        Link database models, including fields and Properties.
        Accepts dicts of previously-saved institutions and nodes
        (by ID) and uses those references instead of querying them all
        from the DB when needed.
        Returns a dictionary of all Links added, for consistency with
        other similar functions in this class.
        """
        if not grenml_topology.links:
            logger.debug(f'No Links found in Topology {grenml_topology.id}.')
            return
        links = {}

        for grenml_link in grenml_topology.links:
            logger.debug(f'Importing Link {grenml_link.id}.')
            messages = []
            link = Link()
            link.grenml_id = grenml_link.id
            messages += link.set_names(
                grenml_link.name,
                grenml_link.short_name,
            )
            link.version = grenml_link.version

            # We rely on GRENML validation to ensure there are exactly
            # two endpoint Nodes per Link, but let's check anyway.
            endpoints = [node for node in grenml_link.nodes]
            if len(endpoints) != 2:
                self.import_log.links.log_skipped(grenml_link.id, [ImportWarning(
                    f'Link {grenml_link.id} did not have exactly two endpoints, so was skipped.',
                )])
                continue
            logger.debug(f'Setting endpoints to <{endpoints[0].id}> and <{endpoints[1].id}>.')
            if endpoints[0].id > endpoints[1].id:
                link.node_a = nodes[endpoints[1].id]
                link.node_b = nodes[endpoints[0].id]
            else:
                link.node_a = nodes[endpoints[0].id]
                link.node_b = nodes[endpoints[1].id]
            link.start = grenml_link.lifetime_start
            link.end = grenml_link.lifetime_end
            link.save()

            for attr, values in grenml_link.additional_properties.items():
                for value in values:
                    logger.debug(f'Adding Property {attr}/{value} to {grenml_link.id}.')
                    link.property(attr, value=value, deduplicate=False)

            for owner in grenml_link.owners:
                logger.debug(f'Adding owner Institution <{owner.id}>.')
                link.owners.add(insts[owner.id])

            link.topologies.add(topology)

            # Filter out Nones from the activity report messages,
            # then add a log entry for this Link.
            messages = [msg for msg in messages if msg]
            self.import_log.links.log_imported(
                link.grenml_id,
                link.pk,
                messages,
            )
            logger.debug(f'Link {link.log_str} imported. ' + ' '.join(messages))

            links[grenml_link.id] = link
        return links

    def _set_topology_owner(self, grenml_topology: GRENMLTopology, topology: Topology, insts):
        """
        Ownership of a Topology can only happen after both Topology has
        been saved, and Institutions have been saved therein.  To avoid
        a chicken-and-egg scenario, the Topology is saved, Institutions
        are imported, and then the owner is set after both of those.
        So, this must be called after both _save_topology and
        _save_institutions.
        """
        if grenml_topology.primary_owner is None:
            warning = ImportWarning(
                f'No primary owner set on Topology {grenml_topology.grenml_id}.',
            )
            self.import_log.topologies.update_log(
                grenml_topology.grenml_id,
                pk=topology.pk,
                warnings=[warning],
            )
        else:
            owner_id = grenml_topology.primary_owner
            logger.debug(f'Adding owner Institution <{owner_id}> to Topology {topology.log_str}.')
            primary_owner = insts[owner_id]
            topology.owner = primary_owner
            topology.save()
            logger.debug(f'Topology {topology.log_str} owner set to {primary_owner.log_str}.')

    def _insert_topology(self, grenml_topology: GRENMLTopology, parent: Topology):
        """
        Performs a postorder depth-first recursive traversal of the
        Topology tree, inserting the Topologies and their contents
        along the way back, using helper methods above.
        Engages the delete propagation system via the DeleteStale
        context manager.
        """
        if parent:
            logger.debug(f'Inserting Topology {grenml_topology.name} into parent {parent.name}.')
        else:
            logger.debug(f'Inserting Topology {grenml_topology.name} into root level.')
        topology = self._save_topology(grenml_topology, parent)

        # Postorder depth-first recursive traversal of the tree
        # (Do children first, then our own contents.)
        for subtopology in grenml_topology.topologies:
            self._insert_topology(subtopology, topology)

        with DeleteStale(topology):
            institutions = self._save_institutions(grenml_topology, topology)
            self._set_topology_owner(grenml_topology, topology, institutions)
            nodes = self._save_nodes(grenml_topology, topology, institutions)
            self._save_links(grenml_topology, topology, institutions, nodes)

    def _identify_cross_topology_elements(self, model_class):
        """
        Scans the entire database looking for elements of a given type
        'model_class' (Institution, Node, or Link), identified as
        being originally from another Topology but included in an
        exported GRENML Topology for its internal self-consistency.
        Returns a list of tuples, each representing one such element,
        and the original element in the proper Topology/-ies.
        The original element may be None if not found, which
        could just mean it hasn't been imported yet and will
        be caught in a future round of imports.
        """
        cross_topology_elements = []

        external_elements = model_class.objects.filter(
            properties__name=EXTERNAL_TOPOLOGY_PROPERTY_KEY,
        )
        for element in external_elements:
            external_property = element.property(EXTERNAL_TOPOLOGY_PROPERTY_KEY).first()
            # Find the original elements in the indicated Topology/-ies
            original_topology_grenml_ids = external_property.value.split(
                EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER
            )
            original_topologies = Topology.objects.filter(
                grenml_id__in=original_topology_grenml_ids,
            )
            originals = model_class.objects.filter(
                grenml_id=element.grenml_id,
                topologies__in=original_topologies,
            )
            originals = originals.exclude(pk=element.pk)
            cross_topology_elements.append(
                (element, list(originals))
            )

        return cross_topology_elements

    def _resolve_cross_topology_elements_by_type(self, type):
        """
        Searches for all elements of a specified type (e.g.
        Institution, Node) identifed as being originally
        from another Topology but included in an exported GRENML
        Topology for its internal self-consistency, using
        self._identify_cross_topology_elements.
        If the original element in the proper Topology is found in
        the database, that helper method will return a reference to
        it, and this method replaces the duplicate 'external' version
        with the original one, updating all relationships accordingly.
        """
        cross_topology_elements = self._identify_cross_topology_elements(type)
        for item in cross_topology_elements:
            element = item[0]
            originals = item[1]
            if originals:
                if len(originals) > 1:
                    logger.error(
                        f'Replacing {type.__name__} {element.log_str}; '
                        f'found {len(originals)}: '
                        f'[{",".join([original.log_str for original in originals])}]'
                    )
                else:
                    original = originals[0]
                    logger.debug(
                        f'Removing external {type.__name__} {element.log_str} '
                        f'in favour of original {original.log_str}.'
                    )
                    element.replace_with(original, union_topologies=False)
            else:
                logger.debug(
                    f'Not removing external {type.__name__} {element.log_str} '
                    'as no originals found in the listed Topologies.'
                )

    def _resolve_cross_topology_elements(self):
        """
        Handy dispatcher to resolve the types of elements
        subject to 'external' or cross-topology references:
        Institutions (owners) and Nodes (endpoints).
        """
        self._resolve_cross_topology_elements_by_type(Institution)
        self._resolve_cross_topology_elements_by_type(Node)

    def from_stream(self, file_stream, parent_topology: Topology = None):
        """
        Takes a stream, attempts to parse it using the GRENML Library,
        and imports it into the database using from_grenml_manager.
        """
        logger.debug('Importing GRENML from a stream.')
        try:
            p = parse.GRENMLParser()
            manager = p.parse_byte_stream(file_stream)
        except Exception as e:
            raise StreamParseError('Error parsing the XML stream: ' + str(e))

        return self.from_grenml_manager(
            manager,
            parent_topology,
        )

    def from_grenml_manager(self, manager, parent_topology: Topology = None):
        """
        Stores the GRENML Manager objects in the database.
        Imports per Topology, postorder depth-first.
        (Depth-first to encourage deduplication to choose the element
        provided higher up in the hierarchy when there are ID
        collisions, since a fallback resolution choosees the latest.)
        Top-level Topology is imported either as a child of a selected
        Topology (parent_topology parameter), or into root level.
        Within each Topology, elements are added in order:
            1. Institutions
            2. Nodes
            3. Links
        Returns an ImportLog instance representing its activity.
        """

        logger.debug('Importing from GRENMLManager.')
        try:
            post_save_disconnect()

            import_errors = manager.validate(raise_error=False)
            if import_errors:
                raise ImportError('; '.join(import_errors))

            with transaction.atomic():
                logger.debug(f'Starting import: {manager.topology.name} <{manager.topology.id}>.')
                self._insert_topology(manager.topology, parent_topology)
                if not self._test_mode:
                    self._resolve_cross_topology_elements()
                logger.debug(f'Import of <{manager.topology.id}> complete.')
                logger.debug('Running post-import Rules.')
                Ruleset.objects.apply_all_rulesets()
                logger.debug(f'Post-import Rules complete after <{manager.topology.id}>.')

            self.import_log.complete()

        except (ImportError, Exception) as e:
            logger.exception('Aborting GRENML import due to ' + str(e))
            self.import_log.abort(e)

        finally:
            post_save_connect()

        # Re-cache GraphQL for the viz
        save_initial_map_data_for_entity('institutions')
        save_initial_map_data_for_entity('nodes')
        save_initial_map_data_for_entity('links')

        return self.import_log
