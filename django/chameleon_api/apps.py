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
        'REN Map topologies and institution descriptions come from different sources: '
        'some were provided by the institutions, others were extracted '
        'semi-automatically or with AI. Some information may be wrong, out of date '
        'or differ from official sources.'
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
        'Some topologies and institution descriptions were extracted '
        'semi-automatically or with AI. Click to read the full notice.'
    )),
    # Per-network badge: whether a representative of the institution has
    # confirmed its topology. It says nothing about where the data came
    # from (AI extraction or the institution itself): the notice covers
    # that, and a confirmed topology may still have been AI-extracted.
    # The repository's maintainers review all data either way. Keys
    # keep their old names (trust_ai_generated / trust_verified),
    # matching the trust_level values in the data. "Confirmed by" is
    # followed by who confirmed it and the date -- neither goes through
    # machine translation.
    ('trust_ai_generated', 'Unconfirmed'),
    # The notice's legend completes each badge on one line and says it
    # is about the topology (not the institution's description).
    ('trust_ai_generated_hint', 'topology reviewed by the maintainers'),
    ('trust_ai_generated_tooltip', (
        "The topology and the institution's description were reviewed by the "
        'maintainers, but not yet officially confirmed by a representative of the '
        'institution.'
    )),
    ('trust_verified', 'Confirmed'),
    ('trust_verified_hint', 'topology confirmed by the institution'),
    ('verified_by', 'Topology confirmed by'),
    # When the network's topology last changed; followed by the date.
    ('updated_on', 'Updated'),
    ('topology_updated_on', 'Topology updated'),
    ('view_latest_change', 'View latest change'),
]


# Hand-written translations that replace LibreTranslate's for these
# keys: its Portuguese comes out European ("Percebeste", "correcção")
# and some popup labels came out wrong ("pré-cheia"); REN Map's
# audience reads Brazilian Portuguese. Each must fit the 256-character
# UIStringTranslation.text column.
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
            'As topologias e descrições das instituições vêm de fontes diferentes: parte '
            'foi enviada pelas próprias instituições, parte extraída de forma '
            'semiautomática ou com IA. Algumas informações podem estar erradas, '
            'desatualizadas ou diferir das fontes oficiais.'
        ),
        'data_notice_levels': (
            'Cada rede mostra seu nível de confiança e quando sua topologia foi '
            'atualizada pela última vez. Encontrou algum erro? Use "Sugerir uma '
            'correção" em qualquer rede ou proponha uma correção no GitHub.'
        ),
        'data_notice_reminder': 'Dados parcialmente extraídos por IA',
        'data_notice_reminder_hint': (
            'Parte das topologias e das descrições das instituições foi extraída de '
            'forma semiautomática ou com IA. Clique para ler o aviso completo.'
        ),
        'trust_ai_generated': 'Não confirmado',
        'trust_ai_generated_hint': 'topologia revisada pelos mantenedores',
        'trust_ai_generated_tooltip': (
            'A topologia e a descrição da instituição foram revisadas pelos mantenedores, '
            'mas ainda não foram confirmadas oficialmente por um representante da '
            'instituição.'
        ),
        'trust_verified': 'Confirmado',
        'trust_verified_hint': 'topologia confirmada pela instituição',
        'topology_updated_on': 'Topologia atualizada em',
        'verified_by': 'Topologia confirmada por',
    },
    # The notice's body runs past the 256-character column when
    # LibreTranslate translates it into these two languages, and it
    # mistranslated "AI-extracted" ("extraites de l'IA", "por AI").
    'es': {
        'data_notice_body': (
            'Las topologías y las descripciones de las instituciones vienen de distintas '
            'fuentes: parte enviada por las instituciones, parte extraída de forma '
            'semiautomática o con IA. Puede haber información errónea, desactualizada o '
            'distinta de las fuentes oficiales.'
        ),
        'trust_ai_generated': 'No confirmado',
        'trust_ai_generated_hint': 'topología revisada por los mantenedores',
        'trust_ai_generated_tooltip': (
            'La topología y la descripción de la institución fueron revisadas por los '
            'mantenedores, pero aún no han sido confirmadas oficialmente por un '
            'representante de la institución.'
        ),
        'trust_verified': 'Confirmado',
        'trust_verified_hint': 'topología confirmada por la institución',
        'topology_updated_on': 'Topología actualizada el',
        'verified_by': 'Topología confirmada por',
        'data_notice_reminder': 'Datos extraídos en parte con IA',
        'data_notice_reminder_hint': (
            'Algunas topologías y descripciones de las instituciones se extrajeron de '
            'forma semiautomática o con IA. Haga clic para leer el aviso completo.'
        ),
    },
    'fr': {
        'data_notice_body': (
            'Les topologies et descriptions des institutions viennent de sources '
            'différentes : en partie fournies par les institutions, en partie extraites de '
            'façon semi-automatique ou par IA. Elles peuvent être erronées, obsolètes ou '
            'différer des sources officielles.'
        ),
        'data_notice_reminder': 'Données extraites en partie par IA',
        'trust_ai_generated': 'Non confirmé',
        'trust_ai_generated_hint': 'topologie relue par les mainteneurs',
        'trust_ai_generated_tooltip': (
            "La topologie et la description de l'institution ont été relues par les "
            'mainteneurs, mais pas encore confirmées officiellement par un représentant '
            "de l'institution."
        ),
        'trust_verified': 'Confirmé',
        'trust_verified_hint': "topologie confirmée par l'institution",
        'topology_updated_on': 'Topologie mise à jour le',
        'verified_by': 'Topologie confirmée par',
        'data_notice_reminder_hint': (
            'Certaines topologies et descriptions des institutions ont été extraites de '
            "façon semi-automatique ou par IA. Cliquez pour lire l'avis complet."
        ),
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
