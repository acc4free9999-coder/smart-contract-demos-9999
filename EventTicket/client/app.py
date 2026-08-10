import io
import os

import qrcode
import requests
import streamlit as st

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000")

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
    with st.form("mint_form"):
        to_address = st.text_input("Dia chi vi nguoi mua (0x...)")
        seat_id = st.number_input("So ghe", min_value=1, step=1)
        price = st.number_input("Gia ve (wei)", min_value=1, value=1_000_000_000_000_000_000, step=1)
        submitted = st.form_submit_button("Phat hanh ve")
        if submitted:
            try:
                resp = requests.post(
                    f"{SERVER_URL}/tickets/mint",
                    json={"to_address": to_address, "seat_id": int(seat_id), "price_wei": int(price)},
                )
                resp.raise_for_status()
                ticket = resp.json()
                st.success(f"Da phat hanh ve #{ticket['token_id']} cho ghe {ticket['seat_id']}")
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

elif role == "Nguoi mua":
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
            with st.container(border=True):
                st.write(f"**Ve #{t['token_id']}** - Ghe {t['seat_id']} - {status}")
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
        price = st.number_input("Gia ban lai (wei)", min_value=1, value=1_000_000_000_000_000_000, step=1)
        submitted = st.form_submit_button("Chuyen nhuong ve")
        if submitted:
            try:
                resp = requests.post(
                    f"{SERVER_URL}/tickets/{int(token_id)}/resale",
                    json={"from_address": from_addr, "to_address": to_addr, "price_wei": int(price)},
                )
                resp.raise_for_status()
                st.success("Chuyen nhuong thanh cong! (Gia ban lai bi gioi han <= 110% gia goc tren smart contract)")
            except requests.HTTPError as e:
                st.error(f"Bi tu choi: {e.response.json().get('detail', str(e))}")
            except Exception as e:
                st.error(f"Loi: {e}")

else:  # Nhan vien check-in
    st.header("Check-in tai cong su kien")
    token_id = st.number_input("Nhap ma ve (token ID) tu QR", min_value=1, step=1)
    if st.button("Xac nhan check-in"):
        try:
            resp = requests.post(f"{SERVER_URL}/tickets/checkin", json={"token_id": int(token_id)})
            resp.raise_for_status()
            ticket = resp.json()
            st.success(f"Ve #{ticket['token_id']} - Ghe {ticket['seat_id']} - CHO VAO ✅")
        except requests.HTTPError as e:
            st.error(f"Tu choi: {e.response.json().get('detail', str(e))} ❌")
        except Exception as e:
            st.error(f"Loi: {e}")
