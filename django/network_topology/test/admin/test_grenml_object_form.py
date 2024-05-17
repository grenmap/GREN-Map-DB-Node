"""
Copyright 2022 GRENMap Authors

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

Synopsis: Test file for forms for the GRENML models in the Django Admin
"""

import pytest

from grenml import models as grenml_models

from network_topology.models.topology import Topology
from network_topology.models import *
from network_topology.admin import (
    InstitutionForm, NodeForm, LinkForm,
)


@pytest.mark.django_db(transaction=True)
class TestGRENMLObjectAdminForms:

    INST_NAME = 'Test Institution'
    INST_SHORT_NAME = 'Test'

    NODE_NAME = 'Test Node'
    NODE_SHORT_NAME = 'Test'

    @pytest.fixture
    def root_topology(self):
        topology = Topology.objects.create(name='Root Topology')
        return topology

    @pytest.fixture
    def grenml_inst(self):
        """
        Directly ascertains the GRENML library's auto-ID behaviour.
        """
        grenml_inst = grenml_models.Institution(
            id=None,
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
        )
        return grenml_inst

    @pytest.fixture
    def grenml_node(self):
        """
        Directly ascertains the GRENML library's auto-ID behaviour.
        """
        grenml_node = grenml_models.Node(
            id=None,
            name=self.NODE_NAME,
            short_name=self.NODE_SHORT_NAME,
        )
        return grenml_node

    def test_inst_creation_with_auto_id(self, root_topology, grenml_inst):
        """
        Test creating an Institution via Admin form.
        ID not specified; relying on auto-ID.
        """
        data = {
            'topologies': [root_topology],
            'grenml_id': '',
            'name': self.INST_NAME,
            'short_name': self.INST_SHORT_NAME,
            'latitude': 0.0,
            'longitude': 0.0,
        }
        form = InstitutionForm(data)
        if not form.is_valid():
            assert not form.errors
        assert form.is_valid()
        assert form.clean()['grenml_id'] == grenml_inst.id

    def test_inst_creation_with_auto_id_collision(self, root_topology, grenml_inst):
        """
        Test creating an Institution via Admin form.
        ID not specified; relying on auto-ID.
        Auto-ID should result in a collision with an identical object.
        """
        # Create an object
        Institution.objects.create(
            grenml_id=grenml_inst.id,
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Submit a form to attempt to create a duplicate object
        # with the same ID.
        data = {
            'topologies': [root_topology],
            'grenml_id': '',
            'name': self.INST_NAME,
            'short_name': self.INST_SHORT_NAME,
            'latitude': 0.0,
            'longitude': 0.0,
        }
        form = InstitutionForm(data)
        # The form should not validate due to the ID collision
        assert not form.is_valid()

    def test_inst_creation_with_custom_id(self, root_topology, grenml_inst):
        """
        Test creating an Institution via Admin form.
        ID specified; all other fields should be exact duplicates.
        """
        # Create an object
        Institution.objects.create(
            grenml_id=grenml_inst.id,
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Submit a form to create a duplicate object, but with custom ID
        data = {
            'topologies': [root_topology],
            'grenml_id': 'Custom-ID',
            'name': self.INST_NAME,
            'short_name': self.INST_SHORT_NAME,
            'latitude': 0.0,
            'longitude': 0.0,
        }
        form = InstitutionForm(data)
        assert form.is_valid()

    def test_inst_update(self, root_topology, grenml_inst):
        """
        Test update an Institution via Admin form,
        to ensure we didn't break anything here.
        """
        # Create an object
        instance = Institution.objects.create(
            grenml_id=grenml_inst.id,
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Submit a form to create a duplicate object
        data = {
            'topologies': [root_topology],
            'grenml_id': '',
            'name': 'My New Name',
            'short_name': self.INST_SHORT_NAME,
            'latitude': 0.0,
            'longitude': 0.0,
        }
        form = InstitutionForm(data, instance=instance)
        assert form.is_valid()

    def test_node_creation_with_auto_id(self, root_topology, grenml_node):
        """
        Test creating a Node via Admin form.
        ID not specified; relying on auto-ID.
        """
        # Create a (required) owner Institution
        inst = Institution.objects.create(
            grenml_id='random-id',
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        data = {
            'topologies': [root_topology],
            'grenml_id': '',
            'name': self.NODE_NAME,
            'short_name': self.NODE_SHORT_NAME,
            'latitude': 0.0,
            'longitude': 0.0,
            'owners': [inst.id],
        }
        form = NodeForm(data)
        assert form.is_valid()
        assert form.clean()['grenml_id'] == grenml_node.id

    def test_node_creation_with_auto_id_collision(self, root_topology, grenml_node):
        """
        Test creating a Node via Admin form.
        ID not specified; relying on auto-ID.
        Auto-ID should result in a collision with an identical object.
        """
        # Create a (required) owner Institution
        inst = Institution.objects.create(
            grenml_id='random-id',
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Create a Node object
        Node.objects.create(
            grenml_id=grenml_node.id,
            name=self.NODE_NAME,
            short_name=self.NODE_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Submit a form to attempt to create a duplicate object
        # with the same ID.
        data = {
            'topologies': [root_topology],
            'grenml_id': '',
            'name': self.NODE_NAME,
            'short_name': self.NODE_SHORT_NAME,
            'latitude': 0.0,
            'longitude': 0.0,
            'owners': [inst.id],
        }
        form = NodeForm(data)
        # The form should not validate due to the ID collision
        assert not form.is_valid()

    def test_link_node_auto_id_near_collision(self, root_topology, grenml_node):
        """
        Test creating a Link via Admin form when the name and short_name
        are identical to a Node's; it should be valid as the type of
        the object factors into the automatic ID.
        """
        # Create a (required) owner Institution
        inst = Institution.objects.create(
            grenml_id='random-id',
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Create a Node object
        node_a = Node.objects.create(
            grenml_id=grenml_node.id,
            name=self.NODE_NAME,
            short_name=self.NODE_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # We need a second Node as an endpoint, just to be valid
        node_b = Node.objects.create(
            grenml_id='second-node',
            name='Second Node',
            short_name='2nd',
            latitude=0.0,
            longitude=0.0,
        )
        # Submit a Link creation form, but using node_a's names
        # The calculated auto-ID should be identical to the Node's
        data = {
            'topologies': [root_topology],
            'grenml_id': '',
            'name': self.NODE_NAME,
            'short_name': self.NODE_SHORT_NAME,
            'node_a': node_a,
            'node_b': node_b,
            'owners': [inst.id],
        }
        form = LinkForm(data)
        assert form.is_valid()

    def test_link_node_id_collision(self, root_topology):
        """
        Test creating a Link via Admin form when the ID is identical
        to one of another GRENML object's ID (in this case a Node).
        It should not validate, as the conflict is on BaseModel.
        """
        collision_prone_id = 'Improbably-Common-ID'
        # Create a (required) owner Institution
        inst = Institution.objects.create(
            grenml_id='random-id',
            name=self.INST_NAME,
            short_name=self.INST_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # Create a Node object
        node_a = Node.objects.create(
            grenml_id=collision_prone_id,
            name=self.NODE_NAME,
            short_name=self.NODE_SHORT_NAME,
            latitude=0.0,
            longitude=0.0,
        )
        # We need a second Node as an endpoint, just to be valid
        node_b = Node.objects.create(
            grenml_id='second-node',
            name='Second Node',
            short_name='2nd',
            latitude=0.0,
            longitude=0.0,
        )
        # Submit a Link creation form, but using node_a's names
        # The calculated auto-ID should be identical to the Node's
        data = {
            'topologies': [root_topology],
            'grenml_id': collision_prone_id,
            'name': 'Does not matter what my name is.',
            'short_name': 'No worries.',
            'node_a': node_a,
            'node_b': node_b,
            'owners': [inst.id],
        }
        form = LinkForm(data)
        # The form should not validate due to the ID collision
        assert not form.is_valid()
