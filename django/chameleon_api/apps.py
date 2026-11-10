from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


INITIAL_UI_STRINGS = [
    ('link_details', 'Link Details'),
    ('connected_to', 'Connected to:'),
    ('managed_by', 'Managed by:'),
    ('close', 'Close'),
    # Split in two (rather than one "Owned by {n} institutions" string)
    # so the institution count never sits inside machine-translated
    # text, where a placeholder could get mistranslated or reordered.
    ('owned_by', 'Owned by'),
    ('institutions_plural', 'institutions'),
    # Popup modal footer. The prompt is followed by the institution
    # name and a "?" -- names are never sent to machine translation.
    ('report_correction_prompt', 'Something wrong or outdated in the information about'),
    ('report_correction', 'Report a correction'),
    ('report_correction_hint', 'Opens your email app with the institution pre-filled'),
    # Notice on the first visit about where the data comes from (partly
    # from the institutions, partly extracted semi-automatically or with
    # AI), and the reminder that reopens it.
    ('data_notice_title', 'About the data on this map'),
    ('data_notice_body', (
        'REN Map topologies come from different sources: some were provided by '
        'the institutions, others were extracted semi-automatically or with AI. '
        'Some information may be wrong, out of date or differ from official sources.'
    )),
    ('data_notice_levels', (
        'Every network shows its level and when its topology was last updated. '
        'Spotted a mistake? Use "Report a correction" in any network, or propose '
        'a fix on GitHub.'
    )),
    ('data_notice_learn_more', 'How the data is maintained'),
    ('data_notice_dismiss', 'Got it'),
    ('data_notice_reminder', 'Partly AI-extracted data'),
    ('data_notice_reminder_hint', (
        'Some topologies were extracted semi-automatically or with AI. '
        'Click to read the full notice.'
    )),
    # Per-network trust badge. "Verified by" is followed by who verified
    # it and the date -- neither goes through machine translation.
    ('trust_ai_generated', 'AI-generated'),
    ('trust_ai_generated_hint', 'extracted automatically, not yet checked'),
    ('trust_ai_generated_tooltip', (
        "This data was extracted automatically and hasn't been reviewed by a person yet."
    )),
    ('trust_verified', 'Verified'),
    # Reviews mostly come from people at the other participating
    # institutions, not from the network's own.
    ('trust_verified_hint', 'reviewed by a member of a participating institution'),
    ('verified_by', 'Verified by'),
    # When the network's topology last changed; followed by the date.
    ('updated_on', 'Updated'),
    ('topology_updated_on', 'Topology updated'),
    ('view_latest_change', 'View latest change'),
]


# Hand-written translations that replace LibreTranslate's for these
# keys: its Portuguese comes out European ("Percebeste", "correcção")
# and some popup labels came out wrong ("pré-cheia"). REN Map's
# audience reads Brazilian Portuguese.
CURATED_TRANSLATIONS = {
    'pt': {
        'connected_to': 'Conectado a:',
        'link_details': 'Detalhes do enlace',
        'managed_by': 'Gerenciado por:',
        'report_correction_prompt': 'Algo errado ou desatualizado nas informações sobre',
        'report_correction': 'Sugerir uma correção',
        'report_correction_hint': 'Abre seu aplicativo de e-mail com a instituição já preenchida',
        'data_notice_title': 'Sobre os dados deste mapa',
        'data_notice_body': (
            'As topologias do REN Map vêm de fontes diferentes: algumas foram enviadas '
            'pelas próprias instituições, outras foram extraídas de forma semiautomática '
            'ou com IA. Algumas informações podem estar erradas, desatualizadas ou '
            'diferir das fontes oficiais.'
        ),
        'data_notice_levels': (
            'Cada rede mostra seu nível de confiança e quando sua topologia foi '
            'atualizada pela última vez. Encontrou algum erro? Use "Sugerir uma '
            'correção" em qualquer rede ou proponha uma correção no GitHub.'
        ),
        'data_notice_reminder': 'Dados parcialmente extraídos por IA',
        'data_notice_reminder_hint': (
            'Parte das topologias foi extraída de forma semiautomática ou com IA. '
            'Clique para ler o aviso completo.'
        ),
        'trust_ai_generated_tooltip': (
            'Estes dados foram extraídos automaticamente e ainda não foram '
            'revisados por uma pessoa.'
        ),
        'trust_verified_hint': 'revisado por um membro de uma instituição participante',
    },
}


def seed_ui_strings(sender, **kwargs):
    """
    Ensures the fixed map interface vocabulary exists and matches
    INITIAL_UI_STRINGS. Connected to post_migrate (rather than done as
    a data migration) because the dev entrypoint runs "manage.py flush"
    on every container start, which clears table data without
    unmarking migrations as applied -- a data migration's RunPython
    would then never run again. post_migrate fires after every
    "migrate" call, including the one that follows that flush, so this
    survives it.

    A string whose English text changed here is updated, and its cached
    machine translations are dropped (they translated the old text) so
    they're regenerated on the next request. CURATED_TRANSLATIONS are
    then written over whatever is cached for their keys.
    """
    from .models import UIString, UIStringTranslation

    for key, text in INITIAL_UI_STRINGS:
        ui_string, created = UIString.objects.get_or_create(key=key, defaults={'text': text})
        if not created and ui_string.text != text:
            ui_string.text = text
            ui_string.save(update_fields=['text'])
            ui_string.translations.all().delete()

    configured = {code for code, _label in settings.LANGUAGES}
    for language_code, texts in CURATED_TRANSLATIONS.items():
        if language_code not in configured:
            continue
        for key, text in texts.items():
            ui_string = UIString.objects.filter(key=key).first()
            if ui_string is None:
                continue
            UIStringTranslation.objects.update_or_create(
                ui_string=ui_string, language_code=language_code,
                defaults={'text': text},
            )


class ChameleonApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chameleon_api'

    def ready(self):
        super().ready()
        post_migrate.connect(seed_ui_strings, sender=self)
