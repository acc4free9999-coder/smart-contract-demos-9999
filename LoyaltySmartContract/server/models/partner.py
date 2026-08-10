from sqlalchemy import Column, String

from server.database import Base


class Partner(Base):
    __tablename__ = "partners"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    wallet_address = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    mint_permission = Column(String, nullable=False, default="true")
    burn_permission = Column(String, nullable=False, default="true")
