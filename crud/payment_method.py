from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.payment_method import PaymentMethod
from models.transaction import Transaction
from schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


async def create_payment_method(*, session: AsyncSession, user_id: str, data: PaymentMethodCreate) -> PaymentMethod:
    pm = PaymentMethod(name=data.name, type=data.type, user_id=user_id, balance=0.0)
    session.add(pm)
    await session.commit()
    await session.refresh(pm)
    return pm


async def get_payment_method(*, session: AsyncSession, pm_id: str) -> PaymentMethod | None:
    return await session.get(PaymentMethod, pm_id)


async def get_payment_methods(*, session: AsyncSession, user_id: str) -> list[PaymentMethod]:
    stmt = select(PaymentMethod).where(PaymentMethod.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_payment_method(*, session: AsyncSession, pm_id: str, user_id: str) -> bool:
    pm = await session.get(PaymentMethod, pm_id)
    if not pm or pm.user_id != user_id:
        return False
    stmt = select(func.count()).select_from(Transaction).where(Transaction.payment_method_id == pm_id)
    result = await session.execute(stmt)
    if result.scalar() > 0:
        raise HTTPException(status_code=409, detail="Não é possível remover método com transações vinculadas")
    await session.delete(pm)
    await session.commit()
    return True
