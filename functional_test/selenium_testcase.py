# -*- coding: utf-8 -*-
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

import base64
import os
import json
from datetime import date, datetime
import time
from typing import Tuple, List, Dict, Union, Optional
from unittest import TestCase
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    TimeoutException
)
# from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException

# TODO NOP-2521, move to configuration file


FIREFOX_BROWSER_IDENTIFIER = 'Firefox'
CHROME_BROWSER_IDENTIFIER = 'Chrome'

DEFAULT_IMPLICITLY_WAIT_TIME = 5
DEFAULT_SCRIPT_TIMEOUT = 10
DEFAULT_PLATFORM = 'LINUX'
DEFAULT_PAGE_LOAD_TIMEOUT = 25
DEFAULT_BROWSER_OPEN_TIMEOUT = 10
FILE_ACCESS_TIMEOUT = 30
MINIMUM_FILE_COUNT = 1
BROWSER_OPEN_ATTEMPT_DELAY = 0.1
DEFAULT_LOCAL_BROWSER_NAME = CHROME_BROWSER_IDENTIFIER
DEFAULT_DOWNLOAD_LOCATION = \
    os.path.join(os.path.expanduser('~'), 'selenium_tests')
BY_ID = By.ID
BY_CLASS = By.CLASS_NAME
BY_NAME = By.NAME
BY_XPATH = By.XPATH
BY_VALUE = 'value'
BY_TEXT = 'text'
BY_TAG = By.TAG_NAME

RADIO_OPTION = 'radio-option'
DROPDOWN_OPTION = 'dropdown-option'
CHECKBOX_OPTION = 'checkbox-option'
TEXT_OPTION = 'text-option'

if not os.path.isdir(DEFAULT_DOWNLOAD_LOCATION):
    os.mkdir(DEFAULT_DOWNLOAD_LOCATION)


class BrowserOpenTimeoutError(TimeoutError):
    pass


