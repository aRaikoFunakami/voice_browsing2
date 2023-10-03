import json
import os, logging
from typing import Any
from typing import Type
from pydantic import BaseModel, Field

#
# LangChain related test codes
#
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool


model_name = "gpt-3.5-turbo-0613"
#
# Ugh!
#
memory = None


# init openai
import config

config.load()


# 動画を番号で選択する
class SelectVideoByNumberInput(BaseModel):
	num: int = Field(descption="Select the video you want to play by number")
	#url: str = Field(descption="url of the web page")


class SelectVideoByNumber(BaseTool):
	name = "select_video_by_number"
	description = "Use this function to select the video you want to play by number"
	args_schema: Type[BaseModel] = SelectVideoByNumberInput

	def _run(self, num: int):
		logging.info(f"select_video_by_number")
		print(f"_run(): input = {num},")
		return select_video_by_number(num=num)

	def _arun(self, ticker: str):
		raise NotImplementedError("not support async")


# キーワードでWebサイトから動画を検索する
class SearchByInputFieldInput(BaseModel):
	input: str = Field(
		descption="String to be searched in the text field of the web page"
	)
	url: str = Field(descption="url of the web page")


class SearchByInputField(BaseTool):
	name = "search_by_input_field"
	description = "You use this function when you want to search in the text field of a Web page. "
	args_schema: Type[BaseModel] = SearchByInputFieldInput

	def _run(self, input: str, url: str):
		logging.info(f"search_by_input_field")
		print(f"_run(): input = {input}, url = {url}")
		return search_by_input_field(input, url)

	def _arun(self, ticker: str):
		raise NotImplementedError("not support async")


tools = [
	SearchByInputField(),
	SelectVideoByNumber(),
]


def OpenAIFunctionsAgent(tools=None, llm=None, verbose=False):
	agent_kwargs = {
		"extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
	}
	#
	# Ugh!
	#
	global memory
	if memory is None:
		memory = ConversationBufferMemory(memory_key="memory", return_messages=True)

		prompt_init = """
		You are helping humans by manipulating the browser with chatgpt functions in natural language.

		# Restrictions
		- Preference for Japanese language sites
		- If the website to search for videos is not already specified, youtube is assumed to be specified.
		- No automatic video selection unless explicitly specified

		# Combination of web sites and URLs to search
		{
			"Amazon Prime Japan" : "https://www.amazon.co.jp/gp/browse.html?node=2351649051&ref_=nav_em__aiv_vid_0_2_2_2",.
			"dアニメ" : "https://animestore.docomo.ne.jp/animestore/CF/search_index",
			"Hulu" : "https://www.hulu.jp/",
			"YouTube" : "https://www.youtube.com/",
			"Yahoo" : "https://www.yahoo.co.jp/",
		}
		"""

		prompts = [
			prompt_init,
		]
		for prompt in prompts:
			memory.save_context({"input": prompt}, {"ouput": "I understood!"})

	return initialize_agent(
		tools=tools,
		llm=llm,
		agent=AgentType.OPENAI_FUNCTIONS,
		verbose=verbose,
		agent_kwargs=agent_kwargs,
		memory=memory,
	)


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import quote
import time


driver = webdriver.Chrome()

"""
動画選択補助用の番号をつける処理
"""
def add_numbers_to_videos_for_youtube():
	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, f"video-title")))
	video_elements = driver.find_elements(By.ID, 'video-title')

	for i, video in enumerate(video_elements):
		x, y = video.location['x'], video.location['y']
		# JavaScriptで半透明な丸と番号を作成
		script = f"""
		var circle = document.createElement('div');
		circle.className = "video-number-circle"; 
		var text = document.createElement('span');
		circle.style.zIndex = "9999";
		circle.style.fontSize = "36px"; 
		circle.style.width = '60px';
		circle.style.height = '60px';
		circle.style.lineHeight = "48px";
		circle.style.background = 'rgba(0, 128, 0, 0.5)';
		circle.style.position = 'absolute';
		circle.style.top = '{y}px';
		circle.style.left = '{x-60}px';
		circle.style.borderRadius = '50%';
		circle.style.display = 'flex';
		circle.style.justifyContent = 'center';
		circle.style.alignItems = 'center';
		text.innerHTML = '{i}';
		text.style.color = 'white';
		circle.appendChild(text);
		document.body.appendChild(circle);
		"""
		driver.execute_script(script, video)


def add_numbers_to_videos(driver):
	url = driver.current_url
	if "google.com" in url:
		return 
	if "youtube.com" in url:
		return add_numbers_to_videos_for_youtube()
	if "hulu.jp" in url:
		return 
	if "animestore.docomo.ne.jp" in url:
		return 
	if "amazon.co.jp" in url:
		return 
	if "yahoo.co.jp" in url:
		return 



