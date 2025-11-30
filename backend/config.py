import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не встановлено в .env")

OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1500

TESSERACT_PATH = r"D:\Dev\Tesseract\tesseract.exe"

UI_THEME = {
    "bg_primary": "#14171B",
    "bg_secondary": "#1A1D22",
    "bg_tertiary": "#1C1F22",
    "text_primary": "#F2F5F7",
    "text_secondary": "#E6EBEE",
    "accent": "#FF8926",
    "font_size_small": 8,
    "font_size_normal": 10,
}