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


class RemoteTest:
    def __init__(self):
        options = webdriver.ChromeOptions()
        # options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 4.3; Nexus 7 Build/JSS15Q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=options)

    def __del__(self):
        if self.driver:
            self.driver.quit()

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

    def add_numbers_to_videos_for_youtube(self, driver):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"video-title"))
            )
            video_elements = driver.find_elements(By.ID, "video-title")

            for i, video in enumerate(video_elements):
                x, y = video.location["x"], video.location["y"]
                script = self.script_add_numbers_template.format(x=x - 60, y=y, i=i)
                driver.execute_script(script, video)
        except TimeoutException:
            logging.error("Timed out waiting for input or textarea elements to load.")
            return "videos are not found"

        return "The search was successful. Please ask Human to select links."

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
        except TimeoutException:
            logging.error("Timed out waiting for input or textarea elements to load.")
            return "videos are not found"

        return "The search was successful. Please ask Human to select links."

    def add_numbers_to_videos(self, driver):
        url = driver.current_url
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

    def search_by_query(self, url: str, input: str):
        """
        Called from function call of Open AI
        Args:
                                        url(str) : VOD service to search for.
                                        input(str): search string.
        Returns:
                                        str: Answer about the results of clicking on the link.
        """
        logging.info(f" url = {url}, input = {input}")
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
                self.driver.get(f"{query_url}{quote(input)}")
                time.sleep(1)
                return self.add_numbers_to_videos(self.driver)
        return "This is the nsupported Web site."

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

    def select_video_youtube(self, num):
        logging.info(f"num = {num}")
        try:
            # 動画のリンクを取得（例として最初の動画）
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, f"video-title"))
            )
            videos = self.driver.find_elements(By.ID, "video-title")
            self.click_link(videos[num])
            # クリック先でリンク番号を追加
            # 非同期処理のため WebDriverWait では正常に動作しない
            time.sleep(2)
            self.add_numbers_to_videos(self.driver)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return f"Playback of the selected video has not started."

        return f"Playback of the selected video has started."

    def select_video_common(self, num, locator, condition_func):
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
            return f"Error"

        return f"The search was successful. Please ask Human to select links."

    def select_link_by_number(self, num: int) -> str:
        """
        Called from function call of Open AI
        Args:
                                        num (int): click the numth link
        Returns:
                                        str: Answer about the results of clicking on the link
        """
        url = self.driver.current_url
        logging.info(f"num = {num}, url = {url}")

        if "m.youtube.com" in url:
            return self.select_video_common(
                num,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None,
            )
        elif "youtube.com" in url:
            return self.select_video_youtube(num)
        elif "animestore.docomo.ne.jp" in url:
            return self.select_video_common(
                num,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None,
            )
        elif "amazon.co.jp" in url:
            return self.select_video_common(
                num,
                (By.XPATH, "//a[descendant::img]"),
                lambda href: href is not None and "instant-video" in href,
            )
        else:
            return

    def play_suspend_youtube(self) -> str:
        element = self.driver.find_element(By.TAG_NAME, "html")
        element.send_keys("k")
        return "success!!!"

    def play_suspend_youtube_mobile(self) -> str:
        """
        it doesn't work well. We must fix issus
        """
        try:
            # 動画のリンクを取得（例として最初の動画）
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, f"ytm-custom-control"))
            )
            element = self.driver.find_element(By.ID, "ytm-custom-control")
            element.click()
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
        Args:
        Returns:
                str: Answer about the results of play or suspend
        """
        url = self.driver.current_url
        logging.info(f"url = {url}")
        if "m.youtube.com" in url:
            return self.play_suspend_youtube_mobile()
        if "youtube.com" in url:
            return self.play_suspend_youtube()
        else:
            return

    def start(self):
        self.driver.get("https://www.google.com")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(filename)s: %(levelname)s: %(funcName)s: %(message)s",
        level=logging.INFO,
    )
    test = RemoteTest()
    test.start()
    test.search_by_query("http://www.youtube.com", "フリーレン")
    time.sleep(2)
    test.select_link_by_number(0)
    time.sleep(2)
    test.play_suspend()
    time.sleep(10)
