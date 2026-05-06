import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(page_title="ระบบจัดการสถานะการใช้รถ", layout="wide")

# --- File paths for persistent storage ---
CARS_FILE = "cars_data.json"
HISTORY_FILE = "history_data.json"

# --- Default car data ---
DEFAULT_CARS = [
    {"ยี่ห้อ": "Honda City (ซิตี้)", "ทะเบียน": "4กธ641",  "สถานะ": "ว่าง", "คนใช้": "-", "สถานที่": "-", "เวลายืม": "-"},
    {"ยี่ห้อ": "Ford Rapter",         "ทะเบียน": "4ขต8699", "สถานะ": "ว่าง", "คนใช้": "-", "สถานที่": "-", "เวลายืม": "-"},
    {"ยี่ห้อ": "มอเตอร์ไซต์",         "ทะเบียน": "7กย445",  "สถานะ": "ว่าง", "คนใช้": "-", "สถานที่": "-", "เวลายืม": "-"},
]

# --- Load / Save helpers ---
def load_json(filepath, default):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Load persistent state into session_state (only once per session) ---
if "cars" not in st.session_state:
    st.session_state.cars = load_json(CARS_FILE, DEFAULT_CARS)

if "history" not in st.session_state:
    st.session_state.history = load_json(HISTORY_FILE, [])

