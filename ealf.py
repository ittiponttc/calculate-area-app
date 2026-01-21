import streamlit as st

st.title("คำนวณค่า Load Equivalency Factor (EALF) ตามมาตรฐาน AASHTO 1993") 
st.title ("พัตนาโดย : รศ.ดร.อิทธิพล มีผล")

import streamlit as st
import pandas as pd
import math
from dataclasses import dataclass, field
from typing import List, Dict

# ============================================================
# ค่าคงที่
# ============================================================
TON_TO_KIP = 2.2046
STANDARD_AXLE_LOAD = 18

# ============================================================
# ฟังก์ชันคำนวณ
# ============================================================
def calc_ealf_flexible(Lx_kip: float, L2: int, pt: float, SN: int) -> float:
    """คำนวณ EALF สำหรับ Flexible Pavement (สมการ 2-1)"""
    if Lx_kip <= 0 or L2 <= 0:
        return 0.0
    
    Gt = math.log10((4.2 - pt) / (4.2 - 1.5))
    beta_x = 0.40 + (0.081 * ((Lx_kip + L2) ** 3.23)) / (((SN + 1) ** 5.19) * (L2 ** 3.23))
    beta_18 = 0.40 + (0.081 * ((STANDARD_AXLE_LOAD + 1) ** 3.23)) / (((SN + 1) ** 5.19) * (1 ** 3.23))
    
    log_ratio = (4.79 * math.log10(STANDARD_AXLE_LOAD + 1) 
                - 4.79 * math.log10(Lx_kip + L2) 
                + 4.33 * math.log10(L2) 
                + (Gt / beta_x) - (Gt / beta_18))
    
    return 10 ** (-log_ratio)


def calc_ealf_rigid(Lx_kip: float, L2: int, pt: float, D: int) -> float:
    """คำนวณ EALF สำหรับ Rigid Pavement (สมการ 2-2)"""
    if Lx_kip <= 0 or L2 <= 0:
        return 0.0
    
    Gt = math.log10((4.5 - pt) / (4.5 - 1.5))
    beta_x = 1.00 + (3.63 * ((Lx_kip + L2) ** 5.20)) / (((D + 1) ** 8.46) * (L2 ** 3.52))
    beta_18 = 1.00 + (3.63 * ((STANDARD_AXLE_LOAD + 1) ** 5.20)) / (((D + 1) ** 8.46) * (1 ** 3.52))
    
    log_ratio = (4.62 * math.log10(STANDARD_AXLE_LOAD + 1) 
                - 4.62 * math.log10(Lx_kip + L2) 
                + 3.28 * math.log10(L2) 
                + (Gt / beta_x) - (Gt / beta_18))
    
    return 10 ** (-log_ratio)


def calc_truck_factor_flexible(axles: List[Dict], pt: float, SN: int) -> float:
    """คำนวณ Truck Factor สำหรับ Flexible Pavement"""
    total = 0.0
    for axle in axles:
        if axle['load'] > 0 and axle['L2'] > 0:
            Lx_kip = axle['load'] * TON_TO_KIP
            total += calc_ealf_flexible(Lx_kip, axle['L2'], pt, SN)
    return total


def calc_truck_factor_rigid(axles: List[Dict], pt: float, D: int) -> float:
    """คำนวณ Truck Factor สำหรับ Rigid Pavement"""
    total = 0.0
    for axle in axles:
        if axle['load'] > 0 and axle['L2'] > 0:
            Lx_kip = axle['load'] * TON_TO_KIP
            total += calc_ealf_rigid(Lx_kip, axle['L2'], pt, D)
    return total


