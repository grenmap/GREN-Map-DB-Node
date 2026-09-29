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
"""

from django.contrib import admin
from .models import *


# Register polling source model
@admin.register(VisualizationAllowedOrigin)
class VisualizationAllowedOriginAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin')


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
