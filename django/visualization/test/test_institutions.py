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
"""

import json

from django.test import TestCase

from .base import BaseGraphQLTestCase
from visualization.schema import schema


class TestInstitutionsQuery(BaseGraphQLTestCase, TestCase):

    GRAPHQL_SCHEMA = schema
    GRAPHQL_URL = '/visualization/graphql/'

    def test_query_all_institutions(self):
        self._enable_visualization()
        self._enable_cache()
        response = self.query(
            '''
            query {
                institutions {
                    id
                    name
                }
            }
            '''
        )

        json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)

    def test_query_single_institution(self):
        self._enable_visualization()
        self._enable_cache()
        response = self.query(
            '''
            query {
                institution(id:"institution1") {
                    id
                    name
                }
            }
            '''
        )

        json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
