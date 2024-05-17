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

Action type classes define the possible actions that Rules can apply on
matched elements in the map database.  This file defines the base class
that all action types should subclass.
"""


# Implementations of this base class should have their docstrings
# specified via the translated_docstring decorator.  This allows the UI
# to display the docstring inline in the Admin, and for the translation
# system to pick up the string for inclusion in the matrix.
# e.g. As follows:
# from django.utils.translation import gettext_noop
# from base_app.utils.decorators import translated_docstring
# @translated_docstring(gettext_noop(
#     """"
#     This ActionType has martial arts training and a thick accent.
#     """"
# ))
class BaseActionType:
    """
    Prototype of a class that applies actions in a Rule to a given
    element, usually either specified directly or matched by a
    subclass of BaseMatchType.

    *** This class should not be instantiated directly. ***

    Behaviours implemented in this prototype are meant to be universal;
    un-implemented methods are indicators of what should be implemented
    in every subclass.
    """
    # Friendly name for this type of action
    # Wrap this in no-op translation, e.g.
    #   from django.utils.translation import gettext_noop
    #   name = gettext_noop('My Action Name')
    name = None

    # One of: "Institution", "Node", "Link"
    # available via collation.constants.ElementTypes
    element_type = None

    # Input field names required in order to apply this type of action
    # Set to an empty list ("[]") if no info is required
    required_info = None

    # Input field names that may further adjust behaviour of the action
    # but are not strictly required.
    optional_info = []

    def __init__(self, action):
        """
        Accepts the Action that usually would spawn an
        instance of this class as a parameter in order to access
        its ActionInfos.
        Contains a check to ensure that any implementation has
        overridden the required properties above.
        """
        if (not self.name) or (not self.element_type) or (self.required_info is None):
            raise NotImplementedError(
                'BaseActionType subclass {} must specify all required properties.'.format(
                    self.__class__.__name__,
                )
            )
        self.action = action

    def apply(self, elements):
        """
        Implementation required for all subclasses.

        Apply this class's action to all qualifying elements specified
        in the parameter.

        Must return a tuple:
            1. Equivalent model object reference (in case some Actions
                effectively replace the object, such as with Replace
                With, or Merge Into varieties)
            2. ActionLog instance
        """
        raise NotImplementedError(
            'BaseActionType subclass {} must override the apply method.'.format(
                self.__class__.__name__,
            )
        )

    def validate_input(self, input_tuple_list):
        """
        Accepts a list of tuples provided as ActionInfo input.
        Each tuple in the list must be a key-value pair.
        Returns True if input matches required parameters.

        Example of input:
            [
                ('id', '567'),
                ('name_like', 'MyISP*'),
            ]

        Default implementation requires input info keys to contain
        every item in required_info, and for all input info keys to be
        represented in either required_ or optional_info.
        """
        input_keys = [item[0] for item in input_tuple_list]
        input_keys_set = set(input_keys)

        # Ensure required_info keys are all present in the input keys
        required_info = set(self.required_info if self.required_info is not None else [])
        required_info_validated = required_info.issubset(input_keys_set)

        # Ensure no required_info keys are duplicated
        if required_info_validated:
            key_occurrence_counts = dict((key, input_keys.count(key)) for key in input_keys)
            for key in required_info:
                if key_occurrence_counts[key] > 1:
                    required_info_validated = False

        # Ensure that all input keys are reflected in either
        # required_info or optional_info
        optional_info = set(self.optional_info if self.optional_info is not None else [])
        permissible_keys = required_info | optional_info
        input_keys_validated = input_keys_set.issubset(permissible_keys)

        return required_info_validated and input_keys_validated
