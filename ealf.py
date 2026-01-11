import streamlit as st
"""
Truck Factor Calculator - คำนวณค่า Load Equivalency Factor (EALF)
ตามมาตรฐาน AASHTO 1993

สูตรที่ใช้:
- สมการ 2-1: Flexible Pavement (ผิวทางลาดยาง)
- สมการ 2-2: Rigid Pavement (ผิวทางคอนกรีต)

ผู้พัฒนา: รศ.ดร.อิทธิพล มีผล
"""

import math
from dataclasses import dataclass
from typing import List, Optional

# ============================================================
# ค่าคงที่
# ============================================================
TON_TO_KIP = 2.2046  # 1 metric ton = 2.2046 kip
STANDARD_AXLE_LOAD = 18  # kip (Single Axle)

# ============================================================
# Data Classes
# ============================================================
@dataclass
class Axle:
    """ข้อมูลเพลา"""
    name: str           # ชื่อเพลา (front, rear, trailer_front, trailer_rear)
    load_ton: float     # น้ำหนักลงเพลา (ตัน)
    L2: int             # ประเภทเพลา: 1=Single, 2=Tandem, 3=Tridem

@dataclass
class Truck:
    """ข้อมูลรถบรรทุก"""
    code: str           # รหัสรถ (MB, HB, MT, HT, STR, TR)
    description: str    # คำอธิบาย
    axles: List[Axle]   # รายการเพลา

# ============================================================
# ฟังก์ชันคำนวณ EALF
# ============================================================
def calc_ealf_flexible(Lx_kip: float, L2: int, pt: float, SN: int) -> float:
    """
    คำนวณ EALF สำหรับผิวทางลาดยาง (Flexible Pavement)
    สมการ 2-1 จาก AASHTO 1993
    
    Parameters:
    -----------
    Lx_kip : float - น้ำหนักลงเพลา (kip)
    L2 : int - ประเภทเพลา (1=Single, 2=Tandem, 3=Tridem)
    pt : float - Terminal Serviceability (2.0, 2.5, 3.0)
    SN : int - Structural Number (4, 5, 6, 7)
    
    Returns:
    --------
    float - ค่า EALF
    """
    if Lx_kip <= 0 or L2 <= 0:
        return 0.0
    
    # Gt = log((4.2 - pt) / (4.2 - 1.5))
    Gt = math.log10((4.2 - pt) / (4.2 - 1.5))
    
    # βx = 0.40 + 0.081 * (Lx + L2)^3.23 / ((SN + 1)^5.19 * L2^3.23)
    beta_x = 0.40 + (0.081 * ((Lx_kip + L2) ** 3.23)) / (((SN + 1) ** 5.19) * (L2 ** 3.23))
    
    # β18 = 0.40 + 0.081 * (18 + 1)^3.23 / ((SN + 1)^5.19 * 1^3.23)
    beta_18 = 0.40 + (0.081 * ((STANDARD_AXLE_LOAD + 1) ** 3.23)) / (((SN + 1) ** 5.19) * (1 ** 3.23))
    
    # log(Wtx/Wt18) = 4.79*log(19) - 4.79*log(Lx+L2) + 4.33*log(L2) + Gt/βx - Gt/β18
    log_ratio = (4.79 * math.log10(STANDARD_AXLE_LOAD + 1) 
                - 4.79 * math.log10(Lx_kip + L2) 
                + 4.33 * math.log10(L2) 
                + (Gt / beta_x) 
                - (Gt / beta_18))
    
    # EALF = 10^(-log_ratio)
    ealf = 10 ** (-log_ratio)
    return ealf


def calc_ealf_rigid(Lx_kip: float, L2: int, pt: float, D: int) -> float:
    """
    คำนวณ EALF สำหรับผิวทางคอนกรีต (Rigid Pavement)
    สมการ 2-2 จาก AASHTO 1993
    
    Parameters:
    -----------
    Lx_kip : float - น้ำหนักลงเพลา (kip)
    L2 : int - ประเภทเพลา (1=Single, 2=Tandem, 3=Tridem)
    pt : float - Terminal Serviceability (2.0, 2.5, 3.0)
    D : int - ความหนาคอนกรีต (นิ้ว)
    
    Returns:
    --------
    float - ค่า EALF
    """
    if Lx_kip <= 0 or L2 <= 0:
        return 0.0
    
    # Gt = log((4.5 - pt) / (4.5 - 1.5))
    Gt = math.log10((4.5 - pt) / (4.5 - 1.5))
    
    # βx = 1.00 + 3.63 * (Lx + L2)^5.20 / ((D + 1)^8.46 * L2^3.52)
    beta_x = 1.00 + (3.63 * ((Lx_kip + L2) ** 5.20)) / (((D + 1) ** 8.46) * (L2 ** 3.52))
    
    # β18 = 1.00 + 3.63 * (18 + 1)^5.20 / ((D + 1)^8.46 * 1^3.52)
    beta_18 = 1.00 + (3.63 * ((STANDARD_AXLE_LOAD + 1) ** 5.20)) / (((D + 1) ** 8.46) * (1 ** 3.52))
    
    # log(Wtx/Wt18) = 4.62*log(19) - 4.62*log(Lx+L2) + 3.28*log(L2) + Gt/βx - Gt/β18
    log_ratio = (4.62 * math.log10(STANDARD_AXLE_LOAD + 1) 
                - 4.62 * math.log10(Lx_kip + L2) 
                + 3.28 * math.log10(L2) 
                + (Gt / beta_x) 
                - (Gt / beta_18))
    
    # EALF = 10^(-log_ratio)
    ealf = 10 ** (-log_ratio)
    return ealf


