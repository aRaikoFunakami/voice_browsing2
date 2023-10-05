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
class SelectLinkByNumberInput(BaseModel):
	num: int = Field(descption="Select the link you want to select by number")
	# url: str = Field(descption="url of the web page")


class SelectLinkByNumber(BaseTool):
	name = "select_link_by_number"
	description = "Use this function to select the link you want to select by number"
	args_schema: Type[BaseModel] = SelectLinkByNumberInput

	def _run(self, num: int):
		logging.info(f"num = {num}")
		response = select_link_by_number(num=num)
		logging.info(f"response: {response}")
		return response

	def _arun(self, ticker: str):
		raise NotImplementedError("not support async")


# キーワードでWebサイトから動画を検索する
class SearchByQueryInput(BaseModel):
	url: str = Field(descption="url of the web page")
	input: str = Field(
		descption="String to be searched in the text field of the web page"
	)



class SearchByQuery(BaseTool):
	name = "search_by_query"
	description = "You use this function when you want to search in the text field of a Web page. "
	args_schema: Type[BaseModel] = SearchByQueryInput

	def _run(self, url: str, input: str):
		logging.info(f" url = {url}, input = {input}")
		response = search_by_query(url=url, input=input)
		logging.info(f"response: {response}")
		return response

	def _arun(self, ticker: str):
		raise NotImplementedError("not support async")


tools = [
	SearchByQuery(),
	SelectLinkByNumber(),
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
		- Use the function to select links by number if only numbers are entered.
  		- If you don't know, say you don't know.
		- Do not lie.
		- Minimal talk, no superfluous words.

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


import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import quote
import time


logging.basicConfig(format='%(filename)s: %(levelname)s: %(funcName)s: %(message)s', level=logging.INFO)
driver = webdriver.Chrome()

"""
Remove numbers for video selection aids
"""
def remove_numbers_from_videos(driver):
	script = """
	var circles = document.querySelectorAll('.video-number-circle');
	circles.forEach(function(circle) {
		circle.parentNode.removeChild(circle);
	});
	"""
	driver.execute_script(script)


"""
Numbering process for video selection aids
"""
# JavaScriptで半透明な丸と番号を作成
script_add_numbers_template = """
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
circle.style.left = '{x}px';
circle.style.borderRadius = '50%';
circle.style.display = 'flex';
circle.style.justifyContent = 'center';
circle.style.alignItems = 'center';
text.innerHTML = '{i}';
text.style.color = 'white';
circle.appendChild(text);
document.body.appendChild(circle);
"""


def add_numbers_to_videos_for_youtube(driver):
	try:
		WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, f"video-title"))
		)
		video_elements = driver.find_elements(By.ID, "video-title")

		for i, video in enumerate(video_elements):
			x, y = video.location["x"], video.location["y"]
			script = script_add_numbers_template.format(x=x - 60, y=y, i=i)
			driver.execute_script(script, video)
	except TimeoutException:
		logging.error("Timed out waiting for input or textarea elements to load.")
		return "videos are not found"

	return "The search was successful. Please ask Human to select links."


def add_numbers_to_videos_common(driver, locator, condition_func, script_template):
	try:
		WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator))
		elements = driver.find_elements(*locator)

		# Search for an element by matching a href. However, if there are multiple elements with the same href, the first element is selected.
		matching_elements = {}
		for element in elements:
			href = element.get_attribute("href")
			if condition_func(href):
				if href not in matching_elements:
					matching_elements[href] = element

		video_elements = list(matching_elements.values())

		for i, video in enumerate(video_elements):
			x, y = video.location["x"], video.location["y"]
			script = script_template.format(x=x - 60, y=y, i=i)
			driver.execute_script(script, video)
	except TimeoutException:
		logging.error("Timed out waiting for input or textarea elements to load.")
		return "videos are not found"

	return "The search was successful. Please ask Human to select links."


