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

Synopsis: Re-importing a topology must keep the popup texts entered
in the admin, and their cached translations.
"""
import pytest

from grenml.managers import GRENMLManager

from chameleon_api.models import InstitutionPopupTranslation as ChameleonTranslation
from grenml_import.importer import GRENMLImporter
from grenml_import.models import ImportAborted, ImportData
from network_topology.models import Institution
from visualization.models import InstitutionPopupTranslation as VisualizationTranslation


SUMMARY = 'Rede Nacional de Ensino e Pesquisa'
CONTENT = '<p>Brazilian NREN</p>'


def make_manager(institution_name='RNP'):
    manager = GRENMLManager(name='Topology')
    owner = manager.add_institution(name=institution_name, latitude=0.0, longitude=0.0)
    manager.set_primary_owner(owner)
    manager.add_node(name='Boa Vista', latitude=2.82, longitude=-60.67, owners=[owner])
    return manager


def import_manager(manager):
    import_log = GRENMLImporter().from_grenml_manager(manager)
    assert import_log.status[0] != import_log.IMPORT_STATUS_ABORTED, str(import_log)


def add_popup(institution):
    institution.popup_summary = SUMMARY
    institution.popup_content = CONTENT
    institution.save()
    for model in (VisualizationTranslation, ChameleonTranslation):
        model.objects.create(
            institution=institution, language_code='pt',
            summary='Resumo', full_content='<p>Conteúdo</p>',
        )


@pytest.mark.django_db
def test_reimport_keeps_popup_and_translations():
    import_manager(make_manager())
    original = Institution.objects.get(name='RNP')
    add_popup(original)

    import_manager(make_manager())

    institution = Institution.objects.get(name='RNP')
    # The importer creates a new row and deletes the old one; the popup
    # must have moved over rather than been deleted with it.
    assert institution.pk != original.pk
    assert institution.popup_summary == SUMMARY
    assert institution.popup_content == CONTENT
    assert list(
        institution.visualization_popup_translations.values_list('language_code', flat=True)
    ) == ['pt']
    assert list(institution.popup_translations.values_list('language_code', flat=True)) == ['pt']
    assert institution.elements.filter(name='Boa Vista').exists()


@pytest.mark.django_db
def test_renamed_institution_starts_without_popup():
    import_manager(make_manager('RNP'))
    add_popup(Institution.objects.get(name='RNP'))

    import_manager(make_manager('Rede Nacional'))

    assert not Institution.objects.filter(name='RNP').exists()
    renamed = Institution.objects.get(name='Rede Nacional')
    assert renamed.popup_summary == ''
    assert VisualizationTranslation.objects.count() == 0
    assert ChameleonTranslation.objects.count() == 0


@pytest.mark.django_db
def test_replace_with_keeps_the_replacements_own_popup():
    old = Institution.objects.create(name='RNP', latitude=0.0, longitude=0.0)
    add_popup(old)
    new = Institution.objects.create(
        name='RNP', latitude=0.0, longitude=0.0,
        popup_summary='Newer summary', popup_content='<p>Newer</p>',
    )

    old.replace_with(new)

    new.refresh_from_db()
    assert new.popup_summary == 'Newer summary'
    assert new.popup_content == '<p>Newer</p>'
    # The old translations were of the old texts, so they go with it.
    assert new.visualization_popup_translations.count() == 0
    assert new.popup_translations.count() == 0


@pytest.mark.django_db
def test_replace_with_does_not_duplicate_existing_translation_languages():
    old = Institution.objects.create(name='RNP', latitude=0.0, longitude=0.0)
    add_popup(old)
    new = Institution.objects.create(name='RNP', latitude=0.0, longitude=0.0)
    VisualizationTranslation.objects.create(
        institution=new, language_code='pt', summary='Already here',
    )

    old.replace_with(new)

    translations = new.visualization_popup_translations.all()
    assert [t.summary for t in translations] == ['Already here']
    assert new.popup_translations.count() == 1


@pytest.mark.django_db
def test_import_data_reports_parse_errors():
    import_data = ImportData.objects.create(source='test', grenml_data='<not grenml')
    with pytest.raises(ImportAborted):
        import_data.execute_import()
    import_data.refresh_from_db()
    assert import_data.import_status.startswith('3')
    assert 'UnboundLocalError' not in import_data.import_message
    assert import_data.import_message
