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

Synopsis: Tests for the replace_with method on Institution, Node, and
Link models.
"""

import pytest

from network_topology.models import Topology, Institution, Node, Link


@pytest.mark.django_db(transaction=True)
class TestReplaceWith:

    @pytest.fixture
    def topologies(self):
        topology1 = Topology.objects.create(
            grenml_id='Topo1',
            name='Topology 1',
        )
        topology2 = Topology.objects.create(
            grenml_id='Topo2',
            name='Topology 2',
        )
        return [topology1, topology2]

    @pytest.fixture
    def institutions(self, topologies):
        institution1 = Institution.objects.create(
            grenml_id='Inst1',
            name='Institution 1',
            latitude=0.0,
            longitude=0.0,
        )
        institution1.topologies.add(topologies[0])
        institution2 = Institution.objects.create(
            grenml_id='Inst2',
            name='Institution 2',
            latitude=0.0,
            longitude=0.0,
        )
        institution2.topologies.add(topologies[1])
        return [institution1, institution2]

    @pytest.fixture
    def nodes(self, topologies, institutions):
        node1 = Node.objects.create(
            grenml_id='Node1',
            name='Node 1',
            latitude=0.0,
            longitude=0.0,
        )
        node1.owners.add(institutions[0])
        node1.topologies.add(topologies[0])
        node2 = Node.objects.create(
            grenml_id='Node2',
            name='Node 2',
            latitude=0.0,
            longitude=0.0,
        )
        node2.owners.add(institutions[1])
        node2.topologies.add(topologies[1])
        # Node3 would make a great replacement for Node1
        node3 = Node.objects.create(
            grenml_id='Node3',
            name='Node 3',
            latitude=0.0,
            longitude=0.0,
        )
        node3.owners.add(institutions[0])
        node3.topologies.add(topologies[0])
        return [node1, node2, node3]

    @pytest.fixture
    def link(self, nodes):
        link = Link.objects.create(
            grenml_id='Link1',
            name='Link 1',
            node_a=nodes[0],
            node_b=nodes[1],
        )
        link.owners.add(nodes[0].owners.first())
        link.topologies.add(nodes[0].topologies.first())
        return link

    def test_institution_replace_with(self, institutions, nodes, link):
        """
        Checks that after an Institution.replace_with call, the
        institution in question is deleted, the replacement remains,
        and all elements originally owned by the deleted institution
        end up owned by the replacement.
        """
        original_institution = institutions[0]
        replacement_institution = institutions[1]

        original_institution.replace_with(replacement_institution)

        assert not Institution.objects.filter(pk=original_institution.pk).exists()
        assert Institution.objects.filter(pk=replacement_institution.pk).exists()
        # Before replace_with, Node1 was owned by original_institution
        node1_owners = nodes[0].owners.all()
        assert node1_owners.count() == 1
        assert node1_owners.get().grenml_id == replacement_institution.grenml_id
        node2_owners = nodes[1].owners.all()
        assert node2_owners.count() == 1
        assert node2_owners.get().grenml_id == replacement_institution.grenml_id
        # Before replace_with, Link1 was owned by original_institution
        link_owners = link.owners.all()
        assert link_owners.count() == 1
        assert link_owners.get().grenml_id == replacement_institution.grenml_id

    def test_institution_replace_with_union_topologies(self, institutions):
        """
        Checks that after an Institution.replace_with call, the
        replacement institution is placed into the topology of the
        deleted element.
        """
        original_institution = institutions[0]
        replacement_institution = institutions[1]
        assert replacement_institution.topologies.count() == 1

        original_institution.replace_with(replacement_institution, union_topologies=True)

        assert replacement_institution.topologies.count() == 2

    def test_node_replace_with(self, nodes, link):
        """
        Checks that after a Node.replace_with call, the
        node in question is deleted, the replacement remains,
        and the link endpoint that used to point to that node
        is updated to point to the replacement.
        """
        original_node = nodes[0]
        replacement_node = nodes[2]

        original_node.replace_with(replacement_node)

        assert not Node.objects.filter(pk=original_node.pk).exists()
        assert Node.objects.filter(pk=replacement_node.pk).exists()
        # Refresh the copy of the Link
        link = Link.objects.get(pk=link.pk)
        assert link.node_a.grenml_id == replacement_node.grenml_id

    def test_node_replace_with_union_topologies(self, topologies, nodes):
        """
        Checks that after a Node.replace_with call, the
        replacement node is placed into the topology of the
        deleted element.
        """
        original_node = nodes[0]
        original_node.topologies.add(topologies[1])
        replacement_node = nodes[2]
        assert replacement_node.topologies.count() == 1

        original_node.replace_with(replacement_node, union_topologies=True)

        assert replacement_node.topologies.count() == 2

    def test_node_replace_with_union_owners(self, institutions, nodes):
        """
        Checks that after a Node.replace_with call, the
        replacement node is additionally owned by the owner of the
        deleted element.
        """
        original_node = nodes[0]
        original_node.owners.add(institutions[1])
        replacement_node = nodes[2]
        assert replacement_node.owners.count() == 1

        original_node.replace_with(replacement_node, union_owners=True)

        assert replacement_node.owners.count() == 2

    def test_link_replace_with(self, nodes, link):
        """
        Checks that after a Link.replace_with call, the
        link in question is deleted, and the replacement remains.
        """
        original_link = link
        replacement_link = Link.objects.create(
            grenml_id='Link2',
            name='Link 2',
            node_a=nodes[0],
            node_b=nodes[1],
        )

        original_link.replace_with(replacement_link)

        assert not Link.objects.filter(pk=original_link.pk).exists()
        assert Link.objects.filter(pk=replacement_link.pk).exists()

    def test_link_replace_with_union_topologies(self, topologies, nodes, link):
        """
        Checks that after a Link.replace_with call, the
        replacement link is placed into the topology of the
        deleted element.
        """
        original_link = link
        original_link.topologies.add(topologies[1])
        replacement_link = Link.objects.create(
            grenml_id='Link2',
            name='Link 2',
            node_a=nodes[0],
            node_b=nodes[1],
        )
        assert replacement_link.topologies.count() == 0

        original_link.replace_with(replacement_link, union_topologies=True)

        assert replacement_link.topologies.count() == 2

    def test_link_replace_with_union_owners(self, institutions, nodes, link):
        """
        Checks that after a Link.replace_with call, the
        replacement link is additionally owned by the owner of the
        deleted element.
        """
        original_link = link
        replacement_link = Link.objects.create(
            grenml_id='Link2',
            name='Link 2',
            node_a=nodes[0],
            node_b=nodes[1],
        )
        replacement_link.owners.add(institutions[1])
        assert replacement_link.owners.count() == 1

        original_link.replace_with(replacement_link, union_owners=True)

        assert replacement_link.owners.count() == 2

    def test_node_replace_with_link_endpoint_conflict(self, nodes, link):
        """
        Checks that during a Node.replace_with call that would cause
        a Link's endpoints to become identical, a ValidationError in
        Link.save causes the Link to be deleted.
        """
        # This is Link1's node_a
        original_node = nodes[0]
        # This is Link1's node_b
        replacement_node = nodes[1]

        original_node.replace_with(replacement_node)

        assert Link.objects.all().count() == 0
