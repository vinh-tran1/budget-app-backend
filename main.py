import os
import jwt
import psycopg2
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# --- 1. Configuration: Reads secrets from your .env file ---
class Settings(BaseSettings):
    database_url: str
    supabase_jwt_secret: str
    class Config:
        env_file = ".env"

settings = Settings()
app = FastAPI()

# --- 2. Database Connection ---
def get_db_connection():
    try:
        conn = psycopg2.connect(dsn=settings.database_url)
        yield conn # 'yield' makes this usable with FastAPI's dependency injection
    finally:
        conn.close()

# --- 3. Authentication: Verifies the user token from the Swift app ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # We don't use tokenUrl, but it's required

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token")
        return user_id
    except (jwt.PyJWTError, Exception):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

# --- 4. API Endpoints ---

# A simple "health check" to see if the server is online
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running!"}

# A placeholder for a real endpoint that requires authentication
@app.get("/api/v1/secure-test")
def get_secure_data(user_id: str = Depends(get_current_user_id)):
    # This endpoint is now protected. It will only work if a valid token is provided.
    # The user_id is safely extracted from the token.
    return {"message": "You have accessed a secure endpoint!", "your_user_id": user_id}
