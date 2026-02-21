from fastapi import APIRouter, Depends, HTTPException, status

from src.application.schemas.auth import TokenRequest, TokenResponse
from src.application.services.auth_service import AuthService
from src.presentation.api.deps import get_auth_service

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/token/", response_model=TokenResponse)
async def issue_token(
    payload: TokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    user = await auth_service.authenticate(email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = auth_service.issue_token(user)
    return TokenResponse(access_token=token)
