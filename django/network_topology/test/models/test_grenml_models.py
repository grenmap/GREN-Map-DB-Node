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

Synopsis: Test file for the GRENML database models
"""

import pytest
from datetime import datetime
from datetime import timedelta

from django.core.exceptions import ValidationError
from network_topology.models import *
from django.utils import timezone


@pytest.mark.django_db(transaction=True)
class TestGRENMLModels:

    @pytest.fixture
    def nodes(self):
        nodes = [
            Node.objects.create(
                grenml_id='test_node_1', name='Node 1',
                longitude=-72.750000, latitude=46.566666
            ),
            Node.objects.create(
                grenml_id='test_node_2', name='Node 2',
                longitude=-72.750000, latitude=46.566666
            ),
        ]
        return nodes

    @pytest.fixture
    def link(self, nodes):
        link = Link.objects.create(
            grenml_id='test_link', name='Test Link',
            node_a=nodes[0], node_b=nodes[1]
        )
        return link

    def test_link_creation_no_errors(self, nodes):
        link_id = 'test_link_normal'
        link = Link.objects.create(
            grenml_id=link_id, name='Test Link', node_a=nodes[0], node_b=nodes[1]
        )
        link.save()
        link = Link.objects.filter(grenml_id=link_id).first()
        assert link.grenml_id is not None, 'A link was created with unique nodes but was not saved'

    def test_link_is_not_created_with_same_node(self, nodes):
        link_id = 'test_link_duplicate_node'
        with pytest.raises(ValidationError):
            # Verify that an attempt to create a link returns an error
            Link.objects.create(
                grenml_id=link_id, name='Test Link',
                node_a=nodes[0], node_b=nodes[0]
            )

    def test_link_set_with_the_same_node_does_not_save(self, nodes):
        link_id = 'test_link_updated_with_same_node'
        link = Link.objects.create(
            grenml_id=link_id, name='Test Link', node_a=nodes[0], node_b=nodes[1]
        )
        link.save()
        link.node_b = nodes[0]
        link.save()
        link = Link.objects.get(grenml_id=link_id)
        assert link.node_b != nodes[0], 'Link was changed to have the same node at both ends'

    def test_link_deletion_does_not_remove_nodes(self, nodes, link):
        link.delete()
        assert nodes[0] is not None and nodes[1] is not None

    def test_link_node_deletion_cascades(self, nodes, link):
        link_id = link.grenml_id
        nodes[0].delete()
        with pytest.raises(Link.DoesNotExist):
            Link.objects.get(grenml_id=link_id)

    @pytest.fixture
    def institutions(self):
        institutions = [
            Institution.objects.create(
                grenml_id='global', name='institution1',
                longitude=-72.750000, latitude=46.566666
            ),
            Institution.objects.create(
                grenml_id='123', name='University of Ottawa',
                longitude=-72.750000, latitude=46.566666
            ),
        ]
        return institutions

    def test_institution_modify(self, institutions):
        institution_a = Institution.objects.get(grenml_id='global')
        new_name = f'new + {institution_a.name}'
        institution_a.name = new_name
        institution_a.save()
        institution_a = Institution.objects.get(grenml_id='global')
        assert institution_a.name == new_name

    def test_node_owner(self, institutions, nodes):
        nodes[0].owners.add(institutions[0])
        nodes[0].save()
        node_a = Node.objects.get(grenml_id=nodes[0].grenml_id)
        assert institutions[0] in node_a.owners.all()

    def test_link_owner(self, institutions, link):
        link.owners.add(institutions[0])
        link.save()
        link_a = Link.objects.get(grenml_id=link.grenml_id)
        assert institutions[0] in link_a.owners.all()

    def test_node_owner_change(self, institutions, nodes):
        nodes[0].owners.add(institutions[0])
        nodes[0].save()
        assert institutions[0] in nodes[0].owners.all()
        nodes[0].owners.remove(institutions[0])
        nodes[0].owners.add(institutions[1])
        nodes[0].save()
        node_a = Node.objects.get(grenml_id=nodes[0].grenml_id)
        assert institutions[0] not in node_a.owners.all()
        assert institutions[1] in node_a.owners.all()

    def test_link_owner_change(self, institutions, link):
        link.owners.add(institutions[0])
        link.save()
        assert institutions[0] in link.owners.all()
        link.owners.remove(institutions[0])
        link.owners.add(institutions[1])
        link.save()
        link_a = Link.objects.get(grenml_id=link.grenml_id)
        assert institutions[0] not in link_a.owners.all()
        assert institutions[1] in link_a.owners.all()

    def test_node_owner_multiple(self, institutions, nodes):
        for institution in institutions:
            nodes[0].owners.add(institution)
            nodes[0].save()
            assert institution in nodes[0].owners.all()

    def test_link_owner_multiple(self, institutions, link):
        for institution in institutions:
            link.owners.add(institution)
            link.save()
            assert institution in link.owners.all()

    @pytest.fixture
    def institutions_with_location(self):
        institutions = [
            Institution.objects.create(
                grenml_id='66', name='institution66', address='CA',
                longitude=-72.750000, latitude=46.566666
            ),
        ]
        return institutions

    def test_institution_with_location_change(self, institutions_with_location):
        institution_a = Institution.objects.get(grenml_id='66')
        assert institution_a.address == 'CA'
        institution_a.address = 'US'
        institution_a.save()
        institution_a = Institution.objects.get(grenml_id='66')
        assert institution_a.address == 'US'

    @pytest.fixture
    def nodes_with_location(self):
        nodes = [
            Node.objects.create(
                grenml_id='1000',
                name='node1000',
                longitude=34.123456,
                latitude=5.123456,
                address="Test Address, US"
            ),
        ]
        return nodes

    def test_node_with_location(self, nodes_with_location):
        node_a = Node.objects.get(grenml_id='1000')
        full_address = node_a.get_full_address()
        assert 'Test Address, US' in full_address

    def test_node_with_lifetime(self):
        start_time = datetime.now(tz=timezone.utc)
        end_time = start_time + timedelta(days=365)
        node_a = Node.objects.create(
            grenml_id='1000', name='test', start=start_time, end=end_time,
            longitude=-72.750000, latitude=46.566666
        )
        node_a.save()
        node_a = Node.objects.get(grenml_id='1000')
        assert node_a.start == start_time
        assert node_a.end == end_time

    @pytest.fixture
    def properties(self, nodes, link):
        property = [
            Property.objects.create(
                name='node property',
                value='Test',
                property_for=nodes[0],
            ),
            Property.objects.create(
                name='Node Property New',
                value='Test New',
                property_for=nodes[1],
            ),
            Property.objects.create(
                name='link capacity',
                value='10000',
                property_for=link,
            ),
        ]
        return property

    def test_property_name_case_sensitivity(self, properties, nodes):
        property = Property.objects.get(property_for=nodes[1])
        assert property.name == 'node property new'
        assert property.value == 'Test New'

    def test_property_with_node_change(self, properties, nodes):
        property = Property.objects.get(property_for=nodes[0])
        assert property.name == 'node property'
        property.name = 'node property new'
        property.save()
        property = Property.objects.get(property_for=nodes[0])
        assert property.name == 'node property new'

    def test_property_with_link_change(self, properties, link):
        property = Property.objects.get(property_for=link)
        assert property.value == '10000'
        property.value = '80000'
        property.save()
        property = Property.objects.get(property_for=link)
        assert property.value == '80000'

    def test_property_with_node_deletion(self, properties, nodes):
        property = Property.objects.get(property_for=nodes[0])
        property.delete()
        with pytest.raises(Property.DoesNotExist):
            Property.objects.get(property_for=nodes[0])

    def test_property_with_link_deletion(self, properties, link):
        property = Property.objects.get(property_for=link)
        property.delete()
        with pytest.raises(Property.DoesNotExist):
            Property.objects.get(property_for=link)

    def test_property_with_link_deletion_cascades(self, properties, nodes, link):
        Property.objects.get(name='link capacity')
        link.delete()
        with pytest.raises(Property.DoesNotExist):
            Property.objects.get(name='link capacity')

    def test_property_with_node_deletion_cascades(self, properties, nodes, link):
        Property.objects.get(name='node property')
        nodes[0].delete()
        with pytest.raises(Property.DoesNotExist):
            Property.objects.get(name='node property')

    def test_link_can_be_created_with_same_id_as_node(self, nodes):
        Link.objects.create(
            grenml_id=nodes[0].grenml_id, name='Test Link',
            node_a=nodes[0], node_b=nodes[1]
        )

    def test_node_can_be_created_with_same_id_as_institution(self, institutions):
        Node.objects.create(
            grenml_id=institutions[0].grenml_id,
            name='Test Link',
            longitude=34.123456,
            latitude=5.123456,
            address="Test Address, US"
        )

    def test_first_topology_is_main_by_default(self):
        topology = Topology.objects.create(
            grenml_id='Topo1',
            name='Topo 1',
            parent=None,
            main=False,
        )
        assert topology.main
