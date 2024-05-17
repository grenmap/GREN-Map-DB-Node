"""
This file contains tests of using rule action
"""
import json
import time

from constants import RULE_TEST_API_URL, RULESET_TEST_API_URL, \
    ACTION_TYPE_LIST, MATCH_TYPE_LIST, ACTION_API_INFO_RUL, \
    TEST_TOKEN_EXPORT, RESTORE_DEFAULT_ID_COLLISION_RULES
from constants import ACTION_API_URL, MATCH_CRITERIA_API_URL, \
    MATCH_INFO_API_URL, IMPORT_RULESETS_API_URL, JSON_HEADER
from constants import IMPORT_GRENML_URL_TEST, EXPORT_GRENML_URL, \
    XML_HEADER, EXPORT_RULESETS_API_URL
from framework import GrenMapTestingFramework
import pytest
import requests

TEST_HEADER = XML_HEADER
TEST_HEADER["Authorization"] = "Bearer " + TEST_TOKEN_EXPORT
TEST_FILE_FOLDER = '/home/grenmap_functional_test/test_files/'
RULESETS = 'rulesets'
RULES = 'rules'
NAME = 'name'
ACTIONS = 'actions'
ACTION_TYPE = 'action_type'
ACTION_INFO_SET = 'actioninfo_set'
MATCH_CRITERIA = 'match_criteria'
MATCH_TYPE = 'match_type'
MATCH_INFO_SET = 'matchinfo_set'
RULESET_WITH_TOPOLOGY_ID = 'test_ruleset_with_topoology_ID.json'
RULESET_IMPORT_FILE = 'test_ruleset_grenml_with_3_topologies.xml'


