"""
Copyright 2020 GRENMap Authors

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

Synopsis: polling URL Configuration
"""

from django.urls import path
from .views.api import *

urlpatterns = [
    # Trigger a poll of all active sources, a.k.a. a "batch"
    path(
        'polling/trigger/',
        trigger_batch_poll,
        name='polling-trigger-batch',
    ),

    # Test REST for polling sources
    path(
        'polling/test/sources/',
        sources,
        name='polling-sources',
    ),
    path(
        'polling/test/sources/<int:id>/',
        source_detail,
        name='polling-source-detail',
    ),

    # Test REST for polling event logs
    path(
        'polling/test/logs/batches/',
        batch_poll_event_logs,
        name='polling-log-batches',
    ),
    path(
        'polling/test/logs/batches/<int:id>/',
        batch_poll_event_log_detail,
        name='polling-log-batch-detail',
    ),

    # Test REST-like endpoints for toggling and changing
    # the automatic polling interval
    path(
        'polling/test/enabled/',
        automatic_polling_enabled,
        name='polling-enabled',
    ),
    path(
        'polling/test/enabled/<int:enable>/',
        automatic_polling_toggle,
        name='polling-toggle',
    ),
    path(
        'polling/test/interval/',
        automatic_polling_interval,
        name='polling-interval',
    ),

    # Test trigger for polling an individual source
    path(
        'polling/test/trigger/source/<int:id>/',
        trigger_source_poll,
        name='polling-trigger-source',
    ),
]
