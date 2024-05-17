
import pytest

from base_app.models.app_configurations import Token
from base_app.utils.access_control import get_token

# String with 32 chars that serves as a token value.
TEST_TOKEN = '12345678' * 4
TEST_TYPE = 'grenml_import'


class MockRequest:
    def __init__(self):
        self._headers = {'Authorization': ''}
        self._META = {'PATH_INFO': ''}

    @property
    def headers(self):
        return self._headers

    @property
    def META(self):  # noqa: N802
        return self._META

    def set_token(self, token):
        self.headers['Authorization'] = 'Bearer {}'.format(token)
        return self

    def set_token_type(self, token_type):
        self.META['PATH_INFO'] = '/{}/verb'.format(token_type)
        return self


@pytest.mark.django_db
class TestGetToken:

    @pytest.mark.parametrize(
        'client_name, request_token, token_type',
        [
            # valid token, valid token_type
            ('test-client', TEST_TOKEN, TEST_TYPE),

            # invalid token, valid token_type
            (None, 'badtoken', TEST_TYPE),

            # no token
            (None, None, TEST_TYPE),

            # valid token, not valid token_type
            (None, TEST_TOKEN, 'test_app'),

            # valid token, no token_type
            (None, TEST_TOKEN, None),

            # no token, no token_type
            (None, None, None),
        ]
    )
    def test_normal_usage(self, client_name, request_token, token_type):
        expected_result = None
        if client_name:
            expected_result = Token.objects.create(
                client_name=client_name,
                token=request_token,
                token_type=token_type,
            )

        request = MockRequest().set_token(request_token).set_token_type(token_type)
        actual = get_token(request)
        assert expected_result == actual
