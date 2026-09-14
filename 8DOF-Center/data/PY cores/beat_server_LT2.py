import sys
import time
import msvcrt
import numpy as np
import pyaudio

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    from pythonosc import SimpleUDPClient

OSC_IP = "127.0.0.1"
OSC_PORT = 7000
client = SimpleUDPClient(OSC_IP, OSC_PORT)

chunk_size = 512
fs = 22050

p = pyaudio.PyAudio()

def get_filtered_inputs():
    """Фильтрует дубликаты и нерабочие устройства, возвращая до 10 уникальных входов."""
    filtered_devices = {}
    seen_names = set()

    for i in range(p.get_device_count()):
        try:
            dev_info = p.get_device_info_by_index(i)
            max_channels = dev_info.get('maxInputChannels', 0)

            if max_channels > 0:
                raw_name = dev_info.get('name', f'Device {i}')
                # Убираем системные суффиксы для точной дедупликации
                clean_name = raw_name.split(' (')[0].strip()

                if clean_name not in seen_names and len(filtered_devices) < 10:
                    seen_names.add(clean_name)
                    filtered_devices[i] = clean_name
        except Exception:
            continue

    return filtered_devices

input_devices = get_filtered_inputs()

if not input_devices:
    print("❌ Активные аудиовходы не найдены!")
    p.terminate()
    sys.exit(1)

# Создаем удобный маппинг клавиш '0'-'9' на реальные индексы PyAudio
key_map = {str(digit): idx for digit, idx in enumerate(input_devices.keys())}
active_index = list(input_devices.keys())[0]
stream = None

def open_audio_stream(index):
    global stream
    if stream is not None:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
    try:
        new_stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=fs,
                            input=True,
                            input_device_index=index,
                            frames_per_buffer=chunk_size)
        return new_stream, index
    except Exception as e:
        return None, None

stream, active_index = open_audio_stream(active_index)

# --- ШАПКА И СПИСОК УСТРОЙСТВ ---
def print_banner():
    print("\033[H\033[J", end="")  # Очистка экрана
    print(" ┌──────────────────────────────────────────────┐")
    print(" │  8DOF  |  BEAT DETECTOR SERVER v1.0          │")
    print(" └──────────────────────────────────────────────┘")
    print("  🎧 Статус: АКТИВЕН   │   OSC: 127.0.0.1:7000")
    print(" ────────────────────────────────────────────────")
    print(" 🎙️ ЖИВЫЕ ВХОДЫ (нажмите клавишу 0-9 для переключения):")

    for digit, dev_idx in key_map.items():
        name = input_devices[dev_idx]
        is_active = (dev_idx == active_index)
        mark = "👉" if is_active else "  "
        status = "[АКТИВЕН]" if is_active else "[ГОТОВ]  "

        short_name = name[:32] + "..." if len(name) > 32 else name
        print(f"   {mark} [{digit}] {status} {short_name}")

    print(" ────────────────────────────────────────────────\n")

print_banner()

history_size = 43
buffer = np.zeros(chunk_size * history_size, dtype=np.float32)

beat_count = -1
last_beat_time = time.time()
min_beat_interval = 0.28
threshold_ratio = 1.6

try:
    while True:
        # Быстрый выбор устройства клавишами '0'-'9'
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8', errors='ignore')
            if key in key_map:
                target_idx = key_map[key]
                if target_idx != active_index:
                    new_stream, new_idx = open_audio_stream(target_idx)
                    if new_stream is not None:
                        stream = new_stream
                        active_index = new_idx
                        buffer.fill(0)
                        print_banner()

        if stream is None:
            time.sleep(0.1)
            continue

        try:
            data = stream.read(chunk_size, exception_on_overflow=False)
        except Exception:
            continue

        raw_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

        buffer = np.roll(buffer, -chunk_size)
        buffer[-chunk_size:] = raw_samples

        current_energy = np.sum(raw_samples ** 2)
        avg_energy = np.mean(buffer ** 2) * chunk_size
        rms = np.sqrt(np.mean(raw_samples ** 2))

        now = time.time()

        if current_energy > avg_energy * threshold_ratio and (now - last_beat_time) > min_beat_interval:
            last_beat_time = now

            # Отсчет 0 -> 1 -> 2 -> 3
            beat_count = (beat_count + 1) % 4
            client.send_message("/beat", beat_count)

        # Однострочный индикатор
        bar = "█" * min(int(rms * 80), 20)
        beat_str = f"| 💥 ДОЛЯ: {beat_count}" if beat_count >= 0 else ""
        sys.stdout.write(f"\r🔊 [Канал {active_index}] [{bar:<20}] RMS: {rms:.3f} {beat_str:<18}")
        sys.stdout.flush()

except KeyboardInterrupt:
    print("\n\n⏹️  Сервер остановлен.")
finally:
    if stream is not None:
        stream.stop_stream()
        stream.close()
    p.terminate()
