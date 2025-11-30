import mss
from PIL import Image
from datetime import datetime
from config import SCREENSHOTS_DIR


def capture_screen(output_filename: str = None) -> str:

    if not output_filename:
        output_filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S")

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        filepath = SCREENSHOTS_DIR / f"{output_filename}.png"
        img.save(filepath)

        print(f"✅ Скріншот: {filepath}")
        return str(filepath)


def get_screenshot_dimensions(screenshot_path: str) -> tuple:
    """Повертає (ширина, висота) скріншоту"""
    try:
        img = Image.open(screenshot_path)
        return img.size
    except Exception as e:
        print(f"❌ Помилка отримання розмірів: {e}")
        return (1920, 1080)