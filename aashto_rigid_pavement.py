"""
โปรแกรมคำนวณความหนาโครงสร้างชั้นทางคอนกรีต (Rigid Pavement)
ตามวิธี AASHTO 1993
พัฒนาสำหรับการเรียนการสอนวิศวกรรมโยธา
"""

import streamlit as st
import numpy as np
import math
import pandas as pd


def bisection_method(func, a, b, tol=1e-6, max_iter=100):
    """
    Bisection Method สำหรับหาค่า root ของฟังก์ชัน
    ใช้แทน scipy.optimize.brentq
    
    Parameters:
    - func: ฟังก์ชันที่ต้องการหา root
    - a, b: ช่วงที่ค้นหา (func(a) และ func(b) ต้องมีเครื่องหมายต่างกัน)
    - tol: ความคลาดเคลื่อนที่ยอมรับได้
    - max_iter: จำนวนรอบสูงสุด
    
    Returns:
    - root: ค่า x ที่ทำให้ func(x) ≈ 0
    """
    fa = func(a)
    fb = func(b)
    
    if fa * fb > 0:
        # ไม่มี root ในช่วงนี้
        return None
    
    for _ in range(max_iter):
        c = (a + b) / 2
        fc = func(c)
        
        if abs(fc) < tol or (b - a) / 2 < tol:
            return c
        
        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc
    
    return (a + b) / 2

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="AASHTO 1993 Rigid Pavement Design",
    page_icon="🛣️",
    layout="wide"
)

# CSS สำหรับตกแต่ง
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: #EFF6FF;
        border: 2px solid #3B82F6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        border: 2px solid #F59E0B;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #D1FAE5;
        border: 2px solid #10B981;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-text {
        font-size: 0.9rem;
        color: #6B7280;
    }
