import io
import os
import re
from decimal import Decimal

import cv2
import numpy as np
import qrcode
import requests
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000")
WEI_PER_ETH = Decimal("1000000000000000000")


def eth_to_wei(eth_amount: float) -> int:
    """Chuyen doi ETH (float, nguoi dung nhap) sang wei (int) khong mat do chinh xac.
    Streamlit number_input dung float64 nen khong the nhap truc tiep so wei lon (10^18)."""
    return int(Decimal(str(eth_amount)) * WEI_PER_ETH)


def wei_to_eth(wei_amount: int) -> float:
    return float(Decimal(wei_amount) / WEI_PER_ETH)


QR_PATTERN = re.compile(r"^ticket:(\d+):owner:(0x[a-fA-F0-9]{40})$")


def decode_qr_image(file_bytes: bytes):
    """Doc ma QR tu anh tai len. Tra ve (token_id, owner_address) hoac (None, None) neu khong doc duoc."""
    file_array = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(file_array, cv2.IMREAD_COLOR)
    if img is None:
        return None, None
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    if not data:
        return None, None
    match = QR_PATTERN.match(data.strip())
    if not match:
        return None, None
    token_id, owner_address = match.groups()
    return int(token_id), owner_address

st.set_page_config(page_title="Event Ticket - Blockchain Demo", page_icon="🎟️")
st.title("🎟️ Ung dung Ve Su Kien Blockchain")

try:
    event_info = requests.get(f"{SERVER_URL}/event", timeout=5).json()
    st.caption(f"Su kien: **{event_info['event_name']}**  |  Contract: `{event_info['contract_address']}`")
except Exception:
    st.error("Khong ket noi duoc server. Vui long kiem tra cac service da chay chua (docker compose up).")
    st.stop()

role = st.sidebar.radio("Chon vai tro", ["Nguoi mua", "Ban to chuc", "Nhan vien check-in"])

if role == "Ban to chuc":
    st.header("Phat hanh ve moi (Mint Ticket)")

    to_address_check = st.text_input("Kiem tra dia chi da ky dieu khoan chua (tuy chon)", key="check_signed")
    if to_address_check:
        try:
            status = requests.get(f"{SERVER_URL}/terms/status/{to_address_check}", timeout=5).json()
            if status["signed"]:
                st.success(f"✅ Dia chi nay da ky dieu khoan mua ve hien hanh.")
            else:
                st.warning("⚠️ Dia chi nay CHUA ky dieu khoan. Phat hanh ve se bi tu choi.")
        except Exception as e:
            st.error(f"Loi kiem tra: {e}")

    with st.form("mint_form"):
        to_address = st.text_input("Dia chi vi nguoi mua (0x...)")
        seat_id = st.number_input("So ghe", min_value=1, step=1)
        price_eth = st.number_input("Gia ve (ETH)", min_value=0.0001, value=1.0, step=0.01, format="%.4f")
        submitted = st.form_submit_button("Phat hanh ve")
        if submitted:
            try:
                resp = requests.post(
                    f"{SERVER_URL}/tickets/mint",
                    json={"to_address": to_address, "seat_id": int(seat_id), "price_wei": eth_to_wei(price_eth)},
                )
                resp.raise_for_status()
                ticket = resp.json()
                st.success(f"Da phat hanh ve #{ticket['token_id']} cho ghe {ticket['seat_id']}")
            except requests.HTTPError as e:
                st.error(f"Bi tu choi: {e.response.json().get('detail', str(e))}")
            except Exception as e:
                st.error(f"Loi: {e}")

    st.divider()
    st.subheader("Danh sach vi demo (Ganache)")
    try:
        accounts = requests.get(f"{SERVER_URL}/accounts", timeout=5).json()
        st.code("\n".join(accounts))
        st.caption("Dung cac dia chi nay de thu nghiem mint / mua / ban lai ve.")
    except Exception:
        pass

    st.divider()
    with st.expander("Cap nhat dieu khoan mua ve"):
        st.caption("Luu y: cap nhat noi dung se tao ra hash moi -> nguoi da ky truoc do se can ky lai.")
        try:
            current_terms = requests.get(f"{SERVER_URL}/terms", timeout=5).json()
        except Exception:
            current_terms = {"text": "", "hash": ""}
        new_terms_text = st.text_area("Noi dung dieu khoan", value=current_terms.get("text", ""), height=180)
        if st.button("Cap nhat dieu khoan"):
            try:
                resp = requests.put(f"{SERVER_URL}/terms", json={"text": new_terms_text})
                resp.raise_for_status()
                st.success("Da cap nhat dieu khoan. Hash moi: " + resp.json()["hash"])
            except Exception as e:
                st.error(f"Loi: {e}")

