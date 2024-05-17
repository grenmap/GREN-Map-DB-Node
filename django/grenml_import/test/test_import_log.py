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

------------------------------------------------------------------------

Synopsis: unit tests for the import log classes
"""

import pytest

from collation.constants import ElementTypes
from grenml_import.utils.import_log import ImportElementTypeLog
from grenml_import.utils.import_exceptions import ImportWarning


@pytest.mark.django_db
class TestImportElementTypeLog:
    """
    This class contains tests for the ImportElementTypeLog class.
    """

    @pytest.fixture
    def sample_import_element_type_log(self):
        """
        Instantiates the ImportLog class and simulates import with:
            - 5 elements imported
            - 1 element skipped
            - 3 total info messages, two of which are for one elem
            - 2 total warnings
        """
        ietl = ImportElementTypeLog(ElementTypes.NODE)
        ietl.log_imported('A', 0)
        ietl.log_imported('B', 1)
        ietl.log_imported('C', 2, info_messages=['message 1', 'message 2'])
        ietl.log_imported('D', 3, info_messages=['message 3'])
        ietl.log_imported('E', 4, warnings=[ImportWarning('oops')])
        ietl.log_skipped('F', warnings=[ImportWarning('skipped')])
        return ietl

    def test_encountered(self, sample_import_element_type_log):
        assert sample_import_element_type_log.encountered == 6

    def test_imported(self, sample_import_element_type_log):
        assert sample_import_element_type_log.imported == 5

    def test_info_messages(self, sample_import_element_type_log):
        assert len(sample_import_element_type_log.info_messages) == 3

    def test_warning_messages(self, sample_import_element_type_log):
        assert len(sample_import_element_type_log.warning_messages) == 2

    def test_update(self, sample_import_element_type_log):
        # Omit an info message and add a warning
        # Note that messages cannot be 'removed' by omitting them;
        # update_log simply adds messages to the lists
        sample_import_element_type_log.update_log(
            'D',
            3,
            info_messages=[],
            warnings=[ImportWarning('achtung')],
        )
        # Confirm no change
        assert sample_import_element_type_log.encountered == 6
        # Confirm no change
        assert sample_import_element_type_log.imported == 5
        # Confirm info, warning messages contain new values as expected
        assert len(sample_import_element_type_log.info_messages) == 3
        assert len(sample_import_element_type_log.warning_messages) == 3

        # Add primary key to previously-skipped element,
        # making it an imported instead of skipped element
        # Note that the new ImportWarning should append, even though
        # it is identical to the one already there.
        sample_import_element_type_log.update_log(
            'F',
            5,
            warnings=[ImportWarning('skipped')],
        )
        # Confirm no change
        assert sample_import_element_type_log.encountered == 6
        # Confirm reflected
        assert sample_import_element_type_log.imported == 6
        # Confirm warning appended
        assert len(sample_import_element_type_log.warning_messages) == 4
