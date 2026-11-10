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

Synopsis: The map's popups say how far to trust each network's data
and when it last changed, from the institution properties that
GRENML-Repository publishes.
"""
import json

import pytest
from grenml.managers import GRENMLManager

from chameleon_api import views
from grenml_import.importer import GRENMLImporter
from network_topology.models import Institution


VERIFIED = {
    'trust_level': 'verified',
    'verified_by': 'hugoromao',
    'verified_on': '2026-11-03',
    'data_updated_on': '2026-11-05',
    'data_updated_url': 'https://github.com/grenmap/GRENML-Repository/commit/abc123',
}


def import_topology(rnp_properties=None):
    manager = GRENMLManager(name='Topology')
    redclara = manager.add_institution(name='RedCLARA', latitude=0.0, longitude=0.0, tag='pren')
    rnp = manager.add_institution(
        name='RNP', latitude=0.0, longitude=0.0, tag='nren', **(rnp_properties or {}),
    )
    manager.set_primary_owner(redclara)
    manager.add_node(
        name='Boa Vista', latitude=2.82, longitude=-60.67, owners=[rnp], networks='RNP;RedCLARA',
    )
    import_log = GRENMLImporter().from_grenml_manager(manager)
    assert import_log.status[0] != import_log.IMPORT_STATUS_ABORTED, str(import_log)


def popup_institutions(rf):
    (location,) = json.loads(views.location(rf.get('/location/')).content)
    return {entry['name']: entry for entry in location['popup_institutions']}


@pytest.mark.django_db
def test_networks_without_popup_text_are_listed_as_ai_generated(rf):
    import_topology()

    entries = popup_institutions(rf)

    assert set(entries) == {'RNP', 'RedCLARA'}
    assert entries['RNP']['description'] == ''
    assert entries['RNP']['translations'] == []
    assert entries['RNP']['parent_menu'] == 2
    assert entries['RedCLARA']['parent_menu'] == 1
    for entry in entries.values():
        assert entry['trust_level'] == 'ai_generated'
        assert entry['verified_by'] is None
        assert entry['verified_on'] is None
        assert entry['data_updated_on'] is None
        assert entry['data_updated_url'] is None


@pytest.mark.django_db
def test_verified_network_and_update_date(rf):
    import_topology(VERIFIED)

    rnp = popup_institutions(rf)['RNP']

    for key, value in VERIFIED.items():
        assert rnp[key] == value


@pytest.mark.django_db
def test_reimport_updates_trust_level_and_keeps_popup(rf):
    import_topology()
    rnp = Institution.objects.get(name='RNP')
    rnp.popup_summary = 'Rede Nacional de Ensino e Pesquisa'
    rnp.save()

    import_topology(VERIFIED)

    entry = popup_institutions(rf)['RNP']
    assert entry['trust_level'] == 'verified'
    assert entry['description'] == 'Rede Nacional de Ensino e Pesquisa'


@pytest.mark.django_db
def test_verified_by_is_ignored_without_verified_trust_level(rf):
    import_topology({'trust_level': 'ai_generated', 'verified_by': 'someone'})

    rnp = popup_institutions(rf)['RNP']

    assert rnp['trust_level'] == 'ai_generated'
    assert rnp['verified_by'] is None


def test_settings_turn_on_the_data_notice(rf):
    (map_settings,) = json.loads(views.settings(rf.get('/settings/')).content)
    assert map_settings['data_notice_enabled'] is True
