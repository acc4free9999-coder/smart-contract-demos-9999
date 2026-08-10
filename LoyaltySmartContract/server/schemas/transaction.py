from pydantic import BaseModel, Field


class LoyaltyEarnRequest(BaseModel):
    user_wallet: str = Field(..., min_length=1)
    partner: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)
    reference: str = Field(..., min_length=1)


class LoyaltyRedeemRequest(BaseModel):
    user_wallet: str = Field(..., min_length=1)
    partner: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)
    reference: str = Field(..., min_length=1)


class TransferRequest(BaseModel):
    from_wallet: str = Field(..., min_length=1)
    to_wallet: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)
