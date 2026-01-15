"""
ESAL Calculator - AASHTO 1993
โปรแกรมคำนวณปริมาณเพลาเดี่ยวมาตรฐานเทียบเท่า (Equivalent Single Axle Load)
สำหรับผิวทาง Rigid Pavement และ Flexible Pavement
ตามมาตรฐาน AASHTO Guide for Design of Pavement Structures (1993)

พัฒนาโดย: รศ.ดร.อิทธิพล มีผล ภาควิชาครุศาสตร์โยธา มจพ.
"""

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ============================================================
# ข้อมูลรถบรรทุก 6 ชนิดตามกรมทางหลวงประเทศไทย
# ============================================================
TRUCKS = {
    'MB': {
        'desc': 'Medium Bus (รถโดยสารขนาดกลาง)',
        'axles': [
            {'name': 'เพลาหน้า', 'load_ton': 3.1, 'type': 'Single'},
            {'name': 'เพลาหลัง', 'load_ton': 12.2, 'type': 'Tandem'}
        ]
    },
    'HB': {
        'desc': 'Heavy Bus (รถโดยสารขนาดใหญ่)',
        'axles': [
            {'name': 'เพลาหน้า', 'load_ton': 4.0, 'type': 'Single'},
            {'name': 'เพลาหลัง', 'load_ton': 14.3, 'type': 'Tandem'}
        ]
    },
    'MT': {
        'desc': 'Medium Truck (รถบรรทุกขนาดกลาง)',
        'axles': [
            {'name': 'เพลาหน้า', 'load_ton': 4.0, 'type': 'Single'},
            {'name': 'เพลาหลัง', 'load_ton': 11.0, 'type': 'Single'}
        ]
    },
    'HT': {
        'desc': 'Heavy Truck (รถบรรทุกขนาดใหญ่)',
        'axles': [
            {'name': 'เพลาหน้า', 'load_ton': 5.0, 'type': 'Single'},
            {'name': 'เพลาหลัง', 'load_ton': 20.0, 'type': 'Tandem'}
        ]
    },
    'STR': {
        'desc': 'Semi-Trailer (รถกึ่งพ่วง)',
        'axles': [
            {'name': 'เพลาหน้า', 'load_ton': 5.0, 'type': 'Single'},
            {'name': 'เพลาหลัง', 'load_ton': 20.0, 'type': 'Tandem'},
            {'name': 'เพลาพ่วงหลัง', 'load_ton': 20.0, 'type': 'Tandem'}
        ]
    },
    'TR': {
        'desc': 'Full Trailer (รถพ่วง)',
        'axles': [
            {'name': 'เพลาหน้า', 'load_ton': 5.0, 'type': 'Single'},
            {'name': 'เพลาหลัง', 'load_ton': 20, 'type': 'Tandem'},
            {'name': 'เพลาพ่วงหน้า', 'load_ton': 11, 'type': 'Single'},
            {'name': 'เพลาพ่วงหลัง', 'load_ton': 11, 'type': 'Single'}
        ]
    }
}

# ============================================================
# ตาราง Truck Factor คำนวณตาม AASHTO 1993
# ตรวจสอบกับตาราง AASHTO Table D.4-D.7 (Flexible) และ D.13-D.16 (Rigid)
# ============================================================

# Rigid Pavement - pt = 2.5
TRUCK_FACTORS_RIGID_PT25 = {
    'MB':  {10: 0.7327, 11: 0.7318, 12: 0.7314, 13: 0.7312, 14: 0.7311},
    'HB':  {10: 1.4579, 11: 1.4623, 12: 1.4643, 13: 1.4653, 14: 1.4659},
    'MT':  {10: 3.6578, 11: 3.7113, 12: 3.7383, 13: 3.7520, 14: 3.7591},
    'HT':  {10: 5.9211, 11: 6.0928, 12: 6.1867, 13: 6.2362, 14: 6.2626},
    'STR': {10: 11.7203, 11: 12.0643, 12: 12.2523, 13: 12.3516, 14: 12.4044},
    'TR':  {10: 13.1410, 11: 13.4203, 12: 13.5684, 13: 13.6454, 14: 13.6860}
}

