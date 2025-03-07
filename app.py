import streamlit as st
from fpdf import FPDF
import datetime
import io
import random
import string
from collections import defaultdict

#####################################
# PDF Class for Page Numbers
#####################################
class PDF(FPDF):
    def footer(self):
        # Position the footer 15 mm from the bottom
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", 0, 0, "C")

#####################################
# Helper Data & Functions
#####################################

# Generate a short random alphanumeric ID (e.g., for Lab IDs)
def generate_id(prefix="LS", length=6):
    return prefix + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

# Generate QC Batch in the format "ABC123"
def generate_qc_batch():
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    digits = ''.join(random.choices("0123456789", k=3))
    return letters + digits

# Generate Method Blank in the format "AB12345"
def generate_method_blank():
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = ''.join(random.choices("0123456789", k=5))
    return letters + digits

# Mapping of analyte to list of possible methods
analyte_to_methods = {
    "Alkalinity": ["SM 2320 B-1997"],
    "Ammonia": ["SM 4500-NH₃ C"],
    "Bromate": ["EPA 300.1", "EPA 302.0", "EPA 317.0", "EPA 321.8", "EPA 326.0", "EPA 557.0"],
    "Bromide": ["EPA 300.0", "EPA 300.1", "EPA 317.0", "EPA 326.0"],
    "Calcium": ["EPA 200.5", "EPA 200.7", "SM 3111 B-1999", "SM 3120 B-1999", "SM 3500-Ca B-1997"],
    "Chlorate": ["EPA 300.0", "EPA 300.1"],
    "Chloride": ["EPA 300.0", "EPA 300.1", "SM 4110B-2000", "SM 4500-Cl- B-1997", "SM 4500-Cl- D-1997"],
    "Chlorine Dioxide": ["EPA 327.0", "SM 4500-ClO2 D-2000", "SM 4500-ClO2 E-2000"],
    "Chlorine, Combined": ["EPA 334.0", "SM 4500-Cl D-2000"],
    "Chlorine, Free Available": ["EPA 334.0", "SM 4500-Cl D-2000", "SM 4500-Cl E-2000", "SM 4500-Cl F-2000", "SM 4500-Cl G-2000"],
    "Chlorine, Total Residual": ["EPA 334.0", "SM 4500-Cl D-2000", "SM 4500-Cl E-2000", "SM 4500-Cl F-2000", "SM 4500-Cl G-2000"],
    "Chlorite": ["EPA 300.0", "EPA 300.1", "EPA 317.0", "EPA 326.0", "EPA 327.0", "SM 4500-ClO2 E-2000"],
    "Conductivity": ["SM 2510 B-1997"],
    "Cyanide": ["EPA 335.4", "Kelada-01 Revision 1.2", "Quickchem 10-204-00-1-X", "OIA-1677, DW"],
    "Cyanide, Total": ["SM 4500-CN E-1999", "SM 4500-CN F-1999"],
    "Cyanide, amenable": ["SM 4500-CN G-1999"],
    "Dissolved Organic Carbon DOC": ["EPA 415.3 Rev. 1.1", "EPA 415.3 Rev. 1.2"],
    "Fluoride": ["EPA 300.0", "EPA 300.1", "SM 4110B-2000", "SM 4500-F C-1997", "SM 4500-F B,D-1997", "SM 4500-F E-1997"],
    "Hardness": ["SM 2340 C-1997"],
    "Hardness (Calculation)": ["EPA 200.7", "SM 2340 B-1997", "SM 3111 B-1999", "SM 3120 B-1999"],
    "Hydrogen Ion (pH)": ["EPA 150.1", "EPA 150.2", "SM 4500-H\\+\\ B-2000"],
    "Magnesium": ["EPA 200.5", "EPA 200.7", "SM 3111 B-1999", "SM 3120 B-1999", "SM 3500-Mg B-1997"],
    "Microplastics > 500 µm": ["SWB-MP2-rev1"],
    "Microplastics >500 µm": ["SWB-MP1-rev1"],
    "Microplastics ≤212 - >20 µm": ["SWB-MP2-rev1"],
    "Microplastics ≤212 - >50 µm": ["SWB-MP1-rev1"],
    "Microplastics ≤500 - >212 µm": ["SWB-MP1-rev1", "SWB-MP2-rev1"],
    "Nickel": ["SM 3500-Ni D", "EPA 200.8"],
    "Nitrate": ["EPA 300.0", "EPA 300.1", "SM 4110B-2000", "SM 4500-NO3-D-2000", "SM 4500-NO3 E-2000", "SM 4500-NO3 F-2000", "Hach 10206"],
    "Nitrate (Calculation)": ["EPA 353.2"],
    "Nitrite": ["EPA 300.0", "EPA 300.1", "EPA 353.2", "SM 4110B-2000", "SM 4500-NO3 E-2000"],
    "Nitrite ": ["SM 4500-NO2 B-2000", "SM 4500-NO3 F-2000"],
    "Organic carbon-Dissolved (DOC)": ["SM 5310 B-2000", "SM 5310C-2000", "SM 5310D-2000"],
    "Organic carbon-Total (TOC)": ["SM 5310 B-2000", "SM 5310C-2000", "SM 5310D-2000"],
    "Perchlorate": ["EPA 314.0", "EPA 314.1", "EPA 314.2", "EPA 331.0", "EPA 332.0"],
    "Phosphate, Ortho": ["EPA 300.0", "EPA 300.1", "EPA 365.1", "SM 4110B-2000", "SM 4500-P E-1999", "SM 4500-P F -1999"],
    "Potassium": ["EPA 200.7", "SM 3111 B-1999", "SM 3120 B-1999"],
    "Residue, Filterable TDS": ["SM 2540 C-1997"],
    "Silica": ["EPA 200.5", "EPA 200.7", "SM 3120 B-1999", "SM 4500-SiO2 C-1997", "SM 4500-SiO2 D-1997", "SM 4500-SiO2 E-1997"],
    "Sodium": ["EPA 200.5", "EPA 200.7", "SM 3111 B-1999"],
    "Specific UV Absorbance SUVA": ["EPA 415.3 Rev. 1.1", "EPA 415.3 Rev. 1.2"],
    "Sulfate": ["EPA 300.0", "EPA 300.1", "EPA 375.2", "SM 4110B-2000", "SM 4500-SO4 C,D-1997", "SM 4500-SO4 E-1997", "SM 4500-SO4 F -1997"],
    "Surfactants": ["SM 5540C-2000"],
    "Total Organic Carbon TOC": ["EPA 415.3 Rev. 1.1", "EPA 415.3 Rev. 1.2"],
    "Turbidity": ["EPA 180.1", "SM 2130B-2001", "Hach 10258 Rev. 2.0"],
    "UV254": ["EPA 415.3 Rev. 1.1", "EPA 415.3 Rev. 1.2", "SM 5910B-2011"]
}

