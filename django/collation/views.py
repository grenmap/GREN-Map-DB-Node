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
import django.contrib.messages as messages

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import status

from base_app.utils.decorators import test_only
from collation.models import (
    MatchType,
    MatchInfo,
    MatchCriterion,
    ActionType,
    Action,
    ActionInfo,
    Rule,
    Ruleset,
)
from . import serializers as s
from . import defaults


log = logging.getLogger(__name__)


class MatchTypeViewSet(ModelViewSet):
    """
    Standard REST CRUD API for MatchTypes.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = MatchType.objects.all().order_by('id')
    serializer_class = s.MatchTypeSerializer
    permission_classes = [IsAuthenticated]


class MatchInfoViewSet(ModelViewSet):
    """
    Standard REST CRUD API for MatchInfo.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = MatchInfo.objects.all().order_by('id')
    serializer_class = s.MatchInfoSerializer
    permission_classes = [IsAuthenticated]


class MatchCriterionViewSet(ModelViewSet):
    """
    Standard REST CRUD API for MatchCriteria.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = MatchCriterion.objects.all().order_by('id')
    serializer_class = s.MatchCriterionSerializer
    permission_classes = [IsAuthenticated]


class ActionTypeViewSet(ReadOnlyModelViewSet):
    """
    Standard REST CRUD API for ActionTypes.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = ActionType.objects.all().order_by('id')
    serializer_class = s.ActionTypeSerializer
    permission_classes = [IsAuthenticated]


class ActionViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Actions.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Action.objects.all().order_by('id')
    serializer_class = s.ActionSerializer
    permission_classes = [IsAuthenticated]


