import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from webdriver_manager.chrome import ChromeDriverManager
import time

class NewVisitorTest(StaticLiveServerTestCase):
    def setUp(self):
        self.service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=self.service)
        real_server = os.environ.get('REAL_SERVER')
        if real_server:
            self.live_server_url = 'http://' + real_server

    def tearDown(self):
        self.browser.quit()

    def wait_for_row_in_list_table(self, row_text, timeout=10):
        start_time = time.time()
        while True:
            try:
                table = self.browser.find_element(By.ID, 'id_list_table')
                rows = table.find_elements(By.TAG_NAME, 'tr')
                self.assertIn(row_text, [row.text for row in rows], f"Row '{row_text}' not found in table")
                return
            except (AssertionError, Exception) as e:
                if time.time() - start_time > timeout:
                    raise e
                time.sleep(0.5)

    def test_can_start_a_list_and_retrieve_it_later(self):
        # User visits the home page
        self.browser.get(self.live_server_url)

        # Check if the title contains 'To-Do'
        self.assertIn('To-Do', self.browser.title), "Browser title was '%s'" % self.browser.title
        # Check if the header contains 'To-Do'
        header_text = self.browser.find_element(By.TAG_NAME, 'h1').text
        self.assertIn('To-Do', header_text)

        # User is prompted to enter a to-do item
        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        self.assertEqual(inputbox.get_attribute('placeholder'), 'Enter a to-do item')
        # User types 'Buy flowers' into the input box
        inputbox.send_keys('Buy flowers')

        # User presses Enter, and the page updates
        inputbox.send_keys(Keys.ENTER)

        # Use helper to check for first item
        self.wait_for_row_in_list_table('1: Buy flowers')

        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        inputbox.send_keys('Give a gift to Lisi')
        inputbox.send_keys(Keys.ENTER)

        # Use helper to check for both items
        self.wait_for_row_in_list_table('1: Buy flowers')
        self.wait_for_row_in_list_table('2: Give a gift to Lisi')

    def test_multiple_users_can_start_lists_at_different_urls(self):
        # User 1 starts a new list
        self.browser.get(self.live_server_url)
        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        inputbox.send_keys('Buy flowers')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('1: Buy flowers')

        # User 1 gets a unique URL for their list
        user1_list_url = self.browser.current_url
        self.assertRegex(user1_list_url, '/lists/.+')

        # A new user comes along and starts a new list
        self.browser.quit()
        self.browser = webdriver.Chrome()
        self.browser.get(self.live_server_url)

        # User 2 does not see User 1's list
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertNotIn('Buy flowers', page_text)
        self.assertNotIn('Give a gift to Lisi', page_text)

        # User 2 starts a new list
        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        inputbox.send_keys('Buy milk')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('1: Buy milk')

        # User 2 gets their own unique URL
        user2_list_url = self.browser.current_url
        self.assertRegex(user2_list_url, '/lists/.+')
        self.assertNotEqual(user1_list_url, user2_list_url)

        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertNotIn('Buy flowers', page_text)
        self.assertIn('Buy milk', page_text)

    def test_layout_and_styling(self):
        # User visits the home page
        self.browser.get(self.live_server_url)
        self.browser.set_window_size(1024, 768)

        # Check if the input box is centered
        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        self.assertAlmostEqual(inputbox.location['x'] + inputbox.size['width'] / 2, 512, delta=10)

        # User starts a new list and checks if the input box remains centered
        inputbox.send_keys('Buy flowers')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('1: Buy flowers')

        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        self.assertAlmostEqual(inputbox.location['x'] + inputbox.size['width'] / 2, 512, delta=10)

