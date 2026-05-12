from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.transaction import Transaction
from models.payment_method import PaymentMethod
from schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilters


async def create_transaction(*, session: AsyncSession, data: TransactionCreate, user_id: str) -> Transaction:
    stmt = select(PaymentMethod).where(PaymentMethod.id == data.payment_method_id)
    result = await session.execute(stmt)
    pm = result.scalar_one_or_none()

    if not pm:
        raise HTTPException(status_code=404, detail="Método de pagamento não encontrado")
    if pm.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado a este método de pagamento")

    tx = Transaction(
        amount=data.amount,
        date=data.date,
        description=data.description,
        type=data.type,
        category=data.category,
        payment_method_id=data.payment_method_id,
    )
    session.add(tx)

    if pm.type == "PIX":
        if data.type == "INCOME":
            pm.balance += data.amount
        elif data.type == "EXPENSE":
            pm.balance -= data.amount

    await session.commit()
    await session.refresh(tx)
    return tx


async def get_transactions(*, session: AsyncSession, user_id: str, filters: TransactionFilters) -> list[Transaction]:
    stmt = select(Transaction).join(PaymentMethod).where(PaymentMethod.user_id == user_id)

    if filters.type:
        stmt = stmt.where(Transaction.type == filters.type)
    if filters.payment_method_id:
        stmt = stmt.where(Transaction.payment_method_id == filters.payment_method_id)
    if filters.category:
        stmt = stmt.where(Transaction.category == filters.category)
    if filters.start_date:
        stmt = stmt.where(Transaction.date >= filters.start_date)
    if filters.end_date:
        stmt = stmt.where(Transaction.date <= filters.end_date)

    stmt = stmt.offset(filters.offset).limit(filters.limit).order_by(Transaction.date.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_transaction(*, session: AsyncSession, tx_id: str, user_id: str) -> Transaction | None:
    stmt = select(Transaction).join(PaymentMethod).where(
        Transaction.id == tx_id, PaymentMethod.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_transaction(*, session: AsyncSession, tx_id: str, data: TransactionUpdate, user_id: str) -> Transaction:
    existing = await get_transaction(session=session, tx_id=tx_id, user_id=user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    stmt = select(PaymentMethod).where(PaymentMethod.id == existing.payment_method_id)
    result = await session.execute(stmt)
    old_pm = result.scalar_one_or_none()

    new_pm_id = data.payment_method_id or existing.payment_method_id
    if new_pm_id != existing.payment_method_id:
        stmt = select(PaymentMethod).where(PaymentMethod.id == new_pm_id)
        result = await session.execute(stmt)
        new_pm = result.scalar_one_or_none()
        if not new_pm or new_pm.user_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado ao novo método de pagamento")
    else:
        new_pm = old_pm

    if old_pm and old_pm.type == "PIX":
        if existing.type == "INCOME":
            old_pm.balance -= existing.amount
        elif existing.type == "EXPENSE":
            old_pm.balance += existing.amount

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing, field, value)

    if new_pm and new_pm.type == "PIX":
        if existing.type == "INCOME":
            new_pm.balance += existing.amount
        elif existing.type == "EXPENSE":
            new_pm.balance -= existing.amount

    await session.commit()
    await session.refresh(existing)
    return existing


async def delete_transaction(*, session: AsyncSession, tx_id: str, user_id: str) -> bool:
    tx = await get_transaction(session=session, tx_id=tx_id, user_id=user_id)
    if not tx:
        return False

    stmt = select(PaymentMethod).where(PaymentMethod.id == tx.payment_method_id)
    result = await session.execute(stmt)
    pm = result.scalar_one_or_none()

    if pm and pm.type == "PIX":
        if tx.type == "INCOME":
            pm.balance -= tx.amount
        elif tx.type == "EXPENSE":
            pm.balance += tx.amount

    await session.delete(tx)
    await session.commit()
    return True


async def get_user_balance(*, session: AsyncSession, user_id: str) -> dict:
    stmt = select(PaymentMethod).where(PaymentMethod.user_id == user_id, PaymentMethod.type == "PIX")
    result = await session.execute(stmt)
    pix_methods = result.scalars().all()

    total = sum(pm.balance for pm in pix_methods)
    accounts = [
        {"id": pm.id, "name": pm.name, "type": pm.type, "balance": pm.balance}
        for pm in pix_methods
    ]
    return {"total_balance": total, "accounts": accounts}
