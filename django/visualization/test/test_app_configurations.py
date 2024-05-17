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

import unittest

from django.forms import ValidationError
from visualization.app_configurations import InitialCoordinatesSetting


class TestInitialCoordinatesSetting(unittest.TestCase):
    def setUp(self):
        self.setting = InitialCoordinatesSetting()
        super().setUp()

    def test_none(self):
        with self.assertRaises(ValidationError):
            self.setting.clean(None)

    def test_simple_invalid_string(self):
        with self.assertRaises(ValidationError):
            self.setting.clean('abcde')

    def test_number(self):
        with self.assertRaises(ValidationError):
            self.setting.clean(123)

    def test_tuple(self):
        with self.assertRaises(ValidationError):
            self.setting.clean((0, 0))

    def test_empty_pair(self):
        with self.assertRaises(ValidationError):
            self.setting.clean('()')

    def test_empty_pair_with_comma(self):
        with self.assertRaises(ValidationError):
            self.setting.clean('(,)')

    def test_only_latitude(self):
        with self.assertRaises(ValidationError):
            self.setting.clean('(0,)')

    def test_only_longitude(self):
        with self.assertRaises(ValidationError):
            self.setting.clean('(,0)')

    def test_no_parentheses(self):
        expected = '(0.0, 0.0)'
        actual = self.setting.clean('0,0')
        self.assertEqual(expected, actual)

    def test_only_left_parentheses(self):
        expected = '(0.0, 0.0)'
        actual = self.setting.clean('(0,0')
        self.assertEqual(expected, actual)

    def test_only_right_parentheses(self):
        expected = '(0.0, 0.0)'
        actual = self.setting.clean('0,0)')
        self.assertEqual(expected, actual)