#####################################
# MAIN APP
#####################################
def main():
    st.title("Water Quality COA (Auto-Generated Fields)")

    #####################################
    # Global Auto-Generated Constants (Fixed Values)
    #####################################
    lab_name = "KELP Laboratory"
    lab_address = "520 Mercury Dr, Sunnyvale, CA 94085"
    lab_email = "kelp@ketoslab.com"
    lab_phone = "(408) 461-8860"
    
    # Auto-generated work order and COC (for cover page)
    auto_work_order = "WO" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
    auto_coc_number = "COC" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
    default_date = datetime.date.today().strftime("%m/%d/%Y")

    #####################################
    # 0. Cover Page Data
    #####################################
    if "cover_data" not in st.session_state:
        st.session_state["cover_data"] = {
            "lab_name": lab_name,
            "work_order": auto_work_order,
            "project_name": "",
            "client_name": "",
            "address_line": "",
            "phone": "",
            "date_samples_received": default_date,
            "date_reported": default_date,
            "analysis_type": "Environmental",
            "coc_number": auto_coc_number,
            "po_number": "ABS 271",
            "report_title": "CERTIFICATE OF ANALYSIS",
            "comments": "None",
            "signatory_name": "",
            "signatory_title": "Lab Manager",
        }
    st.header("Cover Page Fields (Optional Edits)")
    st.session_state["cover_data"]["project_name"] = st.text_input("Project Name", value=st.session_state["cover_data"]["project_name"])
    st.session_state["cover_data"]["client_name"] = st.text_input("Client Name", value=st.session_state["cover_data"]["client_name"])
    st.session_state["cover_data"]["address_line"] = st.text_area("Address", value=st.session_state["cover_data"]["address_line"])
    st.session_state["cover_data"]["analysis_type"] = st.text_input("Analysis Type", value=st.session_state["cover_data"]["analysis_type"])
    st.session_state["cover_data"]["comments"] = st.text_area("Comments / Narrative", value=st.session_state["cover_data"]["comments"])

    sample_type = st.selectbox("Sample Type", options=["GW", "DW", "WW", "IW", "SW"], index=0)
    if "work_order" not in st.session_state["cover_data"] or st.session_state["cover_data"]["work_order"] == auto_work_order:
        try:
            dt = datetime.datetime.strptime(st.session_state["cover_data"]["date_samples_received"], "%m/%d/%Y")
            date_str = dt.strftime("%Y%m%d")
        except:
            date_str = datetime.date.today().strftime("%Y%m%d")
        st.session_state["cover_data"]["work_order"] = f"{sample_type}-{date_str}-0001"

    st.subheader("Lab Manager Signatory")
    st.session_state["cover_data"]["signatory_name"] = st.text_input("Lab Manager Name", value=st.session_state["cover_data"]["signatory_name"])
    st.session_state["cover_data"]["signatory_title"] = st.text_input("Lab Manager Title", value=st.session_state["cover_data"]["signatory_title"])

    st.markdown("---")
    
    #####################################
    # 1. PAGE 1: SAMPLE SUMMARY
    #####################################
    if "page1_data" not in st.session_state:
        st.session_state["page1_data"] = {
            "report_id": "1064819",
            "report_date": default_date,
            "client_name": "City of Atlantic Beach",
            "client_address": "902 Assisi Lane, Atlantic Beach, FL 32233",
            "project_id": "PJ" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4)),
            "samples": []
        }
    st.header("Page 1: SAMPLE SUMMARY")
    st.subheader("Sample Summary Info (Optional Edits)")
    st.session_state["page1_data"]["report_id"] = st.text_input("Report ID (Page 1)", value=st.session_state["page1_data"]["report_id"])
    st.session_state["page1_data"]["report_date"] = st.text_input("Report Date (Page 1)", value=st.session_state["page1_data"]["report_date"])
    st.session_state["page1_data"]["client_name"] = st.text_input("Client Name (Page 1)", value=st.session_state["page1_data"]["client_name"])
    st.session_state["page1_data"]["client_address"] = st.text_input("Client Address (Page 1)", value=st.session_state["page1_data"]["client_address"])
    
    st.subheader("Add Water Sample")
    with st.form("page1_samples_form", clear_on_submit=True):
        sample_lab_id = st.text_input("Lab ID (Leave blank for auto-gen)", value="")
        sample_id = st.text_input("Sample ID", value="")
        matrix = st.text_input("Matrix", value="Water")
        sample_date_collected = st.text_input("Date Collected", value=default_date)
        sample_date_received = st.text_input("Date Received", value=default_date)
        if st.form_submit_button("Add Water Sample"):
            if not sample_lab_id.strip():
                sample_lab_id = generate_id()  # e.g., "LSAB12QF"
            st.session_state["page1_data"]["samples"].append({
                "lab_id": sample_lab_id,
                "sample_id": sample_id,
                "matrix": matrix,
                "date_collected": sample_date_collected,
                "date_received": sample_date_received
            })
    
    if st.session_state["page1_data"]["samples"]:
        st.write("**Current Water Samples (Page 1):**")
        for i, s_ in enumerate(st.session_state["page1_data"]["samples"], 1):
            st.write(f"{i}. Lab ID: {s_['lab_id']}, Sample ID: {s_['sample_id']}, Matrix: {s_['matrix']}, Collected: {s_['date_collected']}, Received: {s_['date_received']}")
    else:
        st.info("No water samples added yet.")
    
    st.markdown("---")
    
    #####################################
    # 2. PAGE 2: ANALYTICAL RESULTS
    #####################################
    if "page2_data" not in st.session_state:
        st.session_state["page2_data"] = {
            "workorder_name": st.session_state["cover_data"]["work_order"],
            "global_analysis_date": default_date + " 10:00",
            "results": [],
            "report_id": st.session_state["page1_data"]["report_id"],
            "report_date": st.session_state["page1_data"]["report_date"]
        }
    st.header("Page 2: ANALYTICAL RESULTS")
    st.subheader("Global Fields (Auto-Populated from Page 1)")
    st.text(f"Work Order: {st.session_state['page2_data']['workorder_name']}")
    st.text(f"Report ID: {st.session_state['page2_data']['report_id']}")
    st.text(f"Report Date: {st.session_state['page2_data']['report_date']}")
    st.text(f"Global Analysis Date: {st.session_state['page2_data']['global_analysis_date']}")
    
    # Dependent dropdowns outside the form for dynamic updates
    selected_parameter = st.selectbox("Parameter (Analyte)", options=list(analyte_to_methods.keys()), key="analyte")
    selected_method = st.selectbox("Analysis (Method)", options=analyte_to_methods[selected_parameter], key="method")
    
    st.subheader("Add Analytical Result (Page 2)")
    with st.form("page2_results_form", clear_on_submit=True):
        st.write(f"Selected Analyte: {selected_parameter}")
        st.write(f"Selected Method: {selected_method}")
        lab_ids = [s_["lab_id"] for s_ in st.session_state["page1_data"]["samples"]]
        if lab_ids:
            result_lab_id = st.selectbox("Select Lab ID", options=lab_ids, key="result_lab_id")
        else:
            result_lab_id = st.text_input("Lab ID", value="")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            dilution_factor = st.text_input("DF", value="")
        with col2:
            mdl_value = st.text_input("MDL", value="")
        with col3:
            pql_value = st.text_input("PQL", value="")
        with col4:
            result_value = st.text_input("Result", value="ND")
        unit_value = st.selectbox("Unit", ["mg/L", "µg/L", "µS/cm", "none"], key="unit")
        
        if st.form_submit_button("Add Analytical Result"):
            if result_lab_id:
                st.session_state["page2_data"]["results"].append({
                    "lab_id": result_lab_id,
                    "parameter": selected_parameter,
                    "analysis": selected_method,
                    "df": dilution_factor,
                    "mdl": mdl_value,
                    "pql": pql_value,
                    "result": result_value,
                    "unit": unit_value
                })
                
    if st.session_state["page2_data"]["results"]:
        st.write("**Current Analytical Results (Page 2):**")
        for i, r_ in enumerate(st.session_state["page2_data"]["results"], 1):
            st.write(f"{i}. Lab ID: {r_['lab_id']}, Parameter: {r_['parameter']}, Analysis: {r_['analysis']}, DF: {r_['df']}, MDL: {r_['mdl']}, PQL: {r_['pql']}, Result: {r_['result']} {r_['unit']}")
    else:
        st.info("No analytical results added yet.")
    
    st.markdown("---")
    
    #####################################
    # 3. PAGE 3: QUALITY CONTROL DATA
    #####################################
    if "page3_data" not in st.session_state:
        st.session_state["page3_data"] = {"qc_entries": []}
    st.header("Page 3: QUALITY CONTROL DATA")
    st.subheader("Add QC Data Entry (Page 3)")
    
    # Dependent dropdowns for QC parameter and method outside the form
    qc_selected_analyte = st.selectbox("QC Parameter (Analyte)", options=list(analyte_to_methods.keys()), key="qc_analyte")
    qc_selected_method = st.selectbox("QC Analysis (Method)", options=analyte_to_methods[qc_selected_analyte], key="qc_method")
    
    with st.form("page3_qc_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            qc_unit = st.text_input("Unit", value="mg/L")
        with col2:
            qc_mdl = st.text_input("MDL", value="0.0010")
        with col3:
            qc_pql = st.text_input("PQL", value="0.005")
        with col4:
            qc_lab_qualifier = st.text_input("Lab Qualifier", value="")
        if st.form_submit_button("Add QC Entry"):
            # Auto-generate QC Batch and Method Blank:
            qc_batch = generate_qc_batch()         # e.g., "ABC123"
            method_blank = generate_method_blank()   # e.g., "AB12345"
            st.session_state["page3_data"]["qc_entries"].append({
                "qc_batch": qc_batch,
                "qc_method": qc_selected_method,
                "parameter": qc_selected_analyte,
                "unit": qc_unit,
                "mdl": qc_mdl,
                "pql": qc_pql,
                "method_blank": method_blank,
                "lab_qualifier": qc_lab_qualifier
            })
    
    if st.session_state["page3_data"]["qc_entries"]:
        st.write("**Current QC Data (Page 3):**")
        for i, qc_ in enumerate(st.session_state["page3_data"]["qc_entries"], 1):
            st.write(
                f"{i}. QC Batch: {qc_['qc_batch']}, "
                f"Method: {qc_['qc_method']}, "
                f"Parameter: {qc_['parameter']}, "
                f"Unit: {qc_['unit']}, "
                f"MDL: {qc_['mdl']}, "
                f"PQL: {qc_['pql']}, "
                f"Method Blank: {qc_['method_blank']}, "
                f"Lab Qualifier: {qc_['lab_qualifier']}"
            )
    else:
        st.info("No QC data entries yet.")
    
    st.markdown("---")
    
    #####################################
    # 4. PAGE 4: QC DATA CROSS REFERENCE TABLE
    #####################################
    if "page4_data" not in st.session_state:
        st.session_state["page4_data"] = {"cross_refs": []}
    st.header("Page 4: QC DATA CROSS REFERENCE TABLE")
    st.subheader("Add Cross Reference Entry (Page 4)")
    with st.form("page4_qc_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cross_lab_id = st.text_input("Lab ID", value="")
        with col2:
            cross_sample_id = st.text_input("Sample ID", value="")
        col3, col4 = st.columns(2)
        with col3:
            prep_method = st.text_input("Prep Method", value="DGMj/1712")
        with col4:
            analysis_method = st.text_input("Analysis Method", value="EPA 200.8")
        col5, col6 = st.columns(2)
        with col5:
            prep_batch = st.text_input("Prep Batch", value="ICMj/1277")
        with col6:
            batch_analysis = st.text_input("Batch Analysis", value="EPA 200.8")
    
        if st.form_submit_button("Add Cross Reference (Page 4)"):
            if cross_lab_id.strip():
                st.session_state["page4_data"]["cross_refs"].append({
                    "lab_id": cross_lab_id,
                    "sample_id": cross_sample_id,
                    "prep_method": prep_method,
                    "analysis_method": analysis_method,
                    "prep_batch": prep_batch,
                    "batch_analysis": batch_analysis
                })
    
    if st.session_state["page4_data"]["cross_refs"]:
        st.write("**Current Cross References (Page 4):**")
        for i, c_ in enumerate(st.session_state["page4_data"]["cross_refs"], 1):
            st.write(
                f"{i}. Lab ID: {c_['lab_id']}, Sample ID: {c_['sample_id']}, "
                f"Prep Method: {c_['prep_method']}, Analysis Method: {c_['analysis_method']}, "
                f"Prep Batch: {c_['prep_batch']}, Batch Analysis: {c_['batch_analysis']}"
            )
    else:
        st.info("No cross references yet.")
    
    st.markdown("---")
    
    #####################################
    # 5. Generate PDF (5 pages total: Cover + 4)
    #####################################
    if st.button("Generate 5-Page COA PDF"):
        pdf_bytes = create_pdf_report(
            lab_name=lab_name,
            lab_address=lab_address,
            lab_email=lab_email,
            lab_phone=lab_phone,
            cover_data=st.session_state["cover_data"],
            page1_data=st.session_state["page1_data"],
            page2_data=st.session_state["page2_data"],
            page3_data=st.session_state["page3_data"],
            page4_data=st.session_state["page4_data"]
        )
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="MultiPage_COA_withCover.pdf",
            mime="application/pdf"
        )

#####################################
# PDF GENERATION FUNCTION
#####################################
def create_pdf_report(lab_name, lab_address, lab_email, lab_phone,
                      cover_data, page1_data, page2_data, page3_data, page4_data):
    pdf = PDF("P", "mm", "A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_text_color(0, 0, 0)
    effective_width = 180
    total_pages = 5  # cover + 4 pages

    # IMPORTANT: Use a Unicode font for characters like "₃"
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font("DejaVu", "", 10)

    
    # ---------------------------
    # 0. COVER PAGE
    # ---------------------------
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, cover_data["report_title"], ln=True, align="C")
    pdf.ln(4)
                          
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 6, lab_name, ln=True, align="R")
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, lab_address, ln=True, align="R")
    pdf.cell(0, 5, f"Email: {lab_email}   Phone: {lab_phone}", ln=True, align="R")
    pdf.ln(4)
    
    left_width = effective_width / 2
    right_width = effective_width / 2

    def table_row(label_text, data_text):
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(left_width, 6, label_text, border=1, ln=0, align="L", fill=True)
        pdf.set_font("DejaVu", "", 10)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(right_width, 6, data_text, border=1, ln=1, align="L", fill=True)

    table_row("Work Order:", cover_data["work_order"])
    table_row("Project:", cover_data["project_name"])
    table_row("Analysis Type:", cover_data["analysis_type"])
    table_row("COC #:", cover_data["coc_number"])
    table_row("PO #:", cover_data["po_number"])
    table_row("Date Samples Received:", cover_data["date_samples_received"])
    table_row("Date Reported:", cover_data["date_reported"])
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Client Name:", border=1, align="L", fill=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(effective_width - 40, 6, cover_data["client_name"], border=1, ln=True, align="L", fill=True)

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Address:", border=1, align="L", fill=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_fill_color(255, 255, 255)
    start_y = pdf.get_y()
    pdf.multi_cell(effective_width - 40, 6, cover_data["address_line"], border=1, align="L")
    end_y = pdf.get_y()
    pdf.ln(2 if (end_y - start_y) < 12 else 0)

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Phone:", border=1, align="L", fill=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(effective_width - 40, 6, cover_data["phone"], border=1, ln=True, align="L", fill=True)
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(effective_width, 6, "Comments / Case Narrative", ln=True, align="L")
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(effective_width, 5, cover_data["comments"], border=1)
    pdf.ln(4)

    pdf.set_font("DejaVu", "", 10)
    signature_text = (
        "All data for associated QC met EPA or laboratory specification(s) except where noted in the case narrative. "
        "This report supersedes any previous report(s) with this reference. Results apply to the sample(s) as submitted. "
        "This document shall not be reproduced, except in full."
    )
    pdf.multi_cell(effective_width, 5, signature_text, border=0)
    pdf.ln(2)

    current_y = pdf.get_y()
    try:
        pdf.image("lab_managersign.jpg", x=15, y=current_y, w=30)
        pdf.set_y(current_y + 15)
    except:
        pdf.cell(0, 5, "[Signature image not found]", ln=True)

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, cover_data["signatory_name"], ln=True, align="L")
    pdf.cell(0, 5, cover_data["signatory_title"], ln=True, align="L")
    signature_date = datetime.date.today().strftime("%m/%d/%Y")
    pdf.cell(0, 5, f"Date: {signature_date}", ln=True, align="L")

    # ---------------------------
    # 1. PAGE 1: SAMPLE SUMMARY
    # ---------------------------
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "SAMPLE SUMMARY", ln=True, align="C")
    pdf.ln(2)
    
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(effective_width, 6, f"Report ID: {page1_data['report_id']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Report Date: {page1_data['report_date']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Client: {page1_data['client_name']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Address: {page1_data['client_address']}", ln=True, align="L")
    pdf.ln(4)
    
    pdf.set_font("DejaVu", "B", 10)
    headers = ["Lab ID", "Sample ID", "Matrix", "Date Collected", "Date Received"]
    widths = [30, 40, 30, 40, 40]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    
    pdf.set_font("DejaVu", "", 10)
    for s_ in page1_data["samples"]:
        row_vals = [s_["lab_id"], s_["sample_id"], s_["matrix"], s_["date_collected"], s_["date_received"]]
        for val, w in zip(row_vals, widths):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)
    
    # ---------------------------
    # 2. PAGE 2: ANALYTICAL RESULTS (Separate table for each Lab ID)
    # ---------------------------
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "ANALYTICAL RESULTS", ln=True, align="C")
    pdf.ln(2)
    
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(effective_width, 6, f"Report ID: {page2_data['report_id']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Report Date: {page2_data['report_date']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Analysis Date: {page2_data['global_analysis_date']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Work Order: {page2_data['workorder_name']}", ln=True, align="L")
    pdf.ln(4)

    # Group results by lab_id
    results_by_lab_id = defaultdict(list)
    for r_ in page2_data["results"]:
        results_by_lab_id[r_["lab_id"]].append(r_)
    
    for lab_id, results_list in results_by_lab_id.items():
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 8, f"Analytical Results for Lab ID: {lab_id}", ln=True, align="L")
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        headers2 = ["Parameter", "Analysis", "DF", "MDL", "PQL", "Result", "Unit"]
        widths2 = [35, 30, 15, 15, 15, 30, 15]
        for h, w in zip(headers2, widths2):
            pdf.cell(w, 7, h, border=1, align="C", fill=True)
        pdf.ln(7)
        pdf.set_font("DejaVu", "", 10)
        for row in results_list:
            row_data = [row["parameter"], row["analysis"], row["df"], row["mdl"], row["pql"], row["result"], row["unit"]]
            for val, w in zip(row_data, widths2):
                pdf.cell(w, 7, str(val), border=1, align="C")
            pdf.ln(7)
        pdf.ln(10)
    
    # ---------------------------
    # 3. PAGE 3: QUALITY CONTROL DATA (Grouped by QC Analysis Method)
    # ---------------------------
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "QUALITY CONTROL DATA", ln=True, align="C")
    pdf.ln(2)
    
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, f"Work Order: {page2_data['workorder_name']}", ln=True, align="L")
    pdf.cell(0, 5, f"Report ID: {page2_data['report_id']}", ln=True, align="L")
    pdf.cell(0, 5, f"Report Date: {page2_data['report_date']}", ln=True, align="L")
    pdf.cell(0, 5, f"Global Analysis Date: {page2_data['global_analysis_date']}", ln=True, align="L")
    pdf.ln(5)
    
    # Group QC data by qc_method
    qc_by_method = defaultdict(list)
    for qc_ in page3_data["qc_entries"]:
        qc_by_method[qc_["qc_method"]].append(qc_)
    
    for method, qcs in qc_by_method.items():
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 5, f"QC Batch: {qcs[0]['qc_batch']}", ln=True, align="L")
        pdf.cell(0, 5, f"QC Analysis (Method): {method}", ln=True, align="L")
        pdf.cell(0, 5, f"Method Blank: {qcs[0]['method_blank']}", ln=True, align="L")
        pdf.ln(3)
    
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        headers_qc = ["Parameter", "Unit", "MDL", "PQL", "Lab Qualifier"]
        widths_qc = [40, 15, 15, 15, 30]
        for h, w in zip(headers_qc, widths_qc):
            pdf.cell(w, 7, h, border=1, align="C", fill=True)
        pdf.ln(7)
    
        pdf.set_font("DejaVu", "", 10)
        for qc_ in qcs:
            row_vals = [
                qc_["parameter"],
                qc_["unit"],
                qc_["mdl"],
                qc_["pql"],
                qc_["lab_qualifier"]
            ]
            for val, w in zip(row_vals, widths_qc):
                pdf.cell(w, 7, str(val), border=1, align="C")
            pdf.ln(7)
    
        pdf.ln(10)
    
    # ---------------------------
    # 4. PAGE 4: QC DATA CROSS REFERENCE TABLE
    # ---------------------------
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "QC DATA CROSS REFERENCE TABLE", ln=True, align="C")
    pdf.ln(2)
    
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers4 = ["Lab ID", "Sample ID", "Prep Method", "Analysis Method", "Prep Batch", "Batch Analysis"]
    widths4 = [25, 30, 30, 30, 35, 30]
    for h, w in zip(headers4, widths4):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    
    pdf.set_font("DejaVu", "", 10)
    for c_ in page4_data["cross_refs"]:
        row_vals = [
            c_["lab_id"],
            c_["sample_id"],
            c_["prep_method"],
            c_["analysis_method"],
            c_["prep_batch"],
            c_["batch_analysis"]
        ]
        for val, w in zip(row_vals, widths4):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)
    
    pdf.ln(8)
    pdf.set_font("DejaVu", "I", 8)
    pdf.multi_cell(0, 5, "This report shall not be reproduced, except in full, without the written consent of KELP Laboratory. "
                         "Test results reported relate only to the samples as received by the laboratory.")
    
    pdf.set_y(-15)
    pdf.set_font("DejaVu", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} of {total_pages}", 0, 0, "C")
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()

if __name__ == "__main__":
    main()
