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
from inspect import cleandoc

from datetime import datetime
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from nested_inline.admin import (
    NestedModelAdmin, NestedStackedInline, NestedTabularInline
)

from collation.constants import DATETIME_FORMAT
from collation.exceptions import RuleApplyError
from collation.models import (
    Action, ActionInfo,
    MatchCriterion, MatchInfo,
    Rule, Ruleset
)
from collation.serializers import rulesets_to_bytes

log = logging.getLogger(__name__)


class NestedMatchInfoInline(NestedTabularInline):
    """ MatchInfo nested inline element. """

    model = MatchInfo
    fk_name = 'match_criterion'
    min_num = 0
    extra = 0


class MatchCriteriaInline(NestedStackedInline):
    """
    Nested inline element for MatchCriteria
    on the Rule admin page.
    """
    model = MatchCriterion
    readonly_fields = (
        'match_description',
        'required_match_info_keys',
        'optional_match_info_keys',
    )
    inlines = [NestedMatchInfoInline]
    fk_name = 'rule'
    min_num = 1
    extra = 0

    @admin.display(description=_('match description'))
    def match_description(self, match_criterion):
        """
        Pipes the MatchType class's docstring to the user as a
        read-only field in the Admin, as handy inline documentation.
        Applies appropriate translation to the text, if available.
        """
        try:
            if match_criterion.pk:
                match_type_class = match_criterion.match_type.get_class_instance(match_criterion)
                return cleandoc(_(match_type_class.__doc__))
            else:
                return (_(
                    'Once a match type has been selected and this Rule is saved, '
                    'a description of the match and its required fields will appear here.'
                ))
        except Exception as e:
            log.warning('Error displaying match description: %s', str(e))
            return '[Error displaying match description.]'

    @admin.display(description=_('required match info keys'))
    def required_match_info_keys(self, match_criterion):
        """
        Outputs a checklist of required MatchInfo entries, by key,
        with helpful icons indicating whether the required
        MatchInfos exist for this Rule.
        """
        match_type = match_criterion.match_type
        if match_type:
            info = match_criterion.info_dict
            required_keys = match_type.required_info_keys
            keys_text = []
            for key in required_keys:
                if key in info:
                    keys_text.append(key + ' ✔️')
                else:
                    keys_text.append(key + ' ❌')
            if keys_text:
                return '\n'.join(keys_text)
            else:
                return '✔️'
        return '---'

    @admin.display(description=_('optional match info keys'))
    def optional_match_info_keys(self, match_criterion):
        """
        Outputs a checklist of optional MatchInfo entries, by key,
        with helpful icons indicating whether there are any
        incompatible keys currently saved with this Rule.
        """
        match_type = match_criterion.match_type
        if match_type:
            info = match_criterion.info_dict
            required_keys = match_type.required_info_keys
            optional_keys = match_type.optional_info_keys
            keys_text = []
            for key in optional_keys:
                if key in info:
                    keys_text.append(key + ' ✔️')
                else:
                    keys_text.append(key + ' ⭕')
            for key in info:
                if key not in required_keys and key not in optional_keys:
                    keys_text.append(key + ' ⛔')
            if keys_text:
                return '\n'.join(keys_text)
            else:
                return '✔️'
        return '---'


class NestedActionInfoInline(NestedTabularInline):
    """ Nested inline element for ActionInfo records. """

    model = ActionInfo
    fk_name = 'action'
    min_num = 0
    extra = 0


class ActionsInline(NestedStackedInline):
    """ Nested inline element for Actions on the Rule page. """

    model = Action
    readonly_fields = (
        'action_description',
        'required_action_info_keys',
        'optional_action_info_keys',
    )
    inlines = [NestedActionInfoInline]
    fk_name = 'rule'
    min_num = 1
    extra = 0

    @admin.display(description=_('action description'))
    def action_description(self, action):
        """
        Pipes the ActionType class's docstring to the user as a
        read-only field in the Admin, as handy inline documentation.
        Applies appropriate translation to the text, if available.
        """
        try:
            if action.pk:
                action_type_class = action.action_type.get_class_instance(action)
                return cleandoc(_(action_type_class.__doc__))
            else:
                return (_(
                    'Once an action type has been selected and this Rule is saved, '
                    'a description of the action and its required fields will appear here.'
                ))
        except Exception as e:
            log.warning('Error displaying action description: %s', str(e))
            return '[Error displaying action description.]'

    @admin.display(description=_('required action info keys'))
    def required_action_info_keys(self, action):
        """
        Outputs a checklist of required ActionInfo entries, by key,
        with helpful icons indicating whether the appropriate
        ActionInfos exist, and whether there are any incompatible keys.
        """
        action_type = action.action_type
        if action_type:
            info = action.info_dict
            required_keys = action_type.required_info_keys
            keys_text = []
            for key in required_keys:
                if key in info:
                    keys_text.append(key + ' ✔️')
                else:
                    keys_text.append(key + ' ❌')
            if keys_text:
                return '\n'.join(keys_text)
            else:
                return '✔️'
        return '---'

    @admin.display(description=_('optional action info keys'))
    def optional_action_info_keys(self, action):
        """
        Outputs a checklist of optional ActionInfo entries, by key,
        with helpful icons indicating whether there are any
        incompatible keys currently saved with this Rule.
        """
        action_type = action.action_type
        if action_type:
            info = action.info_dict
            required_keys = action_type.required_info_keys
            optional_keys = action_type.optional_info_keys
            keys_text = []
            for key in optional_keys:
                if key in info:
                    keys_text.append(key + ' ✔️')
                else:
                    keys_text.append(key + ' ⭕')
            for key in info:
                if key not in required_keys and key not in optional_keys:
                    keys_text.append(key + ' ⛔')
            if keys_text:
                return '\n'.join(keys_text)
            else:
                return '✔️'
        return '---'


