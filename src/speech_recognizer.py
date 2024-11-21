# speech_recognizer.py
import vosk
import json
import logging
from collections import deque
from audio_handler import AudioStreamHandler
from command_processor import CommandProcessor

class SpeechRecognizer:
    def __init__(self, model_path, rate=16000, keyword_list=None):
        self.model = vosk.Model(model_path)
        self.rate = rate
        self.recognizer = vosk.KaldiRecognizer(self.model, self.rate)
        self.audio_buffer = deque(maxlen=2)
        self.last_command_time = 0
        self.keyword_list = keyword_list if keyword_list else ["control", "activar", "inicia", "inicio", "comando", "comienza", "oye vera", "hey vera", "hola vera", "vera"]
        self.audio_handler = AudioStreamHandler(rate=self.rate)

    def start_stream(self):
        self.audio_handler.start_stream()

    def listen(self):
        try:
            while True:
                self.process_audio()
        except KeyboardInterrupt:
            logging.info("Sistema detenido.")
        finally:
            self.audio_handler.close_stream()

    def process_audio(self):
        data = self.audio_handler.read_stream()
        if not data:
            return
        processed_data = self.audio_handler.preprocess_audio(data)
        if self.recognizer.AcceptWaveform(processed_data):
            result_json = self.recognizer.Result()
            result = json.loads(result_json)
            recognized_text = result.get("text", "").lower().strip()
            if recognized_text:
                CommandProcessor.process_command(recognized_text, self)