# 画面遷移前に番号を消すスクリプトを注入
def setup_remove_numbers_on_navigation(driver):
	script = '''
	window.addEventListener('beforeunload', function() {
		var circles = document.querySelectorAll('.video-number-circle');
		circles.forEach(function(circle) {
			circle.parentNode.removeChild(circle);
		});
	});
	'''
	driver.execute_script(script)

def remove_numbers_from_videos(driver):
	script = '''
	var circles = document.querySelectorAll('.video-number-circle');
	circles.forEach(function(circle) {
		circle.parentNode.removeChild(circle);
	});
	'''
	driver.execute_script(script)


def find_first_field_with_id_or_name(fields):
	"""指定された fields から最初に見つかる field の id または name と field name を返す。"""
	for field in fields:
		print(field.get("id"), field.get("name"), field.name)  # デバッグ用

		# id も name も None なら次のループへ
		if field.get("id") is None and field.get("name") is None:
			continue

		return field.get("id") or field.get("name"), field.name
	return None, None


def find_search_input_field(url):
	global driver
	driver.get(f"{url}")

	try:
		# inputまたはtextarea要素が読み込まれるまで最大10秒待つ
		wait = WebDriverWait(driver, 10)
		element = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR, "input, textarea"))
		)
	except TimeoutException:
		print("Timed out waiting for input or textarea elements to load.")
		return None, None

	html = driver.page_source
	soup = BeautifulSoup(html, "html.parser")
	# 'input' と 'textarea' タグを一度に検索
	input_fields = soup.find_all(["input", "textarea"])
	return find_first_field_with_id_or_name(input_fields)


def search_by_query(url, input):
	global driver
	driver.get(f"{url}{quote(input)}")
 
	return add_numbers_to_videos(driver)



def search_by_input_field(input, url):
	# スペシャルケースを追加
	if "google.com" in url:
		return search_by_query("https://www.google.com/search?tbm=vid&q=", input)
	if "youtube.com" in url:
		return search_by_query("https://www.youtube.com/results?search_query=", input)
	if "hulu.jp" in url:
		return search_by_query("https://www.hulu.jp/search?q=", input)
	if "animestore.docomo.ne.jp" in url:
		return search_by_query(
			"https://animestore.docomo.ne.jp/animestore/sch_pc?searchKey=", input
		)
	if "amazon.co.jp" in url:
		return search_by_query("https://www.amazon.co.jp/s?i=instant-video&k=", input)
	if "yahoo.co.jp" in url:
		return search_by_query(
			"https://search.yahoo.co.jp/search?p=", input
		)  # 動画検索だと読み込みが終了しないので動画検索はしていない (普通にアクセスしてもそういう挙動をする)

	# 画面操作が必要な場合
	global driver
	search_field_id_or_name, field_type = find_search_input_field(url)
	print(
		f"search_field_id_or_name, field_type: {search_field_id_or_name}, {field_type}"
	)

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
				search_field.send_keys(input)
				search_field.send_keys(Keys.RETURN)
				time.sleep(2)
				# [TODO] 何を返すのか真島に考える
				return driver.title
			except Exception as e:
				print(f"An error occurred: {e}")
		else:
			print("The search field is not editable.")
	else:
		print("No suitable search field found.")
	return ""


def select_video_by_number(num):
	global driver
	
	try:
		# 動画のリンクを取得（例として最初の動画）
		WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, f"video-title"))
		)
		videos = driver.find_elements(By.ID, 'video-title')

		#画面表示されていないと落ちるので click() を直接呼び出さない
		#videos[num].click()
		#
		# 表示しているリンク番号を削除
		remove_numbers_from_videos(driver)
		# 選択したビデオをクリック
		driver.execute_script("arguments[0].scrollIntoView();", videos[num])
		driver.execute_script("arguments[0].click();", videos[num])
		# クリック先でリンク番号を追加
		# 非同期処理のため WebDriverWait では正常に動作しない
		time.sleep(2)
		add_numbers_to_videos(driver)
	except Exception as e:
		print(f"An error occurred: {e}")

while True:
	user_input = input("Enter the text to search (or 'exit' to quit): ")
	if user_input.lower() == "exit":
		break
#"""
	llm = ChatOpenAI(
		temperature=0,
		model=model_name,
	)
	agent_chain = OpenAIFunctionsAgent(tools=tools, llm=llm, verbose=True)
	response = agent_chain.run(input=user_input)
	print(f"response: {response}")
#"""

'''
	driver.get(
		f"https://www.youtube.com/results?search_query=%E6%8E%A8%E3%81%97%E3%81%AE%E5%AD%90"
	)
	select_link(1)
'''



driver.quit()
