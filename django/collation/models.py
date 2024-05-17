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
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext, gettext_lazy as _

from network_topology.models import Institution, Node, Link, BaseModel

import collation.exceptions as exc
from .constants import ElementTypes
from .match_types import init_match_type
from .action_types import init_action_type
from .rule_log import RuleLog

log = logging.getLogger('collation')


# Dictionary used to look up GRENML entities (classes) by
# their associated ElementTypes.
GRENML_ENTITIES_BY_ELEMENT_TYPE = {
    ElementTypes.INSTITUTION: Institution,
    ElementTypes.NODE: Node,
    ElementTypes.LINK: Link,
}


class RulesetManager(models.Manager):
    """
    Custom Manager for Rulesets that injects an apply_all() method.
    """
    def apply_all_rulesets(self):
        """
        Find all Rulesets and apply the Rules within them.
        Rulesets are run in ascending priority order,
        and only if enabled.

        Returns a list of RuleLog instance, one for each Rule
        run in the chain.
        """
        rule_logs = []
        rulesets = Ruleset.objects.filter(enabled=True).order_by('priority')

        for ruleset in rulesets:
            ruleset_rule_logs = ruleset.apply()
            rule_logs.extend(ruleset_rule_logs)

        return rule_logs


class Ruleset(models.Model):
    """
    A group of Rules, usually related somehow.
    """
    objects = RulesetManager()

    name = models.CharField(
        max_length=200,
        null=False, blank=False,
        unique=True,
        verbose_name=_('name'),
    )

    enabled = models.BooleanField(
        null=False, blank=False,
        default=True,
        verbose_name=_('enabled'),
    )

    priority = models.SmallIntegerField(
        null=False, blank=False,
        default=1000,
        help_text=_(
            'Rulesets are run in ascending order of priority. '
            'Ties are broken arbitrarily.'
        ),
        verbose_name=_('priority'),
    )

    def __str__(self):
        return self.name

    @property
    def log_str(self):
        return f'{self.name} [{self.pk}]'

    def apply(self):
        """
        Executes the Rules contained in this Ruleset.
        Rules are run in ascending priority order, and only if enabled.
        Ties are broken arbitrarily.
        Rules failing their health check are skipped.
        Catch all the Exceptions so that all the Rules can run through.
        """
        rule_logs = []
        for rule in self.rules.filter(enabled=True).order_by('priority'):
            try:
                rule.klean()
                rule_log = rule.apply()
                rule_logs.append(rule_log)
            except ValidationError:
                log.warning('Rule misconfiguration detected: %s', rule.log_str)
            except:  # noqa: E722
                log.exception('Apply rule failed for: %s', rule.log_str)
        return rule_logs

    class Meta:
        verbose_name = _('Ruleset')
        verbose_name_plural = _('Rulesets')


def clone_related(original_rule, cloned_rule, main_entity, info_entity, main_field):
    """
    Helper function for Rule.clone. Deep-copies MatchCriteria and
    Actions of a Rule.

    Parameters:
    - original_rule: the source Rule instance;
    - cloned_rule: the clone under construction;
    - main_entity: a class, either MatchCriterion or Action;
    - info_entity: a class as well. MatchInfo or ActionInfo.
      MatchInfo should be used when main_entity is MatchCriterion.
      ActionInfo should be used when main_entity is Action;
    - main_field: the name of the field in the info_entity class
      that refers to the associated main_entity instance.
    """
    main_instances = main_entity.objects.filter(rule=original_rule).all()

    for main_instance in main_instances:
        # get the info records associated with
        # the main entity instance to be cloned
        filter_params = {main_field: main_instance}
        info_instances = info_entity.objects.filter(**filter_params).all()

        # clone the main entity instance
        main_instance.pk = None
        main_instance.rule = cloned_rule
        main_instance.save()

        # clone the associated infos
        for info_instance in info_instances:
            info_instance.pk = None
            setattr(info_instance, main_field, main_instance)
            info_instance.save()


