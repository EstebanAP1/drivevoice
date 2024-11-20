import vosk
import pyaudio
import json

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
keyword = "activar"

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
                if keyword in recognized_text:
                    print("Palabra clave detectada, procesando comando...")

                    # Extraer el comando después de la palabra clave
                    command = recognized_text.split(keyword, 1)[1].strip()

                    # Realizar acciones según el comando
                    if "luces" in command:
                        print("Encendiendo las luces...")
                        # Código para encender luces
                    elif "abrir puerta" in command:
                        print("Abriendo la puerta...")
                        # Código para abrir puerta
                    elif "luces bajas" in command:
                        print("Colocando luces bajas...")
                    else:
                        print(f"Comando no reconocido: {command}")

except KeyboardInterrupt:
    print("Sistema detenido.")

finally:
    # Cerrar el flujo de audio
    stream.stop_stream()
    stream.close()
    p.terminate()
