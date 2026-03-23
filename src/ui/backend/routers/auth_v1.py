import hashlib
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import deps

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class AuthData(BaseModel):
    email: str
    password: str

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

@router.post("/signup")
async def signup(data: AuthData):
    if deps.profile_user_info_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
        
    email = data.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    existing = deps.profile_user_info_col.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Account with this email already exists")
        
    # Generate unique user_id
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(data.password)
    
    new_user = {
        "id": user_id,
        "email": email,
        "password": hashed_pwd,
        "name": email.split("@")[0] # Default name
    }
    
    deps.profile_user_info_col.insert_one(new_user)
    
    return {"message": "Signup successful", "user_id": user_id, "name": new_user["name"]}

@router.post("/login")
async def login(data: AuthData):
    if deps.profile_user_info_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
        
    email = data.email.strip().lower()
    hashed_pwd = hash_password(data.password)
    
    user = deps.profile_user_info_col.find_one({
        "email": email,
        "password": hashed_pwd
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return {"message": "Login successful", "user_id": user["id"], "name": user.get("name", email.split("@")[0])}
