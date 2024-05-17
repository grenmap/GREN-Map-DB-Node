"""
This file contains tests of import grenml function
"""

import requests
from constants import (
    IMPORT_GRENML_URL,
    EXPORT_GRENML_URL,
    TEST_TOKEN,
    TEST_TOKEN_EXPORT,
    XML_HEADER,
    TEST_FILE_FOLDER, RESTORE_DEFAULT_ID_COLLISION_RULES,
)
from framework import GrenMapTestingFramework
import pytest

TEST_HEADER = {'Authorization': 'Bearer ' + TEST_TOKEN}
TEST_HEADER_EXPORT = XML_HEADER
TEST_HEADER_EXPORT["Authorization"] = "Bearer " + TEST_TOKEN_EXPORT
TEST_FILE = 'test_import_grenml.xml'
TEST_TOPOLOGY = 'test-topology-missing-elements'


class TestImportAPI(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestImportAPI)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        # create default catch-all ruleset
        self.post(
            url=RESTORE_DEFAULT_ID_COLLISION_RULES,
            auth=True,
            expected_status_code=requests.codes.ok
        )

    def test_import_grenml_fail_without_token(self):
        """
        Test the import will fail without token
        """
        self.create_import_token()
        test_grenml_name = TEST_FILE
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            verify=False,
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
        )
        self.poll_import_file()
        assert response.status_code == requests.codes.forbidden

    def test_import_grenml_pass_with_token(self):
        """
        Test the import will pass with proper token
        """
        self.create_import_token()
        test_grenml_name = TEST_FILE
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        self.poll_import_file()
        assert response.status_code == requests.codes.created, \
            'Failed to import grenml'

    def test_import_grenml_fail_with_invalid_token(self):
        """
        Test the import will fail with invalid token
        """
        self.create_import_token()
        test_grenml_name = TEST_FILE
        invalid_token = 'invalidtoken1234'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers={'Authorization': 'Bearer ' + invalid_token},
            verify=False,
        )
        assert response.status_code == requests.codes.forbidden, \
            'Unexpected error code Import should fail without valid token'

    def test_import_grenml_fail_with_no_file(self):
        """
        Test the import will fail with no file
        """
        self.create_import_token()
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.bad_request, \
            'Import should have failed without a file'

    def test_import_grenml_fail_with_corrupt_file(self):
        """
        Test the import will fail with corrupt grenml file
        """
        self.create_import_token()
        test_grenml_name = 'test_corrupt_grenml.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        files = {'file': open(test_file_path, 'rb')}
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files=files,
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.bad_request, \
            'Corrupt file import should have failed'

    def test_import_grenml_fail_with_invalid_file(self):
        """
        Test the import will fail with invalid file format
        Note: No entry will be created on the import page
        for any file type other than xlsx or xml
        """
        self.create_import_token()
        test_invalid_file_name = 'test_invalid_file.txt'
        test_file_path = TEST_FILE_FOLDER + test_invalid_file_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == 406, \
            'Uploading the file should not work'

    def test_import_grenml_fail_with_invalid_pdf_file(self):
        """
        Test the import will fail with invalid file format
        Note: No entry will be created on the import page
        for any file type other than xlsx or xml
        """
        self.create_import_token()
        test_invalid_file_name = 'test_pdf_xml.pdf'
        test_file_path = TEST_FILE_FOLDER + test_invalid_file_name
        test_data = open(test_file_path, encoding="ISO8859-1", mode="r")
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )

        assert response.status_code == 406, \
            'Uploading the file should not work'

    def test_no_address_import_success(self):
        """
        This test uses grenml test file with one institution has no
        address, expected import pass as the address is not a mandatory
        field.
        Note: behaviour changed after story #102 advanced id collision
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_no_address.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'complete' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_no_id_import_fail(self):
        """
        This test uses grenml test file with one institution has no
        id, expected import fail.
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_no_id.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_no_name_import_fail(self):
        """
        This test uses grenml test file with one institution has no
        name, expected import fail.
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_no_name.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_longitude_error_import_fail(self):
        """
        This test uses grenml test file with one institution contain
        incorrect longitude data, expected import fail.
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_longitude_error.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_latitude_error_import_fail(self):
        """
        This test uses grenml test file with one institution contain
        incorrect latitude data, expected import fail.
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_latitude_error.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_altitude_error_import_fail(self):
        """
        This test uses grenml test file with one institution contain
        incorrect altitude data, expected import fail.
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_altitude_error.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_grenml_no_owner_institution_import_fail(self):
        """
        This test uses grenml test file with one institution and no
        grenml owner data, expected import fail.
        """
        self.create_import_token()
        test_grenml_name = 'test_import_grenml_no_owner.xml'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers=TEST_HEADER,
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_link_only_has_one_node_import_fail(self):
        """
        This test uses grenml test file with link contain only one node,
        expected import fail.
        """
        test_grenml_name = 'test_import_grenml_link_has_one_node.xml'
        response = self.import_xml_file(test_grenml_name)
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'

        import_file = self.poll_then_delete()
        assert 'Error' in import_file['import_message'], \
            'Did not get expected error response.'

    def test_import_into_root_topology_without_name_change_during_import(self):
        """
        This test import file into the root topology
        without changing the topology name.
        """
        test_grenml_name = 'test_full_network_data.xml'
        self.import_xml_file(test_grenml_name)
        self.create_grenml_export_token()

        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )

        expected_topology_name = 'Topology Test 2'
        assert expected_topology_name in xml_data, \
            'Fail to find the topology name in the xml data'

    def test_import_into_root_topology_the_same_xml_file_multiple_times(self):
        """
        This test imports a xml topology file multiple times
        into the root topology with same topology name.
        """
        test_grenml_name = TEST_FILE
        # import 1
        self.import_xml_file(test_grenml_name)
        self.create_grenml_export_token()

        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )
        expected_topology_name = 'topology-1'
        assert expected_topology_name in xml_data, \
            'Fail to find the topology names in the xml data'
        # get parent topology PK from DB
        topology_details = self.get_topology_details()
        parent_topology_pk = topology_details[0]['pk']
        # import 2
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=test_grenml_name,
            topology_id=parent_topology_pk,
        )
        # export token created earlier is used
        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )

        # 2nd import should not create new network elements
        topology_count = xml_data.count(expected_topology_name)
        assert topology_count == 1, \
            'the count of topology names in the xml data does not match'
        link_count = xml_data.count('Link 6')
        assert link_count == 1, 'multiple uploads creates multiple DB values'

    def test_import_as_child_with_name_change_into_root_topology(self):
        """
        This test imports a new topology as a child to the root topology
        with name change provided during import.
        This name change should not work as the xml will contain
        a topology name and that is used and the new name is ignored

        Note: this uses the topology name provided in the xml file and
        ignores the provided new name
        """
        test_grenml_name = 'test_full_network_data.xml'
        self.import_xml_file(test_grenml_name)
        self.create_grenml_export_token()

        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )

        expected_topology_name_list = [
            'Topology Test 2',       # topology name from the test file
        ]
        for topology_name in expected_topology_name_list:
            assert topology_name in xml_data, \
                'Fail to find the root topology name in the xml data'

    def test_import_as_child_topology_without_name_change_during_import(self):
        """
        This test imports a new topology as a child to the root topology
        without name change.
        """
        root_grenml_name = 'test_full_network_data.xml'
        # root topology import
        self.import_xml_file(root_grenml_name)
        # get parent topology PK
        topology_details = self.get_topology_details()
        parent_topology_pk = topology_details[0]['pk']
        # child topology import
        child_grenml_name = TEST_FILE
        self.import_xml_file_with_import_type_and_topology_name(
            child_grenml_name,
            topology_id=parent_topology_pk
        )

        self.create_grenml_export_token()
        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )
        expected_topology_name_list = [
            'Topology Test 2',
            'topology-1',
        ]
        for topology_name in expected_topology_name_list:
            assert topology_name in xml_data, \
                'Fail to find the topology name in the xml data'

    def test_import_into_topology_xml_file_with_multiple_topologies(self):
        """
        This test imports a topology xml file with multiple topologies
        into the root topology without name change.
        """
        test_grenml_name = 'test_import_grenml_multiple_topologies.xml'
        self.import_xml_file(test_grenml_name)
        self.create_grenml_export_token()

        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )

        expected_topology_name_list = [
            'Root Topology',
            'Test topology 1',
            'Test topology 2',
        ]
        for topology_name in expected_topology_name_list:
            assert topology_name in xml_data, \
                'Fail to find the root topology name in the xml data'

    def test_topology_owner_should_not_disappear_after_multiple_import(self):
        """
        scenario:
            - import parent topology with an owner institution
            - import a child topology with an institution having same
            grenmlId as the owner institution of parent
            - import child again
            - verify if parent topology is not missing owner institution
        """
        test_grenml_name = 'test_import_missing_elements_after_import.xml'
        self.import_xml_file(test_grenml_name)
        top_level_topology = self.get_topology_details(TEST_TOPOLOGY)[0]
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        value_after_first_import = self.get_topology_details(
            top_level_topology['pk']
        )
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        value_after_second_import = self.get_topology_details(
            top_level_topology['pk']
        )
        assert value_after_first_import == value_after_second_import

    def test_node_should_not_disappear_after_multiple_import(self):
        """
        scenario:
            - import parent topology with an owner institution & a node
            - import a child topology with a node having same grenmlId
            as the node in parent
            - import child again
            - verify if node in parent is not missing and
            their relationships are not missing
        """

        test_grenml_name = 'test_import_missing_elements_after_import.xml'
        self.import_xml_file(test_grenml_name)
        top_level_topology = self.get_topology_details(TEST_TOPOLOGY)[0]
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        value_after_first_import = self.get_node_details('node-4')
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        value_after_second_import = self.get_node_details('node-4')
        assert len(value_after_first_import) == len(value_after_second_import)
        self._compare_except_primary_keys(
            value_after_first_import,
            value_after_second_import
        )

    def test_link_should_not_disappear_after_multiple_import(self):
        """
        scenario:
            - import parent topology with an owner institution and 2
            nodes and a link
            - import a child topology with a link having same grenmlId
            as the link in parent
            - import child again
            - verify if link in parent is not missing and
            their relationships are not missing
        """
        test_grenml_name = 'test_import_missing_elements_after_import.xml'
        self.import_xml_file(test_grenml_name)
        top_level_topology = self.get_topology_details(TEST_TOPOLOGY)[0]
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        value_after_first_import = self.get_link_details('link-4')
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        value_after_second_import = self.get_link_details('link-4')
        assert len(value_after_first_import) == len(value_after_second_import)
        self._compare_except_primary_keys(
            value_after_first_import,
            value_after_second_import
        )

    def test_institution_retains_its_relationships_after_multiple_imports(self):
        """
        When multiple topologies are imported the institutions that own
        elements from existing topology should retain its
        relationships even after multiple import from different
        topologies
         scenario:
            - import parent topology with an owner institution
            - import a child topology with an institution having same
            grenmlId as the owner institution of parent
            - import child again
            - verify if all the relationships of the owner institution
            is maintained
        """
        test_grenml_name = 'test_import_missing_elements_after_import.xml'
        self.import_xml_file(test_grenml_name)
        top_level_topology = self.get_topology_details(TEST_TOPOLOGY)[0]
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        inst_data_first_import = self.get_institution_details('inst-1')
        owned_topologies_list_1 = inst_data_first_import[0]['owned_topologies']
        owned_elements_list_1 = inst_data_first_import[0]['owned_elements']

        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=TEST_FILE,
            topology_id=top_level_topology['pk']
        )
        inst_data_second_import = self.get_institution_details('inst-1')
        owned_topologies_list_2 = inst_data_second_import[0]['owned_topologies']
        owned_elements_list_2 = inst_data_second_import[0]['owned_elements']
        assert len(owned_topologies_list_1) == \
            len(owned_topologies_list_2) == 2, \
            'This institution should own 2 topologies'
        assert len(owned_elements_list_1) == \
            len(owned_elements_list_2) == 15, \
            'This institution should own 15 elements'

    def _compare_except_primary_keys(self, list_a, list_b):
        """
        When comparing before-and-after lists of Topologies,
        where a recent import of recently exported data
        is meant to resemble its prior self, the primary keys
        will of course differ as they get auto-incremented.
        Remove all integers and replace with 0.  This may
        obliterate any non-primary-key integers, but it may
        suffice for simple basic testing regardless.
        If it is desired to confirm particular items, best to
        check them explicitly.
        """
        def _sort_func(item):
            """
            Returns a key to sort lists where list items may be
            dictionaries of common models, but also may not be.
            Prefers 'grenml_id' key, then 'name' key.
            (For uncommon models without those, it returns 0,
            so order may be nondeterministic.)
            """
            if not item:
                return item
            if isinstance(item, dict):
                if item.get('grenml_id', False):
                    return item['grenml_id']
                elif item.get('name', False):
                    return item['name']
                else:
                    return 0

        def _sanitize_for_easy_simple_comparison(input):
            """
            Recursive function to identify integers in lists and
            dictionaries and replace them with zeroes.  Also
            sorts lists for easier comparison, in case they are
            randomly out of order.
            """
            # Lists (sets)
            if isinstance(input, list):
                new_list = []
                for item in input:
                    if isinstance(item, int):
                        new_list.append(0)
                    elif isinstance(item, dict) or isinstance(item, list):
                        new_list.append(_sanitize_for_easy_simple_comparison(item))
                    else:
                        new_list.append(item)
                return sorted(new_list, key=_sort_func)
            # Dictionaries
            elif isinstance(input, dict):
                new_dict = {}
                for key, val in input.items():
                    if isinstance(val, int):
                        new_dict[key] = 0
                    elif isinstance(val, dict) or isinstance(val, list):
                        new_dict[key] = _sanitize_for_easy_simple_comparison(val)
                    else:
                        new_dict[key] = val
                return new_dict
            # Single items
            else:
                if isinstance(input, int):
                    return 0
                else:
                    return input

        sanitized_list_a = _sanitize_for_easy_simple_comparison(list_a)
        sanitized_list_b = _sanitize_for_easy_simple_comparison(list_b)
        assert sanitized_list_b == sanitized_list_a, \
            str(sanitized_list_a) + '\n' + str(sanitized_list_b)
