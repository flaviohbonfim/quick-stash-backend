from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from api.deps import get_current_user
from crud.payment_method import (
    create_payment_method,
    get_payment_methods,
    delete_payment_method,
)
from schemas.payment_method import PaymentMethodCreate, PaymentMethodResponse
from models.user import User

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.post(
    "",
    response_model=PaymentMethodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo meio de pagamento",
)
async def create(
    data: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pm = await create_payment_method(session=db, user_id=current_user.id, data=data)
    return PaymentMethodResponse(**{k: getattr(pm, k) for k in pm.__dict__ if not k.startswith("_")})


@router.get(
    "",
    response_model=list[PaymentMethodResponse],
    summary="Listar meios de pagamento do usuário",
)
async def list_methods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    methods = await get_payment_methods(session=db, user_id=current_user.id)
    return [PaymentMethodResponse(**{k: getattr(pm, k) for k in pm.__dict__ if not k.startswith("_")}) for pm in methods]


@router.delete(
    "/{pm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover meio de pagamento",
)
async def remove(
    pm_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await delete_payment_method(session=db, pm_id=pm_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Método de pagamento não encontrado")
