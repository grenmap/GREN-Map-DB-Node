"""
Copyright 2022 GRENMap Authors

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

import logging

from django.contrib import admin, messages
from django.forms import ModelForm, ValidationError
from django.utils.translation import gettext as _, gettext_lazy
from django_q.tasks import async_task

from .models import BaseModel, Location, Lifetime, Link, Institution, Node, Property, Topology
from grenml import models as grenml_models
from collation.models import Ruleset


log = logging.getLogger()


admin.site.site_title = gettext_lazy('GREN Administration Portal')
MESSAGE_APPLY_ALL_RULESETS = _('Applying Collation rules. Please note: \
    this could result in this Element being modified post add or edit.')


class AutoIDForm(ModelForm):
    """
    Use of this form allows the automatic setting of a (deterministic)
    ID for GRENML objects being first created, when the ID has not
    been provided.  It uses the GRENML library for ID generation.
    """

    # This MUST be set on children of this form
    # Acceptable values:
    # - grenml_models.Institution
    # - grenml_models.Node
    # - grenml_models.Link
    GRENML_OBJECT_TYPE = None

    def produce_id_from_library(self, form_data):
        """
        Uses the automatic ID generation from the GRENML library.
        Instantiate a GRENML library object of the type specified
        in our GRENML_OBJECT_TYPE.  Object instantiation will use
        the library's default ID generation mode.
        """
        grenml_object = self.GRENML_OBJECT_TYPE(
            id=None,
            name=form_data['name'] if 'name' in form_data else '',
            short_name=form_data['short_name'] if 'short_name' in form_data else '',
        )
        return grenml_object.id

    def clean(self):
        if not self.GRENML_OBJECT_TYPE:
            raise NotImplementedError(_('AutoIDForm does not have required GRENML_OBJECT_TYPE.'))

        cleaned_data = super().clean()

        # If the object already has a primary key,
        # this is an update to an existing object.
        # Since we do not support changing primary keys of existing
        # objects, no need to validate ID.  It would hinder updates.
        if self.instance.pk is not None:
            return cleaned_data

        if cleaned_data['grenml_id']:
            custom_id = True
            grenml_id = cleaned_data['grenml_id']

        else:
            custom_id = False
            grenml_id = self.produce_id_from_library(cleaned_data)
            cleaned_data['grenml_id'] = grenml_id

        if BaseModel.objects.filter(grenml_id=grenml_id).count() > 0:
            if custom_id:
                raise ValidationError(
                    _('The element ID provided already exists.')
                )
            else:
                raise ValidationError(_(
                    'There is a conflict with the auto-generated element ID.'
                    ' An object with the same name and short name may already exist.'
                ))

        return cleaned_data


class InstitutionForm(AutoIDForm):
    GRENML_OBJECT_TYPE = grenml_models.Institution

    class Meta:
        model = Institution
        exclude = ('id', )


class NodeForm(AutoIDForm):
    GRENML_OBJECT_TYPE = grenml_models.Node

    class Meta:
        model = Node
        exclude = ('id', )


class TopologyForm(AutoIDForm):
    GRENML_OBJECT_TYPE = grenml_models.Topology

    class Meta:
        model = Topology
        fields = '__all__'


class LinkForm(AutoIDForm):
    GRENML_OBJECT_TYPE = grenml_models.Link

    class Meta:
        model = Link
        exclude = ('id', )


class BaseAdmin(admin.ModelAdmin):

    def get_changeform_initial_data(self, request):
        """
        Overrides default ID auto-generation for Django Admin forms,
        hopefully encouraging administrators to supply their own.
        """
        return {'grenml_id': ''}

    def get_fields(self, request, obj=None, **kwargs):
        """
        Rearranges the fields to ensure the fields in Lifetime and
        Location always comes at the end of the fields in the
        admin panel for add/change view, and the GRENML ID is first.
        """
        fields = super().get_fields(request, obj, **kwargs)
        fields.remove('grenml_id')
        fields.insert(0, 'grenml_id')
        for field in (Location._meta.fields + Lifetime._meta.fields):
            if field.name in fields:
                fields.remove(field.name)
                fields.append(field.name)
        return fields


class PropertyInline(admin.TabularInline):
    model = Property


@admin.register(Node)
class NodeAdmin(BaseAdmin):
    form = NodeForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.message_user(request, MESSAGE_APPLY_ALL_RULESETS)
        async_task(Ruleset.objects.apply_all_rulesets())

    list_display = ('grenml_id', 'name', 'short_name',)
    search_fields = ('grenml_id', 'name', 'short_name',)
    ordering = ('grenml_id', 'name', 'short_name',)
    filter_horizontal = ('owners',)
    exclude = ('dirty',)
    inlines = [
        PropertyInline,
    ]


@admin.register(Link)
class LinkAdmin(BaseAdmin):
    form = LinkForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.message_user(request, MESSAGE_APPLY_ALL_RULESETS)
        async_task(Ruleset.objects.apply_all_rulesets())

    list_display = ('grenml_id', 'name', 'short_name', 'node_a', 'node_b',)
    search_fields = ('grenml_id', 'name', 'short_name',)
    ordering = ('grenml_id', 'name', 'short_name',)
    filter_horizontal = ('owners',)
    exclude = ('dirty',)
    inlines = [
        PropertyInline,
    ]


@admin.register(Institution)
class InstitutionAdmin(BaseAdmin):
    form = InstitutionForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.message_user(request, MESSAGE_APPLY_ALL_RULESETS)
        async_task(Ruleset.objects.apply_all_rulesets())

    list_display = ('grenml_id', 'name', 'short_name',)
    search_fields = ('grenml_id', 'name', 'short_name',)
    ordering = ('grenml_id', 'name', 'short_name',)
    exclude = ('dirty',)
    inlines = [
        PropertyInline,
    ]


class NodeInline(admin.TabularInline):
    model = Node


@admin.register(Topology)
class TopologyAdmin(BaseAdmin):
    form = TopologyForm

    readonly_fields = ('nodes_display', 'links_display', 'institutions_display',)
    list_display = ('grenml_id', 'name', 'parent', 'is_main')
    search_fields = ('grenml_id', 'name',)
    ordering = ('grenml_id', 'name',)
    exclude = ('dirty',)
    actions = ('make_topology_main',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'institutions',
            'nodes',
            'links',
            'institutions__properties',
            'nodes__properties',
            'links__properties',
        )

    def nodes_display(self, obj):
        return '\n'.join([node.__str__() for node in obj.nodes.all()])

    def links_display(self, obj):
        return '\n'.join([link.__str__() for link in obj.links.all()])

    def institutions_display(self, obj):
        return '\n'.join([institution.__str__() for institution in obj.institutions.all()])

    @admin.display(description=gettext_lazy('is main'))
    def is_main(self, obj):
        if obj.main:
            return '✅'
        else:
            return '❌'

    nodes_display.short_description = gettext_lazy(Node._meta.verbose_name_plural.title())
    links_display.short_description = gettext_lazy(Link._meta.verbose_name_plural.title())
    institutions_display.short_description = \
        gettext_lazy(Institution._meta.verbose_name_plural.title())

    def get_deleted_objects(self, objs, request):
        """
        Hook for customizing the delete process for the delete
        view and the "delete selected" action.
        """
        # Initial list to be populated by iterating over objects marked
        # for deletion
        to_delete = {
            'topologies': set(),
            'nodes': set(),
            'links': set(),
            'institutions': set()
        }
        # Iterate over all topologies marked for deletion and collect
        # the objects
        for topology in objs:
            del_result = topology.get_delete_objects()
            to_delete['topologies'].update(del_result['topologies'])
            to_delete['nodes'].update(del_result['nodes'])
            to_delete['links'].update(del_result['links'])
            to_delete['institutions'].update(del_result['institutions'])

        # List of objects that will be deleted. Grouped by type for
        # readability
        delete_list = []
        delete_list.extend([
            f'{topology._meta.verbose_name}: {topology.__str__()}'
            for topology in to_delete['topologies']
        ])
        delete_list.extend([
            f'{node._meta.verbose_name}: {node.__str__()}'
            for node in to_delete['nodes']
        ])
        delete_list.extend([
            f'{link._meta.verbose_name}: {link.__str__()}'
            for link in to_delete['links']
        ])
        delete_list.extend([
            f'{institution._meta.verbose_name}: {institution.__str__()}'
            for institution in to_delete['institutions']
        ])

        # Create a summary of the number of each type of object
        # that will be deleted
        delete_summary = {}
        if len(to_delete['topologies']) > 0:
            delete_summary[
                Topology._meta.verbose_name_plural.title()
            ] = len(to_delete['topologies'])
        if len(to_delete['nodes']) > 0:
            delete_summary[
                Node._meta.verbose_name_plural.title()
            ] = len(to_delete['nodes'])
        if len(to_delete['links']) > 0:
            delete_summary[
                Link._meta.verbose_name_plural.title()
            ] = len(to_delete['links'])
        if len(to_delete['institutions']) > 0:
            delete_summary[
                Institution._meta.verbose_name_plural.title()
            ] = len(to_delete['institutions'])

        return delete_list, delete_summary, set(), []

    @admin.action(description=_('Mark one Topology as the main Topology for export.'))
    def make_topology_main(self, request, queryset):
        if queryset.count() == 1:
            Topology.objects.update(main=False)
            queryset.update(main=True)
            self.message_user(
                request,
                # Translators: {} is the name of a database record created by the user  # noqa
                _('Topology {} set as root for export and distributed database polling.').format(
                    queryset.first().name,
                ),
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                'Select exactly one Topology when setting the main Topology.',
                messages.ERROR,
            )
