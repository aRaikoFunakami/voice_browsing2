import json
import logging
from typing import Any, Type
from pydantic import BaseModel, Field
import threading
import queue
import langid
from flask import Flask, render_template, request, jsonify

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

# from remote_chrome import RemoteTest
from remote_chrome import RemoteChrome
from remote_intent import intent_googlenavigation, intent_application, intent_chrome, intent_googlemap

LAUNCHER_HTML = config.keys["launcher"]
model_name = config.keys["model_name"]
test = None
lang_id = "ja"


# Weather
from openai_function_weather import get_weather_info
class WeatherInfoInput(BaseModel):
    latitude: float = Field(descption="latitude")
    longitude: float = Field(descption="longitude")


class WeatherInfo(BaseTool):
    name = "get_weather_info"
    description = "This is useful when you want to know the weather forecast. Enter longitude in the latitude field and latitude in the longitude field."
    args_schema: Type[BaseModel] = WeatherInfoInput

    def _run(self, latitude: float, longitude: float):
        logging.info(f"get_weather_info(latitude, longitude)")
        return get_weather_info(latitude, longitude)

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# Launch Application or Change Application
class LaunchAppInput(BaseModel):
    application: str = Field(descption="Specify the application.")


class LaunchApp(BaseTool):
    name = "intent_application"
    description = (
        """
        The argument application is a string specified by the adb command "adb shell am start -n".
        Example)
        - Chrome: "com.android.chrome/com.google.android.apps.chrome.Main"
        - 動画再生: "com.android.chrome/com.google.android.apps.chrome.Main"
        - YouTube: "com.android.chrome/com.google.android.apps.chrome.Main"
        - Hulu: "com.android.chrome/com.google.android.apps.chrome.Main"
        - dアニメ: "com.android.chrome/com.google.android.apps.chrome.Main"
        - TVer: "com.android.chrome/com.google.android.apps.chrome.Main"
        - Google Maps: "com.google.android.apps.maps/com.google.android.maps.MapsActivity"
        - ナビ: "com.google.android.apps.maps/com.google.android.maps.MapsActivity"
        """
    )
    args_schema: Type[BaseModel] = LaunchAppInput
    return_direct = False  # if True, Tool returns output directly

    def _run(self, application:str):
        logging.info(f"application = {application}")
        response = intent_application(application=application)
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")

# Googla Map Navigationを起動する
class LaunchNavigationInput(BaseModel):
    latitude: float = Field(descption="Specify the Latitude of the destination.")
    longitude: float = Field(description="Specify the longitude of the destination")


class LaunchNavigation(BaseTool):
    name = "intent_googlenavigation"
    description = (
        "Use this function to provides route guidance to a specified location."
    )
    args_schema: Type[BaseModel] = LaunchNavigationInput
    return_direct = False  # if True, Tool returns output directly

    def _run(self, latitude: float, longitude: float):
        logging.info(f"lat, lon = {latitude}, {longitude}")
        response = intent_googlenavigation(latitude=latitude, longitude=longitude)
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")


# playlistを再生する
class PlayVideoInPlaylistInput(BaseModel):
    num: int = Field(
        descption="Select the video to be played from the playlist by number."
    )


class PlayVideoInPlaylist(BaseTool):
    name = "play_video_in_playlist"
    description = "Use this function to play a video in the play list.The search results are saved as a playlist. Media playback is performed according to that playlist. The first media designation specifies 0; for the second, 1."
    args_schema: Type[BaseModel] = PlayVideoInPlaylistInput
    return_direct = False  # if True, Tool returns output directly

    def _run(self, num: int):
        logging.info(f"num = {num}")
        response = test.play_video_in_playlist(num=num, lang_id=lang_id)
        logging.info(f"response: {response}")
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("not support async")


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
    previousvideo: str = Field(
        descption="Play the previous video while playing a video."
    )


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
    fullscreen: bool = Field(
        descption="Toggle fullscreen and normal screen while playing a video."
    )


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
    fastforward: str = Field(
        descption="Reduce the video playback speed while playing a video."
    )


class FastForwardPlayback(BaseTool):
    name = "fast_forward_playback"
    description = (
        "Use this function to reduce the video playback speed while playing a video."
    )
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
    slowforward: str = Field(
        descption="Reduce the video playback speed while playing a video."
    )


