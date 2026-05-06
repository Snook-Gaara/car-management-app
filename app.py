import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(page_title="ระบบจัดการสถานะการใช้รถ", layout="wide")

# --- Fixed Data (No one can add cars via UI) ---
if 'cars' not in st.session_state:
    st.session_state.cars = [
        {"ยี่ห้อ": "Honda City (ซิตี้)", "ทะเบียน": "4กธ641", "สถานะ": "ว่าง", "คนใช้": "-", "สถานที่": "-"},
        {"ยี่ห้อ": "Ford Rapter", "ทะเบียน": "4ขต8699", "สถานะ": "ว่าง", "คนใช้": "-", "สถานที่": "-"},
        {"ยี่ห้อ": "มอเตอร์ไซต์", "ทะเบียน": "7กย445", "สถานะ": "ว่าง", "คนใช้": "-", "สถานที่": "-"},
    ]

# --- Usage History Log ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Header ---
st.title("🚗 ระบบเช็คสถานะการใช้รถรายวัน")
st.write(f"วันที่ปัจจุบัน: {datetime.now().strftime('%d/%m/%Y')}")

# --- Section 1: Summary Table ---
st.subheader("📊 ตารางสรุปสถานะรถปัจจุบัน")
df_current = pd.DataFrame(st.session_state.cars)
st.table(df_current)

# --- Section 2: Recording/Update Form ---
st.divider()
st.subheader("📝 บันทึกการใช้งาน/คืนรถ")

col1, col2 = st.columns(2)

with col1:
    selected_car = st.selectbox("เลือกยี่ห้อรถ", [c['ยี่ห้อ'] for c in st.session_state.cars])
    status = st.radio("เปลี่ยนสถานะเป็น", ["กำลังใช้งาน", "ว่าง"])

with col2:
    user_name = st.text_input("ชื่อผู้ใช้งาน", placeholder="ระบุชื่อผู้ขับ")
    destination = st.text_input("สถานที่ไป", placeholder="ระบุจุดหมาย")

if st.button("บันทึกข้อมูล"):
    # Update Current Status
    for car in st.session_state.cars:
        if car['ยี่ห้อ'] == selected_car:
            car['สถานะ'] = status
            car['คนใช้'] = user_name if status == "กำลังใช้งาน" else "-"
            car['สถานที่'] = destination if status == "กำลังใช้งาน" else "-"
            
            # Log to History (Only if status is 'กำลังใช้งาน')
            if status == "กำลังใช้งาน":
                new_log = {
                    "วันที่": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "User": user_name,
                    "Vehicle": selected_car,
                    "Destination": destination
                }
                st.session_state.history.append(new_log)
    
    st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
    st.rerun()

# --- Section 3: 7-Day History Log ---
st.divider()
st.subheader("📜 ประวัติการใช้รถ (ย้อนหลัง 7 วัน)")

if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history)
    
    # Convert to datetime to filter
    df_history['วันที่'] = pd.to_datetime(df_history['วันที่'])
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Filter only last 7 days
    filtered_history = df_history[df_history['วันที่'] >= seven_days_ago].sort_values(by="วันที่", ascending=False)
    
    if not filtered_history.empty:
        st.dataframe(filtered_history, use_container_width=True)
    else:
        st.info("ไม่มีประวัติการใช้งานในช่วง 7 วันที่ผ่านมา")
else:
    st.write("ยังไม่มีประวัติการใช้งาน")

# --- Section 4: Who is out now? ---
st.divider()
st.subheader("📍 สถานะการออกพื้นที่ปัจจุบัน")
busy_cars = df_current[df_current['สถานะ'] == "กำลังใช้งาน"]
if not busy_cars.empty:
    for index, row in busy_cars.iterrows():
        st.info(f"👤 **{row['คนใช้']}** กำลังใช้รถ **{row['ยี่ห้อ']}** ไปที่ **{row['สถานที่']}**")
else:
    st.write("ขณะนี้รถทุกคันจอดอยู่ที่สำนักงาน")