class Rule(models.Model):
    """
    A Rule performs an update to the database, of a variety specified
    by the related Actions, when certain criteria are met, specified by
    the related MatchCriteria.

    When a Rule executes, the MatchCriteria are used first to define
    a set of items on which the Actions will work.
    """
    ruleset = models.ForeignKey(
        Ruleset,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name=_('ruleset'),
    )

    name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('name'),
    )

    enabled = models.BooleanField(
        null=False, blank=False,
        default=True,
        verbose_name=_('enabled'),
    )

    priority = models.SmallIntegerField(
        null=False, blank=False,
        default=1000,
        help_text=_(
            'Rules within a Ruleset are run in ascending order of priority. '
            'Ties are broken arbitrarily.'
        ),
        verbose_name=_('priority'),
    )

    def __str__(self):
        return self.name

    @property
    def log_str(self):
        return f'{self.name} [{self.pk}]'

    @property
    def element_type(self):
        """
        Infers the element_type to which this Rule pertains by the
        value of element_type on its components (MatchCriteria and
        Actions).
        If not all Rule components have the same element type, raises a
        ConflictingElementTypesError.
        """
        rule_components = list(self.match_criteria.all()) + list(self.actions.all())
        element_types = list(set([c.element_type for c in rule_components]))
        if not element_types:
            return None
        elif len(element_types) == 1:
            return element_types[0]
        else:
            raise exc.ConflictingElementTypesError(self)

    def add_match_criterion(
        self,
        match_type_class_name,
        infos=None,
    ):
        """
        Given a class name, adds an appropriate Match
        Criterion of the type indicated by the MatchBy* class name.
        If 'info' param is given (as a list of key-value tuples),
        also adds a MatchInfo for each item therein.
        """
        match_type = MatchType.objects.get(class_name=match_type_class_name)
        match_criterion = MatchCriterion.objects.create(
            rule=self,
            match_type=match_type,
        )
        for info_set in (infos or []):
            MatchInfo.objects.create(
                match_criterion=match_criterion,
                key=info_set[0],
                value=info_set[1],
            )
        return match_criterion

    def klean(self):
        """
        Ensures that the Rule is complete and consistent.
        1. Must have at least one MatchCriterion and Action
        2. Actions must operate on the same type of Elements
            (Node, Link, or Institution) as the Match Criteria
        3. Match Criteria and Actions must have the correct
            MatchInfos and ActionInfos
        """
        # Confirm presence of MatchCriteria and Actions
        if self.match_criteria.count() < 1:
            raise exc.NoMatchCriteriaError(self)
        if self.actions.count() < 1:
            raise exc.NoActionsError(self)

        # Ensure consistent Element type
        try:
            self.element_type
        except exc.ConflictingElementTypesError:
            raise exc.ConflictingElementTypesValidationError(self)

        # Ensure correct MatchInfo keys
        match_criteria = self.match_criteria.all()
        for match_criterion in match_criteria:
            match_type_class = match_criterion.match_type.get_class_instance(match_criterion)
            if not match_type_class.validate_input(match_criterion.info_tuples):
                raise exc.IncorrectMatchInfosValidationError(
                    match_criterion,
                    match_criterion.info_dict.keys(),
                    match_criterion.match_type.required_info_keys,
                )

        # Ensure correct ActionInfo keys
        actions = self.actions.all()
        for action in actions:
            action_type_class = action.action_type.get_class_instance(action)
            if not action_type_class.validate_input(action.info_tuples):
                raise exc.IncorrectActionInfosValidationError(
                    action,
                    action.info_dict.keys(),
                    action.action_type.required_info_keys,
                )

    def apply(self):
        """
        This method executes the Rule. It first locates network topology
        items in the database using MatchCriteria, then it modifies
        those items using Actions.

        When there are two or more MatchCriteria defined
        on an element type, the method uses them to successively
        restrict the set of elements it will affect. In other words,
        two or more criteria are like AND clauses of a SQL query.

        Returns a RuleLog class that can output such things as what
        elements have been affected and how.
        """
        self.klean()

        # Get all elements of the appropriate type,
        # then filter by all MatchCriteria.
        element_type = self.element_type
        element_model = GRENML_ENTITIES_BY_ELEMENT_TYPE[element_type]
        matched_elements = element_model.objects.all()
        log.debug(f'Rule {self} starting with {matched_elements.count()} {element_type}s.')
        for match_criterion in self.match_criteria.all():
            matched_elements = match_criterion.filter(matched_elements)
            log.debug(
                f'Rule {self} now operating on {matched_elements.count()} {element_type}s '
                f'after {match_criterion}.'
            )

        rule_log = RuleLog(self, matched_elements=matched_elements)

        # Run all Actions on the filtered element list
        for element in matched_elements:
            # Confirm this element still exists before proceeding.
            # Processing of previous Actions may have already deleted
            # this one, so our reference could be stale
            if BaseModel.objects.filter(pk=element.pk).exists():
                for action in self.actions.all():
                    log.debug(f'Rule {self} applying {action} on {element.log_str}.')
                    element, action_log = action.apply(element)
                    rule_log.add_action_log(action_log)
                    # If the element has been deleted (and not replaced)
                    # by an Action, we cannot continue the Action chain
                    # (Bonus: helps enforce that Action classes should
                    # return object references as intended.)
                    if element is None:
                        break
            else:
                log.debug('Skipping Actions on element %s that no longer exists.', element.log_str)

        return rule_log

    def clone(self):
        """
        Creates a copy of a Rule.

        After executing this method, the database will have
        one new Rule record and as many MatchCriteria and Actions
        as the Rule it is called on.

        The MatchInfo in each MatchCriterion and the ActionInfo in each
        Action will be duplicated.

        The MatchTypes and ActionTypes associated to MatchCriteria and
        Actions are not cloned.
        """
        number_of_copies = Rule.objects.filter(name__startswith=self.name).count()
        rule_clone = Rule.objects.get(name=self.name)

        # In case Rule were a subclass of another model,
        # we would also need to assign its id to None.
        rule_clone.pk = None
        rule_clone.name = rule_clone.name + ' {}'.format(number_of_copies)
        rule_clone.ruleset = self.ruleset
        rule_clone.save()

        clone_related(self, rule_clone, MatchCriterion, MatchInfo, 'match_criterion')
        clone_related(self, rule_clone, Action, ActionInfo, 'action')

        return rule_clone

    class Meta:
        verbose_name = _('Rule')
        verbose_name_plural = _('Rules')


