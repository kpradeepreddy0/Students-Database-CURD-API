"""Students Database CRUD API — FastAPI + SQLite (EWB Internship Project)."""
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import ai, crud, models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)  # creates students.db and the table on first run

app = FastAPI(
    title="Students Database CRUD API",
    description="Create, read, update and delete student records. "
    "Bonus: ask questions about the data with a local Ollama model.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


def _get_or_404(db: Session, student_id: int) -> models.Student:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")
    return student


def _check_email_free(db: Session, email: str | None, current_id: int | None = None) -> None:
    if email:
        existing = crud.get_student_by_email(db, email)
        if existing and existing.id != current_id:
            raise HTTPException(status_code=409, detail=f"Email {email} is already used by another student")


@app.get("/", include_in_schema=False)
def root(request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return FileResponse(Path(__file__).parent / "static" / "index.html")
    return {"message": "Students CRUD API is running. Open /docs to test it."}


@app.post("/students", response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    _check_email_free(db, payload.email)
    return crud.create_student(db, payload)


@app.get("/students", response_model=list[schemas.StudentOut], tags=["Students"])
def list_students(
    name: str | None = Query(None, description="Part of the name, case-insensitive"),
    course: str | None = Query(None, description="Part of the course name"),
    born_after: date | None = Query(None, description="Only students born after this date (YYYY-MM-DD)"),
    born_before: date | None = Query(None, description="Only students born before this date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.list_students(db, name, course, born_after, born_before, skip, limit)


@app.get("/students/{student_id}", response_model=schemas.StudentOut, tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, student_id)


@app.put("/students/{student_id}", response_model=schemas.StudentOut, tags=["Students"])
@app.patch("/students/{student_id}", response_model=schemas.StudentOut, tags=["Students"])
def update_student(student_id: int, payload: schemas.StudentUpdate, db: Session = Depends(get_db)):
    student = _get_or_404(db, student_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Send at least one field to update")
    for required in ("name", "date_of_birth"):
        if required in changes and changes[required] is None:
            raise HTTPException(status_code=422, detail=f"{required} cannot be empty")
    new_email = changes.get("email", student.email)
    new_phone = changes.get("phone", student.phone)
    if not new_email and not new_phone:
        raise HTTPException(status_code=422, detail="Student must keep at least one contact: email or phone")
    _check_email_free(db, changes.get("email"), current_id=student_id)
    return crud.update_student(db, student, payload)


@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Students"])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    crud.delete_student(db, _get_or_404(db, student_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/ask", response_model=schemas.AskResponse, tags=["AI (optional)"])
def ask_ai(payload: schemas.AskRequest, db: Session = Depends(get_db)):
    """Ask a question in plain English, e.g. "List students born after 2005"."""
    try:
        return ai.ask(db, payload.question)
    except ai.OllamaUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama is not reachable at {ai.OLLAMA_URL}. Start it with 'ollama serve' "
            f"and pull the model with 'ollama pull {ai.OLLAMA_MODEL}'. ({exc})",
        )
