from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from api.deps import get_current_user
from crud.transaction import (
    create_transaction,
    get_transactions,
    update_transaction,
    delete_transaction,
    get_user_balance,
)
from schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionFilters,
)
from schemas.account import BalanceResponse
from models.user import User

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nova transação",
)
async def create(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = await create_transaction(session=db, data=data, user_id=current_user.id)
    return TransactionResponse(**{k: getattr(tx, k) for k in tx.__dict__ if not k.startswith("_")})


@router.get(
    "",
    response_model=list[TransactionResponse],
    summary="Listar transações com filtros",
)
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type: str | None = Query(None),
    payment_method_id: str | None = Query(None),
    category: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    filters = TransactionFilters(
        type=type,
        payment_method_id=payment_method_id,
        category=category,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    transactions = await get_transactions(session=db, user_id=current_user.id, filters=filters)
    return [TransactionResponse(**{k: getattr(tx, k) for k in tx.__dict__ if not k.startswith("_")}) for tx in transactions]


@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="Saldo consolidado de todas as contas PIX",
)
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    balance_data = await get_user_balance(session=db, user_id=current_user.id)
    return BalanceResponse(**balance_data)


@router.patch(
    "/{tx_id}",
    response_model=TransactionResponse,
    summary="Editar transação (recalcula saldo)",
)
async def update(
    tx_id: str,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = await update_transaction(session=db, tx_id=tx_id, data=data, user_id=current_user.id)
    return TransactionResponse(**{k: getattr(tx, k) for k in tx.__dict__ if not k.startswith("_")})


@router.delete(
    "/{tx_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir transação (estorna saldo)",
)
async def remove(
    tx_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await delete_transaction(session=db, tx_id=tx_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Transação não encontrada")
