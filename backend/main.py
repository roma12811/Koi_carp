from fastapi import FastAPI
from fastapi.responses import JSONResponse
from ai_client import define_program, generate_instructions
from pydantic import BaseModel
import base64
import os

app = FastAPI()

# Кеш для скріншотів та результатів
screenshot_cache = {}


class ScreenshotRequest(BaseModel):
    screenshot_base64: str


class ActionRequest(BaseModel):
    action_id: str


@app.post("/api/actions")
async def get_actions(req: ScreenshotRequest):
    """
    Отримує скріншот та повертає топ 5 можливих дій
    """
    # Декодуємо base64 в тимчасовий файл
    screenshot_data = base64.b64decode(req.screenshot_base64)
    temp_path = "temp_screenshot.png"

    with open(temp_path, "wb") as f:
        f.write(screenshot_data)

    try:
        # Аналізуємо скріншот за допомогою AI
        program_info = define_program(temp_path)

        # Кешуємо результат з шляхом до скріншоту
        cache_key = req.screenshot_base64[:50]  # Використовуємо частину base64 як ключ
        screenshot_cache[cache_key] = {
            "program_name": program_info["Name"],
            "current_location": program_info["Location"],
            "actions": program_info["Actions"],
            "screenshot_path": temp_path
        }

        # Форматуємо відповідь згідно API
        actions = []
        for idx, action_name in enumerate(program_info["Actions"], 1):
            actions.append({
                "id": f"action_{idx}",
                "name": action_name
            })

        return JSONResponse({
            "actions": actions
        })

    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


@app.post("/api/get-steps")
async def get_steps(req: ActionRequest):
    """
    Отримує action_id та повертає кроки для виконання дії
    """
    # Відновлюємо інформацію з кешу (останній скріншот)
    if not screenshot_cache:
        return JSONResponse({
            "error": "No screenshot cached. Please call /api/actions first."
        }, status_code=400)

    # Беремо останній закешований скріншот
    last_cache_key = list(screenshot_cache.keys())[-1]
    cached_info = screenshot_cache[last_cache_key]

    program_name = cached_info["program_name"]
    current_location = cached_info["current_location"]
    screenshot_path = cached_info["screenshot_path"]

    try:
        # Отримуємо индекс дії
        action_idx = int(req.action_id.split("_")[1]) - 1

        # Перевіряємо, що індекс в межах списку дій
        if action_idx < 0 or action_idx >= len(cached_info["actions"]):
            return JSONResponse({
                "error": "Invalid action_id"
            }, status_code=400)

        action_name = cached_info["actions"][action_idx]

        # Генеруємо інструкції передаючи скріншот для точнішого аналізу
        steps_text = generate_instructions(
            program_name=program_name,
            current_location=current_location,
            action=action_name,
            screenshot_path=screenshot_path
        )

        # Форматуємо кроки згідно API
        steps = []
        for step_num, instruction in enumerate(steps_text, 1):
            steps.append({
                "step_number": step_num,
                "instruction": instruction,
                "grid_position": 1
            })

        return JSONResponse({
            "action_name": action_name,
            "steps": steps
        })

    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


@app.on_event("shutdown")
async def cleanup():
    """
    Видаляємо тимчасові файли при завершенні додатку
    """
    temp_path = "temp_screenshot.png"
    if os.path.exists(temp_path):
        os.remove(temp_path)


@app.get("/health")
async def health():
    """
    Перевірка здоров'я API
    """
    return {"status": "ok"}