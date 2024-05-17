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

import json

from django.test import TestCase

from network_topology.models import Institution, Node, Link
from grenml_export.constants import RESERVED_PROPERTY_PREFIX

from .base import BaseGraphQLTestCase
from visualization.schema import schema


class TestResolvedPropertiesFilter(BaseGraphQLTestCase, TestCase):

    GRAPHQL_SCHEMA = schema
    GRAPHQL_URL = '/visualization/graphql/'

    def test_query_nodes_with_properties(self):
        """
        Control case.  Nodes with some generic Properties.
        """
        Node.objects.create(
            grenml_id='NodeA',
            name='Node A',
            latitude=0.0,
            longitude=0.0,
        )
        node_b = Node.objects.create(
            grenml_id='NodeB',
            name='Node B',
            latitude=0.0,
            longitude=0.0,
        )
        node_b.property('test property 1', value='value placeholder')
        node_c = Node.objects.create(
            grenml_id='NodeC',
            name='Node C',
            latitude=0.0,
            longitude=0.0,
        )
        node_c.property('test property 1', value='value placeholder')
        node_c.property('test property 2', value='another value placeholder')

        self._enable_visualization()
        response = self.query(
            '''
            query {
                nodes {
                    id
                    name
                    properties {
                        name
                        value
                    }
                }
            }
            '''
        )

        self.assertResponseNoErrors(response)

        response_data = json.loads(response.content)
        nodes = response_data['data']['nodes']

        nodes_b = filter(lambda x: (True if x['id'] == 'NodeB' else False), nodes)
        node_b = next(nodes_b)
        self.assertEquals(len(node_b['properties']), 1)

        nodes_c = filter(lambda x: (True if x['id'] == 'NodeC' else False), nodes)
        node_c = next(nodes_c)
        self.assertEquals(len(node_c['properties']), 2)

    def test_query_nodes_with_reserved_properties(self):
        """
        Nodes with some generic Properties and some reserved
        Properties, which should not get transmitted by queries.
        """
        Node.objects.create(
            grenml_id='NodeA',
            name='Node A',
            latitude=0.0,
            longitude=0.0,
        )
        node_b = Node.objects.create(
            grenml_id='NodeB',
            name='Node B',
            latitude=0.0,
            longitude=0.0,
        )
        node_b.property('test property 1', value='value placeholder')
        node_b.property(RESERVED_PROPERTY_PREFIX + 'test_reserved_property', value='anything')
        node_c = Node.objects.create(
            grenml_id='NodeC',
            name='Node C',
            latitude=0.0,
            longitude=0.0,
        )
        node_c.property('test property 1', value='value placeholder')
        node_c.property('test property 2', value='another value placeholder')
        node_c.property(RESERVED_PROPERTY_PREFIX + 'test_reserved_property', value='anything')

        self._enable_visualization()
        response = self.query(
            '''
            query {
                nodes {
                    id
                    name
                    properties {
                        name
                        value
                    }
                }
            }
            '''
        )

        self.assertResponseNoErrors(response)

        response_data = json.loads(response.content)
        nodes = response_data['data']['nodes']

        nodes_b = filter(lambda x: (True if x['id'] == 'NodeB' else False), nodes)
        node_b = next(nodes_b)
        self.assertEquals(len(node_b['properties']), 1)

        nodes_c = filter(lambda x: (True if x['id'] == 'NodeC' else False), nodes)
        node_c = next(nodes_c)
        self.assertEquals(len(node_c['properties']), 2)

    def test_query_institutions_with_reserved_properties(self):
        """
        Institution with some generic Properties and a reserved
        Property, which should not get transmitted by queries.
        """
        institution = Institution.objects.create(
            grenml_id='InstA',
            name='Institution A',
            latitude=0.0,
            longitude=0.0,
        )
        institution.property('test property 1', value='value placeholder')
        institution.property('test property 2', value='another value placeholder')
        institution.property(RESERVED_PROPERTY_PREFIX + 'test_reserved_property', value='anything')

        self._enable_visualization()
        response = self.query(
            '''
            query {
                institutions {
                    id
                    name
                    properties {
                        name
                        value
                    }
                }
            }
            '''
        )

        self.assertResponseNoErrors(response)

        response_data = json.loads(response.content)
        institution = response_data['data']['institutions'][0]
        self.assertEquals(len(institution['properties']), 2)

    def test_query_links_with_reserved_properties(self):
        """
        Link with some generic Properties and a reserved
        Property, which should not get transmitted by queries.
        """
        node_a = Node.objects.create(
            grenml_id='NodeA',
            name='Node A',
            latitude=0.0,
            longitude=0.0,
        )
        node_b = Node.objects.create(
            grenml_id='NodeB',
            name='Node B',
            latitude=0.0,
            longitude=0.0,
        )
        link = Link.objects.create(
            grenml_id='LinkA',
            name='Link A',
            node_a=node_a,
            node_b=node_b,
        )
        link.property('test property 1', value='value placeholder')
        link.property('test property 2', value='another value placeholder')
        link.property(RESERVED_PROPERTY_PREFIX + 'test_reserved_property', value='anything')

        self._enable_visualization()
        response = self.query(
            '''
            query {
                links {
                    id
                    name
                    properties {
                        name
                        value
                    }
                }
            }
            '''
        )

        self.assertResponseNoErrors(response)

        response_data = json.loads(response.content)
        link = response_data['data']['links'][0]
        self.assertEquals(len(link['properties']), 2)
