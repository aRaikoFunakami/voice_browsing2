from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pyautogui

# Chromeのオプションを設定
chrome_options = Options()

# 既に起動しているChromeに接続
# chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
chrome_options.add_experimental_option("debuggerAddress", "192.168.1.90:9222")

# WebDriverのインスタンスを作成
driver = webdriver.Chrome(options=chrome_options)


# 新しいタブでURLを開く（既存のタブはそのまま）
driver.get('https://www.youtube.com')

# 何らかの操作（例：Googleでの検索）
#search_box = driver.find_element(By.CSS_SELECTOR, 'q')
#search_box.send_keys('Selenium')
#search_box.submit()

# 注意: driver.quit()を呼び出さないように（既存のブラウザセッションを閉じてしまうため）
