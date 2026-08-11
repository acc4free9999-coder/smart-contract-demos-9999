import json
import os
import time
from pathlib import Path
from typing import List, Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from web3 import Web3

GANACHE_URL = os.environ.get("GANACHE_URL", "http://ganache:8545")
SHARED_DIR = Path(os.environ.get("SHARED_DIR", "/shared"))
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

app = FastAPI(
    title="Event Ticket API",
    description="API quan ly ve su kien dua tren blockchain (NFT ticketing)",
)

w3: Optional[Web3] = None
contract = None
organizer_address = None


def load_contract_data(retries: int = 30, delay: int = 2):
    abi_path = SHARED_DIR / "abi.json"
    addr_path = SHARED_DIR / "address.txt"
    org_path = SHARED_DIR / "organizer.txt"
    for i in range(retries):
        if abi_path.exists() and addr_path.exists() and org_path.exists():
            abi = json.loads(abi_path.read_text())
            address = addr_path.read_text().strip()
            organizer = org_path.read_text().strip()
            return abi, address, organizer
        print(f"Dang cho contract duoc deploy... ({i + 1}/{retries})")
        time.sleep(delay)
    raise RuntimeError("Khong tim thay du lieu contract. Kiem tra lai service 'deploy'.")


@app.on_event("startup")
def startup():
    global w3, contract, organizer_address
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    abi, address, organizer = load_contract_data()
    contract = w3.eth.contract(address=address, abi=abi)
    organizer_address = organizer
    print(f"Server da ket noi contract tai {address}, organizer={organizer}")


class MintRequest(BaseModel):
    to_address: str
    seat_id: int
    price_wei: int


class ResaleRequest(BaseModel):
    from_address: str
    to_address: str
    price_wei: int


class CheckInRequest(BaseModel):
    token_id: int


class SignTermsRequest(BaseModel):
    address: str
    signature: str  # hex string, vi du "0xabc..."


class UpdateTermsRequest(BaseModel):
    text: str


class TicketResponse(BaseModel):
    token_id: int
    seat_id: int
    original_price: int
    checked_in: bool
    owner: str


def _get_ticket(token_id: int) -> TicketResponse:
    try:
        seat_id, original_price, checked_in, owner = contract.functions.getTicket(token_id).call()
    except Exception:
        raise HTTPException(status_code=404, detail="Ve khong ton tai")
    if owner == ZERO_ADDRESS:
        raise HTTPException(status_code=404, detail="Ve khong ton tai")
    return TicketResponse(
        token_id=token_id,
        seat_id=seat_id,
        original_price=original_price,
        checked_in=checked_in,
        owner=owner,
    )


@app.get("/health")
def health():
    return {"status": "ok", "connected": bool(w3 and w3.is_connected())}


@app.get("/event")
def get_event():
    name = contract.functions.eventName().call()
    return {"event_name": name, "contract_address": contract.address, "organizer": organizer_address}


@app.post("/tickets/mint", response_model=TicketResponse)
def mint_ticket(req: MintRequest):
    to_checksum = Web3.to_checksum_address(req.to_address)
    if not contract.functions.hasSignedCurrentTerms(to_checksum).call():
        raise HTTPException(
            status_code=400,
            detail="Nguoi mua chua ky dieu khoan mua ve. Vui long ky truoc khi phat hanh ve.",
        )
    tx_hash = contract.functions.mintTicket(
        to_checksum, req.seat_id, req.price_wei
    ).transact({"from": organizer_address})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    logs = contract.events.TicketMinted().process_receipt(receipt)
    if not logs:
        raise HTTPException(status_code=500, detail="Mint that bai")
    token_id = logs[0]["args"]["tokenId"]
    return _get_ticket(token_id)


@app.get("/tickets/{token_id}", response_model=TicketResponse)
def get_ticket(token_id: int):
    return _get_ticket(token_id)


@app.get("/tickets/owner/{address}", response_model=List[TicketResponse])
def get_tickets_by_owner(address: str):
    token_ids = contract.functions.ticketsOf(Web3.to_checksum_address(address)).call()
    return [_get_ticket(tid) for tid in token_ids]


@app.post("/tickets/checkin", response_model=TicketResponse)
def check_in(req: CheckInRequest):
    ticket = _get_ticket(req.token_id)
    if ticket.checked_in:
        raise HTTPException(status_code=400, detail="Ve da duoc su dung truoc do")
    tx_hash = contract.functions.checkIn(req.token_id).transact({"from": organizer_address})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return _get_ticket(req.token_id)


@app.post("/tickets/{token_id}/resale", response_model=TicketResponse)
def resale_ticket(token_id: int, req: ResaleRequest):
    tx_hash = contract.functions.transferTicket(
        token_id,
        Web3.to_checksum_address(req.from_address),
        Web3.to_checksum_address(req.to_address),
        req.price_wei,
    ).transact({"from": organizer_address})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return _get_ticket(token_id)


@app.get("/accounts")
def list_demo_accounts():
    """Danh sach vi demo tu Ganache - chi dung cho moi truong test/local."""
    accounts_path = SHARED_DIR / "accounts.json"
    if accounts_path.exists():
        return json.loads(accounts_path.read_text())
    return []


@app.get("/terms")
def get_terms():
    text = contract.functions.termsText().call()
    terms_hash = contract.functions.termsHash().call()
    return {"text": text, "hash": Web3.to_hex(terms_hash)}


@app.put("/terms")
def update_terms(req: UpdateTermsRequest):
    """Chi ban to chuc dung: cap nhat noi dung dieu khoan. Luu y: cap nhat dieu khoan
    se tao hash moi, nguoi da ky dieu khoan cu se can ky lai dieu khoan moi."""
    tx_hash = contract.functions.setTerms(req.text).transact({"from": organizer_address})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return get_terms()


@app.get("/terms/status/{address}")
def terms_status(address: str):
    checksum = Web3.to_checksum_address(address)
    signed = contract.functions.hasSignedCurrentTerms(checksum).call()
    return {"address": checksum, "signed": signed}


@app.post("/terms/sign")
def sign_terms(req: SignTermsRequest):
    terms_hash = contract.functions.termsHash().call()
    if terms_hash == b"\x00" * 32:
        raise HTTPException(status_code=400, detail="Chua thiet lap dieu khoan mua ve")

    checksum_address = Web3.to_checksum_address(req.address)

    # Xac minh chu ky truoc, tra loi ro rang cho nguoi dung neu sai, khong can ton phi gas
    # de thu roi moi biet fail.
    message = encode_defunct(primitive=terms_hash)
    try:
        recovered = Account.recover_message(message, signature=req.signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Chu ky khong dung dinh dang")

    if recovered.lower() != checksum_address.lower():
        raise HTTPException(
            status_code=400,
            detail=f"Chu ky khong khop dia chi. Chu ky nay thuc ra thuoc ve {recovered}",
        )

    if contract.functions.signedAt(checksum_address, terms_hash).call() != 0:
        raise HTTPException(status_code=400, detail="Dia chi nay da ky dieu khoan hien hanh roi")

    tx_hash = contract.functions.recordSignature(
        checksum_address, Web3.to_bytes(hexstr=req.signature)
    ).transact({"from": organizer_address})
    w3.eth.wait_for_transaction_receipt(tx_hash)

    return {"address": checksum_address, "signed": True, "terms_hash": Web3.to_hex(terms_hash)}
