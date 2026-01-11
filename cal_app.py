st.title("โปรแกรมคำนวณพื้นที่สี่เหลี่ยม")

# รับค่า input
width = st.number_input("กว้าง (เมตร)", min_value=0.0, value=10.0)
length = st.number_input("ยาว (เมตร)", min_value=0.0, value=20.0)

# คำนวณ
area = width * length

# แสดงผล
st.success(f"พื้นที่ = {area:,.2f} ตร.ม.")

