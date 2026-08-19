from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionLocal
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == request.username).first()

        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        token = create_access_token({
            "sub": str(user.id),
            "entity_id": str(user.entity_id),
        })

        return TokenResponse(access_token=token)
    finally:
        db.close()