# ============================================================
# ข้อมูลเริ่มต้น
# ============================================================
def get_default_trucks():
    """ข้อมูลรถบรรทุกมาตรฐาน"""
    return {
        'MB': {'name': 'Medium Bus', 'axles': [
            {'name': 'เพลาหน้า', 'load': 3.1, 'L2': 1},
            {'name': 'เพลาหลัง', 'load': 12.2, 'L2': 2},
            
        ]},
        'HB': {'name': 'Heavy Bus', 'axles': [
            {'name': 'เพลาหน้า', 'load': 4.0, 'L2': 1},
            {'name': 'เพลาหลัง', 'load': 14.3, 'L2': 2},

        ]},
        'MT': {'name': 'Medium Truck', 'axles': [
            {'name': 'เพลาหน้า', 'load': 4.0, 'L2': 1},
            {'name': 'เพลาหลัง', 'load': 11.0, 'L2': 1},

        ]},
        'HT': {'name': 'Heavy Truck', 'axles': [
            {'name': 'เพลาหน้า', 'load': 5.0, 'L2': 1},
            {'name': 'เพลาหลัง', 'load': 20.0, 'L2': 2},

        ]},
        'STR': {'name': 'Semi-Trailer', 'axles': [
            {'name': 'เพลาหน้า', 'load': 5.0, 'L2': 1},
            {'name': 'เพลาหลัง', 'load': 20.0, 'L2': 2},
            {'name': 'เพลาพ่วงหน้า', 'load': 0.0, 'L2': 0},
            {'name': 'เพลาพ่วงหลัง', 'load': 20.0, 'L2': 2},
        ]},
        'TR': {'name': 'Full Trailer', 'axles': [
            {'name': 'เพลาหน้า', 'load': 5.0, 'L2': 1},
            {'name': 'เพลาหลัง', 'load': 20, 'L2': 2},
            {'name': 'เพลาพ่วงหน้า', 'load': 11, 'L2': 1},
            {'name': 'เพลาพ่วงหลัง', 'load': 11, 'L2': 1},
        ]},
    }


