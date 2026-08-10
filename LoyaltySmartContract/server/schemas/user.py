from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    wallet_address: str = Field(..., min_length=1)


class UserRead(BaseModel):
    id: str
    name: str
    wallet_address: str
