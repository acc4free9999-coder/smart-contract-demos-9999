from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.database import get_db
from server.schemas.transaction import LoyaltyEarnRequest, LoyaltyRedeemRequest, TransferRequest
from server.services.loyalty_service import LoyaltyService, get_blockchain_service

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


@router.post("/earn", summary="Award points to a wallet")
def earn_points(payload: LoyaltyEarnRequest, db: Session = Depends(get_db)):
    service = LoyaltyService(db=db, blockchain_service=get_blockchain_service())
    try:
        result = service.earn_points(payload.user_wallet, payload.partner, payload.amount, payload.reference)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return result


@router.post("/redeem", summary="Redeem points from a wallet")
def redeem_points(payload: LoyaltyRedeemRequest, db: Session = Depends(get_db)):
    service = LoyaltyService(db=db, blockchain_service=get_blockchain_service())
    try:
        result = service.redeem_points(payload.user_wallet, payload.partner, payload.amount, payload.reference)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return result


@router.post("/transfer", summary="Transfer points between wallets")
def transfer_points(payload: TransferRequest, db: Session = Depends(get_db)):
    service = LoyaltyService(db=db, blockchain_service=get_blockchain_service())
    try:
        result = service.blockchain_service.transfer(payload.from_wallet, payload.to_wallet, payload.amount, "0x")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.get("/balance/{wallet}", summary="Get token balance from blockchain")
def get_balance(wallet: str, db: Session = Depends(get_db)):
    service = LoyaltyService(db=db, blockchain_service=get_blockchain_service())
    balance = service.get_balance(wallet)
    return {"wallet": wallet, "balance": balance, "token": "ULP"}


@router.get("/transactions/{wallet}", summary="Get loyalty transaction history")
def get_transactions(wallet: str, db: Session = Depends(get_db)):
    service = LoyaltyService(db=db, blockchain_service=get_blockchain_service())
    return service.get_transactions(wallet)