# --- Header ---
st.title("🚗 ระบบเช็คสถานะการใช้รถรายวัน")
st.write(f"วันที่ปัจจุบัน: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ============================================================
# Section 1: Summary Table
# ============================================================
st.subheader("📊 ตารางสรุปสถานะรถปัจจุบัน")

display_cols = ["ยี่ห้อ", "ทะเบียน", "สถานะ", "คนใช้", "สถานที่", "เวลายืม"]
df_current = pd.DataFrame(st.session_state.cars)[display_cols]

def highlight_status(row):
    if row["สถานะ"] == "กำลังใช้งาน":
        return ["background-color: #fff3cd"] * len(row)
    return [""] * len(row)

st.dataframe(df_current.style.apply(highlight_status, axis=1), use_container_width=True)

# ============================================================
# Section 2: ยืมรถ
# ============================================================
st.divider()
st.subheader("🔑 ยืมรถ")

available_cars = [c["ยี่ห้อ"] for c in st.session_state.cars if c["สถานะ"] == "ว่าง"]

if available_cars:
    col1, col2 = st.columns(2)
    with col1:
        borrow_car  = st.selectbox("เลือกรถที่ต้องการยืม", available_cars, key="borrow_car")
        borrow_name = st.text_input("ชื่อผู้ยืม", placeholder="ระบุชื่อผู้ขับ", key="borrow_name")
    with col2:
        borrow_dest = st.text_input("สถานที่ไป", placeholder="ระบุจุดหมาย", key="borrow_dest")

    if st.button("✅ ยืมรถ", type="primary"):
        if not borrow_name.strip():
            st.warning("กรุณาระบุชื่อผู้ยืม")
        elif not borrow_dest.strip():
            st.warning("กรุณาระบุสถานที่ไป")
        else:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            for car in st.session_state.cars:
                if car["ยี่ห้อ"] == borrow_car:
                    car["สถานะ"]  = "กำลังใช้งาน"
                    car["คนใช้"]  = borrow_name.strip()
                    car["สถานที่"] = borrow_dest.strip()
                    car["เวลายืม"] = now_str

            log = {
                "วันที่ยืม":    now_str,
                "วันที่คืน":    "-",
                "ผู้ใช้":       borrow_name.strip(),
                "รถ":           borrow_car,
                "สถานที่":      borrow_dest.strip(),
                "สถานะบันทึก": "ยืม",
            }
            st.session_state.history.append(log)

            save_json(CARS_FILE,    st.session_state.cars)
            save_json(HISTORY_FILE, st.session_state.history)

            st.success(f"บันทึกการยืมรถ **{borrow_car}** โดย **{borrow_name}** เรียบร้อยแล้ว!")
            st.rerun()
else:
    st.info("ขณะนี้ไม่มีรถว่าง")

# ============================================================
# Section 3: คืนรถ
# ============================================================
st.divider()
st.subheader("🔄 คืนรถ")

in_use_cars = [c["ยี่ห้อ"] for c in st.session_state.cars if c["สถานะ"] == "กำลังใช้งาน"]

if in_use_cars:
    return_car = st.selectbox("เลือกรถที่ต้องการคืน", in_use_cars, key="return_car")

    # Show who borrowed it
    for c in st.session_state.cars:
        if c["ยี่ห้อ"] == return_car:
            st.caption(f"ผู้ยืม: **{c['คนใช้']}**  |  สถานที่: **{c['สถานที่']}**  |  ยืมเมื่อ: **{c['เวลายืม']}**")

    if st.button("🔙 คืนรถ", type="secondary"):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        returned_user = "-"

        for car in st.session_state.cars:
            if car["ยี่ห้อ"] == return_car:
                returned_user    = car["คนใช้"]
                car["สถานะ"]    = "ว่าง"
                car["คนใช้"]    = "-"
                car["สถานที่"]  = "-"
                car["เวลายืม"]  = "-"

        # Update the matching borrow log with return time
        for log in reversed(st.session_state.history):
            if log["รถ"] == return_car and log["สถานะบันทึก"] == "ยืม" and log["วันที่คืน"] == "-":
                log["วันที่คืน"]    = now_str
                log["สถานะบันทึก"] = "คืนแล้ว"
                break

        save_json(CARS_FILE,    st.session_state.cars)
        save_json(HISTORY_FILE, st.session_state.history)

        st.success(f"บันทึกการคืนรถ **{return_car}** โดย **{returned_user}** เรียบร้อยแล้ว!")
        st.rerun()
else:
    st.write("ขณะนี้ไม่มีรถที่กำลังถูกใช้งาน")

# ============================================================
# Section 4: Who is out now?
# ============================================================
st.divider()
st.subheader("📍 สถานะการออกพื้นที่ปัจจุบัน")

busy_cars = [c for c in st.session_state.cars if c["สถานะ"] == "กำลังใช้งาน"]
if busy_cars:
    for car in busy_cars:
        st.info(f"👤 **{car['คนใช้']}** กำลังใช้รถ **{car['ยี่ห้อ']}** ไปที่ **{car['สถานที่']}** (ยืมเมื่อ {car['เวลายืม']})")
else:
    st.success("✅ ขณะนี้รถทุกคันจอดอยู่ที่สำนักงาน")

# ============================================================
# Section 5: 7-Day History Log
# ============================================================
st.divider()
st.subheader("📜 ประวัติการใช้รถ (ย้อนหลัง 7 วัน)")

if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history)

    df_history["_dt_ยืม"] = pd.to_datetime(df_history["วันที่ยืม"], errors="coerce")
    seven_days_ago = datetime.now() - timedelta(days=7)

    filtered = (
        df_history[df_history["_dt_ยืม"] >= seven_days_ago]
        .drop(columns=["_dt_ยืม"])
        .sort_values(by="วันที่ยืม", ascending=False)
        .reset_index(drop=True)
    )

    if not filtered.empty:
        # Colour rows: still borrowed = yellow, returned = green
        def highlight_log(row):
            if row["สถานะบันทึก"] == "ยืม":
                return ["background-color: #fff3cd"] * len(row)
            return ["background-color: #d1e7dd"] * len(row)

        show_cols = ["วันที่ยืม", "วันที่คืน", "ผู้ใช้", "รถ", "สถานที่", "สถานะบันทึก"]
        st.dataframe(
            filtered[show_cols].style.apply(highlight_log, axis=1),
            use_container_width=True,
        )
    else:
        st.info("ไม่มีประวัติการใช้งานในช่วง 7 วันที่ผ่านมา")
else:
    st.write("ยังไม่มีประวัติการใช้งาน")
