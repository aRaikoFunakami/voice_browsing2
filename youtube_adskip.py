# 必要なモジュールをインポート
import threading
import time
import logging
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException 
from selenium.webdriver.support.ui import WebDriverWait

class YouTube_Adskip(threading.Thread):
	def __init__(self, driver: webdriver):
		super().__init__()
		self.daemon = True
		self.driver = driver
		self.thread_id = uuid.uuid4() 
		self.cancel = False

	def _adskip(self):
		try:
			logging.debug(f"waiting Adskip")
			skip_button = WebDriverWait(self.driver, 60).until(
				EC.presence_of_element_located((By.CSS_SELECTOR, ".ytp-ad-skip-button.ytp-button"))
			)
			logging.debug(f"Adskip!!!")
			skip_button.click()
		except TimeoutException as e:
			logging.error("Timeout: Skip button was not found within the time limit: {e}")
		except Exception as e:
			logging.error("click error: {e}")

	def run(self):
		while True:
			if self.cancel == True:
				logging.debug(f"Stopping thread {self.thread_id}.")
				break
			logging.debug(
				f"Thread {self.thread_id} received cancel_message: {self.cancel}"
			)
			self._adskip()
			time.sleep(3)

	def cancel(self):
		self.cancel = True

	def __del__(self):
		logging.debug(f"Destructor called for thread {self.thread_id}, cleaning up...")


def main():
	logging.basicConfig(
		format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
		level=logging.INFO,
	)
	options = webdriver.ChromeOptions()
	driver = webdriver.Chrome(options=options)
	driver.get("https://www.youtube.com")
	time.sleep(2)

	adskip_thread = YouTube_Adskip(driver=driver)
	adskip_thread.start()

	# finish
	adskip_thread.join()
	time.sleep(2)

if __name__ == "__main__":
	main()

