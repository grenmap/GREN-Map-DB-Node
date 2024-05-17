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

Synopsis: Test file for the export node feature
"""

from grenml import parse
from network_topology.models.topology import Topology
import pytest
from network_topology.models import Node, Link, Institution, Property
from grenml_export.exporter import GRENMLExporter
import io

INSTITUTION_TEST_ID = 'TEST_ID'
INSTITUTION_TEST_NAME = 'TEST_NAME'
INSTITUTION_TEST_ADDRESS = "TEST_ADDRESS"
INSTITUTION_TEST_LATITUDE = -9
INSTITUTION_TEST_LONGITUDE = 22

NODE_TEST_ID = ["NODE_A_ID", "NODE_B_ID"]
NODE_TEST_NAME = ["NODE_A_NAME", "NODE_B_NAME"]
NODE_TEST_LATITUDE = [-9, -10]
NODE_TEST_LONGITUDE = [22, 20]
NODE_TEST_START = ["2020-03-20T14:30:43+00:00", "2020-03-20T14:30:44+00:00"]
NODE_TEST_END = ["2020-03-29T14:30:44+00:00", "2020-03-29T14:30:45+00:00"]

LINK_TEST_ID = "LINK_ID"
LINK_TEST_NAME = "LINK_NAME"
LINK_TEST_START = "2020-03-20T14:30:43+05:00"
LINK_TEST_END = "2020-03-29T14:30:43Z"

PROPERTY_TEST_NAME = 'tag'
PROPERTY_TEST_VALUE = 'NREN'


def check_additional_properties(element, **kwargs):
    """
    This method verifies the additional properties are correct or not
    """
    element.__dict__.items() <= kwargs.items()


def check_lifetime(element, lifetime_start, lifetime_end):
    """
    This method verifies that lifetime element is correct or not
    """
    assert element.lifetime_start == lifetime_start
    assert element.lifetime_end == lifetime_end


def check_location(
    location_element, latitude, longitude, altitude, unlocode, address
):
    """
    This method verifies that location element is correct or not
    """
    if longitude is not None:
        assert location_element.longitude == longitude
    if latitude is not None:
        assert location_element.latitude == latitude
    if altitude is not None:
        assert location_element.altitude == altitude
    if unlocode is not None:
        assert location_element.unlocode == unlocode
    if address is not None:
        if not isinstance(address, (list, set, tuple)):
            address = [address]
        assert location_element.addresses == address


class TestExportNode:

    @pytest.mark.django_db
    def test_export_default_topology(self):
        """
        This test checks the writer's ability to write
        default xml when pass only instance of manager
        """

        institution = Institution.objects.create(
            grenml_id=INSTITUTION_TEST_ID,
            name=INSTITUTION_TEST_NAME,
            address=INSTITUTION_TEST_ADDRESS,
            latitude=INSTITUTION_TEST_LATITUDE,
            longitude=INSTITUTION_TEST_LONGITUDE,
        )

        node_a = Node.objects.create(
            grenml_id=NODE_TEST_ID[0],
            name=NODE_TEST_NAME[0],
            latitude=NODE_TEST_LATITUDE[0],
            longitude=NODE_TEST_LONGITUDE[0],
            start=NODE_TEST_START[0],
            end=NODE_TEST_END[0],
        )

        node_b = Node.objects.create(
            grenml_id=NODE_TEST_ID[1],
            name=NODE_TEST_NAME[1],
            latitude=NODE_TEST_LATITUDE[1],
            longitude=NODE_TEST_LONGITUDE[1],
            start=NODE_TEST_START[1],
            end=NODE_TEST_END[1],
        )

        link = Link.objects.create(
            grenml_id=LINK_TEST_ID,
            name=LINK_TEST_NAME,
            node_a=node_a,
            node_b=node_b,
            start=LINK_TEST_START,
            end=LINK_TEST_END,
        )

        Property.objects.create(
            property_for=institution,
            name=PROPERTY_TEST_NAME,
            value=PROPERTY_TEST_VALUE
        )

        Property.objects.create(
            property_for=node_a,
            name=PROPERTY_TEST_NAME,
            value=PROPERTY_TEST_VALUE
        )

        Property.objects.create(
            property_for=link,
            name=PROPERTY_TEST_NAME,
            value=PROPERTY_TEST_VALUE
        )

        root = Topology.objects.create(name='test topology')

        root.owner = institution
        root.save()

        # Add parent topology to the created elements
        institution.topologies.add(root)
        node_a.topologies.add(root)
        node_b.topologies.add(root)
        link.topologies.add(root)

        exporter = GRENMLExporter()
        output_stream = exporter.to_stream()
        p = parse.GRENMLParser()
        manager = p.parse_byte_stream(io.BytesIO(output_stream.getvalue().encode()))

        institution_out = manager.get_institution(id=INSTITUTION_TEST_ID)
        node_a_out = manager.get_node(id=NODE_TEST_ID[0])
        node_b_out = manager.get_node(id=NODE_TEST_ID[1])
        link_out = manager.get_link(id=LINK_TEST_ID)

        # Check institution ID
        assert institution_out.id == INSTITUTION_TEST_ID
        # Check institution Name
        assert institution_out.name == INSTITUTION_TEST_NAME
        # Check others properties
        check_additional_properties(
            institution_out,
            address=[INSTITUTION_TEST_ADDRESS]
        )
        # Check properties
        assert institution_out.additional_properties[PROPERTY_TEST_NAME] == [PROPERTY_TEST_VALUE]

        # Check node a and b
        assert node_a_out.name == NODE_TEST_NAME[0]
        assert node_b_out.name == NODE_TEST_NAME[1]
        # Check properties
        assert node_a_out.additional_properties[PROPERTY_TEST_NAME] == [PROPERTY_TEST_VALUE]

        check_lifetime(node_a_out, NODE_TEST_START[0], NODE_TEST_END[0])
        check_lifetime(node_b_out, NODE_TEST_START[1], NODE_TEST_END[1])

        check_location(
            node_a_out,
            NODE_TEST_LATITUDE[0],
            NODE_TEST_LONGITUDE[0],
            None, None, None
        )
        check_location(
            node_b_out,
            NODE_TEST_LATITUDE[1],
            NODE_TEST_LONGITUDE[1],
            None, None, None
        )

        # Check link id
        assert link_out.id == LINK_TEST_ID
        # checking link' name
        assert link_out.name == LINK_TEST_NAME
        # Check properties
        assert link_out.additional_properties[PROPERTY_TEST_NAME] == [PROPERTY_TEST_VALUE]
