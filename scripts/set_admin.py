import sys
from app.database import SessionLocal
from app.models import User


def main(email: str) -> int:
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            print(f"No user found: {email}")
            return 1
        u.role = "admin"
        db.add(u)
        db.commit()
        print(f"Role set: {email} -> {u.role}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
    sys.exit(main(email))