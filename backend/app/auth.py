import hashlib, hmac, os, re, secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .db import Base, get_db

router = APIRouter(prefix="/api/auth")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TOKEN_DAYS = 7


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, index=True, nullable=False)
    pw_hash = Column(String(255), nullable=False)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)


def _sha(s):
    return hashlib.sha256((s + os.getenv("AUTH_SECRET", "change-me")).encode()).hexdigest()


def hash_password(pw):
    salt = secrets.token_hex(16)
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 200_000).hex()}"


def check_password(pw, stored):
    try:
        salt, h = stored.split("$")
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200_000).hex(), h)
    except Exception:
        return False


def make_token(db, user):
    tok = secrets.token_urlsafe(32)
    db.add(AuthToken(token_hash=_sha(tok), user_id=user.id,
                     expires_at=datetime.utcnow() + timedelta(days=TOKEN_DAYS)))
    db.commit()
    return tok


def current_user(authorization: str = Header(default=""), db=Depends(get_db)):
    tok = authorization.replace("Bearer ", "").strip()
    t = db.query(AuthToken).filter_by(token_hash=_sha(tok)).first() if tok else None
    if not t or t.expires_at < datetime.utcnow():
        raise HTTPException(401, "Please log in.")
    u = db.get(User, t.user_id)
    if not u:
        raise HTTPException(401, "Please log in.")
    return u


def udict(u):
    return {"id": u.id, "name": u.name, "email": u.email}


class SignupIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=100)


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201)
def signup(b: SignupIn, db=Depends(get_db)):
    email = b.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Enter a valid email address.")
    u = db.query(User).filter_by(email=email).first()
    if u and u.verified:
        raise HTTPException(409, "This email is already registered. Please log in.")
    if not u:  # (an unfinished signup from the old OTP flow is simply completed here)
        u = User(email=email)
        db.add(u)
    u.name, u.pw_hash, u.verified = b.name.strip(), hash_password(b.password), True
    db.commit()
    return {"token": make_token(db, u), "user": udict(u)}


@router.post("/login")
def login(b: LoginIn, db=Depends(get_db)):
    email = b.email.strip().lower()
    u = db.query(User).filter_by(email=email).first()
    if not u or not check_password(b.password, u.pw_hash):
        raise HTTPException(401, "Wrong email or password.")
    return {"token": make_token(db, u), "user": udict(u)}


@router.get("/me")
def me(u=Depends(current_user)):
    return udict(u)
