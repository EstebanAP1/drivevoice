# audio_handler.py
import pyaudio
from pydub import AudioSegment
from pydub.effects import normalize

class AudioStreamHandler:
    def __init__(self, rate=16000, chunk_size=1024, format=pyaudio.paInt16, channels=1):
        self.rate = rate
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels

        self.p = pyaudio.PyAudio()  # Inicializar PyAudio
        self.sample_width = self.p.get_sample_size(self.format)  # Obtener sample_width después de inicializar PyAudio

        self.stream = None

    def start_stream(self):
        self.stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

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
        audio_segment = AudioSegment(
            data=audio_data,
            sample_width=self.sample_width,
            frame_rate=self.rate,
            channels=self.channels
        )
        return normalize(audio_segment).raw_data
