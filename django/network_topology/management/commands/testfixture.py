"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2023 GRENMap Authors

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

Synopsis: Management command to insert a Topology of pseudo-random data
    (Institutions, Nodes, and Links, each in the quantity specified).
Usage example:
    python manage.py testfixture 1000
"""

import string
import random

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from network_topology.models import Topology, Institution, Node, Link


# A string length of 4 in base 36 allows over 1,600,000 permutations.
# This applies a practical limit of well under 200,000
# institutions, nodes, links, with an average of 2 properties each.
# Uniqueness assurance will begin to bog long before that.
# Increase this value if generating beyond 50,000 elements.
RANDOM_STRING_LENGTH = 4

# The number of each type of element that will be created
# if an argument is not specified on the command line
DEFAULT_NUM_ELEMENTS = 100

# Includes topology owner; must be greater than 1
MAX_OWNERS = 2

MAX_PROPERTIES = 3


random_strings_used = []


def random_string():
    """
    Generates a random string of length RANDOM_STRING_LENGTH,
    consisting of uppercase ascii characters and numerical digits.
    Recursively tries again if there is a random string collision.
    """
    char_set = string.ascii_uppercase + string.digits
    rs = ''.join(random.choices(char_set, k=RANDOM_STRING_LENGTH))  # nosec B311
    if rs in random_strings_used:
        rs = random_string()
    random_strings_used.append(rs)
    return rs


def add_owners(element, institutions, num_owners):
    for i in range(num_owners):
        element.owners.add(random.choice(institutions))  # nosec B311


def add_properties(element, num_properties):
    for i in range(num_properties):
        element.property(
            name=f'Property {random_string()}',
            value='value',
        )


class Command(BaseCommand):
    help = _('Creates a Topology containing randomized Institutions, Nodes, and Links')

    def add_arguments(self, parser):
        parser.add_argument('num_elements', nargs='?', type=int)

    def handle(self, *args, **options):

        num_elements = options.get('num_elements', DEFAULT_NUM_ELEMENTS)

        topology_id = random_string()
        topology = Topology.objects.create(
            grenml_id=topology_id,
            name=f'Sample Topology {topology_id} Size {num_elements}',
        )
        self.stdout.write(f'Added Topology {topology_id}.')

        institutions = []
        for i in range(num_elements):
            inst_id = random_string()
            inst = Institution.objects.create(
                grenml_id=inst_id,
                name=f'Institution {inst_id}',
                latitude=float(random.randrange(-89, 89)),  # nosec B311
                longitude=float(random.randrange(-179, 179)),  # nosec B311
            )
            inst.topologies.add(topology)
            num_properties = random.randrange(0, MAX_PROPERTIES)  # nosec B311
            add_properties(inst, num_properties)
            self.stdout.write(f'Added Institution {inst_id}, #{i + 1} of {num_elements}')
            institutions.append(inst)

        # Set the Topology owner to be one of the Institutions
        topology.owner = random.choice(institutions)  # nosec B311
        topology.save()

        nodes = []
        for i in range(num_elements):
            node_id = random_string()
            node = Node.objects.create(
                grenml_id=node_id,
                name=f'Node {node_id}',
                latitude=float(random.randrange(-89, 89)),  # nosec B311
                longitude=float(random.randrange(-179, 179)),  # nosec B311
            )
            node.topologies.add(topology)
            node.owners.add(topology.owner)
            num_additional_owners = random.randrange(0, MAX_OWNERS - 1)  # nosec B311
            add_owners(node, institutions, num_additional_owners)
            num_properties = random.randrange(0, MAX_PROPERTIES)  # nosec B311
            add_properties(node, num_properties)
            self.stdout.write(f'Added Node {node_id}, #{i + 1} of {num_elements}.')
            nodes.append(node)

        links = []
        for i in range(num_elements):
            node_a = random.choice(nodes)  # nosec B311
            node_b = node_a
            while node_b == node_a:
                node_b = random.choice(nodes)  # nosec B311
            link_id = random_string()
            link = Link.objects.create(
                grenml_id=link_id,
                name=f'Link {link_id}',
                node_a=node_a,
                node_b=node_b,
            )
            link.topologies.add(topology)
            link.owners.add(topology.owner)
            num_additional_owners = random.randrange(0, MAX_OWNERS - 1)  # nosec B311
            add_owners(link, institutions, num_additional_owners)
            num_properties = random.randrange(0, MAX_PROPERTIES)  # nosec B311
            add_properties(link, num_properties)
            self.stdout.write(f'Added Link {link_id}, #{i + 1} of {num_elements}.')
            links.append(link)
