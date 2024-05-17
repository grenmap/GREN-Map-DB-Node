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
"""
import pytest

from collation.action_types.deduplication_action_mixin import (
    DeduplicationActionMixin,
    NoSubstituteElementError,
    MultipleSubstituteElementsError,
)
from collation.constants import ElementTypes
from network_topology import models as tm


@pytest.mark.django_db
class TestDeduplicationActionMixin:
    """
    This class contains tests for the mixin class
    DeduplicationActionMixin.
    """

    @pytest.fixture
    def dedupe_mixin(self):
        """
        Instantiates the DeduplicationActionMixin class and sets its
        self.element_type to NODE.
        """
        mixin = DeduplicationActionMixin()
        mixin.element_type = ElementTypes.NODE
        return mixin

    @pytest.fixture
    def two_topologies(self):
        """
        Populates the database with a parent and child Topology
        and some basic network data in each.
        """
        topology_one = tm.Topology.objects.create(
            grenml_id='Topo1',
            name='Topology 1',
        )
        parent_institution = tm.Institution.objects.create(
            grenml_id='ParentInst',
            name='Parent Inst',
            short_name='ParentInst',
            latitude=10,
            longitude=10,
        )
        parent_institution.topologies.add(topology_one)
        node_a = tm.Node.objects.create(grenml_id='NA', name='node_a', latitude=80, longitude=80)
        node_a.owners.add(parent_institution)
        node_a.topologies.add(topology_one)
        node_b = tm.Node.objects.create(grenml_id='NB', name='node_b', latitude=90, longitude=90)
        node_b.owners.add(parent_institution)
        node_b.topologies.add(topology_one)
        parent_link = tm.Link.objects.create(
            grenml_id='L1',
            name='link',
            node_a=node_a,
            node_b=node_b,
        )
        parent_link.owners.add(parent_institution)
        parent_link.topologies.add(topology_one)

        topology_two = tm.Topology.objects.create(
            grenml_id='Topo2',
            name='Topology 2',
            parent=topology_one,
        )
        child_institution = tm.Institution.objects.create(
            grenml_id='ChildInst',
            name='Child Inst',
            short_name='ChildInst',
            latitude=30,
            longitude=30,
        )
        child_institution.topologies.add(topology_two)
        node_c = tm.Node.objects.create(grenml_id='NC', name='node_c', latitude=60, longitude=60)
        node_c.owners.add(child_institution)
        node_c.topologies.add(topology_two)
        node_d = tm.Node.objects.create(grenml_id='ND', name='node_d', latitude=70, longitude=70)
        node_d.owners.add(child_institution)
        node_d.topologies.add(topology_two)
        child_link = tm.Link.objects.create(
            grenml_id='L2',
            name='another link',
            node_a=node_c,
            node_b=node_d,
        )
        child_link.owners.add(child_institution)
        child_link.topologies.add(topology_two)

        return (topology_one, topology_two)

    def test_fetch_element_from_any_topology(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be node_a
        starting_element = two_topologies[0].nodes.first()

        target = dedupe_mixin._fetch_deduplication_target_element(
            starting_element,
            'NC',
        )
        assert target.grenml_id == 'NC'

    def test_fetch_element_that_doesnt_exist(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be node_a
        starting_element = two_topologies[0].nodes.first()

        with pytest.raises(NoSubstituteElementError):
            dedupe_mixin._fetch_deduplication_target_element(
                starting_element,
                'NE',
            )

    def test_fetch_element_that_has_more_than_one_match(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be node_a
        starting_element = two_topologies[0].nodes.first()

        # Create a duplicate NC Node
        tm.Node.objects.create(
            grenml_id='NC',
            name='node_c_duplicate',
            latitude=100.0,
            longitude=100.0,
        )

        with pytest.raises(MultipleSubstituteElementsError):
            dedupe_mixin._fetch_deduplication_target_element(
                starting_element,
                'NC',
            )

    def test_fetch_element_from_specified_topology(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be node_a
        starting_element = two_topologies[0].nodes.first()

        # Create a duplicate NA Node in second (child) Topology
        node_a_2 = tm.Node.objects.create(
            grenml_id='NA',
            name='node_a_duplicate',
            latitude=100.0,
            longitude=100.0,
        )
        node_a_2.topologies.add(two_topologies[1])

        with pytest.raises(MultipleSubstituteElementsError):
            dedupe_mixin._fetch_deduplication_target_element(
                starting_element,
                'NA',
            )

        # Fetch the original one from the parent Topo
        target = dedupe_mixin._fetch_deduplication_target_element(
            starting_element,
            'NA',
            topology_id=two_topologies[0].grenml_id,
        )
        assert target.name == 'node_a'

        # Fetch the new duplicate
        target = dedupe_mixin._fetch_deduplication_target_element(
            starting_element,
            'NA',
            topology_id=two_topologies[1].grenml_id,
        )
        assert target.name == 'node_a_duplicate'

    def test_fetch_element_with_incorrect_topo(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be node_a
        starting_element = two_topologies[1].nodes.first()

        with pytest.raises(NoSubstituteElementError):
            dedupe_mixin._fetch_deduplication_target_element(
                starting_element,
                'NC',
                topology_id=two_topologies[0].grenml_id,
            )

    def test_fetch_element_with_nonexistent_topo(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be node_a
        starting_element = two_topologies[0].nodes.first()

        with pytest.raises(NoSubstituteElementError):
            dedupe_mixin._fetch_deduplication_target_element(
                starting_element,
                'NA',
                topology_id='NotATopology',
            )

    def test_fetch_wrong_type_of_element(
        self,
        dedupe_mixin,
        two_topologies,
    ):
        # This should be "link"
        starting_element = two_topologies[0].links.first()

        with pytest.raises(NoSubstituteElementError):
            dedupe_mixin._fetch_deduplication_target_element(
                starting_element,
                'L2',
            )
