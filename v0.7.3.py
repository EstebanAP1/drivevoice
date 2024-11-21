import vosk
import pyaudio
import json
import threading
import logging
import time
from collections import deque
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import numpy as np
import queue
from concurrent.futures import ThreadPoolExecutor
import fuzzywuzzy.process as fuzz
from pydub import AudioSegment
from pydub.effects import normalize

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioStreamHandler:
    def __init__(self, rate=16000, chunk_size=1024, format=pyaudio.paInt16, channels=1):
        self.rate = rate
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.p = pyaudio.PyAudio()
        self.stream = None

    def start_stream(self):
        self.stream = self.p.open(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk_size)

    def read_stream(self):
        try:
            return self.stream.read(self.chunk_size, exception_on_overflow=False)
        except IOError:
            return None

    def close_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def preprocess_audio(self, audio_data):
        audio_segment = AudioSegment(data=audio_data, sample_width=2, frame_rate=self.rate, channels=self.channels)
        return normalize(audio_segment).raw_data

class SpeechRecognizer:
    def __init__(self, model_path, rate=16000, keyword_list=None):
        self.model = vosk.Model(model_path)
        self.rate = rate
        self.recognizer = vosk.KaldiRecognizer(self.model, self.rate)
        self.audio_buffer = deque(maxlen=2)
        self.last_command_time = 0
        self.keyword_list = keyword_list if keyword_list else ["control", "activar", "inicia", "inicio", "comando"]
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

class CommandProcessor:
    @staticmethod
    def process_command(recognized_text, recognizer):
        if "ayuda" in recognized_text:
            CommandHandler.display_help()
            return
        keyword_found = next((k for k in recognizer.keyword_list if k in recognized_text), None)
        if keyword_found:
            command = recognized_text.split(keyword_found, 1)[-1].strip()
            matched_command = CommandHandler.get_best_match(command)
            current_time = time.time()
            if matched_command and (matched_command != recognizer.last_command_time or current_time - recognizer.last_command_time > 5):
                recognizer.last_command_time = current_time
                CommandHandler.queue_command(matched_command)
                CommandHandler.schedule_training(matched_command, time.localtime().tm_hour)
            else:
                logging.info(f"Comando no reconocido o repetido: {command}")
                # Fallback mechanism
                CommandHandler.fallback_command(command)

class CommandHandler:
    commands_list = ["encender luces de cabina", "apagar luces de cabina", "encender luces de lectura", "apagar luces de lectura", "abrir puerta delantera", "abrir puerta trasera", "cerrar puerta delantera", "cerrar puerta trasera"]
    vectorizer = TfidfVectorizer().fit(commands_list)
    commands_vectorized = vectorizer.transform(commands_list)
    model_ml = MultinomialNB()
    command_history = []
    time_history = []
    command_queue = queue.Queue()
    executor = ThreadPoolExecutor(max_workers=5)
    training_scheduled = False

    @classmethod
    def load_model(cls):
        try:
            data = joblib.load("command_history.pkl")
            cls.command_history, cls.time_history = data['command_history'], data['time_history']
            if cls.command_history:
                X = cls.vectorizer.transform(cls.command_history)
                y = np.array(cls.time_history)
                cls.model_ml.fit(X, y)
        except FileNotFoundError:
            cls.command_history, cls.time_history = [], []

    @classmethod
    def get_best_match(cls, command):
        current_hour = time.localtime().tm_hour
        # Reduce el umbral durante la noche (horas menos activas)
        confidence_threshold = 70 if 22 <= current_hour or current_hour <= 6 else 75
        best_match, confidence = fuzz.extractOne(command, cls.commands_list)
        return best_match if confidence > confidence_threshold else None

    @classmethod
    def queue_command(cls, command):
        cls.command_queue.put(command)
        cls.executor.submit(cls.execute_command, command)

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
    def fallback_command(cls, command):
        logging.warning(f"No se reconoció el comando: '{command}'. ¿Quisiste decir uno de los siguientes?")
        suggestions = fuzz.extract(command, cls.commands_list, limit=3)
        for suggestion, confidence in suggestions:
            logging.info(f"- {suggestion} (confianza: {confidence}%)")

    @classmethod
    def schedule_training(cls, command, hour):
        cls.command_history.append(command)
        cls.time_history.append(hour)
        if len(cls.command_history) % 5 == 0:
            cls.train_model()

    @classmethod
    def train_model(cls):
        X = cls.vectorizer.fit_transform(cls.command_history)
        y = np.array(cls.time_history)
        cls.model_ml.fit(X, y)
        joblib.dump({'command_history': cls.command_history, 'time_history': cls.time_history}, "command_history.pkl")
        logging.info("Modelo entrenado y guardado exitosamente.")

    @classmethod
    def display_help(cls):
        logging.info("Comandos disponibles: encender luces, apagar luces, abrir puerta, cerrar puerta")

if __name__ == "__main__":
    CommandHandler.load_model()
    recognizer = SpeechRecognizer("./model")
    recognizer.start_stream()
    recognizer.listen()
