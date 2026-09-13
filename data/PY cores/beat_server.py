import sys
import importlib.metadata

# Создаем заглушку метаданных для madmom
class MockDistribution(importlib.metadata.Distribution):
    def read_text(self, filename): return None
    def locate_file(self, path): return path
    @property
    def metadata(self): return importlib.metadata.Message()
    @property
    def version(self): return "0.4.1"

original_distribution = importlib.metadata.distribution
def smart_distribution(distribution_name, *args, **kwargs):
    if distribution_name.lower() == "madmom":
        return MockDistribution()
    return original_distribution(distribution_name, *args, **kwargs)

importlib.metadata.distribution = smart_distribution

# Импорты нейросети
from BeatNet.BeatNet import BeatNet
import numpy as np
import pyaudio

# Правильный импорт OSC клиента
try:
    from pythonosc.udp_client import SimpleUDPClient
    print("✅ OSC клиент загружен через udp_client")
except ImportError:
    from pythonosc import SimpleUDPClient
    print("✅ OSC клиент загружен напрямую")

print("=============================================")
print("✅ ВСЕ ЗАВИСИМОСТИ И МЕТАДАННЫЕ ИСПРАВЛЕНЫ!")
print("=============================================")

# 1. Настраиваем отправку OSC в TouchDesigner 2025
OSC_IP = "127.0.0.1"
OSC_PORT = 7000
client = SimpleUDPClient(OSC_IP, OSC_PORT)

# 2. Инициализируем BeatNet в режиме реального времени
try:
    estimator = BeatNet(1, mode='realtime', inference_model='PF', plot=[], thread=False)
    print("🤖 Нейросеть BeatNet успешно инициализирована.")
except Exception as e:
    print(f"❌ Ошибка инициализации BeatNet: {e}")
    sys.exit(1)

# 3. Настраиваем аудиопоток через PyAudio
chunk_size = 512
fs = 22050
p = pyaudio.PyAudio()

try:
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=fs,
                    input=True,
                    frames_per_buffer=chunk_size)
    print("🎙️ Аудиопоток открыт. Слушаю звуковую карту...")
except Exception as e:
    print(f"❌ Ошибка открытия аудиопотока: {e}")
    p.terminate()
    sys.exit(1)

print("\n🚀 --- БИТ-СЕРВЕР РАБОТАЕТ И ШЛЕТ OSC НА ПОРТ 7000 ---")

try:
    while True:
        data = stream.read(chunk_size, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.float32)

        # ИСПОЛЬЗУЕМ ОБНОВЛЕННЫЙ МЕТОД ОЦЕНКИ КАДРА
        output = estimator.process(audio_data)

        if output is not None and len(output) > 0:
            beat_number = int(output[0][1])
            client.send_message("/beat", beat_number)

            if beat_number == 1:
                client.send_message("/downbeat", 1)
                print("💥 НАЧАЛО ТАКТА (Доля 1)")
            else:
                client.send_message("/downbeat", 0)
                print(f"  🎵 удар (Доля {beat_number})")

except KeyboardInterrupt:
    print("\nВыключение...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