class TestRuleAction(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestRuleAction)

    @pytest.fixture(autouse=True)
    def before_each(self):
        # Setup testing database
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.create_grenml_export_token()

        # Clean All rule before each test
        existing_rule_list = self.get(url=RULE_TEST_API_URL, auth=True)
        if len(existing_rule_list) > 0:
            for rule in existing_rule_list:
                self.delete(
                    url=RULE_TEST_API_URL + str(rule['id']) + '/',
                    auth=True
                )

        # create default catch-all ruleset
        self.post(
            url=RESTORE_DEFAULT_ID_COLLISION_RULES,
            auth=True,
            expected_status_code=requests.codes.ok
        )

    def test_remove_node_with_apply_all_rule_sets(self):
        """
        Create new delete link rule, expect delete one matched link
        """

        # Create delete node rule
        test_match_node_id = 'd268e2c2-e8a1-4282-8c65-27f404f5a13d'
        delete_node_action_id = self._get_delete_node_action_id()
        match_node_id = self._get_match_node_id()
        self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_node_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )

        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_node_id = 'd268e2c2-e8a1-4282-8c65-27f404f5a13d'
        assert test_node_id not in export_xml_data, \
            f'Node 2 should be removed. Export xml is {export_xml_data}'

    def test_remove_link_with_apply_all_rule_sets(self):
        """
        Create new delete link rule, expect delete one matched link
        """
        # Create delete link rule
        test_match_link_id = '43743718-3687-4064-9be8-eee2f49d7186'
        delete_link_action_id = self._get_delete_link_action_id()
        match_link_id = self._get_match_link_id()
        self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_link_action_id,
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_node_1_id = 'a0038057-d2e8-4222-b288-4c1c1687de7d'
        test_node_2_id = '5eabd741-4f97-40cf-9276-629b6af97541'
        test_link_id = '43743718-3687-4064-9be8-eee2f49d7186'
        assert test_link_id not in export_xml_data, \
            f'Link should be removed. Export xml is {export_xml_data}'
        assert test_node_1_id in export_xml_data, \
            f'Node 1-1 should not be removed. Export xml is {export_xml_data}'
        assert test_node_2_id in export_xml_data, \
            f'Node 1-2 should not be removed. Export xml is {export_xml_data}'

    def test_remove_institution_with_apply_all_rule_sets(self):
        """
        Create new delete institution rule, and expect only
        remove one match institution.
        """
        # Create delete node rule
        test_match_institution_id = 'ccc832d8-0039-484a-a981-94964a07d5d0'
        delete_institution_action_id = self._get_delete_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_institution_action_id,
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )

        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_institution_id = 'ccc832d8-0039-484a-a981-94964a07d5d0'
        assert test_institution_id not in export_xml_data, \
            f'Institution should be removed. Export xml is {export_xml_data}'

    def test_delete_link_rule_remove_one_link(self):
        """
        Create new delete link rule, expect delete one matched link
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete link rule
        test_match_link_id = '43743718-3687-4064-9be8-eee2f49d7186'
        delete_link_action_id = self._get_delete_link_action_id()
        match_link_id = self._get_match_link_id()
        delete_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_link_action_id,
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_link_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_node_1_id = 'a0038057-d2e8-4222-b288-4c1c1687de7d'
        test_node_2_id = '5eabd741-4f97-40cf-9276-629b6af97541'
        test_link_id = '43743718-3687-4064-9be8-eee2f49d7186'
        assert test_link_id not in export_xml_data, \
            f'Link should be removed. Export xml is {export_xml_data}'
        assert test_node_1_id in export_xml_data, \
            f'Node 1-1 should not be removed. Export xml is {export_xml_data}'
        assert test_node_2_id in export_xml_data, \
            f'Node 1-2 should not be removed. Export xml is {export_xml_data}'

    def test_delete_link_rule_does_not_find_match_link(self):
        """
        Create new delete link rule, expect no link is removed
        if link id does not match
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete link rule
        test_match_link_id = 'test-not-match-link-id'
        delete_link_action_id = self._get_delete_link_action_id()
        match_link_id = self._get_match_link_id()
        delete_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_link_action_id,
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_link_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_link_list = [
            '43743718-3687-4064-9be8-eee2f49d7186',
            'f7d7dd5e-7fc3-4e28-9595-0565ce78506c'
        ]
        for link_id in test_link_list:
            assert link_id in export_xml_data, \
                f'Link {link_id} should not be removed. ' \
                f'Export xml is {export_xml_data}'
        expected_node_list = [
            'a0038057-d2e8-4222-b288-4c1c1687de7d',
            '5eabd741-4f97-40cf-9276-629b6af97541',
            'd268e2c2-e8a1-4282-8c65-27f404f5a13d',
            '2275d34e-d5b1-4d58-9f2b-af8a5c909255',
            '81108b0f-abe3-472b-bb96-60a65bd2a523'
        ]
        for node_id in expected_node_list:
            assert node_id in export_xml_data, \
                f'Node {node_id} should not be removed. ' \
                f'Export xml is {export_xml_data}'

    def test_delete_node_rule_remove_only_one_node(self):
        """
        Create new delete node rule, and expect only remove
        one match node.
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_node_id = 'd268e2c2-e8a1-4282-8c65-27f404f5a13d'
        delete_node_action_id = self._get_delete_node_action_id()
        match_node_id = self._get_match_node_id()
        delete_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_node_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_node_id = 'd268e2c2-e8a1-4282-8c65-27f404f5a13d'
        assert test_node_id not in export_xml_data, \
            f'Node 2 should be removed. Export xml is {export_xml_data}'

    def test_delete_node_rule_does_not_find_match_node(self):
        """
        Create new delete node rule, expect no node is removed
        if link id does not match
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_node_id = 'test-not-match-node-id'
        delete_node_action_id = self._get_delete_node_action_id()
        match_node_id = self._get_match_node_id()
        delete_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_node_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        expected_node_list = [
            'a0038057-d2e8-4222-b288-4c1c1687de7d',
            '5eabd741-4f97-40cf-9276-629b6af97541',
            'd268e2c2-e8a1-4282-8c65-27f404f5a13d',
            '2275d34e-d5b1-4d58-9f2b-af8a5c909255',
            '81108b0f-abe3-472b-bb96-60a65bd2a523'
        ]
        for node_id in expected_node_list:
            assert node_id in export_xml_data, \
                f'Node {node_id} should not be removed. Export xml is {export_xml_data}'

    def test_delete_node_rule_remove_one_node_and_one_cascaded_link(self):
        """
        Create new delete node rule, and expect remove one node,
        one cascaded link.
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_node_id = '2275d34e-d5b1-4d58-9f2b-af8a5c909255'
        delete_node_action_id = self._get_delete_node_action_id()
        match_node_id = self._get_match_node_id()
        delete_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_node_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_node_id = '2275d34e-d5b1-4d58-9f2b-af8a5c909255'
        test_not_removed_node_id = '81108b0f-abe3-472b-bb96-60a65bd2a523'
        test_cascade_link_id = 'f7d7dd5e-7fc3-4e28-9595-0565ce78506c'
        assert test_node_id not in export_xml_data, \
            f'Node 3-1 should be removed. Export xml is {export_xml_data}'
        assert test_cascade_link_id not in export_xml_data, \
            f'Link 2 should be removed. Export xml is {export_xml_data}'
        assert test_not_removed_node_id in export_xml_data, \
            f'Node 3-2 should be removed. Export xml is {export_xml_data}'

    def test_delete_node_rule_remove_two_nodes_and_one_cascaded_link(self):
        """
        Create two delete node rule, and expect remove two nodes,
        one cascaded link.
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create first delete node rule
        test_match_node_id = '2275d34e-d5b1-4d58-9f2b-af8a5c909255'
        delete_node_action_id = self._get_delete_node_action_id()
        match_node_id = self._get_match_node_id()
        delete_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_1',
            action_type_id=delete_node_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_node_rule_id) + '/apply/',
            auth=True
        )

        # Create second delete node rule
        test_match_node_id = '81108b0f-abe3-472b-bb96-60a65bd2a523'
        delete_node_action_id = self._get_delete_node_action_id()
        match_node_id = self._get_match_node_id()
        delete_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_2',
            action_type_id=delete_node_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_first_node_id = '2275d34e-d5b1-4d58-9f2b-af8a5c909255'
        test_second_node_id = '81108b0f-abe3-472b-bb96-60a65bd2a523'
        test_cascade_link_id = 'f7d7dd5e-7fc3-4e28-9595-0565ce78506c'
        assert test_first_node_id not in export_xml_data, \
            f'Node 3-1 should be removed. Export xml is {export_xml_data}'
        assert test_second_node_id not in export_xml_data, \
            f'Node 3-2 should be removed. Export xml is {export_xml_data}'
        assert test_cascade_link_id not in export_xml_data, \
            f'Link 2 should be removed. Export xml is {export_xml_data}'

    def test_fail_apply_rule_mix_match_node_and_action_delete_link_action(self):
        """
        Test the rule using mix match, expect the rule should fail and
        should not remove any data
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete rule
        test_match_id = 'a0038057-d2e8-4222-b288-4c1c1687de7d'
        delete_link_action_id = self._get_delete_link_action_id()
        match_node_id = self._get_match_node_id()
        delete_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_link_action_id,
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_id}
        )
        # Call rule action and expect the rule will not be applied
        self.get(
            url=RULE_TEST_API_URL + str(delete_rule_id) + '/apply/',
            auth=True,
            expected_status_code=requests.codes.internal_server_error
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )
        test_link_list = [
            '43743718-3687-4064-9be8-eee2f49d7186',
            'f7d7dd5e-7fc3-4e28-9595-0565ce78506c'
        ]
        for link_id in test_link_list:
            assert link_id in export_xml_data, \
                f'Link {link_id} should not be removed. Export xml is {export_xml_data}'
        expected_node_list = [
            'a0038057-d2e8-4222-b288-4c1c1687de7d',
            '5eabd741-4f97-40cf-9276-629b6af97541',
            'd268e2c2-e8a1-4282-8c65-27f404f5a13d',
            '2275d34e-d5b1-4d58-9f2b-af8a5c909255',
            '81108b0f-abe3-472b-bb96-60a65bd2a523'
        ]
        for node_id in expected_node_list:
            assert node_id in export_xml_data, \
                f'Node {node_id} should not be removed. Export xml is {export_xml_data}'

    def test_fail_apply_rule_mix_match_link_and_delete_node_action(self):
        """
        Test the rule using mix match, expect the rule should fail and
        should not remove any data
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create rule
        test_match_id = '43743718-3687-4064-9be8-eee2f49d7186'
        delete_node_action_id = self._get_delete_node_action_id()
        match_link_id = self._get_match_link_id()
        delete_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_node_action_id,
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_id}
        )
        # Call rule action and expect the rule will not be applied
        self.get(
            url=RULE_TEST_API_URL + str(delete_rule_id) + '/apply/',
            auth=True,
            expected_status_code=requests.codes.internal_server_error
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )
        test_link_list = [
            '43743718-3687-4064-9be8-eee2f49d7186',
            'f7d7dd5e-7fc3-4e28-9595-0565ce78506c'
        ]
        for link_id in test_link_list:
            assert link_id in export_xml_data, \
                f'Link {link_id} should not be removed. Export xml is {export_xml_data}'
        expected_node_list = [
            'a0038057-d2e8-4222-b288-4c1c1687de7d',
            '5eabd741-4f97-40cf-9276-629b6af97541',
            'd268e2c2-e8a1-4282-8c65-27f404f5a13d',
            '2275d34e-d5b1-4d58-9f2b-af8a5c909255',
            '81108b0f-abe3-472b-bb96-60a65bd2a523'
        ]
        for node_id in expected_node_list:
            assert node_id in export_xml_data, \
                f'Node {node_id} should not be removed. Export xml is {export_xml_data}'

    def test_delete_institution_rule_does_not_find_match_institution(self):
        """
        Create new delete institution rule, expect no institution
        is removed if the id does not match
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_institution_id = 'test-not-match-institution-id'
        delete_institution_action_id = self._get_delete_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        delete_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_institution_action_id,
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=XML_HEADER
        )

        expected_institution_list = [
            '6fe21b72-d4fb-49d4-be1d-d5a8d4a80385',
            '4372ceeb-6b75-4e81-9a98-2fa3e1ecbe8b',
            'cacf4f3a-fbf3-4afd-bdeb-22e8189ad253',
            'ccc832d8-0039-484a-a981-94964a07d5d0'
        ]
        for institution_id in expected_institution_list:
            assert institution_id in export_xml_data, \
                f'Institution {institution_id} should not be removed.'

    def test_delete_institution_rule_remove_only_one_institution(self):
        """
        Create new delete institution rule, and expect only
        remove one match institution.
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_institution_id = 'ccc832d8-0039-484a-a981-94964a07d5d0'
        delete_institution_action_id = self._get_delete_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        delete_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_institution_action_id,
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_institution_id = 'ccc832d8-0039-484a-a981-94964a07d5d0'
        assert test_institution_id not in export_xml_data, \
            f'Institution should be removed. Export xml is {export_xml_data}'

    def test_delete_institution_rule_remove_one_institution_owner_of_node(self):
        """
        Create new delete institution rule, and expect only remove one
        match institution and does not remove the node
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_institution_id = '4372ceeb-6b75-4e81-9a98-2fa3e1ecbe8b'
        delete_institution_action_id = self._get_delete_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        delete_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_institution_action_id,
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_institution_id = '4372ceeb-6b75-4e81-9a98-2fa3e1ecbe8b'
        assert test_institution_id not in export_xml_data, \
            f'Institution should be removed. Export xml is {export_xml_data}'
        test_node_id = 'd268e2c2-e8a1-4282-8c65-27f404f5a13d'
        assert test_node_id in export_xml_data, \
            f'Node should not be removed. Export xml is {export_xml_data}'

    def test_delete_institution_rule_remove_one_institution_owner_of_multiple_nodes_links(self):
        """
        Create new delete institution rule, and expect only remove
        one match institution and does not remove any connected
        links or nodes
        """
        # Import test data
        test_grenml_name = 'test_rule_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create delete node rule
        test_match_institution_id = '6fe21b72-d4fb-49d4-be1d-d5a8d4a80385'
        delete_institution_action_id = self._get_delete_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        delete_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=delete_institution_action_id,
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(delete_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        test_link_list = [
            '43743718-3687-4064-9be8-eee2f49d7186',
            'f7d7dd5e-7fc3-4e28-9595-0565ce78506c'
        ]
        for link_id in test_link_list:
            assert link_id in export_xml_data, \
                f'Link {link_id} should not be removed. Export xml is {export_xml_data}'
        expected_node_list = [
            'a0038057-d2e8-4222-b288-4c1c1687de7d',
            '5eabd741-4f97-40cf-9276-629b6af97541',
            'd268e2c2-e8a1-4282-8c65-27f404f5a13d',
            '2275d34e-d5b1-4d58-9f2b-af8a5c909255',
            '81108b0f-abe3-472b-bb96-60a65bd2a523'
        ]
        for node_id in expected_node_list:
            assert node_id in export_xml_data, \
                f'Node {node_id} should not be removed. Export xml is {export_xml_data}'

    def test_import_rule_sets_and_verify_rulesets(self):
        """
        Test import ruleset functionality and check if the
        rulesets are successfully in the DB
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as test_data_string:
            test_data_object = test_data_string.read()
        # post ruleset to DB
        response = requests.post(
            url=IMPORT_RULESETS_API_URL,
            data=test_data_object,
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'POST not successful to via API'
        expected_value = 'New test ruleset'

        # Get the list of rulesets from DB and verify if the
        # data is populated correctly in the DB
        json_data = self.get(
            url=RULESET_TEST_API_URL,
            headers=JSON_HEADER,
            auth=True,
        )

        rule_set_data = [
            ruleset for ruleset in json_data if ruleset['name'] == expected_value
        ]
        assert expected_value in rule_set_data[0][NAME]

    def test_import_rule_sets_and_verify_rules(self):
        """
        Test if rulesets can be imported from a JSON file and the
        rules are populated correctly in DB
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as test_data_string:
            test_data_object = test_data_string.read()
        # post ruleset to DB
        response = requests.post(
            url=IMPORT_RULESETS_API_URL,
            data=test_data_object,
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'POST not successful to via API'
        expected_value = 'Delete rule'

        # Get the rules list from DB and verify if
        # the data is populated correctly in the DB
        json_data = self.get(
            url=RULE_TEST_API_URL,
            headers=JSON_HEADER,
            auth=True,
        )

        rule_set_data = [
            ruleset for ruleset in json_data if ruleset['name'] == expected_value
        ]
        assert expected_value in rule_set_data[0][NAME]

    def test_export_rule_sets(self):
        """
        Test if rule sets can be exported to a JSON file
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as test_data_string:
            test_data_object = test_data_string.read()

        # post ruleset to DB
        response = requests.post(
            url=IMPORT_RULESETS_API_URL,
            data=test_data_object,
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'POST not successful to via API'

        # expected_value = json.loads(test_data_string.read())
        expected_value = 'New test ruleset'

        # Get the list of rulesets from DB
        rulesets_json_data = self.get(
            url=RULESET_TEST_API_URL,
            headers=JSON_HEADER,
            auth=True,
        )
        rule_set_data = [
            ruleset for ruleset in rulesets_json_data if ruleset['name'] == expected_value
        ]
        rule_set_id = rule_set_data[0]['id']

        # export the ruleset with the ID from the previous step
        json_data = self.get(
            url=EXPORT_RULESETS_API_URL + '?ids=' + str(rule_set_id),
            headers=JSON_HEADER,
            auth=True,
        )
        assert expected_value == json_data[0]['name']

    def test_replace_institution_rule_action(self):
        """
        Test Replace single institution replace and remove by
        another institution
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create replace rule
        test_match_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        test_replace_institution_id = 'a9af48fd-2332-462d-9584-0f83abbf64de'
        replace_institution_action_id = self._get_replace_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        replace_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=replace_institution_action_id,
            action_info_data={"key": "ID", "value": test_replace_institution_id},
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_institution_id not in export_xml_data, \
            f'Match institution should be removed. Export xml is {export_xml_data}'
        assert test_replace_institution_id in export_xml_data, \
            f'Replacement institution should not be remove. Export xml is {export_xml_data}'

        affected_node_id = '665a5cf4-87f3-4334-bd9f-9eb28ac89a8b'
        assert affected_node_id in export_xml_data, \
            f'Node should not be removed. Export xml is {export_xml_data}'

    def test_replace_institution_of_multiple_nodes_and_link_rule_action(self):
        """
        Test Replace single institution replace rule action, and
        make sure all the elements' owner are updated
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create replace rule
        test_match_institution_id = 'a9af48fd-2332-462d-9584-0f83abbf64de'
        test_replace_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        replace_institution_action_id = self._get_replace_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        replace_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=replace_institution_action_id,
            action_info_data={"key": "ID", "value": test_replace_institution_id},
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_institution_id not in export_xml_data, \
            'Match institution should be removed.'
        assert test_replace_institution_id in export_xml_data, \
            'Replacement institution should not be remove.'

        count_owners = export_xml_data.count(test_replace_institution_id)
        assert count_owners == 5, \
            'count discrepancy after institution replace rule action'

    def test_replace_institution_rule_action_fail_find_replacement(self):
        """
        Test replace action fail if unable to find the
        replacement institution
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create replace rule
        test_match_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        test_replace_institution_id = 'test-replacement-id'
        replace_institution_action_id = self._get_replace_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        replace_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=replace_institution_action_id,
            action_info_data={"key": "ID", "value": test_replace_institution_id},
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(replace_institution_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        message = response['actions'][0]['message']
        assert "Could not find the substitute Institution." in message, \
            "Unexpected error message when unable find replace institution"

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_institution_id in export_xml_data, \
            f'Match institution should not be removed. Export xml is {export_xml_data}'

    def test_replace_node_rule_action(self):
        """
        Test Replace single node replace and remove by
        another institution
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create replace rule
        test_match_node_id = '665a5cf4-87f3-4334-bd9f-9eb28ac89a8b'
        test_replace_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        replace_node_action_id = self._get_replace_node_action_id()
        match_node_id = self._get_match_node_id()
        replace_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=replace_node_action_id,
            action_info_data={"key": "ID", "value": test_replace_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_node_id not in export_xml_data, \
            f'Match node should be removed. Export xml is {export_xml_data}'
        assert test_replace_node_id in export_xml_data, \
            f'Replacement node should not be remove. Export xml is {export_xml_data}'

        owner_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        assert owner_institution_id in export_xml_data, \
            f'Institution should not be removed. Export xml is {export_xml_data}'

    def test_replace_node_rule_action_with_link_connected(self):
        """
        Test Replace a node with link connected replace and remove
        by another institution
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create replace rule
        test_match_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        test_replace_node_id = '665a5cf4-87f3-4334-bd9f-9eb28ac89a8b'
        replace_node_action_id = self._get_replace_node_action_id()
        match_node_id = self._get_match_node_id()
        replace_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=replace_node_action_id,
            action_info_data={"key": "ID", "value": test_replace_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_node_id not in export_xml_data, \
            f'Match node should be removed. Export xml is {export_xml_data}'
        assert test_replace_node_id in export_xml_data, \
            f'Replacement node should not be remove. Export xml is {export_xml_data}'

        expected_endpoints_count = export_xml_data.count(test_replace_node_id)
        assert expected_endpoints_count == 2, \
            "Unexpected amount of the test nodes after the rule action"

    def test_replace_node_rule_action_fail_find_replacement(self):
        """
        Test replace action fail if unable to find the replacement node
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create replace rule
        test_match_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        test_replace_node_id = 'test-replacement-id'
        replace_node_action_id = self._get_replace_node_action_id()
        match_node_id = self._get_match_node_id()
        replace_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=replace_node_action_id,
            action_info_data={"key": "ID", "value": test_replace_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(replace_node_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        message = response['actions'][0]['message']
        assert "Could not find the substitute Node." in message, \
            "Unexpected error message when unable find replace node"

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_node_id in export_xml_data, \
            f'Match node should not be removed. Export xml is {export_xml_data}'

    def test_replace_link_rule_action(self):
        """
        Test link replace and remove by another link,
        two links must have same two nodes
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # replace two nodes to make sure two links have same endpoints
        first_match_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        first_replace_node_id = 'ba435a0b-425f-4933-b113-9da546f9fdc9'
        replace_node_action_id = self._get_replace_node_action_id()
        match_node_id = self._get_match_node_id()
        replace_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_1',
            action_type_id=replace_node_action_id,
            action_info_data={"key": "ID", "value": first_replace_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": first_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_node_rule_id) + '/apply/',
            auth=True
        )

        # Create second replace rule
        second_match_node_id = '14bdb1f4-c226-48ef-84f2-c907b3c149b9'
        second_replace_node_id = '55ff5edf-9fcf-4aa3-b7e5-b0bcb92bae9e'
        replace_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_2',
            action_type_id=replace_node_action_id,
            action_info_data={"key": "ID", "value": second_replace_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": second_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_node_rule_id) + '/apply/',
            auth=True
        )

        # Create link replace rule
        test_match_link_id = '14b209b2-fecb-4239-9698-3e900270b9ef'
        test_replace_link_id = '890adec5-a530-48fe-9875-415a06ee4b1e'
        replace_link_action_id = self._get_replace_link_action_id()
        match_link_id = self._get_match_link_id()
        replace_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_link',
            action_type_id=replace_link_action_id,
            action_info_data={"key": "ID", "value": test_replace_link_id},
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(replace_link_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_link_id not in export_xml_data, \
            f'Match link should be removed. Export xml is {export_xml_data}'
        assert test_replace_link_id in export_xml_data, \
            f'Replacement link should not be remove. Export xml is {export_xml_data}'

    def test_replace_link_rule_action_fail_endpoints_not_same(self):
        """
        Test link replace and remove by another link fail
        if the endpoints are not same.
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create link replace rule
        test_match_link_id = '14b209b2-fecb-4239-9698-3e900270b9ef'
        test_replace_link_id = '890adec5-a530-48fe-9875-415a06ee4b1e'
        replace_link_action_id = self._get_replace_link_action_id()
        match_link_id = self._get_match_link_id()
        replace_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_link',
            action_type_id=replace_link_action_id,
            action_info_data={"key": "ID", "value": test_replace_link_id},
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(replace_link_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        message = response['actions'][0]['message']
        assert 'have different endpoints' in message, 'Unexpected error message'

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_link_id in export_xml_data, \
            f'Match link should be removed. Export xml is {export_xml_data}'
        assert test_replace_link_id in export_xml_data, \
            f'Replacement link should not be remove. Export xml is {export_xml_data}'

    def test_replace_link_rule_action_fail_find_replace_link(self):
        """
        Test link replace and remove by another link fail if
        unable find the replace link
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create link replace rule
        test_match_link_id = '14b209b2-fecb-4239-9698-3e900270b9ef'
        test_replace_link_id = 'test-link-id'
        replace_link_action_id = self._get_replace_link_action_id()
        match_link_id = self._get_match_link_id()
        replace_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_link',
            action_type_id=replace_link_action_id,
            action_info_data={"key": "ID", "value": test_replace_link_id},
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(replace_link_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        message = response['actions'][0]['message']
        assert 'Could not find the substitute Link.' in message, \
            "Unexpected error message when two links endpoints are different"

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_link_id in export_xml_data, \
            f'Match link should be removed. Export xml is {export_xml_data}'

    def test_merge_into_institution_rule_action(self):
        """
        Test merge into single institution merge and remove
        by another institution
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create merge rule
        test_match_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        test_merge_into_institution_id = 'a9af48fd-2332-462d-9584-0f83abbf64de'
        merge_into_institution_action_id = self._get_merge_into_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        merge_into_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=merge_into_institution_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_institution_id},
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_institution_id not in export_xml_data, \
            f'Match institution should be removed. Export xml is {export_xml_data}'
        assert test_merge_into_institution_id in export_xml_data, \
            f'Merge into institution should not be remove. Export xml is {export_xml_data}'

        affected_node_id = '665a5cf4-87f3-4334-bd9f-9eb28ac89a8b'
        assert affected_node_id in export_xml_data, \
            f'Node should not be removed. Export xml is {export_xml_data}'

        # if the key matches then the properties must not be
        # duplicated except for the key 'tag'
        url_occurance = export_xml_data.count('institution-url.com')
        assert url_occurance == 1, \
            'There should only be one property after merge'

        # if the key and value matches then the properties
        # must not be duplicated even for 'tag'
        description_occurance = export_xml_data.count('institution value sample')
        assert description_occurance == 1, \
            'There should only be 1 value for tag in properties after merge'

        # merge must retain multiple properties if the key is 'tag'
        # and the value are different
        tag_occurance = export_xml_data.count('institution tag')
        assert tag_occurance == 2, \
            'There should be 2 value for tag in properties after merge'

    def test_merge_into_institution_of_multiple_nodes_and_link_rule_action(self):
        """
        Test Merge into rule action, and make sure all the elements'
        owner are updated
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create merge rule
        test_match_institution_id = 'a9af48fd-2332-462d-9584-0f83abbf64de'
        test_merge_into_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        merge_into_institution_action_id = self._get_merge_into_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        merge_into_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=merge_into_institution_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_institution_id},
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_institution_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_institution_id not in export_xml_data, \
            f'Match institution should be removed. Export xml is {export_xml_data}'
        assert test_merge_into_institution_id in export_xml_data, \
            f'Merge into institution should not be remove. Export xml is {export_xml_data}'

        count_owners = export_xml_data.count(test_merge_into_institution_id)
        assert count_owners == 5, \
            'count discrepancy after institution merge into rule action'

    def test_merge_action_fails_when_unable_to_find_merge_into_institution(self):
        """
        Test merge into action must fail if unable to find the
        merge into institution
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create merge rule
        test_match_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        test_merge_into_institution_id = 'test-merge-id'
        merge_into_institution_action_id = self._get_merge_into_institution_action_id()
        match_institution_id = self._get_match_institution_id()
        merge_into_institution_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=merge_into_institution_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_institution_id},
            match_type_id=match_institution_id,
            match_info_data={"key": "ID", "value": test_match_institution_id}
        )
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(merge_into_institution_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        message = response['actions'][0]['message']
        assert "Could not find the substitute Institution." in message, \
            "Unexpected error message when unable find merge into institution"

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_institution_id in export_xml_data, \
            f'Match institution should not be removed. Export xml is {export_xml_data}'

    def test_merge_into_node_rule_action(self):
        """
        Test merge into single node and remove by another
        node after merging
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create merge rule
        test_match_node_id = '665a5cf4-87f3-4334-bd9f-9eb28ac89a8b'
        test_merge_into_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        merge_into_node_action_id = self._get_merge_into_node_action_id()
        match_node_id = self._get_match_node_id()
        merge_into_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=merge_into_node_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_node_id not in export_xml_data, \
            f'Match node should be removed. Export xml is {export_xml_data}'
        assert test_merge_into_node_id in export_xml_data, \
            f'Merge into node should not be remove. Export xml is {export_xml_data}'

        owner_institution_id = '549a6e56-1eef-4d11-8602-5e8d694e3cbd'
        assert owner_institution_id in export_xml_data, \
            f'Institution should not be removed. Export xml is {export_xml_data}'

        # if the key matches then the properties must not be
        # duplicated except for the key 'tag'
        url_occurance = export_xml_data.count('node-url.com')
        assert url_occurance == 1, \
            'There should only be one URL property after merge'

        # if the key and value matches then the properties
        # must not be duplicated even for 'tag'
        description_occurance = export_xml_data.count('node value sample')
        assert description_occurance == 1, \
            'There should only be 1 tag in properties after merge for same values'

        # merge must retain multiple properties if the key is 'tag'
        # and the value are different
        tag_occurance = export_xml_data.count('node tag')
        assert tag_occurance == 2, \
            'There should be 2 tag in properties after merge for different values for "tag" key'

    def test_merge_into_node_rule_action_with_link_connected(self):
        """
        Test merge a node with another node connected to a link,
        and remove matched node
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create merge rule
        test_match_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        test_merge_into_node_id = '665a5cf4-87f3-4334-bd9f-9eb28ac89a8b'
        merge_into_node_action_id = self._get_merge_into_node_action_id()
        match_node_id = self._get_match_node_id()
        merge_into_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=merge_into_node_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_node_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_node_id not in export_xml_data, \
            'Match node should be removed.'
        assert test_merge_into_node_id in export_xml_data, \
            'Merge into node should not be remove.'

        expected_endpoints_count = export_xml_data.count(test_merge_into_node_id)
        assert expected_endpoints_count == 2, \
            "Unexpected amount of the test nodes after the rule action"

    def test_merge_into_node_rule_action_fail_find_node_to_merge_into(self):
        """
        Test merge into action fail if unable to find the
        merge into node
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create merge into rule
        test_match_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        test_merge_into_node_id = 'test-replacement-id'
        merge_into_node_action_id = self._get_merge_into_node_action_id()
        match_node_id = self._get_match_node_id()
        merge_into_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test',
            action_type_id=merge_into_node_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": test_match_node_id}
        )
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(merge_into_node_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        message = response['actions'][0]['message']
        assert "Could not find the substitute Node." in message, \
            "Unexpected error message when unable find merge into node"

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_node_id in export_xml_data, \
            f'Match node should not be removed. Export xml is {export_xml_data}'

    def test_merge_into_link_rule_action(self):
        """
        Test link merge into another link and remove matched link,
        two links must have same two nodes
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # merge two nodes to make sure two links have same endpoints
        first_match_node_id = '9f220271-b951-45c8-9f63-59a8749ddf4b'
        first_merge_into_node_id = 'ba435a0b-425f-4933-b113-9da546f9fdc9'
        merge_into_node_action_id = self._get_merge_into_node_action_id()
        match_node_id = self._get_match_node_id()
        merge_into_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_1',
            action_type_id=merge_into_node_action_id,
            action_info_data={"key": "ID", "value": first_merge_into_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": first_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_node_rule_id) + '/apply/',
            auth=True
        )

        # Create second merge node rule
        second_match_node_id = '14bdb1f4-c226-48ef-84f2-c907b3c149b9'
        second_merge_into_node_id = '55ff5edf-9fcf-4aa3-b7e5-b0bcb92bae9e'
        merge_into_node_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_2',
            action_type_id=merge_into_node_action_id,
            action_info_data={"key": "ID", "value": second_merge_into_node_id},
            match_type_id=match_node_id,
            match_info_data={"key": "ID", "value": second_match_node_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_node_rule_id) + '/apply/',
            auth=True
        )

        # Create link merge rule
        test_match_link_id = '14b209b2-fecb-4239-9698-3e900270b9ef'
        test_merge_into_link_id = '890adec5-a530-48fe-9875-415a06ee4b1e'
        merge_into_link_action_id = self._get_merge_into_link_action_id()
        match_link_id = self._get_match_link_id()
        merge_into_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_link',
            action_type_id=merge_into_link_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_link_id},
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        self.get(
            url=RULE_TEST_API_URL + str(merge_into_link_rule_id) + '/apply/',
            auth=True
        )

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_link_id not in export_xml_data, \
            f'Match link should be removed. Export xml is {export_xml_data}'
        assert test_merge_into_link_id in export_xml_data, \
            f'Merge into link should not be remove. Export xml is {export_xml_data}'

        # if the key matches then the properties must not be
        # duplicated except for the key 'tag'
        url_occurance = export_xml_data.count('link-url.com')
        assert url_occurance == 1, \
            'There should only be one URL property after merge'

        # if the key and value matches then the properties must not be
        # duplicated even for 'tag'
        same_tag_value_occurance = export_xml_data.count('link value sample')
        assert same_tag_value_occurance == 1, \
            'There should only be 1 "tag" in properties after merge for same value'

        # merge must retain multiple properties if the key is 'tag'
        # and the value are different
        tag_occurance = export_xml_data.count('link tag')
        assert tag_occurance == 2, \
            'There should be 2 tag in properties after merge for different values in "tag" key'

    def test_merge_into_link_rule_action_fail_endpoints_not_same(self):
        """
        Test link merge into and remove by another link fails if the
        endpoints are not same.
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create link merge rule
        test_match_link_id = '14b209b2-fecb-4239-9698-3e900270b9ef'
        test_merge_into_link_id = '890adec5-a530-48fe-9875-415a06ee4b1e'
        merge_into_link_action_id = self._get_merge_into_link_action_id()
        match_link_id = self._get_match_link_id()
        merge_into_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_link',
            action_type_id=merge_into_link_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_link_id},
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action and expected the rule won't be applied
        response = self.get(
            url=RULE_TEST_API_URL + str(merge_into_link_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )

        assert 'have different endpoints' in \
            response['actions'][0]['message'], \
            'Unexpected error message'

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_link_id in export_xml_data, \
            f'Match link should be removed.Export xml is {export_xml_data}'
        assert test_merge_into_link_id in export_xml_data, \
            f'Merge into link should not be remove. Export xml is {export_xml_data}'

    def test_merge_into_link_rule_action_fail_to_find_merge_into_link(self):
        """
        Test link merge into and remove by another link fail if
        unable find the merge into link
        """
        # Import test data
        test_grenml_name = 'test_replace_action_grenml.xml'
        self.import_xml_file(test_grenml_name)

        # Create link merge into rule
        test_match_link_id = '14b209b2-fecb-4239-9698-3e900270b9ef'
        test_merge_into_link_id = 'test-link-id'
        merge_into_link_action_id = self._get_merge_into_link_action_id()
        match_link_id = self._get_match_link_id()
        merge_into_link_rule_id = self._get_or_create_new_rule(
            rule_set_name='new_ruleset',
            rule_name='new_rule_test_link',
            action_type_id=merge_into_link_action_id,
            action_info_data={"key": "ID", "value": test_merge_into_link_id},
            match_type_id=match_link_id,
            match_info_data={"key": "ID", "value": test_match_link_id}
        )
        # Call rule action
        response = self.get(
            url=RULE_TEST_API_URL + str(merge_into_link_rule_id) + '/apply/',
            auth=True,
            # expected_status_code=requests.codes.internal_server_error
        )
        assert len(response['affected']['links']) == 0, \
            "Unexpected error message when two links endpoints are different"

        # Export xml and check the result
        export_xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        assert test_match_link_id in export_xml_data, \
            f'Match link should not be removed. Export xml is {export_xml_data}'

    def test_ruleset_health_check_healthy(self):
        """
        Verify if the ruleset shows Ready under healthcheck
        section in the ruleset page
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        # get Ruleset ID
        ruleset_id = self._get_ruleset_id(
            rule_set_name=data[RULESETS][0][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_set_health = self.get(
            url=RULESET_TEST_API_URL + str(ruleset_id) + '/status/',
            auth=True,
        )

        assert rule_set_health['ready'] is True, \
            'Ruleset expected to be configured correctly'

    def test_rule_health_check_healthy(self):
        """
        Verify if the rule shows Ready under healthcheck
        section in the rules page
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        # get Rule ID
        delete_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][0][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(delete_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is True, \
            'Rule expected to be configured correct and ready'

    def test_rule_misconfiguration_ruleset_health_check_is_misconfigured(self):
        """
        Verify that if a rule is misconfigured in a rule the
        ruleset shows misconfigured message in the ruleset page
        the rule health check should alert user for misconfigured
        ruleset
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            action_info_set_list = data[RULESETS][0][RULES][0][ACTIONS][0][ACTION_INFO_SET]
            # append value to the action info set
            action_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        ruleset_id = self._get_ruleset_id(
            rule_set_name=data[RULESETS][0][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_set_health = self.get(
            url=RULESET_TEST_API_URL + str(ruleset_id) + '/status/',
            auth=True,
        )

        assert rule_set_health['ready'] is False, 'Ruleset expected to be misconfigured'

    def test_rule_misconfiguration_delete_action_with_multiple_match_info(self):
        """
        Verify if multiple match info values of ID are not
        accepted by delete action rule
        the rule health check should alert user for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            match_info_set_list = data[RULESETS][0][RULES][0][MATCH_CRITERIA][0][MATCH_INFO_SET]
            # append value to the action info set
            match_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        delete_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][0][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(delete_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, 'Rule expected to be misconfigured'

    def test_rule_misconfiguration_delete_action_with_multiple_action_info(self):
        """
        Verify if multiple action info values of ID are not
        accepted by delete action rule
        the rule health check should alert user for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            action_info_set_list = data[RULESETS][0][RULES][0][ACTIONS][0][ACTION_INFO_SET]
            # append value to the action info set
            action_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        delete_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][0][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(delete_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, 'Rule expected to be misconfigured'

    def test_rule_misconfiguration_merge_action_with_multiple_action_info(self):
        """
        Verify if multiple action info values of ID are not
        accepted by merge action rule
        the rule health check should alert user for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            action_info_set_list = data[RULESETS][0][RULES][1][ACTIONS][0][ACTION_INFO_SET]
            # append value to the action info set
            action_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        merge_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][1][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(merge_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, 'Rule expected to be misconfigured'

    def test_rule_misconfiguration_merge_action_with_multiple_match_info_set(self):
        """
        Verify if multiple match info set values of ID are not
        accepted by merge action rule
        the rule health check should alert user for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            match_info_set_list = data[RULESETS][0][RULES][1][MATCH_CRITERIA][0][MATCH_INFO_SET]
            # append value to the action info set
            match_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        merge_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][1][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(merge_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, 'Rule expected to be misconfigured'

    def test_rule_misconfiguration_replace_action_with_multiple_action_info(self):
        """
        Verify if multiple action info values of ID are not accepted
         by replace action rule
        the rule health check should alert user for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            action_info_set_list = data[RULESETS][0][RULES][2][ACTIONS][0][ACTION_INFO_SET]
            # append value to the action info set
            action_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        replace_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][2][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(replace_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, 'Rule expected to be misconfigured'

    def test_rule_misconfiguration_replace_action_with_multiple_match_info_set(self):
        """
        Verify if multiple match info set values of ID are not accepted
        by replace action rule
        the rule health check should alert user for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        value = {'key': 'ID', 'value': '98573145'}
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            match_info_set_list = data[RULESETS][0][RULES][2][MATCH_CRITERIA][0][MATCH_INFO_SET]
            # append value to the action info set
            match_info_set_list.append(value)
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        replace_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][2][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(replace_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, \
            'Rule expected to be misconfigured'

    def test_rule_misconfiguration_delete_action_no_id_in_match_info_set(self):
        """
        Verify if match info values are not provided for the delete
        action the rule health check should alert user for
        misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name

        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            match_info_set_list = data[RULESETS][0][RULES][0][MATCH_CRITERIA][0][MATCH_INFO_SET]
            # clear the values on the match info set list
            match_info_set_list.clear()
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        delete_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][0][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(delete_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, \
            'Rule expected to be misconfigured'

    def test_rule_misconfiguration_merge_action_no_id_in_match_info_set(self):
        """
        Verify if match info values are not provided for the merge
        action the rule health check should alert user for
        misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            match_info_set_list = data[RULESETS][0][RULES][1][MATCH_CRITERIA][0][MATCH_INFO_SET]
            # append value to the action info set
            match_info_set_list.clear()
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        merge_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][1][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(merge_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, \
            'Rule expected to be misconfigured'

    def test_rule_misconfiguration_replace_action_no_id_in_match_info_set(self):
        """
        Verify if match info values are not provided for the replace
        action the rule health check should alert user for
        misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            match_info_set_list = data[RULESETS][0][RULES][2][MATCH_CRITERIA][0][MATCH_INFO_SET]
            # append value to the action info set
            match_info_set_list.clear()
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        replace_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][2][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(replace_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, \
            'Rule expected to be misconfigured'

    def test_rule_misconfiguration_merge_action_no_id_in_action_info_set(self):
        """
        Verify if action info values are not provided for the merge
        action the rule health check should alert user for
        misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            action_info_set_list = data[RULESETS][0][RULES][1][ACTIONS][0][ACTION_INFO_SET]
            # append value to the action info set
            action_info_set_list.clear()
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        merge_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][1][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(merge_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, \
            'Rule expected to be misconfigured'

    def test_rule_misconfiguration_replace_action_no_id_in_action_info_set(self):
        """
        Verify if action info values are not provided for the
        replace action the rule health check should alert user
        for misconfigured rule
        """
        # Import test data
        test_grenml_name = 'test_import_rulesets.json'
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            action_info_set_list = data[RULESETS][0][RULES][2][ACTIONS][0][ACTION_INFO_SET]
            # append value to the action info set
            action_info_set_list.clear()
            # convert json object to string type for API
            data_string = json.dumps(data)

        # post ruleset to DB
        self._import_ruleset_via_api(data=data_string)

        replace_action_rule_id = self._get_or_create_new_rule(
            rule_set_name=data[RULESETS][0][NAME],
            rule_name=data[RULESETS][0][RULES][2][NAME],
        )

        # Call rule status api to retrieve health check information
        rule_health = self.get(
            url=RULE_TEST_API_URL + str(replace_action_rule_id) + '/status/',
            auth=True,
        )

        assert rule_health['ready'] is False, \
            'Rule expected to be misconfigured'

    def test_rule_filters_institution_using_topology_id_merge_action(self):
        """
        This test verifies that if institutions can be filtered with the
        topology they belong rule to merge institutions with same
        ID from 2 topologies so assertion counts if the element is
        part of both after import
        """
        self.import_ruleset(RULESET_WITH_TOPOLOGY_ID)
        self.import_xml_file(RULESET_IMPORT_FILE)
        time.sleep(2)
        institution_data = self.get_institution_details(grenml_id='Test-Institution-1')
        assert len(institution_data[0]['topologies']) == 2

    def test_rule_filters_link_using_topology_id_delete_action(self):
        """
        This test verifies that if link can be filtered with the
        topology they belong and link from 3rd topology is deleted
        every time using rules
        """
        self.import_ruleset(RULESET_WITH_TOPOLOGY_ID)
        self.import_xml_file(RULESET_IMPORT_FILE)
        time.sleep(2)
        link_data = self.get_link_details(grenml_id='child-topo-link')
        assert link_data[0]['topologies'][0]['grenml_id'] != "third-topology"

    def test_rule_filters_node_using_topology_id_replace_action(self):
        """
        This test verifies that if nodes can be filtered with the
        topology they belong and replace a node in one topo with a
        node in another topo
        assert if link:3 has child-node-1 instead of node:1
        """
        self.import_ruleset(RULESET_WITH_TOPOLOGY_ID)
        self.import_xml_file(RULESET_IMPORT_FILE)
        time.sleep(2)
        link_data = self.get_link_details(grenml_id='link:3')
        time.sleep(2)
        node_a_ids = [data["node_a"]["grenml_id"] for data in link_data]
        node_b_ids = [data["node_b"]["grenml_id"] for data in link_data]
        assert 'node:1' not in node_a_ids and node_b_ids

    def test_rule_filters_institutions_using_wrong_topology_id_delete_action(self):
        """
        This test verifies that if an institution ID is filtered
        using the topology ID in which the institution does not
        belong it should not delete the element
        """
        self.import_ruleset(RULESET_WITH_TOPOLOGY_ID)
        self.import_xml_file(RULESET_IMPORT_FILE)
        time.sleep(2)
        institution_data = self.get_institution_details(
            grenml_id='Test Institution 2'
        )
        assert institution_data

    def test_rule_filters_nodes_using_non_existent_topology_id_delete_action(self):
        """
        This test verifies that if non-existing topology id is used to
        filer a node no action is performed and node:3 should exist
        """
        self.import_ruleset(RULESET_WITH_TOPOLOGY_ID)
        self.import_xml_file(RULESET_IMPORT_FILE)
        time.sleep(2)
        node_data = self.get_node_details(grenml_id='node:3')
        assert node_data

    def _get_or_create_new_rule(
            self,
            rule_set_name,
            rule_name,
            action_type_id=None,
            action_info_data=None,
            match_type_id=None,
            match_info_data=None,
    ):
        """
        This function will use the test rule API to create new rule,
        will return the rule id
        """
        # Check if rule already create
        rule_list = self.get(url=RULE_TEST_API_URL, auth=True)
        for rule in rule_list:
            if rule[NAME] == rule_name:
                return rule['id']

        # Get or Create rule sets
        rule_sets_list = self.get(url=RULESET_TEST_API_URL, auth=True)
        found_rule_set = False
        for rule_set in rule_sets_list:
            if rule_set[NAME] == rule_set_name:
                rule_set_id = rule_set['id']
                found_rule_set = True
        if not found_rule_set:
            test_rule_set_data = {"name": rule_set_name}
            location, response = self.post(
                url=RULESET_TEST_API_URL,
                data=test_rule_set_data,
                auth=True
            )
            rule_set_id = response['id']

        # Create new rule
        test_rule = {"name": rule_name, "ruleset": rule_set_id}
        location, response = self.post(
            url=RULE_TEST_API_URL,
            data=test_rule,
            auth=True
        )
        create_rule_id = response['id']

        # Connect rule to action type
        if action_type_id:
            action_data = {"rule": create_rule_id, "action_type": action_type_id}
            location, action = self.post(
                url=ACTION_API_URL,
                data=action_data,
                auth=True
            )

        # Create match info
        if action_info_data:
            info_data = {
                "key": action_info_data['key'],
                "value": action_info_data['value'],
                "action": action['id']
            }
            self.post(url=ACTION_API_INFO_RUL, data=info_data, auth=True)

        # Connect rule to match criterion
        if match_type_id:
            match_criterion_data = {
                "rule": create_rule_id,
                "match_type": match_type_id
            }
            location, match_criterion = self.post(
                url=MATCH_CRITERIA_API_URL,
                data=match_criterion_data,
                auth=True
            )
        # Create match info
        if match_info_data:
            info_data = {
                "key": match_info_data['key'],
                "value": match_info_data['value'],
                "match_criterion": match_criterion['id']
            }
            self.post(url=MATCH_INFO_API_URL, data=info_data, auth=True)
        return create_rule_id

    def _get_ruleset_id(self, rule_set_name):
        """
        this helper method uses the ruleset API to return the
        ruleset id and health check info
        """
        # Get rule set id
        rule_sets_list = self.get(url=RULESET_TEST_API_URL, auth=True)
        for rule_set in rule_sets_list:
            if rule_set[NAME] == rule_set_name:
                rule_set_id = rule_set['id']
                return rule_set_id

    def _import_ruleset_via_api(self, data):
        # post ruleset to DB
        response = requests.post(
            url=IMPORT_RULESETS_API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'POST not successful via API'

    def _get_delete_link_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Delete Link':
                return action_type['id']

    def _get_delete_node_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Delete Node':
                return action_type['id']

    def _get_delete_institution_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Delete Institution':
                return action_type['id']

    def _get_replace_link_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Replace with Link':
                return action_type['id']

    def _get_replace_node_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Replace with Node':
                return action_type['id']

    def _get_replace_institution_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Replace with Institution':
                return action_type['id']

    def _get_match_link_id(self):
        match_type_list = self.get(url=MATCH_TYPE_LIST, auth=True)
        for match_type in match_type_list:
            if match_type[NAME] == 'Match Links by ID':
                return match_type['id']

    def _get_match_node_id(self):
        match_type_list = self.get(url=MATCH_TYPE_LIST, auth=True)
        for match_type in match_type_list:
            if match_type[NAME] == 'Match Nodes by ID':
                return match_type['id']

    def _get_match_institution_id(self):
        match_type_list = self.get(url=MATCH_TYPE_LIST, auth=True)
        for match_type in match_type_list:
            if match_type[NAME] == 'Match Institutions by ID':
                return match_type['id']

    def _get_merge_into_link_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Merge into Link':
                return action_type['id']

    def _get_merge_into_node_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Merge into Node':
                return action_type['id']

    def _get_merge_into_institution_action_id(self):
        action_type_list = self.get(url=ACTION_TYPE_LIST, auth=True)
        for action_type in action_type_list:
            if action_type[NAME] == 'Merge into Institution':
                return action_type['id']

    def _import_test_data(self, data_file_name):

        # Import test data
        test_file_path = TEST_FILE_FOLDER + data_file_name
        with open(test_file_path, 'r') as test_data_string:
            test_data = test_data_string.read()
        self.post(url=IMPORT_GRENML_URL_TEST, data=test_data)
