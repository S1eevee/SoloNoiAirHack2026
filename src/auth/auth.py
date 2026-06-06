"""Authentication module for employee account management."""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24  # 30 days
DB_PATH = "auth.db"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class User(BaseModel):
    employee_id: str
    name: str
    email: str
    role: str  # "supervisor", "employee", "admin"

class UserInDB(User):
    hashed_password: str

class TokenData(BaseModel):
    employee_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    employee_id: str
    name: str

# Database initialization
def init_auth_db():
    """Create users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (employee_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  hashed_password TEXT NOT NULL,
                  role TEXT DEFAULT 'employee',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  fcm_token TEXT)''')
    conn.commit()
    conn.close()

# Password utilities
def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

# JWT utilities
def create_access_token(employee_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": employee_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token. Returns employee_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employee_id: str = payload.get("sub")
        if employee_id is None:
            return None
        return employee_id
    except JWTError:
        return None

# User management
def register_user(employee_id: str, name: str, email: str, password: str, role: str = "employee") -> bool:
    """Register a new user."""
    init_auth_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        hashed_pw = hash_password(password)
        c.execute('''INSERT INTO users 
                     (employee_id, name, email, hashed_password, role)
                     VALUES (?, ?, ?, ?, ?)''',
                  (employee_id, name, email, hashed_pw, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user by email and password."""
    init_auth_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT employee_id, name, email, hashed_password, role
                 FROM users WHERE email = ?''', (email,))
    row = c.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    employee_id, name, email_db, hashed_password, role = row
    if not verify_password(password, hashed_password):
        return None
    
    return UserInDB(employee_id=employee_id, name=name, email=email_db, 
                   hashed_password=hashed_password, role=role)

def get_user_by_id(employee_id: str) -> Optional[User]:
    """Get user by employee ID."""
    init_auth_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT employee_id, name, email, role FROM users WHERE employee_id = ?''', 
             (employee_id,))
    row = c.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    employee_id, name, email, role = row
    return User(employee_id=employee_id, name=name, email=email, role=role)

def save_fcm_token(employee_id: str, fcm_token: str) -> bool:
    """Save Firebase Cloud Messaging token for push notifications."""
    init_auth_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''UPDATE users SET fcm_token = ? WHERE employee_id = ?''',
                  (fcm_token, employee_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_all_fcm_tokens() -> list:
    """Get all FCM tokens for push notifications."""
    init_auth_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT employee_id, name, fcm_token FROM users WHERE fcm_token IS NOT NULL''')
    rows = c.fetchall()
    conn.close()
    return [{"employee_id": r[0], "name": r[1], "fcm_token": r[2]} for r in rows]

# Initialize on import
init_auth_db()
