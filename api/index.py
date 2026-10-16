from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import random
import os

app = FastAPI()

CASES_FILE = os.path.join(os.path.dirname(__file__), "cases.json")


def load_cases():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


ALL_CASES = load_cases()


class AnswerPayload(BaseModel):
    case_id: str
    question_index: int
    user_answer: str
    sanity: int


@app.get("/api/new-game")
def new_game():
    case = random.choice(ALL_CASES)
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "dossier": case["dossier"],
        "total_questions": len(case["questions"]),
        "first_question": case["questions"][0]["question"],
        "question_index": 0
    }


@app.post("/api/verify")
def verify_answer(payload: AnswerPayload):
    case = next((c for c in ALL_CASES if c["case_id"] == payload.case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if payload.question_index >= len(case["questions"]):
        raise HTTPException(status_code=400, detail="Invalid question index")

    q_data = case["questions"][payload.question_index]
    user_txt = payload.user_answer.lower()

    # Kiểm tra xem câu trả lời có chứa từ khóa hợp lệ không
    is_correct = any(kw in user_txt for kw in q_data["keywords"])

    # Tỉ lệ Gaslighting tăng dần khi Sanity giảm
    gaslight_chance = max(0.2, (100 - payload.sanity) / 100.0)
    will_gaslight = random.random() < gaslight_chance

    if is_correct:
        if will_gaslight:
            return {
                "status": "GASLIGHT",
                "output": f"SYSTEM: [VERIFIED_WITH_DOUBT]\n{q_data['gaslight_bluff']}",
                "sanity_change": -5,
                "correct": True
            }
        else:
            return {
                "status": "TRUTH",
                "output": f"SYSTEM: [DATA_RESTORED]\n{q_data['truth_response']}",
                "sanity_change": +10,
                "correct": True
            }
    else:
        return {
            "status": "WRONG",
            "output": f"SYSTEM: [MEMORY_CORRUPTED]\n{q_data['wrong_response']}",
            "sanity_change": -20,
            "correct": False
        }