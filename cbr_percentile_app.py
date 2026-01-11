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
        "เลือกไฟล์ Excel (.xlsx, .xls)",
        type=['xlsx', 'xls'],
        help="ไฟล์ควรมีคอลัมน์ Percentile และ CBR(%)"
    )
    
    st.markdown("---")
    st.markdown("### 📋 รูปแบบข้อมูลที่ต้องการ")
    st.markdown("""
    | Percentile | CBR(%) |
    |------------|--------|
    | 100.00     | 14.8   |
    | 97.22      | 14.37  |
    | ...        | ...    |
    """)

# Sample data (based on the image)
sample_data = {
    'Percentile': [100.00, 97.22, 94.44, 91.67, 88.89, 86.11, 83.33, 80.56, 
                   77.78, 75.00, 69.44, 66.67, 63.89, 61.11, 58.33, 55.56, 
                   52.78, 50.00, 47.22, 44.44, 41.67, 38.89, 36.11, 33.33,
                   30.56, 27.78, 25.00, 22.22, 19.44, 16.67, 13.89, 11.11,
                   8.33, 5.56, 2.78],
    'CBR': [14.8, 14.37, 5.31, 17.37, 5.48, 18.46, 4.85, 6.23,
            5.02, 10.78, 10.52, 14, 15.5, 8.7, 12.93, 8.19,
            8.1, 15.56, 16.88, 20.75, 20.3, 8, 7.84, 7.48,
            23.55, 8.92, 13.3, 13.5, 13.86, 7.18, 6.95, 5.8,
            6, 11.18, 9.69]
}

if uploaded_file is not None:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        # Try to identify columns
        percentile_col = None
        cbr_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'percentile' in col_lower:
                percentile_col = col
            elif 'cbr' in col_lower:
                cbr_col = col
        
        # If not found, use first two columns
        if percentile_col is None:
            percentile_col = df.columns[0]
        if cbr_col is None:
            cbr_col = df.columns[1]
        
        # Create working dataframe
        df_work = pd.DataFrame({
            'Percentile': pd.to_numeric(df[percentile_col], errors='coerce'),
            'CBR': pd.to_numeric(df[cbr_col], errors='coerce')
        }).dropna()
        
        st.success(f"✅ อ่านข้อมูลสำเร็จ: {len(df_work)} แถว")
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        st.info("กรุณาตรวจสอบรูปแบบไฟล์ Excel")
        df_work = None
else:
    st.info("📌 กรุณาอัปโหลดไฟล์ Excel หรือใช้ข้อมูลตัวอย่าง")
    use_sample = st.checkbox("ใช้ข้อมูลตัวอย่าง", value=True)
    
    if use_sample:
        df_work = pd.DataFrame(sample_data)
    else:
        df_work = None

if df_work is not None and len(df_work) > 0:
    
    # Sort by CBR for proper curve
    df_sorted = df_work.sort_values('CBR').reset_index(drop=True)
    
    # Calculate cumulative percentile (percentage of values <= each CBR)
    df_sorted['Cumulative_Percentile'] = (np.arange(1, len(df_sorted) + 1) / len(df_sorted)) * 100
    
    # Create interpolation function
    # For finding CBR at a given percentile
    f_interp = interpolate.interp1d(
        df_sorted['Cumulative_Percentile'], 
        df_sorted['CBR'],
        kind='linear',
        fill_value='extrapolate'
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
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
        # For design, we typically want CBR at (100 - percentile)
        # e.g., 90th percentile means 90% of values are >= this CBR
        design_percentile = 100 - target_percentile
        
        if design_percentile >= df_sorted['Cumulative_Percentile'].min() and \
           design_percentile <= df_sorted['Cumulative_Percentile'].max():
            cbr_at_percentile = float(f_interp(design_percentile))
        else:
            cbr_at_percentile = float(f_interp(np.clip(design_percentile, 
                                                        df_sorted['Cumulative_Percentile'].min(),
                                                        df_sorted['Cumulative_Percentile'].max())))
        
        st.markdown("---")
        st.markdown("### 📊 ผลการวิเคราะห์")
        st.metric(
            label=f"CBR ที่ Percentile {target_percentile}%",
            value=f"{cbr_at_percentile:.2f} %"
        )
        
        st.markdown("---")
        st.markdown("### 📋 สถิติข้อมูล CBR")
        st.write(f"**จำนวนตัวอย่าง:** {len(df_work)}")
        st.write(f"**ค่าต่ำสุด:** {df_work['CBR'].min():.2f} %")
        st.write(f"**ค่าสูงสุด:** {df_work['CBR'].max():.2f} %")
        st.write(f"**ค่าเฉลี่ย:** {df_work['CBR'].mean():.2f} %")
        st.write(f"**ส่วนเบี่ยงเบนมาตรฐาน:** {df_work['CBR'].std():.2f} %")
    
    with col1:
        st.markdown("### 📈 กราฟ Percentile vs CBR")
        
        # Create figure
        fig = go.Figure()
        
        # Add main curve
        fig.add_trace(go.Scatter(
            x=df_sorted['CBR'],
            y=100 - df_sorted['Cumulative_Percentile'],  # Convert to "% >= value"
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
        
        # Update layout
        fig.update_layout(
            xaxis_title="CBR (%)",
            yaxis_title="Percentile (%)",
            xaxis=dict(
                range=[0, max(df_sorted['CBR']) * 1.1],
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                range=[0, 105],
                gridcolor='lightgray',
                showgrid=True
            ),
            plot_bgcolor='white',
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            title=dict(
                text=f"รูปที่ 2-1 ค่าร้อยละ CBR ที่เปอร์เซ็นต์ไทล์ ร้อยละ {target_percentile:.0f}",
                x=0.5,
                xanchor='center'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Show data table
    st.markdown("---")
    st.markdown("### 📋 ตารางข้อมูล")
    
    # Create display table similar to the image
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.dataframe(
            df_work.head(len(df_work)//2 + 1),
            use_container_width=True,
            hide_index=True
        )
    
    with col_b:
        st.dataframe(
            df_work.tail(len(df_work)//2),
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
