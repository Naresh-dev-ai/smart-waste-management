import base64, hashlib, hmac, json, secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.models import User

http_bearer = HTTPBearer()
def _b64(data: bytes) -> str: return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
def _unb64(value: str) -> bytes: return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
def hash_password(password: str) -> str:
    salt=secrets.token_bytes(16); rounds=310000
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,rounds)
    return f"pbkdf2_sha256${rounds}${_b64(salt)}${_b64(digest)}"
def verify_password(plain: str, hashed: str) -> bool:
    try:
        scheme,rounds,salt,digest=hashed.split("$")
        if scheme!="pbkdf2_sha256": return False
        actual=hashlib.pbkdf2_hmac("sha256",plain.encode(),_unb64(salt),int(rounds))
        return hmac.compare_digest(actual,_unb64(digest))
    except Exception: return False
def create_token(subject: str, token_type: str = "access", expires_minutes: int | None = None):
    if expires_minutes is None: expires_minutes = settings.access_token_minutes if token_type == "access" else settings.refresh_token_days * 24 * 60
    header={"alg":"HS256","typ":"JWT"}; payload={"sub":subject,"type":token_type,"exp":int((datetime.now(timezone.utc)+timedelta(minutes=expires_minutes)).timestamp())}
    signing=f"{_b64(json.dumps(header,separators=(',',':')).encode())}.{_b64(json.dumps(payload,separators=(',',':')).encode())}"
    signature=hmac.new(settings.secret_key.encode(),signing.encode(),hashlib.sha256).digest()
    return signing+"."+_b64(signature)
def decode_token(token: str):
    try:
        head,body,sig=token.split("."); signing=f"{head}.{body}"
        expected=hmac.new(settings.secret_key.encode(),signing.encode(),hashlib.sha256).digest()
        if not hmac.compare_digest(expected,_unb64(sig)): raise ValueError()
        payload=json.loads(_unb64(body))
        if int(payload.get("exp",0)) < int(datetime.now(timezone.utc).timestamp()): raise ValueError()
        return payload
    except Exception: raise ValueError("Invalid token")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer), db: Session = Depends(get_db)):
    error=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired authentication token",headers={"WWW-Authenticate":"Bearer"})
    try:
        payload=decode_token(credentials.credentials)
        if payload.get("type")!="access": raise error
        user_id=int(payload.get("sub"))
    except (ValueError,TypeError): raise error
    user=db.get(User,user_id)
    if not user or not user.is_active: raise error
    return user
def require_roles(*roles):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles: raise HTTPException(403,"You do not have permission for this operation")
        return user
    return checker