class SlowForwardPlayback(BaseTool):
    name = "slow_forward_playback"
    description = (
        "Use this function to reduce the video playback speed while playing a video."
    )
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
    playback_or_suspend: str = Field(
        descption="Toggle pause and playback while playing a video"
    )


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
    return_direct = True  # Tool returns output directly

    def _run(self, num: int):
        logging.info(f"num = {num}")
        response = test.select_link_by_number(num=num, lang_id=lang_id)
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
    return_direct = True  # Tool returns output directly

    def _run(self, url: str, input: str):
        logging.info(f" url = {url}, input = {input}")
        intent_chrome()
        response = test.search_by_query(url=url, input=input, lang_id=lang_id)
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
        WeatherInfo(),
        LaunchApp(),
        LaunchNavigation(),
        PlayVideoInPlaylist(),
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
	## Language
	- Respond in the same language as the input text
	- Prefer to use websites in the same language as the language of the input
	## Response
 	- You are chatting with a user via the ChatGPT voice app. For this reason, in most cases your response should be one or two sentences. However, unless the user's request requires inference or longer output. Do not use characters that cannot be pronounced.
	- To search for videos in a situation where you are not navigating to the video search page, search for videos on youtube. youtube's URL is "https://www.youtube.com".
	- In order to keep the answers brief, detailed explanations will not be given until asked. For example, "What are the sights in Sakuragicho?" I will answer the name of the sightseeing spot, but not the details until I am asked.
	- Use the function to select links by number if only numbers are entered.
	- If you don't know, say you don't know.
	- Do not lie.
	- Minimal talk, no superfluous words.
    - When responding to the weather, mention sensory information such as whether it is hot or chilly like a weather announcer, and respond in short sentences with the date, time, and miscellaneous information about the weather or location.
	## Function Call
	- Use function call in the following cases
	-- Searching for videos
	-- Pause a video
	-- Play or resume video

	# Combination of web sites and URLs to search
	- Use the following site/URL combination to search for videos
	{
		"Amazon Prime Japan" : "https://www.amazon.co.jp/gp/browse.html?node=2351649051&ref_=nav_em__aiv_vid_0_2_2_2",.
		"dアニメ" : "https://animestore.docomo.ne.jp/animestore/CF/search_index",
		"Hulu" : "https://www.hulu.jp/",
		"Yahoo" : "https://www.yahoo.co.jp/",
		"YouTube" : "https://www.youtube.com/",
	}
    Respond in the same language as the input text
	"""

    def __init__(self, history):
        config.load()
        global test
        test = RemoteChrome()
        test.set_start_url(LAUNCHER_HTML)
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
            global lang_id
            lang_id = langid.classify(user_message)[0]
            logging.debug(f"memory: {self.memory}")
            logging.info(f"lang_id: {lang_id}")

            llm = ChatOpenAI(
                temperature=0,
                model=model_name,
                # request_timeout=15,
            )

            agent_chain = initialize_agent(
                tools=self.tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                agent_kwargs=self.agent_kwargs,
                memory=self.memory,
            )
            response = agent_chain.run(input=user_message)
            """
			try:
				json_response = json.loads(response)
				if json_response["type"] == "video_list":
					response = agent_chain.run(input="プレイリストの0番の動画を再生しなさい")
			except json.JSONDecodeError as e:
				logging.error(f"you can ignor this error: JSON decode error: {e}")
			"""
            return response
        finally:
            g.close()

    def llm_run(self, user_message):
        """sync call llm_thread directly instead of chat.generator(user_input)"""
        g = ThreadedGenerator()
        return self.llm_thread(g, user_message)


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
        level=logging.INFO,
    )

    app = Flask(__name__, static_folder="./templates", static_url_path="")

    @app.route("/")
    def index():
        return render_template("index.html")

    def run_server():
        app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)

    def chat():
        chat = SimpleConversationRemoteChat("")
        while True:
            user_input = input("Enter the text to search (or 'exit' to quit): ")
            if user_input.lower() == "exit":
                break
            chat.llm_run(user_input)

    # Start the web server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Run the chat in the main thread
    chat()
