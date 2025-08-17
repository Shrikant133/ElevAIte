from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin, Token, User as UserSchema
import pyotp
import qrcode
from io import BytesIO
import base64

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserSchema)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.create_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return user

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(user_data.email, user_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return token

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    token = await auth_service.refresh_access_token(refresh_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    return token

@router.get("/me", response_model=UserSchema)
async def get_current_user(
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    return current_user

@router.post("/2fa/setup")
async def setup_2fa(
    current_user: UserSchema = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Generate TOTP secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        current_user.email,
        issuer_name="Student CRM"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Save secret to user (temporarily)
    auth_service = AuthService(db)
    await auth_service.save_2fa_secret(current_user.id, secret)
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_code_data}"
    }

@router.post("/2fa/verify")
async def verify_2fa(
    token: str,
    current_user: UserSchema = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    is_valid = await auth_service.verify_2fa_token(current_user.id, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    return {"message": "2FA enabled successfully"}