</style>
""", unsafe_allow_html=True)

# หัวข้อหลัก
st.markdown('<h1 class="main-header">🛣️ การออกแบบโครงสร้างชั้นทางคอนกรีต</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">ตามวิธี AASHTO 1993 (Rigid Pavement Design)</p>', unsafe_allow_html=True)

# ข้อมูลวัสดุรองพื้นทาง (Material Database)
MATERIALS = {
    "รองผิวทาง วัสดุ AC (Asphalt Concrete)": {"E_MPa": 2500, "E_psi": 362500},
    "พื้นทางซีเมนต์ CTB (Cement Treated Base)": {"E_MPa": 1200, "E_psi": 174000},
    "พื้นทางหินคลุกผสมซีเมนต์ UCS 24.5 ksc": {"E_MPa": 850, "E_psi": 123250},
    "พื้นทางหินคลุก CBR 80%": {"E_MPa": 350, "E_psi": 50750},
    "รองพื้นทางวัสดุมวลรวม CBR 25%": {"E_MPa": 150, "E_psi": 21750},
    "วัสดุคัดเลือก n (Selected Material)": {"E_MPa": 76, "E_psi": 11020},
    "ทรายถม (Sand Fill)": {"E_MPa": 100, "E_psi": 14500},
}

# ข้อมูล Subgrade
SUBGRADE_OPTIONS = {
    "ดินถมคันทาง CBR 3%": {"CBR": 3, "MR_psi": 4500},
    "ดินถมคันทาง CBR 4%": {"CBR": 4, "MR_psi": 6000},
    "ดินถมคันทาง CBR 5%": {"CBR": 5, "MR_psi": 7500},
    "ดินถมคันทาง CBR 6%": {"CBR": 6, "MR_psi": 9000},
    "ทรายคันทาง CBR 10%": {"CBR": 10, "MR_psi": 15000},
    
}

# ประเภทผิวทางคอนกรีต
PAVEMENT_TYPES = {
    "JPCP (Jointed Plain Concrete Pavement)": {"J_default": 2.8, "description": "ผิวทางคอนกรีตแบบมีรอยต่อไม่เสริมเหล็ก"},
    "JRCP (Jointed Reinforced Concrete Pavement)": {"J_default": 2.8, "description": "ผิวทางคอนกรีตแบบมีรอยต่อเสริมเหล็ก"},
    "CRCP (Continuously Reinforced Concrete Pavement)": {"J_default": 2.5, "description": "ผิวทางคอนกรีตเสริมเหล็กต่อเนื่อง"},
}


def calculate_odemark_equivalent_thickness(layers, subgrade_MR, nu_concrete=0.15, nu_subgrade=0.40):
    """
    คำนวณ Equivalent Thickness ตามวิธี Odemark
    
    สูตร: h_e = h × (E₁/E₂)^(1/3) × [(1-ν₂²)/(1-ν₁²)]^(1/3)
    
    Parameters:
    - layers: list of dict with 'E_psi' and 'thickness_inch'
    - subgrade_MR: Resilient Modulus ของ Subgrade (psi)
    - nu_concrete: Poisson's ratio ของคอนกรีต (default 0.15)
    - nu_subgrade: Poisson's ratio ของ Subgrade (default 0.40)
    
    Returns:
    - h_equivalent: ความหนาเทียบเท่า (นิ้ว)
    - calculation_details: รายละเอียดการคำนวณ
    """
    if not layers:
        return 0, []
    
    calculation_details = []
    h_equivalent_total = 0
    
    # Poisson's ratio correction factor
    # สำหรับแต่ละชั้น เทียบกับ Subgrade
    poisson_factor = ((1 - nu_subgrade**2) / (1 - nu_concrete**2)) ** (1/3)
    
    for i, layer in enumerate(layers):
        h_i = layer['thickness_inch']
        E_i = layer['E_psi']
        
        if h_i > 0 and E_i > 0:
            # Odemark's transformation
            # h_e = h × (E_layer/E_subgrade)^(1/3)
            modulus_ratio = (E_i / subgrade_MR) ** (1/3)
            h_e = h_i * modulus_ratio * poisson_factor
            
            h_equivalent_total += h_e
            
            calculation_details.append({
                'layer': i + 1,
                'name': layer.get('name', f'Layer {i+1}'),
                'h_actual_inch': h_i,
                'h_actual_cm': h_i * 2.54,
                'E_psi': E_i,
                'modulus_ratio': modulus_ratio,
                'h_equiv_inch': h_e,
                'h_equiv_cm': h_e * 2.54
            })
    
    return h_equivalent_total, calculation_details


def calculate_composite_k_odemark(layers, subgrade_MR, loss_of_support=0):
    """
    คำนวณค่า Composite Modulus of Subgrade Reaction (k-effective)
    โดยใช้วิธี Odemark's Equivalent Thickness ตาม AASHTO 1993
    
    ขั้นตอน:
    1. คำนวณ Equivalent Thickness ของชั้นรองพื้นทาง
    2. หาค่า k จาก Subgrade MR
    3. ปรับค่า k ตาม Equivalent Thickness
    4. ปรับแก้ Loss of Support (ถ้ามี)
    
    Parameters:
    - layers: list of dict with 'E_psi' and 'thickness_inch'
    - subgrade_MR: Resilient Modulus ของ Subgrade (psi)
    - loss_of_support: ค่า LS (0, 1, 2, หรือ 3)
    
    Returns:
    - k_effective: ค่า k ประสิทธิผล (pci)
    - k_composite: ค่า k composite ก่อนปรับ LS
    - h_equiv: ความหนาเทียบเท่า (นิ้ว)
    - details: รายละเอียดการคำนวณ
    """
    # ค่า k ของ Subgrade โดยประมาณ
    # จาก AASHTO: k ≈ MR / 19.4 (สำหรับ semi-infinite subgrade)
    k_subgrade = subgrade_MR / 19.4
    
    if not layers:
        k_effective = k_subgrade
        # ปรับแก้ Loss of Support
        if loss_of_support > 0:
            k_effective = k_subgrade * (10 ** (-loss_of_support * 0.3))
        return k_effective, k_subgrade, 0, {'h_equiv': 0, 'layer_details': []}
    
    # คำนวณ Equivalent Thickness
    h_equiv, layer_details = calculate_odemark_equivalent_thickness(layers, subgrade_MR)
    
    # คำนวณ Composite k ตาม AASHTO 1993 Figure 3.3
    # ใช้ความสัมพันธ์ระหว่าง k_composite, k_subgrade, และ D_sb (equivalent)
    
    if h_equiv > 0:
        # สูตรประมาณจาก AASHTO Nomograph
        # k_∞ = k_subgrade × f(D_sb, E_sb/MR)
        
        # หา Equivalent Modulus ของชั้นรองพื้นทางรวม
        total_h = sum(layer['thickness_inch'] for layer in layers)
        sum_h_sqrt_E = sum(layer['thickness_inch'] * math.sqrt(layer['E_psi']) for layer in layers)
        
        if total_h > 0:
            E_eq = (sum_h_sqrt_E / total_h) ** 2
        else:
            E_eq = subgrade_MR
        
        # Composite k calculation based on Odemark
        # k_composite ≈ k_subgrade × [1 + (h_equiv/a)²]^0.5
        # โดย a = radius of relative stiffness ≈ 30 นิ้ว (typical)
        
        # Alternative: ใช้ AASHTO Figure 3.3 approximation
        # สำหรับ subbase thickness และ E_sb
        
        # Enhancement factor
        D_sb = h_equiv  # ใช้ความหนาเทียบเท่า
        E_ratio = E_eq / subgrade_MR
        
        # Polynomial approximation จาก AASHTO nomograph
        # k_composite/k_subgrade ≈ 1 + C1×(D_sb)^C2 × (E_ratio)^C3
        C1 = 0.025
        C2 = 0.8
        C3 = 0.33
        
        enhancement = 1 + C1 * (D_sb ** C2) * (E_ratio ** C3)
        k_composite = k_subgrade * enhancement
        
        # จำกัดค่าไม่เกิน practical range
        k_composite = min(k_composite, 1500)
        k_composite = max(k_composite, k_subgrade)
    else:
        k_composite = k_subgrade
    
    # ปรับแก้ Loss of Support (LS)
    # จาก AASHTO 1993 Figure 3.6
    if loss_of_support > 0:
        # k_eff = k_composite × 10^(-LS × factor)
        # factor ≈ 0.3 for typical conditions
        k_effective = k_composite * (10 ** (-loss_of_support * 0.25))
    else:
        k_effective = k_composite
    
    # จำกัดค่า k ไม่ให้เกิน practical limits
    k_effective = min(k_effective, 1000)
    k_effective = max(k_effective, 25)
    
    details = {
        'h_equiv': h_equiv,
        'layer_details': layer_details,
        'k_subgrade': k_subgrade,
        'E_equivalent': E_eq if 'E_eq' in dir() else subgrade_MR,
    }
    
    return k_effective, k_composite, h_equiv, details


def calculate_composite_k(layers, subgrade_MR):
    """
    Wrapper function สำหรับความเข้ากันได้กับโค้ดเดิม
    """
    k_effective, _, _, _ = calculate_composite_k_odemark(layers, subgrade_MR, loss_of_support=0)
    return k_effective


def calculate_W18_rigid(D, params):
    """
    คำนวณค่า W18 (ESAL capacity) สำหรับความหนา D ที่กำหนด
    ตามสมการ AASHTO 1993 สำหรับ Rigid Pavement
    
    Parameters:
    - D: ความหนาแผ่นคอนกรีต (นิ้ว)
    - params: dictionary ของพารามิเตอร์ออกแบบ
    
    Returns:
    - log10(W18)
    """
    ZR = params['ZR']
    S0 = params['S0']
    pt = params['pt']
    Sc = params['Sc']
    Cd = params['Cd']
    J = params['J']
    Ec = params['Ec']
    k = params['k']
    delta_PSI = params['delta_PSI']
    
    # สมการ AASHTO 1993 สำหรับ Rigid Pavement
    # log W18 = ZR*S0 + 7.35*log(D+1) - 0.06 + term1 + term2
    
    # Term 1: log[ΔPSI/(4.5-1.5)] / [1 + 1.624×10^7/(D+1)^8.46]
    numerator1 = math.log10(delta_PSI / 3.0)
    denominator1 = 1 + (1.624e7 / ((D + 1) ** 8.46))
    term1 = numerator1 / denominator1
    
    # Term 2: (4.22 - 0.32*pt) * log{[Sc*Cd*(D^0.75 - 1.132)] / [215.63*J*(D^0.75 - 18.42/(Ec/k)^0.25)]}
    D_075 = D ** 0.75
    Ec_k_ratio = (Ec / k) ** 0.25
    
    inner_num = Sc * Cd * (D_075 - 1.132)
    inner_denom = 215.63 * J * (D_075 - 18.42 / Ec_k_ratio)
    
    if inner_num <= 0 or inner_denom <= 0:
        return -999  # Invalid case
    
    term2 = (4.22 - 0.32 * pt) * math.log10(inner_num / inner_denom)
    
    log_W18 = ZR * S0 + 7.35 * math.log10(D + 1) - 0.06 + term1 + term2
    
    return log_W18


def find_required_thickness(W18_design, params, D_min=6, D_max=20):
    """
    หาความหนาที่ต้องการเพื่อรองรับ W18 ที่กำหนด
    
    Parameters:
    - W18_design: ค่า ESAL ออกแบบ
    - params: พารามิเตอร์ออกแบบ
    - D_min, D_max: ช่วงความหนาที่ค้นหา (นิ้ว)
    
    Returns:
    - ความหนาที่ต้องการ (นิ้ว)
    """
    log_W18_design = math.log10(W18_design)
    
    def objective(D):
        return calculate_W18_rigid(D, params) - log_W18_design
    
    try:
        # ตรวจสอบว่ามีคำตอบในช่วงหรือไม่
        f_min = objective(D_min)
        f_max = objective(D_max)
        
        if f_min > 0:
            return D_min  # ความหนาต่ำสุดก็เพียงพอแล้ว
        if f_max < 0:
            return D_max + 1  # ต้องการความหนามากกว่าช่วงที่กำหนด
        
        # ใช้ Bisection Method แทน scipy.optimize.brentq
        D_required = bisection_method(objective, D_min, D_max)
        return D_required
    except:
        return None


def inch_to_cm(inch):
    """แปลงนิ้วเป็นเซนติเมตร"""
    return inch * 2.54


def cm_to_inch(cm):
    """แปลงเซนติเมตรเป็นนิ้ว"""
    return cm / 2.54


# ========================
# ส่วน Sidebar - พารามิเตอร์
# ========================
st.sidebar.header("⚙️ พารามิเตอร์ออกแบบ")

# เลือกประเภทผิวทาง
pavement_type = st.sidebar.selectbox(
    "ประเภทผิวทางคอนกรีต",
    list(PAVEMENT_TYPES.keys()),
    index=0
)
st.sidebar.caption(PAVEMENT_TYPES[pavement_type]["description"])

st.sidebar.subheader("📊 ค่าระดับความเชื่อมั่น")
reliability_options = {
    "80%": -0.841,
    "85%": -1.037,
    "90%": -1.282,
    "95%": -1.645,
    "99%": -2.326,
}
reliability = st.sidebar.selectbox(
    "Reliability (R)",
    list(reliability_options.keys()),
    index=2  # Default 90%
)
ZR = reliability_options[reliability]
st.sidebar.caption(f"Z_R = {ZR:.3f}")

S0 = st.sidebar.slider(
    "Overall Standard Deviation (S₀)",
    min_value=0.30, max_value=0.45, value=0.35, step=0.01,
    help="AASHTO แนะนำ 0.35 สำหรับ Rigid Pavement"
)

st.sidebar.subheader("📈 ค่า Serviceability")
Pi = st.sidebar.slider(
    "Initial Serviceability (Pᵢ)",
    min_value=4.0, max_value=4.8, value=4.5, step=0.1
)
pt = st.sidebar.slider(
    "Terminal Serviceability (pₜ)",
    min_value=2.0, max_value=3.0, value=2.5, step=0.1
)
delta_PSI = Pi - pt
st.sidebar.info(f"ΔPSI = {delta_PSI:.1f}")

st.sidebar.subheader("🧱 คุณสมบัติคอนกรีต")
fc_options = {
    "280 ksc (C24)": {"fc_psi": 3980, "Sc_psi": 500, "Ec_psi": 3200000},
    "320 ksc (C28)": {"fc_psi": 4550, "Sc_psi": 550, "Ec_psi": 3400000},
    "350 ksc (C35)": {"fc_psi": 4978, "Sc_psi": 600, "Ec_psi": 3670559},
    "400 ksc (C40)": {"fc_psi": 5688, "Sc_psi": 650, "Ec_psi": 3900000},
}
fc_selected = st.sidebar.selectbox(
    "กำลังอัดคอนกรีต (f'c)",
    list(fc_options.keys()),
    index=2  # Default 350 ksc
)
concrete_props = fc_options[fc_selected]

# ให้ผู้ใช้ปรับค่า Sc ได้
Sc = st.sidebar.number_input(
    "Modulus of Rupture, Sc (psi)",
    min_value=400.0, max_value=800.0, 
    value=float(concrete_props['Sc_psi']), step=50,
    help="ค่า Modulus of Rupture ของคอนกรีต"
)

Ec = st.sidebar.number_input(
    "Elastic Modulus, Ec (psi)",
    min_value=2000000.0, max_value=5000000.0,
    value=float(concrete_props['Ec_psi']), step=50000.0,
    help="ค่า Modulus of Elasticity ของคอนกรีต"
)

st.sidebar.subheader("🔗 ค่าสัมประสิทธิ์")
J_default = PAVEMENT_TYPES[pavement_type]["J_default"]
J = st.sidebar.slider(
    "Load Transfer Coefficient (J)",
    min_value=2.0, max_value=4.5, value=J_default, step=0.1,
    help="ค่า J ขึ้นอยู่กับประเภทไหล่ทางและอุปกรณ์ถ่ายแรง"
    help="JPCP/JRCP ไหล่ทางคอนกรีต 2.5-3.5 ค่ากลาง 2.8"
    help="CRCP ไหล่ทางคอนกรีต 2.3-2.9 ค่ากลาง 2.5"
    help=" ค่า J หากใช้ค่าน้อย==>ความหนาผิวทาง>>บางลง"
)

Cd = st.sidebar.slider(
    "Drainage Coefficient (Cd)",
    min_value=0.70, max_value=1.25, value=1.20, step=0.05,
    help="ค่าสัมประสิทธิ์การระบายน้ำ"
    help="ค่าแนะนำโดยกรมทางหลวง = 1.0"
    help=" ค่า Cd หากมีค่ามาก==>ความหนาผิวทาง>>บางลง"
)

st.sidebar.subheader("📉 Loss of Support")
LS = st.sidebar.selectbox(
    "Loss of Support (LS)",
    options=[0, 1, 2, 3],
    index=0,
    help="ค่าการสูญเสียฐานรองรับ (0=ไม่มี, 1=เล็กน้อย, 2=ปานกลาง, 3=มาก)"
)
st.sidebar.caption("LS=0: CTB/LCB, LS=1: Cement aggregate, LS=2: Asphalt treated, LS=3: Granular")

# ========================
# ส่วนหลัก - ข้อมูลออกแบบ
# ========================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 ข้อมูลปริมาณจราจร")
    
    # กรอกค่า ESAL
    W18_input = st.number_input(
        "ปริมาณ ESAL ออกแบบ (W₁₈)",
        min_value=1000000.0,
        max_value=1000000000.0,
        value=250000000.0,
        step=1000000.0,
        format="%.0f",
        help="Equivalent Single Axle Load 18 kips ตลอดอายุออกแบบ"
    )
    
    st.caption(f"log₁₀(W₁₈) = {math.log10(W18_input):.4f}")

with col2:
    st.subheader("🏗️ ดินฐานราก (Subgrade)")
    
    subgrade_selected = st.selectbox(
        "เลือกประเภทดินฐานราก",
        list(SUBGRADE_OPTIONS.keys()),
        index=1  # Default CBR 5%
    )
    
    subgrade_data = SUBGRADE_OPTIONS[subgrade_selected]
    
    # ให้ปรับค่า CBR ได้
    CBR_custom = st.number_input(
        "ค่า CBR (%)",
        min_value=1.0, max_value=30.0,
        value=float(subgrade_data['CBR']), step=0.5
    )
    
    # คำนวณ MR จาก CBR (MR = 1500 × CBR สำหรับ CBR ≤ 10%)
    if CBR_custom <= 10:
        MR_subgrade = 1500 * CBR_custom
    else:
        MR_subgrade = 1500 * 10 + 500 * (CBR_custom - 10)
    
    st.info(f"M_R (Subgrade) = {MR_subgrade:,.0f} psi ({MR_subgrade/145.038:.0f} MPa)")

# ========================
# ส่วนเลือกวัสดุรองพื้นทาง
# ========================
st.subheader("📦 วัสดุรองพื้นทาง (Subbase/Base Layers)")

st.markdown("""
<div class="info-text">
กำหนดวัสดุและความหนาของชั้นรองพื้นทาง (สูงสุด 4 ชั้น จากบนลงล่าง)
</div>
""", unsafe_allow_html=True)

num_layers = st.slider("จำนวนชั้นวัสดุรองพื้นทาง", 1, 4, 3)

layers = []
layer_cols = st.columns(num_layers)

layer_names = ["ชั้นที่ 1 (บนสุด)", "ชั้นที่ 2", "ชั้นที่ 3", "ชั้นที่ 4"]
default_materials = [
    "รองผิวทาง วัสดุ AC (Asphalt Concrete)",
    "พื้นทางซีเมนต์ CTB (Cement Treated Base)",
    "รองพื้นทางวัสดุมวลรวม CBR 25%",
    "ทรายถม (Sand Fill)"
]
default_thicknesses = [5, 20, 15, 30]  # cm

for i, col in enumerate(layer_cols):
    with col:
        st.markdown(f"**{layer_names[i]}**")
        
        material = st.selectbox(
            "วัสดุ",
            list(MATERIALS.keys()),
            index=list(MATERIALS.keys()).index(default_materials[min(i, len(default_materials)-1)]),
            key=f"material_{i}"
        )
        
        thickness_cm = st.number_input(
            "ความหนา (ซม.)",
            min_value=0.0, max_value=100.0,
            value=float(default_thicknesses[min(i, len(default_thicknesses)-1)]),
            step=5.0,
            key=f"thickness_{i}"
        )
        
        mat_data = MATERIALS[material]
        st.caption(f"E = {mat_data['E_MPa']} MPa")
        
        if thickness_cm > 0:
            layers.append({
                "name": material,
                "E_psi": mat_data["E_psi"],
                "E_MPa": mat_data["E_MPa"],
                "thickness_cm": thickness_cm,
                "thickness_inch": cm_to_inch(thickness_cm)
            })

# ========================
# คำนวณและแสดงผล
# ========================
st.markdown("---")

if st.button("🔢 คำนวณความหนาผิวทางคอนกรีต", type="primary", use_container_width=True):
    
    # คำนวณ Composite k โดยใช้ Odemark's Method
    k_effective, k_composite, h_equiv, odemark_details = calculate_composite_k_odemark(
        layers, MR_subgrade, loss_of_support=LS
    )
    
    # รวบรวมพารามิเตอร์
    params = {
        'ZR': ZR,
        'S0': S0,
        'pt': pt,
        'Sc': Sc,
        'Cd': Cd,
        'J': J,
        'Ec': Ec,
        'k': k_effective,
        'delta_PSI': delta_PSI,
    }
    
    # หาความหนาที่ต้องการ
    D_required = find_required_thickness(W18_input, params)
    
    # แสดงผลลัพธ์
    st.subheader("📊 ผลการคำนวณ")
    
    # แสดง Odemark Equivalent Thickness
    with st.expander("🔬 การคำนวณ Odemark's Equivalent Thickness", expanded=True):
        st.markdown("""
        **สูตร Odemark:**
        $$h_e = h \\times \\left(\\frac{E_{layer}}{E_{subgrade}}\\right)^{1/3} \\times \\left(\\frac{1-\\nu_{sg}^2}{1-\\nu_{layer}^2}\\right)^{1/3}$$
        """)
        
        if odemark_details['layer_details']:
            odemark_df_data = []
            for detail in odemark_details['layer_details']:
                odemark_df_data.append({
                    "ชั้น": detail['layer'],
                    "วัสดุ": detail['name'].split('(')[0].strip()[:25],
                    "h จริง (ซม.)": f"{detail['h_actual_cm']:.1f}",
                    "E (psi)": f"{detail['E_psi']:,}",
                    "(E/MR)^⅓": f"{detail['modulus_ratio']:.3f}",
                    "h_equiv (ซม.)": f"{detail['h_equiv_cm']:.2f}",
                })
            
            odemark_df = pd.DataFrame(odemark_df_data)
            st.dataframe(odemark_df, use_container_width=True, hide_index=True)
            
            st.info(f"📏 **รวมความหนาเทียบเท่า (h_equiv) = {h_equiv:.2f} นิ้ว ({h_equiv*2.54:.1f} ซม.)**")
        else:
            st.warning("ไม่มีชั้นรองพื้นทาง")
    
    # แสดงค่า k
    k_col1, k_col2, k_col3 = st.columns(3)
    
    with k_col1:
        st.metric(
            "k (Subgrade)",
            f"{odemark_details.get('k_subgrade', MR_subgrade/19.4):.0f} pci",
            help="ค่า k ของดินฐานราก = MR/19.4"
        )
    
    with k_col2:
        st.metric(
            "k (Composite)",
            f"{k_composite:.0f} pci",
            f"+{((k_composite/odemark_details.get('k_subgrade', MR_subgrade/19.4))-1)*100:.0f}% จาก subgrade",
            help="ค่า k รวมจากชั้นรองพื้นทาง (ก่อนปรับ LS)"
        )
    
    with k_col3:
        if LS > 0:
            st.metric(
                "k (Effective)",
                f"{k_effective:.0f} pci",
                f"LS = {LS}",
                delta_color="inverse",
                help="ค่า k ประสิทธิผลหลังปรับ Loss of Support"
            )
        else:
            st.metric(
                "k (Effective)",
                f"{k_effective:.0f} pci",
                "LS = 0 (ไม่ปรับ)",
                help="ค่า k ประสิทธิผล (ไม่มี Loss of Support)"
            )
    
    st.markdown("---")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    
    with res_col1:
        if D_required and D_required <= 20:
            D_cm = inch_to_cm(D_required)
            st.metric(
                "ความหนาคำนวณ (D)",
                f"{D_required:.2f} นิ้ว",
                f"({D_cm:.1f} ซม.)"
            )
        else:
            st.metric("ความหนาคำนวณ", "> 20 นิ้ว", "ต้องปรับพารามิเตอร์")
    
    with res_col2:
        # เลือกความหนาออกแบบ (ปัดขึ้น)
        if D_required and D_required <= 20:
            D_design_inch = math.ceil(D_required * 2) / 2  # ปัดขึ้นทุก 0.5 นิ้ว
            D_design_cm = round(inch_to_cm(D_design_inch))
            
            # ปรับเป็นความหนามาตรฐาน (28, 30, 32, 35 cm)
            standard_thicknesses = [28, 30, 32, 35, 36]
            D_design_cm = min([t for t in standard_thicknesses if t >= D_design_cm], default=36)
            D_design_inch = cm_to_inch(D_design_cm)
            
            st.metric(
                "ความหนาออกแบบ",
                f"{D_design_cm} ซม.",
                f"({D_design_inch:.2f} นิ้ว)"
            )
        else:
            D_design_inch = 14
            D_design_cm = 36
            st.metric("ความหนาออกแบบ", "36 ซม.", "(ค่าสูงสุด)")
    
    with res_col3:
        # แสดง log(W18) ที่คำนวณได้
        if D_required and D_required <= 20:
            log_W18_calc = calculate_W18_rigid(D_design_inch, params)
            st.metric(
                "log₁₀(W₁₈) ออกแบบ",
                f"{log_W18_calc:.4f}",
                f"ต้องการ: {math.log10(W18_input):.4f}"
            )
    
    # ตรวจสอบ W18 ที่ออกแบบได้
    if D_required and D_required <= 20:
        log_W18_design = calculate_W18_rigid(D_design_inch, params)
        W18_design_capacity = 10 ** log_W18_design
        
        margin_percent = ((W18_design_capacity - W18_input) / W18_input) * 100
        
        st.markdown("---")
        st.subheader("✅ การตรวจสอบ")
        
        check_col1, check_col2 = st.columns(2)
        
        with check_col1:
            st.markdown(f"""
            <div class="result-box">
            <h4>W₁₈ ที่รองรับได้</h4>
            <p style="font-size: 1.5rem; font-weight: bold; color: #1E40AF;">
            {W18_design_capacity:,.0f} ESAL
            </p>
            <p class="info-text">สำหรับความหนา {D_design_cm} ซม.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with check_col2:
            if W18_design_capacity >= W18_input:
                st.markdown(f"""
                <div class="success-box">
                <h4>✓ ผ่านการตรวจสอบ</h4>
                <p>W₁₈ (ออกแบบ) = {W18_design_capacity:,.0f}</p>
                <p>W₁₈ (ต้องการ) = {W18_input:,.0f}</p>
                <p><strong>ส่วนเผื่อ: {margin_percent:.1f}%</strong></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="warning-box">
                <h4>⚠ ไม่ผ่านการตรวจสอบ</h4>
                <p>ต้องเพิ่มความหนาหรือปรับปรุงวัสดุ</p>
                </div>
                """, unsafe_allow_html=True)
    
    # แสดงตารางสรุป
    st.markdown("---")
    st.subheader("📋 สรุปโครงสร้างชั้นทาง")
    
    summary_data = []
    
    # ชั้นผิวทางคอนกรีต
    summary_data.append({
        "ลำดับ": 1,
        "ชั้นวัสดุ": f"ผิวทางคอนกรีต {pavement_type.split()[0]}",
        "ความหนา (ซม.)": D_design_cm,
        "E (MPa)": f"{Ec/145.038:,.0f}",
        "หมายเหตุ": f"f'c = {fc_selected}"
    })
    
    # ชั้นรองพื้นทาง
    for i, layer in enumerate(layers):
        summary_data.append({
            "ลำดับ": i + 2,
            "ชั้นวัสดุ": layer['name'].split('(')[0].strip(),
            "ความหนา (ซม.)": layer['thickness_cm'],
            "E (MPa)": layer['E_MPa'],
            "หมายเหตุ": ""
        })
    
    # Subgrade
    summary_data.append({
        "ลำดับ": len(layers) + 2,
        "ชั้นวัสดุ": "ดินถมคันทาง/Subgrade",
        "ความหนา (ซม.)": "∞",
        "E (MPa)": f"{MR_subgrade/145.038:.0f}",
        "หมายเหตุ": f"CBR ≥ {CBR_custom}%"
    })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # แสดงรวมความหนารองพื้นทาง
    total_subbase = sum(layer['thickness_cm'] for layer in layers)
    st.info(f"📏 รวมความหนาชั้นรองพื้นทาง = {total_subbase:.0f} ซม. ({cm_to_inch(total_subbase):.1f} นิ้ว)")
    
    # ========================
    # ส่วนวิเคราะห์เปรียบเทียบ ESAL 5 ความหนา
    # ========================
    st.markdown("---")
    st.subheader("📊 วิเคราะห์เปรียบเทียบ ESAL สำหรับความหนาต่างๆ")
    
    # กำหนดความหนามาตรฐาน 5 ระดับ
    thickness_options = [
        {"D_inch": 10, "D_cm": 25, "label": "D=10\" (25 ซม.)"},
        {"D_inch": 11, "D_cm": 28, "label": "D=11\" (28 ซม.)"},
        {"D_inch": 12, "D_cm": 30, "label": "D=12\" (30 ซม.)"},
        {"D_inch": 13, "D_cm": 32, "label": "D=13\" (32 ซม.)"},
        {"D_inch": 14, "D_cm": 35, "label": "D=14\" (35 ซม.)"},
    ]
    
    # คำนวณ W18 สำหรับแต่ละความหนา
    comparison_data = []
    for opt in thickness_options:
        D_inch = opt["D_inch"]
        D_cm = opt["D_cm"]
        
        log_W18 = calculate_W18_rigid(D_inch, params)
        W18_capacity = 10 ** log_W18
        
        # เปรียบเทียบกับ W18 ออกแบบ
        ratio = W18_capacity / W18_input
        margin_percent = (ratio - 1) * 100
        status = "✅ เพียงพอ" if W18_capacity >= W18_input else "❌ ไม่เพียงพอ"
        
        comparison_data.append({
            "ความหนา": opt["label"],
            "D (นิ้ว)": D_inch,
            "D (ซม.)": D_cm,
            "W₁₈ รองรับได้": f"{W18_capacity:,.0f}",
            "W₁₈ รองรับได้ (ล้าน)": W18_capacity / 1e6,
            "อัตราส่วน": f"{ratio:.2f}",
            "ส่วนเผื่อ (%)": f"{margin_percent:+.1f}%",
            "สถานะ": status,
            "W18_raw": W18_capacity,
        })
    
    # แสดงตาราง
    df_comparison = pd.DataFrame(comparison_data)
    
    # แสดงตารางแบบสวยงาม
    st.markdown("##### ตารางเปรียบเทียบความสามารถรองรับ ESAL")
    
    # สร้าง DataFrame สำหรับแสดง
    df_display = df_comparison[["ความหนา", "D (นิ้ว)", "D (ซม.)", "W₁₈ รองรับได้", "อัตราส่วน", "ส่วนเผื่อ (%)", "สถานะ"]].copy()
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ความหนา": st.column_config.TextColumn("ความหนา", width="medium"),
            "D (นิ้ว)": st.column_config.NumberColumn("D (นิ้ว)", format="%d"),
            "D (ซม.)": st.column_config.NumberColumn("D (ซม.)", format="%d"),
            "W₁₈ รองรับได้": st.column_config.TextColumn("W₁₈ รองรับได้ (ESAL)", width="large"),
            "อัตราส่วน": st.column_config.TextColumn("W₁₈/W₁₈ ออกแบบ"),
            "ส่วนเผื่อ (%)": st.column_config.TextColumn("ส่วนเผื่อ"),
            "สถานะ": st.column_config.TextColumn("สถานะ"),
        }
    )
    
    # แสดงกราฟเปรียบเทียบ
    st.markdown("##### กราฟเปรียบเทียบ W₁₈ ที่รองรับได้")
    
    # สร้างกราฟด้วย Streamlit
    chart_data = pd.DataFrame({
        "ความหนา (ซม.)": [opt["D_cm"] for opt in thickness_options],
        "W₁₈ รองรับได้ (ล้าน ESAL)": [d["W18_raw"] / 1e6 for d in comparison_data],
    })
    
    # เพิ่มเส้น W18 ออกแบบ
    W18_design_million = W18_input / 1e6
    
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.bar_chart(
            chart_data.set_index("ความหนา (ซม.)"),
            use_container_width=True,
        )
        st.caption(f"🔴 เส้นประ: W₁₈ ออกแบบ = {W18_design_million:,.1f} ล้าน ESAL")
    
    with col_chart2:
        # แสดงสรุป
        st.markdown("**สรุปผล:**")
        
        # หาความหนาที่เหมาะสม (เพียงพอและเล็กที่สุด)
        suitable_options = [d for d in comparison_data if d["W18_raw"] >= W18_input]
        
        if suitable_options:
            min_suitable = min(suitable_options, key=lambda x: x["D (นิ้ว)"])
            st.success(f"✅ ความหนาต่ำสุดที่เพียงพอ: **{min_suitable['D (ซม.)']} ซม.** ({min_suitable['D (นิ้ว)']} นิ้ว)")
            st.write(f"W₁₈ รองรับได้: {min_suitable['W18_raw']:,.0f} ESAL")
            st.write(f"ส่วนเผื่อ: {min_suitable['ส่วนเผื่อ (%)']}")
        else:
            st.error("❌ ไม่มีความหนาที่เพียงพอ ต้องใช้ความหนามากกว่า 14 นิ้ว")
        
        st.markdown("---")
        st.markdown(f"**W₁₈ ออกแบบ:**")
        st.markdown(f"**{W18_input:,.0f}** ESAL")
        st.markdown(f"({W18_design_million:,.1f} ล้าน)")
    
    # แสดงรายละเอียดเพิ่มเติม
    with st.expander("📈 รายละเอียดการคำนวณแต่ละความหนา"):
        for i, opt in enumerate(thickness_options):
            D_inch = opt["D_inch"]
            D_cm = opt["D_cm"]
            data = comparison_data[i]
            
            log_W18 = calculate_W18_rigid(D_inch, params)
            
            st.markdown(f"**{opt['label']}**")
            
            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.write(f"log₁₀(W₁₈) = {log_W18:.4f}")
            with detail_col2:
                st.write(f"W₁₈ = {data['W18_raw']:,.0f} ESAL")
            with detail_col3:
                st.write(f"สถานะ: {data['สถานะ']}")
            
            st.markdown("---")
    
    # แสดงพารามิเตอร์ที่ใช้
    with st.expander("📝 พารามิเตอร์ที่ใช้ในการคำนวณ"):
        param_col1, param_col2, param_col3 = st.columns(3)
        
        with param_col1:
            st.markdown(f"""
            **ค่าระดับความเชื่อมั่น**
            - Reliability (R) = {reliability}
            - Z_R = {ZR:.3f}
            - S₀ = {S0:.2f}
            """)
        
        with param_col2:
            st.markdown(f"""
            **ค่า Serviceability**
            - Pᵢ = {Pi:.1f}
            - pₜ = {pt:.1f}
            - ΔPSI = {delta_PSI:.1f}
            """)
        
        with param_col3:
            st.markdown(f"""
            **ค่าสัมประสิทธิ์**
            - J = {J:.1f}
            - Cd = {Cd:.2f}
            - LS = {LS}
            """)
            st.markdown(f"""
            **ค่า k (Modulus of Subgrade Reaction)**
            - k_subgrade = {odemark_details.get('k_subgrade', MR_subgrade/19.4):.0f} pci
            - k_composite = {k_composite:.0f} pci
            - k_effective = {k_effective:.0f} pci
            - h_equiv = {h_equiv:.2f} นิ้ว
            """)
        
        st.markdown(f"""
        **คุณสมบัติคอนกรีต**
        - f'c = {fc_selected}
        - Sc (Modulus of Rupture) = {Sc:.0f} psi
        - Ec (Elastic Modulus) = {Ec:,.0f} psi ({Ec/145.038:,.0f} MPa)
        """)

