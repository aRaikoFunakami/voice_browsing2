from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
import time

class RemoteTest:
	capabilities = dict(
		platformName='Android',
		automationName='UiAutomator2',
		deviceName='ADT-3',
		appPackage='com.access_company.nfbe.oibtv.content_shell_apk',
		appActivity='.ContentShellActivity',
		language='en',
		locale='US',
		noReset=True,
	)
	appium_server_url = 'http://localhost:4723'

	def __init__(self):
		capabilities_options = UiAutomator2Options().load_capabilities(self.capabilities)
		self.driver = webdriver.Remote(command_executor=self.appium_server_url, options=capabilities_options)

	def __del__(self):
		if self.driver:
			self.driver.quit()

	def start(self):
		self.driver.get("https://www.google.com")
		time.sleep(10)

if __name__ == '__main__':
	test = RemoteTest()
	test.start()