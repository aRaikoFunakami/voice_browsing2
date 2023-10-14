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

from remote_chrome import RemoteTest
test = RemoteTest()

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
		response = test.select_link_by_number(num=num)
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
		response = test.search_by_query(url=url, input=input)
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

