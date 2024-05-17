"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2020 GRENMap Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

------------------------------------------------------------------------

Synopsis: Project-wide view decorators.
"""

import functools

import base_app.utils.access_control as ac

from django.conf import settings
from django.core.exceptions import PermissionDenied


def translated_docstring(docstring):
    """
    Adds function or class docstrings in a way that supports inclusion
    of the text literal in the Python/Django auto translation matrix.
    This is useful if the docstring will end up facing the user,
    such as in the Django Admin.  Replaces any docstrings specified
    in the traditional manner.

    Usage example:

        from django.utils.translation import gettext_noop as _noop
        from base_app.utils.decorators import translated_docstring

        @translated_docstring(_noop('<docstring text goes here>'))
        class MyClass:
            ...
    """
    def decorate(class_or_function):
        class_or_function.__doc__ = docstring
        return class_or_function
    return decorate


def test_only(func):
    """
    Decorator for view functions to enforce their availability only
    when the TEST_MODE setting is True.

    Raises a PermissionDenied exception if the condition is not met,
    which will result in an HTTP 403 Forbidden.

    Usage example:

        from base_app.utils.decorators import test_only

        @test_only
        def my_view_function(request):
            ...
            return Response(...)

    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if settings.TEST_MODE:
            return func(*args, **kwargs)
        else:
            raise PermissionDenied
    return wrapper


def wrap_to_check_token(access_control_enabled, func):
    """
    Decorates func with access control code.

    Func should be a request handler (a function that takes
    a request and returns a response).

    Access_control_enabled should be a function without parameters
    that returns a boolean; True to enable the token check,
    False to disable it.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        if not ac.allow_request(request, access_control_enabled):
            raise PermissionDenied('Failed access control check')
        return func(*args, **kwargs)
    return wrapper


# Decorator that checks the access token if the development mode is off.
check_token = functools.partial(wrap_to_check_token, ac.is_in_production_mode)

# Decorator for endpoints which will always check the token.
always_check_token = functools.partial(wrap_to_check_token, lambda: True)
