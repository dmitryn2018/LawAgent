from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, set_auth_cookie, clear_auth_cookie
)
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Set cookie
    set_auth_cookie(response, access_token)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear auth cookie."""
    clear_auth_cookie(response)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

