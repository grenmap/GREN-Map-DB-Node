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

import copy
import io
import logging

from django.db import transaction
from rest_framework import serializers as s
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from .models import (
    MatchType, MatchInfo, MatchCriterion,
    ActionType, ActionInfo, Action,
    Rule, Ruleset
)

log = logging.getLogger(__name__)


class MatchTypeSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = MatchType
        fields = '__all__'


class MatchInfoSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = MatchInfo
        fields = '__all__'


class MatchCriterionSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = MatchCriterion
        fields = '__all__'


class ActionTypeSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = ActionType
        fields = '__all__'


class ActionInfoSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = ActionInfo
        fields = '__all__'


class ActionSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = Action
        fields = '__all__'


class RuleSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = Rule
        fields = '__all__'


class RulesetSerializer(s.ModelSerializer):
    id = s.ReadOnlyField()

    class Meta:
        model = Ruleset
        fields = '__all__'


class NestedMatchInfoSerializer(s.ModelSerializer):
    """ MatchInfo serializer for import and export rulesets. """
    class Meta:
        model = MatchInfo
        fields = ['key', 'value']


class NestedMatchCriterionSerializer(s.ModelSerializer):
    """
    MatchCriterion serializer for import and export rulesets.

    This is different from MatchCriterionSerializer in that it includes
    the MatchInfo records associated to the MatchCriterion.
    """
    match_type = s.SlugRelatedField(
        slug_field='name',
        queryset=MatchType.objects.all(),
    )
    matchinfo_set = NestedMatchInfoSerializer(many=True)

    class Meta:
        model = MatchCriterion
        fields = ['match_type', 'matchinfo_set']


class NestedActionInfoSerializer(s.ModelSerializer):
    """ ActionInfo serializer for import and export rulesets. """
    class Meta:
        model = ActionInfo
        fields = ['key', 'value']


class NestedActionSerializer(s.ModelSerializer):
    """
    Action serializer for import and exporting rulesets.

    Unlike ActionSerializer, this Includes the ActionInfo records
    associated to the Action.
    """
    action_type = s.SlugRelatedField(
        slug_field='name',
        queryset=ActionType.objects.all(),
    )
    actioninfo_set = NestedActionInfoSerializer(many=True)

    class Meta:
        model = Action
        fields = ['action_type', 'actioninfo_set']


class NestedRuleSerializer(s.ModelSerializer):
    """
    Serializes not only the Rule attributes, but also the Action and
    MatchCriteria linked to the rule.
    This is for import and export rulesets.
    """
    actions = NestedActionSerializer(many=True)
    match_criteria = NestedMatchCriterionSerializer(many=True)

    class Meta:
        model = Rule
        fields = ['name', 'actions', 'match_criteria', 'enabled', 'priority']


class NestedRulesetSerializer(s.ModelSerializer):
    """
    Serializes a ruleset and the rules it contains.
    Used to export and import rulesets.
    """
    rules = NestedRuleSerializer(many=True)

    class Meta:
        model = Ruleset
        fields = ['name', 'rules', 'enabled', 'priority']


def create_composite(
        composite_model, composite_name, component_constructors, validated_data
):
    """
    This function is a constructor for a database model that contains
    other models.

    Composite_model is the class object for the composite. The function
    uses it to instantiate the model.

    Composite_name is the name of the attribute in the component that
    refers to the composite.

    Component_constructors is a dictionary that associates the name
    of an attribute in the model instance the function will build to a
    function that returns a value for the attribute. Currently this
    attribute is an instance of another model (a component) that
    participates in the model instance being created.

    Validated_data is a dictionary obtained from the serializer for
    the composite model. It provides values for the composite and
    the component models.
    """
    validated_data = copy.deepcopy(validated_data)

    # Move relationship attributes out of validated_data,
    # into component_data.
    component_data = {}
    for component_attribute in component_constructors:
        data = validated_data.pop(component_attribute)
        component_data[component_attribute] = data

    # Create an instance of the composite model;
    # this requires removing the attributes that store
    # component fields from validated_data.
    composite_instance = composite_model.objects.create(**validated_data)

    # Create the component instances.
    for component_attribute, component_constructor in component_constructors.items():
        component_items = component_data[component_attribute]
        for item in component_items:
            item[composite_name] = composite_instance
            component_constructor(item)

    return composite_instance


