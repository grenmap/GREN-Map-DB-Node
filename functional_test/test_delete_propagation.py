"""
This file contains tests of propagating deletion of
network elements up the hierarchy
"""
import time

import pytest
import requests
from constants import EXPORT_GRENML_URL, TEST_TOKEN, XML_HEADER, \
    TEST_TOKEN_EXPORT, RESTORE_DEFAULT_ID_COLLISION_RULES
from framework import GrenMapTestingFramework


TEST_HEADER = {'Authorization': 'Bearer ' + TEST_TOKEN}
TEST_HEADER_EXPORT = XML_HEADER
TEST_HEADER_EXPORT["Authorization"] = "Bearer " + TEST_TOKEN_EXPORT
INSTITUTION = 'institution'
NODE = 'node'
LINK = 'link'


class TestDeletePropagation(GrenMapTestingFramework):
    """
    This suite of tests verifies the ability to propagate the
    deletion of elements to the destination which polls the source.
    these tests are set up as follows:
        1. # import full data
        2. # assert if a node is present
        3. # import data with deleted node
        4. # assert if node is deleted
    Note: import is used instead of polling as the polling method
    uses the import method to write data to the DB
    """

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestDeletePropagation)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.create_grenml_export_token()
        # create default catch-all ruleset
        self.post(
            url=RESTORE_DEFAULT_ID_COLLISION_RULES,
            auth=True,
            expected_status_code=requests.codes.ok
        )
        self.import_ruleset('test_custom_rulesets.json')

    def test_delete_propagation_node_deletion(self):
        """
        This tests verifies the propagation of deleted node
        assertion is done in the helper method
        """
        missing_node_grenml = 'test_delete_propagation_missing_node_data.xml'
        deleted_link = 'Router3'
        self._verify_missing_elements(
            topology_with_missing_element=missing_node_grenml,
            deleted_element=deleted_link,
        )

    def test_delete_propagation_link_deletion(self):
        """
        This tests verifies the propagation of deleted link
        assertion is done in the helper method
        """
        missing_link_grenml = 'test_delete_propagation_missing_link_data.xml'
        deleted_link = 'link:3'
        self._verify_missing_elements(
            topology_with_missing_element=missing_link_grenml,
            deleted_element=deleted_link,
        )

    def test_delete_propagation_institution_deletion(self):
        """
        This tests verifies the propagation of deleted institution
        assertion is done in the helper method
        """
        missing_institution_grenml = 'test_delete_propagation_missing_institution_data.xml'
        deleted_institution = 'Test Institution 2'
        self._verify_missing_elements(
            topology_with_missing_element=missing_institution_grenml,
            deleted_element=deleted_institution,
        )

    def test_delete_propagation_property_deletion(self):
        """
        This tests verifies the propagation of deleted property
        assertion is done in the helper method
        """
        missing_topology_grenml = 'test_delete_propagation_missing_property_data.xml'
        deleted_property = 'test property 2'
        self._verify_missing_elements(
            topology_with_missing_element=missing_topology_grenml,
            deleted_element=deleted_property,
        )

    def test_delete_propagation_topology_deletion(self):
        """
        This tests verifies deletion of topology is not propagated
        since story #102 topology deletion is not propagated
        """
        initial_import_topology = 'test_delete_propagation_data_with_two_topologies.xml'
        missing_topology_grenml = 'test_delete_propagation_full_data.xml'
        deleted_topology = 'child topology'
        initial_count, final_count = self._verify_missing_elements_multi_topology(
            initial_import_topology=initial_import_topology,
            topology_with_missing_element=missing_topology_grenml,
            deleted_element=deleted_topology,
        )
        assert final_count == initial_count, \
            f'the final count of {deleted_topology} names in ' \
            f'the xml data must be equal to the initial count'

    def test_delete_propagation_altitude_deletion(self):
        """
        This tests verifies the propagation of deleted altitude in node
        this is node update propagation
        assertion is done in the helper method
        """
        file_with_missing_data = \
            'test_delete_propagation_missing_altitude_and_address_data.xml'
        deleted_altitude = '<grenml:alt>4215</grenml:alt>'
        self._verify_missing_elements(
            topology_with_missing_element=file_with_missing_data,
            deleted_element=deleted_altitude,
        )

    def test_delete_propagation_address_update(self):
        """
        This tests verifies the propagation of updated address in node
        this is node update propagation
        assertion is done in the helper method
        """
        file_with_missing_data = \
            'test_delete_propagation_missing_altitude_and_address_data.xml'
        old_address = 'test address to be deleted Canada'
        self._verify_missing_elements(
            topology_with_missing_element=file_with_missing_data,
            deleted_element=old_address,
        )

    def test_delete_propagation_remove_node_from_parent_topology(self):
        """
        This test verifies the case that when one node is a part of
        multiple topologies, and it is removed from one topology the
        propagation must be successful
        """
        file_with_missing_data = 'test_delete_propagation_data_with_two_topologies.xml'
        node_name = 'child-node-2'
        initial_count, final_count = self._verify_missing_elements_multi_topology(
            topology_with_missing_element=file_with_missing_data,
            deleted_element=node_name,
        )
        assert final_count < initial_count, \
            f'the final count of {node_name} names in the ' \
            f'xml data is not less than original import count'

    def test_delete_propagation_remove_link_from_parent_topology(self):
        """
        This test verifies the case that when one link is a part of
        multiple topologies, and it is removed from one topology the
        propagation must be successful
        """
        file_with_missing_data = \
            'test_delete_propagation_data_with_two_topologies.xml'
        link_name = 'child-topo-link'
        initial_count, final_count = self._verify_missing_elements_multi_topology(
            topology_with_missing_element=file_with_missing_data,
            deleted_element=link_name,
        )
        assert final_count < initial_count, \
            f'the final count of {link_name} names in the ' \
            f'xml data is not less than original import count'

    def test_delete_propagation_remove_institution_from_parent_topology(self):
        """
        This test verifies the case that when one institution is a
        part of multiple topologies, and it is removed from one
        topology the propagation must be successful
        """
        file_with_missing_data = \
            'test_delete_propagation_data_with_two_topologies.xml'
        institution_name = 'Test-Institution-3'
        initial_count, final_count = self._verify_missing_elements_multi_topology(
            topology_with_missing_element=file_with_missing_data,
            deleted_element=institution_name,
        )
        assert final_count < initial_count, \
            f'the final count of {institution_name} names in the ' \
            f'xml data is not less than original import count'

    def _verify_missing_elements(
            self,
            topology_with_missing_element,
            deleted_element,
            initial_import_topology='test_delete_propagation_full_data.xml',
    ):
        """
        This helper method gets the following inputs:
            - initial_import_topology: initial topology with full data
            - topology_with_missing_element: topology that has one
            or more elements deleted
            - deleted_element: missing element to be verified
        and performs assertions on the extracted xml data.
        """
        # first import
        self.import_xml_file(initial_import_topology)
        time.sleep(2)

        # second import (import topology with the missing element)
        self.import_xml_file_with_import_type_and_topology_name(
            topology_with_missing_element,
        )

        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )

        assert deleted_element not in xml_data, \
            f'{deleted_element} should not be in the exported grenml data'

    def _verify_missing_elements_multi_topology(
            self,
            topology_with_missing_element,
            deleted_element,
            initial_import_topology='test_delete_propagation_node_in_multiple_topologies.xml',
    ):
        """
        This helper method gets the following inputs:
            - initial_import_topology: initial topology with full data
            - topology_with_missing_element: topology that has one
            or more elements deleted
            - deleted_element: missing element to be verified
        and performs assertions on the extracted xml data.
        """
        # first import
        self.import_xml_file(initial_import_topology)
        # this time delay is added to wait for the rules to finish
        # applying after import
        time.sleep(1)
        # find initial count
        xml_data_1 = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )
        initial_count = xml_data_1.count(deleted_element)

        topology_details = self.get_topology_details('test-topology-1')

        # 2nd import (import topology with the missing element)
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=topology_with_missing_element,
            topology_id=topology_details[0]['pk'],
        )
        # delay is added to wait for the rules to finish after import
        time.sleep(1)
        # find count after propagation
        xml_data_2 = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )
        # count number of occurrences of the element after deletion
        final_count = xml_data_2.count(deleted_element)
        return initial_count, final_count