# Rigid Pavement - pt = 2.0
TRUCK_FACTORS_RIGID_PT20 = {
    'MB':  {10: 0.5765, 11: 0.5758, 12: 0.5755, 13: 0.5754, 14: 0.5753},
    'HB':  {10: 1.1691, 11: 1.1725, 12: 1.1740, 13: 1.1748, 14: 1.1752},
    'MT':  {10: 3.0458, 11: 3.0879, 12: 3.1091, 13: 3.1197, 14: 3.1252},
    'HT':  {10: 4.9862, 11: 5.1310, 12: 5.2101, 13: 5.2518, 14: 5.2740},
    'STR': {10: 9.8709, 11: 10.1609, 12: 10.3192, 13: 10.4028, 14: 10.4474},
    'TR':  {10: 8.0167, 11: 8.1311, 12: 8.1891, 13: 8.2185, 14: 8.2339}
}

# Flexible Pavement - pt = 2.5
TRUCK_FACTORS_FLEX_PT25 = {
    'MB':  {4: 0.4788, 5: 0.4368, 6: 0.4116, 7: 0.3990},
    'HB':  {4: 0.9002, 5: 0.8580, 6: 0.8295, 7: 0.8146},
    'MT':  {4: 3.0695, 5: 3.2038, 6: 3.4511, 7: 3.6452},
    'HT':  {4: 3.0536, 5: 3.1575, 6: 3.3118, 7: 3.4218},
    'STR': {4: 5.9557, 5: 6.1828, 6: 6.5016, 7: 6.7265},
    'TR':  {4: 6.0018, 5: 6.1519, 6: 6.3433, 7: 6.4731}
}

# Flexible Pavement - pt = 2.0
TRUCK_FACTORS_FLEX_PT20 = {
    'MB':  {4: 0.3665, 5: 0.3376, 6: 0.3202, 7: 0.3116},
    'HB':  {4: 0.7089, 5: 0.6814, 6: 0.6626, 7: 0.6534},
    'MT':  {4: 2.5455, 5: 2.6613, 6: 2.8713, 7: 3.0364},
    'HT':  {4: 2.5080, 5: 2.5937, 6: 2.7220, 7: 2.8131},
    'STR': {4: 4.8886, 5: 5.0778, 6: 5.3438, 7: 5.5286},
    'TR':  {4: 4.9138, 5: 5.0387, 6: 5.1978, 7: 5.3023}
}


def get_default_truck_factor(truck_code, pavement_type, pt, param):
    """ดึงค่า Truck Factor เริ่มต้นจากตาราง"""
    if pavement_type == 'rigid':
        if pt == 2.5:
            return TRUCK_FACTORS_RIGID_PT25[truck_code][param]
        else:
            return TRUCK_FACTORS_RIGID_PT20[truck_code][param]
    else:
        if pt == 2.5:
            return TRUCK_FACTORS_FLEX_PT25[truck_code][param]
        else:
            return TRUCK_FACTORS_FLEX_PT20[truck_code][param]


def calculate_esal(traffic_df, truck_factors, lane_factor=0.5, direction_factor=1.0):
    """คำนวณ ESAL จากข้อมูลปริมาณจราจร"""
    results = []
    total_esal = 0
    
    for idx, row in traffic_df.iterrows():
        year = row.get('Year', idx + 1)
        year_esal = 0
        year_data = {'Year': year}
        
        for code in TRUCKS.keys():
            if code in traffic_df.columns:
                aadt = row[code]
                tf = truck_factors[code]
                esal = aadt * tf * lane_factor * direction_factor * 365
                year_data[f'{code}_ADT'] = aadt
                year_data[f'{code}_TF'] = tf
                year_data[f'{code}_ESAL'] = esal
                year_esal += esal
        
        year_data['Total_ESAL'] = year_esal
        total_esal += year_esal
        results.append(year_data)
    
    return pd.DataFrame(results), total_esal


def create_template():
    """สร้าง Template Excel สำหรับอัพโหลดข้อมูล"""
    base = {'MB': 120, 'HB': 60, 'MT': 250, 'HT': 180, 'STR': 120, 'TR': 100}
    growth_rate = 1.045
    
    data = {'Year': list(range(1, 21))}
    for code in base.keys():
        data[code] = [int(base[code] * (growth_rate ** i)) for i in range(20)]
    
    return pd.DataFrame(data)


