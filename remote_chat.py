import json
import os, logging
from typing import Any, Type
from pydantic import BaseModel, Field
import threading
import queue

#
# LangChain related test codes
#
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# init openai
import config
#from remote_chrome import RemoteTest
from remote_chrome_androidtablet import RemoteTest

model_name = "gpt-3.5-turbo-0613"
test = None

# play next video
class PlayNextVideoInput(BaseModel):
    nextvideo: str = Field(descption="Play the next video while playing a video.")

class PlayNextVideo(BaseTool):
    name = "play_next_video"
    description = "Use this function to play the next video while playing a video."
    args_schema: Type[BaseModel] = PlayNextVideoInput

    def _run(self, nextvideo: str):
        logging.info(f"nextvideo = {nextvideo}")
        response = test.play_next_video()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# play previous video
class PlayPreviousVideoInput(BaseModel):
    previousvideo: str = Field(descption="Play the previous video while playing a video.")

class PlayPreviousVideo(BaseTool):
    name = "play_previous_video"
    description = "Use this function to play the previous video while playing a video."
    args_schema: Type[BaseModel] = PlayPreviousVideoInput

    def _run(self, previousvideo: str):
        logging.info(f"previousvideo = {previousvideo}")
        response = test.play_previous_video()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# Fullscreen
class FullscreenInput(BaseModel):
    fullscreen: bool = Field(descption="Toggle fullscreen and normal screen while playing a video.")

class Fullscreen(BaseTool):
    name = "fullscreen"
    description = "Use this function to toggle fullscreen and normal screen  while playing a video"
    args_schema: Type[BaseModel] = FullscreenInput

    def _run(self, fullscreen: bool):
        logging.info(f"fullscreen = {fullscreen}")
        response = test.fullscreen()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# FastPlayback
class FastForwardPlaybackInput(BaseModel):
    fastforward: str = Field(descption="Reduce the video playback speed while playing a video.")

class FastForwardPlayback(BaseTool):
    name = "fast_forward_playback"
    description = "Use this function to reduce the video playback speed while playing a video."
    args_schema: Type[BaseModel] = FastForwardPlaybackInput

    def _run(self, fastforward: str):
        logging.info(f"mute = {fastforward}")
        response = test.fast_forward_playback()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# SlowPlayback
class SlowForwardPlaybackInput(BaseModel):
    slowforward: str = Field(descption="Reduce the video playback speed while playing a video.")

class SlowForwardPlayback(BaseTool):
    name = "slow_forward_playback"
    description = "Use this function to reduce the video playback speed while playing a video."
    args_schema: Type[BaseModel] = SlowForwardPlaybackInput

    def _run(self, slowforward: str):
        logging.info(f"slowforward = {slowforward}")
        response = test.slow_forward_playback()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# Mute
class MuteInput(BaseModel):
    mute: bool = Field(descption="Toggle mute and unmute while playing a video.")

class Mute(BaseTool):
    name = "mute"
    description = "Use this function to toggle mute and unmute while playing a video."
    args_schema: Type[BaseModel] = MuteInput

    def _run(self, mute: bool):
        logging.info(f"mute = {mute}")
        response = test.mute()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# Play or Suspend
class PlaySuspendInput(BaseModel):
    playback_or_suspend: str = Field(descption="Toggle pause and playback while playing a video")

class PlaySuspend(BaseTool):
    name = "play_suspend"
    description = "Use this function to toggle pause and playback while playing a video"
    args_schema: Type[BaseModel] = PlaySuspendInput

    def _run(self, playback_or_suspend: str):
        logging.info(f"play_or_suepend = {playback_or_suspend}")
        response = test.play_suspend()
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# 動画を番号で選択する
class SelectLinkByNumberInput(BaseModel):
    num: int = Field(descption="Select the link you want to select by number")


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


class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration:
            raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)


class ChainStreamHandler(StreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)


class SimpleConversationRemoteChat:
    tools = [
        PlayNextVideo(),
        PlayPreviousVideo(),
        Fullscreen(),
        FastForwardPlayback(),
        SlowForwardPlayback(),
        Mute(),
        PlaySuspend(),
        SearchByQuery(),
        SelectLinkByNumber(),
    ]
    prompt_init = """
	You are helping humans by manipulating the browser with chatgpt functions in natural language.
    Follow the instructions in markdown format below

	# Restrictions
	- Preference for Japanese language sites
	- If the website to search for videos is not already specified, youtube is assumed to be specified.
	- Use the function to select links by number if only numbers are entered.
	- If you don't know, say you don't know.
	- Do not lie.
	- Minimal talk, no superfluous words.
    - Use function call in the following cases
    -- Searching for videos
    -- Pause a video
    -- Play or resume video

	# Combination of web sites and URLs to search
	{
		"Amazon Prime Japan" : "https://www.amazon.co.jp/gp/browse.html?node=2351649051&ref_=nav_em__aiv_vid_0_2_2_2",.
		"dアニメ" : "https://animestore.docomo.ne.jp/animestore/CF/search_index",
		"Hulu" : "https://www.hulu.jp/",
		"YouTube" : "https://www.youtube.com/",
		"Yahoo" : "https://www.yahoo.co.jp/",
	}
	"""

    def __init__(self, history):
        config.load()
        global test
        test = RemoteTest()
        self.agent_kwargs = {
            "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
        }
        self.memory = ConversationBufferMemory(
            memory_key="memory", return_messages=True
        )
        prompts = [
            self.prompt_init,
        ]
        for prompt in prompts:
            self.memory.save_context({"input": prompt}, {"ouput": "I understood!"})

    def generator(self, user_message):
        g = ThreadedGenerator()
        threading.Thread(target=self.llm_thread, args=(g, user_message)).start()
        return g

    def llm_thread(self, g, user_message):
        try:
            logging.info(f"memory: {self.memory}")

            llm = ChatOpenAI(
                temperature=0,
                model=model_name,
            )

            agent_chain = initialize_agent(
                tools=self.tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                agent_kwargs=self.agent_kwargs,
                memory=self.memory,
            )
            return agent_chain.run(input=user_message)
        finally:
            g.close()

    def llm_run(self, user_message):
        """sync call llm_thread directly instead of chat.generator(user_input)"""
        g = ThreadedGenerator()
        self.llm_thread(g, user_message)


if __name__ == "__main__":
    chat = SimpleConversationRemoteChat("")
    while True:
        user_input = input("Enter the text to search (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break
        chat.llm_run(user_input)
