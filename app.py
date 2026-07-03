import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta, timezone

# Thailand timezone = UTC+7
TH_TZ = timezone(timedelta(hours=7))

def now_th():
    """Return current datetime in Thailand timezone (UTC+7)."""
    return datetime.now(TH_TZ)

# --- Page Configuration ---
st.set_page_config(page_title="ระบบจัดการสถานะการใช้รถ", layout="wide")

# --- File paths for persistent storage ---
CARS_FILE = "cars_data.json"
HISTORY_FILE = "history_data.json"
FUEL_FILE = "fuel_data.json"

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

if "fuel" not in st.session_state:
    st.session_state.fuel = load_json(FUEL_FILE, [])

# --- Header ---
st.title("🚗 ระบบเช็คสถานะการใช้รถรายวัน")
st.write(f"วันที่ปัจจุบัน: {now_th().strftime('%d/%m/%Y %H:%M')}")

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
            now_str = now_th().strftime("%Y-%m-%d %H:%M")
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
        now_str = now_th().strftime("%Y-%m-%d %H:%M")
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
# Section 5: ⛽ บันทึกค่าใช้จ่ายการเติมน้ำมัน
# ============================================================
st.divider()
st.subheader("⛽ บันทึกค่าใช้จ่ายการเติมน้ำมัน")

all_car_names = [c["ยี่ห้อ"] for c in st.session_state.cars]

with st.form("fuel_form", clear_on_submit=True):
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        fuel_car = st.selectbox("เลือกรถ", all_car_names, key="fuel_car")
        fuel_date = st.date_input("วันที่เติมน้ำมัน", value=now_th().date(), key="fuel_date")
    with fcol2:
        fuel_liters = st.number_input("จำนวนลิตร", min_value=0.0, step=0.1, format="%.2f", key="fuel_liters")
        fuel_price_per_liter = st.number_input("ราคาต่อลิตร (บาท)", min_value=0.0, step=0.1, format="%.2f", key="fuel_price_per_liter")
    with fcol3:
        fuel_odometer = st.text_input("เลขไมล์ (ถ้ามี)", placeholder="เช่น 123456", key="fuel_odometer")
        fuel_payer = st.text_input("ผู้จ่าย/ผู้เติม", placeholder="ระบุชื่อผู้เติมน้ำมัน", key="fuel_payer")

    fuel_note = st.text_input("หมายเหตุ (ถ้ามี)", placeholder="เช่น ปั๊ม ปตท. สาขา...", key="fuel_note")

    fuel_amount_manual = st.number_input(
        "จำนวนเงินรวม (บาท) — หากไม่กรอก จะคำนวณจากลิตร x ราคาต่อลิตร",
        min_value=0.0, step=1.0, format="%.2f", key="fuel_amount_manual"
    )

    submitted = st.form_submit_button("✅ บันทึกค่าน้ำมัน", type="primary")

    if submitted:
        if not fuel_payer.strip():
            st.warning("กรุณาระบุชื่อผู้เติมน้ำมัน")
        else:
            calculated_amount = fuel_liters * fuel_price_per_liter
            total_amount = fuel_amount_manual if fuel_amount_manual > 0 else calculated_amount

            if total_amount <= 0:
                st.warning("กรุณาระบุจำนวนเงิน หรือ จำนวนลิตรและราคาต่อลิตร")
            else:
                fuel_record = {
                    "วันที่": fuel_date.strftime("%Y-%m-%d"),
                    "รถ": fuel_car,
                    "จำนวนลิตร": round(fuel_liters, 2) if fuel_liters > 0 else "-",
                    "ราคาต่อลิตร": round(fuel_price_per_liter, 2) if fuel_price_per_liter > 0 else "-",
                    "จำนวนเงิน (บาท)": round(total_amount, 2),
                    "เลขไมล์": fuel_odometer.strip() if fuel_odometer.strip() else "-",
                    "ผู้จ่าย": fuel_payer.strip(),
                    "หมายเหตุ": fuel_note.strip() if fuel_note.strip() else "-",
                    "บันทึกเมื่อ": now_th().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.fuel.append(fuel_record)
                save_json(FUEL_FILE, st.session_state.fuel)
                st.success(f"บันทึกค่าน้ำมันรถ **{fuel_car}** จำนวน **{total_amount:,.2f} บาท** เรียบร้อยแล้ว!")
                st.rerun()

# --- แสดงประวัติการเติมน้ำมัน + สรุปยอด ---
if st.session_state.fuel:
    df_fuel = pd.DataFrame(st.session_state.fuel)

    # ตัวกรอง: เลือกรถ / ช่วงวันที่
    fcol_a, fcol_b = st.columns([1, 2])
    with fcol_a:
        filter_car = st.selectbox("กรองตามรถ", ["ทั้งหมด"] + all_car_names, key="filter_fuel_car")
    with fcol_b:
        min_date = pd.to_datetime(df_fuel["วันที่"]).min().date()
        max_date = pd.to_datetime(df_fuel["วันที่"]).max().date()
        date_range = st.date_input(
            "ช่วงวันที่", value=(min_date, max_date), key="filter_fuel_date"
        )

    filtered_fuel = df_fuel.copy()
    filtered_fuel["_dt"] = pd.to_datetime(filtered_fuel["วันที่"])

    if filter_car != "ทั้งหมด":
        filtered_fuel = filtered_fuel[filtered_fuel["รถ"] == filter_car]

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_fuel = filtered_fuel[
            (filtered_fuel["_dt"] >= pd.to_datetime(start_d)) &
            (filtered_fuel["_dt"] <= pd.to_datetime(end_d))
        ]

    filtered_fuel = filtered_fuel.drop(columns=["_dt"]).sort_values(by="วันที่", ascending=False).reset_index(drop=True)

    show_fuel_cols = ["วันที่", "รถ", "จำนวนลิตร", "ราคาต่อลิตร", "จำนวนเงิน (บาท)", "เลขไมล์", "ผู้จ่าย", "หมายเหตุ"]
    st.dataframe(filtered_fuel[show_fuel_cols], use_container_width=True)

    total_baht = filtered_fuel["จำนวนเงิน (บาท)"].sum()
    total_liters = pd.to_numeric(filtered_fuel["จำนวนลิตร"], errors="coerce").sum()

    scol1, scol2 = st.columns(2)
    with scol1:
        st.metric("💰 ยอดรวมค่าน้ำมัน (ตามตัวกรอง)", f"{total_baht:,.2f} บาท")
    with scol2:
        st.metric("⛽ ยอดรวมจำนวนลิตร (ตามตัวกรอง)", f"{total_liters:,.2f} ลิตร")

    with st.expander("📈 สรุปค่าน้ำมันแยกตามรถ (ทั้งหมด)"):
        summary = (
            df_fuel.groupby("รถ")["จำนวนเงิน (บาท)"]
            .sum()
            .reset_index()
            .sort_values(by="จำนวนเงิน (บาท)", ascending=False)
        )
        st.dataframe(summary, use_container_width=True)
else:
    st.write("ยังไม่มีประวัติการเติมน้ำมัน")

# ============================================================
# Section 6: 7-Day History Log
# ============================================================
st.divider()
st.subheader("📜 ประวัติการใช้รถ (ย้อนหลัง 7 วัน)")

if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history)

    df_history["_dt_ยืม"] = pd.to_datetime(df_history["วันที่ยืม"], errors="coerce")
    seven_days_ago = now_th().replace(tzinfo=None) - timedelta(days=7)

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