elif role == "Nguoi mua":
    st.header("Diem danh & Ky dieu khoan mua ve")
    st.caption(
        "Trong mo hinh nay, ban to chuc (backend) tra phi gas thay ban - ban chi can ky "
        "message bang private key, khong can co ETH trong vi. Day la vi 'demo' tao ngay "
        "trong trinh duyet, KHONG dung cho vi that."
    )

    if "buyer_private_key" not in st.session_state:
        st.session_state.buyer_private_key = None
        st.session_state.buyer_address = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Tao vi demo moi"):
            acct = Account.create()
            st.session_state.buyer_private_key = acct.key.hex()
            st.session_state.buyer_address = acct.address
    with col2:
        if st.session_state.buyer_address:
            st.code(st.session_state.buyer_address, language=None)

    if st.session_state.buyer_address:
        try:
            terms = requests.get(f"{SERVER_URL}/terms", timeout=5).json()
        except Exception as e:
            st.error(f"Loi tai dieu khoan: {e}")
            terms = None

        if terms and terms.get("text"):
            st.text_area("Dieu khoan mua ve", value=terms["text"], height=160, disabled=True)

            try:
                status = requests.get(
                    f"{SERVER_URL}/terms/status/{st.session_state.buyer_address}", timeout=5
                ).json()
            except Exception:
                status = {"signed": False}

            if status.get("signed"):
                st.success("✅ Vi nay da ky dieu khoan hien hanh. Ban to chuc co the phat hanh ve cho ban.")
            else:
                agree = st.checkbox("Toi da doc va dong y voi dieu khoan mua ve tren")
                if st.button("✍️ Ky dieu khoan", disabled=not agree):
                    try:
                        terms_hash_bytes = bytes.fromhex(terms["hash"][2:])
                        message = encode_defunct(primitive=terms_hash_bytes)
                        signed = Account.sign_message(
                            message, private_key=st.session_state.buyer_private_key
                        )
                        resp = requests.post(
                            f"{SERVER_URL}/terms/sign",
                            json={
                                "address": st.session_state.buyer_address,
                                "signature": signed.signature.hex(),
                            },
                        )
                        resp.raise_for_status()
                        st.success("Da ky dieu khoan thanh cong! Bao dia chi vi nay cho ban to chuc de nhan ve.")
                    except requests.HTTPError as e:
                        st.error(f"Bi tu choi: {e.response.json().get('detail', str(e))}")
                    except Exception as e:
                        st.error(f"Loi: {e}")

    st.divider()
    st.header("Ve cua toi")
    address = st.text_input("Nhap dia chi vi cua ban (0x...)")
    if address:
        try:
            tickets = requests.get(f"{SERVER_URL}/tickets/owner/{address}", timeout=5).json()
        except Exception as e:
            st.error(f"Loi: {e}")
            tickets = []

        if not tickets:
            st.info("Chua co ve nao cho dia chi nay.")

        for t in tickets:
            status = "Da su dung" if t["checked_in"] else "Chua su dung"
            gia_eth = wei_to_eth(t["original_price"])
            with st.container(border=True):
                st.write(f"**Ve #{t['token_id']}** - Ghe {t['seat_id']} - Gia goc {gia_eth:.4f} ETH - {status}")
                qr_payload = f"ticket:{t['token_id']}:owner:{t['owner']}"
                img = qrcode.make(qr_payload)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.image(buf.getvalue(), width=180, caption="Ma QR check-in")

    st.divider()
    st.subheader("Ban lai ve (Resale)")
    with st.form("resale_form"):
        token_id = st.number_input("Ma ve (token ID)", min_value=1, step=1)
        from_addr = st.text_input("Dia chi hien tai")
        to_addr = st.text_input("Dia chi nguoi mua moi")
        price_eth = st.number_input("Gia ban lai (ETH)", min_value=0.0001, value=1.0, step=0.01, format="%.4f")
        submitted = st.form_submit_button("Chuyen nhuong ve")
        if submitted:
            try:
                resp = requests.post(
                    f"{SERVER_URL}/tickets/{int(token_id)}/resale",
                    json={"from_address": from_addr, "to_address": to_addr, "price_wei": eth_to_wei(price_eth)},
                )
                resp.raise_for_status()
                st.success("Chuyen nhuong thanh cong! (Gia ban lai bi gioi han <= 110% gia goc tren smart contract)")
            except requests.HTTPError as e:
                st.error(f"Bi tu choi: {e.response.json().get('detail', str(e))}")
            except Exception as e:
                st.error(f"Loi: {e}")

