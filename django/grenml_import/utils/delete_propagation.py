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
import logging
from network_topology.models import Institution, Node, Link


logger = logging.getLogger(__name__)


class DeleteStale:
    """
    This is a context manager that integrates the mark-as-dirty
    and delete functions.
    """

    def __init__(self, topology):
        self.topology = topology

    def mark(self, value):
        """
        Updates the dirty flag of all elements in a given Topology.
        Does not descend into subtopologies.
        """
        insts = list(Institution.objects.filter(topologies__in=[self.topology]))
        nodes = list(Node.objects.filter(topologies__in=[self.topology]))
        links = list(Link.objects.filter(topologies__in=[self.topology]))
        elements = insts + nodes + links
        logger.debug(
            'Slating %s elements for deletion: %s Institutions, %s Nodes, %s Links.',
            len(elements),
            len(insts),
            len(nodes),
            len(links),
        )
        for element in elements:
            element.dirty = value
            element.save()
            logger.debug(
                '%s is now slated for deletion.',
                element.log_str,
            )

    def delete_dirty(self):
        """
        This function removes the dirty objects.
        It first breaks their associations to the given Topology.
        An Institution, Link or Node not associated to any Topologies
        is either replaced with a newer version of the same element
        (identified by GRENML ID and sorted by primary key) if
        available, or deleted if no newer version found.
        """
        for link in Link.objects.filter(topologies__in=[self.topology], dirty=True):
            logger.debug('Deleting stale Link %s.', link.log_str)
            link.topologies.remove(self.topology)
            if not link.topologies.count():
                try:
                    link.replace_with_newest(union_topologies=False, union_owners=False)
                except Link.DoesNotExist:
                    link.delete()
        for node in Node.objects.filter(topologies__in=[self.topology], dirty=True):
            logger.debug('Deleting stale Node %s.', node.log_str)
            if node.links.exists():
                logger.error('Node %s still serves as a Link endpoint!', node.log_str)
                for link in node.links:
                    logger.debug('Node %s is an endpoint for Link %s', node.log_str, link.log_str)
            node.topologies.remove(self.topology)
            if not node.topologies.count():
                try:
                    node.replace_with_newest(union_topologies=False, union_owners=False)
                except Node.DoesNotExist:
                    node.delete()
        for inst in Institution.objects.filter(topologies__in=[self.topology], dirty=True):
            logger.debug('Deleting stale Institution %s.', inst.log_str)
            if inst.elements.exists() or inst.owned_topologies.exists():
                logger.error('Institution %s still serves as an owner!', inst.log_str)
                for element in (list(inst.elements.all()) + list(inst.owned_topologies.all())):
                    logger.debug('Institution %s owns %s.', inst.log_str, element.log_str)
            inst.topologies.remove(self.topology)
            if not inst.topologies.count():
                try:
                    inst.replace_with_newest(union_topologies=False)
                except Institution.DoesNotExist:
                    inst.delete()

    def __enter__(self):
        """
        Context manager entry method
        (executes at the top of the with block).
        """
        self.mark(True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method
        (executes at the end of the with block).
        """
        if exc_val:
            # do not delete if an exception happens, only unset the flag
            self.mark(False)
        else:
            self.delete_dirty()

        # let exceptions out of the with block
        return False
