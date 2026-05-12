from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from api.deps import get_current_user
from crud.user import create_user, get_user, get_user_by_email, get_users, update_user, delete_user
from schemas.user import UserCreate, UserUpdate, UserResponse
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
)
async def create_user_router(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await create_user(session=db, user_in=user_in)
    return UserResponse(**user.__dict__.copy())


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar todos os usuários",
)
async def read_users(
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    users = await get_users(session=db, limit=limit, offset=offset)
    return [UserResponse(**user.__dict__.copy()) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Buscar usuário por ID",
)
async def read_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await get_user(session=db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return UserResponse(**user.__dict__.copy())


@router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Buscar usuário por e-mail",
)
async def read_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await get_user_by_email(session=db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return UserResponse(**user.__dict__.copy())


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Atualizar usuário",
)
async def update_user_router(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_user = await update_user(session=db, user_id=user_id, user_in=user_in)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return UserResponse(**db_user.__dict__.copy())


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário",
)
async def delete_user_router(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await delete_user(session=db, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return None


@router.post(
    "/check-email",
    status_code=status.HTTP_409_CONFLICT,
    summary="Verificar duplicidade de e-mail",
)
async def check_email_exists(
    email: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint auxiliar para verificar se o email já existe"""
    user = await get_user_by_email(session=db, email=email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O e-mail {email} já está cadastrado",
        )
    return None
