# 必要なモジュールをインポート
import threading
import time
import logging
import uuid

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class YouTube_AutoPlay(threading.Thread):
    def __init__(
        self, driver: webdriver, playlist: [], playnumber: int, overlay: bool = True
    ):
        super().__init__()
        self.driver = driver
        self.playlist = playlist
        self.playnumber = playnumber
        self.overlay = overlay
        self.thread_id = uuid.uuid4()
        self.cancel = False

    def _hide_titles(self):
        try:
            if self.driver.execute_script(
                "return document.getElementById('overlay') !== null;"
            ):
                self.driver.execute_script(
                    "document.getElementById('overlay').remove();"
                )
        except Exception as e:
            logging.error(f"execute_script: {e}")

    def _overlay_titles(self, num):
        if self.overlay == False:
            return
        try:
            list = self.playlist["list"]
            titles = [i["title"] for i in list]
            progress_titles = titles[num:]

            html_content = """
                <div id="overlay" style="
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    height: 30%;
                    background-color: rgba(0, 0, 0, 0.7);
                    z-index: 9999;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                ">
                    <div style="
                        background-color: rgba(255, 255, 255, 0.7); 
                        padding: 20px;
                        width: 80%;
                        text-align: center;
                    ">
                        <div style="font-size: 32px;">Now Playing: {}</div>
                        <div style="font-size: 26px;">Up Next: {}</div>
                    </div>
                </div>
            """.format(
                progress_titles[0],  # 現在のタイトル
                progress_titles[1] if len(progress_titles) > 1 else "None"  # 次のタイトル（存在する場合）
            )

            self.driver.execute_script(
                "document.body.insertAdjacentHTML('beforeend', arguments[0]);",
                html_content,
            )
        except Exception as e:
            logging.error(f"execute_script: {e}")

    def _play_next_video(self):
        try:
            WebDriverWait(self.driver, 60).until(
                EC.url_changes(self.driver.current_url)
            )
            if self.cancel == True:
                return
            self._play()
        except Exception as e:
            logging.error(f"WebDriverWait: {e}")

    def _play(self):
        logging.info(f"num: {self.playnumber}, playlist: {self.playlist}")
        try:
            num = self.playnumber
            url = self.playlist["list"][num]["url"]
            self.driver.get(url)
            self.playnumber += 1
            time.sleep(2)
            self._overlay_titles(num)
        except Exception as e:
            logging.error(f"Error selecting video link: {e}")

    def run(self):
        self._play()
        while True:
            if self.cancel == True:
                logging.info(f"Stopping thread {self.thread_id}.")
                break
            logging.info(
                f"Thread {self.thread_id} received cancel_message: {self.cancel}"
            )
            self._play_next_video()
        self._hide_titles()

    def cancel(self):
        self.cancel = True
        self._hide_titles()

    def __del__(self):
        logging.info(f"Destructor called for thread {self.thread_id}, cleaning up...")


def main():
    playlist = {
        "type": "video_list",
        "keyword": "フリーレン",
        "list": [
            {
                "title": "YOASOBI「勇者」 Official Music Video／TVアニメ『葬送のフリーレン』オープニングテーマ",
                "url": "https://www.youtube.com/watch?v=OIBODIPC_8Y&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "『葬送のフリーレン』第7話「おとぎ話のようなもの」次回予告／10月20日(金)よる11:20放送",
                "url": "https://www.youtube.com/watch?v=IbXI9LU5gZQ&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "milet「Anytime Anywhere」MUSIC VIDEO (TVアニメ『葬送のフリーレン』エンディングテーマ)",
                "url": "https://www.youtube.com/watch?v=r105CzDvoo0&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "【葬送のフリーレン】ヒンメルってそんなに強くない？結局どのくらい強いのこの勇者？を見たネットの反応集【ゆっくり】",
                "url": "https://www.youtube.com/watch?v=pfjLnrcKc_Y&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "『葬送のフリーレン』ノンクレジットOP／OPテーマ：YOASOBI「勇者」／毎週金曜よる11時放送",
                "url": "https://www.youtube.com/watch?v=QoGM9hCxr4k&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "葬送のフリーレン ミニアニメ「●●の魔法」第1回：「考えていることを言ってしまう魔法」",
                "url": "https://www.youtube.com/watch?v=X3Y9esqDspY&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "【葬送のフリーレン】フリーレンの強さって魔力というよりも…を見たネットの反応集【ゆっくり】",
                "url": "https://www.youtube.com/watch?v=-d3QqS0v5Wg&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "【葬送のフリーレン】最強キャラランキング5【ゆっくり解説】",
                "url": "https://www.youtube.com/watch?v=0zoU0yYEV-o&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "ガチで面白い2023年秋アニメ超厳選の新作7作品が歴代最高クラスの名作揃いで強烈すぎる【2023年アニメ】【おすすめアニメ】【薬屋のひとりごと】【葬送のフリーレン】【シャンフロ】【ひきこまり吸血姫】",
                "url": "https://www.youtube.com/watch?v=2qrVBs7iCHg&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "僧侶ハイターを楽しむ読者の反応集【葬送のフリーレン反応集】",
                "url": "https://www.youtube.com/watch?v=ncQhIyDMX1w&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "ジャニーズ・ジブリ・フリーレンなど最新の話題をピックアップ 岡田斗司夫ゼミ＃505（2023.10.1）",
                "url": "https://www.youtube.com/watch?v=JNqzuwsYb_c&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "【葬送のフリーレン】ぶっ壊れ勇者パーティーをわかりやすく解説",
                "url": "https://www.youtube.com/watch?v=9KgAouvuUE8&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "TVアニメ『葬送のフリーレン』PV第2弾／毎週金曜よる11時放送",
                "url": "https://www.youtube.com/watch?v=itKPyGXrCVA&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "【葬送のフリーレン ep6】超作画によって、ドラゴン戦の描写がかなり大迫力に盛られまくる！【ネットの反応】【2023年秋アニメ】フリーレン フェルン #フリーレン #YOASOBI #milet",
                "url": "https://www.youtube.com/watch?v=Dy_-Re-hQHM&pp=ygUP44OV44Oq44O844Os44Oz",
            },
            {
                "title": "『みんな泣くんですよ…泣いちゃう』葬送のフリーレンを見た人が号泣してしまう訳【岡田斗司夫 切り抜き サイコパス アニメ 】",
                "url": "https://www.youtube.com/watch?v=3urgJ5ZJwrA&pp=ygUP44OV44Oq44O844Os44Oz",
            },
        ],
    }

    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
        level=logging.INFO,
    )
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.youtube.com")
    time.sleep(2)

    # dummy operation for automatic video playback
    driver.execute_script("window.scrollBy(0, 100);")
    time.sleep(2)
    autoplay_thread = YouTube_AutoPlay(driver=driver, playlist=playlist, playnumber=0)
    autoplay_thread.start()

    # finish
    autoplay_thread.join()
    time.sleep(2)


if __name__ == "__main__":
    main()