def create_match_criterion(validated_data):
    """ Makes a MatchCriterion from a validated_data dictionary. """
    return create_composite(
        MatchCriterion,
        'match_criterion',
        {'matchinfo_set': lambda data: MatchInfo.objects.create(**data)},
        validated_data,
    )


def create_action(validated_data):
    """ Creates an Action instance. Validated_data is a dictionary. """
    return create_composite(
        Action,
        'action',
        {'actioninfo_set': lambda data: ActionInfo.objects.create(**data)},
        validated_data,
    )


def create_rule(validated_data):
    """
    Returns a rule whose fields have values taken from
    the validated_data dictionary.
    """
    return create_composite(
        Rule,
        'rule',
        {
            'actions': create_action,
            'match_criteria': create_match_criterion,
        },
        validated_data,
    )


def create_ruleset(validated_data):
    """ Uses the validated_data dictionary to create a ruleset. """
    return create_composite(
        Ruleset,
        'ruleset',
        {'rules': create_rule},
        validated_data,
    )


def rulesets_to_bytes(rulesets):
    """
    Converts the Ruleset instances in the given list to a JSON object
    encoded as a list of bytes.
    """
    ruleset_data = [
        NestedRulesetSerializer(ruleset).data
        for ruleset in rulesets
    ]
    json_renderer = JSONRenderer()
    ruleset_bytes = json_renderer.render(
        ruleset_data,
        accepted_media_type='Accept: application/json; indent=4',
    )
    return ruleset_bytes


class RulesetParseError(Exception):
    """
    This represents a problem in parsing the array of bytes
    which should de-serialize into a list of Rulesets.
    """
    pass


class RollbackInvalidRuleset(Exception):
    """
    We use this exception to exit a "with" block where we execute
    a transaction to overwrite a ruleset.
    """
    pass


def dict_list_to_rulesets(dict_list):
    """
    Creates rulesets from the dictionaries contained
    in the given list.

    Return a dictionary with two attributes: created_rulesets is a list
    of Ruleset instances; invalid_rulesets is a list of dictionaries
    that describe rulesets which failed the serializer validation.
    """
    invalid_rulesets = []
    created_rulesets = []
    for item in dict_list:
        serializer = NestedRulesetSerializer(data=item)
        ruleset_name = item['name']

        try:
            with transaction.atomic():
                # delete ruleset if it exists
                try:
                    existing_ruleset = Ruleset.objects.get(name=ruleset_name)
                    existing_ruleset.delete()
                    log.debug('deleted existing ruleset %s', ruleset_name)
                except Ruleset.DoesNotExist:
                    log.debug('ruleset %s does not exist', ruleset_name)

                # roll back the transaction if the ruleset to be created
                # is invalid
                if not serializer.is_valid():
                    log.debug(
                        'ruleset %s is invalid - errors: %s',
                        ruleset_name,
                        serializer.errors,
                    )
                    invalid_rulesets.append(item)
                    raise RollbackInvalidRuleset()

                # create ruleset
                ruleset = create_ruleset(serializer.validated_data)
                log.debug('created ruleset %s', ruleset_name)
                created_rulesets.append(ruleset)
        except RollbackInvalidRuleset:
            # we raised this exception to escape the "with" block
            pass

    return {
        'created_rulesets': created_rulesets,
        'invalid_rulesets': invalid_rulesets,
    }


def bytes_to_rulesets(ruleset_bytes):
    """
    Takes an array of bytes, de-serializes it and builds
    Ruleset instances.

    The result value is described in the dict_list_to_rulesets
    docstring.

    Raises RulesetParseError in case of problems when the function
    attempts to parse the byte array;
    """
    stream = io.BytesIO(ruleset_bytes)

    try:
        data = JSONParser().parse(stream)
    except ParseError:
        raise RulesetParseError()

    if not isinstance(data, list):
        log.warning('ruleset bytearray did not deserialize to list')
        raise RulesetParseError()

    if not all(map(lambda obj: isinstance(obj, dict), data)):
        log.warning('at least one item in the rulesets list is not a dict')
        raise RulesetParseError()

    return dict_list_to_rulesets(data)
