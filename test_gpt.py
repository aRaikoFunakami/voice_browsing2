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
    return "{input}"


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

        # if search_field.is_enabled() and search_field.is_displayed():
        if True:
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


while True:
    user_input = input("Enter the text to search (or 'exit' to quit): ")
    if user_input.lower() == "exit":
        break

    llm = ChatOpenAI(
        temperature=0,
        model=model_name,
    )
    agent_chain = OpenAIFunctionsAgent(tools=tools, llm=llm, verbose=True)
    response = agent_chain.run(input=user_input)
    print(f"response: {response}")

    # search_by_input_field(user_input, driver.page_source)


driver.quit()