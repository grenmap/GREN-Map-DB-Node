"""
Copyright 2026 GRENMap Authors

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
from unittest import mock

import pytest
import requests
from django_q.models import Schedule

from grenml.managers import GRENMLManager

from base_app.models.app_configurations import AppConfiguration
from grenml_import.models import ImportData
from network_topology.models import Institution, Node, Topology
from repository_sync import tasks
from repository_sync.models import RepositorySyncState
from repository_sync.scheduling import (
    ENABLED_SETTING, INTERVAL_SETTING, SYNC_JOB_NAME, schedule_sync,
)


def make_grenml(*node_names):
    manager = GRENMLManager(name='Topology')
    owner = manager.add_institution(name='RNP', latitude=0.0, longitude=0.0)
    manager.set_primary_owner(owner)
    # Coordinates start at 1: the grenml writer drops a 0.0 coordinate,
    # producing a Node without Location that fails schema validation.
    for i, name in enumerate(node_names, start=1):
        manager.add_node(name=name, latitude=float(i), longitude=float(i), owners=[owner])
    return manager.write_to_string().encode('utf-8')


def response(content=b'', status_code=200):
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = content
    resp.url = 'https://example.org/topologies.xml'
    return resp


def set_setting(name, value):
    AppConfiguration.objects.update_or_create(
        name=name, defaults={'value': value, 'display_name': name},
    )


@pytest.fixture
def enabled(db):
    set_setting(ENABLED_SETTING, 'True')


@pytest.fixture
def get():
    with mock.patch('repository_sync.tasks.requests.get') as patched:
        yield patched


@pytest.mark.django_db
def test_disabled_does_nothing(get):
    assert tasks.sync_repository() == tasks.RESULT_DISABLED
    get.assert_not_called()


@pytest.mark.django_db
def test_force_runs_even_when_disabled(get):
    get.return_value = response(make_grenml('Manaus'))
    assert tasks.sync_repository(force=True) == RepositorySyncState.STATUS_IMPORTED
    assert Node.objects.filter(name='Manaus').exists()


def test_first_run_imports(enabled, get):
    get.return_value = response(make_grenml('Manaus', 'Belem'))

    assert tasks.sync_repository() == RepositorySyncState.STATUS_IMPORTED

    assert set(Node.objects.values_list('name', flat=True)) == {'Manaus', 'Belem'}
    state = RepositorySyncState.get()
    assert len(state.last_sha256) == 64
    assert state.last_imported_at is not None
    assert state.last_import == ImportData.objects.get()
    assert Topology.objects.get(name='Topology').main


def test_unchanged_file_is_not_imported_again(enabled, get):
    get.return_value = response(make_grenml('Manaus'))
    tasks.sync_repository()

    assert tasks.sync_repository() == RepositorySyncState.STATUS_UNCHANGED
    assert ImportData.objects.count() == 1


def test_changed_file_replaces_topology_and_keeps_popup(enabled, get):
    get.return_value = response(make_grenml('Manaus', 'Belem'))
    tasks.sync_repository()
    rnp = Institution.objects.get(name='RNP')
    rnp.popup_summary = 'Summary'
    rnp.popup_content = '<p>Content</p>'
    rnp.save()

    get.return_value = response(make_grenml('Manaus', 'Macapa'))
    assert tasks.sync_repository() == RepositorySyncState.STATUS_IMPORTED

    assert set(Node.objects.values_list('name', flat=True)) == {'Manaus', 'Macapa'}
    assert Topology.objects.filter(name='Topology').count() == 1
    rnp = Institution.objects.get(name='RNP')
    assert (rnp.popup_summary, rnp.popup_content) == ('Summary', '<p>Content</p>')


@pytest.mark.parametrize('failure', [
    requests.exceptions.ConnectionError('connection refused'),
    requests.exceptions.Timeout('timed out'),
    response(b'Not Found', status_code=404),
])
def test_download_failure_keeps_previous_state(enabled, get, failure):
    get.return_value = response(make_grenml('Manaus'))
    tasks.sync_repository()
    previous_sha = RepositorySyncState.get().last_sha256

    if isinstance(failure, Exception):
        get.side_effect = failure
    else:
        get.return_value = failure
    assert tasks.sync_repository() == RepositorySyncState.STATUS_DOWNLOAD_FAILED

    state = RepositorySyncState.get()
    assert state.last_sha256 == previous_sha
    assert state.last_message
    assert Node.objects.filter(name='Manaus').exists()


def test_invalid_grenml_keeps_topology_and_retries(enabled, get):
    get.return_value = response(make_grenml('Manaus'))
    tasks.sync_repository()
    previous_sha = RepositorySyncState.get().last_sha256

    get.return_value = response(b'<grenml:Topology this is not xml')
    assert tasks.sync_repository() == RepositorySyncState.STATUS_IMPORT_FAILED
    state = RepositorySyncState.get()
    assert state.last_sha256 == previous_sha
    assert state.last_message
    assert Node.objects.filter(name='Manaus').exists()

    # Not recorded as imported, so the same broken file is tried again
    # (and fails again) instead of being reported as unchanged.
    assert tasks.sync_repository() == RepositorySyncState.STATUS_IMPORT_FAILED


@pytest.mark.django_db
def test_schedule_sync_replaces_the_job():
    schedule_sync(5)
    schedule_sync(7)

    job = Schedule.objects.get(name=SYNC_JOB_NAME)
    assert job.func == 'repository_sync.tasks.sync_repository'
    assert job.schedule_type == Schedule.MINUTES
    assert job.minutes == 7


@pytest.mark.django_db
def test_saving_the_interval_setting_reschedules():
    set_setting(INTERVAL_SETTING, '15')
    assert Schedule.objects.get(name=SYNC_JOB_NAME).minutes == 15