# ============================================================
# ฟังก์ชันคำนวณ Truck Factor
# ============================================================
def calc_truck_factor_flexible(truck: Truck, pt: float, SN: int) -> float:
    """
    คำนวณ Truck Factor สำหรับ Flexible Pavement
    Truck Factor = ผลรวม EALF ของทุกเพลา
    
    Parameters:
    -----------
    truck : Truck - ข้อมูลรถบรรทุก
    pt : float - Terminal Serviceability
    SN : int - Structural Number
    
    Returns:
    --------
    float - ค่า Truck Factor
    """
    total_ealf = 0.0
    for axle in truck.axles:
        Lx_kip = axle.load_ton * TON_TO_KIP
        ealf = calc_ealf_flexible(Lx_kip, axle.L2, pt, SN)
        total_ealf += ealf
    return total_ealf


def calc_truck_factor_rigid(truck: Truck, pt: float, D: int) -> float:
    """
    คำนวณ Truck Factor สำหรับ Rigid Pavement
    Truck Factor = ผลรวม EALF ของทุกเพลา
    
    Parameters:
    -----------
    truck : Truck - ข้อมูลรถบรรทุก
    pt : float - Terminal Serviceability
    D : int - ความหนาคอนกรีต (นิ้ว)
    
    Returns:
    --------
    float - ค่า Truck Factor
    """
    total_ealf = 0.0
    for axle in truck.axles:
        Lx_kip = axle.load_ton * TON_TO_KIP
        ealf = calc_ealf_rigid(Lx_kip, axle.L2, pt, D)
        total_ealf += ealf
    return total_ealf


# ============================================================
# ฟังก์ชันสร้างข้อมูลรถบรรทุกมาตรฐาน
# ============================================================
def get_standard_trucks() -> List[Truck]:
    """
    สร้างรายการรถบรรทุก 6 ประเภทตามมาตรฐานกรมทางหลวง
    
    Returns:
    --------
    List[Truck] - รายการรถบรรทุก
    """
    trucks = [
        Truck(
            code='MB',
            description='Medium Bus',
            axles=[
                Axle(name='front', load_ton=3.1, L2=1),
                Axle(name='rear', load_ton=12.2, L2=2),
            ]
        ),
        Truck(
            code='HB',
            description='Heavy Bus',
            axles=[
                Axle(name='front', load_ton=4.0, L2=1),
                Axle(name='rear', load_ton=14.3, L2=2),
            ]
        ),
        Truck(
            code='MT',
            description='Medium Truck',
            axles=[
                Axle(name='front', load_ton=4.0, L2=1),
                Axle(name='rear', load_ton=11.0, L2=1),
            ]
        ),
        Truck(
            code='HT',
            description='Heavy Truck',
            axles=[
                Axle(name='front', load_ton=5.0, L2=1),
                Axle(name='rear', load_ton=20.0, L2=2),
            ]
        ),
        Truck(
            code='STR',
            description='Semi-Trailer',
            axles=[
                Axle(name='front', load_ton=5.0, L2=1),
                Axle(name='rear', load_ton=20.0, L2=2),
                Axle(name='trailer_rear', load_ton=20.0, L2=2),
            ]
        ),
        Truck(
            code='TR',
            description='Full Trailer',
            axles=[
                Axle(name='front', load_ton=5.0, L2=1),
                Axle(name='rear', load_ton=17.75, L2=2),
                Axle(name='trailer_front', load_ton=10.0, L2=1),
                Axle(name='trailer_rear', load_ton=17.75, L2=2),
            ]
        ),
    ]
    return trucks


