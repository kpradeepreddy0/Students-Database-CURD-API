"""Database operations (Create, Read, Update, Delete)."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


def create_student(db: Session, data: schemas.StudentCreate) -> models.Student:
    student = models.Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student(db: Session, student_id: int) -> models.Student | None:
    return db.get(models.Student, student_id)


def get_student_by_email(db: Session, email: str) -> models.Student | None:
    return db.scalar(select(models.Student).where(models.Student.email == email))


def list_students(
    db: Session,
    name: str | None = None,
    course: str | None = None,
    born_after: date | None = None,
    born_before: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Student]:
    query = select(models.Student)
    if name:
        query = query.where(models.Student.name.ilike(f"%{name}%"))
    if course:
        query = query.where(models.Student.course.ilike(f"%{course}%"))
    if born_after:
        query = query.where(models.Student.date_of_birth > born_after)
    if born_before:
        query = query.where(models.Student.date_of_birth < born_before)
    query = query.order_by(models.Student.id).offset(skip).limit(limit)
    return list(db.scalars(query))


def update_student(db: Session, student: models.Student, data: schemas.StudentUpdate) -> models.Student:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: models.Student) -> None:
    db.delete(student)
    db.commit()
