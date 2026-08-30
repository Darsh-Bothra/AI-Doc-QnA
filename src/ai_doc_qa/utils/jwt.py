from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ai_doc_qa.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algo,
    )

    return encoded_jwt


def decode_access_token(
    token: Annotated[str, Depends(oauth2_scheme)]
):
    cred_execption = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Can't validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algo],
        )
        return payload

    except InvalidTokenError:
        raise cred_execption
