import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, nullable=True)

    transactions = relationship("Transaction", back_populates="payment_method")
    owner = relationship("User", back_populates="payment_methods")
