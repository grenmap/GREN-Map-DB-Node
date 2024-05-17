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

Synopsis: Test file for the GRENML database model API.
    Note: This model API is for testing purposes only.
    The presence of these tests does not imply that the API has
    been tested thoroughly for production purposes.
"""

import pytest

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from network_topology.models import (
    Topology,
    Institution,
    Node,
    Link,
)
from network_topology.views.api import (
    TopologyViewSet,
    InstitutionViewSet,
    NodeViewSet,
    LinkViewSet,
)


# This is a mapping required by Django REST Framework's
# ViewSet.as_view() method.  To get the view for a GET request, for
# example, this is the syntax:
#     MyViewSet.as_view({'get': 'retrieve'})
# We abstract this with the constants below as follows:
#     MyViewSet.as_view(DRF_AS_VIEW_MAPS[GET])
GET = 'get'
POST = 'post'
PUT = 'put'
PATCH = 'patch'
DELETE = 'delete'
DRF_AS_VIEW_MAPS = {
    GET: {'get': 'retrieve'},
    POST: {'post': 'create'},
    PUT: {'put': 'update'},
    PATCH: {'patch': 'partial_update'},
    DELETE: {'delete': 'destroy'},
}


@pytest.mark.django_db
class TestNetworkTopologyModelAPI:
    """
    Base class for tests of the test-only model API
    that injects a few handy fixtures.
    """

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def superuser(self):
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            return superusers.first()
        else:
            return User.objects.create_superuser('admin', 'admin@example.com', '123456')

    @pytest.fixture
    def topology(self):
        return Topology.objects.create(
            grenml_id='Topo1',
            name='Topo 1',
        )

    @pytest.fixture
    def institution(self):
        return Institution.objects.create(
            grenml_id='Inst1',
            name='Institution 1',
            short_name='INST1',
            latitude=0.0,
            longitude=0.0,
        )

    @pytest.fixture
    def node(self):
        return Node.objects.create(
            grenml_id='Node1',
            name='Node 1',
            short_name='NODE1',
            latitude=0.0,
            longitude=0.0,
        )

    @pytest.fixture
    def link_nodes(self):
        node_a = Node.objects.create(
            grenml_id='NodeA',
            name='Node A',
            short_name='NODEA',
            latitude=0.0,
            longitude=0.0,
        )
        node_b = Node.objects.create(
            grenml_id='NodeB',
            name='Node B',
            short_name='NODEB',
            latitude=10.0,
            longitude=10.0,
        )
        return (node_a, node_b)

    @pytest.fixture
    def link(self, link_nodes):
        return Link.objects.create(
            grenml_id='Link1',
            name='Link 1',
            short_name='LINK1',
            node_a=link_nodes[0],
            node_b=link_nodes[1],
        )

    def test_api_hello_world(self, factory, superuser, topology):
        """
        This establishes the basic structure of Django REST Framework
        Viewset API tests, for reference, by simply retrieving a
        pre-seeded Topology.
        """
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[GET])
        url = reverse('topology-detail', kwargs={'pk': topology.pk})
        # .get method aligns with the ViewSet.as_view(...GET) param
        request = factory.get(url)
        force_authenticate(request, user=superuser)
        # The view requires the kwarg even though we also put
        # it in the URL above.
        response = view(request, pk=topology.pk)
        # This will print error messages returned by the view if the
        # assertion fails.
        print(response.data)
        assert response.status_code == status.HTTP_200_OK


class TestTopologyAPI(TestNetworkTopologyModelAPI):
    """
    Tests basic write functions on the (test-only) Topology API,
    including common POST, PUT, PATCH, and DELETE operations.
    """

    def test_topology_create(self, factory, superuser, institution):
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('topology-list')
        # No Properties, to keep it simple
        data = {
            'grenml_id': 'Topo',
            'name': 'Test Topology',
            'owner': institution.pk,
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # No topology should be created if no name is given
        data = {
            'grenml_id': 'Topo',
            'name': '',
            'owner': institution.pk,
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        response_data = response.data['name']
        assert "This field may not be blank." in response_data[0]
        assert response.status_code != status.HTTP_201_CREATED

        # Fetch the (only) Topology to confirm it was added to the DB
        topology = Topology.objects.get()
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[GET])
        url = reverse('topology-detail', kwargs={'pk': topology.pk})
        request = factory.get(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=topology.pk)
        assert response.status_code == status.HTTP_200_OK

    def test_topology_create_with_property(self, factory, superuser):
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('topology-list')
        data = {
            'grenml_id': 'Topo',
            'name': 'Test Topology',
            'properties': [
                {'name': 'key1', 'value': 'value1'},
            ],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Topology to confirm it was added to the DB
        topology = Topology.objects.get()
        # Confirm Property was added to the Topology
        assert topology.property('key1').get().value == 'value1'

    def test_topology_patch_properties(self, factory, superuser, topology):
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('topology-detail', kwargs={'pk': topology.pk})
        data = {
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=topology.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        topology = Topology.objects.get(pk=topology.pk)
        assert topology.property('key1').get().value == 'value1'
        assert topology.property('key2').get().value == 'value2'

    def test_topology_patch_parent(self, factory, superuser, topology):
        parent_topology = Topology.objects.create(grenml_id='ParentTopo', name='Parent')
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('topology-detail', kwargs={'pk': topology.pk})
        data = {
            'parent': parent_topology.pk,
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=topology.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        topology = Topology.objects.get(pk=topology.pk)
        assert topology.parent.pk == parent_topology.pk

    def test_topology_put_with_properties(self, factory, superuser, topology):
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[PUT])
        # PUT this Topology on top of the existing one
        url = reverse('topology-detail', kwargs={'pk': topology.pk})
        data = {
            'grenml_id': 'Topo',
            'name': 'Test Topology',
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
        }
        request = factory.put(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=topology.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        topology = Topology.objects.get(pk=topology.pk)
        assert topology.grenml_id == 'Topo'
        assert topology.name == 'Test Topology'
        assert topology.property('key1').get().value == 'value1'
        assert topology.property('key2').get().value == 'value2'

    def test_topology_delete(self, factory, superuser, topology):
        view = TopologyViewSet.as_view(DRF_AS_VIEW_MAPS[DELETE])
        url = reverse('topology-detail', kwargs={'pk': topology.pk})
        request = factory.delete(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=topology.pk)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Topology.objects.exists()


class TestInstitutionAPI(TestNetworkTopologyModelAPI):
    """
    Tests basic write functions on the (test-only) Institution API,
    including common POST, PUT, PATCH, and DELETE operations.
    """

    def test_institution_create(self, factory, superuser):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('institution-list')
        # No Properties or Topologies, to keep it simple
        data = {
            'grenml_id': 'Inst',
            'name': 'Test Institution',
            'latitude': 10.0,
            'longitude': 20.0,
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Institution to confirm it was added to the DB
        institution = Institution.objects.get()
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[GET])
        url = reverse('institution-detail', kwargs={'pk': institution.pk})
        request = factory.get(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=institution.pk)
        assert response.status_code == status.HTTP_200_OK

    def test_institution_create_with_property(self, factory, superuser):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('institution-list')
        data = {
            'grenml_id': 'Inst',
            'name': 'Test Institution',
            'latitude': 10.0,
            'longitude': 20.0,
            'properties': [
                {'name': 'key1', 'value': 'value1'},
            ],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Institution to confirm it was added to the DB
        institution = Institution.objects.get()
        # Confirm Property was added to the Institution
        assert institution.property('key1').get().value == 'value1'

    def test_institution_create_with_topology(self, factory, superuser, topology):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('institution-list')
        data = {
            'grenml_id': 'Inst',
            'name': 'Test Institution',
            'latitude': 10.0,
            'longitude': 20.0,
            'topologies': [topology.pk],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Institution to confirm it was added to the DB
        institution = Institution.objects.get()
        # Confirm Institution is in the Topology
        assert topology.pk in institution.topologies.values_list('pk', flat=True)

    def test_institution_patch_properties(self, factory, superuser, institution):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('institution-detail', kwargs={'pk': institution.pk})
        data = {
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=institution.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        institution = Institution.objects.get(pk=institution.pk)
        assert institution.property('key1').get().value == 'value1'
        assert institution.property('key2').get().value == 'value2'

    def test_institution_patch_topologies(self, factory, superuser, institution, topology):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('institution-detail', kwargs={'pk': institution.pk})
        data = {
            'topologies': [topology.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=institution.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        institution = Institution.objects.get(pk=institution.pk)
        assert topology.pk in institution.topologies.values_list('pk', flat=True)

    def test_institution_patch_change_topologies(self, factory, superuser, institution, topology):
        """
        Start with the Institution belonging to one Topology,
        submit a PATCH indicating that it should belong to only
        a different Topology, and expect it to respect those
        instructions explicitly.
        """
        institution.topologies.add(topology)
        second_topology = Topology.objects.create(
            grenml_id='Topo2',
            name='Topology 2',
        )
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('institution-detail', kwargs={'pk': institution.pk})
        data = {
            'topologies': [second_topology.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=institution.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        institution = Institution.objects.get(pk=institution.pk)
        assert institution.topologies.count() == 1
        assert second_topology.pk in institution.topologies.values_list('pk', flat=True)

    def test_institution_put_with_prop_and_topo(self, factory, superuser, institution, topology):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[PUT])
        # PUT this Institution on top of the existing one
        url = reverse('institution-detail', kwargs={'pk': institution.pk})
        data = {
            'grenml_id': 'Inst',
            'name': 'Test Institution',
            'latitude': 10.0,
            'longitude': 20.0,
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
            'topologies': [topology.pk],
        }
        request = factory.put(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=institution.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        institution = Institution.objects.get(pk=institution.pk)
        assert institution.grenml_id == 'Inst'
        assert institution.name == 'Test Institution'
        assert institution.property('key1').get().value == 'value1'
        assert institution.property('key2').get().value == 'value2'
        assert topology.pk in institution.topologies.values_list('pk', flat=True)

    def test_institution_delete(self, factory, superuser, institution):
        view = InstitutionViewSet.as_view(DRF_AS_VIEW_MAPS[DELETE])
        url = reverse('institution-detail', kwargs={'pk': institution.pk})
        request = factory.delete(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=institution.pk)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Institution.objects.exists()


class TestNodeAPI(TestNetworkTopologyModelAPI):
    """
    Tests basic write functions on the (test-only) Node API,
    including common POST, PUT, PATCH, and DELETE operations.
    """

    def test_node_create(self, factory, superuser):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('node-list')
        # No Properties or Topologies or owner Institutions,
        # to keep it simple.
        data = {
            'grenml_id': 'Node',
            'name': 'Test Node',
            'latitude': 10.0,
            'longitude': 20.0,
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Node to confirm it was added to the DB
        node = Node.objects.get()
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[GET])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        request = factory.get(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK

    def test_node_create_with_property(self, factory, superuser):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('node-list')
        data = {
            'grenml_id': 'Node',
            'name': 'Test Node',
            'latitude': 10.0,
            'longitude': 20.0,
            'properties': [
                {'name': 'key1', 'value': 'value1'},
            ],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Node to confirm it was added to the DB
        node = Node.objects.get()
        # Confirm Property was added to the Node
        assert node.property('key1').get().value == 'value1'

    def test_node_create_with_topology(self, factory, superuser, topology):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('node-list')
        data = {
            'grenml_id': 'Node',
            'name': 'Test Node',
            'latitude': 10.0,
            'longitude': 20.0,
            'topologies': [topology.pk],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Node to confirm it was added to the DB
        node = Node.objects.get()
        # Confirm Node is in the Topology
        assert topology.pk in node.topologies.values_list('pk', flat=True)

    def test_node_create_with_owner(self, factory, superuser, institution):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('node-list')
        data = {
            'grenml_id': 'Node',
            'name': 'Test Node',
            'latitude': 10.0,
            'longitude': 20.0,
            'owners': [institution.pk],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Node to confirm it was added to the DB
        node = Node.objects.get()
        # Confirm Node has the Institution as owner
        assert institution.pk in node.owners.values_list('pk', flat=True)

    def test_node_patch_properties(self, factory, superuser, node):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        data = {
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        node = Node.objects.get(pk=node.pk)
        assert node.property('key1').get().value == 'value1'
        assert node.property('key2').get().value == 'value2'

    def test_node_patch_topologies(self, factory, superuser, node, topology):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        data = {
            'topologies': [topology.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        node = Node.objects.get(pk=node.pk)
        assert topology.pk in node.topologies.values_list('pk', flat=True)

    def test_node_patch_owners(self, factory, superuser, node, institution):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        data = {
            'owners': [institution.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        node = Node.objects.get(pk=node.pk)
        assert institution.pk in node.owners.values_list('pk', flat=True)

    def test_node_patch_change_topologies(self, factory, superuser, node, topology):
        """
        Start with the Node belonging to one Topology,
        submit a PATCH indicating that it should belong to only
        a different Topology, and expect it to respect those
        instructions explicitly.
        """
        node.topologies.add(topology)
        second_topology = Topology.objects.create(
            grenml_id='Topo2',
            name='Topology 2',
        )
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        data = {
            'topologies': [second_topology.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        node = Node.objects.get(pk=node.pk)
        assert node.topologies.count() == 1
        assert second_topology.pk in node.topologies.values_list('pk', flat=True)

    def test_node_patch_change_owners(self, factory, superuser, node, institution):
        """
        Start with the Node belonging to one owner Institution,
        submit a PATCH indicating that it should belong to only
        a different Institution, and expect it to respect those
        instructions explicitly.
        """
        node.owners.add(institution)
        second_institution = Institution.objects.create(
            grenml_id='Inst2',
            name='Institution 2',
            latitude=42.0,
            longitude=47.0,
        )
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        data = {
            'owners': [second_institution.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        node = Node.objects.get(pk=node.pk)
        assert node.owners.count() == 1
        assert second_institution.pk in node.owners.values_list('pk', flat=True)

    def test_node_put_with_prop_and_topo_and_owner(
        self,
        factory,
        superuser,
        node,
        topology,
        institution,
    ):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[PUT])
        # PUT this Node on top of the existing one
        url = reverse('node-detail', kwargs={'pk': node.pk})
        data = {
            'grenml_id': 'Node',
            'name': 'Test Node',
            'latitude': 10.0,
            'longitude': 20.0,
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
            'topologies': [topology.pk],
            'owners': [institution.pk],
        }
        request = factory.put(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        node = Node.objects.get(pk=node.pk)
        assert node.grenml_id == 'Node'
        assert node.name == 'Test Node'
        assert node.property('key1').get().value == 'value1'
        assert node.property('key2').get().value == 'value2'
        assert topology.pk in node.topologies.values_list('pk', flat=True)
        assert institution.pk in node.owners.values_list('pk', flat=True)

    def test_node_delete(self, factory, superuser, node):
        view = NodeViewSet.as_view(DRF_AS_VIEW_MAPS[DELETE])
        url = reverse('node-detail', kwargs={'pk': node.pk})
        request = factory.delete(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=node.pk)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Node.objects.exists()


class TestLinkAPI(TestNetworkTopologyModelAPI):
    """
    Tests basic write functions on the (test-only) Link API,
    including common POST, PUT, PATCH, and DELETE operations.
    """

    def test_link_create(self, factory, superuser, link_nodes):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('link-list')
        # No Properties or Topologies or owner Institutions,
        # to keep it simple.
        data = {
            'grenml_id': 'Link',
            'name': 'Test Link',
            'node_a': link_nodes[0].pk,
            'node_b': link_nodes[1].pk,
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the Link to confirm it was added to the DB
        link = Link.objects.get()
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[GET])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        request = factory.get(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK

    def test_link_create_with_property(self, factory, superuser, link_nodes):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('link-list')
        data = {
            'grenml_id': 'Link',
            'name': 'Test Link',
            'node_a': link_nodes[0].pk,
            'node_b': link_nodes[1].pk,
            'properties': [
                {'name': 'key1', 'value': 'value1'},
            ],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Link to confirm it was added to the DB
        link = Link.objects.get()
        # Confirm Property was added to the Link
        assert link.property('key1').get().value == 'value1'

    def test_link_create_with_topology(self, factory, superuser, topology, link_nodes):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('link-list')
        data = {
            'grenml_id': 'Link',
            'name': 'Test Link',
            'node_a': link_nodes[0].pk,
            'node_b': link_nodes[1].pk,
            'topologies': [topology.pk],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Link to confirm it was added to the DB
        link = Link.objects.get()
        # Confirm Link is in the Topology
        assert topology.pk in link.topologies.values_list('pk', flat=True)

    def test_link_create_with_owner(self, factory, superuser, link_nodes, institution):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[POST])
        url = reverse('link-list')
        data = {
            'grenml_id': 'Link',
            'name': 'Test Link',
            'node_a': link_nodes[0].pk,
            'node_b': link_nodes[1].pk,
            'owners': [institution.pk],
        }
        request = factory.post(url, data)
        force_authenticate(request, user=superuser)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED

        # Fetch the (only) Link to confirm it was added to the DB
        link = Link.objects.get()
        # Confirm Link has the Institution as owner
        assert institution.pk in link.owners.values_list('pk', flat=True)

    def test_link_patch_nodes(self, factory, superuser, link):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        # Swap the endpoint Nodes
        data = {
            'node_a': link.node_b.pk,
            'node_b': link.node_a.pk,
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert link.node_a.grenml_id == 'NodeB'
        assert link.node_b.grenml_id == 'NodeA'

    def test_link_patch_properties(self, factory, superuser, link):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        data = {
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert link.property('key1').get().value == 'value1'
        assert link.property('key2').get().value == 'value2'

    def test_link_patch_topologies(self, factory, superuser, link, topology):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        data = {
            'topologies': [topology.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert topology.pk in link.topologies.values_list('pk', flat=True)

    def test_link_patch_owners(self, factory, superuser, link, institution):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        data = {
            'owners': [institution.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert institution.pk in link.owners.values_list('pk', flat=True)

    def test_link_patch_change_topologies(self, factory, superuser, link, topology):
        """
        Start with the Link belonging to one Topology,
        submit a PATCH indicating that it should belong to only
        a different Topology, and expect it to respect those
        instructions explicitly.
        """
        link.topologies.add(topology)
        second_topology = Topology.objects.create(
            grenml_id='Topo2',
            name='Topology 2',
        )
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        data = {
            'topologies': [second_topology.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert link.topologies.count() == 1
        assert second_topology.pk in link.topologies.values_list('pk', flat=True)

    def test_link_patch_change_owners(self, factory, superuser, link, institution):
        """
        Start with the Link belonging to one owner Institution,
        submit a PATCH indicating that it should belong to only
        a different Institution, and expect it to respect those
        instructions explicitly.
        """
        link.owners.add(institution)
        second_institution = Institution.objects.create(
            grenml_id='Inst2',
            name='Institution 2',
            latitude=42.0,
            longitude=47.0,
        )
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PATCH])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        data = {
            'owners': [second_institution.pk],
        }
        request = factory.patch(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert link.owners.count() == 1
        assert second_institution.pk in link.owners.values_list('pk', flat=True)

    def test_link_put_with_prop_and_topo_and_owner(
        self,
        factory,
        superuser,
        link,
        link_nodes,
        topology,
        institution,
    ):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[PUT])
        # PUT this Link on top of the existing one
        url = reverse('link-detail', kwargs={'pk': link.pk})
        data = {
            'grenml_id': 'Link',
            'name': 'Test Link',
            'node_a': link_nodes[0].pk,
            'node_b': link_nodes[1].pk,
            'properties': [
                {'name': 'key1', 'value': 'value1'},
                {'name': 'key2', 'value': 'value2'},
            ],
            'topologies': [topology.pk],
            'owners': [institution.pk],
        }
        request = factory.put(url, data)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_200_OK
        # Refresh our copy of the model object to reflect changes
        link = Link.objects.get(pk=link.pk)
        assert link.grenml_id == 'Link'
        assert link.name == 'Test Link'
        assert link.property('key1').get().value == 'value1'
        assert link.property('key2').get().value == 'value2'
        assert topology.pk in link.topologies.values_list('pk', flat=True)
        assert institution.pk in link.owners.values_list('pk', flat=True)

    def test_link_delete(self, factory, superuser, link):
        view = LinkViewSet.as_view(DRF_AS_VIEW_MAPS[DELETE])
        url = reverse('link-detail', kwargs={'pk': link.pk})
        request = factory.delete(url)
        force_authenticate(request, user=superuser)
        response = view(request, pk=link.pk)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Link.objects.exists()
