from pydantic import BaseModel, field_validator


TRANSACTION_TYPES = ("INCOME", "EXPENSE")


class TransactionCreate(BaseModel):
    amount: float
    date: str
    description: str | None = None
    type: str
    category: str | None = None
    payment_method_id: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Valor deve ser positivo")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in TRANSACTION_TYPES:
            raise ValueError(f"Tipo deve ser um de: {', '.join(TRANSACTION_TYPES)}")
        return v


class TransactionUpdate(BaseModel):
    amount: float | None = None
    date: str | None = None
    description: str | None = None
    type: str | None = None
    category: str | None = None
    payment_method_id: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Valor deve ser positivo")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in TRANSACTION_TYPES:
            raise ValueError(f"Tipo deve ser um de: {', '.join(TRANSACTION_TYPES)}")
        return v


class TransactionResponse(BaseModel):
    id: str
    amount: float
    date: str
    description: str | None
    type: str
    category: str | None
    payment_method_id: str
    created_at: str

    class Config:
        from_attributes = True


class TransactionFilters(BaseModel):
    type: str | None = None
    payment_method_id: str | None = None
    category: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int = 100
    offset: int = 0
