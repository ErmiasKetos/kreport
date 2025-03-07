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
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", 0, 0, "C")

#####################################
# Helper Functions
#####################################
def generate_id(prefix="LS", length=6):
    return prefix + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

def generate_qc_batch():
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    digits = ''.join(random.choices("0123456789", k=3))
    return letters + digits

def generate_method_blank():
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = ''.join(random.choices("0123456789", k=5))
    return letters + digits

def generate_coc_number():
    return "COC-" + ''.join(random.choices("0123456789", k=6))

def generate_po_number():
    return "PO-KL" + datetime.datetime.today().strftime("%Y%m") + ''.join(random.choices("0123456789", k=4))

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
    "Chlorine, Combined": ["EPA 334.0", "SM 4500-Cl D-1997"],
    "Chlorine, Free Available": ["EPA 334.0", "SM 4500-Cl D-1997", "SM 4500-Cl E-1997", "SM 4500-Cl F-1997", "SM 4500-Cl G-1997"],
    "Chlorine, Total Residual": ["EPA 334.0", "SM 4500-Cl D-1997", "SM 4500-Cl E-1997", "SM 4500-Cl F-1997", "SM 4500-Cl G-1997"],
    "Chlorite": ["EPA 300.0", "EPA 300.1", "EPA 317.0", "EPA 326.0", "EPA 327.0", "SM 4500-ClO2 E-1997"],
    "Conductivity": ["SM 2510 B-1997"],
    "Cyanide": ["EPA 335.4", "Kelada-01 Revision 1.2", "Quickchem 10-204-00-1-X", "OIA-1677, DW"],
    "Cyanide, Total": ["SM 4500-CN E-1999", "SM 4500-CN F-1999"],
    "Cyanide, amenable": ["SM 4500-CN G-1999"],
    "Dissolved Organic Carbon DOC": ["EPA 415.3 Rev. 1.1", "EPA 415.3 Rev. 1.2"],
    "Fluoride": ["EPA 300.0", "EPA 300.1", "SM 4110B-2000", "SM 4500-F C-1997", "SM 4500-F B,D-1997", "SM 4500-F E-1997"],
    "Hardness": ["SM 2340 C-1997"],
    "Hardness (Calculation)": ["EPA 200.7", "SM 2340 B-1997", "SM 3111 B-1999", "SM 3120 B-1999"],
    "Hydrogen Ion (pH)": ["EPA 150.1", "EPA 150.2", "SM 4500-H\\+\\ B-1997"],
    "Magnesium": ["EPA 200.5", "EPA 200.7", "SM 3111 B-1999", "SM 3120 B-1999", "SM 3500-Mg B-1997"],
    "Microplastics > 500 µm": ["SWB-MP2-rev1"],
    "Microplastics >500 µm": ["SWB-MP1-rev1"],
    "Microplastics ≤212 - >20 µm": ["SWB-MP2-rev1"],
    "Microplastics ≤212 - >50 µm": ["SWB-MP1-rev1"],
    "Microplastics ≤500 - >212 µm": ["SWB-MP1-rev1", "SWB-MP2-rev1"],
    "Nickel": ["SM 3500-Ni D", "EPA 200.8"],
    "Nitrate": ["EPA 300.0", "EPA 300.1", "SM 4110B-2000", "SM 4500-NO3-D-1997", "SM 4500-NO3 E-1997", "SM 4500-NO3 F-1997", "Hach 10206"],
    "Nitrate (Calculation)": ["EPA 353.2"],
    "Nitrite": ["EPA 300.0", "EPA 300.1", "EPA 353.2", "SM 4110B-2000", "SM 4500-NO3 E-1997"],
    "Nitrite ": ["SM 4500-NO2 B-1997", "SM 4500-NO3 F-1997"],
    "Organic carbon-Dissolved (DOC)": ["SM 5310 B-2000", "SM 5310C-2000", "SM 5310D-2000"],
    "Organic carbon-Total (TOC)": ["SM 5310 B-2000", "SM 5310C-2000", "SM 5310D-2000"],
    "Perchlorate": ["EPA 314.0", "EPA 314.1", "EPA 314.2", "EPA 331.0", "EPA 332.0"],
    "Phosphate, Ortho": ["EPA 300.0", "EPA 300.1", "EPA 365.1", "SM 4110B-2000", "SM 4500-P E-1997", "SM 4500-P F -1997"],
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
# NAVIGATION PAGES
#####################################
PAGES = ["Cover Page", "Sample Summary", "Analytical Results", "Quality Control Data"]

