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

Synopsis: Test file for the GRENML database models' fields.
"""

import pytest
from random import choice
from string import ascii_letters
from types import SimpleNamespace

from network_topology.models import *


@pytest.mark.django_db
class TestFieldTrimming:

    def generate_random_string(self, length):
        """
        Generate a string of specified length, consisting of random
        ASCII letter characters.
        """
        return ''.join(choice(ascii_letters) for i in range(length))  # nosec B311

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
    def link(self):
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
        return Link.objects.create(
            grenml_id='Link1',
            name='Link 1',
            short_name='LINK1',
            node_a=node_a,
            node_b=node_b,
        )

    def test_name_not_trimmed(self, topology):
        max_length = topology._meta.get_field('name').max_length
        assert max_length > 14
        name = self.generate_random_string(13)
        topology.set_name(name)
        topology.save()
        assert topology.name == name

    def test_max_length_name_not_trimmed(self, node):
        max_length = node._meta.get_field('name').max_length
        name = self.generate_random_string(max_length)
        node.set_name(name)
        node.save()
        assert node.name == name

    def test_long_name_trimmed(self, link):
        max_length = link._meta.get_field('name').max_length
        name = self.generate_random_string(max_length + 1)
        link.set_name(name)
        link.save()
        assert link.name == name[:max_length - 3] + '...'

    def test_name_trim_on_direct_instantiation(self, node):
        max_length = node._meta.get_field('name').max_length
        name = self.generate_random_string(max_length + 1)
        new_node = Node(
            grenml_id='NewNode',
            name=name,
            short_name=name,
            latitude=0.0,
            longitude=0.0,
        )
        assert new_node.name == name[:max_length - 3] + '...'
        new_node.save()
        assert new_node.name == name[:max_length - 3] + '...'

    def test_name_trim_on_manager_instantiation(self, node):
        max_length = node._meta.get_field('name').max_length
        name = self.generate_random_string(max_length + 1)
        new_node = Node.objects.create(
            grenml_id='NewNode',
            name=name,
            short_name=name,
            latitude=0.0,
            longitude=0.0,
        )
        assert new_node.name == name[:max_length - 3] + '...'

    def test_property_value_trim_on_direct_instantiation(self, node):
        # Make a Property in order to inspect its fields
        dummy_property = Property()
        max_length = dummy_property._meta.get_field('value').max_length
        value = self.generate_random_string(max_length + 1)
        new_property = Property(name='prop', value=value, property_for=node)
        assert new_property.value == value[:max_length - 3] + '...'


@pytest.mark.django_db
class TestFieldTruncation:

    @pytest.fixture
    def node(self):
        return Node.objects.create(
            grenml_id='Node1',
            name='Node 1',
            short_name='NODE1',
            latitude=0.0,
            longitude=0.0,
        )

    def test_truncate_decimal_value_pass(self):
        # SimpleNamespace is used here as what amounts to an empty class
        # so that we can add in the properties required for the meta
        # argument for _truncate_decimal_value without requiring the
        # overhead of actually creating the proper type of object
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-50.0, 50.0)
        input_value = 47.0
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == 47.0

    def test_truncate_decimal_value_too_low(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-42.0, 42.0)
        input_value = -47.0
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == -42.0

    def test_truncate_decimal_value_too_high(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-42.0, 42.0)
        input_value = 47.0
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == 42.0

    def test_truncate_decimal_value_too_many_digits_positive(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-100000000.0, 100000000.0)
        input_value = 4700.474747
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == 999.999999

    def test_truncate_decimal_value_too_many_digits_negative(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-100000000.0, 100000000.0)
        input_value = -4700.474747
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == -999.999999

    def test_truncate_decimal_value_too_much_precision_positive_round_down(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-100000000.0, 100000000.0)
        input_value = 470.47474747
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == 470.474747

    def test_truncate_decimal_value_too_much_precision_positive_round_up(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-100000000.0, 100000000.0)
        input_value = 470.51515151
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == 470.515152

    def test_truncate_decimal_value_too_much_precision_negative_round_down(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-100000000.0, 100000000.0)
        input_value = -470.47474747
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == -470.474747

    def test_truncate_decimal_value_too_much_precision_negative_round_up(self):
        meta = SimpleNamespace()
        meta.max_digits = 9
        meta.decimal_places = 6
        range = (-100000000.0, 100000000.0)
        input_value = -470.51515151
        output_value = Location._truncate_decimal_value(input_value, meta, range)
        assert output_value == -470.515152

    def test_coordinate_setter_fields_not_truncated(self, node):
        node.coordinates = (90.0, -180.0, 5632.704)
        node.save()
        assert node.latitude == 90.0
        assert node.longitude == -180.0
        assert node.altitude == 5632.704

    def test_coordinate_setter_fields_truncated_for_range(self, node):
        node.coordinates = (-91.0, 180.1, -12000.0)
        node.save()
        assert node.latitude == -90.0
        assert node.longitude == 180.0
        assert node.altitude == Location.ALTITUDE_RANGE[0]

    def test_coordinate_setter_fields_truncated_for_precision(self, node):
        node.coordinates = (-89.123456789, 179.123123123, -1000.123456789)
        node.save()
        # This one should be rounded up
        assert node.latitude == -89.123457
        # This one should be rounded down
        assert node.longitude == 179.123123
        # This one should be rounded up
        assert node.altitude == -1000.123457
