import vosk
import pyaudio
import json
import threading
import logging
import time
from collections import deque
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import numpy as np
import queue
from concurrent.futures import ThreadPoolExecutor
import fuzzywuzzy.process as fuzz

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SpeechRecognizer:
    def __init__(self, model_path, rate=16000):
        self.model = vosk.Model(model_path)
        self.rate = rate
        self.recognizer = vosk.KaldiRecognizer(self.model, self.rate)
        self.audio_buffer = deque(maxlen=2)
        self.sleep_mode = False
        self.sleep_timeout = 15
        self.last_command_time = 0
        self.keyword = ["control", "activar", "inicia", "inicio", "comando"]

    def start_stream(self, chunk_size=1024, format=pyaudio.paInt16, channels=1):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=format, channels=channels, rate=self.rate, input=True, frames_per_buffer=chunk_size)
        return self.stream

    def listen(self):
        try:
            while True:
                # Comprobar si debe entrar en modo dormir
                if not self.sleep_mode and (time.time() - self.last_command_time > self.sleep_timeout):
                    logging.info("No se han detectado comandos recientes. Activando modo dormir...")
                    self.sleep_mode = True

                if self.sleep_mode:
                    self.sleep_mode = self.wait_for_keyword()
                else:
                    self.process_audio()
        except KeyboardInterrupt:
            logging.info("Sistema detenido.")
        finally:
            self.close_stream()

    def wait_for_keyword(self):
        logging.info("Sistema en modo dormir. Esperando palabra clave para activarse...")
        while self.sleep_mode:
            data = self.read_stream()
            if not data:
                continue
            if self.recognizer.AcceptWaveform(data):
                result_json = self.recognizer.Result()
                result = json.loads(result_json)
                recognized_text = result.get("text", "").lower().strip()
                if any(k in recognized_text for k in self.keyword):
                    logging.info("Palabra clave detectada. Activando sistema...")
                    self.last_command_time = time.time()
                    return False
        return True

    def process_audio(self):
        data = self.read_stream()
        if not data:
            return
        if self.recognizer.AcceptWaveform(data):
            result_json = self.recognizer.Result()
            result = json.loads(result_json)
            recognized_text = result.get("text", "").lower().strip()
            if recognized_text:
                CommandHandler.handle_command(recognized_text, self)

    def read_stream(self):
        try:
            return self.stream.read(1024, exception_on_overflow=False)
        except IOError:
            return None

    def close_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

class CommandHandler:
    commands_list = ["encender luces", "apagar luces", "abrir puerta", "cerrar puerta"]
    vectorizer = CountVectorizer().fit(commands_list)
    commands_vectorized = vectorizer.transform(commands_list)
    model_ml = MultinomialNB()
    command_history = []
    time_history = []
    command_queue = queue.Queue()
    executor = ThreadPoolExecutor(max_workers=3)

    @classmethod
    def load_model(cls):
        try:
            with open("command_history.pkl", "rb") as f:
                cls.command_history, cls.time_history = pickle.load(f)
                if cls.command_history:
                    X = cls.vectorizer.transform(cls.command_history)
                    y = np.array(cls.time_history)
                    cls.model_ml.fit(X, y)
        except FileNotFoundError:
            cls.command_history, cls.time_history = [], []

    @classmethod
    def handle_command(cls, recognized_text, recognizer):
        if "ayuda" in recognized_text:
            logging.info("Comandos disponibles: encender luces, apagar luces, abrir puerta, cerrar puerta")
            return
        keyword_found = next((k for k in recognizer.keyword if k in recognized_text), None)
        if keyword_found:
            command = recognized_text.split(keyword_found, 1)[-1].strip()
            matched_command = cls.get_best_match(command)
            current_time = time.time()
            if matched_command and (matched_command != recognizer.last_command_time or current_time - recognizer.last_command_time > 5):
                recognizer.last_command_time = current_time
                cls.command_queue.put(matched_command)
                cls.executor.submit(cls.execute_command, matched_command)
                cls.train_model(matched_command, time.localtime().tm_hour)
            else:
                logging.info(f"Comando no reconocido o repetido: {command}")
        if "modo dormir" in recognized_text:
            logging.info("Activando modo dormir...")
            recognizer.sleep_mode = True

    @classmethod
    def get_best_match(cls, command):
        best_match, confidence = fuzz.extractOne(command, cls.commands_list)
        return best_match if confidence > 70 else None

    @classmethod
    def execute_command(cls, command):
        logging.info(f"Ejecutando comando: {command}")
        if "encender luces" in command:
            logging.info("Encendiendo las luces...")
        elif "apagar luces" in command:
            logging.info("Apagando las luces...")
        elif "abrir puerta" in command:
            logging.info("Abriendo la puerta...")
        elif "cerrar puerta" in command:
            logging.info("Cerrando la puerta...")

    @classmethod
    def train_model(cls, command, hour):
        cls.command_history.append(command)
        cls.time_history.append(hour)
        X = cls.vectorizer.fit_transform(cls.command_history)
        y = np.array(cls.time_history)
        cls.model_ml.fit(X, y)
        with open("command_history.pkl", "wb") as f:
            pickle.dump((cls.command_history, cls.time_history), f)

if __name__ == "__main__":
    CommandHandler.load_model()
    recognizer = SpeechRecognizer("./model")
    recognizer.start_stream()
    recognizer.listen()
