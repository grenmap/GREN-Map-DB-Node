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

import io
import published_network_data.models.models as models

from django.contrib import admin
from django.http import FileResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


@admin.register(models.PublishedNetworkData)
class PublishedNetworkData(admin.ModelAdmin):
    fields = ('name', 'grenml_export_description')
    list_display = (
        'name',
        'version',
        'file_date',
        'published_state',
        'grenml_export_description',
        'download_button',
    )

    readonly_fields = ['file_date']

    def has_delete_permission(self, request, obj=None):
        """
        Prevents users from deleting submitted records
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Prevents users from editing submitted records
        """
        return False

    def download_button(self, obj):
        """ This renders a download button for each published file. """
        if obj.published_status == "success":
            return format_html(
                '<a class="button" href="{}">{}</a>',
                reverse('admin:download-published-data', args=[obj.id]),
                _('Download'),
            )

        return format_html(
            '<a class="button" href="{}" style="pointer-events: none;" disabled>{}</a>',
            reverse('admin:download-published-data', args=[obj.id]),
            _('Download'),
        )

    download_button.short_description = _('Actions')

    def get_urls(self):
        """
        Override the get_urls function to add the URLs needed for
        the admin button actions
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                '<file_id>/download/',
                self.download_action,
                name='download-published-data'
            ),
        ]
        return custom_urls + urls

    def download_action(self, request, file_id):
        """
        Handler for the download endpoint declared
        in the get_urls method.
        """
        published_data = models.PublishedNetworkData.objects.get(id=file_id)
        return FileResponse(
            io.BytesIO(published_data.file_contents.encode()),
            as_attachment=True,
            filename='published_data_{}.xml'.format(
                published_data.version,
            ),
        )
