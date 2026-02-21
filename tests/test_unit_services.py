"""Unit tests for application-layer services and security utilities."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("SUPERUSER_EMAIL", "admin@example.com")
os.environ.setdefault("SUPERUSER_PASSWORD", "admin12345")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402

from src.application.security.jwt import (  # noqa: E402
    JWTError,
    create_access_token,
    decode_access_token,
)
from src.application.security.password import hash_password, verify_password  # noqa: E402


def test_hash_and_verify() -> None:
    with patch("src.application.security.password.pwd_context") as mock_ctx:
        mock_ctx.hash.return_value = "$2b$12$fakehash"
        mock_ctx.verify.return_value = True
        hashed = hash_password("my-secret-pass")
        assert hashed == "$2b$12$fakehash"
        assert verify_password("my-secret-pass", hashed)
        mock_ctx.hash.assert_called_once_with("my-secret-pass")
        mock_ctx.verify.assert_called_once_with("my-secret-pass", "$2b$12$fakehash")


def test_verify_wrong_password() -> None:
    with patch("src.application.security.password.pwd_context") as mock_ctx:
        mock_ctx.verify.return_value = False
        assert not verify_password("wrong", "$2b$12$somehash")
        mock_ctx.verify.assert_called_once_with("wrong", "$2b$12$somehash")


def test_hash_and_verify_long_password() -> None:
    long_password = "very-long-password-" * 10
    hashed = hash_password(long_password)
    assert hashed
    assert verify_password(long_password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_create_and_decode_token() -> None:
    token = create_access_token(subject="user-123", secret_key="s3cret", expires_minutes=30)
    payload = decode_access_token(token, secret_key="s3cret")
    assert payload["sub"] == "user-123"
    assert "exp" in payload


def test_decode_token_wrong_key() -> None:
    token = create_access_token(subject="user-1", secret_key="key-a", expires_minutes=30)
    with pytest.raises(JWTError):
        decode_access_token(token, secret_key="key-b")


def test_decode_token_invalid_string() -> None:
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.jwt", secret_key="any")


from src.domain.exceptions import (  # noqa: E402
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


def test_exception_hierarchy() -> None:
    assert issubclass(NotFoundError, DomainError)
    assert issubclass(PermissionDeniedError, DomainError)
    assert issubclass(ValidationError, DomainError)


def test_exception_message() -> None:
    err = NotFoundError("item missing")
    assert str(err) == "item missing"
