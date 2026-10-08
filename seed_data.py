"""Fill the database with DUMMY students for testing. Run: python seed_data.py"""
from datetime import date

from app.database import Base, SessionLocal, engine
from app.models import Student

DUMMY_STUDENTS = [
    dict(name="Aarav Patel", date_of_birth=date(2004, 3, 15), email="aarav.patel@example.com", phone="+91 90000 00001", course="AI & ML", address="Vadodara", enrollment_date=date(2026, 9, 22)),
    dict(name="Diya Shah", date_of_birth=date(2005, 7, 2), email="diya.shah@example.com", course="AI & ML", enrollment_date=date(2026, 9, 22)),
    dict(name="Rohan Mehta", date_of_birth=date(2006, 1, 20), phone="+91 90000 00003", course="Python with AI", enrollment_date=date(2026, 10, 1)),
    dict(name="Isha Reddy", date_of_birth=date(2003, 11, 9), email="isha.reddy@example.com", course="Data Science", address="Hyderabad"),
    dict(name="Kabir Joshi", date_of_birth=date(2006, 5, 30), email="kabir.joshi@example.com", phone="+91 90000 00005", course="AI & ML", enrollment_date=date(2026, 9, 22)),
]

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Student).count() == 0:
            db.add_all(Student(**s) for s in DUMMY_STUDENTS)
            db.commit()
            print(f"Added {len(DUMMY_STUDENTS)} dummy students.")
        else:
            print("Database already has students; nothing added.")
    finally:
        db.close()