def to_excel(df):
    """แปลง DataFrame เป็น Excel bytes"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Traffic Data')
    return output.getvalue()


def get_all_truck_factors_table(pavement_type, pt):
    """สร้างตาราง Truck Factor ทั้งหมด"""
    data = []
    
    if pavement_type == 'rigid':
        params = [10, 11, 12, 13, 14]
        param_label = 'D'
        tf_table = TRUCK_FACTORS_RIGID_PT25 if pt == 2.5 else TRUCK_FACTORS_RIGID_PT20
    else:
        params = [4, 5, 6, 7]
        param_label = 'SN'
        tf_table = TRUCK_FACTORS_FLEX_PT25 if pt == 2.5 else TRUCK_FACTORS_FLEX_PT20
    
    for code in TRUCKS.keys():
        row = {'ประเภท': code, 'รายละเอียด': TRUCKS[code]['desc']}
        for p in params:
            col_name = f'{param_label}={p}"' if pavement_type == 'rigid' else f'{param_label}={p}'
            row[col_name] = f"{tf_table[code][p]:.4f}"
        data.append(row)
    
    return pd.DataFrame(data)


# ============================================================
# Streamlit App
# ============================================================
def main():
    st.set_page_config(
        page_title="ESAL Calculator - AASHTO 1993",
        page_icon="🛣️",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4A6FA5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-box {
        background: linear-gradient(135deg, #1E3A5F 0%, #4A6FA5 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<p class="main-header">🛣️ ESAL Calculator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">คำนวณปริมาณเพลาเดี่ยวมาตรฐานเทียบเท่า ตามมาตรฐาน AASHTO 1993</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ พารามิเตอร์การคำนวณ")
        
        pavement_type = st.selectbox(
            "ประเภทผิวทาง",
            options=['rigid', 'flexible'],
            format_func=lambda x: '🧱 Rigid Pavement (คอนกรีต)' if x == 'rigid' else '🛤️ Flexible Pavement (ลาดยาง)'
        )
        
        pt = st.selectbox(
            "Terminal Serviceability (pt)",
            options=[2.5, 2.0],
            format_func=lambda x: f"pt = {x}"
        )
        
        if pavement_type == 'rigid':
            param = st.selectbox(
                "ความหนาพื้นคอนกรีต (D)",
                options=[10, 11, 12, 13, 14],
                format_func=lambda x: f"D = {x} นิ้ว"
            )
            param_label = f"D = {param} นิ้ว"
        else:
            param = st.selectbox(
                "Structural Number (SN)",
                options=[4, 5, 6, 7],
                format_func=lambda x: f"SN = {x}"
            )
            param_label = f"SN = {param}"
        
        st.divider()
        
        st.subheader("🚗 ค่าสัดส่วน")
        lane_factor = st.slider("Lane Distribution Factor", 0.1, 1.0, 0.5, 0.05)
        direction_factor = st.slider("Directional Factor", 0.5, 1.0, 1.0, 0.1)
        
        st.divider()
        
        # ============================================================
        # ส่วนแก้ไขค่า Truck Factor
        # ============================================================
        st.subheader("🚛 ค่า Truck Factor")
        
        # สร้าง session state สำหรับเก็บค่า Truck Factor
        tf_key = f"tf_{pavement_type}_{pt}_{param}"
        if tf_key not in st.session_state:
            st.session_state[tf_key] = {}
            for code in TRUCKS.keys():
                st.session_state[tf_key][code] = get_default_truck_factor(code, pavement_type, pt, param)
        
        # ปุ่ม Reset เป็นค่า Default
        if st.button("🔄 Reset เป็นค่า Default", use_container_width=True):
            for code in TRUCKS.keys():
                st.session_state[tf_key][code] = get_default_truck_factor(code, pavement_type, pt, param)
            st.rerun()
        
        # Input สำหรับแก้ไขค่า Truck Factor แต่ละประเภท
        st.caption("กรอกค่า Truck Factor (แก้ไขได้)")
        
        truck_factors = {}
        for code in TRUCKS.keys():
            default_val = get_default_truck_factor(code, pavement_type, pt, param)
            current_val = st.session_state[tf_key].get(code, default_val)
            
            new_val = st.number_input(
                f"{code}",
                min_value=0.0,
                max_value=50.0,
                value=float(current_val),
                step=0.0001,
                format="%.4f",
                key=f"input_{tf_key}_{code}",
                help=f"{TRUCKS[code]['desc']} | Default: {default_val:.4f}"
            )
            
            st.session_state[tf_key][code] = new_val
            truck_factors[code] = new_val
        
        st.divider()
        
        st.subheader("📥 ดาวน์โหลด Template")
        template_df = create_template()
        st.download_button(
            label="📄 ดาวน์โหลด Template Excel",
            data=to_excel(template_df),
            file_name="traffic_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Main Content
    tab1, tab2, tab3 = st.tabs(["📊 คำนวณ ESAL", "🚛 ข้อมูล Truck Factor", "📘 คู่มือ"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📤 อัพโหลดข้อมูลปริมาณจราจร")
            
            uploaded_file = st.file_uploader(
                "เลือกไฟล์ Excel",
                type=['xlsx', 'xls'],
                help="อัพโหลดไฟล์ Excel (หน่วย: คัน/วัน)"
            )
            
            if 'use_sample' not in st.session_state:
                st.session_state['use_sample'] = False
            
            if uploaded_file is not None:
                try:
                    traffic_df = pd.read_excel(uploaded_file)
                    st.success("✅ อัพโหลดสำเร็จ!")
                    st.session_state['use_sample'] = False
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                    traffic_df = None
            else:
                st.info("📌 อัพโหลดไฟล์ Excel หรือใช้ข้อมูลตัวอย่าง")
                
                if st.button("🔄 ใช้ข้อมูลตัวอย่าง", use_container_width=True):
                    st.session_state['use_sample'] = True
                
                traffic_df = create_template() if st.session_state['use_sample'] else None
            
            if traffic_df is not None:
                st.write("**ข้อมูลปริมาณจราจร (คัน/วัน):**")
                st.dataframe(traffic_df, use_container_width=True, height=350)
        
        with col2:
            st.subheader("📈 ผลการคำนวณ ESAL")
            
            if traffic_df is not None:
                # ใช้ค่า Truck Factor จาก sidebar (ที่ผู้ใช้กรอก/แก้ไขได้)
                results_df, total_esal = calculate_esal(
                    traffic_df, truck_factors, lane_factor, direction_factor
                )
                
                # แสดงผลรวม
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-value">{total_esal:,.0f}</div>
                        <div class="metric-label">ESAL รวมทั้งหมด</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_m2:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-value">{len(traffic_df)}</div>
                        <div class="metric-label">จำนวนปี</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_m3:
                    pavement_label = "Rigid" if pavement_type == 'rigid' else "Flexible"
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-value">{pavement_label}</div>
                        <div class="metric-label">ประเภทผิวทาง</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_m4:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-value">{param_label}</div>
                        <div class="metric-label">พารามิเตอร์</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # ตาราง Truck Factor ที่ใช้ (แสดงค่าที่ผู้ใช้กรอก)
                st.write("**🚛 ค่า Truck Factor ที่ใช้:**")
                tf_display = []
                for code, tf in truck_factors.items():
                    default_tf = get_default_truck_factor(code, pavement_type, pt, param)
                    status = "✅" if abs(tf - default_tf) < 0.0001 else "✏️ แก้ไข"
                    tf_display.append({
                        'รหัส': code, 
                        'ประเภท': TRUCKS[code]['desc'], 
                        'Truck Factor': f"{tf:.4f}",
                        'Default': f"{default_tf:.4f}",
                        'สถานะ': status
                    })
                st.dataframe(pd.DataFrame(tf_display), use_container_width=True, hide_index=True)
                
                st.divider()
                
                # ผลลัพธ์รายปี
                st.write("**📊 ESAL รายปี:**")
                
                summary_cols = ['Year']
                for code in TRUCKS.keys():
                    if f'{code}_ESAL' in results_df.columns:
                        summary_cols.append(f'{code}_ESAL')
                summary_cols.append('Total_ESAL')
                
                summary_df = results_df[summary_cols].copy()
                rename_dict = {'Year': 'ปีที่', 'Total_ESAL': 'ESAL รวม'}
                for code in TRUCKS.keys():
                    rename_dict[f'{code}_ESAL'] = code
                summary_df = summary_df.rename(columns=rename_dict)
                
                for col in summary_df.columns:
                    if col != 'ปีที่':
                        summary_df[col] = summary_df[col].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(summary_df, use_container_width=True, height=400)
                
                # ดาวน์โหลด
                st.divider()
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Summary sheet
                    pd.DataFrame({
                        'รายการ': ['ประเภทผิวทาง', 'pt', 'พารามิเตอร์', 'Lane Factor', 'Direction Factor', 'ESAL รวม', 'จำนวนปี'],
                        'ค่า': ['Rigid' if pavement_type == 'rigid' else 'Flexible', pt, param_label, lane_factor, direction_factor, f"{total_esal:,.0f}", len(traffic_df)]
                    }).to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Truck Factors sheet (รวมค่าที่ใช้และค่า Default)
                    pd.DataFrame(tf_display).to_excel(writer, sheet_name='Truck Factors', index=False)
                    
                    # ESAL by Year
                    results_df.to_excel(writer, sheet_name='ESAL by Year', index=False)
                    
                    # Input Data
                    traffic_df.to_excel(writer, sheet_name='Input Data', index=False)
                
                st.download_button(
                    label="📥 ดาวน์โหลดผลลัพธ์ (Excel)",
                    data=output.getvalue(),
                    file_name=f"ESAL_Results_{pavement_type}_{param}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ กรุณาอัพโหลดข้อมูลหรือใช้ข้อมูลตัวอย่าง")
    
    with tab2:
        st.subheader("🚛 ข้อมูลรถบรรทุก 6 ประเภทตามกรมทางหลวง")
        
        truck_details = []
        for code, truck in TRUCKS.items():
            axle_info = []
            for axle in truck['axles']:
                axle_info.append(f"{axle['name']}: {axle['load_ton']} ตัน ({axle['type']})")
            truck_details.append({'รหัส': code, 'ประเภท': truck['desc'], 'ข้อมูลเพลา': ' | '.join(axle_info)})
        
        st.dataframe(pd.DataFrame(truck_details), use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📊 ตาราง Truck Factor (ค่า Default ตาม AASHTO 1993)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🧱 Rigid Pavement (pt = 2.5)**")
            st.dataframe(get_all_truck_factors_table('rigid', 2.5), use_container_width=True, hide_index=True)
            
            st.write("**🧱 Rigid Pavement (pt = 2.0)**")
            st.dataframe(get_all_truck_factors_table('rigid', 2.0), use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**🛤️ Flexible Pavement (pt = 2.5)**")
            st.dataframe(get_all_truck_factors_table('flexible', 2.5), use_container_width=True, hide_index=True)
            
            st.write("**🛤️ Flexible Pavement (pt = 2.0)**")
            st.dataframe(get_all_truck_factors_table('flexible', 2.0), use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("📘 คู่มือการใช้งาน")
        
        st.markdown("""
        ### 1️⃣ เตรียมไฟล์ Excel
        
        | คอลัมน์ | คำอธิบาย |
        |---------|----------|
        | `Year` | ปีที่ (1, 2, 3, ... n) |
        | `MB` | Medium Bus (คัน/วัน) |
        | `HB` | Heavy Bus (คัน/วัน) |
        | `MT` | Medium Truck (คัน/วัน) |
        | `HT` | Heavy Truck (คัน/วัน) |
        | `STR` | Semi-Trailer (คัน/วัน) |
        | `TR` | Full Trailer (คัน/วัน) |
        
        ### 2️⃣ ตั้งค่าพารามิเตอร์
        
        - **Rigid:** D = 10-14 นิ้ว
        - **Flexible:** SN = 4-7
        - **pt:** 2.0 หรือ 2.5
        
        ### 3️⃣ แก้ไขค่า Truck Factor (ใหม่!)
        
        - ค่า Truck Factor สามารถแก้ไขได้ที่ Sidebar
        - ค่า Default จะโหลดตามตาราง AASHTO 1993
        - กดปุ่ม "Reset เป็นค่า Default" เพื่อคืนค่าเริ่มต้น
        - ค่าที่แก้ไขจะแสดงสถานะ "✏️ แก้ไข" ในตารางผลลัพธ์
        
        ### 4️⃣ สูตรคำนวณ ESAL
        """)
        
        st.latex(r'ESAL = \sum_{i=1}^{n} \sum_{j=1}^{6} (ADT_{ij} \times TF_j \times LF \times DF \times 365)')
        
        st.markdown("""
        ### 📚 อ้างอิง
        - AASHTO Guide for Design of Pavement Structures (1993)
        - กรมทางหลวง กระทรวงคมนาคม
        """)
    
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888;">
        พัฒนาเพื่อการเรียนการสอนโดย รศ.ดร.อิทธิพล มีผล ภาควิชาครุศาสตร์โยธา มจพ. | ESAL Calculator v1.1
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
