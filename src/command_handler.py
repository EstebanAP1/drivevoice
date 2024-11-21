import logging
import time
import numpy as np
import joblib
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from fuzzywuzzy import process as fuzz
from can_sender import CanSender

class CommandHandler:

    # Lista global de comandos disponibles
    commands_list = [
        "encender luces de cabina", "apagar luces de cabina",
        "encender luces exteriores", "apagar luces exteriores",
        "abrir puerta", "cerrar puerta",
        "consultar nivel de combustible", 
        "encender motor", "apagar motor",
    ]

    # Inicialización de modelos y parámetros
    vectorizer = TfidfVectorizer().fit(commands_list)
    model_ml = MultinomialNB()
    command_history = []
    time_history = []
    max_history_size = 100
    confidence_threshold = {
        "day": 75,
        "night": 70,
    }
    train_batch_size = 5

    # Estado inicial de los dispositivos
    state = {
        "luces_cabina": False,
        "luces_exteriores": False,
        "puerta": False,
        "nivel_combustible": None,
        "motor": False,
    }

    # Lock para acceso seguro al estado compartido
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
        confidence_threshold = cls.confidence_threshold["night"] if 22 <= current_hour or current_hour <= 6 else cls.confidence_threshold["day"]
        best_match, confidence = fuzz.extractOne(command, cls.commands_list)
        return best_match if confidence >= confidence_threshold else None

    @classmethod
    def execute_command(cls, command):
        message = None
        with cls.state_lock:
            sender = CanSender()

            if command == "encender luces de cabina":
                if not cls.state["luces_cabina"]:
                    cls.state["luces_cabina"] = True
                    sender.lights_command(exterior=cls.state['luces_exteriores'], interior=True)
                else:
                    message = "Las luces de cabina ya están encendidas."

            elif command == "apagar luces de cabina":
                if cls.state["luces_cabina"]:
                    cls.state["luces_cabina"] = False
                    sender.lights_command(exterior=cls.state['luces_exteriores'], interior=False)
                else:
                    message = "Las luces de cabina ya están apagadas."

            elif command == "encender luces exteriores":
                if not cls.state["luces_exteriores"]:
                    cls.state["luces_exteriores"] = True
                    sender.lights_command(exterior=True, interior=cls.state['luces_cabina'])
                else:
                    message = "Las luces exteriores ya están encendidas."

            elif command == "apagar luces exteriores":
                if cls.state["luces_exteriores"]:
                    cls.state["luces_exteriores"] = False
                    sender.lights_command(exterior=False, interior=cls.state['luces_cabina'])
                else:
                    message = "Las luces exteriores ya están apagadas."

            elif command == "abrir puerta":
                if not cls.state["puerta"]:
                    sender.door_command(True)
                    cls.state["puerta"] = True
                else:
                    message = "La puerta ya está abierta."

            elif command == "cerrar puerta":
                if cls.state["puerta"]:
                    sender.door_command(False)
                    cls.state["puerta"] = False
                else:
                    message = "La puerta ya está cerrada."
            elif command == "consultar nivel de combustible":
                sender.fuel_level_request()
            elif command == "encender motor":
                if not cls.state["motor"]:
                    sender.engine_control(True)
                    cls.state["motor"] = True
                else:
                    message = "El motor ya está encendido."
            elif command == "apagar motor":
                if cls.state["motor"]:
                    sender.engine_control(False)
                    cls.state["motor"] = False
                else:
                    message = "El motor ya está apagado."
            else:
                best_match = cls.get_best_match(command)
                if best_match:
                    cls.execute_command(best_match)
                    return
                else:
                    cls.fallback_command(command)
                    return
        if message:
          logging.info(message)

    @classmethod
    def fallback_command(cls, command):
        suggestions = fuzz.extract(command, cls.commands_list, limit=3)
        if suggestions:
            logging.warning(f"No se reconoció el comando: '{command}'. ¿Quizás quisiste decir?")
            for suggestion, confidence in suggestions:
                  logging.info(f"- {suggestion} (confianza: {confidence}%)")
        else:
            logging.warning(f"No se encontraron sugerencias para el comando: '{command}'.")

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
        for command in cls.commands_list:
            logging.info(f"- {command}")
        logging.info("Para obtener ayuda, puedes decir 'ayuda'.")

    @classmethod
    def get_state(cls):
        with cls.state_lock:
            return cls.state.copy()
        
    @classmethod
    def get_state(cls):
        with cls.state_lock:
            return cls.state.copy()
