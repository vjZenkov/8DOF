import pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()

print("\n--- СПИСОК ВСЕХ ВХОДНЫХ УСТРОЙСТВ ---")
input_devices = []

for i in range(p.get_device_count()):
    try:
        dev = p.get_device_info_by_index(i)
        if dev.get('maxInputChannels', 0) > 0:
            input_devices.append(i)
            print(f"Индекс [{i}]: {dev.get('name')} | Channels: {dev.get('maxInputChannels')}")
    except Exception:
        pass

print("\n--- ТЕСТ ГРОМКОСТИ (Включите музыку или говорите!) ---")

for idx in input_devices:
    try:
        dev_info = p.get_device_info_by_index(idx)
        rate = int(dev_info.get('defaultSampleRate', 44100))

        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=rate,
                        input=True,
                        input_device_index=idx,
                        frames_per_buffer=1024)

        levels = []
        for _ in range(10):
            data = stream.read(1024, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.float32)
            rms = np.sqrt(np.mean(audio**2))
            levels.append(rms)
            time.sleep(0.05)

        stream.stop_stream()
        stream.close()

        avg_level = np.mean(levels)
        status = "🟢 ЕСТЬ ЗВУК!" if avg_level > 0.001 else "🔴 ТИШИНА"
        print(f"Устройство [{idx}] ({dev_info.get('name')[:30]}...): Уровень = {avg_level:.6f} -> {status}")

    except Exception as e:
        print(f"Устройство [{idx}]: Ошибка подключения")

p.terminate()

# Пауза, чтобы окно не закрывалось
input("\nНажмите Enter, чтобы закрыть...")
