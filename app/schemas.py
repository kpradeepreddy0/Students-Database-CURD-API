"""Pydantic schemas: request validation and response shapes."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

PHONE_PATTERN = r"^\+?[0-9\- ]{7,15}$"


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Aarav Patel"])
    date_of_birth: date = Field(..., examples=["2005-04-12"])
    email: EmailStr | None = Field(None, examples=["aarav@example.com"])
    phone: str | None = Field(None, pattern=PHONE_PATTERN, examples=["+91 98765 43210"])
    course: str | None = Field(None, max_length=100, examples=["AI & ML"])
    address: str | None = Field(None, max_length=255, examples=["Vadodara, Gujarat"])
    enrollment_date: date | None = Field(None, examples=["2026-09-22"])

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must have at least 2 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return v


class StudentCreate(StudentBase):
    @model_validator(mode="after")
    def need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email or phone")
        return self


class StudentUpdate(BaseModel):
    """All fields optional: used for both PUT and PATCH (only sent fields change)."""
    name: str | None = Field(None, min_length=2, max_length=100)
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, pattern=PHONE_PATTERN)
    course: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=255)
    enrollment_date: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, v: date | None) -> date | None:
        if v is not None and v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return v


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, examples=["How many students are there?"])


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    records_used: int
