from flask import Flask, render_template, request, jsonify
import openai
import os, json, tempfile
import logging
import threading
import config
from remote_chat import SimpleConversationRemoteChat

openai.api_key = "YOUR_API_KEY"
app = Flask(__name__, static_folder="./templates", static_url_path="")


@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    try:
        audio_data = request.files["audio"].read()
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=True, suffix=".wav"
        ) as temp_file:
            temp_file.write(audio_data)
            with open(temp_file.name, "rb") as temp_read_file:
                response = openai.Audio.transcribe("whisper-1", temp_read_file)

        transcription = response["text"]
        logging.info(f"transcription {transcription}")
        global remote_chat
        response = remote_chat.llm_run(transcription)
        return jsonify({"transcription": transcription,
                        "response": response,
                        })
    except Exception as e:
        logging.info(f"Exception: {str(e)}")
        return jsonify({"error": "Server Error"}), 500


@app.route("/")
def index():
    return render_template("index.html")

def run_server():
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)

def chat():
    global remote_chat
    chat = remote_chat
    while True:
        user_input = input("Enter the text to search (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break
        chat.llm_run(user_input)

if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
        level=logging.INFO,
    )
    # Start the web server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    openai.api_key = config.keys["openai_api_key"]
    remote_chat = SimpleConversationRemoteChat(history=None)

    # debug
    chat()


