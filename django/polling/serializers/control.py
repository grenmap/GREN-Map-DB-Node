"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2023 GRENMap Authors

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

Synopsis: This file contains the Django REST Framework model serializers
for data polling event logs.
"""

from rest_framework import serializers

from grenml_import.serializers import ImportDataSerializer
from polling.models.control import PollImport, BatchPollImport
from polling.serializers.sources import PollingSourceSerializer


class PollImportSerializer(serializers.ModelSerializer):
    polling_source = PollingSourceSerializer()
    grenml_data_import = ImportDataSerializer()

    class Meta:
        model = PollImport
        fields = [
            'id',
            'batch_poll_import',
            'polling_source',
            'status',
            'status_message',
            'poll_datetime',
            'poll_duration_seconds',
            'import_datetime',
            'import_duration_seconds',
            'grenml_data_import',
            '__str__',  # computed field
        ]
        read_only_fields = [
            'id',
            'batch_poll_import',
            'status',
            'status_message',
            'poll_datetime',
            'poll_duration_seconds',
            'import_datetime',
            'import_duration_seconds',
            'grenml_data_import',
            '__str__',
        ]


class BatchPollImportSerializer(serializers.ModelSerializer):

    class Meta:
        model = BatchPollImport
        fields = [
            'id',
            'was_scheduled',
            'timestamp',
            'duration_seconds',
            'status',
            '__str__',  # computed field
        ]
        read_only_fields = [
            'id',
            'was_scheduled',
            'timestamp',
            'duration_seconds',
            'status',
            '__str__',
        ]


class BatchPollImportDetailSerializer(BatchPollImportSerializer):
    polls = PollImportSerializer(many=True)

    class Meta:
        model = BatchPollImport
        fields = [
            'id',
            'was_scheduled',
            'timestamp',
            'duration_seconds',
            'status',
            '__str__',  # computed field
            'polls',
        ]
        read_only_fields = [
            'id',
            'was_scheduled',
            'timestamp',
            'duration_seconds',
            'status',
            '__str__',
        ]
