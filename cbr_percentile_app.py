import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import interpolate

st.set_page_config(
    page_title="CBR Percentile Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("📊 การวิเคราะห์ค่า CBR ที่เปอร์เซ็นต์ไทล์")
st.markdown("### Subgrade CBR Analysis Tool")
st.markdown("---")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 อัปโหลดข้อมูล")
    uploaded_file = st.file_uploader(
        "เลือกไฟล์ Excel (.xlsx)",
        type=['xlsx'],
        help="ไฟล์ควรมีคอลัมน์ CBR(%) เพียงคอลัมน์เดียว"
    )
    
    st.markdown("---")
    st.markdown("### 📋 รูปแบบข้อมูลที่ต้องการ")
    st.markdown("""
    | CBR(%) |
    |--------|
    | 14.8   |
    | 14.37  |
    | 5.31   |
    | ...    |
    """)
    st.info("ระบบจะคำนวณ Percentile ให้อัตโนมัติ")

# Sample data (CBR values only)
sample_cbr = [14.8, 14.37, 5.31, 17.37, 5.48, 18.46, 4.85, 6.23,
              5.02, 10.78, 10.52, 14, 15.5, 8.7, 12.93, 8.19,
              8.1, 15.56, 16.88, 20.75, 20.3, 8, 7.84, 7.48,
              23.55, 8.92, 13.3, 13.5, 13.86, 7.18, 6.95, 5.8,
              6, 11.18, 9.69, 7.48]

if uploaded_file is not None:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        # Try to identify CBR column
        cbr_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'cbr' in col_lower:
                cbr_col = col
                break
        
        # If not found, use first column
        if cbr_col is None:
            cbr_col = df.columns[0]
        
        # Get CBR values
        cbr_values = pd.to_numeric(df[cbr_col], errors='coerce').dropna().tolist()
        
        st.success(f"✅ อ่านข้อมูลสำเร็จ: {len(cbr_values)} ตัวอย่าง")
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        st.info("กรุณาตรวจสอบรูปแบบไฟล์ Excel")
        cbr_values = None
else:
    st.info("📌 กรุณาอัปโหลดไฟล์ Excel หรือใช้ข้อมูลตัวอย่าง")
    use_sample = st.checkbox("ใช้ข้อมูลตัวอย่าง", value=True)
    
    if use_sample:
        cbr_values = sample_cbr
    else:
        cbr_values = None

if cbr_values is not None and len(cbr_values) > 0:
    
    # Sort CBR values
    cbr_sorted = np.sort(cbr_values)
    n = len(cbr_sorted)
    
    # Calculate cumulative percentile (percentage of values <= each CBR)
    cumulative_percentile = (np.arange(1, n + 1) / n) * 100
    
    # Create dataframe for display
    df_sorted = pd.DataFrame({
        'CBR': cbr_sorted,
        'Cumulative_Percentile': cumulative_percentile
    })
    
    # Create interpolation function
    f_interp = interpolate.interp1d(
        cumulative_percentile, 
        cbr_sorted,
        kind='linear',
        fill_value='extrapolate'
    )
    
    # Input percentile at the top
    st.markdown("### 🎯 กำหนดค่า Percentile")
    target_percentile = st.number_input(
        "Percentile ที่ต้องการ (%)",
        min_value=0.0,
        max_value=100.0,
        value=90.0,
        step=1.0,
        help="ใส่ค่า Percentile ที่ต้องการหาค่า CBR"
    )
    
    # Calculate CBR at target percentile
    design_percentile = 100 - target_percentile
    
    if design_percentile >= cumulative_percentile.min() and \
       design_percentile <= cumulative_percentile.max():
        cbr_at_percentile = float(f_interp(design_percentile))
    else:
        cbr_at_percentile = float(f_interp(np.clip(design_percentile, 
                                                    cumulative_percentile.min(),
                                                    cumulative_percentile.max())))
    
    st.markdown("---")
    
    # Graph section - full width
    st.markdown("### 📈 กราฟ Percentile vs CBR")
    
    # Create figure
    fig = go.Figure()
    
    # Add main curve
    fig.add_trace(go.Scatter(
        x=cbr_sorted,
        y=100 - cumulative_percentile,  # Convert to "% >= value"
        mode='lines+markers',
        name='CBR Distribution',
        line=dict(color='blue', width=2),
        marker=dict(size=6, symbol='x', color='blue')
    ))
    
    # Add horizontal red dashed line at target percentile
    fig.add_trace(go.Scatter(
        x=[0, cbr_at_percentile],
        y=[target_percentile, target_percentile],
        mode='lines',
        name=f'Percentile {target_percentile}%',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Add vertical red dashed line at CBR value
    fig.add_trace(go.Scatter(
        x=[cbr_at_percentile, cbr_at_percentile],
        y=[0, target_percentile],
        mode='lines',
        name=f'CBR = {cbr_at_percentile:.2f}%',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Add annotation for CBR value
    fig.add_annotation(
        x=cbr_at_percentile,
        y=0,
        text=f"<b>{cbr_at_percentile:.2f}</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='red',
        ax=0,
        ay=40,
        font=dict(size=14, color='red')
    )
    
    # Update layout with black border and square aspect ratio
    fig.update_layout(
        xaxis_title="CBR (%)",
        yaxis_title="Percentile (%)",
        xaxis=dict(
            range=[0, max(cbr_sorted) * 1.1],
            gridcolor='lightgray',
            showgrid=True,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            constrain='domain'
        ),
        yaxis=dict(
            range=[0, 105],
            gridcolor='lightgray',
            showgrid=True,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            scaleanchor='x',
            scaleratio=105 / (max(cbr_sorted) * 1.1)
        ),
        plot_bgcolor='white',
        width=600,
        height=1000,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        title=dict(
            text=f"ค่าร้อยละ CBR ที่เปอร์เซ็นต์ไทล์ ร้อยละ {target_percentile:.0f}",
            x=0.5,
            xanchor='center'
        )
    )
    
    # Center the chart
    col_left, col_chart, col_right = st.columns([1, 2, 1])
    with col_chart:
        st.plotly_chart(fig, use_container_width=False)
    
    # Results section - below the graph
    st.markdown("---")
    
    col_result, col_stat = st.columns(2)
    
    with col_result:
        st.markdown("### 📊 ผลการวิเคราะห์")
        st.metric(
            label=f"CBR ที่ Percentile {target_percentile}%",
            value=f"{cbr_at_percentile:.2f} %"
        )
    
    with col_stat:
        st.markdown("### 📋 สถิติข้อมูล CBR")
        st.write(f"**จำนวนตัวอย่าง:** {n}")
        st.write(f"**ค่าต่ำสุด:** {np.min(cbr_values):.2f} %")
        st.write(f"**ค่าสูงสุด:** {np.max(cbr_values):.2f} %")
        st.write(f"**ค่าเฉลี่ย:** {np.mean(cbr_values):.2f} %")
        st.write(f"**ส่วนเบี่ยงเบนมาตรฐาน:** {np.std(cbr_values):.2f} %")
    
    # Show data table
    st.markdown("---")
    st.markdown("### 📋 ตารางข้อมูล (เรียงตาม CBR)")
    
    # Create display table with calculated percentile
    df_display = pd.DataFrame({
        'ลำดับ': range(1, n + 1),
        'CBR (%)': cbr_sorted,
        'Percentile (%)': np.round(100 - cumulative_percentile, 2)
    })
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.dataframe(
            df_display.head(len(df_display)//2 + 1),
            use_container_width=True,
            hide_index=True
        )
    
    with col_b:
        st.dataframe(
            df_display.tail(len(df_display)//2),
            use_container_width=True,
            hide_index=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>พัฒนาสำหรับการวิเคราะห์ค่า CBR ดินฐานรากตามแนวสายทาง</p>
    <p>ภาควิชาครุศาสตร์โยธา คณะครุศาสตร์อุตสาหกรรม มจพ.</p>
</div>
""", unsafe_allow_html=True)
