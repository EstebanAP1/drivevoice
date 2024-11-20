import whisper
import pyaudio
import numpy as np

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

# Cargar el modelo Whisper
model = whisper.load_model("medium")

# Palabra clave para activar
keyword = "activar"

# Definir el idioma para la transcripción
language = "es"  # Cambiar el idioma según se necesite

print("Sistema en escucha...")

try:
    while True:
        print("Escuchando...")
        frames = []

        # Capturar audio durante 3 segundos (ajustable)
        for _ in range(0, int(RATE / CHUNK * 3)):
            data = stream.read(CHUNK)
            frames.append(data)

        # Convertir el audio a un numpy array
        audio_data = b''.join(frames)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        # Procesar el audio con Whisper
        print("Procesando audio con Whisper...")
        result = model.transcribe(audio_np, fp16=False, language=language)
        recognized_text = result['text'].lower()
        print(f"Texto reconocido: {recognized_text}")

        # Buscar la palabra clave
        if keyword in recognized_text:
            print("Palabra clave detectada, procesando comando...")

            # Extraer el comando después de la palabra clave
            command = recognized_text.split(keyword, 1)[1].strip()

            # Realizar acciones según el comando
            if "encender luces" in command:
                print("Encendiendo las luces...")
                # Código para encender luces
            elif "abrir puerta" in command:
                print("Abriendo la puerta...")
                # Código para abrir puerta
            else:
                print(f"Comando no reconocido: {command}")

except KeyboardInterrupt:
    print("Sistema detenido.")

finally:
    # Cerrar el flujo de audio
    stream.stop_stream()
    stream.close()
    p.terminate()
