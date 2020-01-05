import os
import re
import time
import unittest

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys


MAX_WAIT = 10


def wait_for_row_in_list_table(selenium, row_text):
    start_time = time.time()
    while True:
        try:
            table = selenium.find_element_by_id('id_list_table')
            rows = table.find_elements_by_tag_name('tr')
            assert row_text in [row.text for row in rows]
            return
        except (AssertionError, WebDriverException) as e:
            if time.time() - start_time > MAX_WAIT:
                selenium.quit()
                raise e
            time.sleep(0.5)


def test_can_start_a_list_and_retrieve_it_later(selenium, live_server):
    # Edith heard about a cool new online to-do app.
    # She goes to check out its homepage.
    selenium.get(live_server.url)

    # She notices the page title and header mention to-do lists
    assert 'To-Do' in selenium.title
    header_text = selenium.find_element_by_tag_name('h1').text
    assert 'To-Do' in header_text

    # She is invited to enter a to-do item straight away.
    inputbox = selenium.find_element_by_id('id_new_item')
    assert inputbox.get_attribute('placeholder') == 'Enter a to-do item'

    # She types "Buy peacock feathers" into a text box.
    inputbox.send_keys('Buy peacock feathers')

    # When she hits enter, the page updates, and now the page lists
    # "1: Buy peacock feathers" as an item in a to-do list
    inputbox.send_keys(Keys.ENTER)

    wait_for_row_in_list_table(selenium, '1: Buy peacock feathers')

    # There is still a text box inviting her to add another item.
    # She enters "Use peacock feathers to make a fly"
    inputbox = selenium.find_element_by_id('id_new_item')
    assert inputbox.get_attribute('placeholder') == 'Enter a to-do item'
    inputbox.send_keys('Use peacock feathers to make a fly')
    inputbox.send_keys(Keys.ENTER)
    time.sleep(1)

    # The page updates again, and now shows both items on her list
    wait_for_row_in_list_table(selenium, '1: Buy peacock feathers')
    wait_for_row_in_list_table(selenium, '2: Use peacock feathers to make a fly')

    # Satisfied she goes back to sleep.
    selenium.quit()

def test_multiple_users_can_start_lists_at_different_urls(selenium, live_server):
    # Edith starts a new to-do list
    selenium.get(live_server.url)
    inputbox = selenium.find_element_by_id('id_new_item')
    inputbox.send_keys('Buy peacock feathers')
    inputbox.send_keys(Keys.ENTER)
    wait_for_row_in_list_table(selenium, '1: Buy peacock feathers')

    # She notices that her list has a unique URL
    edith_list_url = selenium.current_url
    print(f'ELU: {edith_list_url}')
    assert re.search(r'/lists/.+', edith_list_url)

    # Now a new user, Francis, comes along to the site

    ## We use a new browser session to make sure that no information
    ## of Edith's is coming through from cookies etc
    selenium.quit()
    browser = webdriver.Firefox()

    # Francis visits the home page. There is no sign of Edith's list.
    browser.get(live_server.url)
    page_text = browser.find_element_by_tag_name('body').text
    assert 'Buy peacock feathers' not in page_text
    assert 'make a fly' not in page_text

    # Francis starts a new list by entering a new item.
    inputbox = browser.find_element_by_id('id_new_item')
    inputbox.send_keys('Buy milk')
    inputbox.send_keys(Keys.ENTER)
    wait_for_row_in_list_table(browser, '1: Buy milk')

    # Francis gets his own URL
    francis_list_url = browser.current_url
    assert re.search(r'/lists/.+', francis_list_url)
    assert francis_list_url != edith_list_url

    # Again there is no trace of Edith's list
    page_text = browser.find_element_by_tag_name('body').text
    assert 'Buy peacock feathers' not in page_text
    assert 'Buy milk' in page_text

    # Satisfied, they both go back to sleep.
    browser.quit()


class TestLayout(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = 'http://' + staging_server

    def test_layout_and_styling(self):
        # Edith goes to the home page.
        self.browser.get(self.live_server_url)
        self.browser.set_window_size(1024, 768)

        # She notices the input box is nicely centered.
        inputbox = self.browser.find_element_by_id('id_new_item')
        assert inputbox.location['x'] + inputbox.size['width'] / 2 == pytest.approx(512, abs=10)

        # She starts a new list and sees the input is nicely centered there, too.
        inputbox.send_keys('new item')
        inputbox.send_keys(Keys.ENTER)
        wait_for_row_in_list_table(self.browser, '1: new item')
        inputbox = self.browser.find_element_by_id('id_new_item')
        assert inputbox.location['x'] + inputbox.size['width'] / 2 == pytest.approx(512, abs=10)

        # So she goes back to sleep.
        self.browser.quit()


