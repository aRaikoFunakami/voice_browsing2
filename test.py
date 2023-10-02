from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from selenium.webdriver import ActionChains


"""
def find_search_input_field(html):
	soup = BeautifulSoup(html, 'html.parser')
	input_fields = soup.find_all(['textarea',])
	for field in input_fields:
		print(field.get('id'), field.get('name'), field.name)
		if field.get('id') is None and field.get('name') is None:
			break
		return field.get('id') or field.get('name'), field.name

	input_fields = soup.find_all(['input',])
	for field in input_fields:
		print(field.get('id'), field.get('name'), field.name)
		if field.get('id') is None and field.get('name') is None:
			break
		return field.get('id') or field.get('name'), field.name

	return None, None
"""


def find_first_field_with_id_or_name(fields):
    """指定された fields から最初に見つかる field の id または name と field name を返す。"""
    for field in fields:
        print(field.get("id"), field.get("name"), field.name)  # デバッグ用

        # id も name も None なら次のループへ
        if field.get("id") is None and field.get("name") is None:
            continue

        return field.get("id") or field.get("name"), field.name
    return None, None


def find_search_input_field(html):
    """指定された HTML から検索用の input フィールドまたは textarea の id または name を探す。"""
    soup = BeautifulSoup(html, "html.parser")

    # 'input' と 'textarea' タグを一度に検索
    input_fields = soup.find_all(["input", "textarea"])

    return find_first_field_with_id_or_name(input_fields)


driver = webdriver.Chrome()

driver.get("https://animestore.docomo.ne.jp/animestore/CF/search_index")
time.sleep(2)


def search_by_input_field(input, html_source):
    search_field_id_or_name, field_type = find_search_input_field(html_source)
    print(search_field_id_or_name, field_type)
    if search_field_id_or_name:
        search_field = (
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"#{search_field_id_or_name}")
                )
            )
            if driver.find_elements(By.CSS_SELECTOR, f"#{search_field_id_or_name}")
            else WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, search_field_id_or_name))
            )
        )

        if search_field.is_enabled() and search_field.is_displayed():
            try:
                search_field.clear()  # yahoo.co.jp では clear が効かない
                search_field.send_keys(user_input)
                search_field.send_keys(Keys.RETURN)
                time.sleep(2)
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("The search field is not editable.")
    else:
        print("No suitable search field found.")


while True:
    user_input = input("Enter the text to search (or 'exit' to quit): ")

    if user_input.lower() == "exit":
        break
    search_by_input_field(user_input, driver.page_source)


driver.quit()