class MatchType(models.Model):
    """
    MatchType contains a MatchCriterion's name and element type.
    """
    class_name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('class name'),
    )
    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('name'),
    )
    element_type = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=ElementTypes.choices,
        verbose_name=_('element type'),
    )
    required_info = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_('JSON array of required ActionInfo keys'),
        verbose_name=_('required info'),
    )
    optional_info = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        default='',
        help_text=_('JSON array of optional ActionInfo keys'),
        verbose_name=_('optional info'),
    )

    @property
    def required_info_keys(self):
        """
        Parses the JSON required_info field into a list.
        """
        return json.loads(self.required_info) if self.required_info else []

    def __str__(self):
        return gettext(self.name)

    def get_class_instance(self, match_criterion):
        try:
            return init_match_type(self.class_name, match_criterion)
        except NotImplementedError:
            raise exc.UnsupportedMatchTypeError(self)

    class Meta:
        verbose_name = _('Match Type')
        verbose_name_plural = _('Match Types')


class MatchCriterion(models.Model):
    """
    This determines which GRENML elements a Rule affects.

    A Rule may have one or more MatchCriteria.

    Through its associated MatchType, a MatchCriterion has
    an element type. This binds the criterion to one of the
    GRENML entity types (Institution, Node or Link).

    A MatchCriterion may be connected to any number of MatchInfo
    records, including zero. Together they describe the subset of
    a GRENML entity the Rule will modify.
    """
    rule = models.ForeignKey(
        Rule,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='match_criteria',
        verbose_name=_('rule'),
    )
    match_type = models.ForeignKey(
        MatchType,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        verbose_name=_('match type'),
    )

    def __str__(self):
        return self.rule.name + ' - ' + self.match_type.name

    @property
    def element_type(self):
        """
        The element type of a MatchCriterion is the one
        in its associated MatchType entity.
        """
        return self.match_type.element_type

    @property
    def info_dict(self):
        """
        Returns associated MatchInfo key-vals as a dictionary.
        """
        return {mi.key: mi.value for mi in self.matchinfo_set.all()}

    @property
    def info_tuples(self):
        """
        Returns associated MatchInfo key-vals as a list of tuples.
        """
        return [(mi.key, mi.value) for mi in self.matchinfo_set.all()]

    def filter(self, elements_query):
        """
        Adds filters to the given query, based on the MatchInfo linked
        to this MatchCriterion, via the MatchType specified in the
        class_name.
        """
        match_type = self.match_type.get_class_instance(self)
        return match_type.filter(elements_query)

    class Meta:
        verbose_name = _('Match Criterion')
        verbose_name_plural = _('Match Criteria')