class RuleInline(NestedStackedInline):
    """ Nested inline element for Rules on the Ruleset page. """

    model = Rule
    inlines = [MatchCriteriaInline, ActionsInline]
    fk_name = 'ruleset'
    extra = 0


class RulesetAdmin(NestedModelAdmin):
    model = Ruleset
    list_display = ['name', 'rules', 'priority', 'enabled', 'health_check']
    ordering = ('priority', )
    inlines = [RuleInline]
    actions = ['export']

    def rules(self, ruleset):
        return ', '.join([str(rule) for rule in ruleset.rules.all()])

    @admin.display(description=_('health check'))
    def health_check(self, ruleset):
        """
        Runs each contained Rule's klean method; if any fail,
        the Ruleset is not ready to run.
        """
        for rule in ruleset.rules.all():
            try:
                rule.klean()
            except ValidationError:
                return _('Rule misconfiguration detected')
        return _('Ready')

    def export(self, request, queryset):
        """
        This method implements the export action that serializes
        the selected rulesets to JSON and delivers them to the user
        in a file.
        """
        response = None
        try:
            rulesets = queryset.all()
            json_bytes = rulesets_to_bytes(rulesets)

            now = datetime.utcnow().strftime(DATETIME_FORMAT)
            filename = 'rulesets_{}.json'.format(now)

            response = HttpResponse(json_bytes, content_type='application/json')
            response['Content-Disposition'] = (
                'attachment; filename="{}"'.format(filename)
            )
        except Exception:
            log.exception('RulesetAdmin.export')
            response = HttpResponseRedirect('./')
            self.message_user(
                request,
                _('Failed to export rulesets.'),
                level=messages.ERROR,
            )
        return response

    export.short_description = 'Export Ruleset(s) to file'


class RuleAdmin(NestedModelAdmin):
    model = Rule
    readonly_fields = ('health_warning', )
    list_display = ['id', 'name', 'ruleset', 'priority', 'enabled', 'health_check', 'rule_actions']
    ordering = ('ruleset', 'priority')
    inlines = [MatchCriteriaInline, ActionsInline]

    def get_form(self, request, obj=None, **kwargs):
        """
        There is a bug with the built-in Admin UI related to the
        Ruleset foreign key widget: it throws an error when inline
        changes are attempted..  Since adding a Ruleset inline
        is not deemed necessary functionality, it is simply disabled
        for now.  This method overrides the ModelForm to disable the
        relevant UI form buttons.
        """
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['ruleset'].widget.can_add_related = False
        form.base_fields['ruleset'].widget.can_change_related = False
        form.base_fields['ruleset'].widget.can_delete_related = False
        return form

    @admin.display(description=_('health warning'))
    def health_warning(self, rule):
        """
        Runs the model's klean method and spits out text of the
        first ValidationError it encounters.
        """
        try:
            rule.klean()
            return _('Ready')
        except ValidationError as e:
            # e.message is a tuple
            return '❌ ' + ''.join(e.message)

    @admin.display(description=_('health check'))
    def health_check(self, rule):
        """
        Runs the model's klean method to ensure it's ready to run.
        """
        try:
            rule.klean()
            return _('Ready')
        except ValidationError:
            return _('Rule misconfiguration detected')

    @admin.display(description=_('rule actions'))
    def rule_actions(self, obj):
        """
        This method outputs html that appear as buttons
        in every rule on the admin page.
        """
        return format_html(
            '<a class="button" href="{}">{}</a>&nbsp'
            '<a class="button" href="{}">{}</a>',
            reverse('admin:apply-rule', args=[obj.pk]),
            _('Apply Rule'),
            reverse('admin:clone-rule', args=[obj.pk]),
            _('Clone Rule'),
        )

    def apply_rule(self, request, rule_id):
        """
        Calls a Rule's apply method in response to a click
        on its apply button.
        """
        rule = Rule.objects.get(id=rule_id)

        message = None
        message_level = None
        try:
            rule_log = rule.apply()
            message = rule_log.admin_message()
            log.debug(message)
            message_level = messages.INFO
        except RuleApplyError as e:
            log.warning(str(e))
            message = e.translated_message()
            message_level = messages.ERROR
        self.message_user(request, message, level=message_level)
        return HttpResponseRedirect('../')

    def clone_rule(self, request, rule_id):
        """ Handles clicks on a Rule's clone button. """
        rule = Rule.objects.get(id=rule_id)

        message = None
        message_level = None
        try:
            rule.clone()

            # Translators: {} is the name of a database record created by the user  # noqa
            message = _('Cloned rule {} successfully').format(rule.name)
            message_level = messages.INFO
        except Exception:
            log.exception('Failed to clone rule %s', rule)

            # Translators: {} is the name of a database record created by the user  # noqa
            message = _('Failed to clone rule {}').format(rule.name)
            message_level = messages.ERROR
        self.message_user(request, message, level=message_level)
        return HttpResponseRedirect('../')

    def get_urls(self):
        """
        This registers endpoints that respond to clicks
        on the buttons shown in each rule row.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                'apply_rule/<rule_id>',
                self.apply_rule,
                name='apply-rule'
            ),
            path(
                'clone_rule/<rule_id>',
                self.clone_rule,
                name='clone-rule'
            ),
        ]
        return custom_urls + urls


admin.site.register(Rule, RuleAdmin)
admin.site.register(Ruleset, RulesetAdmin)
