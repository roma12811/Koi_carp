import base64
import os
import re
import json
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from openai import OpenAI

# Налаштування Tesseract
pytesseract.pytesseract.tesseract_cmd = r"D:\Dev\Tesseract\tesseract.exe"

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI()

SYSTEM_PROMPT = ""
MAX_TOKENS = 1500
MODEL = "gpt-4o-mini"


def image_to_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def parse_program_message(message: str):
    # Парсимо Name
    name_match = re.search(r'Name:\s*"([^"]+)"', message)
    name = name_match.group(1) if name_match else None

    # Парсимо Location
    location_match = re.search(r'Location:\s*"([^"]+)"', message)
    location = location_match.group(1) if location_match else None

    # Парсимо Actions
    actions_matches = re.findall(r'Action:\s*"([^"]+)"', message)
    actions = actions_matches if actions_matches else []

    return {
        "Name": name,
        "Location": location,
        "Actions": actions
    }


def define_program(screen_url):
    b64_img = image_to_base64(screen_url)
    prompt = f"""You are a UI expert and you are given screenshot of some program in Base64 format. 
      Response in format:
        Name: "put here name of the program"
        Location: "put here the current location of program page that is shown on screenshot. For example: home_page -> settings"
        Action: "first action"
        Action: "second action"
        Action: "third action"
        Action: "fourth action"
        Action: "fifth action"

      Strictly follow brackets in response template
      No explanations, no extra text."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_img}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        max_tokens=MAX_TOKENS
    )

    print(response.choices[0].message.content.strip())
    print("------------------------------------------")

    return parse_program_message(response.choices[0].message.content.strip())


def get_screenshot_dimensions(screenshot_path: str) -> tuple:
    """Отримує розміри скріншоту (ширина, висота)"""
    try:
        img = Image.open(screenshot_path)
        return img.size  # (width, height)
    except Exception as e:
        print(f"Error getting screenshot dimensions: {e}")
        return (1920, 1080)


def find_text_on_screen(screenshot_path: str, search_text: str) -> dict:
    """
    Шукає текст на скріншоті через Tesseract OCR.
    Повертає координати: {"x": int, "y": int, "width": int, "height": int}
    або None якщо текст не знайдено
    """
    try:
        img = Image.open(screenshot_path)

        # Розпізнаємо текст з координатами
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        # Шукаємо слово
        for i, text in enumerate(data['text']):
            if text.strip() and search_text.lower() in text.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                # Повертаємо центр слова
                center_x = x + w // 2
                center_y = y + h // 2

                print(f"✅ OCR: Знайдено '{search_text}' на ({center_x}, {center_y}), розмір={w}x{h}")

                return {
                    "x": center_x,
                    "y": center_y,
                    "width": w,
                    "height": h,
                    "radius": max(w, h) // 2 + 10
                }

        print(f"❌ OCR: Текст '{search_text}' не знайдено на екрані")
        return None

    except Exception as e:
        print(f"❌ OCR Error: {e}")
        return None


def extract_quoted_text(text: str) -> list:
    """Витягує текст в лапках з інструкції"""
    matches = re.findall(r'"([^"]+)"', text)
    return matches


def generate_instructions(program_name: str, current_location: str, action: str, screenshot_path: str = None) -> list:
    """
    Генерує конкретні кроки (назви кнопок/елементів) для виконання дії.
    Якщо передано screenshot_path, AI буде аналізувати реальні елементи на екрані.

    Повертає список словників з форматом:
    {
        "action": "Click \"File\" menu",
        "quoted_text": ["File"],
        "coordinates": {"x": 150, "y": 50, "radius": 20}  # або None якщо координати невідомі
    }
    """

    if screenshot_path and os.path.exists(screenshot_path):
        b64_img = image_to_base64(screenshot_path)

        prompt = f"""You are a UI expert analyzing a screenshot of {program_name}.

Current location: {current_location}
Required action: {action}

Based on the visible UI elements in the screenshot, provide a step-by-step instruction to complete this action.

IMPORTANT:
- Return ONLY the exact button/menu/field names as they appear in the UI, WRAPPED IN DOUBLE QUOTES ("")
- One action/click per line
- Be precise and specific - mention exact text on buttons, menu items, or fields in quotes
- Include typing instructions if text input is needed (e.g., "Type: \\"filename\\" in the file name field")
- Use imperative form (Click, Type, Select, etc.)
- Do NOT include explanations or numbers
- Do NOT include step numbers or bullet points
- Start directly with the first action
- EVERY button name, menu item, or text must be in double quotes ""

Example format:
Click "File" menu
Click "Save As"
Type "document_name" in the "filename" field
Select "PDF format" from "dropdown"
Click "Save" button"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_img}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=MAX_TOKENS
        )

        text = response.choices[0].message.content.strip()
        steps = [line.strip("- 0123456789.").strip() for line in text.splitlines() if line.strip()]

        # Тепер обробляємо кожну інструкцію
        result = []
        for step in steps:
            # Витягуємо текст в лапках
            quoted_texts = extract_quoted_text(step)

            # Намагаємося знайти координати для першого цитованого тексту
            coordinates = None
            if quoted_texts:
                coordinates = find_text_on_screen(screenshot_path, quoted_texts[0])

            result.append({
                "action": step,
                "quoted_text": quoted_texts,
                "coordinates": coordinates
            })

        return result
    else:
        # Fallback без скріншоту
        prompt = f"""You are a UI expert. Generate step-by-step instructions for completing this action.

Program: {program_name}
Current location: {current_location}
Action needed: {action}

Provide clear, precise instructions:
- Return ONLY the exact button/menu/field names or actions, WRAPPED IN DOUBLE QUOTES ("")
- One action per line
- Use imperative form (Click, Type, Select, etc.)
- Include specific text if needed, all wrapped in double quotes
- Do NOT include explanations, numbers, or step indicators
- Do NOT include bullet points
- EVERY button name or text must be in double quotes ""

Start directly with the first action."""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a UI expert. Return ONLY the exact button/element names or menu items to click in order, WRAPPED IN DOUBLE QUOTES. Be precise. No explanations, no extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=MAX_TOKENS
        )

        text = response.choices[0].message.content.strip()
        steps = [line.strip("- 0123456789.").strip() for line in text.splitlines() if line.strip()]

        # Без скріншоту координати невідомі
        result = []
        for step in steps:
            quoted_texts = extract_quoted_text(step)
            result.append({
                "action": step,
                "quoted_text": quoted_texts,
                "coordinates": None
            })

        return result