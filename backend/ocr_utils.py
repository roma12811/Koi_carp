from PIL import Image
import pytesseract
from config import TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def find_text_on_screen(screenshot_path: str, search_text: str) -> dict:
    try:
        img = Image.open(screenshot_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        for i, text in enumerate(data['text']):
            if text.strip() and search_text.lower() in text.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                center_x = x + w // 2
                center_y = y + h // 2

                print(f"✅ OCR: '{search_text}' на ({center_x}, {center_y})")

                return {
                    "x": center_x,
                    "y": center_y,
                    "width": w,
                    "height": h,
                    "radius": max(w, h) // 2 + 10
                }

        print(f"❌ OCR: '{search_text}' не знайдено")
        return None

    except Exception as e:
        print(f"❌ OCR помилка: {e}")
        return None