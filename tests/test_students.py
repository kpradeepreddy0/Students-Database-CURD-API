"""Automated tests. Run: pytest -v"""
import os
from unittest.mock import Mock

os.environ["DATABASE_URL"] = "sqlite:///./test_students.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

NEW = {"name": "Test Student", "date_of_birth": "2005-06-01", "email": "test@example.com", "course": "AI & ML"}


def test_full_crud_flow():
    r = client.post("/students", json=NEW)
    assert r.status_code == 201
    sid = r.json()["id"]

    assert client.get(f"/students/{sid}").json()["name"] == "Test Student"
    assert len(client.get("/students").json()) >= 1
    assert len(client.get("/students", params={"born_after": "2005-01-01"}).json()) >= 1
    assert client.get("/students", params={"name": "nobody"}).json() == []

    r = client.patch(f"/students/{sid}", json={"course": "Data Science"})
    assert r.status_code == 200 and r.json()["course"] == "Data Science"
    r = client.put(f"/students/{sid}", json={"phone": "+91 99999 11111"})
    assert r.status_code == 200 and r.json()["phone"] == "+91 99999 11111"

    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404


def test_dashboard_and_assets_are_served():
    dashboard = client.get("/", headers={"accept": "text/html"})
    assert dashboard.status_code == 200
    assert "text/html" in dashboard.headers["content-type"]
    assert "Student directory" in dashboard.text
    assert "Ask the directory" in dashboard.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/").json() == {
        "message": "Students CRUD API is running. Open /docs to test it."
    }


def test_ask_endpoint_uses_ai_service(monkeypatch):
    from app import ai

    monkeypatch.setattr(ai, "ask", lambda db, question: {
        "question": question,
        "answer": "There are 3 students.",
        "model": "llama3.2:1b",
        "records_used": 3,
    })

    response = client.post("/ask", json={"question": "How many students?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "There are 3 students."
    assert response.json()["model"] == "llama3.2:1b"


def test_ask_prompt_uses_authoritative_student_count(monkeypatch):
    from app import ai

    captured_prompt = {}
    response = Mock()
    response.json.return_value = {"response": "There are 2 students."}
    monkeypatch.setattr(ai, "_build_context", lambda db: ("FACTS:\n{}", 2))

    def capture_request(url, *, json, timeout):
        captured_prompt["text"] = json["prompt"]
        return response

    monkeypatch.setattr(ai.httpx, "post", capture_request)
    ai.ask(None, "total how many students in all records")

    assert "AUTHORITATIVE TOTAL STUDENT COUNT: 2." in captured_prompt["text"]
    assert "answer directly with this exact count" in captured_prompt["text"]


def test_validation_errors():
    assert client.post("/students", json={"name": "No Contact", "date_of_birth": "2005-01-01"}).status_code == 422
    assert client.post("/students", json={**NEW, "email": "bad-email"}).status_code == 422
    assert client.post("/students", json={**NEW, "date_of_birth": "2999-01-01"}).status_code == 422
    assert client.post("/students", json={**NEW, "name": "A"}).status_code == 422


def test_duplicate_email_and_missing_records():
    client.post("/students", json={**NEW, "email": "dup@example.com"})
    assert client.post("/students", json={**NEW, "email": "dup@example.com"}).status_code == 409
    assert client.get("/students/99999").status_code == 404
    assert client.patch("/students/99999", json={"name": "X Y"}).status_code == 404
    assert client.delete("/students/99999").status_code == 404
