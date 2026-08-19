"""Quick script to check if users exist in the database."""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()
try:
    users = db.query(User).all()
    if not users:
        print("❌ No users found! You need to run: python seed_data.py")
    else:
        print(f"✅ Found {len(users)} users in database:")
        for u in users[:10]:
            pw_ok = verify_password("password123", u.password_hash)
            print(f"  - {u.username} (entity: {u.entity_id}) | password123 works: {pw_ok}")
finally:
    db.close()
