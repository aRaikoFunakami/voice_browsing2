import os
import logging
import time
import json
from typing import Any
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import quote
from youtube_autoplay import YouTube_AutoPlay
from youtube_adskip import YouTube_Adskip

#android_tablet = False
android_tablet = True
youtube_playlist = True

class RemoteChrome:
    def __init__(self):
        global android_tablet
        self.lang_id = "ja"
        self.playlist = []
        self.playlist_mode = False
        self.youtube_autoplay_thread  = None
        options = webdriver.ChromeOptions()
        if android_tablet == True:
            chromedriver = os.path.abspath("./chromedriver/M118/chromedriver")
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            )
            options.add_experimental_option("androidPackage", "com.android.chrome")
            self.driver = webdriver.Chrome(
                service=ChromeService(chromedriver), options=options, keep_alive=False
            )
        else:
            # PC
            self.driver = webdriver.Chrome(options=options)
        #youtube AdSkip thread
        self.youtube_adskip_thread = YouTube_Adskip(driver=self.driver)
        self.youtube_adskip_thread.start()

    def __del__(self):
        if(self.youtube_adskip_thread is not None):
            self.youtube_adskip_thread.cancel()
        if(self.youtube_autoplay_thread is not None):
            self.youtube_autoplay_thread.cancel()
        if self.driver:
            self.driver.quit()

    def get_current_url(self):
        driver_class_name = str(self.driver.__class__)
        # Appiumのドライバであるかを判定（例として"AndroidUiautomator2Driver"を使用）
        print(driver_class_name)
        if "appium" in driver_class_name:
            logging.info(self.current_url)
            return self.current_url
        else:
            return self.driver.current_url
        
    def set_start_url(self, url):
        time.sleep(1)
        logging.info(url)
        self.driver.get(url)

    """
	Remove numbers for video selection aids
	"""

    def remove_numbers_from_videos(self, driver):
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

    def add_numbers_to_videos_for_youtube(self, driver):
        try:
            logging.info("start WebDriverWait")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="thumbnail"]'))
            )
            # call javascript directly because taking time for seach id
            script_add_numbers_template = """
			var elements = document.querySelectorAll('[id="thumbnail"]');
			Array.from(elements).forEach(function(el, index) {
				var x = el.getBoundingClientRect().left + window.scrollX;
				var y = el.getBoundingClientRect().top + window.scrollY;
				var isDisplayed = !(el.offsetWidth === 0 && el.offsetHeight === 0);
				if (isDisplayed) {
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
					circle.style.top = '0' + 'px';
					circle.style.left = '0' + 'px';
					circle.style.borderRadius = '50%';
					circle.style.display = 'flex';
					circle.style.justifyContent = 'center';
					circle.style.alignItems = 'center';
					text.innerHTML = index;
					text.style.color = 'white';
					circle.appendChild(text);
					el.appendChild(circle);
					console.log(x, y, index);
				}
			});
			"""
            logging.info("Start executing script to add numbers to video thumbnails.")
            driver.execute_script(script_add_numbers_template)
            logging.info("Numbers added to video thumbnails successfully.")
            if self.lang_id != "ja":
                response = "Moved to the link."
            else:
                response = "リンク先に移動しました"
            return response
        except TimeoutException:
            logging.error("Timed out waiting for input or textarea elements to load.")
            return "videos are not found"

    def add_numbers_to_videos_common(
        self, driver, locator, condition_func, script_template
    ):
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
            # logging.info(video_elements)

            for i, video in enumerate(video_elements):
                x, y = video.location["x"], video.location["y"]
                script = script_template.format(x=x + 15, y=y, i=i)
                logging.info(f"(x, y) = ({x}, {y})")
                driver.execute_script(script, video)
                return "Videos found."
        except TimeoutException:
            logging.error("Timed out waiting for input or textarea elements to load.")
            return "videos are not found"

    def add_numbers_to_videos(self, driver):
        url = self.get_current_url()
        logging.info(f"url: {url}")

        if "m.youtube.com" in url:
            return self.add_numbers_to_videos_common(
                driver,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None,
                self.script_add_numbers_template,
            )
        elif "youtube.com" in url:
            return self.add_numbers_to_videos_for_youtube(driver)
        elif "animestore.docomo.ne.jp" in url:
            return self.add_numbers_to_videos_common(
                driver,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None,
                self.script_add_numbers_template,
            )
        elif "amazon.co.jp" in url:
            return self.add_numbers_to_videos_common(
                driver,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None and "instant-video" in href,
                self.script_add_numbers_template,
            )
        else:
            return "The search was successful. Link selection by number not supported in this web site."

    """
	Called from function call of langchain
	url : VOD service to search for
	input: search string
	"""
    def play_video_in_playlist(self, num, lang_id="ja"):
        logging.info(f"num: {num}, playlist: {self.playlist}")
        try:
            self.youtube_autoplay_thread = YouTube_AutoPlay(driver=self.driver, playlist=self.playlist, playnumber=num, overlay=True)
            self.youtube_autoplay_thread.start()
            return f"プレイリストの{num}番目の動画{self.playlist['list'][num]['title']}を再生します"
        except Exception as e:
            logging.error(f"Error selecting video link: {e}")
            return f"Failed to play the video"

    def search_videos_automatically_at_youtube(self, input: str) -> str:
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[@id="video-title"]'))
        )
        try:
            videos_elements = self.driver.find_elements(
                By.XPATH, '//a[@id="video-title"]'
            )
            video_list = {"type": "video_list", "keyword": input, "list": []}

            i = 0
            limit = 15
            for video_element in videos_elements:
                if i < limit:
                    title = video_element.get_attribute("title")
                    url = video_element.get_attribute("href")
                    video_list["list"].append({"title": title, "url": url})
                    i += 1
                else:
                    break

            self.playlist = video_list
            logging.info(
                f"video_list: {json.dumps(self.playlist, indent=2, ensure_ascii=False)}"
            )
            return f"検索結果からプレイリストを作成しました。プレイリストを再生しますか？"
        except Exception as e:
            logging.error(f"Error selecting video link: {e}")
            return f"Failed to get video list."

    def search_by_query(self, url: str, input: str, lang_id: str = "ja"):
        """
        Called from function call of Open AI
        """
        if(self.youtube_autoplay_thread is not None):
            self.youtube_autoplay_thread.cancel()
            self.youtube_autoplay_thread = None

        logging.info(f" url = {url}, input = {input}, lang_id = {lang_id}")
        self.lang_id = lang_id
        search_queries = {
            "google.com": "https://www.google.com/search?tbm=vid&q=",
            "youtube.com": "https://www.youtube.com/results?search_query=",
            "hulu.jp": "https://www.hulu.jp/search?q=",
            "animestore.docomo.ne.jp": "https://animestore.docomo.ne.jp/animestore/sch_pc?searchKey=",
            "amazon.co.jp": "https://www.amazon.co.jp/s?i=instant-video&k=",
            "yahoo.co.jp": "https://search.yahoo.co.jp/search?p=",
        }
        for domain, query_url in search_queries.items():
            if domain in url:
                goto_url = f"{query_url}{quote(input)}"
                self.current_url = goto_url
                logging.info(f"get({goto_url})")
                self.driver.get(goto_url)
                time.sleep(1)
                # youtubeの場合のみ
                if domain in "youtube.com" and youtube_playlist == True:
                    self.add_numbers_to_videos(self.driver)
                    return self.search_videos_automatically_at_youtube(input)
                return self.add_numbers_to_videos(self.driver)
        return "This is the unsupported Web site."

    """
	Select the link (video) of the selected number
	"""

    def click_link(self, link):
        logging.info(f"link = {link}")
        # 画面表示されていないと落ちるので click() を直接呼び出さない
        # videos[num].click()
        #
        # 表示しているリンク番号を削除
        self.remove_numbers_from_videos(self.driver)
        # 選択したビデオをクリック
        self.driver.execute_script("arguments[0].scrollIntoView();", link)
        self.driver.execute_script("arguments[0].click();", link)
        return

    def select_link_youtube(self, num):
        logging.info(f"Selecting video link number: {num}")
        try:
            # ビデオリンクの取得
            video_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@id="thumbnail"]'))
            )[num]

            # error check
            if not video_element.is_displayed():
                raise Exception(f"Video element number {num} is not visible.")

            # elect link
            self.click_link(video_element)

            # add numbers at the next page after clicking the link
            time.sleep(3)
            return self.add_numbers_to_videos(self.driver)
        except Exception as e:
            logging.error(f"Error selecting video link: {e}")
            return f"Failed to move to selected linked content."

    def select_link_common(self, num, locator, condition_func):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(locator)
            )
            elements = self.driver.find_elements(*locator)

            matching_elements = {}
            for element in elements:
                href = element.get_attribute("href")
                if condition_func(href):
                    if href not in matching_elements:
                        matching_elements[href] = element

            videos = list(matching_elements.values())
            self.click_link(videos[num])
            time.sleep(1)
            self.add_numbers_to_videos(self.driver)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return f"Move to selected linked content failed."

        return f"You have navigated to the content of the link you selected."

    def select_link_by_number(self, num: int, lang_id: str = "ja") -> str:
        """
        Called from function call of Open AI
        """
        if(self.youtube_autoplay_thread is not None):
            self.youtube_autoplay_thread.cancel()
            self.youtube_autoplay_thread = None

        self.lang_id = lang_id
        url = self.get_current_url()
        logging.info(f"num = {num}, url = {url}")

        if "m.youtube.com" in url:
            return self.select_video_common(
                num,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None,
            )
        elif "youtube.com" in url:
            return self.select_link_youtube(num)
        elif "animestore.docomo.ne.jp" in url:
            return self.select_link_common(
                num,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None,
            )
        elif "amazon.co.jp" in url:
            return self.select_link_common(
                num,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None and "instant-video" in href,
            )
        else:
            return

    def youtube_shortcut_key(self, *keys: Any) -> str:
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//html"))
            )
            elements = self.driver.find_elements(By.XPATH, "//html")
            elements[0].send_keys(keys)
            return "success!!!"
        except TimeoutException:
            logging.error("Timed out waiting for input or textarea elements to load.")
            return "videos are not found"
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return f"Error"

    def play_suspend_youtube_mobile(self) -> str:
        """
        it doesn't work well. We must fix issus
        """
        try:
            # 動画のリンクを取得（例として最初の動画）
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="ytm-custom-control"]')
                )
            )
            videos = self.driver.find_elements(
                By.XPATH, '//*[@id="ytm-custom-control"]'
            )
            videos.click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        f"//button[@class='player-control-play-pause-icon']//c3-icon",
                    )
                )
            )
            c3_icon_element = self.driver.find_element(
                By.XPATH, "//button[@class='player-control-play-pause-icon']//c3-icon"
            )
            c3_icon_element.click()
        except TimeoutException:
            logging.error("Timed out waiting for input or textarea elements to load.")
            return "videos are not found"
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return f"Error"

    def play_suspend(self) -> str:
        """
        Called from function call of Open AI
        """
        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return self.play_suspend_youtube_mobile()
        if "youtube.com" in url:
            return self.youtube_shortcut_key("k")
        else:
            return

    def mute(self) -> str:
        """
        Called from function call of Open AI
        """
        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return
        if "youtube.com" in url:
            return self.youtube_shortcut_key("m")
        else:
            return

    def fullscreen(self) -> str:
        """
        Called from function call of Open AI
        """
        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return
        if "youtube.com" in url:
            # not support add_numbers
            self.remove_numbers_from_videos(self.driver)
            return self.youtube_shortcut_key("f")
        else:
            return

    def fast_forward_playback(self) -> str:
        """
        Called from function call of Open AI
        """
        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return
        if "youtube.com" in url:
            # not support add_numbers
            self.remove_numbers_from_videos(self.driver)
            return self.youtube_shortcut_key(">")
        else:
            return

    def slow_forward_playback(self) -> str:
        """
        Called from function call of Open AI
        """
        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return
        if "youtube.com" in url:
            return self.youtube_shortcut_key("<")
        else:
            return

    def play_next_video(self) -> str:
        """
        Called from function call of Open AI
        """
        if(self.youtube_autoplay_thread is not None):
            logging.info(f" self.youtube_autoplay_thread.play_next_video()")
            self.youtube_autoplay_thread.play_next_video()
            num = self.youtube_autoplay_thread.playnumber
            return f"プレイリストの{num}番目の動画{self.playlist['list'][num]['title']}を再生します"

        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return
        if "youtube.com" in url:
            return self.youtube_shortcut_key("N", Keys.SHIFT)
        else:
            return

    def play_previous_video(self) -> str:
        """
        Called from function call of Open AI
        """
        if(self.youtube_autoplay_thread is not None):
            logging.info(f" self.youtube_autoplay_thread.play_previous_video()")
            self.youtube_autoplay_thread.play_previous_video()
            num = self.youtube_autoplay_thread.playnumber
            return f"プレイリストの{num}番目の動画{self.playlist['list'][num]['title']}を再生します"

        url = self.get_current_url()
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return
        if "youtube.com" in url:
            # return self.youtube_shortcut_key("P", Keys.SHIFT)
            return self.driver.back()
        else:
            return

    def start(self):
        self.driver.get("https://www.google.com")


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
        level=logging.INFO,
    )
    test = RemoteChrome()
    test.start()
    test.search_by_query("https://www.youtube.com", "フリーレン")
    time.sleep(1)
    test.select_link_by_number(1)
    time.sleep(1)

    test.fullscreen()
    time.sleep(1)
    test.fullscreen()
    time.sleep(1)

    test.fast_forward_playback()
    time.sleep(2)
    test.fast_forward_playback()
    time.sleep(2)

    test.slow_forward_playback()
    time.sleep(2)
    test.slow_forward_playback()
    time.sleep(2)

    test.mute()
    time.sleep(2)
    test.mute()
    time.sleep(2)

    test.play_suspend()
    time.sleep(2)
    test.play_suspend()
    time.sleep(2)

    test.play_next_video()
    time.sleep(2)
    test.play_previous_video()
    time.sleep(2)

    time.sleep(10)