# ========================
# ส่วนข้อมูลอ้างอิง
# ========================
st.markdown("---")
with st.expander("📚 ข้อมูลอ้างอิงและสมการ"):
    st.markdown("""
    ### สมการ AASHTO 1993 สำหรับ Rigid Pavement
    
    $$\\log W_{18} = Z_R S_0 + 7.35 \\log(D+1) - 0.06 + \\frac{\\log[\\Delta PSI / (4.5-1.5)]}{1+1.624 \\times 10^7 / (D+1)^{8.46}}$$
    
    $$+ (4.22 - 0.32 p_t) \\log \\left\\{ \\frac{S_c C_d (D^{0.75} - 1.132)}{215.63 J [D^{0.75} - 18.42 / (E_c/k)^{0.25}]} \\right\\}$$
    
    ---
    
    ### Odemark's Equivalent Thickness Method
    
    การคำนวณความหนาเทียบเท่าของชั้นรองพื้นทาง:
    
    $$h_e = h \\times \\left(\\frac{E_1}{E_2}\\right)^{1/3} \\times \\left(\\frac{1-\\nu_2^2}{1-\\nu_1^2}\\right)^{1/3}$$
    
    **โดยที่:**
    - $h_e$ = ความหนาเทียบเท่า (Equivalent Thickness)
    - $h$ = ความหนาจริงของชั้นวัสดุ
    - $E_1$ = Modulus ของชั้นวัสดุที่พิจารณา
    - $E_2$ = Modulus ของชั้นรองรับ (Subgrade)
    - $\\nu$ = Poisson's ratio
    
    **การคำนวณ Composite k:**
    
    $$k_{subgrade} = \\frac{M_R}{19.4}$$
    
    $$k_{composite} = k_{subgrade} \\times f(h_{equiv}, E_{eq}/M_R)$$
    
    **การปรับแก้ Loss of Support:**
    
    $$k_{effective} = k_{composite} \\times 10^{-LS \\times 0.25}$$
    
    ---
    
    **โดยที่:**
    - $W_{18}$ = Equivalent Single Axle Load 18 kips
    - $Z_R$ = Standard Normal Deviate
    - $S_0$ = Overall Standard Deviation
    - $D$ = ความหนาแผ่นคอนกรีต (นิ้ว)
    - $\\Delta PSI$ = การสูญเสียความสามารถในการให้บริการ
    - $p_t$ = Terminal Serviceability
    - $S_c$ = Modulus of Rupture (psi)
    - $C_d$ = Drainage Coefficient
    - $J$ = Load Transfer Coefficient
    - $E_c$ = Elastic Modulus of Concrete (psi)
    - $k$ = Modulus of Subgrade Reaction (pci)
    - $LS$ = Loss of Support (0, 1, 2, 3)
    
    ### ตาราง Loss of Support (LS)
    | ประเภทชั้นรองพื้นทาง | ค่า LS |
    |:---|:---:|
    | Cement Treated Base (CTB), Lean Concrete Base (LCB) | 0.0 - 1.0 |
    | Cement Aggregate Mixture | 1.0 - 2.0 |
    | Asphalt Treated Base | 2.0 - 3.0 |
    | Bituminous Stabilized Base | 2.0 - 3.0 |
    | Granular Base | 3.0 |
    
    ### ตาราง Drainage Coefficient (Cd)
    | Quality of Drainage | < 1% | 1-5% | 5-25% | > 25% |
    |:---|:---:|:---:|:---:|:---:|
    | Excellent | 1.25-1.20 | 1.20-1.15 | 1.15-1.10 | 1.10 |
    | Good | 1.20-1.15 | 1.15-1.10 | 1.10-1.00 | 1.00 |
    | Fair | 1.15-1.10 | 1.10-1.00 | 1.00-0.90 | 0.90 |
    | Poor | 1.10-1.00 | 1.00-0.90 | 0.90-0.80 | 0.80 |
    
    ### ตาราง Load Transfer Coefficient (J)
    | Pavement Type | Asphalt Shoulder | Tied P.C.C. Shoulder |
    |:---|:---:|:---:|
    | JPCP/JRCP (with dowels) | 3.2 | 2.5-3.1 |
    | JPCP/JRCP (without dowels) | 3.8-4.4 | 3.6-4.2 |
    | CRCP | 2.9-3.2 | 2.3-2.9 |
    
    **อ้างอิง:** AASHTO Guide for Design of Pavement Structures (1993)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.9rem;">
    <p>📚 โปรแกรมสำหรับการเรียนการสอนวิศวกรรมโยธา</p>
    <p>พัฒนาตามหลักการ AASHTO Guide for Design of Pavement Structures (1993)</p>
</div>
""", unsafe_allow_html=True)
