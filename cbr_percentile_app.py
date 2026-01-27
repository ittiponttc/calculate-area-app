import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import interpolate
import json
import subprocess
import os

st.set_page_config(
    page_title="CBR Percentile Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("📊 การวิเคราะห์ค่า CBR ที่เปอร์เซ็นต์ไทล์")
st.markdown("### Subgrade CBR Analysis Tool")
st.markdown("---")

# Sample data (CBR values only)
sample_cbr = [14.8, 14.37, 5.31, 17.37, 5.48, 18.46, 4.85, 6.23,
              5.02, 10.78, 10.52, 14, 15.5, 8.7, 12.93, 8.19,
              8.1, 15.56, 16.88, 20.75, 20.3, 8, 7.84, 7.48,
              23.55, 8.92, 13.3, 13.5, 13.86, 7.18, 6.95, 5.8,
              6, 11.18, 9.69, 7.48]

# Sidebar for file upload
with st.sidebar:
    st.header("📁 อัปโหลดข้อมูล")
    
    # Upload JSON for settings
    st.markdown("#### 📂 โหลดการตั้งค่า")
    uploaded_json = st.file_uploader(
        "โหลดข้อมูลจากไฟล์ JSON",
        type=['json'],
        help="โหลดค่า Percentile และข้อมูล CBR จากไฟล์ JSON"
    )
    
    if uploaded_json is not None:
        try:
            loaded_data = json.load(uploaded_json)
            
            # ตรวจสอบว่าเป็นไฟล์ใหม่
            file_id = f"{uploaded_json.name}_{uploaded_json.size}"
            if st.session_state.get('last_uploaded_json') != file_id:
                st.session_state['last_uploaded_json'] = file_id
                
                # อัพเดท session_state
                if 'target_percentile' in loaded_data:
                    st.session_state['input_percentile'] = float(loaded_data['target_percentile'])
                if 'cbr_values' in loaded_data:
                    st.session_state['loaded_cbr_values'] = loaded_data['cbr_values']
                if 'use_sample' in loaded_data:
                    st.session_state['input_use_sample'] = loaded_data['use_sample']
                
                st.success("✅ โหลดการตั้งค่าสำเร็จ!")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ ไม่สามารถอ่านไฟล์ JSON ได้: {e}")
    
    st.markdown("---")
    
    # Upload Excel for CBR data
    st.markdown("#### 📊 อัปโหลดข้อมูล CBR")
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

# Process uploaded Excel file
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

elif 'loaded_cbr_values' in st.session_state and st.session_state['loaded_cbr_values']:
    # Use CBR values from loaded JSON
    cbr_values = st.session_state['loaded_cbr_values']
    st.info(f"📌 ใช้ข้อมูลจากไฟล์ JSON: {len(cbr_values)} ตัวอย่าง")

else:
    st.info("📌 กรุณาอัปโหลดไฟล์ Excel หรือใช้ข้อมูลตัวอย่าง")
    
    default_use_sample = st.session_state.get('input_use_sample', True)
    use_sample = st.checkbox(
        "ใช้ข้อมูลตัวอย่าง", 
        value=default_use_sample,
        key="input_use_sample"
    )
    
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
    
    default_percentile = st.session_state.get('input_percentile', 90.0)
    target_percentile = st.number_input(
        "Percentile ที่ต้องการ (%)",
        min_value=0.0,
        max_value=100.0,
        value=default_percentile,
        step=1.0,
        help="ใส่ค่า Percentile ที่ต้องการหาค่า CBR",
        key="input_percentile"
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
    
    # Calculate axis ranges
    x_max = max(cbr_sorted) * 1.1
    y_max = 100
    
    # Add main curve
    fig.add_trace(go.Scatter(
        x=cbr_sorted,
        y=100 - cumulative_percentile,  # Convert to "% >= value"
        mode='lines+markers',
        name='CBR Distribution',
        line=dict(color='blue', width=2),
        marker=dict(size=6, symbol='x', color='black')
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
        font=dict(size=16, color='red')
    )
    
    # Border line width (consistent for all 4 sides)
    border_width = 2
    
    # Update layout - remove axis lines, we'll draw border using shapes
    fig.update_layout(
        xaxis_title="CBR (%)",
        yaxis_title="Percentile (%)",
        xaxis=dict(
            range=[0, x_max],
            gridcolor='lightgray',
            showgrid=True,
            showline=False,  # Disable built-in axis line
            zeroline=False,
            ticks='outside',
            tickwidth=1,
            tickcolor='black',
            ticklen=5,
        ),
        yaxis=dict(
            range=[0, y_max],
            gridcolor='lightgray',
            showgrid=True,
            showline=False,  # Disable built-in axis line
            zeroline=False,
            ticks='outside',
            tickwidth=1,
            tickcolor='black',
            ticklen=5,
        ),
        plot_bgcolor='white',
        width=600,
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1
        ),
        title=dict(
            text=f"ค่าร้อยละ CBR ที่เปอร์เซ็นต์ไทล์ ร้อยละ {target_percentile:.0f}",
            x=0.5,
            xanchor='center'
        ),
        margin=dict(l=70, r=70, t=70, b=70)
    )
    
    # Draw complete border using a rectangle shape (ensures all 4 corners connect)
    fig.add_shape(
        type="rect",
        x0=0, y0=0,
        x1=x_max, y1=y_max,
        line=dict(color="black", width=border_width),
        xref="x", yref="y"
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
    
    # Export section
    st.markdown("---")
    st.markdown("### 💾 บันทึกข้อมูล")
    
    col_json, col_word = st.columns(2)
    
    with col_json:
        # Prepare export data for JSON
        export_data = {
            'target_percentile': target_percentile,
            'cbr_at_percentile': round(cbr_at_percentile, 2),
            'cbr_values': [float(v) for v in cbr_values],
            'statistics': {
                'n_samples': n,
                'min': round(float(np.min(cbr_values)), 2),
                'max': round(float(np.max(cbr_values)), 2),
                'mean': round(float(np.mean(cbr_values)), 2),
                'std': round(float(np.std(cbr_values)), 2)
            },
            'use_sample': st.session_state.get('input_use_sample', True)
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="cbr_percentile_data.json",
            mime="application/json",
            help="บันทึกข้อมูลและการตั้งค่าเป็นไฟล์ JSON"
        )
    
    with col_word:
        # Generate Word document
        if st.button("📄 สร้างรายงาน Word", help="สร้างรายงานผลการวิเคราะห์เป็นไฟล์ Word"):
            try:
                # Save chart as image first
                chart_path = "/tmp/cbr_chart.png"
                fig.write_image(chart_path, width=600, height=600, scale=2)
                
                # Create Word document using docx-js
                js_code = f'''
const {{ Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        ImageRun, AlignmentType, BorderStyle, WidthType, HeadingLevel }} = require('docx');
const fs = require('fs');

const border = {{ style: BorderStyle.SINGLE, size: 1, color: "000000" }};
const borders = {{ top: border, bottom: border, left: border, right: border }};

// Read chart image
const chartImage = fs.readFileSync("{chart_path}");

const doc = new Document({{
    styles: {{
        default: {{
            document: {{
                run: {{ font: "TH SarabunPSK", size: 32 }}
            }}
        }},
        paragraphStyles: [
            {{
                id: "Heading1",
                name: "Heading 1",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: {{ size: 36, bold: true, font: "TH SarabunPSK" }},
                paragraph: {{ spacing: {{ before: 240, after: 240 }}, alignment: AlignmentType.CENTER }}
            }},
            {{
                id: "Heading2",
                name: "Heading 2",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: {{ size: 32, bold: true, font: "TH SarabunPSK" }},
                paragraph: {{ spacing: {{ before: 180, after: 120 }} }}
            }}
        ]
    }},
    sections: [{{
        properties: {{
            page: {{
                size: {{ width: 11906, height: 16838 }},
                margin: {{ top: 1440, right: 1440, bottom: 1440, left: 1440 }}
            }}
        }},
        children: [
            new Paragraph({{
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun("รายงานผลการวิเคราะห์ค่า CBR ที่เปอร์เซ็นต์ไทล์")]
            }}),
            
            new Paragraph({{
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("ผลการวิเคราะห์")]
            }}),
            
            new Paragraph({{
                children: [
                    new TextRun({{ text: "Percentile ที่กำหนด: ", bold: true }}),
                    new TextRun("{target_percentile:.0f} %")
                ],
                spacing: {{ after: 120 }}
            }}),
            
            new Paragraph({{
                children: [
                    new TextRun({{ text: "ค่า CBR ที่ Percentile {target_percentile:.0f}%: ", bold: true }}),
                    new TextRun({{ text: "{cbr_at_percentile:.2f} %", bold: true, color: "FF0000" }})
                ],
                spacing: {{ after: 240 }}
            }}),
            
            new Paragraph({{
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("สถิติข้อมูล CBR")]
            }}),
            
            new Table({{
                width: {{ size: 50, type: WidthType.PERCENTAGE }},
                columnWidths: [4500, 4500],
                rows: [
                    new TableRow({{
                        children: [
                            new TableCell({{
                                borders,
                                width: {{ size: 4500, type: WidthType.DXA }},
                                children: [new Paragraph({{ children: [new TextRun({{ text: "รายการ", bold: true }})] }})]
                            }}),
                            new TableCell({{
                                borders,
                                width: {{ size: 4500, type: WidthType.DXA }},
                                children: [new Paragraph({{ children: [new TextRun({{ text: "ค่า", bold: true }})] }})]
                            }})
                        ]
                    }}),
                    new TableRow({{
                        children: [
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("จำนวนตัวอย่าง")] }}),
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("{n}")] }})
                        ]
                    }}),
                    new TableRow({{
                        children: [
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("ค่าต่ำสุด")] }}),
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("{np.min(cbr_values):.2f} %")] }})
                        ]
                    }}),
                    new TableRow({{
                        children: [
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("ค่าสูงสุด")] }}),
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("{np.max(cbr_values):.2f} %")] }})
                        ]
                    }}),
                    new TableRow({{
                        children: [
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("ค่าเฉลี่ย")] }}),
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("{np.mean(cbr_values):.2f} %")] }})
                        ]
                    }}),
                    new TableRow({{
                        children: [
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("ส่วนเบี่ยงเบนมาตรฐาน")] }}),
                            new TableCell({{ borders, width: {{ size: 4500, type: WidthType.DXA }}, children: [new Paragraph("{np.std(cbr_values):.2f} %")] }})
                        ]
                    }})
                ]
            }}),
            
            new Paragraph({{
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun("กราฟ Percentile vs CBR")],
                spacing: {{ before: 360 }}
            }}),
            
            new Paragraph({{
                alignment: AlignmentType.CENTER,
                children: [
                    new ImageRun({{
                        type: "png",
                        data: chartImage,
                        transformation: {{ width: 400, height: 400 }},
                        altText: {{ title: "CBR Chart", description: "CBR Percentile Chart", name: "chart" }}
                    }})
                ]
            }}),
            
            new Paragraph({{
                alignment: AlignmentType.CENTER,
                children: [new TextRun({{ text: "รูปที่ 1 กราฟแสดงความสัมพันธ์ระหว่าง Percentile และ CBR", italics: true }})],
                spacing: {{ before: 120, after: 240 }}
            }}),
            
            new Paragraph({{
                children: [new TextRun("---")],
                alignment: AlignmentType.CENTER,
                spacing: {{ before: 480 }}
            }}),
            
            new Paragraph({{
                children: [new TextRun({{ text: "พัฒนาโดย รศ.ดร.อิทธิพล มีผล", italics: true }})],
                alignment: AlignmentType.CENTER
            }}),
            new Paragraph({{
                children: [new TextRun({{ text: "ภาควิชาครุศาสตร์โยธา คณะครุศาสตร์อุตสาหกรรม มจพ.", italics: true }})],
                alignment: AlignmentType.CENTER
            }})
        ]
    }}]
}});

Packer.toBuffer(doc).then(buffer => {{
    fs.writeFileSync("/tmp/cbr_report.docx", buffer);
    console.log("Document created successfully");
}});
'''
                
                # Write JS file
                with open("/tmp/create_doc.js", "w", encoding="utf-8") as f:
                    f.write(js_code)
                
                # Run Node.js to create document
                result = subprocess.run(
                    ["node", "/tmp/create_doc.js"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and os.path.exists("/tmp/cbr_report.docx"):
                    with open("/tmp/cbr_report.docx", "rb") as f:
                        docx_data = f.read()
                    
                    st.download_button(
                        label="📥 Download Word",
                        data=docx_data,
                        file_name="cbr_percentile_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("✅ สร้างรายงาน Word สำเร็จ!")
                else:
                    st.error(f"❌ เกิดข้อผิดพลาด: {result.stderr}")
                    
            except Exception as e:
                st.error(f"❌ ไม่สามารถสร้างรายงาน Word ได้: {e}")
    
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
    <p>สำหรับการวิเคราะห์ค่า CBR ดินฐานรากตามแนวสายทาง</p>
    <p>พัฒนาโดย รศ.ดร.อิทธิพล มีผล // ภาควิชาครุศาสตร์โยธา // คณะครุศาสตร์อุตสาหกรรม // มจพ.</p>
</div>
""", unsafe_allow_html=True)
