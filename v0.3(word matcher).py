import vosk
import pyaudio
import json
from difflib import SequenceMatcher

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

# Función para encontrar el comando más parecido usando SequenceMatcher
def get_best_match(command, commands_list):
    best_match = None
    highest_ratio = 0.0
    for cmd in commands_list:
        ratio = SequenceMatcher(None, command, cmd).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = cmd
    return best_match if highest_ratio > 0.5 else None

print("Sistema en escucha continua...")

try:
    while True:
        # Leer fragmento de audio
        data = stream.read(CHUNK)
        
        # Si no hay suficiente audio, continuar
        if len(data) == 0:
            continue

        # Pasar el audio al reconocedor
        if recognizer.AcceptWaveform(data):
            result_json = recognizer.Result()
            result = json.loads(result_json)
            recognized_text = result.get("text", "").lower().strip()
            
            # Mostrar el texto reconocido
            if recognized_text:
                print(f"Texto reconocido: {recognized_text}")

                # Buscar la palabra clave
                keyword_found = next((k for k in keyword if k in recognized_text), None)
                if keyword_found:
                    print("Palabra clave detectada, procesando comando...")

                    # Extraer el comando después de la palabra clave
                    command = recognized_text.split(keyword_found, 1)[-1].strip()

                    # Buscar el mejor comando coincidente
                    matched_command = get_best_match(command, commands_list)

                    if matched_command:
                        print(f"Comando más cercano encontrado: {matched_command}")
                        print("Ejecutando comando:", matched_command)
                        if "encender luces" in matched_command:
                            print("Encendiendo las luces...")
                            # Código para encender luces
                        elif "apagar luces" in matched_command:
                            print("Apagando las luces...")
                            # Código para apagar luces
                        elif "abrir puerta" in matched_command:
                            print("Abriendo la puerta...")
                            # Código para abrir puerta
                        elif "cerrar puerta" in matched_command:
                            print("Cerrando la puerta...")
                            # Código para cerrar puerta
                    else:
                        print(f"Comando no reconocido: {command}")

except KeyboardInterrupt:
    print("Sistema detenido.")

finally:
    # Cerrar el flujo de audio
    stream.stop_stream()
    stream.close()
    p.terminate()
