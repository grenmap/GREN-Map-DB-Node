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

Functions to create and clear a cache for the results of GraphQL queries
sent by the web client.
"""

import json
import logging
import os

from redis import Redis

from django.db.models.signals import post_delete, post_save

logger = logging.getLogger()


REDIS_KEY_TEMPLATE = 'graphql_cached_{}'

NODES_QUERY = '''query {
  nodes {
    id, name, shortName, latitude, longitude,
    properties { name, value, __typename },
    owners { id, __typename },
    __typename
  }
}'''

LINKS_QUERY = '''query {
  links {
    id, name,
    nodeA { id, latitude, longitude, __typename },
    nodeB { id, latitude, longitude, __typename },
    properties { name, value, __typename },
    owners { id, __typename },
    __typename
  }
}'''

INSTITUTIONS_QUERY = '''query {
  institutions {
    id, name, shortName, latitude, longitude,
    properties { name, value, __typename },
    __typename
  }
}'''

# Associates entity names to GraphQL query strings.
QUERIES = {
    'nodes': NODES_QUERY,
    'links': LINKS_QUERY,
    'institutions': INSTITUTIONS_QUERY,
}


def key_for_entity(entity):
    """
    Uses the entity name to create a retrieval key we will use
    when we store GraphQL query results on redis.
    """
    return REDIS_KEY_TEMPLATE.format(entity)


class NullRedisClient:
    """
    This object provides the same methods we expect in the actual
    Redis client, but doesn't do any work.
    """
    def set(self, key, value):
        pass

    def get(self, key):
        pass

    def delete(self, key):
        pass


def make_redis_client():
    """
    Returns a Redis client object if the REDIS_HOST environment variable
    is defined. Otherwise return an instance of NullRedisClient.
    """
    redis_host = os.environ.get('REDIS_HOST')
    client = NullRedisClient()
    if redis_host is not None:
        client = Redis.from_url(redis_host)
    return client


def save_initial_map_data_for_entity(entity):
    """
    Saves the result of a GraphQL request associated to the entity
    passed as parameter to a file.
    """
    def store(key, value):
        r = make_redis_client()
        r.set(key, value)

    logger.info('save_initial_map_data_for_entity: computing %s', entity)

    # The server fails to start (AppRegistryNotReady exception)
    # if we move this import out of the function.
    from .schema import schema
    response = schema.execute(QUERIES[entity])

    key = key_for_entity(entity)
    result = json.dumps({'data': response.data})
    store(key, result)
    logger.info('save_initial_map_data_for_entity: finished %s', entity)
    return result


def save_initial_map_data_for_all_entities():
    """
    Saves the redis records for the GraphQL query results
    """
    logger.info('Set redis cache for map data')
    for entity in QUERIES.keys():
        try:
            save_initial_map_data_for_entity(entity)
        except:  # noqa: E722
            logger.warning(f'Set redis cache failed for {entity}')


def get_initial_map_data(entity):
    """
    Returns the GraphQL query result for an entity.
    Tries first to obtain the result from a file.
    If not possible, recomputes it.
    """
    logger.info(f'get_initial_map_data for: {entity}')
    key = key_for_entity(entity)
    r = make_redis_client()
    result = r.get(key)
    if result is None:
        result = save_initial_map_data_for_entity(entity)
    return result


class InvalidSenderError(Exception):
    pass


def clear_cache(sender, **kwargs):
    """
    Receiver function connected to post_save and post_delete signals
    from network topology models (Node, Link and Institution).

    Deletes a file containing the GraphQL query results,
    according to the type of the signal sender.
    """
    from network_topology.models.institution import Institution
    from network_topology.models.link import Link
    from network_topology.models.node import Node

    # determine entity
    entity = None
    if isinstance(kwargs['instance'], Institution):
        entity = 'institutions'
    elif isinstance(kwargs['instance'], Link):
        entity = 'links'
    elif isinstance(kwargs['instance'], Node):
        entity = 'nodes'
    else:
        # If this happens, we have made a programming mistake.
        raise InvalidSenderError()

    # delete the GraphQL result for the entity
    key = key_for_entity(entity)
    r = make_redis_client()
    r.delete(key)


def post_save_connect():
    """
    Registers the clear_cache function as a receiver
    for post_save and post_delete signals sent by
    Node, Link and Institution models.
    """
    post_save.connect(
        clear_cache,
        sender='network_topology.Node',
    )
    post_save.connect(
        clear_cache,
        sender='network_topology.Link',
    )
    post_save.connect(
        clear_cache,
        sender='network_topology.Institution',
    )

    post_delete.connect(
        clear_cache,
        sender='network_topology.Node',
    )
    post_delete.connect(
        clear_cache,
        sender='network_topology.Link',
    )
    post_delete.connect(
        clear_cache,
        sender='network_topology.Institution',
    )


def post_save_disconnect():
    """
    Disables clear_cache as handler of post_save and post_delete signals
    from nodes, links and institutions.
    """
    post_save.disconnect(
        clear_cache,
        sender='network_topology.Node',
    )
    post_save.disconnect(
        clear_cache,
        sender='network_topology.Link',
    )
    post_save.disconnect(
        clear_cache,
        sender='network_topology.Institution',
    )

    post_delete.disconnect(
        clear_cache,
        sender='network_topology.Node',
    )
    post_delete.disconnect(
        clear_cache,
        sender='network_topology.Link',
    )
    post_delete.disconnect(
        clear_cache,
        sender='network_topology.Institution',
    )
