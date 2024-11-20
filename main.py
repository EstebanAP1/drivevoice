import vosk
import pyaudio
import json
from fuzzywuzzy import process
import threading
import logging
import time
from collections import deque
import unidecode

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Cargar el modelo de Vosk para español (cambia la ruta según corresponda)
model = vosk.Model("./model")

# Configuración para capturar audio en tiempo real
CHUNK = 1024  # Tamaño del buffer
FORMAT = pyaudio.paInt16  # Formato de audio
CHANNELS = 1  # Canal (mono)
RATE = 16000  # Frecuencia de muestreo

# Inicializar PyAudio
p = pyaudio.PyAudio()

# Abrir flujo de audio
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Inicializar el reconocedor de Vosk
recognizer = vosk.KaldiRecognizer(model, RATE)

# Palabra clave para activar
keyword = ["control", "activar", "inicia", "inicio", "comando"]

# Lista de comandos disponibles
commands_list = [
    "encender luces",
    "apagar luces",
    "abrir puerta",
    "cerrar puerta"
]

# Último comando reconocido
last_command = None
last_command_time = 0

# Estado del sistema (modo de dormir)
sleep_mode = False

# Tiempo para activar automáticamente el modo de dormir (en segundos)
sleep_timeout = 15

# Buffer circular para optimizar el uso de recursos (reducido a 2 fragmentos)
audio_buffer = deque(maxlen=2)

def normalize_text(text):
    return unidecode.unidecode(text).lower().strip()

# Función para encontrar el comando más parecido usando fuzzywuzzy
def get_best_match(command, commands_list):
    best_match, highest_ratio = process.extractOne(command, commands_list)
    return best_match if highest_ratio > 50 else None

# Función para ejecutar el comando en un hilo separado
def ejecutar_comando(comando):
    logging.info(f"Ejecutando comando: {comando}")
    if "encender luces" in comando:
        logging.info("Encendiendo las luces...")
        # Código para encender luces
    elif "apagar luces" in comando:
        logging.info("Apagando las luces...")
        # Código para apagar luces
    elif "abrir puerta" in comando:
        logging.info("Abriendo la puerta...")
        # Código para abrir puerta
    elif "cerrar puerta" in comando:
        logging.info("Cerrando la puerta...")
        # Código para cerrar puerta

logging.info("Sistema en escucha continua...")

try:
    while True:
        # Comprobar si el tiempo de inactividad ha superado el límite para activar el modo de dormir
        if not sleep_mode and (time.time() - last_command_time > sleep_timeout):
            logging.info("No se han detectado comandos recientes. Activando modo dormir...")
            sleep_mode = True

        # Modo de dormir: esperar palabra clave para activarse
        if sleep_mode:
            logging.info("Sistema en modo dormir. Esperando palabra clave para activarse...")
            while sleep_mode:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                except IOError:
                    continue

                if len(data) == 0:
                    continue

                # Procesar solo el fragmento más reciente
                if recognizer.AcceptWaveform(data):
                    result_json = recognizer.Result()
                    result = json.loads(result_json)
                    recognized_text = normalize_text(result.get("text", ""))

                    keyword_found = next((k for k in keyword if k in recognized_text), None)
                    if keyword_found:
                        logging.info("Palabra clave detectada. Activando sistema y procesando comando...")
                        sleep_mode = False
                        last_command_time = time.time()  # Actualizar el tiempo del último comando
                        # Extraer el comando después de la palabra clave
                        command = recognized_text.split(keyword_found, 1)[-1].strip()
                        matched_command = get_best_match(command, commands_list)
                        if matched_command:
                            last_command = matched_command
                            ejecutar_comando(last_command)    # Leer fragmento de audio con manejo de excepciones
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
        except IOError:
            continue
        
        # Si no hay suficiente audio, continuar
        if len(data) == 0:
            continue

        # Añadir el fragmento al buffer circular (solo para optimización, no para concatenar)
        audio_buffer.append(data)

        # Pasar el último fragmento de audio al reconocedor
        if recognizer.AcceptWaveform(data):
            result_json = recognizer.Result()
            result = json.loads(result_json)
            recognized_text = result.get("text", "").lower().strip()
            
            # Mostrar el texto reconocido
            if recognized_text:
                logging.info(f"Texto reconocido: {recognized_text}")

                # Comando de ayuda
                if "ayuda" in recognized_text:
                    logging.info("Comandos disponibles: encender luces, apagar luces, abrir puerta, cerrar puerta")
                    continue

                # Buscar la palabra clave
                keyword_found = next((k for k in keyword if k in recognized_text), None)
                if keyword_found:
                    logging.info("Palabra clave detectada, procesando comando...")

                    # Extraer el comando después de la palabra clave
                    command = recognized_text.split(keyword_found, 1)[-1].strip()

                    # Buscar el mejor comando coincidente
                    matched_command = get_best_match(command, commands_list)

                    # Verificar si el comando es una repetición
                    current_time = time.time()
                    if matched_command and (matched_command != last_command or current_time - last_command_time > 5):
                        last_command = matched_command
                        last_command_time = current_time
                        comando_thread = threading.Thread(target=ejecutar_comando, args=(matched_command,))
                        comando_thread.start()
                        comando_thread.join(timeout=5)  # Tiempo máximo de 5 segundos para ejecutar el comando
                    else:
                        logging.info(f"Comando no reconocido o repetido: {command}")

                # Activar modo de dormir si se reconoce "modo dormir"
                if "modo dormir" in recognized_text:
                    logging.info("Activando modo dormir...")
                    sleep_mode = True

except KeyboardInterrupt:
    logging.info("Sistema detenido.")

finally:
    # Cerrar el flujo de audio
    stream.stop_stream()
    stream.close()
    p.terminate()
