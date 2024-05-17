"""
Copyright 2022 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext as _

from grenml_import.models import ImportFile, ImportData


logger = logging.getLogger()


# Currently allowed maxium upload size is 20MB.
# Django gives file size in Bytes. 1MB = 1048576 Bytes
MAX_UPLOAD_SIZE = 20971520


class ImportFileAdminForm(ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get('file')
        # Validate uploaded file size is within limit
        # and correct file type is uploaded
        if uploaded_file is not None and uploaded_file.name.endswith(('xlsx', 'xml')):
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                logger.debug('Uploaded file size is : "%s" ,'
                             ' which is larger than allowed 20MB file size ',
                             str(uploaded_file.size / 1048576)
                             )
                raise ValidationError(_(
                    'File size must not exceed 20 MB'
                ))
            else:
                """
                Validate if topology is provided or not only
                for excel files. For XML files topology name
                is not required as it is provided in the file.
                """
                topology_name = cleaned_data['topology_name']
                if uploaded_file.name.endswith('xlsx') and not bool(topology_name):
                    raise ValidationError(_(
                        'Please provide a topology name while importing.'
                    ))
        else:
            logger.debug('Invalid file uploaded. Uploaded file is : "%s"',
                         str(uploaded_file)
                         )
            raise ValidationError(_(
                'Please upload .xlsx or .xml extension files only'
            ))


@admin.register(ImportFile)
class ImportFile(admin.ModelAdmin):
    fields = (
        'file',
        'parent_topology',
        'topology_name',
        'import_message',
    )
    list_display = (
        'name',
        'source',
        'token_client_name',
        'import_state',
        'imported_at',
    )
    form = ImportFileAdminForm

    readonly_fields = ['import_message']

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

    def get_fields(self, request, obj=None):
        """
        This removes the file attribute from the change page, and
        the import_message field from the create page.

        Although the ImportFile instances are not editable,
        the presence of the file attribute creates a download link.
        We don't wnat to show it, because the file is not in persistent
        storage.  And the import_message field is read-only, so
        displaying it in the create form is just confusing.
        """
        fields = super().get_fields(request, obj)
        if obj:
            try:
                fields_list = list(fields)
                fields_list.remove('file')
                fields = tuple(fields_list)
            except ValueError:
                pass
        else:
            try:
                fields_list = list(fields)
                fields_list.remove('import_message')
                fields = tuple(fields_list)
            except ValueError:
                pass
        return fields


@admin.register(ImportData)
class ImportData(admin.ModelAdmin):

    fields = (
        'import_status',
        'import_message',
        'parent_topology',
        'grenml',
    )

    readonly_fields = [
        'grenml',
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def grenml(self, obj):
        if obj.grenml_data:
            return obj.grenml_data
        else:
            return _('(Empty!  GRENML data may have been purged to save database space.)')

    grenml.short_description = 'GRENML'
