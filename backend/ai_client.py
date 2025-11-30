import base64
import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS
from ocr_utils import find_text_on_screen

client = OpenAI(api_key=OPENAI_API_KEY)


def image_to_base64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def parse_program_message(message: str) -> dict:
    name_match = re.search(r'Name:\s*"([^"]+)"', message)
    location_match = re.search(r'Location:\s*"([^"]+)"', message)
    actions_matches = re.findall(r'Action:\s*"([^"]+)"', message)

    return {
        "Name": name_match.group(1) if name_match else None,
        "Location": location_match.group(1) if location_match else None,
        "Actions": actions_matches if actions_matches else []
    }


def define_program(screenshot_path: str) -> dict:
    b64_img = image_to_base64(screenshot_path)

    prompt = """You are a UI expert analyzing a program screenshot in Base64 format.
    Response EXACTLY in this format:
    Name: "program_name"
    Location: "page_path"
    Action: "action_1"
    Action: "action_2"
    Action: "action_3"
    Action: "action_4"
    Action: "action_5"

    No explanations, no extra text."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                },
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=OPENAI_MAX_TOKENS
    )

    response_text = response.choices[0].message.content.strip()
    print(response_text)
    print("--" * 20)

    return parse_program_message(response_text)


def extract_quoted_text(text: str) -> list:
    """Витягує текст в подвійних лапках"""
    return re.findall(r'"([^"]+)"', text)


def generate_instructions(program_name: str, current_location: str,
                          action: str, screenshot_path: str = None) -> list:

    if screenshot_path:
        b64_img = image_to_base64(screenshot_path)

        prompt = f"""You are a UI expert analyzing {program_name}.
        Current location: {current_location}
        Required action: {action}

        Provide step-by-step instructions:
        - ONLY exact button/menu/field names in DOUBLE QUOTES ("")
        - One action per line
        - Imperative form (Click, Type, Select, etc.)
        - NO explanations, numbers, or extra text
        - EVERY button must be in double quotes ""

        Example:
        Click "File" menu
        Click "Save As"
        Type "document_name" in the "filename" field
        Click "Save" button"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                    },
                    {"type": "text", "text": prompt}
                ]
            }],
            max_tokens=OPENAI_MAX_TOKENS
        )

        text = response.choices[0].message.content.strip()
    else:
        prompt = f"""Generate step-by-step instructions for:
        Program: {program_name}
        Location: {current_location}
        Action: {action}

        Format:
        - ONLY exact button names in DOUBLE QUOTES ("")
        - One action per line
        - Imperative form (Click, Type, Select)
        - NO explanations or numbers"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=OPENAI_MAX_TOKENS
        )

        text = response.choices[0].message.content.strip()

    steps = [line.strip("- 0123456789.").strip()
             for line in text.splitlines() if line.strip()]

    result = []
    for step in steps:
        quoted_texts = extract_quoted_text(step)
        coordinates = None

        if screenshot_path and quoted_texts:
            coordinates = find_text_on_screen(screenshot_path, quoted_texts[0])

        result.append({
            "action": step,
            "quoted_text": quoted_texts,
            "coordinates": coordinates
        })

    return result