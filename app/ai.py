"""OPTIONAL BONUS: answer natural-language questions about students with a local Ollama model.

Safety design: the model never touches the database or writes SQL. Our backend code
fetches the records with normal SQLAlchemy queries and passes them to the model as
read-only context; the model only reads that context and writes an answer.
"""
import json
import os
from datetime import date

import httpx
from sqlalchemy.orm import Session

from app import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_RECORDS = 200


class OllamaUnavailable(Exception):
    pass


def _build_context(db: Session) -> tuple[str, int]:
    students = crud.list_students(db, limit=MAX_RECORDS)
    records = [
        {
            "id": s.id,
            "name": s.name,
            "date_of_birth": s.date_of_birth.isoformat(),
            "birth_year": s.date_of_birth.year,
            "course": s.course,
            "enrollment_date": s.enrollment_date.isoformat() if s.enrollment_date else None,
        }
        for s in students
    ]
    # Pre-computed facts help small models answer counting questions accurately
    facts = {
        "today": date.today().isoformat(),
        "total_students": len(records),
        "students_per_course": {},
    }
    for r in records:
        key = r["course"] or "Not set"
        facts["students_per_course"][key] = facts["students_per_course"].get(key, 0) + 1
    context = "FACTS:\n" + json.dumps(facts, indent=1) + "\n\nSTUDENT RECORDS:\n" + json.dumps(records, indent=1)
    return context, len(records)


def ask(db: Session, question: str) -> dict:
    context, count = _build_context(db)
    prompt = (
        "You are a helpful assistant for a student database. Answer using only the facts below. "
        f"AUTHORITATIVE TOTAL STUDENT COUNT: {count}. "
        "For any question asking how many students there are or for the total number of students, "
        "answer directly with this exact count. Do not calculate it from courses or records. "
        "Never write code. Say you don't know only when the requested fact is missing. "
        "Be short and clear, and list names when asked.\n\n"
        f"{context}\n\nQUESTION: {question}\nANSWER:"
    )
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
            timeout=120,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaUnavailable(str(exc)) from exc
    return {
        "question": question,
        "answer": resp.json().get("response", "").strip(),
        "model": OLLAMA_MODEL,
        "records_used": count,
    }
