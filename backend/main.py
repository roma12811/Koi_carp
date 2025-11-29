#main.py
from fastapi import FastAPI
from ai_client import generate_instructions
from pydantic import BaseModel

app = FastAPI()

class ActionRequest(BaseModel):
    program_name: str
    current_location: str
    action: str

@app.post("/instructions")
async def instructions(req: ActionRequest):
    steps = generate_instructions(
        program_name=req.program_name,
        current_location=req.current_location,
        action=req.action
    )
    return {"instructions": steps}
