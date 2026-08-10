from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.user import User
from server.schemas.user import UserCreate, UserRead
from server.services.loyalty_service import LoyaltyService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, summary="Create a new user")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = LoyaltyService(db=db)
    return service.create_user(payload.name, payload.wallet_address)


@router.get("", response_model=list[UserRead], summary="List users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": user.id, "name": user.name, "wallet_address": user.wallet_address} for user in users]
