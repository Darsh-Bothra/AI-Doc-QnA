from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from ai_doc_qa.db import get_db
from ai_doc_qa.db.models import User
from ai_doc_qa.utils import decode_access_token

protected = APIRouter(prefix="/protected", tags=["Protected"])


async def get_current_user(
    payload=Depends(decode_access_token), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    query = select(User).where(User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    return user


@protected.get("/")
async def get_users(current_user: User = Depends(get_current_user)):
    return current_user
