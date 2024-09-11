import speech_recognition as sr
from deep_translator import GoogleTranslator
import threading
import pyaudio
from threading import Semaphore
from queue import Queue
import time
import socket
import subprocess

def wait(amount):
    time.sleep(amount)
    print()

src_lang = "en"
dest_lang = "fa"

semaphore = Semaphore(1)

translate_result = Queue()
translator = GoogleTranslator(source=src_lang, target=dest_lang)

NAME = socket.gethostname()
T_IP = socket.gethostbyname(NAME)

# Welcome message
print("""\
 _  _  _       _                                        ______   ______        ______  
| || || |     | |                          _           (____  \ / _____)  /\  |  ___ \ 
| || || | ____| | ____ ___  ____   ____   | |_  ___     ____)  ) /       /  \ | |   | |
| ||_|| |/ _  ) |/ ___) _ \|    \ / _  )  |  _)/ _ \   |  __  (| |      / /\ \| |   | |
| |___| ( (/ /| ( (__| |_| | | | ( (/ /   | |_| |_| |  | |__)  ) \_____| |__| | |   | |
 \______|\____)_|\____)___/|_|_|_|\____)   \___)___/   |______/ \______)______|_|   |_| 
  TRANSLATOR -""", NAME, T_IP,)

# Input Audio
Audio = pyaudio.PyAudio()
info = Audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(numdevices):
    if (Audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print(i, " - ", Audio.get_device_info_by_host_api_device_index(0, i).get('name'))

Au_Input = input("Which input are we using?: ")
Input = int(Au_Input)
device_index = Input
print('Ready to translate!')

# Translation 
def translate_text(text, translator, translate_result):
    try:
        result = translator.translate(text=text)
        translate_result.put(result)
    except Exception as e:
        print(f"Translation error: {e}")

def play_audio_with_edge_playback(text):
    try:
        with semaphore:
            command = ['edge-playback', '--voice', 'fa-IR-FaridNeural', '--text', text]
            subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during playback: {e}")

def listen_callback(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio, language=src_lang)
        translate_thread = threading.Thread(target=translate_text, args=(text, translator, translate_result))
        translate_thread.start()
        translate_thread.join()
        result = translate_result.get()
        print(f"Transcribed Text (English): {text}")
        print(f"Translated Text (Persian): {result}")
        play_audio_thread = threading.Thread(target=play_audio_with_edge_playback, args=(result,))
        play_audio_thread.start()
    except sr.UnknownValueError:
        print("Waiting for clean dialogue")
    except sr.RequestError as e:
        print(f"Request error: {e}")

r = sr.Recognizer()
mic = sr.Microphone()

while True:
    try:
        with mic as source:
            audio = r.listen(source, phrase_time_limit=6)
        listen_callback(r, audio)
    except KeyboardInterrupt:
        print("Exiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.1)
