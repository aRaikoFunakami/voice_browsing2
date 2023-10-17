import os

keys = {
    "openai_api_key": "<YOUR OPENAI ID>",
}

def load():
    os.environ["OPENAI_API_KEY"] = keys["openai_api_key"]