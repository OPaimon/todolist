from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import unittest
class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list_and_retrieve_it_later(self):
        # User visits the home page
        self.browser.get('http://localhost:8000')

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

        table = self.browser.find_element(By.ID, 'id_list_table')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        self.assertTrue(
            any(row.text == '1: Buy flowers' for row in rows),
            "New to-do item did not appear in the table"
        )

        self.fail("Finish the test! Add more items and check the list.")

if __name__ == '__main__':
    unittest.main()  # Suppress warnings from Selenium


