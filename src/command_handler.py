# command_handler.py
import logging
import time
import numpy as np
import joblib
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import fuzzywuzzy.process as fuzz
from can_sender import CanSender

# Lista global de comandos disponibles
commands_list = [
    "encender luces de cabina", "apagar luces de cabina",
    "encender luces de lectura", "apagar luces de lectura",
    "abrir puerta", "cerrar puerta",
]

class CommandHandler:
    vectorizer = TfidfVectorizer().fit(commands_list)
    commands_vectorized = vectorizer.transform(commands_list)
    model_ml = MultinomialNB()
    command_history = []
    time_history = []
    training_scheduled = False
    max_history_size = 100  # Limitar el historial a los últimos 100 comandos
    confidence_threshold_day = 75  # Umbral de confianza para horas diurnas
    confidence_threshold_night = 70  # Umbral de confianza para horas nocturnas
    train_batch_size = 5  # Número de comandos para desencadenar el entrenamiento

    # Estado inicial de los dispositivos
    state = {
        "luces_cabina": False,
        "luces_lectura": False,
        "puerta": False,
    }

    # Lock reentrante para asegurar acceso seguro al estado compartido
    state_lock = threading.RLock()

    @classmethod
    def load_model(cls):
        try:
            data = joblib.load("command_history.pkl")
            cls.command_history, cls.time_history = data['command_history'], data['time_history']
            if cls.command_history:
                X = cls.vectorizer.transform(cls.command_history)
                y = np.array(cls.time_history)
                cls.model_ml.fit(X, y)
                logging.info("Modelo cargado exitosamente.")
        except FileNotFoundError:
            cls.command_history, cls.time_history = [], []
            logging.info("No se encontró un modelo previo. Se iniciará un nuevo modelo.")

    @classmethod
    def get_best_match(cls, command):
        current_hour = time.localtime().tm_hour
        if 22 <= current_hour or current_hour <= 6:
            confidence_threshold = cls.confidence_threshold_night
        else:
            confidence_threshold = cls.confidence_threshold_day
        best_match, confidence = fuzz.extractOne(command, commands_list)
        logging.debug(f"Mejor coincidencia: {best_match} con confianza {confidence}%")
        return best_match if confidence > confidence_threshold else None

    @classmethod
    def execute_command(cls, command):
        sender = CanSender()
        with cls.state_lock:
            if "encender luces de cabina" == command:
                if not cls.state["luces_cabina"]:
                    cls.state["luces_cabina"] = True
                    message = "Luces de cabina encendidas."
                    sender.send_message()
                else:
                    message = "Las luces de cabina ya están encendidas."
            elif "apagar luces de cabina" == command:
                if cls.state["luces_cabina"]:
                    cls.state["luces_cabina"] = False
                    message = "Luces de cabina apagadas."
                else:
                    message = "Las luces de cabina ya están apagadas."
            elif "encender luces de lectura" == command:
                if not cls.state["luces_lectura"]:
                    cls.state["luces_lectura"] = True
                    message = "Luces de lectura encendidas."
                else:
                    message = "Las luces de lectura ya están encendidas."
            elif "apagar luces de lectura" == command:
                if cls.state["luces_lectura"]:
                    cls.state["luces_lectura"] = False
                    message = "Luces de lectura apagadas."
                else:
                    message = "Las luces de lectura ya están apagadas."
            elif "abrir puerta" == command:
                if not cls.state["puerta"]:
                    cls.state["puerta"] = True
                    message = "Puerta abierta."
                else:
                    message = "La puerta ya está abierta."
            elif "cerrar puerta" == command:
                if cls.state["puerta"]:
                    cls.state["puerta"] = False
                    message = "Puerta cerrada."
                else:
                    message = "La puerta ya está cerrada."
            else:
                # Si el comando no coincide exactamente, intentamos encontrar el mejor match
                best_match = cls.get_best_match(command)
                if best_match:
                    # Llamamos recursivamente a execute_command con el mejor match
                    cls.execute_command(best_match)
                    return
                else:
                    cls.fallback_command(command)
                    return
        # Fuera del lock
        logging.info(message)

    @classmethod
    def fallback_command(cls, command):
        suggestions = fuzz.extract(command, commands_list, limit=3)
        if suggestions:
            logging.warning(f"No se reconoció el comando: '{command}'. ¿Quizás quisiste decir:")
            for suggestion, confidence in suggestions:
                if confidence > 50:  # Umbral para mostrar sugerencias
                    logging.info(f"- {suggestion} (confianza: {confidence}%)")
        else:
            logging.warning(f"No se encontró ninguna sugerencia para el comando: '{command}'")

    @classmethod
    def schedule_training(cls, command, hour):
        with cls.state_lock:
            cls.command_history.append(command)
            cls.time_history.append(hour)
            # Limitar el historial a los últimos 100 comandos
            if len(cls.command_history) > cls.max_history_size:
                cls.command_history = cls.command_history[-cls.max_history_size:]
                cls.time_history = cls.time_history[-cls.max_history_size:]
            # Entrenar el modelo después de acumular un batch de nuevos comandos
            if len(cls.command_history) % cls.train_batch_size == 0:
                cls.train_model()

    @classmethod
    def train_model(cls):
        with cls.state_lock:
            X = cls.vectorizer.fit_transform(cls.command_history)
            y = np.array(cls.time_history)
            cls.model_ml.fit(X, y)
            joblib.dump({'command_history': cls.command_history, 'time_history': cls.time_history}, "command_history.pkl")
            logging.info("Modelo entrenado y guardado exitosamente.")

    @classmethod
    def display_help(cls):
        logging.info("Lista de comandos disponibles:")
        for command in commands_list:
            logging.info(f"- {command}")
        logging.info("Para obtener ayuda, puedes decir 'ayuda'.")

    @classmethod
    def get_state(cls):
        with cls.state_lock:
            return cls.state.copy()
