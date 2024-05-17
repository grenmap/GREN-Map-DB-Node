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

import logging
from copy import copy

from django.utils.translation import gettext as _


log = logging.getLogger('collation')


class ActionLog:
    """
    Collects information about the execution of a Rule Action,
    mostly consisting of affected elements.  Stores the primary keys
    of affected elements for deduplication in case the same element is
    affected more than once in a chain of Actions.
    """
    def __init__(self, action, element):
        self.action = action
        # We copy the element instead of binding a reference to it,
        # so that the PK can be read back later even if the object
        # is deleted during the Action operations (Django nullifies
        # the PK when an object is deleted)
        self.element = copy(element)
        self.succeeded = None
        self.message = 'PROGRAMMING ERROR: This default Action results message was not replaced.'
        self.affected_institutions_primary_keys = []
        self.affected_nodes_primary_keys = []
        self.affected_links_primary_keys = []

    def abort(self, message):
        self.succeeded = False
        log.warning(message)
        self.message = message

    def result(self, message, affected_institutions, affected_nodes, affected_links):
        self.succeeded = True
        log.debug(message)
        self.message = message
        self.affected_institutions_primary_keys = list(set([e.pk for e in affected_institutions]))
        self.affected_nodes_primary_keys = list(set([e.pk for e in affected_nodes]))
        self.affected_links_primary_keys = list(set([e.pk for e in affected_links]))


class RuleLog:
    """
    Collects information about the execution of a Rule:
    - matched elements
    - actions taken, and affected elements
    Also provides handy output methods for formats suitable for
    feedback in the Django Admin and API return.
    """
    def __init__(self, rule, matched_elements=[]):
        self.rule = rule
        self.matched_elements = [e.pk for e in matched_elements]
        self.action_logs = []
        log.info(
            f'Rule {self.rule.log_str} running Actions on '
            f'{len(matched_elements)} {self.rule.element_type}s.'
        )

    def add_action_log(self, action_log: ActionLog):
        self.action_logs.append(action_log)

    def _unique_affected_elements(self):
        """
        Peruses the list of ActionLogs and concatenates the lists of
        affected elements (by primary key), deduplicating keys that
        have been affected more than once.
        """
        affected_institutions = []
        for action_log in self.action_logs:
            affected_institutions.extend(action_log.affected_institutions_primary_keys)
        affected_institutions = list(set(affected_institutions))
        affected_nodes = []
        for action_log in self.action_logs:
            affected_nodes.extend(action_log.affected_nodes_primary_keys)
        affected_nodes = list(set(affected_nodes))
        affected_links = []
        for action_log in self.action_logs:
            affected_links.extend(action_log.affected_links_primary_keys)
        affected_links = list(set(affected_links))
        return (affected_institutions, affected_nodes, affected_links)

    def admin_message(self):
        """
        Creates a message for display in the Django Admin following
        application of a Rule.  Lists the number of affected elements.
        """
        # Translators: {} is the name of a database record created by the user  # noqa
        rule_message = _('Applied Rule {} successfully. ').format(self.rule)
        (insts, nodes, links) = self._unique_affected_elements()

        elements_affected = _(
            # Translators: {}'s are numbers of links, nodes and institutions  # noqa
            'Elements affected: {} Link(s), {} Node(s), {} Institution(s).'
        ).format(len(links), len(nodes), len(insts))
        rule_message += elements_affected

        return rule_message

    def api_message(self):
        """
        Creates a message for return to the RPC API for running Rules
        (especially useful for testing).
        """
        (insts, nodes, links) = self._unique_affected_elements()
        actions = [{
            'action': al.action.action_type.name,
            'element': al.element.log_str,
            'message': al.message,
        } for al in self.action_logs]
        return {
            'rule': {
                'pk': self.rule.pk,
                'name': self.rule.name,
            },
            'matched_elements': {
                'type': self.rule.element_type,
                'quantity': len(self.matched_elements),
                'primary_keys': self.matched_elements,
            },
            'actions': actions,
            'affected': {
                'institutions': insts,
                'nodes': nodes,
                'links': links,
            }
        }