class SeleniumCommonOperationsMixin():
    """
    Tries to simplify and clarify many of the common Selenium operations
    by abstracting them to SeleniumTestCase class methods.
    """

    def wait(self, timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT) -> WebDriverWait:
        """
        Thin wrapper for the Selenium WebDriverWait class.
        Returns an instance object of that class, generally for use with
        something like its .until(<condition>) method.

        :param timeout: The amount of time to wait until the
                later-specified condition is met before throwing an
                error.  Default: DEFAULT_PAGE_LOAD_TIMEOUT.
        """
        return WebDriverWait(self.browser_driver, timeout)

    def wait_for_element(
            self,
            element_identifier: str,
            by: str = BY_ID,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT
    ) -> None:
        """
        Handy wrapper for the Selenium WebDriverWait class that waits
        for an element to be present in the DOM.

        :param element_identifier: The element identifier, either an ID
                or a class name.
        :param by: BY_ID (default), BY_CLASS, BY_XPATH or BY_NAME
        :param timeout: The amount of time the wait should last before
                throwing an error.  Default: DEFAULT_PAGE_LOAD_TIMEOUT.
        :raises ValueError: If the by parameter is an invalid option
        :raises TimeoutException: If the element does not become
                available within the specified (or default) timeout.
        :returns: The element that was waited for

        """
        wait = self.wait(timeout)
        if by == BY_ID:
            wait.until(EC.presence_of_element_located(
                (By.ID, element_identifier)))
        elif by == BY_CLASS:
            wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, element_identifier)))
        elif by == BY_XPATH:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, element_identifier)))
        elif by == BY_NAME:
            wait.until(EC.presence_of_element_located(
                (By.NAME, element_identifier)))
        else:
            raise ValueError(
                'Can only wait for elements selectable by BY_ID or \
                BY_CLASS or BY_XPATH or BY_NAME'
            )

    def wait_for_element_to_be_visible(
            self,
            element_identifier: str,
            by: str = BY_ID,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT
    ) -> None:
        """
        Selects a specified element on the screen and
        waits for the element to become visible.

        :param element_identifier: The element identifier using the
            by= argument to determine the element to check for
            visibility
        :param by: The options to check for the element with.
            Options are BY_ID, BY_CLASS, BY_XPATH and BY_NAME
            defaults to BY_ID
        :param timeout: The amount of time the wait should
            last before raising an error.
            Defaults to the value set in DEFAULT_PAGE_LOAD_TIMEOUT
        :raises ValueError: If the by parameter is an invalid option
        :raises TimeoutException:
            If the element does not turn visible within the timeout time
        """
        wait = self.wait(timeout)
        if by == BY_ID:
            wait.until(EC.visibility_of_element_located(
                (By.ID, element_identifier)))
        elif by == BY_CLASS:
            wait.until(EC.visibility_of_element_located(
                (By.CLASS_NAME, element_identifier)))
        elif by == BY_XPATH:
            wait.until(EC.visibility_of_element_located(
                (By.XPATH, element_identifier)))
        elif by == BY_NAME:
            wait.until(EC.visibility_of_element_located(
                (By.NAME, element_identifier)))
        else:
            raise ValueError(
                'Can only wait for elements selectable by BY_ID \
                    or BY_CLASS or BY_XPATH or BY_NAME'
            )

    def wait_for_element_to_be_clickable(
            self,
            element_identifier: str,
            by: str = BY_ID,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT
    ) -> None:
        """
        Selects a specified element on the screen and waits for the
        element to become clickable.

        :param element_identifier: The element identifier using the by=
                argument to determine the element to check if clickable
        :param by: The options to check for the element with. Options
                are BY_ID, BY_CLASS, BY_XPATH and BY_NAME.
                Defaults to BY_ID
        :param timeout: The amount of time the wait should last before
                raising an error. Defaults to the value
                set in DEFAULT_PAGE_LOAD_TIMEOUT
        :raises ValueError: If the by parameter is an invalid option
        :raises TimeoutException:
                If the element does not turn visible within the
                timeout time
        """
        wait = self.wait(timeout)
        if by == BY_ID:
            wait.until(EC.element_to_be_clickable(
                (By.ID, element_identifier)))
        elif by == BY_CLASS:
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, element_identifier)))
        elif by == BY_XPATH:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, element_identifier)))
        elif by == BY_NAME:
            wait.until(EC.element_to_be_clickable(
                (By.NAME, element_identifier)))
        else:
            raise ValueError(
                'Can only wait for elements Clickable by BY_ID \
                    or BY_CLASS or BY_XPATH or BY_NAME'
            )

    def wait_for_element_to_not_be_visible(
            self, element_identifier: str, by: str = BY_ID,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT) -> None:
        """
        Selects a specified element on the screen and waits
        for the element to become invisible
        or removed from the dom.

        :param element_identifier: The element identifier using the by=
                argument to determine the element to check
                for visibility
        :param by: The options to check for the element with. Options
                are BY_ID and BY_CLASS. Defaults to BY_ID
        :param timeout: The amount of time the wait should last before
                raising an error. Defaults to the value
                set in DEFAULT_PAGE_LOAD_TIMEOUT
        :raises ValueError: If the by parameter is an invalid option
        :raises TimeoutException:
                If the element does not turn visible within the
                timeout time
        :raises NoSuchElementException: If the element specified by the
                element_identifier and the by does not exist in the DOM
        """
        wait = self.wait(timeout)
        if by == BY_ID:
            wait.until(EC.invisibility_of_element_located(
                (By.ID, element_identifier)))
        elif by == BY_CLASS:
            wait.until(EC.invisibility_of_element_located(
                (By.CLASS_NAME, element_identifier)))
        elif by == BY_XPATH:
            wait.until(EC.invisibility_of_element_located(
                (By.XPATH, element_identifier)))
        elif by == BY_NAME:
            wait.until(EC.invisibility_of_element_located(
                (By.NAME, element_identifier)))
        else:
            raise ValueError(
                'Can only wait for elements selectable by BY_ID or BY_CLASS'
            )

    def wait_for_alert_to_be_visible(
            self,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT
    ) -> None:
        """
        Selects a specified element on the screen and waits for the
        element to become invisible or removed from the dom.

        :param element_identifier: The element identifier using the by=
                argument to determine the element to
                check for visibility
        :param by: The options to check for the element with.
                Options are BY_ID and BY_CLASS defaults to BY_ID
        :param timeout: The amount of time the wait should last before
                raising an error. Defaults to the value
                set in DEFAULT_PAGE_LOAD_TIMEOUT
        :raises ValueError: If the by parameter is an invalid option
        :raises TimeoutException:
                If the element does not turn visible within
                the timeout time
        :raises NoSuchElementException: If the element specified by the
                element_identifier and the by does not exist in the DOM
        """
        wait = self.wait(timeout)
        wait.until(EC.alert_is_present())

    def wait_for_and_find_element(
            self,
            element_identifier: str,
            by: str = BY_ID,
            source: Optional[WebElement] = None,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT
    ) -> Union[WebElement, None]:
        """
        Handy wrapper for the Selenium WebDriverWait class that waits
        for an element to be present in the DOM. Will return the found
        element once it shows

        :param element_identifier: The element identifier, either an ID
                or a class name.
        :param by: BY_ID (default), BY_CLASS, BY_XPATH or BY_NAME
        :param source: The web element to extract the elements from.
            If left empty or set to None, the elements will be extracted
            from the currently displayed page
        :param timeout: The amount of time the wait should last before
                throwing an error.  Default: DEFAULT_PAGE_LOAD_TIMEOUT.
        :raises ValueError: If the by parameter is an invalid option
        :returns: The element that was waited for
        :returns: None if there is no element that can be identified
        """
        wait = self.wait(timeout)
        try:
            wait.until(EC.presence_of_element_located(
                (by, element_identifier)))
            return self.find_element(element_identifier, by, source)
        except TimeoutException:
            return None

    # TODO add meta tag that could be use to check page
    # load correctly NOP-2619
    def wait_for_page(
            self,
            page_title: str,
            timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT
    ) -> None:
        """
        Ultimately wraps the Selenium WebDriverWait class to await
        the condition where the title of the page is equal to the
        provided string.

        :param page_title: The string to which the page title must be
                equal to consider the condition met.
        :param timeout: The amount of time to wait before raising an
                error.  Default: DEFAULT_PAGE_LOAD_TIMEOUT.
        :raises TimeoutException: If the page's title does not become
                equal to the page_title string by the timeout.
        """
        self.wait(timeout).until(EC.title_is(page_title))

    def get_page(
            self,
            url: str,
            *args,
            **kwargs
    ) -> None:
        """
        Navigates the Selenium-controlled web browser to the provided
        URL.

        :param url: The URL to which the browser is to be directed.
        """
        self.browser_driver.get(url, *args, **kwargs)

    def find_element(
            self,
            element_identifier: str,
            by: str = BY_ID,
            source: Optional[WebElement] = None,
            allow_element_not_exist: bool = False
    ) -> Union[WebElement, None]:
        """
        Collects a single element based on the provided
        identifier and option
        :param element_identifier: The string to identify the element
            with using the option selected in the by parameter
        :param by: The method the element should be identified with.
            Supports BY_ID, BY_CLASS, BY_NAME, BY_TAG and BY_XPATH.
            Defaults to BY_ID
        :param source: The web element to extract the elements from.
            If left empty or set to None, the elements will be
            extracted from the currently displayed page
        :param allow_element_not_exist:
            if False, raise NoSuchElement error if couldn't find
            the elements.If True, return None if couldn't
            find the elements.
        :returns The first located element in the source that fit the
            specifications as defined by the element_identifier and the
            by parameters.
        :returns None if there is no element that can be identified
        :raises ValueError: If the by parameter is an invalid option
        """
        elements = self.find_elements(
            element_identifier, by, source, allow_element_not_exist)
        return elements[0] if elements else None

    def find_elements(
            self, element_identifier: str, by: str = BY_ID,
            source: Optional[WebElement] = None,
            allow_element_not_exist: bool = False
    ) -> Union[List[WebElement], None]:
        """
        Collects a list of elements based on the provided identifier
        and option
        :param element_identifier: The string to identify the element
            with using the option selected in the by parameter
        :param by: The method the element should be identified with.
            Supports BY_ID, BY_CLASS, BY_NAME, BY_TAG and BY_XPATH.
            Defaults to BY_ID
        :param source: The web element to extract the elements from.
            If left empty or set to None, the elements will be extracted
            from the currently displayed page.
        :param allow_element_not_exist:
            if False, raise NoSuchElement error if couldn't
            find the elements.If True, return None if couldn't
            find the elements.
        :returns A list of all the elements in the source that fit the
            specifications as defined by the element_identifier
            and the by parameters.
        :returns None if there is no element that can be
            found producing a NoSuchElementException
        :raises ValueError: If the by parameter is an invalid option
        """
        try:
            source = source if source else self.browser_driver
            return source.find_elements(value=element_identifier, by=by)
        except NoSuchElementException:
            if allow_element_not_exist:
                return None
            else:
                raise NoSuchElementException
                (f'Fail to find the {element_identifier} elements {by}')

    def element_has_class(
            self,
            element_identifier: str,
            class_name: str,
            by: str = BY_ID
    ) -> bool:
        """
        Searches the DOM for an element identified by either an ID
        (by=BY_ID, the default) or a class name (by=BY_CLASS), and
        returns True if that element has the specified class name, or
        False if it does not.
        Remember that elements may have more than one class, and be
        careful when identifying elements by class, in case more than
        one match exists.

        :param element_identifier: The element identifier, either an ID
                or a class name.
        :param class_name: The class name to match against the list of
                classes on the located element.
        :param by: The attribute to match when locating an element by
                element_identifier; either BY_ID (default) or BY_CLASS.
        :raises ValueError: If the by parameter is an invalid option.
        :raises NoSuchElementException: If the element specified by
                element_identifier  does not exist in the DOM.
        :raises TimeoutException: If the element does not become
                available within the specified (or default) timeout.
        """
        element = self.find_element(element_identifier, by=by)
        has_class = EC.attribute_contains(element, 'class', class_name)
        return has_class

    def element_contains_attribute(
            self,
            element_identifier: str,
            attribute_name: str,
            by: str = BY_VALUE
    ) -> None:
        """
        Check if a DOM element still contains the specified attribute.

        :param element_identifier: The element identifier, either an ID
                or a class name.
        :param attribute_name: The name of the attribute to search for.
        :param by: The attribute to match when locating an element by
                element_identifier; either BY_ID (default) or BY_CLASS.
        :raises ValueError: If the by parameter is an invalid option.
        :raises NoSuchElementException: If the element specified by
                element_identifier does not exist in the DOM.
        """
        element = self.find_element(element_identifier, by=by)
        attribute_present = element.get_attribute(attribute_name)
        if attribute_present is None:
            return False
        else:
            return attribute_present

    def populate_text_field(
            self,
            text_input_element_id: str,
            value: str,
            by: str = BY_ID
    ) -> None:
        """
        Send a string to a text input field on the web page as if they
        were typed on the keyboard.
        Does not verify that the element is, in fact, a text input
        element.

        :param text_input_element_id: The text input element identifier
                (ID or name).
        :param value: A string to enter into the text input field.
        :raises NoSuchElementException: If the element specified by
                text_input_element_id does not exist in the DOM.
        """
        self.wait_for_element_to_be_visible(text_input_element_id, by)
        input_field = self.find_element(text_input_element_id, by)
        input_field.clear()
        input_field.send_keys(value)

    def click_button(
            self,
            button_element_identifier: str,
            by: str = BY_ID,
            await_page_load: bool = False,
            load_page_title: Optional[str] = None
    ) -> None:
        """
        Send a mouse click event to an element on the web page
        (usually a button).

        :param button_element_identifier: The button (or other)
                element to which to send the click event.
        :param by: The attribute to match when locating an element by
                button_element_identifier; either BY_ID (default) or
                BY_CLASS.
        :param await_page_load: Sometimes after clicking an element, a
                test might expect the page to refresh or a new page to
                load. This option causes the function to wait for that
                to happen.
        :param load_page_title: If the above option is selected, also
                verifies that the page that gets loaded is the correct
                one, by specifying the title of the intended page.
        :raises NoSuchElementException: If the element specified by
                button_element_identifier does not exist in the DOM.
        :raises TimeoutException: If the element specified by
                button_element_identifier does not become enabled
                within the established DEFAULT_PAGE_LOAD_TIMEOUT time.
        """
        if await_page_load:
            page_title = self.browser_driver.current_url

        # Solves an issue on firefox where the element is not clickable
        for i in range(DEFAULT_SCRIPT_TIMEOUT):
            try:
                button_element = self.wait_for_and_find_element(
                    button_element_identifier, by)
                if button_element is None:
                    raise NoSuchElementException
                self.wait().until(lambda driver: button_element.is_enabled())
                self.wait().until(EC.element_to_be_clickable(
                    (by, button_element_identifier)))
                self.scroll_to(button_element_identifier, by)
                button_element.click()
                if await_page_load:
                    if load_page_title:
                        self.wait_for_page(load_page_title)
                    else:
                        self.wait_for_page(page_title)
                return
            except ElementClickInterceptedException:
                time.sleep(1)
        raise ElementClickInterceptedException

    def click_checkbox(
            self,
            checkbox_element_identifier: str,
            by: str = BY_ID,
            checked: bool = True,
    ) -> None:
        """
        Sets the checkbox to the requested value

        :param checkbox_element_identifier:
            The checkbox to which to send the click event.
        :param by: The attribute to match when locating an element by
                checkbox; either BY_ID (default) or
                BY_CLASS.
        :param checked: Sometimes after clicking a checkbox,
                it wont actually be checked. Provide what state you want
                the checkbox to be in.(Default True)
        :raises NoSuchElementException: If the element specified by
                checkbox_element_identifier does not exist in the DOM.
        """

        checkbox_element = self.find_element(
            checkbox_element_identifier, by=by)
        while not checkbox_element.is_selected() == checked:
            checkbox_element.click()

    def populate_form(self, data_list):
        """
        Populates specified elements on the page with provided values
        data_list format:
        [
            {
                'type': <element type>,
                'id': <id of the form field to populate>,
                'by': <BY_VALUE (default) the method of matching \
                    option>,
                'value': <The option to select or value to input for \
                    text fields>
                'list': None | [
                    {
                        <Same format as previous defined schema. \
                        Used to chain selection of fields>
                    }
                ]
            },
            <additional command sets>
        ]
        """
        for entry in data_list:
            if entry['type'] == DROPDOWN_OPTION:
                self.select_dropdown_item(
                    entry['id'],
                    entry['value'],
                    entry['by']
                )
            elif entry['type'] == CHECKBOX_OPTION:
                self.click_checkbox(entry['id'], BY_ID, entry['value'])
            elif entry['type'] == RADIO_OPTION:
                self.find_element(entry['id']).click()
            elif entry['type'] == TEXT_OPTION:
                self.populate_text_field(entry['id'], entry['value'])
            if entry['list'] is not None:
                self.populate_form(entry['list'])

    def select_dropdown_item(
            self,
            dropdown_identifier: str,
            item_identifier: str,
            by: str = BY_VALUE,
            element_by: str = BY_ID
    ) -> None:
        """
        Find a specified dropdown field (<select>) in the DOM,
        and select one of the items (<option>) within it, either by
        its form value or its visible text representation.

        :param dropdown_identifier: The <select> element's ID.
        :param item_identifier: The <option> within the dropdown to
                select, either by form field value ('value' attribute,
                specified by BY_VALUE, default), or by visible text
                representation (element contents, specified by BY_TEXT).
        :param by: BY_VALUE (default) to match item_identifier on the
                form value of the desired <option>, or BY_TEXT to match
                on the visible text representation of the element.
        :param element_by: BY_ID (default) to match element by its id
                or BY_NAME, BY_XPATH or BY_CLASS
        :raises NoSuchElementException: If the element specified by
                button_element_identifier does not exist in the DOM.
        :raises ValueError: If the 'by' parameter is not one of the
                acceptable options BY_VALUE or BY_TEXT.
        """
        self.wait_for_element_to_be_visible(dropdown_identifier, element_by)
        dropdown = Select(self.find_element(dropdown_identifier, element_by))
        if by == BY_VALUE:
            dropdown.select_by_value(item_identifier)
        elif by == BY_TEXT:
            dropdown.select_by_visible_text(item_identifier)
        else:
            raise ValueError(
                'Can only select a dropdown value by BY_VALUE or BY_TEXT.'
            )

    def scroll_to(
            self,
            element_identifier: str,
            by: str = BY_ID
    ):
        """
        Scroll the rendered (visible) view of the webpage until it
        includes a particular element.

        :param element_identifier: The element identifier, either an ID
                or a class name, to scroll into view.
        :param by: The attribute to match when locating an element by
                element_identifier; either BY_ID (default) or BY_CLASS.
        """
        element = self.find_element(element_identifier, by=by)
        self.browser_driver.execute_script(
            'arguments[0].scrollIntoView()', element)

    def collect_table_headers_and_data(
            self,
            table: WebElement,
            has_id=False
    ) -> Tuple[List[str], Dict[int, Dict[str, str]]]:
        """
        Collect the data of the table on the webpage selected by
            table web-element or By_ID and return the header data
            and body data of the table as separate iterable values.
        :param table: the table element to read from
        :returns table_headers: A List containing the text for \
        the headers of the table
        :returns table_body: A Dict containing all the rows \
            of data in the format:
            {
                <row_number>:{
                    <column_id>:<column_value>,
                    <Continue data for remaining columns>
                },
                <Continue Rows for each row in the table>
            }
        """

        table_header_row = table.find_element
        (By.TAG_NAME, 'thead').find_element(By.TAG_NAME, 'tr')

        # Collect the text of the headers
        table_headers = [head.text for head in table_header_row.find_elements(
            By.TAG_NAME, 'th')]

        table_rows = table.find_element(By.TAG_NAME, 'tbody').find_elements(
            By.TAG_NAME, 'tr')

        table_body = {
            count: { # noqa E501
                (col.get_attribute('id') if has_id else col_num): col.text for col_num, col in enumerate(row.find_elements(By.TAG_NAME, 'td')) # noqa E501
            }
            for count, row in enumerate(table_rows) if row.text
        }

        return table_headers, table_body

    def collect_json_data(self) -> Dict:
        """
        Assumptions: The web page is opened on a page displaying
            just json data
        :return: The JSON that's displayed on the
            page in a python dict format
        """

        body = self.find_element('body', by=BY_TAG)
        data = json.loads(body.text)

        return data

    def hover_over_element(
            self,
            element: WebElement,
            x_offset: Optional[int] = 0,
            y_offset: Optional[int] = 0,
            click: Optional[bool] = False) -> None:
        """
        Using Webdriver Actions, take an element and hover
        the cursor over the element.
        :param element: The WebElement to hover over.
            Hovering will start in the upper left corner of the element
        :param x_offset: The amount, in pixels, to move the cursor
            horizontally from the upper left corner.
            Positive values moves the cursor to the right
            Negative values moves the cursor to the left
            Default Value: 0
        :param y_offset: The amount, in pixels, to move the cursor
            vertically from the upper left corner
            Positive values moves the cursor down
            Negative values moves the cursor up
            Default value: 0
        :param click: A boolean indicating if there's the desire to use
            the click action on the element.
            This will use the cursor to click the element as
            opposed to Selenium's element clicking
            Default value: False
        """

        action = ActionChains(self.browser_driver)
        action.move_to_element_with_offset(element, x_offset, y_offset)
        if click:
            action.click()
        action.perform()

    def accept_alert(
            self, timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT):
        """
        Accepts the alert that is currently on screen
        """
        wait = self.wait(timeout)
        wait.until(EC.alert_is_present())
        alert = self.browser_driver.switch_to.alert
        alert.accept()
        wait.until(lambda i: not EC.alert_is_present()(i))

    def decline_alert(
            self, timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT):
        """
        Declines the alert that is currently on screen
        """
        wait = self.wait(timeout)
        wait.until(EC.alert_is_present())
        alert = self.browser_driver.switch_to.alert
        alert.decline()
        wait.until(lambda i: not EC.alert_is_present()(i))

    def refresh_page(self):
        """
        Refreshes the current browser page
        """
        self.browser_driver.refresh()

    def show_cursor(self):
        """
        Shows the location of the cursor on the current page
        until it is refreshed.
        Can be used to track mouse movements during testing
        """
        self.browser_driver.execute_script(
            """
                var cursorCover = document.createElement('div');
                cursorCover.style['position']='fixed';
                cursorCover.style['width']='5px';
                cursorCover.style['height']='5px';
                cursorCover.style['border']= '1px solid red';
                cursorCover.style['border-radius']='5px';
                cursorCover.style['pointer-events']='none';
                cursorCover.id='cursorCover';
                document.body.appendChild(cursorCover);
                document.body.addEventListener("mousemove", function(event) {
                    document.getElementById('cursorCover').style.left=`${event.clientX-2.5}px`;
                    document.getElementById('cursorCover').style.top=`${event.clientY-2.5}px`;
                });
            """
        )


