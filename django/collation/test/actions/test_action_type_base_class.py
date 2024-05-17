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
import pytest

from collation.action_types import BaseActionType
from collation.constants import ElementTypes
from collation.models import Action


class EmptyDummyActionType(BaseActionType):
    """
    Makes a concrete ActionType class out of BaseActionType,
    in order to test its methods.
    """
    name = 'Test Action With No Required Or Optional Info'
    element_type = ElementTypes.LINK
    required_info = []

    def apply(self, element):
        """
        Null action.
        """
        return (None, None)


class RequiredInfoDummyActionType(BaseActionType):
    """
    Makes a concrete ActionType class out of BaseActionType,
    in order to test its methods.  This one has required_info
    fields.
    """
    name = 'Test Action With Required Info Only'
    element_type = ElementTypes.LINK
    required_info = ['info1', 'info2']

    def apply(self, element):
        """
        Null action.
        """
        return (None, None)


class OptionalInfoDummyActionType(BaseActionType):
    """
    Makes a concrete ActionType class out of BaseActionType,
    in order to test its methods.  This one has optional_info
    fields.
    """
    name = 'Test Action With Optional Info Only'
    element_type = ElementTypes.LINK
    required_info = []
    optional_info = ['info3']

    def apply(self, element):
        """
        Null action.
        """
        return (None, None)


class BothInfoDummyActionType(BaseActionType):
    """
    Makes a concrete ActionType class out of BaseActionType,
    in order to test its methods.  This one has required_info
    and optional_info fields.
    """
    name = 'Test Action With Both Requird and Optional Info'
    element_type = ElementTypes.LINK
    required_info = ['info1', 'info2']
    optional_info = ['info3']

    def apply(self, element):
        """
        Null action.
        """
        return (None, None)


class TestActionTypeBaseClass:
    """
    This class contains tests for the ActionType base class.
    """

    @pytest.fixture
    def two_correct_required_infos(self):
        return [
            ('info1', 'testval'),
            ('info2', 'testval'),
        ]

    @pytest.fixture
    def one_correct_optional_info(self):
        return [
            ('info3', 'testval'),
        ]

    def test_no_required_or_optional_info(
        self,
        two_correct_required_infos,
    ):
        """
        Confirms that input to an ActionType with no supported
        required or optional ActionInfos is validated correctly.
        """
        action_type = EmptyDummyActionType(Action())

        # It should validate when no ActionInfos (as a list of tuples)
        # are provided.
        assert action_type.validate_input([])

        # It should not validate when ActionInfos are provided
        assert not action_type.validate_input(two_correct_required_infos)

    def test_required_info_matches_exactly(
        self,
        two_correct_required_infos,
        one_correct_optional_info,
    ):
        """
        Confirms that input to an ActionType with required ActionInfos
        but no optional ActionInfos is validated correctly.
        """
        action_type = RequiredInfoDummyActionType(Action())

        # It should validate when the correct required ActionInfos
        # are provided.
        assert action_type.validate_input(two_correct_required_infos)

        # It should not validate when no ActionInfos are provided
        assert not action_type.validate_input([])

        # It should not validate when only a subset of the correct
        # required ActionInfos are provided.
        assert not action_type.validate_input(two_correct_required_infos[0:1])

        # It should not validate when more than the correct required
        # ActionInfos are provided.
        three_infos = two_correct_required_infos + one_correct_optional_info
        assert not action_type.validate_input(three_infos)

    def test_optional_info_matches_optionally(
        self,
        one_correct_optional_info,
    ):
        """
        Confirms that input to an ActionType with no required
        ActionInfos but an optional ActionInfo is validated correctly.
        """
        action_type = OptionalInfoDummyActionType(Action())

        # It should validate when the correct required ActionInfos
        # are provided.
        assert action_type.validate_input(one_correct_optional_info)

        # It should still validate when no ActionInfos are provided
        assert action_type.validate_input([])

        # It should not validate when a random ActionInfo is provided
        assert not action_type.validate_input([('random_key', 'random_val')])

        # It should not validate when both a correct optional and a
        # random ActionInfo are provided.
        infos = one_correct_optional_info + [('random_key', 'random_val')]
        assert not action_type.validate_input(infos)

    def test_required_and_optional_info_matches(
        self,
        two_correct_required_infos,
        one_correct_optional_info,
    ):
        """
        Confirms that input to an ActionType with required ActionInfos
        and optional ActionInfos is validated correctly.
        """
        action_type = BothInfoDummyActionType(Action())

        # It should validate when the correct required ActionInfos
        # are provided.
        assert action_type.validate_input(two_correct_required_infos)

        # It should not validate when no ActionInfos are provided
        assert not action_type.validate_input([])

        # It should not validate when only optional ActionInfos
        # are provided.
        assert not action_type.validate_input(one_correct_optional_info)

        # It should validate when correct required and optional
        # ActionInfos are provided.
        infos = two_correct_required_infos + one_correct_optional_info
        assert action_type.validate_input(infos)

        # It should not validate when both correct required and a random
        # ActionInfo are provided.
        infos = two_correct_required_infos + [('random_key', 'random_val')]
        assert not action_type.validate_input(infos)