# ============================================================
# ฟังก์ชันสร้างรถบรรทุกแบบกำหนดเอง
# ============================================================
def create_custom_truck(code: str, description: str, 
                        front_load: float, front_L2: int,
                        rear_load: float, rear_L2: int,
                        trailer_front_load: float = 0, trailer_front_L2: int = 0,
                        trailer_rear_load: float = 0, trailer_rear_L2: int = 0) -> Truck:
    """
    สร้างรถบรรทุกแบบกำหนดเอง
    
    Parameters:
    -----------
    code : str - รหัสรถ
    description : str - คำอธิบาย
    front_load : float - น้ำหนักเพลาหน้า (ตัน)
    front_L2 : int - ประเภทเพลาหน้า
    rear_load : float - น้ำหนักเพลาหลัง (ตัน)
    rear_L2 : int - ประเภทเพลาหลัง
    trailer_front_load : float - น้ำหนักเพลาพ่วงหน้า (ตัน)
    trailer_front_L2 : int - ประเภทเพลาพ่วงหน้า
    trailer_rear_load : float - น้ำหนักเพลาพ่วงหลัง (ตัน)
    trailer_rear_L2 : int - ประเภทเพลาพ่วงหลัง
    
    Returns:
    --------
    Truck - รถบรรทุกที่สร้างขึ้น
    """
    axles = [
        Axle(name='front', load_ton=front_load, L2=front_L2),
        Axle(name='rear', load_ton=rear_load, L2=rear_L2),
    ]
    
    if trailer_front_load > 0 and trailer_front_L2 > 0:
        axles.append(Axle(name='trailer_front', load_ton=trailer_front_load, L2=trailer_front_L2))
    
    if trailer_rear_load > 0 and trailer_rear_L2 > 0:
        axles.append(Axle(name='trailer_rear', load_ton=trailer_rear_load, L2=trailer_rear_L2))
    
    return Truck(code=code, description=description, axles=axles)


# ============================================================
# ฟังก์ชันแสดงผลลัพธ์
# ============================================================
def print_truck_info(truck: Truck):
    """แสดงข้อมูลรถบรรทุก"""
    print(f"\n{'='*60}")
    print(f"รถประเภท: {truck.code} - {truck.description}")
    print(f"{'='*60}")
    print(f"{'เพลา':<20} {'น้ำหนัก (ตัน)':<15} {'น้ำหนัก (kip)':<15} {'L2':<10}")
    print(f"{'-'*60}")
    for axle in truck.axles:
        kip = axle.load_ton * TON_TO_KIP
        l2_desc = {1: 'Single', 2: 'Tandem', 3: 'Tridem'}.get(axle.L2, '-')
        print(f"{axle.name:<20} {axle.load_ton:<15.2f} {kip:<15.3f} {axle.L2} ({l2_desc})")


def print_flexible_results(trucks: List[Truck], pt_values: List[float], sn_values: List[int]):
    """แสดงผลลัพธ์ Truck Factor สำหรับ Flexible Pavement"""
    print("\n" + "="*80)
    print("TRUCK FACTOR - FLEXIBLE PAVEMENT (ผิวทางลาดยาง)")
    print("="*80)
    
    for pt in pt_values:
        print(f"\n>>> pt = {pt}")
        print(f"{'ประเภท':<8}", end="")
        for sn in sn_values:
            print(f"{'SN='+str(sn):>12}", end="")
        print()
        print("-"*60)
        
        for truck in trucks:
            print(f"{truck.code:<8}", end="")
            for sn in sn_values:
                tf = calc_truck_factor_flexible(truck, pt, sn)
                print(f"{tf:>12.6f}", end="")
            print()


def print_rigid_results(trucks: List[Truck], pt_values: List[float], d_values: List[int]):
    """แสดงผลลัพธ์ Truck Factor สำหรับ Rigid Pavement"""
    print("\n" + "="*80)
    print("TRUCK FACTOR - RIGID PAVEMENT (ผิวทางคอนกรีต)")
    print("="*80)
    
    for pt in pt_values:
        print(f"\n>>> pt = {pt}")
        print(f"{'ประเภท':<8}", end="")
        for d in d_values:
            print(f"{'D='+str(d)+'\"':>12}", end="")
        print()
        print("-"*72)
        
        for truck in trucks:
            print(f"{truck.code:<8}", end="")
            for d in d_values:
                tf = calc_truck_factor_rigid(truck, pt, d)
                print(f"{tf:>12.6f}", end="")
            print()


