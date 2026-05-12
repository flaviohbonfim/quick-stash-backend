import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password

async def create_user(*, session: AsyncSession, user_in: UserCreate) -> User:
    """Criar novo usuário"""
    db_user = User(
        id=str(uuid.uuid4()),
        name=user_in.name,
        email=user_in.email,
        password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        created_at=datetime.utcnow().isoformat(),
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user(*, session: AsyncSession, user_id: str) -> User | None:
    """Buscar usuário por ID"""
    return await session.get(User, user_id)


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """Buscar usuário por e-mail"""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_users(*, session: AsyncSession, limit: int = 100, offset: int = 0) -> list[User]:
    """Listar usuários"""
    from sqlalchemy import desc
    stmt = select(User).offset(offset).limit(limit).order_by(desc(User.id))
    result = await session.scalars(stmt)
    return result.all()


async def update_user(*, session: AsyncSession, user_id: str, user_in: UserUpdate) -> User | None:
    """Atualizar usuário"""
    db_user = await get_user(session=session, user_id=user_id)
    if not db_user:
        return None

    user_data = user_in.model_dump(exclude_unset=True)

    for field, value in user_data.items():
        if value is not None:
            setattr(db_user, field, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def delete_user(*, session: AsyncSession, user_id: str) -> bool:
    """Excluir usuário"""
    db_user = await get_user(session=session, user_id=user_id)
    if not db_user:
        return False
    session.delete(db_user)
    await session.commit()
    return True


async def update_user_refresh_token(*, session: AsyncSession, user_id: str, refresh_token: str) -> User | None:
    """Atualizar refresh token do usuário"""
    db_user = await get_user(session=session, user_id=user_id)
    if not db_user:
        return None
    db_user.refresh_token = refresh_token
    db_user.updated_at = datetime.utcnow().isoformat()
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def change_user_password(*, session: AsyncSession, user: User, old_password: str, new_password: str) -> bool:
    """Alterar senha do usuário"""
    if not verify_password(old_password, user.password):
        return False
    user.password = get_password_hash(new_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return True