from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from server.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String, nullable=False, index=True)
    partner = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    reference = Column(String, nullable=False, unique=True)
    tx_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
