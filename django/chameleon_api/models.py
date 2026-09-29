from django.conf import settings
from django.db import models

from network_topology.models import Institution


class InstitutionPopupTranslation(models.Model):
    """
    Translated copies of an Institution's popup_summary/popup_content,
    generated via LibreTranslate and cached here.
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='popup_translations',
    )
    language_code = models.CharField(max_length=10, choices=settings.LANGUAGES)
    summary = models.TextField(blank=True, default='')
    full_content = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('institution', 'language_code')

    def __str__(self):
        return f'{self.institution.name} popup [{self.language_code}]'


class UIString(models.Model):
    """
    A piece of fixed map interface vocabulary (e.g. button/label text)
    in its canonical English form, translatable via LibreTranslate.
    """
    key = models.SlugField(max_length=64, unique=True)
    text = models.CharField(max_length=256)

    class Meta:
        ordering = ('key',)

    def __str__(self):
        return f'{self.key} = "{self.text}"'


class UIStringTranslation(models.Model):
    """
    Translated copy of a UIString, generated via LibreTranslate and
    cached here.
    """
    ui_string = models.ForeignKey(
        UIString,
        on_delete=models.CASCADE,
        related_name='translations',
    )
    language_code = models.CharField(max_length=10, choices=settings.LANGUAGES)
    text = models.CharField(max_length=256, blank=True, default='')

    class Meta:
        unique_together = ('ui_string', 'language_code')

    def __str__(self):
        return f'{self.ui_string.key} [{self.language_code}]'
