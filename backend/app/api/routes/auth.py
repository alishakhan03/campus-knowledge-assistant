from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import AdminCreateRequest, LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.auth_service import authenticate_user, create_admin_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=201, summary="Register a new student account")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, payload)
    return user


@router.post(
    "/register-admin",
    response_model=UserPublic,
    status_code=201,
    summary="Create a new admin account (admin only)",
)
def register_admin(
    payload: AdminCreateRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = create_admin_user(db, payload)
    return user


@router.post("/login", response_model=TokenResponse, summary="Log in and receive a JWT access token")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = authenticate_user(db, payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic, summary="Get the current logged-in user's profile")
def me(current_user: User = Depends(get_current_user)):
    return current_user









# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from app.core.dependencies import get_current_user
# from app.db.database import get_db
# from app.models.user import User
# from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
# from app.services.auth_service import authenticate_user, register_user

# router = APIRouter(prefix="/api/auth", tags=["auth"])


# @router.post("/register", response_model=UserPublic, status_code=201, summary="Register a new student account")
# def register(payload: RegisterRequest, db: Session = Depends(get_db)):
#     user = register_user(db, payload)
#     return user


# @router.post("/login", response_model=TokenResponse, summary="Log in and receive a JWT access token")
# def login(payload: LoginRequest, db: Session = Depends(get_db)):
#     token = authenticate_user(db, payload)
#     return TokenResponse(access_token=token)


# @router.get("/me", response_model=UserPublic, summary="Get the current logged-in user's profile")
# def me(current_user: User = Depends(get_current_user)):
#     return current_user
