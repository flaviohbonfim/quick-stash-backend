import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)
    category = Column(String, nullable=True)
    payment_method_id = Column(String, ForeignKey("payment_methods.id"), nullable=False, index=True)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())

    payment_method = relationship("PaymentMethod", back_populates="transactions")