class ActionInfoViewSet(ModelViewSet):
    """
    Standard REST CRUD API for ActionInfo.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = ActionInfo.objects.all().order_by('id')
    serializer_class = s.ActionInfoSerializer
    permission_classes = [IsAuthenticated]


class RuleViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Rules.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Rule.objects.all()
    serializer_class = s.RuleSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated])
    def apply(self, request, pk=None):
        """
        RPC endpoint to apply a Rule.
        """
        try:
            rule = Rule.objects.get(pk=pk)
        except Rule.DoesNotExist:
            return Response('', status=status.HTTP_404_NOT_FOUND)
        rule_log = rule.apply()
        return Response(rule_log.api_message())

    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated])
    def status(self, request, pk=None):
        """
        Endpoint to check the health status of a Rule.

        Returns:
            {
                'ready': true|false,
                'detail': '<error message>'  # iff 'ready' is false
            }
        """
        try:
            rule = Rule.objects.get(pk=pk)
        except Rule.DoesNotExist:
            return Response('', status=status.HTTP_404_NOT_FOUND)
        try:
            rule.klean()
            return Response({
                'ready': True,
            })
        except ValidationError as e:
            return Response({
                'ready': False,
                'detail': e.message,
            })


class RulesetViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Rulesets.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Ruleset.objects.all()
    serializer_class = s.RulesetSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['patch'], detail=False, permission_classes=[IsAuthenticated])
    def disable_all(self, request):
        """
        Bulk PATCH-like functionality to set the 'enabled' flag
        on all Rulesets to False.
        """
        Ruleset.objects.update(enabled=False)
        return Response('')

    @action(methods=['patch'], detail=False, permission_classes=[IsAuthenticated])
    def enable_all(self, request):
        """
        Bulk PATCH-like functionality to set the 'enabled' flag
        on all Rulesets to True.
        """
        Ruleset.objects.update(enabled=True)
        return Response('')

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
    def apply_all(self, request):
        """
        RPC endpoint to apply all Rulesets and their Rules.
        Returns an array of objects.
        """
        rule_logs = Ruleset.objects.apply_all_rulesets()
        return Response([rl.api_message() for rl in rule_logs])

    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated])
    def apply(self, request, pk=None):
        """
        RPC endpoint to apply all Rules in a Ruleset.
        """
        try:
            ruleset = Ruleset.objects.get(pk=pk)
        except Ruleset.DoesNotExist:
            return Response('', status=status.HTTP_404_NOT_FOUND)
        rule_logs = ruleset.apply()
        return Response([rl.api_message() for rl in rule_logs])

    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated])
    def status(self, request, pk=None):
        """
        Endpoint to check the health status of a Ruleset.

        Returns:
            {
                'ready': true|false,
                'detail': {  # only present if 'ready' is false
                    <Rule PK>: '<error message>',
                }
            }
        """
        try:
            ruleset = Ruleset.objects.get(pk=pk)
        except Ruleset.DoesNotExist:
            return Response('', status=status.HTTP_404_NOT_FOUND)
        validation_errors = {}
        for rule in ruleset.rules.all():
            try:
                rule.klean()
            except ValidationError as e:
                validation_errors[rule.pk] = e.message
        if validation_errors:
            return Response({
                'ready': False,
                'detail': validation_errors,
            })
        else:
            return Response({
                'ready': True,
            })

    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
    def restore_default_collision_resolution(self, request):
        """
        RPC endpoints to remove Rulesets with the names
        defaults.CUSTOM_RULESET_NAME and defaults.DEFAULT_RULESET_NAME,
        then recreate them and populate them with whatever current
        initial defaults are shipped with this version.
        """
        defaults.unpopulate_default_id_collision_rulesets_from_normal_django()
        rulesets = defaults.populate_default_id_collision_rulesets_from_normal_django()
        return Response([
            s.RulesetSerializer(ruleset).data for ruleset in rulesets
        ])


# Name of the form attribute that receives the contents of the file
# to be imported. Should match the "name" attribute of the input
# contained within the form element in the rulesets page.
FILE_TO_IMPORT_FORM_ATTRIBUTE = 'rulesets'


def import_rulesets(request):
    """
    Handles a multipart POST request from the web client carrying a file
    that should contain Rulesets serialized as JSON. Creates the Ruleset
    records on the database.
    Redirects the client to the Ruleset admin page. Includes a success
    or failure message in the redirect response.
    """
    try:
        file_contents = request.FILES[FILE_TO_IMPORT_FORM_ATTRIBUTE].read()
        import_result = s.bytes_to_rulesets(file_contents)
        messages.add_message(
            request,
            messages.SUCCESS,
            _(
                # Translators: {}'s are numbers of rulesets (database entities)  # noqa
                'Imported {} Ruleset(s) successfully. '
                'Discarded {} invalid ruleset(s).'
            ).format(
                len(import_result['created_rulesets']),
                len(import_result['invalid_rulesets']),
            ),
        )
    except s.RulesetParseError:
        messages.add_message(
            request,
            messages.ERROR,
            _('Import failed. Malformed file'),
        )
        log.exception('import_rulesets')
    return HttpResponseRedirect(reverse('admin:collation_ruleset_changelist'))


@test_only
@api_view(['POST'])
def test_import_rulesets(request):
    """
    Test endpoint.

    This handles a POST request containing a list of rulesets
    to be imported. The rulesets should be encoded as JSON.
    The response is empty.
    The status code 201 Created indicates success.
    Code 400 indicates a problem parsing the JSON.

    Command line usage example (omits the ruleset for brevity):
    curl -H "Content-Type: application/json" -X POST \
    -d '{"rulesets":[]}' \
    localhost/test/collation/import_rulesets
    """
    response_status = status.HTTP_201_CREATED
    response_data = None
    try:
        data = request.data['rulesets']
        import_result = s.dict_list_to_rulesets(data)
        response_data = {
            'created_rulesets': [
                ruleset.name for ruleset in import_result['created_rulesets']
            ],
            'invalid_rulesets': [
                ruleset['name'] for ruleset in import_result['invalid_rulesets']
            ],
        }
    except KeyError:
        response_status = status.HTTP_400_BAD_REQUEST
        response_data = 'request body missing required "rulesets" key'
    except s.RulesetParseError:
        response_status = status.HTTP_400_BAD_REQUEST
        response_data = 'could not parse the rulesets'

    return Response(status=response_status, data=response_data)


@test_only
@api_view(['GET'])
def test_export_rulesets(request):
    """
    Test endpoint.

    This handles a GET request that provides ids of rulesets
    to be exported. The response is an array of rulesets
    encoded as JSON.

    Command line usage example:
    curl localhost/test/collation/export_rulesets?ids=1,2
    """
    try:
        ids_parameter = request.GET['ids']
        ruleset_ids = list(map(int, ids_parameter.split(',')))
    except KeyError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data='request missing required parameter "ids"',
        )
    except ValueError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data='the ids must be integers',
        )

    try:
        rulesets = Ruleset.objects.filter(id__in=ruleset_ids)
    except Exception:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data='could not retrieve rulesets with given ids',
        )

    return Response(
        status=status.HTTP_200_OK,
        data=[
            s.NestedRulesetSerializer(ruleset).data
            for ruleset in rulesets
        ]
    )