class SeleniumTestCase(TestCase, SeleniumCommonOperationsMixin):
    """
    Customized unittest TestCase for Selenium tests. Test authors
    should subclass this TestCase for their own tests. This TestCase
    contains open browser and close browser functions.
    """

    node_url = None
    browser_name = None
    browser_driver = None
    node_platform = DEFAULT_PLATFORM

    def __init__(self, *args, **kwargs):
        super(SeleniumTestCase, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up the class testing
        Note: Always have calling this setUpClass the last
        instruction for any and all subclasses that use
        a setUpClass function
        """
        super(SeleniumTestCase, cls).setUpClass()
        if not cls.browser_name:
            cls.browser_name = DEFAULT_LOCAL_BROWSER_NAME
        cls.remote_testing = True if cls.node_url else False
        cls._class_start = time.time()
        cls._open_browser()

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Finish the testing for this class by removing processes
        that is currently being used
        """
        super(SeleniumTestCase, cls).tearDownClass()
        cls._close_browser()

    @classmethod
    def _open_browser(cls) -> None:
        """
        Set up Selenium web browser driver,
        Configure default settings of the testing browser.
        :raises WebDriverException: IF the web browser is unable to be
        opened in the amount of time set in DEFAULT_BROWSER_OPEN_TIMEOUT
        """
        # Create the browser profile
        parameters = 'options=options'
        # remote = {}
        if cls.browser_name.lower() == FIREFOX_BROWSER_IDENTIFIER.lower():
            options = webdriver.FirefoxOptions()
            options.set_capability('platformName', cls.node_platform)
            options.set_preference('browser.download.folderList', 2)
            options.set_preference(
                'browser.download.manager.showWhenStarting', False)
            options.set_preference(
                'browser.download.dir', DEFAULT_DOWNLOAD_LOCATION)
            options.set_preference(
                'browser.helperApps.neverAsk.saveToDisk',
                'application/octet-stream,application/pdf,text/csv'
            )
            options.set_preference('browser.download.useDownloadDir', True)
            options.set_preference(
                'browser.download.manager.showWhenStarting', False)
            options.set_preference(
                'browser.download.animateNotifications', False)
            options.set_preference(
                'browser.safebrowsing.downloads.enabled', False)
            options.set_preference('browser.download.folderList', 2)
            options.set_preference('pdfjs.disabled', True)
            options.set_preference('javascriptEnabled', True)
            options.set_preference('jacceptSslCerts', True)
            options.set_preference('acceptInsecureCerts', True)

        elif cls.browser_name.lower() == CHROME_BROWSER_IDENTIFIER.lower():
            options = webdriver.ChromeOptions()
            options.add_experimental_option('prefs', {
                'download.default_directory': DEFAULT_DOWNLOAD_LOCATION,
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True,
            })

        start_opening_browser = time.time()
        exception = ''

        while (time.time() - start_opening_browser) < DEFAULT_BROWSER_OPEN_TIMEOUT: # noqa E501
            try:
                # Configure browser capabilities for
                # remote testing platform
                if cls.remote_testing:
                    # Setup browser capabilities
                    # if cls.browser_name.lower() == 'ff' or cls.browser_name.lower() == 'firefox': # noqa E501
                    #     desired_capabilities = DesiredCapabilities.FIREFOX.copy() # noqa E501
                    # elif cls.browser_name.lower() == 'ie':
                    #     desired_capabilities = DesiredCapabilities.INTERNETEXPLORER.copy() # noqa E501
                    # elif cls.browser_name.lower() == 'chrome':
                    #     desired_capabilities = DesiredCapabilities.CHROME.copy() # noqa E501
                    # elif cls.browser_name.lower() == 'opera':
                    #     desired_capabilities = DesiredCapabilities.OPERA.copy() # noqa E501
                    # elif cls.browser_name.lower() == 'safari':
                    #     desired_capabilities = DesiredCapabilities.SAFARI.copy() # noqa E501
                    cls.browser_driver = webdriver.Remote(
                        command_executor=cls.node_url,
                        options=options,
                    )
                else:
                    # If running test locally,
                    # use the installed Selenium browser driver
                    exec('cls.browser_driver=webdriver.{}({})'.format(cls.browser_name, parameters)) # noqa E501
                    cls.browser_driver.maximize_window()
                break
            except WebDriverException as e:
                exception = e
                time.sleep(BROWSER_OPEN_ATTEMPT_DELAY)
        else:
            error_message = ('Test Suite {} timed out when attempting to open \
                             browser after {} seconds (actual waited {})'
                             ).format(
                cls.__name__,
                DEFAULT_BROWSER_OPEN_TIMEOUT,
                round((time() - start_opening_browser), 2),)
            raise BrowserOpenTimeoutError(exception, error_message)

        cls.browser_driver.set_page_load_timeout(DEFAULT_PAGE_LOAD_TIMEOUT)
        cls.browser_driver.set_script_timeout(DEFAULT_SCRIPT_TIMEOUT)

    @classmethod
    def _close_browser(cls) -> None:
        """
        Quit testing browser
        """
        cls.browser_driver.quit()
        cls.browser_driver = None

    def setUp(self) -> None:
        """
        Start the test by printing out and recording
        the method name and start time
        self.method_start_time =
         self._print_method_name_and_start_time()
        """
        super(SeleniumTestCase, self).setUp()

    def tearDown(self) -> None:
        """
        Close out the currently finished test and report
        the test and time
        """
        self._report_error()
        super(SeleniumTestCase, self).tearDown()

    def _print_method_name_and_start_time(self) -> float:
        if self.remote_testing:
            print('Started at {}'.format(datetime.now()), end='')
        else:
            print('Test {} started at {}'.format(
                self._testMethodName, datetime.now()), end='')
        return time()

    def _print_end_time(self) -> None:
        print(' ({}s)'.format(round(time() - self.method_start_time, 2)))

    def _report_error(self) -> None:
        """
        Report an error occurring by taking a screenshot of the web page
        and the time of it happening
        """
        for method, error in self._outcome.errors:
            if error:
                test_case = str(method).split()[0]
                # TODO get executing this working again
                # print(
                # self.browser_driver.execute_script('return window.getLogs();')) # noqa E501
                self.browser_driver.save_screenshot
                ('/home/grenmap_functional_test/{}-{}-{}.png'.format(
                    date.today().strftime('%Y-%m-%d'),
                    test_case,
                    self.browser_driver.name,
                ))

    def collect_downloaded_files(
            self,
            download_location: str = DEFAULT_DOWNLOAD_LOCATION,
            requested_filename: str = None
    ) -> str:
        """
        Accesses the remote browser node to transfer all, or specified
        downloaded files from the remote node to the local
        node to be read.
        :param requested_filename: If a single file is desired
            from the remote browser, then enter this parameter with the
            filename and extension of the file to be downloaded
        :param download_location: A file path to download
            the extracted files.
        :raises AssertionError: If a filename is given, this error is
            raised if there's no file with the given name
        :raises FileNotFoundError: If the DEFAULT_DOWNLOAD_LOCATION does
                                    not exist
        :raises WebDriverTimeout: If there is no file downloaded in
                                    the remote browser
        """

        if not self.remote_testing:
            return DEFAULT_DOWNLOAD_LOCATION

        try:
            if self.browser_name.lower() == FIREFOX_BROWSER_IDENTIFIER.lower():
                file_paths = WebDriverWait(self.browser_driver, FILE_ACCESS_TIMEOUT, MINIMUM_FILE_COUNT).until( # noqa E501
                    self._mozilla_file_names
                )
            elif self.browser_name.lower() == CHROME_BROWSER_IDENTIFIER.lower(): # noqa E501
                file_paths = WebDriverWait(self.browser_driver, FILE_ACCESS_TIMEOUT, MINIMUM_FILE_COUNT).until( # noqa E501
                    self._chrome_file_names
                )

            if requested_filename:
                files = [os.path.basename(file) for file in file_paths]
                self.assertIn(
                    requested_filename,
                    files,
                    'The file requested from the remote\
                     downloads directory not found')
            for file in file_paths:
                filename = os.path.basename(file)
                if not requested_filename or filename == requested_filename:
                    with open(os.path.join(download_location, filename), 'wb') as f: # noqa E501
                        if self.browser_name.lower() == FIREFOX_BROWSER_IDENTIFIER.lower(): # noqa E501
                            f.write(self._get_file_content_moz(file))
                        elif self.browser_name.lower() == CHROME_BROWSER_IDENTIFIER.lower(): # noqa E501
                            f.write(self._get_file_content_chrome(file))
        finally:
            # If an error is thrown without setting the context back to content, reset it back # noqa E501
            try:
                self.browser_driver.execute(
                    'SET_CONTEXT', {'context': 'content'})
            except KeyError:
                # If the context is already content,
                # the above code could throw a KeyError.
                pass

        return download_location

    @staticmethod
    def _mozilla_file_names(driver: webdriver):
        """
        Iterator yields files recently downloaded by the browser.
        Mozilla is shorthand for the Firefox browser.
        """
        driver.command_executor._commands['SET_CONTEXT'] = (
            'POST', '/session/$sessionId/moz/context')
        driver.execute('SET_CONTEXT', {'context': 'chrome'})
        return driver.execute_async_script(
            """
            var { Downloads } = Components.utils.import(
                'resource://gre/modules/Downloads.jsm', {});
            Downloads.getList(Downloads.ALL)
                .then(list => list.getAll())
                .then(entries => entries.filter(e => e.succeeded).map(
                    e => e.target.path))
                .then(arguments[0]);
            """
        )
        driver.execute('SET_CONTEXT', {'context': 'content'})

    # moz stand for Firefox browser
    def _get_file_content_moz(self, path: str) -> bytes:
        self.browser_driver.execute('SET_CONTEXT', {'context': 'chrome'})
        result = self.browser_driver.execute_async_script("""
            var { OS } = Cu.import('resource://gre/modules/osfile.jsm', {});
            OS.File.read(arguments[0]).then(function(data) {
                var base64 = Cc['@mozilla.org/scriptablebase64encoder;1'].
                                                          getService(Ci.nsIScriptableBase64Encoder);
                var stream = Cc['@mozilla.org/io/arraybuffer-input-stream;1'].
                                                          createInstance(Ci.nsIArrayBufferInputStream);
                stream.setData(data.buffer, 0, data.length);
                return base64.encodeToString(stream, data.length);
            }).then(arguments[1]);
            """, path)
        self.browser_driver.execute('SET_CONTEXT', {'context': 'content'})
        return base64.b64decode(result)

    @staticmethod
    def _chrome_file_names(driver: webdriver):
        if not driver.current_url.startswith("chrome://downloads"):
            driver.get("chrome://downloads/")

        return driver.execute_script(
            "return downloads.Manager.get().items_   "
            "  .filter(e => e.state === 'COMPLETE')  "
            "  .map(e => e.filePath || e.file_path); ")

    def _get_file_content_chrome(self, path):

        elem = self.browser_driver.execute_script(
            "var input = window.document.createElement('INPUT'); "
            "input.setAttribute('type', 'file'); "
            "input.hidden = true; "
            "input.onchange = function (e) { e.stopPropagation() }; "
            "return window.document.documentElement.appendChild(input); ")

        elem._execute('sendKeysToElement', {'value': [path], 'text': path})

        result = self.browser_driver.execute_async_script(
            "var input = arguments[0], callback = arguments[1]; "
            "var reader = new FileReader(); "
            "reader.onload = function (ev) { callback(reader.result) }; "
            "reader.onerror = function (ex) { callback(ex.message) }; "
            "reader.readAsDataURL(input.files[0]); "
            "input.remove(); ", elem)

        if not result.startswith('data:'):
            raise Exception("Failed to get file content: %s" % result)

        return base64.b64decode(result[result.find('base64,') + 7:])
