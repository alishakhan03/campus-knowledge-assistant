"""
Development-only seed script.

Usage:
    python seed.py

Creates one ADMIN and one STUDENT account for local testing.
DO NOT use these credentials in any deployed environment.
"""
import getpass

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.db import base  # noqa: F401  (registers all models before we touch User directly)
from app.models.user import User, UserRole


def upsert_user(db, name: str, email: str, password: str, role: UserRole) -> None:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"  - {email} already exists, skipping")
        return
    user = User(name=name, email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    print(f"  - created {role.value.lower()} {email}")


def main():
    print("Campus Knowledge Assistant - development seed")
    print("These are DEVELOPMENT-ONLY accounts. Set your own passwords below.\n")

    admin_password = getpass.getpass("Set a development password for admin@example.com: ") or "ChangeMe123!"
    student_password = getpass.getpass("Set a development password for student@example.com: ") or "ChangeMe123!"

    db = SessionLocal()
    try:
        upsert_user(db, "Dev Admin", "admin@example.com", admin_password, UserRole.ADMIN)
        upsert_user(db, "Dev Student", "student@example.com", student_password, UserRole.STUDENT)
        db.commit()
        print("\nSeed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
