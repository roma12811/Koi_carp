import mss
from PIL import Image

def capture_screen(output_path="screenshot.png"):
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # 0 = весь екран (усі монітори)
        screenshot = sct.grab(monitor)

        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img.save("./screenshots/" + output_path)
        print(f"Скріншот збережено як {"./screenshots/" + output_path}")
        
capture_screen("screenshot.png")

capture_screen()