from selenium import webdriver
# from chromedriver_py import binary_path
# google-chrome-stable 
# options = webdriver.ChromeOptions()
# options.binary_location = '/usr/sbin/google-chrome-stable'
# Create a new instance of the Chrome driver

browser = webdriver.Chrome()
browser.get('http://localhost:8000')

assert 'Django' in browser.page_source