from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from django.test import LiveServerTestCase

class NewVisitorTest(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()

    def tearDown(self):
        self.browser.quit()

    def check_for_row_in_list_table(self, row_text):
        table = self.browser.find_element(By.ID, 'id_list_table')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        self.assertIn(row_text, [row.text for row in rows], f"Row '{row_text}' not found in table")

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
        self.browser.implicitly_wait(3)

        # Use helper to check for first item
        self.check_for_row_in_list_table('1: Buy flowers')

        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        inputbox.send_keys('Give a gift to Lisi')
        inputbox.send_keys(Keys.ENTER)
        self.browser.implicitly_wait(3)

        # Use helper to check for both items
        self.check_for_row_in_list_table('1: Buy flowers')
        self.check_for_row_in_list_table('2: Give a gift to Lisi')

        self.fail("Finish the test!")