def add_numbers_to_videos(driver):
	url = driver.current_url
	logging.info(f"url: {url}")

	if "youtube.com" in url:
		return add_numbers_to_videos_for_youtube(driver)
	elif "animestore.docomo.ne.jp" in url:
		return add_numbers_to_videos_common(
			driver,
			(By.XPATH, "//a[descendant::img]"),
			lambda href: href is not None,
			script_add_numbers_template,
		)
	elif "amazon.co.jp" in url:
		return add_numbers_to_videos_common(
			driver,
			(By.XPATH, "//a[descendant::img]"),
			lambda href: href is not None and "instant-video" in href,
			script_add_numbers_template,
		)
	else:
		return


def search_by_query(url, input):
	logging.info(f" url = {url}, input = {input}")
	search_queries = {
		"google.com": "https://www.google.com/search?tbm=vid&q=",
		"youtube.com": "https://www.youtube.com/results?search_query=",
		"hulu.jp": "https://www.hulu.jp/search?q=",
		"animestore.docomo.ne.jp": "https://animestore.docomo.ne.jp/animestore/sch_pc?searchKey=",
		"amazon.co.jp": "https://www.amazon.co.jp/s?i=instant-video&k=",
		"yahoo.co.jp": "https://search.yahoo.co.jp/search?p=",
	}
	global driver
	for domain, query_url in search_queries.items():
		if domain in url:
			driver.get(f"{query_url}{quote(input)}")
			time.sleep(1)
			return add_numbers_to_videos(driver)
	return "This is the nsupported Web site."


"""
Select the link (video) of the selected number
"""
def click_link(link):
	logging.info(f"link = {link}")
	# 画面表示されていないと落ちるので click() を直接呼び出さない
	# videos[num].click()
	#
	# 表示しているリンク番号を削除
	remove_numbers_from_videos(driver)
	# 選択したビデオをクリック
	driver.execute_script("arguments[0].scrollIntoView();", link)
	driver.execute_script("arguments[0].click();", link)

def select_video_youtube(num):
	logging.info(f"num = {num}")
	global driver

	try:
		# 動画のリンクを取得（例として最初の動画）
		WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, f"video-title"))
		)
		videos = driver.find_elements(By.ID, "video-title")
		click_link(videos[num])
		# クリック先でリンク番号を追加
		# 非同期処理のため WebDriverWait では正常に動作しない
		time.sleep(2)
		add_numbers_to_videos(driver)
	except Exception as e:
		logging.error(f"An error occurred: {e}")
		return f"Playback of the selected video has not started."

	return f"Playback of the selected video has started."


def select_video_common(num, locator, condition_func):
	global driver

	try:
		WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator))
		elements = driver.find_elements(*locator)

		matching_elements = {}
		for element in elements:
			href = element.get_attribute("href")
			if condition_func(href):
				if href not in matching_elements:
					matching_elements[href] = element

		videos = list(matching_elements.values())
		click_link(videos[num])
		time.sleep(1)
		add_numbers_to_videos(driver)
	except Exception as e:
		logging.error(f"An error occurred: {e}")
		return f"Error"

	return f"The search was successful. Please ask Human to select links."


def select_link_by_number(num):
	global driver
	url = driver.current_url
	logging.info(f"num = {num}, nul = {url}")

	if "youtube.com" in url:
		return select_video_youtube(num)
	elif "animestore.docomo.ne.jp" in url:
		return select_video_common(
			num,
			(By.XPATH, "//a[descendant::img]"),
			lambda href: href is not None,
		)
	elif "amazon.co.jp" in url:
		return select_video_common(
			num,
			(By.XPATH, "//a[descendant::img]"),
			lambda href: href is not None and "instant-video" in href,
		)
	else:
		return


"""
テスト
"""
while True:
	user_input = input("Enter the text to search (or 'exit' to quit): ")
	if user_input.lower() == "exit":
		break
	# """
	llm = ChatOpenAI(
		temperature=0,
		model=model_name,
	)
	agent_chain = OpenAIFunctionsAgent(tools=tools, llm=llm, verbose=True)
	response = agent_chain.run(input=user_input)
	print(f"response: {response}")
# """

"""
	driver.get(
		f"https://www.youtube.com/results?search_query=%E6%8E%A8%E3%81%97%E3%81%AE%E5%AD%90"
	)
	select_link(1)
"""


driver.quit()
