"""
This file contains gren-map-db-node basic API tests
"""

from framework import GrenMapTestingFramework


class TestNodeAPI(GrenMapTestingFramework):

    def test_server_status_api(self):
        """
        Check test docker server is connected
        """
        self.check_test_server_status()
