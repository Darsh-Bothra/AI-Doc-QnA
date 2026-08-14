from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from ai_doc_qa.db.db import get_db
from ai_doc_qa.db.models.user import User
from ai_doc_qa.schemas.user import LoginResponse, UserCreate, UserResponse, UserLogin
from ai_doc_qa.utils import security
from ai_doc_qa.utils.jwt import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication route"]
)

@router.post("/register", response_model=UserResponse)
async def register(
    req: UserCreate, 
    db: AsyncSession=Depends(get_db)
):
    email, password = req.email, req.password
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    exists = result.scalar_one_or_none()

    if exists:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )
    
    hashed_password = security.hash_password(password=password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(id=new_user.id, email=new_user.email, created_at=new_user.created_at)


@router.post("/login")
async def login(
    req: UserLogin, db: 
    AsyncSession=Depends(get_db)
):
    query = select(User).where(User.email == req.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    is_valid = security.verify_password(req.password, user.hashed_password)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token({
        "sub": str(user.id)
    })

    return LoginResponse(
        access_token=token,
        token_type="bearer"
    )


