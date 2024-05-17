
"""
This file contains gren-map-db-node basic IdP login tests
using selenium test framework
"""

import pytest
from constants import *
from framework import GrenMapUITestingFramework
from framework import BY_XPATH, BY_CLASS
from selenium_testcase import BY_VALUE

LOGIN_BUTTON_ID = 'fim_login'
LOGOUT_BUTTON_ID = 'fim_logout_user'
IDP_LOGIN_BUTTON_XPATH = '//button[@name="_eventId_proceed"]'
ADMIN_LOGIN_BUTTON_XPATH = '//input[@type="submit"]'
IDP_USERNAME_FIELD_ID = 'username'
IDP_PASSWORD_FIELD_ID = 'password'
IDP_ERROR_MESSAGE_XPATH = '//p[@class="form-element form-error"]'
AUTH_XPATH = '//a[contains(text(),"Authentication and Authorization")]'
ALLOW_USER_XPATH = '//div[@id="idpSelectIdPEntryTile"]/a[@href][1]'
IDP_DROPDOWN = 'idpSelectSelector'
IDP_URL = 'https://idp.example.org/idp/shibboleth'
CONTINUE_BUTTON_XPATH = '//*[@id="idpSelectListButton"]'
GREN_ADMIN_PAGE_ICON_ID = 'gren_icon'
CLEAR_LOGIN_CACHE_BOX_ID = 'donotcache'
ADMIN_USERNAME_ID = 'id_username'
ADMIN_PASSWORD_ID = 'id_password'
ADMIN_TOP_LINK_ID = 'user-tools'
DJANGO_LOGIN_PAGE_TITLE = 'Site administration | GREN Administration Portal'
DJANGO_ADMIN_LINK_XPATH = '//a[@href="/admin/"]'
LOGIN_INFO_CLASS = 'info'
LOGIN_ERROR_CLASS = 'error'
# Make sure the test user info is set up in the users.ldif file
TEST_USER_NAME_WITH_EPPN = 'testuser1'
TEST_USER_PASSWORD_WITH_EPPN = 'ChangePassword'
TEST_USER_FULL_NAME = 'User1'
TEST_USER_NAME_WITHOUT_EPPN = 'testuser4'
TEST_USER_PASSWORD_WITHOUT_EPPN = 'ChangePassword'
TEST_USER_WITH_EPPN_NON_ADMIN = 'testuser3'
TEST_USER_PASSWORD_WITH_EPPN_NON_ADMIN = 'ChangePassword'


