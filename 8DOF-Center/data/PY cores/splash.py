import os
import socket
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageFont, ImageDraw

# --- Конфигурация заставки ---
SPLASH_WIDTH = 900
SPLASH_HEIGHT = 500
BG_COLOR = "#222222"         # Тёмно-серый фон
BORDER_COLOR = "#333333"     # Цвет рамки окна
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT_COLOR = "#999999"

# Определение путей от расположения splash.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # \data\PY cores
DATA_DIR = os.path.dirname(SCRIPT_DIR)                   # \data

IMAGE_PATH = os.path.join(DATA_DIR, "graphic", "logov03_cream.png")
FONT_PATH = os.path.join(DATA_DIR, "fonts", "buttons_font.ttf")

root = tk.Tk()
root.overrideredirect(True)
root.configure(bg=BORDER_COLOR) # Цвет рамки подложкой

# --- Центрирование окна ---
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int((screen_width / 2) - (SPLASH_WIDTH / 2))
center_y = int((screen_height / 2) - (SPLASH_HEIGHT / 2))
root.geometry(f"{SPLASH_WIDTH}x{SPLASH_HEIGHT}+{center_x}+{center_y}")

# Внутренний контейнер с отступом 2px под рамочку
window_frame = tk.Frame(root, bg=BG_COLOR)
window_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

# --- Вспомогательная функция для генерации текста с TTF шрифтом ---
def render_custom_text(text, font_path, size, color):
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, size)
    else:
        font = ImageFont.load_default()
    
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0] + 10
    height = bbox[3] - bbox[1] + 10
    
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, font=font, fill=color)
    
    return ImageTk.PhotoImage(img)

# --- Основные контейнеры ---
# 1. Футер снизу
footer_label = tk.Label(
    window_frame,
    text="Created by Stanislav Zenkov in TouchDesigner",
    fg=MUTED_TEXT_COLOR,
    bg=BG_COLOR,
    font=("Helvetica", 9),
    anchor="center"
)
footer_label.pack(side=tk.BOTTOM, fill=tk.X, pady=15)

# 2. Главный контейнер для колонок
main_container = tk.Frame(window_frame, bg=BG_COLOR)
main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(40, 0), pady=(30, 0))

# Левая половина (Все тексты + Прогресс-бар)
left_frame = tk.Frame(main_container, bg=BG_COLOR)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Правая половина (Большой логотип)
right_frame = tk.Frame(main_container, bg=BG_COLOR)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

# --- Наполнение ЛЕВОЙ половины ---
# 1. Заголовок (8DOF - Center)
title_img = render_custom_text("8DOF - Center", FONT_PATH, 42, TEXT_COLOR)
title_label = tk.Label(left_frame, image=title_img, bg=BG_COLOR, anchor="w")
title_label.image = title_img
title_label.pack(fill=tk.X, anchor="w", pady=(30, 5))

# 2. Подзаголовок (Imagine, creat, play.)
subtitle_img = render_custom_text("Imagine, creat, play.", FONT_PATH, 20, MUTED_TEXT_COLOR)
subtitle_label = tk.Label(left_frame, image=subtitle_img, bg=BG_COLOR, anchor="w")
subtitle_label.image = subtitle_img
subtitle_label.pack(fill=tk.X, anchor="w", pady=(0, 40))

# 3. Подпись статуса
loading_label = tk.Label(
    left_frame, 
    text="Loading system...", 
    fg=TEXT_COLOR, 
    bg=BG_COLOR, 
    font=("Helvetica", 10)
)
loading_label.pack(anchor="w", pady=(0, 5))

# 4. Прогресс-бар
style = ttk.Style()
style.theme_use('default')
style.configure(
    "Custom.Horizontal.TProgressbar", 
    troughcolor='#333333', 
    background='#ffffff', 
    thickness=4, 
    borderwidth=0
)

progress = ttk.Progressbar(
    left_frame, 
    orient="horizontal", 
    length=280, 
    mode="indeterminate", 
    style="Custom.Horizontal.TProgressbar"
)
progress.pack(anchor="w")
progress.start(25) # Медленный бегунок слева направо

# --- Наполнение ПРАВОЙ половины (Крупный логотип во всю высоту) ---
if os.path.exists(IMAGE_PATH):
    img = Image.open(IMAGE_PATH)
    max_img_height = 400 # Масштабируем по всей доступной высоте окна
    aspect_ratio = img.width / img.height
    new_width = int(max_img_height * aspect_ratio)
    
    img_resized = img.resize((new_width, max_img_height), Image.Resampling.LANCZOS)
    photo_img = ImageTk.PhotoImage(img_resized)
    
    img_label = tk.Label(right_frame, image=photo_img, bg=BG_COLOR, anchor="e")
    img_label.image = photo_img
    img_label.pack(fill=tk.BOTH, anchor="e", expand=True)

# --- Логика ожидания сигнала закрытия от TouchDesigner (UDP) ---
def listen_for_td():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 9000))
    sock.settimeout(1.0)
    
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            if b'ready' in data:
                root.after(0, root.destroy)
                break
        except socket.timeout:
            continue

threading.Thread(target=listen_for_td, daemon=True).start()

root.mainloop()