class MatchInfo(models.Model):
    """
    MatchInfo identifies an attribute of a GRENML element
    that a MatchCriterion takes as input.

    ActionTypes and Actions are associated one-to-one.
    """
    match_criterion = models.ForeignKey(
        MatchCriterion,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name=_('match criterion'),
    )
    key = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        verbose_name=_('key'),
    )
    value = models.CharField(
        max_length=1000,
        null=False,
        blank=False,
        verbose_name=_('value'),
    )

    def __str__(self):
        return self.match_criterion.rule.name + ' - ' + self.key

    class Meta:
        verbose_name = _('Match Info')
        verbose_name_plural = _('Match Infos')


class ActionType(models.Model):
    """
    An ActionType defines the type of GRENML element an Action affects
    and what kind of change will happen.
    """
    class_name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('class name'),
    )
    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('name'),
    )
    element_type = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=ElementTypes.choices,
        verbose_name=_('element type'),
    )
    required_info = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_('JSON array of required ActionInfo keys'),
        verbose_name=_('required info'),
    )
    optional_info = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        default='',
        help_text=_('JSON array of optional ActionInfo keys'),
        verbose_name=_('optional info'),
    )

    @property
    def required_info_keys(self):
        """
        Parses the JSON required_info field into a list.
        """
        return json.loads(self.required_info) if self.required_info else []

    @property
    def optional_info_keys(self):
        """
        Parses the JSON optional_info field into a list.
        """
        return json.loads(self.optional_info) if self.optional_info else []

    def __str__(self):
        return gettext(self.name)

    def get_class_instance(self, action):
        try:
            return init_action_type(self.class_name, action)
        except NotImplementedError:
            raise exc.UnsupportedActionTypeError(action)

    class Meta:
        verbose_name = _('Action Type')
        verbose_name_plural = _('Action Types')


class Action(models.Model):
    """
    An Action modifies GRENML elements
    selected by its related Rule's MatchCriteria.
    """
    rule = models.ForeignKey(
        Rule,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name=_('rule'),
    )
    action_type = models.ForeignKey(
        ActionType,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        verbose_name=_('action type'),
    )

    @property
    def element_type(self):
        """ The element type of an Action comes from its ActionType. """
        return self.action_type.element_type

    @property
    def info_dict(self):
        """
        Returns associated ActionInfo key-vals as a dictionary.
        """
        return {ai.key: ai.value for ai in self.actioninfo_set.all()}

    @property
    def info_tuples(self):
        """
        Returns associated ActionInfo key-vals as a list of tuples.
        """
        return [(ai.key, ai.value) for ai in self.actioninfo_set.all()]

    def __str__(self):
        return self.rule.name + ' - ' + self.action_type.name

    def apply(self, elements):
        """
        Executes this Action on the given elements, via the class
        referenced by the related ActionType.
        """
        action_type = self.action_type.get_class_instance(self)
        return action_type.apply(elements)

    class Meta:
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')


class ActionInfo(models.Model):
    """
    ActionInfo instances represent fields of GRENML entities
    that are used by Actions.
    """
    action = models.ForeignKey(
        Action,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name=_('action'),
    )
    key = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        verbose_name=_('key'),
    )
    value = models.CharField(
        max_length=1000,
        null=False,
        blank=False,
        verbose_name=_('value'),
    )

    def __str__(self):
        return self.action.rule.name + ' - ' + self.key

    class Meta:
        verbose_name = _('Action Info')
        verbose_name_plural = _('Action Infos')