def print_ealf_detail(truck: Truck, pt: float, SN: int = None, D: int = None):
    """แสดงรายละเอียดการคำนวณ EALF แต่ละเพลา"""
    print(f"\n{'='*70}")
    print(f"รายละเอียดการคำนวณ EALF - {truck.code} ({truck.description})")
    print(f"{'='*70}")
    
    if SN is not None:
        print(f"ผิวทาง: Flexible | pt = {pt} | SN = {SN}")
        print(f"{'-'*70}")
        print(f"{'เพลา':<18} {'Lx (kip)':<12} {'L2':<8} {'EALF':<15}")
        print(f"{'-'*70}")
        
        total_ealf = 0
        for axle in truck.axles:
            Lx_kip = axle.load_ton * TON_TO_KIP
            ealf = calc_ealf_flexible(Lx_kip, axle.L2, pt, SN)
            total_ealf += ealf
            print(f"{axle.name:<18} {Lx_kip:<12.3f} {axle.L2:<8} {ealf:<15.6f}")
        
        print(f"{'-'*70}")
        print(f"{'Truck Factor':<38} {total_ealf:<15.6f}")
    
    if D is not None:
        print(f"ผิวทาง: Rigid | pt = {pt} | D = {D} นิ้ว")
        print(f"{'-'*70}")
        print(f"{'เพลา':<18} {'Lx (kip)':<12} {'L2':<8} {'EALF':<15}")
        print(f"{'-'*70}")
        
        total_ealf = 0
        for axle in truck.axles:
            Lx_kip = axle.load_ton * TON_TO_KIP
            ealf = calc_ealf_rigid(Lx_kip, axle.L2, pt, D)
            total_ealf += ealf
            print(f"{axle.name:<18} {Lx_kip:<12.3f} {axle.L2:<8} {ealf:<15.6f}")
        
        print(f"{'-'*70}")
        print(f"{'Truck Factor':<38} {total_ealf:<15.6f}")


# ============================================================
# ตัวอย่างการใช้งาน
# ============================================================
if __name__ == "__main__":
    # พารามิเตอร์
    pt_values = [2.0, 2.5, 3.0]
    sn_values = [4, 5, 6, 7]
    d_values = [10, 11, 12, 13, 14]
    
    # โหลดรถบรรทุกมาตรฐาน
    trucks = get_standard_trucks()
    
    # แสดงข้อมูลรถ
    print("\n" + "#"*80)
    print("# ข้อมูลรถบรรทุก 6 ประเภท ตามมาตรฐานกรมทางหลวง")
    print("#"*80)
    for truck in trucks:
        print_truck_info(truck)
    
    # แสดงผลลัพธ์ Flexible Pavement
    print_flexible_results(trucks, pt_values, sn_values)
    
    # แสดงผลลัพธ์ Rigid Pavement
    print_rigid_results(trucks, pt_values, d_values)
    
    # แสดงรายละเอียดการคำนวณสำหรับรถ HT
    ht = trucks[3]  # Heavy Truck
    print_ealf_detail(ht, pt=2.5, SN=5)
    print_ealf_detail(ht, pt=2.5, D=10)
    
    # ตัวอย่างการสร้างรถแบบกำหนดเอง
    print("\n" + "#"*80)
    print("# ตัวอย่างการสร้างรถแบบกำหนดเอง")
    print("#"*80)
    
    custom_truck = create_custom_truck(
        code='CUSTOM',
        description='รถบรรทุกกำหนดเอง',
        front_load=5.5,      # เพลาหน้า 5.5 ตัน
        front_L2=1,          # เดี่ยว
        rear_load=22.0,      # เพลาหลัง 22 ตัน
        rear_L2=2,           # คู่
        trailer_rear_load=18.0,  # พ่วงหลัง 18 ตัน
        trailer_rear_L2=2        # คู่
    )
    
    print_truck_info(custom_truck)
    print_ealf_detail(custom_truck, pt=2.5, SN=5)
    print_ealf_detail(custom_truck, pt=2.5, D=10)
    
    # คำนวณค่าเดี่ยว
    print("\n" + "#"*80)
    print("# ตัวอย่างการคำนวณค่า EALF เดี่ยว")
    print("#"*80)
    
    # คำนวณ EALF สำหรับเพลาเดี่ยว 20 ตัน
    load_kip = 20 * TON_TO_KIP
    ealf_flex = calc_ealf_flexible(Lx_kip=load_kip, L2=2, pt=2.5, SN=5)
    ealf_rigid = calc_ealf_rigid(Lx_kip=load_kip, L2=2, pt=2.5, D=10)
    
    print(f"\nน้ำหนักเพลา: 20 ตัน ({load_kip:.3f} kip), L2=2 (Tandem)")
    print(f"EALF (Flexible, pt=2.5, SN=5): {ealf_flex:.6f}")
    print(f"EALF (Rigid, pt=2.5, D=10\"): {ealf_rigid:.6f}")
