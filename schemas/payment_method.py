from pydantic import BaseModel, field_validator


PAYMENT_METHOD_TYPES = ("CREDIT_CARD", "PIX")


class PaymentMethodCreate(BaseModel):
    name: str
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in PAYMENT_METHOD_TYPES:
            raise ValueError(f"Tipo deve ser um de: {', '.join(PAYMENT_METHOD_TYPES)}")
        return v


class PaymentMethodResponse(BaseModel):
    id: str
    name: str
    type: str
    balance: float
    created_at: str

    class Config:
        from_attributes = True


class PaymentMethodUpdate(BaseModel):
    name: str | None = None
