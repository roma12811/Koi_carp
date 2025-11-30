from PIL import ImageGrab
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"D:\Dev\Tesseract\tesseract.exe"
# Робимо скріншот всього екрану
screenshot = ImageGrab.grab()
screenshot = screenshot.convert("RGB")

# Використовуємо Tesseract для розпізнавання
data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)

# Шукаємо конкретне слово
word_to_find = "program.py"
for i, text in enumerate(data['text']):
    if text.lower() == word_to_find.lower():
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        print(f"Found '{word_to_find}' at ({x}, {y}, {x+w}, {y+h})")
