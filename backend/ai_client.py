import os
from openai import OpenAI

# Отримання ключа з змінної середовища
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Ініціалізація клієнта
client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = ""
MAX_TOKENS = 400
MODEL = "gpt-4o-mini"

# Для локального тесту можна використовувати опис картинки замість Base64
screenshot_description = "A screenshot of wscode"

def define_program():
    prompt = "You are a UI expert. Return the name of programe on screenshot, the current location on screenshot and top 5 possible actions a user can perform in this program. No explanations, no extra text."

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
            ],
        }],
    )
    return response

def generate_instructions(program_name: str, current_location: str, action: str) -> list:
    messages = [
        {
            "role": "system",
            "content": "You are a UI expert. Return ONLY the exact button/element names or menu items to click in order. Return one item per line. Be precise - use the exact names as they appear in the UI. No explanations, no extra text."
        },
        {
            "role": "user",
            "content": f"Program: {program_name}\nCurrent location: {current_location}\nAction needed: {action}\n\nReturn only the exact UI elements/buttons to click, one per line."
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS
    )

    text = response.choices[0].message.content.strip()
    # Перетворюємо текст у список кроків (по рядках)
    steps = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    return steps
