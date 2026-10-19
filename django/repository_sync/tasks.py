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

Synopsis: Download the GRENML file published by a repository (by
default the RENMAP topology in grenmap/GRENML-Repository) and import it
when it has changed since the last successful import.
"""
import hashlib
import logging

import requests
from django.conf import settings
from django.db import DatabaseError, transaction
from django.utils import timezone

from grenml_import.models import ImportAborted, ImportData
from network_topology.models import Topology
from repository_sync.models import RepositorySyncState
from repository_sync.scheduling import URL_SETTING, get_setting, sync_enabled


log = logging.getLogger(__name__)

# Returned by sync_repository; also handy in logs and tests.
RESULT_DISABLED = 'disabled'
RESULT_BUSY = 'busy'


def sync_repository(force=False):
    """
    Scheduled task. Imports the GRENML file at the configured URL if
    its content differs from the last successful import. "force" skips
    the enabled check (used by the admin's "sync now" action) but not
    the change check.

    Returns the resulting status (see RepositorySyncState), or
    RESULT_DISABLED / RESULT_BUSY when nothing was attempted.
    """
    if not force and not sync_enabled():
        log.debug('GRENML repository sync is disabled')
        return RESULT_DISABLED

    url = get_setting(URL_SETTING)
    RepositorySyncState.get()

    # The row lock keeps two runs (e.g. a slow import overlapping the
    # next scheduled one) from importing at the same time.
    with transaction.atomic():
        try:
            state = RepositorySyncState.objects.select_for_update(nowait=True).get(
                pk=RepositorySyncState.SINGLETON_PK,
            )
        except DatabaseError:
            log.info('GRENML repository sync already running; skipping this run')
            return RESULT_BUSY
        _sync(state, url)
        state.source_url = url
        state.last_checked_at = timezone.now()
        state.save()
        return state.last_status


def _sync(state, url):
    """Download, compare and import; records the outcome on state."""
    try:
        response = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error(f'GRENML repository sync could not download {url}: {e}')
        state.last_status = RepositorySyncState.STATUS_DOWNLOAD_FAILED
        state.last_message = str(e)
        return

    content = response.content
    sha256 = hashlib.sha256(content).hexdigest()
    if sha256 == state.last_sha256:
        log.debug('GRENML repository file unchanged')
        state.last_status = RepositorySyncState.STATUS_UNCHANGED
        state.last_message = ''
        return

    log.info(f'GRENML repository file changed (sha256 {sha256}); importing')
    import_data = ImportData.objects.create(
        source=f'{url[:240]}@{sha256[:12]}',
        grenml_data=content.decode('utf-8', errors='replace'),
    )
    state.last_import = import_data
    try:
        import_data.execute_import(parent_topology=Topology.objects.get_main_topology())
    except ImportAborted as e:
        # last_sha256 is left alone, so the next run retries.
        log.error(f'GRENML repository import failed: {e}')
        state.last_status = RepositorySyncState.STATUS_IMPORT_FAILED
        state.last_message = import_data.import_message or str(e)
        return

    state.last_sha256 = sha256
    state.last_imported_at = timezone.now()
    state.last_status = RepositorySyncState.STATUS_IMPORTED
    state.last_message = import_data.import_message
    log.info('GRENML repository import finished')
