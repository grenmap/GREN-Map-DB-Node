
"""
This file contains tests for the custom ID collision resolution
section of resolving ID collision mechanism.
The flow of the ID collision mechanism works in the order as follows
    1. custom ID collision --->
    2. default catch all ID collision(has default priority of 0) --->
    3. all the other rules
This is enforced by setting a priority on the rulesets and rules.
The lowest number of priority executes first.
lower the number higher the priority
(for example -1 has more priority than 0)
These tests are to verify the order of priority of execution,
and check if the custom rules are executed first.
"""

import pytest
import requests

from constants import RESTORE_DEFAULT_ID_COLLISION_RULES, \
    RULESET_TEST_API_URL, RULE_TEST_API_URL
from framework import GrenMapTestingFramework


INITIAL_FILE = 'test_delete_propagation_full_data.xml'
SECOND_FILE = 'test_delete_propagation_data_with_two_topologies.xml'
DISABLE = 'disable'
ENABLE = 'enable'
APPLY = 'apply'


class TestCustomIdCollisionResolution(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestCustomIdCollisionResolution)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.create_import_token()

        # create default catch-all ruleset
        self.post(
            url=RESTORE_DEFAULT_ID_COLLISION_RULES,
            auth=True,
            expected_status_code=requests.codes.ok
        )
        self.import_ruleset('test_custom_rulesets.json')
        self.import_ruleset('test_import_rulesets.json')
        # initial import
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=INITIAL_FILE,
        )

    def test_rules_are_executed_in_order_of_priority(self):
        """
        Test if the custom ruleset with negative priority(-1) gets
        executed before the default catch all ruleset(priority 0)
        Test flow:
        1. import rulesets with varying priorities 0, -1 and 1000
        and disable them
        2. import a grenml file and enable all the rulesets
        3. apply all rulesets via rpc and get the execution order
        os the rules
        4. verify if the rulesets and rules are executed
        in order of priorities
        5. check if only enabled rules and rulesets are applied
        """
        self._actions_on_all_rulesets(action=DISABLE)
        topology_details = self.get_topology_details('test-topology-1')
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=SECOND_FILE,
            topology_id=topology_details[0]['pk'],
        )
        self._actions_on_all_rulesets(action=ENABLE)
        # import disabled ruleset after enabling all existing rulesets
        self.import_ruleset('test_disabled_ruleset.json')
        # get the execution order of rules from RPC
        rules_execution_log_in_order = self._actions_on_all_rulesets(action=APPLY)
        rules_pk_in_execution_order = []
        for log in rules_execution_log_in_order:
            pk = log['rule']['pk']
            rules_pk_in_execution_order.append(pk)
        ruleset_id = []
        rules_priority_in_execution_order = []
        # get the ruleset ID & priority of each rule in order
        for rule_id in rules_pk_in_execution_order:
            rule_details = self.get(
                url=RULE_TEST_API_URL + str(rule_id),
                auth=True,
            )
            ruleset_id.append(rule_details["ruleset"])
            rules_priority_in_execution_order.append(rule_details["priority"])
        # use the ruleset ID to get the priority of the ruleset
        ruleset_priority_in_execution_order = []
        for ruleset_pk in ruleset_id:
            ruleset_details = self.get(
                url=RULESET_TEST_API_URL + str(ruleset_pk),
                auth=True,
            )
            ruleset_priority_in_execution_order.append(
                ruleset_details["priority"]
            )
        # check if only enabled rules are applied.
        # 9 rules are imported and 8 should be executed
        assert len(rules_execution_log_in_order) == 8, \
            'count discrepancy: Disabled rule is executed or All enabled ' \
            'rules are not executed'
        # assert rules order
        assert rules_priority_in_execution_order == [-1, 5000, 0, 0, 0, 10, 20, 30], \
            'Rules are not executed according to priority'
        # assert ruleset order
        is_sorted = all(a <= b for a, b in zip(
            ruleset_priority_in_execution_order,
            ruleset_priority_in_execution_order[1:]))
        assert is_sorted, 'Rules are not executed according to priority'

    def _actions_on_all_rulesets(self, action):
        """
        This helper method disables all rulesets after import
        """
        if action == ENABLE:
            self.patch(
                url=RULESET_TEST_API_URL + '/enable_all/',
                auth=True
            )
        elif action == DISABLE:
            self.patch(
                url=RULESET_TEST_API_URL + '/disable_all/',
                auth=True
            )
        elif action == APPLY:
            ruleset_execution_order = self.get(
                url=RULESET_TEST_API_URL + '/apply_all/',
                auth=True
            )
            return ruleset_execution_order
        else:
            print("Value does not match available options")
