from pydantic import BaseModel


class BalanceResponse(BaseModel):
    total_balance: float
    accounts: list[dict]


class AccountBalanceDetail(BaseModel):
    payment_method_id: str
    payment_method_name: str
    type: str
    balance: float