else:  # Nhan vien check-in
    st.header("Check-in tai cong su kien")

    tab_qr, tab_manual = st.tabs(["Quet QR (tai anh len)", "Nhap tay (du phong)"])

    with tab_qr:
        uploaded = st.file_uploader("Tai anh QR cua ve len", type=["png", "jpg", "jpeg"])
        if uploaded is not None:
            token_id, qr_owner = decode_qr_image(uploaded.getvalue())

            if token_id is None:
                st.error("Khong doc duoc ma QR hop le tu anh nay. Vui long thu lai voi anh ro net hon.")
            else:
                st.image(uploaded, width=200, caption=f"Da doc: ve #{token_id}")
                try:
                    ticket = requests.get(f"{SERVER_URL}/tickets/{token_id}", timeout=5).json()
                except Exception as e:
                    st.error(f"Loi khi tra cuu ve tren blockchain: {e}")
                    ticket = None

                if ticket is None or "owner" not in ticket:
                    st.error("Ve nay khong ton tai tren blockchain. Co the la ve gia.")
                elif ticket["owner"].lower() != qr_owner.lower():
                    st.error(
                        "❌ QR KHONG HOP LE: dia chi chu so huu trong ma QR "
                        "khong khop voi chu so huu thuc te tren blockchain. "
                        "Co the QR nay la anh chup lai cua nguoi khac hoac ve da duoc ban lai."
                    )
                    st.caption(f"Dia chi trong QR: `{qr_owner}`")
                    st.caption(f"Chu so huu that su tren chain: `{ticket['owner']}`")
                elif ticket["checked_in"]:
                    st.warning(f"⚠️ Ve #{token_id} DA duoc su dung truoc do. Tu choi cho vao lan nua.")
                else:
                    st.success(f"✅ QR hop le - Ve #{token_id}, ghe {ticket['seat_id']}, dung chu so huu.")
                    if st.button("Xac nhan check-in", key="checkin_qr"):
                        try:
                            resp = requests.post(f"{SERVER_URL}/tickets/checkin", json={"token_id": token_id})
                            resp.raise_for_status()
                            st.success("CHO VAO ✅")
                        except requests.HTTPError as e:
                            st.error(f"Tu choi: {e.response.json().get('detail', str(e))} ❌")
                        except Exception as e:
                            st.error(f"Loi: {e}")

    with tab_manual:
        st.caption("Chi dung khi may quet/anh QR khong hoat dong. Cach nay KHONG kiem tra chu so huu.")
        token_id_manual = st.number_input("Nhap ma ve (token ID)", min_value=1, step=1, key="manual_token_id")
        if st.button("Xac nhan check-in (nhap tay)", key="checkin_manual"):
            try:
                resp = requests.post(f"{SERVER_URL}/tickets/checkin", json={"token_id": int(token_id_manual)})
                resp.raise_for_status()
                ticket = resp.json()
                st.success(f"Ve #{ticket['token_id']} - Ghe {ticket['seat_id']} - CHO VAO ✅")
            except requests.HTTPError as e:
                st.error(f"Tu choi: {e.response.json().get('detail', str(e))} ❌")
            except Exception as e:
                st.error(f"Loi: {e}")