# ============================================================
# Streamlit App
# ============================================================
def main():
    st.set_page_config(
        page_title="Truck Factor Calculator",
        page_icon="🚛",
        layout="wide"
    )
    
    st.title("🚛 Truck Factor Calculator")
    st.markdown("### คำนวณค่า Load Equivalency Factor (EALF) ตามมาตรฐาน AASHTO 1993")
    
    # Initialize session state
    if 'trucks' not in st.session_state:
        st.session_state.trucks = get_default_trucks()
    
    # Sidebar - Parameters
    st.sidebar.header("⚙️ พารามิเตอร์")
    
    st.sidebar.subheader("Terminal Serviceability (pt)")
    pt_options = st.sidebar.multiselect(
        "เลือกค่า pt",
        options=[2.0, 2.5, 3.0],
        default=[2.0, 2.5, 3.0]
    )
    
    st.sidebar.subheader("Flexible Pavement")
    sn_options = st.sidebar.multiselect(
        "Structural Number (SN)",
        options=[4, 5, 6, 7, 8],
        default=[4, 5, 6, 7, 8]
    )
    
    st.sidebar.subheader("Rigid Pavement")
    d_options = st.sidebar.multiselect(
        "ความหนาคอนกรีต D (นิ้ว)",
        options=[10, 11, 12, 13, 14],
        default=[10, 11, 12, 13, 14]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 รีเซ็ตค่าเริ่มต้น"):
        st.session_state.trucks = get_default_trucks()
        st.rerun()
    
    # Main content - Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 ข้อมูลรถบรรทุก", 
        "🛣️ Flexible Pavement", 
        "🧱 Rigid Pavement",
        "📊 รายละเอียด EALF"
    ])
    
    # ============================================================
    # Tab 1: ข้อมูลรถบรรทุก
    # ============================================================
    with tab1:
        st.header("ข้อมูลรถบรรทุก 6 ประเภท")
        st.markdown("*แก้ไขน้ำหนักเพลา (ตัน) และประเภทเพลา L₂ ได้ตามต้องการ*")
        st.markdown("**L₂:** 0 = ไม่มีเพลา, 1 = เดี่ยว (Single), 2 = คู่ (Tandem), 3 = สามเพลา (Tridem)")
        
        cols = st.columns(2)
        
        truck_codes = list(st.session_state.trucks.keys())
        
        for idx, code in enumerate(truck_codes):
            truck = st.session_state.trucks[code]
            col = cols[idx % 2]
            
            with col:
                with st.expander(f"🚚 {code} - {truck['name']}", expanded=True):
                    for i, axle in enumerate(truck['axles']):
                        c1, c2 = st.columns(2)
                        with c1:
                            new_load = st.number_input(
                                f"{axle['name']} (ตัน)",
                                min_value=0.0,
                                max_value=50.0,
                                value=float(axle['load']),
                                step=0.1,
                                key=f"{code}_load_{i}"
                            )
                            st.session_state.trucks[code]['axles'][i]['load'] = new_load
                        
                        with c2:
                            new_L2 = st.selectbox(
                                f"L₂ {axle['name']}",
                                options=[0, 1, 2, 3],
                                index=axle['L2'],
                                format_func=lambda x: {0: '0 - ไม่มี', 1: '1 - เดี่ยว', 2: '2 - คู่', 3: '3 - สามเพลา'}[x],
                                key=f"{code}_L2_{i}"
                            )
                            st.session_state.trucks[code]['axles'][i]['L2'] = new_L2
        
        # แสดงตารางสรุป
        st.markdown("---")
        st.subheader("📋 สรุปข้อมูลรถบรรทุก")
        
        summary_data = []
        for code, truck in st.session_state.trucks.items():
            row = {'ประเภท': code, 'คำอธิบาย': truck['name']}
            for axle in truck['axles']:
                if axle['load'] > 0 and axle['L2'] > 0:
                    l2_text = {1: 'เดี่ยว', 2: 'คู่', 3: 'สามเพลา'}[axle['L2']]
                    row[axle['name']] = f"{axle['load']:.2f} ตัน (L₂={axle['L2']} {l2_text})"
                else:
                    row[axle['name']] = "-"
            summary_data.append(row)
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # ============================================================
    # Tab 2: Flexible Pavement
    # ============================================================
    with tab2:
        st.header("🛣️ Truck Factor - Flexible Pavement (ผิวทางลาดยาง)")
        st.latex(r"\log\left(\frac{W_{tx}}{W_{t18}}\right) = 4.79\log(19) - 4.79\log(L_x+L_2) + 4.33\log(L_2) + \frac{G_t}{\beta_x} - \frac{G_t}{\beta_{18}}")
        
        if not pt_options or not sn_options:
            st.warning("กรุณาเลือกค่า pt และ SN ในแถบด้านซ้าย")
        else:
            for pt in pt_options:
                st.subheader(f"pt = {pt}")
                
                # สร้างตาราง
                data = []
                for code, truck in st.session_state.trucks.items():
                    row = {'ประเภท': code}
                    for sn in sn_options:
                        tf = calc_truck_factor_flexible(truck['axles'], pt, sn)
                        row[f'SN={sn}'] = tf
                    data.append(row)
                
                df = pd.DataFrame(data)
                
                # จัดรูปแบบตัวเลข
                styled_df = df.style.format({col: '{:.4f}' for col in df.columns if col != 'ประเภท'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
    
    # ============================================================
    # Tab 3: Rigid Pavement
    # ============================================================
    with tab3:
        st.header("🧱 Truck Factor - Rigid Pavement (ผิวทางคอนกรีต)")
        st.latex(r"\log\left(\frac{W_{tx}}{W_{t18}}\right) = 4.62\log(19) - 4.62\log(L_x+L_2) + 3.28\log(L_2) + \frac{G_t}{\beta_x} - \frac{G_t}{\beta_{18}}")
        
        if not pt_options or not d_options:
            st.warning("กรุณาเลือกค่า pt และ D ในแถบด้านซ้าย")
        else:
            for pt in pt_options:
                st.subheader(f"pt = {pt}")
                
                # สร้างตาราง
                data = []
                for code, truck in st.session_state.trucks.items():
                    row = {'ประเภท': code}
                    for d in d_options:
                        tf = calc_truck_factor_rigid(truck['axles'], pt, d)
                        row[f'D={d}"'] = tf
                    data.append(row)
                
                df = pd.DataFrame(data)
                
                styled_df = df.style.format({col: '{:.4f}' for col in df.columns if col != 'ประเภท'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
    
    # ============================================================
    # Tab 4: รายละเอียด EALF
    # ============================================================
    with tab4:
        st.header("📊 รายละเอียดการคำนวณ EALF แต่ละเพลา")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_truck = st.selectbox(
                "เลือกประเภทรถ",
                options=list(st.session_state.trucks.keys()),
                format_func=lambda x: f"{x} - {st.session_state.trucks[x]['name']}"
            )
        with col2:
            selected_pt = st.selectbox("เลือก pt", options=[2.0, 2.5, 3.0], index=1)
        with col3:
            pavement_type = st.radio("ประเภทผิวทาง", ["Flexible", "Rigid"], horizontal=True)
        
        if pavement_type == "Flexible":
            selected_param = st.selectbox("เลือก SN", options=[4, 5, 6, 7], index=1)
        else:
            selected_param = st.selectbox("เลือก D (นิ้ว)", options=[10, 11, 12, 13, 14], index=0)
        
        st.markdown("---")
        
        truck = st.session_state.trucks[selected_truck]
        st.subheader(f"🚚 {selected_truck} - {truck['name']}")
        
        # สร้างตารางรายละเอียด
        detail_data = []
        total_ealf = 0
        
        for axle in truck['axles']:
            if axle['load'] > 0 and axle['L2'] > 0:
                Lx_kip = axle['load'] * TON_TO_KIP
                
                if pavement_type == "Flexible":
                    ealf = calc_ealf_flexible(Lx_kip, axle['L2'], selected_pt, selected_param)
                else:
                    ealf = calc_ealf_rigid(Lx_kip, axle['L2'], selected_pt, selected_param)
                
                total_ealf += ealf
                l2_text = {1: 'เดี่ยว', 2: 'คู่', 3: 'สามเพลา'}[axle['L2']]
                
                detail_data.append({
                    'เพลา': axle['name'],
                    'น้ำหนัก (ตัน)': axle['load'],
                    'น้ำหนัก (kip)': Lx_kip,
                    'L₂': f"{axle['L2']} ({l2_text})",
                    'EALF': ealf
                })
        
        if detail_data:
            df_detail = pd.DataFrame(detail_data)
            
            styled_detail = df_detail.style.format({
                'น้ำหนัก (ตัน)': '{:.2f}',
                'น้ำหนัก (kip)': '{:.3f}',
                'EALF': '{:.6f}'
            })
            
            st.dataframe(styled_detail, use_container_width=True, hide_index=True)
            
            # แสดง Truck Factor
            st.success(f"**Truck Factor = {total_ealf:.6f}**")
            
            # แสดงพารามิเตอร์ที่ใช้
            if pavement_type == "Flexible":
                st.info(f"พารามิเตอร์: pt = {selected_pt}, SN = {selected_param}")
            else:
                st.info(f"พารามิเตอร์: pt = {selected_pt}, D = {selected_param} นิ้ว")
        else:
            st.warning("ไม่มีข้อมูลเพลา กรุณากรอกข้อมูลในแท็บ 'ข้อมูลรถบรรทุก'")
    
    # ============================================================
    # Footer
    # ============================================================
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>📚 อ้างอิง: AASHTO Guide for Design of Pavement Structures (1993)</p>
        <p>🔢 หน่วย: 1 ตัน = 2.2046 kip | Standard Axle Load = 18 kip</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()








