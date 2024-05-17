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
for data polling source models.
"""

from rest_framework import serializers

from polling.models.sources import PollingSource


class PollingSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollingSource
        fields = [
            'id',
            'name',
            'protocol',
            'hostname',
            'port',
            'path',
            'url',  # computed field
            'status_url',  # computed field
            'polling_url',  # computed field
            'active',
        ]
        read_only_fields = [
            'id',
            'url',
            'status_url',
            'polling_url',
        ]