#####################################
# Initialize session state
#####################################
if "current_page" not in st.session_state:
    st.session_state.current_page = 0

# Ensure cover_data is present
if "cover_data" not in st.session_state:
    st.session_state["cover_data"] = {}

# Ensure page1_data is present
if "page1_data" not in st.session_state:
    st.session_state["page1_data"] = {}

# Ensure page2_data is present
if "page2_data" not in st.session_state:
    st.session_state["page2_data"] = {}

# Ensure page3_data is present
if "page3_data" not in st.session_state:
    st.session_state["page3_data"] = {}

#####################################
# Render Navbar (Top Buttons)
#####################################
def render_navbar():
    st.markdown(
        """
        <style>
        .progress-bar-container {
            width: 100%;
            background-color: #ddd;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 16px;
        }
        .progress-bar-fill {
            height: 16px;
            background: linear-gradient(90deg, #2196F3, #4CAF50);
            width: 0%;
            transition: width 0.5s ease;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    progress = int((st.session_state.current_page + 1) / len(PAGES) * 100)
    st.markdown(f"""
    <div class="progress-bar-container">
      <div class="progress-bar-fill" style="width: {progress}%"></div>
    </div>
    """, unsafe_allow_html=True)

    # Create columns for the top navbar
    nav_cols = st.columns(len(PAGES))
    for i, page_name in enumerate(PAGES):
        # Each nav button has a unique key = nav_btn_i
        if nav_cols[i].button(page_name, key=f"nav_btn_{i}"):
            st.session_state.current_page = i

#####################################
# Render Next/Back Buttons
#####################################
def render_nav_buttons():
    # Use random suffix to ensure unique keys each time
    random_suffix = ''.join(random.choices("0123456789", k=5))
    col1, col2 = st.columns(2)
    if st.session_state.current_page > 0:
        if col1.button("Back", key=f"back_btn_{random_suffix}"):
            st.session_state.current_page -= 1
    if st.session_state.current_page < len(PAGES) - 1:
        if col2.button("Next", key=f"next_btn_{random_suffix}"):
            st.session_state.current_page += 1

#####################################
# Page: Cover
#####################################
def render_cover_page():
    st.header("Cover Page Fields (Optional Edits)")
    default_date = datetime.date.today().strftime("%m/%d/%Y")

    # If not set, initialize st.session_state["cover_data"] with defaults
    cover = st.session_state["cover_data"]
    if not cover:
        cover["lab_name"] = "KELP Laboratory"
        cover["work_order"] = "WO" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        cover["project_name"] = ""
        cover["client_name"] = ""
        cover["street"] = ""
        cover["city"] = ""
        cover["state"] = ""
        cover["zip"] = ""
        cover["country"] = ""
        cover["phone"] = ""
        cover["date_samples_received"] = default_date
        cover["date_reported"] = default_date
        cover["analysis_type"] = "Environmental"
        cover["coc_number"] = generate_coc_number()
        cover["po_number"] = generate_po_number()
        cover["report_title"] = "CERTIFICATE OF ANALYSIS"
        cover["comments"] = "None"
        cover["signatory_name"] = ""
        cover["signatory_title"] = "Lab Manager"

    # Editable fields
    cover["project_name"] = st.text_input("Project Name", value=cover.get("project_name", ""))
    cover["client_name"] = st.text_input("Client Name", value=cover.get("client_name", ""))
    cover["street"] = st.text_input("Street Address", value=cover.get("street", ""))
    cover["city"] = st.text_input("City", value=cover.get("city", ""))
    cover["state"] = st.text_input("State/Province/Region", value=cover.get("state", ""))
    cover["zip"] = st.text_input("Postal/Zip Code", value=cover.get("zip", ""))
    cover["country"] = st.text_input("Country", value=cover.get("country", ""))
    cover["analysis_type"] = st.text_input("Analysis Type", value=cover.get("analysis_type", "Environmental"))
    cover["comments"] = st.text_area("Comments / Narrative", value=cover.get("comments", "None"))

    # Rebuild address line
    cover["address_line"] = (
        cover["street"] + ", " +
        cover["city"] + ", " +
        cover["state"] + " " +
        cover["zip"] + ", " +
        cover["country"]
    )

    sample_type = st.selectbox("Sample Type", options=["GW", "DW", "WW", "IW", "SW"], index=0)
    try:
        dt = datetime.datetime.strptime(cover["date_samples_received"], "%m/%d/%Y")
        date_str = dt.strftime("%Y%m%d")
    except:
        date_str = datetime.date.today().strftime("%Y%m%d")
    cover["work_order"] = f"{sample_type}-{date_str}-0001"

    st.subheader("Lab Manager Signatory")
    cover["signatory_name"] = st.text_input("Lab Manager Name", value=cover.get("signatory_name", ""))
    cover["signatory_title"] = st.text_input("Lab Manager Title", value=cover.get("signatory_title", "Lab Manager"))

    render_nav_buttons()

#####################################
# Page 1: SAMPLE SUMMARY
#####################################
def render_sample_summary_page():
    page1 = st.session_state["page1_data"]
    if not page1:
        page1["report_id"] = "".join(random.choices("0123456789", k=7))
        page1["report_date"] = datetime.date.today().strftime("%m/%d/%Y")
        page1["client_name"] = st.session_state["cover_data"].get("client_name", "")
        page1["client_address"] = st.session_state["cover_data"].get("address_line", "")
        page1["project_id"] = "PJ" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        page1["samples"] = []

    st.header("Page 1: SAMPLE SUMMARY")

    with st.form("page1_samples_form", clear_on_submit=True):
        sample_lab_id = st.text_input("Lab ID (Leave blank for auto-gen)", value="")
        sample_id = st.text_input("Sample ID", value="")
        matrix = st.text_input("Matrix", value="Water")
        sample_date_collected = st.text_input("Date Collected", value=datetime.date.today().strftime("%m/%d/%Y"))
        sample_date_received = st.text_input("Date Received", value=datetime.date.today().strftime("%m/%d/%Y"))
        if st.form_submit_button("Add Water Sample"):
            if not sample_lab_id.strip():
                sample_lab_id = generate_id()
            page1["samples"].append({
                "lab_id": sample_lab_id,
                "sample_id": sample_id,
                "matrix": matrix,
                "date_collected": sample_date_collected,
                "date_received": sample_date_received
            })

    st.write("**Current Water Samples (Page 1):**")
    if page1["samples"]:
        for i, s_ in enumerate(page1["samples"], 1):
            st.write(f"{i}. Lab ID: {s_['lab_id']}, Sample ID: {s_['sample_id']}, Matrix: {s_['matrix']}, Collected: {s_['date_collected']}, Received: {s_['date_received']}")
    else:
        st.info("No water samples added yet.")

    render_nav_buttons()

#####################################
# Page 2: ANALYTICAL RESULTS
#####################################
def render_analytical_results_page():
    page2 = st.session_state["page2_data"]
    if not page2:
        page2["workorder_name"] = st.session_state["cover_data"].get("work_order", "WO-UNKNOWN")
        page2["global_analysis_date"] = datetime.date.today().strftime("%m/%d/%Y") + " 10:00"
        page2["results"] = []
        # Tie these to page1_data if needed
        page2["report_id"] = st.session_state["page1_data"].get("report_id", "0000000")
        page2["report_date"] = st.session_state["page1_data"].get("report_date", datetime.date.today().strftime("%m/%d/%Y"))

    st.header("Page 2: ANALYTICAL RESULTS")
    st.text(f"Work Order: {page2['workorder_name']}")
    st.text(f"Report ID: {page2['report_id']}")
    st.text(f"Report Date: {page2['report_date']}")
    st.text(f"Global Analysis Date: {page2['global_analysis_date']}")

    selected_parameter = st.selectbox("Parameter (Analyte)", options=list(analyte_to_methods.keys()), key="analyte")
    selected_method = st.selectbox("Analysis (Method)", options=analyte_to_methods[selected_parameter], key="method")

    with st.form("page2_results_form", clear_on_submit=True):
        st.write(f"Selected Analyte: {selected_parameter}")
        st.write(f"Selected Method: {selected_method}")

        lab_ids = [s_["lab_id"] for s_ in st.session_state["page1_data"].get("samples", [])]
        if lab_ids:
            result_lab_id = st.selectbox("Select Lab ID", options=lab_ids, key="result_lab_id")
            sample_id_val = next((s["sample_id"] for s in st.session_state["page1_data"]["samples"] if s["lab_id"] == result_lab_id), "")
            st.text(f"Corresponding Sample ID: {sample_id_val}")
        else:
            result_lab_id = st.text_input("Lab ID", value="")
            sample_id_val = ""

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
                page2["results"].append({
                    "lab_id": result_lab_id,
                    "sample_id": sample_id_val,
                    "parameter": selected_parameter,
                    "analysis": selected_method,
                    "df": dilution_factor,
                    "mdl": mdl_value,
                    "pql": pql_value,
                    "result": result_value,
                    "unit": unit_value
                })

    st.write("**Current Analytical Results (Page 2):**")
    if page2["results"]:
        for i, r_ in enumerate(page2["results"], 1):
            st.write(f"{i}. Lab ID: {r_['lab_id']}, Sample ID: {r_.get('sample_id','')}, Parameter: {r_['parameter']}, Analysis: {r_['analysis']}, DF: {r_['df']}, MDL: {r_['mdl']}, PQL: {r_['pql']}, Result: {r_['result']} {r_['unit']}")
    else:
        st.info("No analytical results added yet.")

    render_nav_buttons()

#####################################
# Page 3: QUALITY CONTROL
#####################################
def render_quality_control_page():
    page3 = st.session_state["page3_data"]
    if not page3:
        page3["qc_entries"] = []

    st.header("Page 3: QUALITY CONTROL DATA")

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
        qc_method_blank_conc = st.text_input("Method Blank Conc.", value="")

        if st.form_submit_button("Add QC Entry"):
            qc_batch = generate_qc_batch()
            method_blank = generate_method_blank()
            page3["qc_entries"].append({
                "qc_batch": qc_batch,
                "qc_method": qc_selected_method,
                "parameter": qc_selected_analyte,
                "unit": qc_unit,
                "mdl": qc_mdl,
                "pql": qc_pql,
                "blank_result": qc_method_blank_conc,
                "lab_qualifier": qc_lab_qualifier,
                "method_blank": method_blank
            })

    st.write("**Current QC Data (Page 3):**")
    if page3["qc_entries"]:
        for i, qc_ in enumerate(page3["qc_entries"], 1):
            st.write(
                f"{i}. QC Batch: {qc_['qc_batch']}, Method: {qc_['qc_method']}, Parameter: {qc_['parameter']}, "
                f"Unit: {qc_['unit']}, MDL: {qc_['mdl']}, PQL: {qc_['pql']}, Method Blank Conc.: {qc_['blank_result']}, "
                f"Lab Qualifier: {qc_['lab_qualifier']}"
            )
    else:
        st.info("No QC data entries yet.")

    render_nav_buttons()

#####################################
# PDF GENERATION
#####################################
def create_pdf_report(lab_name, lab_address, lab_email, lab_phone,
                      cover_data, page1_data, page2_data, page3_data):
    pdf = PDF("P", "mm", "A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_text_color(0, 0, 0)
    effective_width = 180
    total_pages = 4

    # Load DejaVu fonts if you have them:
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "DejaVuSans-Italic.ttf", uni=True)
    pdf.set_font("DejaVu", "", 10)

    # (Cover Page, Sample Summary, Analytical Results, Quality Control)
    # ---------------------------
    # 0. COVER PAGE
    # ---------------------------
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, cover_data.get("report_title", "CERTIFICATE OF ANALYSIS"), ln=True, align="C")
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

    table_row("Work Order:", cover_data.get("work_order", ""))
    table_row("Project:", cover_data.get("project_name", ""))
    table_row("Analysis Type:", cover_data.get("analysis_type", ""))
    table_row("COC #:", cover_data.get("coc_number", ""))
    table_row("PO #:", cover_data.get("po_number", ""))
    table_row("Date Samples Received:", cover_data.get("date_samples_received", ""))
    table_row("Date Reported:", cover_data.get("date_reported", ""))
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Client Name:", border=1, align="L", fill=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(effective_width - 40, 6, cover_data.get("client_name", ""), border=1, ln=True, align="L", fill=True)

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Address:", border=1, align="L", fill=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_fill_color(255, 255, 255)
    address_line = cover_data.get("address_line", "")
    pdf.multi_cell(effective_width - 40, 6, address_line, border=1, align="L")
    pdf.ln(2)

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Phone:", border=1, align="L", fill=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(effective_width - 40, 6, cover_data.get("phone", ""), border=1, ln=True, align="L", fill=True)
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(effective_width, 6, "Comments / Case Narrative", ln=True, align="L")
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(effective_width, 5, cover_data.get("comments", ""), border=1)
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
    pdf.cell(0, 5, cover_data.get("signatory_name", ""), ln=True, align="L")
    pdf.cell(0, 5, cover_data.get("signatory_title", ""), ln=True, align="L")
    signature_date = datetime.date.today().strftime("%m/%d/%Y")
    pdf.cell(0, 5, f"Date: {signature_date}", ln=True, align="L")

    # PAGE 1: SAMPLE SUMMARY
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "SAMPLE SUMMARY", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(effective_width, 6, f"Report ID: {page1_data.get('report_id', '')}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Report Date: {page1_data.get('report_date', '')}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Client: {cover_data.get('client_name', '')}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Address: {cover_data.get('address_line', '')}", ln=True, align="L")
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 10)
    headers = ["Lab ID", "Sample ID", "Matrix", "Date Collected", "Date Received"]
    widths = [30, 40, 30, 40, 40]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)

    pdf.set_font("DejaVu", "", 10)
    for s_ in page1_data.get("samples", []):
        row_vals = [s_["lab_id"], s_["sample_id"], s_["matrix"], s_["date_collected"], s_["date_received"]]
        for val, w in zip(row_vals, widths):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # PAGE 2: ANALYTICAL RESULTS
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "ANALYTICAL RESULTS", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(effective_width, 6, f"Report ID: {page2_data.get('report_id', '')}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Report Date: {page2_data.get('report_date', '')}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Analysis Date: {page2_data.get('global_analysis_date', '')}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Work Order: {page2_data.get('workorder_name', '')}", ln=True, align="L")
    pdf.ln(4)

    from collections import defaultdict
    results_by_lab = defaultdict(list)
    for r_ in page2_data.get("results", []):
        key = (r_["lab_id"], r_.get("sample_id", ""))
        results_by_lab[key].append(r_)

    widths2 = [40, 35, 20, 20, 20, 30, 15]
    for (lab_id, sample_id), results_list in results_by_lab.items():
        header_text = f"Analytical Results for Lab ID: {lab_id}"
        if sample_id:
            header_text += f" ( Sample ID: {sample_id} )"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 8, header_text, ln=True, align="L")
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        heads2 = ["Parameter", "Analysis", "DF", "MDL", "PQL", "Result", "Unit"]
        for h, w in zip(heads2, widths2):
            pdf.cell(w, 7, h, border=1, align="C", fill=True)
        pdf.ln(7)
        pdf.set_font("DejaVu", "", 10)
        for row in results_list:
            row_data = [row["parameter"], row["analysis"], row["df"], row["mdl"], row["pql"], row["result"], row["unit"]]
            for val, w in zip(row_data, widths2):
                pdf.cell(w, 7, str(val), border=1, align="C")
            pdf.ln(7)
        pdf.ln(10)

    # PAGE 3: QUALITY CONTROL
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "QUALITY CONTROL DATA", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, f"Work Order: {page2_data.get('workorder_name','')}", ln=True, align="L")
    pdf.cell(0, 5, f"Report ID: {page2_data.get('report_id','')}", ln=True, align="L")
    pdf.cell(0, 5, f"Report Date: {page2_data.get('report_date','')}", ln=True, align="L")
    pdf.cell(0, 5, f"Global Analysis Date: {page2_data.get('global_analysis_date','')}", ln=True, align="L")
    pdf.ln(5)

    qc_by_method = defaultdict(list)
    for qc_ in page3_data.get("qc_entries", []):
        qc_by_method[qc_["qc_method"]].append(qc_)

    widths_qc = [45, 20, 20, 20, 40, 35]
    for method, qcs in qc_by_method.items():
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 5, f"QC Batch: {qcs[0]['qc_batch']}", ln=True, align="L")
        pdf.cell(0, 5, f"QC Analysis (Method): {method}", ln=True, align="L")
        pdf.cell(0, 5, f"Method Blank: {qcs[0]['method_blank']}", ln=True, align="L")
        pdf.ln(3)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        heads_qc = ["Parameter", "Unit", "MDL", "PQL", "Method Blank Conc.", "Lab Qualifier"]
        for h, w in zip(heads_qc, widths_qc):
            pdf.cell(w, 7, h, border=1, align="C", fill=True)
        pdf.ln(7)
        pdf.set_font("DejaVu", "", 10)
        for qc_ in qcs:
            row_vals = [
                qc_["parameter"],
                qc_["unit"],
                qc_["mdl"],
                qc_["pql"],
                qc_["blank_result"],
                qc_["lab_qualifier"]
            ]
            for val, w in zip(row_vals, widths_qc):
                pdf.cell(w, 7, str(val), border=1, align="C")
            pdf.ln(7)
        pdf.ln(10)

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

#####################################
# Main App
#####################################
def main_app():
    st.title("Water Quality COA (Auto-Generated Fields)")
    # Render top navbar
    render_navbar()

    # Single-page container
    page_container = st.empty()

    # Decide which page to show
    if st.session_state.current_page == 0:
        with page_container:
            render_cover_page()
    elif st.session_state.current_page == 1:
        with page_container:
            render_sample_summary_page()
    elif st.session_state.current_page == 2:
        with page_container:
            render_analytical_results_page()
    elif st.session_state.current_page == 3:
        with page_container:
            render_quality_control_page()

    # If we are on the last page, show "Generate PDF" button
    if st.session_state.current_page == len(PAGES) - 1:
        st.markdown("### All pages completed.")
        if st.button("Generate PDF and Download", key="generate_pdf_btn"):
            pdf_bytes = create_pdf_report(
                lab_name="KELP Laboratory",
                lab_address="520 Mercury Dr, Sunnyvale, CA 94085",
                lab_email="kelp@ketoslab.com",
                lab_phone="(408) 461-8860",
                cover_data=st.session_state["cover_data"],
                page1_data=st.session_state["page1_data"],
                page2_data=st.session_state["page2_data"],
                page3_data=st.session_state["page3_data"]
            )
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="MultiPage_COA_withCover.pdf",
                mime="application/pdf",
                key="download_pdf_btn"
            )

if __name__ == "__main__":
    main_app()
