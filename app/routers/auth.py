from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
import uuid, re

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Schemas ──────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    full_name: str
    phone: str                  # primary identifier — Pakistani users have phones
    password: str
    org_name: str
    preferred_language: str = "ur"

class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    org_id: str
    dukandaar_mode: bool
    org_name: str = ""

# ── Helpers ──────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:50] + "-" + str(uuid.uuid4())[:8]

# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user + create their organization"""

    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        phone=payload.phone,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        preferred_language=payload.preferred_language,
        is_verified=True,   # TODO: add OTP verification
    )
    db.add(user)
    db.flush()

    org = Organization(
        name=payload.org_name,
        slug=slugify(payload.org_name),
        dukandaar_mode=True,   # all new users start in Dukandaar Mode
    )
    db.add(org)
    db.flush()

    from app.models.user import OrganizationUser, UserRole
    membership = OrganizationUser(
        org_id=org.id,
        user_id=user.id,
        role=UserRole.owner,
        is_default_org=True,
    )
    db.add(membership)

    # Seed default chart of accounts
    from app.models.account import PAKISTAN_DEFAULT_COA, Account, AccountType, NormalBalance, NORMAL_BALANCE_MAP
    code_to_id = {}
    for code, name, name_ur, acc_type, parent_code in PAKISTAN_DEFAULT_COA:
        acc = Account(
            org_id=org.id,
            code=code,
            name=name,
            name_ur=name_ur,
            type=acc_type,
            normal_balance=NORMAL_BALANCE_MAP[acc_type],
            is_system=True,
            parent_id=code_to_id.get(parent_code),
        )
        db.add(acc)
        db.flush()
        code_to_id[code] = acc.id

    db.commit()

    token = create_token({"sub": str(user.id), "org_id": str(org.id)})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        org_id=str(org.id),
        dukandaar_mode=True,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    from app.models.user import OrganizationUser
    membership = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == user.id,
        OrganizationUser.is_default_org == True,
    ).first()

    org_id = str(membership.org_id) if membership else ""
    dukandaar_mode = membership.organization.dukandaar_mode if membership else True

    user.last_login = datetime.utcnow()
    db.commit()

    org_name = membership.organization.name if membership else ""
    token = create_token({"sub": str(user.id), "org_id": org_id})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        org_id=org_id,
        dukandaar_mode=dukandaar_mode,
        org_name=org_name,
    )
