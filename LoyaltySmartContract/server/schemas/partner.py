from pydantic import BaseModel


class PartnerRead(BaseModel):
    id: str
    name: str
    wallet_address: str
    status: str
    mint_permission: bool
    burn_permission: bool


class PartnerConfig(BaseModel):
    id: str
    name: str
    earn_rate: int | None = None
    redeem_rate: int | None = None
