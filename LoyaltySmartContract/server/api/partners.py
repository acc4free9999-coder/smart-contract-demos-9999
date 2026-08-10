from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.database import get_db
from server.schemas.partner import PartnerRead
from server.services.loyalty_service import LoyaltyService

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=list[PartnerRead], summary="List partner configuration")
def list_partners(db: Session = Depends(get_db)):
    service = LoyaltyService(db=db)
    return service.get_partners()
