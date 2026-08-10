from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.database import get_db
from server.services.loyalty_service import LoyaltyService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", summary="List settlement activity")
def list_settlement(db: Session = Depends(get_db)):
    service = LoyaltyService(db=db)
    return service.get_settlement()
