# voice_browsing2

Voice Browsing2 is a project that allows for text and voice-based browsing control, primarily on an Android device. Below are the steps to set up the project and get started with using it.

<img src="templates/concept.png" width="50%" />


## Setup
Firstly, clone the repository and navigate into the project directory:

```terminal:
$ cd work
$ git clone https://github.com/aRaikoFunakami/voice_browsing2.git
$ cd voice_browsing2/
```

Please prepare [poetry](https://python-poetry.org/docs/) like the following commands

```terminal: for Mac/Linux/Windows
$ curl -sSL https://install.python-poetry.org | python3 -
```

If your machine is Mac...

```terminal: for Mac brew
$ brew install poetry
```

Once inside the project directory, use poetry to install the necessary dependencies:

```terminal
$ poetry install
```

Next, copy the sample configuration file config_sample.py to config.py:

```terminal
$ cp config_sample.py config.py
```

Please replace `<YOUR OPENAI ID>` by your OpenAI ID in config.py.

```text:config.py
keys = {
    "openai_api_key": "<YOUR OPENAI ID>",
}
```


## Connect to the Android Device
Ensure your Android device is connected to your machine. You can verify the connection using the following command:

```terminal
$ adb devices
List of devices attached
R52N800FR2Y	device
```

The device ID R52N800FR2Y confirms that the device is successfully connected.


## Text-based Browsing
To initiate text-based browsing, run the following command:

```terminal
$ poetry run python remote_chat.py
```

You'll be prompted to enter a text search query. For instance, to search for "Back to the Future" on YouTube, type the following and hit enter:

```terminal
Enter the text to search (or 'exit' to quit): search "back to the future" in youtube
```

The program will execute the search and prompt you to select a link from the search results:


```terminal
> Entering new AgentExecutor chain...

Invoking: `search_by_query` with `{'url': 'https://www.youtube.com/', 'input': 'back to the future'}`


<class 'selenium.webdriver.chrome.webdriver.WebDriver'>
The search was successful. Please ask Human to select links.I have searched for "back to the future" on YouTube. Please select the link you want to open by providing the corresponding number.

> Finished chain.
Enter the text to search (or 'exit' to quit):
```

## Voice Browsing
Voice browsing allows you to control the browsing experience using voice commands. To set up voice browsing, run the following command to launch the server application:

```terminal
poetry run python app.py
```

The Chrome application on your connected Android device will launch automatically.
Next, launch the voice controller application as a Web App by running the following command:

```terminal
open -a 'Google Chrome' 'http://127.0.0.1:8080'
```

Now you can use voice commands to control the browsing experience on your Android device.

These steps should provide a smooth setup and user experience for text and voice-controlled browsing using the voice_browsing2 project.

## Support list in v0.1.0

| Actions                  | YouTube | Amazon Prime | Hulu | dAnime |
|--------------------------|---------|--------------|------|--------|
| Video Search             | YES     | YES          | YES  | YES    |
| Select by Number         | YES     | -            | -    | -      |
| Play/Pause               | YES     | -            | -    | -      |
| Audio Mute               | YES     | -            | -    | -      |
| Enter Fullscreen         | YES     | -            | -    | -      |
| Adjust Playback Speed    | YES     | -            | -    | -      |
| Navigate Videos          | YES     | -            | -    | -      |

