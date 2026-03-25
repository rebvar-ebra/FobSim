import sys
import os

# Add api directory to path to import models
sys.path.append(os.path.join(os.getcwd(), 'api'))

import models
from database import SessionLocal, engine
from auth import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(models.User).filter(models.User.email == "admin@fobsim.io").first()
        if admin:
            print("Admin already exists.")
            return

        hashed_password = get_password_hash("password123")
        new_user = models.User(
            email="admin@fobsim.io",
            hashed_password=hashed_password,
            full_name="System Administrator"
        )
        db.add(new_user)
        db.commit()
        print("Admin user created successfully!")
        print("Email: admin@fobsim.io")
        print("Password: password123")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