class TestIdPLogin(GrenMapUITestingFramework):

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.load_fixture('test_app_configurations.json')

    def test_01_success_idp_login_process(self):
        """
        Test the login proces IdP successfully with correct user info,
        it should automatically gain access to django admin.
        """
        self._reach_idp_login_page()
        # Test IdP login
        self._idp_login(
            idp_username=TEST_USER_NAME_WITH_EPPN,
            idp_password=TEST_USER_PASSWORD_WITH_EPPN
        )
        # Test Django admin login welcome message
        self.wait_for_element_to_be_clickable(
            DJANGO_ADMIN_LINK_XPATH,
            BY_XPATH
        )
        welcome_message = self.find_element(LOGIN_INFO_CLASS, BY_CLASS).text
        assert TEST_USER_FULL_NAME in welcome_message, 'Fail with IdP login'
        # The first user with eppn obtained the admin permission
        self.find_element(DJANGO_ADMIN_LINK_XPATH, BY_XPATH).click()
        self.wait_for_page(DJANGO_LOGIN_PAGE_TITLE, timeout=5)

    def test_fail_login_with_empty_username_password(self):
        expected_error = 'The username you entered cannot be identified.'
        self._reach_idp_login_page()
        self.find_element(IDP_LOGIN_BUTTON_XPATH, BY_XPATH).click()
        # Check the error message with empty username and password
        self.wait_for_element_to_be_visible(IDP_ERROR_MESSAGE_XPATH, BY_XPATH)
        error_text = self.find_element(IDP_ERROR_MESSAGE_XPATH, BY_XPATH).text
        assert error_text == expected_error, \
            'Unexpected error message with empty username and password.'

    def test_fail_login_with_incorrect_username(self):
        expected_error = 'The username you entered cannot be identified.'
        self._reach_idp_login_page()
        self._idp_login(
            idp_username='errorusername',
            idp_password=TEST_USER_PASSWORD_WITH_EPPN
        )
        # Check the error message with incorrect username
        self.wait_for_element_to_be_visible(IDP_ERROR_MESSAGE_XPATH, BY_XPATH)
        error_text = self.find_element(IDP_ERROR_MESSAGE_XPATH, BY_XPATH).text
        assert error_text == expected_error, \
            'Unexpected error message with incorrect username'

    def test_fail_login_with_incorrect_password(self):
        expected_error = 'The password you entered was incorrect.'
        self._reach_idp_login_page()
        self._idp_login(
            idp_username=TEST_USER_NAME_WITH_EPPN,
            idp_password='errorpassword'
        )
        # Check the error message with incorrect password
        self.wait_for_element_to_be_visible(IDP_ERROR_MESSAGE_XPATH, BY_XPATH)
        error_text = self.find_element(IDP_ERROR_MESSAGE_XPATH, BY_XPATH).text
        assert error_text == expected_error, \
            'Unexpected error message with incorrect password.'

    def test_fail_login_with_empty_password(self):
        expected_error = 'The password you entered was incorrect.'
        self._reach_idp_login_page()
        self._idp_login(
            idp_username=TEST_USER_NAME_WITH_EPPN
        )
        # Check the error message with incorrect password
        self.wait_for_element_to_be_visible(IDP_ERROR_MESSAGE_XPATH, BY_XPATH)
        error_text = self.find_element(IDP_ERROR_MESSAGE_XPATH, BY_XPATH).text
        assert error_text == expected_error, \
            'Unexpected error message with incorrect password.'

    def test_idp_login_process_user_is_admin(self):
        """
        Test the login proces IdP successfully with correct user info,
        then user has admin privileges if user is defined
        as part of ADMIN_EPPNS in .env.dev file.
        """
        self._reach_idp_login_page()
        # Test IdP login
        self._idp_login(
            idp_username=TEST_USER_NAME_WITH_EPPN,
            idp_password=TEST_USER_PASSWORD_WITH_EPPN
        )
        # Test Django admin login
        self.wait_for_element_to_be_clickable(
            DJANGO_ADMIN_LINK_XPATH,
            BY_XPATH
        )
        self.find_element(DJANGO_ADMIN_LINK_XPATH, BY_XPATH).click()
        self.wait_for_page(DJANGO_LOGIN_PAGE_TITLE, timeout=5)
        authentication_authorization = self.find_element(AUTH_XPATH, BY_XPATH)
        assert authentication_authorization is not None, \
            'The user should have been an admin user'

    def test_idp_login_process_user_is_not_admin(self):
        """
        Test the login proces IdP successfully with correct user info,
        non admin user then user is not defined as part of
        ADMIN_EPPNS in .env.dev file.
        """
        self._reach_idp_login_page()
        # Test IdP login
        self._idp_login(
            idp_username=TEST_USER_WITH_EPPN_NON_ADMIN,
            idp_password=TEST_USER_PASSWORD_WITH_EPPN_NON_ADMIN
        )
        # Test Django admin login
        self.wait_for_element_to_be_visible(LOGOUT_BUTTON_ID)
        self.wait_for_element_to_be_clickable(LOGOUT_BUTTON_ID)
        admin_button = self.find_element(DJANGO_ADMIN_LINK_XPATH, BY_XPATH)
        assert admin_button is None, 'The non admin user has admin access'

    def _reach_idp_login_page(self):
        """
        This a helper function with all the steps to reach the
        IDP login page
        """
        self.get_page(TEST_SITE_URL)
        self.wait_for_element_to_be_clickable(LOGIN_BUTTON_ID)
        self.find_element(LOGIN_BUTTON_ID).click()
        self.find_element(ALLOW_USER_XPATH, BY_XPATH).click()
        self.select_dropdown_item(
            dropdown_identifier=IDP_DROPDOWN,
            item_identifier=IDP_URL,
            by=BY_VALUE
        )
        self.wait_for_element_to_be_clickable(CONTINUE_BUTTON_XPATH, BY_XPATH)
        self.find_element(CONTINUE_BUTTON_XPATH, BY_XPATH).click()
        self.wait_for_element_to_be_clickable(IDP_LOGIN_BUTTON_XPATH, BY_XPATH)

    def _idp_login(
            self,
            idp_username='',
            idp_password='',
    ):
        """
        This is a helper function with all the steps to log into map
        """
        self.populate_text_field(IDP_USERNAME_FIELD_ID, idp_username)
        self.populate_text_field(IDP_PASSWORD_FIELD_ID, idp_password)
        self.find_element(CLEAR_LOGIN_CACHE_BOX_ID).click()
        self.find_element(IDP_LOGIN_BUTTON_XPATH, BY_XPATH).click()
