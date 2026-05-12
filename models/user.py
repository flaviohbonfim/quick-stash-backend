import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    refresh_token = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)

    payment_methods = relationship("PaymentMethod", back_populates="owner")
