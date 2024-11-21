# main.py
import threading
import logging
from command_handler import CommandHandler
from speech_recognizer import SpeechRecognizer
from gui import GUI

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    CommandHandler.load_model()

    # Crear instancia de la GUI
    gui = GUI()

    # Crear instancia del reconocedor de voz
    recognizer = SpeechRecognizer("./model")

    # Iniciar el stream de audio
    recognizer.start_stream()

    # Crear hilo para el reconocedor de voz
    recognizer_thread = threading.Thread(target=recognizer.listen)

    # Iniciar el hilo del reconocedor de voz
    recognizer_thread.start()

    # Ejecutar la interfaz gráfica en el hilo principal
    gui.run()

    # Esperar a que el hilo del reconocedor de voz termine (si es que lo hace)
    recognizer_thread.join()

if __name__ == "__main__":
    main()
