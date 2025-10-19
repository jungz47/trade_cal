import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# ซ่อน GitHub icon, Fork button, และ viewer badge
hide_github_icon = """
<style>
#GithubIcon {
    visibility: hidden !important;
}
.css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_, .viewerBadge_link__1S4ls {
    display: none !important;
}
</style>
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)

# ชื่อแอป
st.title("เครื่องมือคำนวณขนาดการเทรดง่ายๆ (มีประวัติการคำนวณ)")

# เริ่มต้น session_state สำหรับเก็บประวัติ
if 'history' not in st.session_state:
    st.session_state.history = []

# ช่องพิมพ์สัญลักษณ์หุ้น
selected_symbol = st.text_input("ใส่สัญลักษณ์หุ้น (เช่น TSLA, NVDA, PTT.BK):", value="TSLA").upper()

# ดึงข้อมูลหุ้น (ราคาปิดและชื่อบริษัท)
@st.cache_data(ttl=300)  # Cache 5 นาทีเพื่อความเร็ว
def get_stock_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if not hist.empty:
            close_price = hist['Close'].iloc[-1]
            company_name = ticker.info.get('longName', 'ไม่พบชื่อบริษัท')
            return close_price, company_name
        else:
            return None, None
    except Exception as e:
        st.error(f"ไม่สามารถดึงข้อมูลสำหรับ {symbol} ได้: {str(e)}")
        return None, None

latest_close, company_name = get_stock_info(selected_symbol)
default_entry = latest_close if latest_close is not None else 100.0

# แสดงชื่อบริษัทเพื่อ cross-check
if company_name:
    st.info(f"ชื่อบริษัท: {company_name}")
else:
    st.warning("ไม่พบข้อมูลหุ้น กรุณาตรวจสอบสัญลักษณ์ หรือใช้ค่า default")

# อินพุตจากผู้ใช้
account_balance = st.number_input("ทุนทั้งหมด (บาทหรือ USD)", min_value=0.0, value=100000.0)
risk_percent = st.number_input("ความเสี่ยงต่อเทรด (%)", min_value=0.0, max_value=100.0, value=1.0)
entry_price = st.number_input(
    f"ราคาเข้า (Entry) - ล่าสุด: {latest_close:.2f}" if latest_close else "ราคาเข้า (Entry)",
    min_value=0.0,
    value=default_entry
)
stop_loss_price = st.number_input(
    "ราคาหยุดขาดทุน (Stop Loss / Exit)",
    min_value=0.0,
    value=default_entry * 0.95
)

# คำนวณและบันทึกประวัติ
if st.button("คำนวณ"):
    if entry_price > stop_loss_price:
        risk_per_unit = entry_price - stop_loss_price
        risk_amount = account_balance * (risk_percent / 100)
        position_size = risk_amount / risk_per_unit
        trade_value = position_size * entry_price
        
        # บันทึกผลลงประวัติ
        calculation = {
            "วันที่เวลา": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "หุ้น": selected_symbol,
            "ชื่อบริษัท": company_name if company_name else "ไม่พบชื่อบริษัท",
            "ทุน (บาท/USD)": round(account_balance, 2),
            "ความเสี่ยง (%)": risk_percent,
            "ราคาเข้า": round(entry_price, 2),
            "Stop Loss": round(stop_loss_price, 2),
            "ขนาดการเทรด (หน่วย)": round(position_size, 2),
            "มูลค่าการเทรด": round(trade_value, 2),
            "ความเสี่ยงทั้งหมด": round(risk_amount, 2),
            "ระยะห่าง Stop Loss": round(risk_per_unit, 2)
        }
        st.session_state.history.insert(0, calculation)  # เพิ่มที่ด้านบนสุด
        
        # แสดงผลลัพธ์
        st.success(f"หุ้น: {selected_symbol} ({company_name if company_name else 'ไม่พบชื่อบริษัท'})")
        st.success(f"ขนาดการเทรดที่แนะนำ: {position_size:.2f} หน่วย (หุ้น)")
        st.success(f"มูลค่าการเทรด: {trade_value:.2f} บาท/USD")
        st.info(f"ความเสี่ยงทั้งหมด: {risk_amount:.2f} บาท/USD\nระยะห่าง Stop Loss: {risk_per_unit:.2f}")
    else:
        st.error("ราคาเข้า ต้องสูงกว่าราคา Stop Loss สำหรับ Long Position")

# แสดงตารางประวัติ
if st.session_state.history:
    st.subheader("ประวัติการคำนวณ")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
