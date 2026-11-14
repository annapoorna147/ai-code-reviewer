from fastapi import APIRouter, HTTPException, status

from app.models.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.services.user_database import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    hashed_password = hash_password(request.password)

    user_id = create_user(
        username=request.username.strip(),
        email=request.email,
        password_hash=hashed_password,
    )

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists.",
        )

    return {
        "message": "Account created successfully.",
        "user": {
            "id": user_id,
            "username": request.username.strip(),
            "email": request.email.lower(),
        },
    }


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    user = get_user_by_email(request.email)

    if user is None or not verify_password(
        request.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user["id"])

    return TokenResponse(access_token=token)
