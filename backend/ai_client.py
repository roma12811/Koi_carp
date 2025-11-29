#ai_client.py
import base64
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

# Отримання ключа з змінної середовища
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Ініціалізація клієнта
client = OpenAI()

SYSTEM_PROMPT = ""
MAX_TOKENS = 400
MODEL = "gpt-4o-mini"

def image_to_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
# Для локального тесту можна використовувати опис картинки замість Base64
screenshot_description = "A screenshot of wscode"
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
    # prompt = "You are a UI expert. Return the name of programe on screenshot, the current location on screenshot and top 5 possible actions a user can perform in this program. No explanations, no extra text."
    prompt = f"""You are a UI expert and you are given screenshot of some program in Base64 format. 
      Response in format:
        Name: \n"put here name of the program"
        Location: \n"put here the current location of program page that is shown on screenshot. For example: home_page -> settings"
        \n put here the top 5 possible actions put in format: Action: "... \n" 

      stricktly follow brackets in respobse template
      No explanations, no extra text."""

    response = client.responses.create(
        model="gpt-5.1",
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{b64_img}"
                },

                {
                    "type": "input_text",
                    "text": prompt
                },
            ],
        }],
    )

    print(response.output_text)
    print("------------------------------------------")

    return parse_program_message(response.output_text)


def generate_instructions(program_name: str, current_location: str, action: str, screenshot_path: str = None) -> list:
    """
    Генерує конкретні кроки (назви кнопок/елементів) для виконання дії.
    Якщо передано screenshot_path, AI буде аналізувати реальні елементи на екрані.
    """

    if screenshot_path and os.path.exists(screenshot_path):
        b64_img = image_to_base64(screenshot_path)

        prompt = f"""You are a UI expert analyzing a screenshot of {program_name}.

Current location: {current_location}
Required action: {action}

Based on the visible UI elements in the screenshot, provide a step-by-step instruction to complete this action.

IMPORTANT:
- Return ONLY the exact button/menu/field names as they appear in the UI
- One action/click per line
- Be precise and specific - mention exact text on buttons, menu items, or fields
- Include typing instructions if text input is needed (e.g., "Type: 'filename' in the file name field")
- Use imperative form (Click, Type, Select, etc.)
- Do NOT include explanations or numbers
- Do NOT include step numbers or bullet points
- Start directly with the first action

Example format:
Click File menu
Click Save As
Type "document_name" in the filename field
Select PDF format from dropdown
Click Save button"""

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
    else:
        # Fallback без скріншоту
        prompt = f"""You are a UI expert. Generate step-by-step instructions for completing this action.

Program: {program_name}
Current location: {current_location}
Action needed: {action}

Provide clear, precise instructions:
- Return ONLY the exact button/menu/field names or actions
- One action per line
- Use imperative form (Click, Type, Select, etc.)
- Include specific text if needed (e.g., "Type: 'filename'")
- Do NOT include explanations, numbers, or step indicators
- Do NOT include bullet points

Start directly with the first action."""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a UI expert. Return ONLY the exact button/element names or menu items to click in order. Be precise - use the exact names as they appear in the UI. No explanations, no extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=MAX_TOKENS
        )

    text = response.choices[0].message.content.strip()
    # Перетворюємо текст у список кроків (по рядках), видаляючи числа та дефіси в початку
    steps = [line.strip("- 0123456789.").strip() for line in text.splitlines() if line.strip()]
    return steps