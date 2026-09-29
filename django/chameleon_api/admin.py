from django.contrib import admin

from .models import InstitutionPopupTranslation, UIString, UIStringTranslation


@admin.register(InstitutionPopupTranslation)
class InstitutionPopupTranslationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'language_code', 'summary')
    list_filter = ('language_code',)
    search_fields = ('institution__name', 'summary', 'full_content')


class UIStringTranslationInline(admin.TabularInline):
    model = UIStringTranslation
    extra = 0


@admin.register(UIString)
class UIStringAdmin(admin.ModelAdmin):
    list_display = ('key', 'text')
    search_fields = ('key', 'text')
    inlines = [UIStringTranslationInline]
