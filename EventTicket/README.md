# Event Ticket Blockchain Demo

Ung dung ve su kien dua tren blockchain (NFT ticketing), gom 4 thanh phan chay bang Docker Compose:

| Service | Vai tro | Cong |
|---|---|---|
| `ganache` | Blockchain thu nghiem (local Ethereum node) | 8545 |
| `deploy` | Bien dich + deploy smart contract `EventTicket.sol`, chay 1 lan roi tat | - |
| `server` | REST API (FastAPI) giao tiep voi smart contract qua web3.py | 8000 |
| `client` | Giao dien nguoi dung (Streamlit) - Ban to chuc / Nguoi mua / Nhan vien check-in | 8501 |

## Kien truc

```
client (Streamlit) --HTTP--> server (FastAPI) --web3.py--> ganache (blockchain)
                                                                   ^
                                                    deploy (chay 1 lan luc khoi dong)
```

`deploy` va `server` chia se 1 Docker volume (`contract-data`) de truyen ABI + dia chi contract
sau khi deploy xong. `server` co co che retry, tu cho `deploy` hoan tat.

## Chay thu

```bash
cd event-ticket-blockchain
docker compose up --build
```

Sau khi tat ca service khoi dong (lan dau co the mat 1-2 phut vi phai tai solc compiler):

- API docs: http://localhost:8000/docs
- Giao dien: http://localhost:8501

## Luong su dung thu

1. Mo http://localhost:8501, chon vai tro **Ban to chuc**
2. Xem danh sach vi demo (10 dia chi tao san tu Ganache)
3. Nhap 1 dia chi lam nguoi mua, phat hanh ve (mint) cho ho
4. Chuyen sang vai tro **Nguoi mua**, nhap dia chi vua mint -> xem ve + ma QR
5. Chuyen sang vai tro **Nhan vien check-in**, nhap token ID -> xac nhan check-in
6. Thu check-in lai lan 2 -> se bi tu choi (chong ve gia/dung 2 lan)
7. Thu ban lai ve (resale) voi gia vuot 110% gia goc -> se bi tu choi boi smart contract

## Cac API chinh (server)

| Method | Endpoint | Mo ta |
|---|---|---|
| GET | `/event` | Thong tin su kien + dia chi contract |
| POST | `/tickets/mint` | Phat hanh ve moi |
| GET | `/tickets/{token_id}` | Chi tiet 1 ve |
| GET | `/tickets/owner/{address}` | Danh sach ve cua 1 vi |
| POST | `/tickets/checkin` | Check-in ve tai cong |
| POST | `/tickets/{token_id}/resale` | Chuyen nhuong / ban lai ve |
| GET | `/accounts` | Danh sach vi demo tu Ganache |

## Ghi chu quan trong

- Day la ban demo/hoc tap: `EventTicket.sol` la ban rut gon cua ERC-721 (khong day du ERC165/safeTransfer),
  du de minh hoa logic mint / check-in / gioi han gia ban lai.
- Trong mo hinh nay, **server giu private key cua ban to chuc** va thuc hien giao dich thay nguoi dung
  (giong mo hinh "embedded wallet" - nguoi dung khong can quan ly private key). Day la lua chon UX
  pho bien cho app mobile huong den nguoi dung khong rành crypto.
- Muon dua len production that: thay Ganache bang testnet/mainnet that (Polygon, BNB Chain...),
  dung dich vu quan ly key an toan (AWS KMS, HSM, hoac Web3Auth/Privy cho vi nguoi dung),
  va bo sung xac thuc/KYC cho cac endpoint nhay cam.
- `deploy` service can ket noi internet khi build/chay lan dau de tai solc compiler (qua `py-solc-x`).
