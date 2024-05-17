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

Synopsis: Test file for GRENML Properties.
"""

import pytest

from network_topology.models import *


@pytest.mark.django_db
class TestPropertyMethod:

    @pytest.fixture
    def node(self):
        return Node.objects.create(
            grenml_id='NodeA',
            name='Node A',
            short_name='NA',
            latitude=0.0,
            longitude=0.0,
        )

    def test_property_getter_zero(self, node):
        assert node.property('k1').count() == 0

    def test_property_getter_one(self, node):
        Property.objects.create(name='k1', value='v1', property_for=node)
        assert node.property('k1').count() == 1

    def test_property_getter_three(self, node):
        Property.objects.create(name='k1', value='v1', property_for=node)
        Property.objects.create(name='k1', value='v2', property_for=node)
        Property.objects.create(name='k1', value='v3', property_for=node)
        assert node.property('k1').count() == 3

    def test_property_getter_others(self, node):
        node2 = Node.objects.create(
            grenml_id='NodeB',
            name='Node B',
            short_name='NB',
            latitude=10.0,
            longitude=10.0,
        )
        Property.objects.create(name='k1', value='v1', property_for=node)
        Property.objects.create(name='k1', value='v2', property_for=node2)
        assert node.property('k1').count() == 1
        assert node.property('k1').first().value == 'v1'

    def test_property_setter_zero(self, node):
        node.property('k1', value='v2')
        properties = Property.objects.all()
        assert properties.count() == 1
        assert properties.first().name == 'k1'

    def test_property_setter_single_deduplicate(self, node):
        Property.objects.create(name='k1', value='v1', property_for=node)
        node.property('k1', value='v2')
        properties = Property.objects.all()
        assert properties.count() == 1
        assert properties.first().value == 'v2'

    def test_property_setter_single_no_deduplicate(self, node):
        Property.objects.create(name='k1', value='v1', property_for=node)
        node.property('k1', value='v2', deduplicate=False)
        properties = Property.objects.all()
        assert properties.count() == 2
        values = [p.value for p in properties]
        assert set(values) == set(['v1', 'v2'])

    def test_property_setter_multiple_deduplicate(self, node):
        Property.objects.create(name='k1', value='v1', property_for=node)
        Property.objects.create(name='k1', value='v2', property_for=node)
        Property.objects.create(name='k1', value='v3', property_for=node)
        with pytest.raises(Property.MultipleObjectsReturned):
            node.property('k1', value='v4')

    def test_property_setter_multiple_no_deduplicate(self, node):
        Property.objects.create(name='k1', value='v1', property_for=node)
        Property.objects.create(name='k1', value='v2', property_for=node)
        Property.objects.create(name='k1', value='v3', property_for=node)
        node.property('k1', value='v4', deduplicate=False)
        properties = Property.objects.all()
        assert properties.count() == 4
        values = [p.value for p in properties]
        assert set(values) == set(['v1', 'v2', 'v3', 'v4'])
