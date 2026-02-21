from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

ALGORITHM = "HS256"


def create_access_token(subject: str, secret_key: str, expires_minutes: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return str(jwt.encode(payload, secret_key, algorithm=ALGORITHM))


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    result: dict[str, Any] = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    return result


__all__ = ["JWTError", "create_access_token", "decode_access_token"]
