import whisper
import pyaudio
import wave
import json
from deep_translator import GoogleTranslator
import threading
from threading import Semaphore
from queue import Queue
import time
import socket
import subprocess
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead", category=UserWarning)


# Set the language codes
src_lang = "en"
dest_lang = "fa"

semaphore = Semaphore(1)
translate_result = Queue()
translator = GoogleTranslator(source=src_lang, target=dest_lang)

NAME = socket.gethostname()
T_IP = socket.gethostbyname(NAME)

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000 
CHUNK = 1024

# Welcome message
print(f"""
 _  _  _       _                                        ______   ______        ______  
| || || |     | |                          _           (____  \ / _____)  /\  |  ___ \ 
| || || | ____| | ____ ___  ____   ____   | |_  ___     ____)  ) /       /  \ | |   | |
| ||_|| |/ _  ) |/ ___) _ \|    \ / _  )  |  _)/ _ \   |  __  (| |      / /\ \| |   | |
| |___| ( (/ /| ( (__| |_| | | | ( (/ /   | |_| |_| |  | |__)  ) \_____| |__| | |   | |
 \______|\____)_|\____)___/|_|_|_|\____)   \___)___/   |______/ \______)______|_|   |_| 
  TRANSLATOR - {NAME} {T_IP} 
""")

# Load Whisper
model = whisper.load_model("base")

# Set up audio input
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


# The function that does the trabslating
def translate_text(text, translator, translate_result):
    try:
        result = translator.translate(text=text)
        translate_result.put(result)
    except Exception as e:
        print(f"Translation error: {e}")

def play_audio_with_edge_playback(text):
    try:
        with semaphore:
            command = ['edge-playback', '--voice', 'fa-IR-FaridNeural', '--text', text, '--rate=+20%']
            subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during playback: {e}")

def listen_and_transcribe():
    stream = Audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=4096)
    stream.start_stream()

    while True:
        frames = []
        print("Recording...")
        for _ in range(0, int(RATE / CHUNK * 6)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        # Save input audio to a temp file for Whisper
        wf = wave.open("temp.wav", 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(Audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Transcribe the audio using Whisper
        result = model.transcribe("temp.wav")
        text = result['text']

        ###################################
        #   .-.
        #  (o o) YouGhost
        #  | O \
        #   \   \
        #    `~~~'
        # Removing YouGhost from the script
        ###################################

        # Check if the transcribed text is exactly "you"
        if text.lower().strip() == "you":
            print("YouGhost detected, skipping translation")
            continue  # Skip the translation process

        if text:
            translate_thread = threading.Thread(target=translate_text, args=(text, translator, translate_result))
            translate_thread.start()
            translate_thread.join()
            translated_text = translate_result.get()
            print(f"Transcribed Text (English): {text}")
            print(f"Translated Text (Persian): {translated_text}")
            play_audio_thread = threading.Thread(target=play_audio_with_edge_playback, args=(translated_text,))
            play_audio_thread.start()

if __name__ == "__main__":
    try:
        listen_and_transcribe()
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")

# be kind - don't eat animals 
# BCAN - ben costerton audio network 
