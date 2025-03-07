import streamlit as st
from fpdf import FPDF
import datetime
import io
import random
import string
from collections import defaultdict


def reset_app():
    """Clears all session state variables and reloads the app."""
    st.session_state.clear()  # This removes all session state variables
    st.rerun()  # Use this instead of st.experimental_rerun()


#####################################
# PDF Class for Page Numbers
#####################################
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        # If you have DejaVu fonts, use them:
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
    "Potassium": ["EPA 200.7", "SM 3111 B-1999", "SM 3120 B-1999", "SM 3500 K C-1997"],
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
# PAGES
#####################################
PAGES = ["Cover Page", "Sample Summary", "Analytical Results", "Quality Control Data"]

#####################################
# 1) Ensure we only do initialization once
#####################################
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    # We start on page 0 => cover page
    st.session_state.current_page = 0
    
    # Prepare each dictionary if not present
    st.session_state.setdefault("cover_data", {})
    st.session_state.setdefault("page1_data", {})
    st.session_state.setdefault("page2_data", {})
    st.session_state.setdefault("page3_data", {})

#####################################
# 2) NAVBAR
#####################################
def render_navbar():
    # Show progress
    progress = int((st.session_state.current_page + 1) / len(PAGES) * 100)
    st.markdown(f"""
    <div style="width: 100%; background-color: #eee; border-radius: 4px; margin-bottom: 16px;">
      <div style="height: 16px; background: linear-gradient(90deg, #2196F3, #4CAF50); width: {progress}%;">
      </div>
    </div>
    """, unsafe_allow_html=True)

    nav_cols = st.columns(len(PAGES))
    for i, page_name in enumerate(PAGES):
        # unique key: e.g. nav_btn_cover, nav_btn_sample, ...
        btn_key = f"nav_btn_{page_name.replace(' ','_')}_{i}"
        if nav_cols[i].button(page_name, key=btn_key):
            st.session_state.current_page = i

#####################################
# 3) Next/Back
#####################################

def render_nav_buttons():
    col1, col2 = st.columns([1, 1])
    
    # Back button (show only if not on the first page)
    if st.session_state.current_page > 0:
        if col1.button("Back", key=f"back_{st.session_state.current_page}"):
            st.session_state.current_page -= 1
            st.rerun()

    # Next button (show only if not on the last page)
    if st.session_state.current_page < len(PAGES) - 1:
        if col2.button("Next", key=f"next_{st.session_state.current_page}"):
            st.session_state.current_page += 1
            st.rerun()


#####################################
# 4) Page Renders
#####################################
def render_cover_page():
    st.header("Cover Page")
    cover = st.session_state["cover_data"]
    # If empty, init with default
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
        default_date = datetime.date.today().strftime("%m/%d/%Y")
        cover["date_samples_received"] = default_date
        cover["date_reported"] = default_date
        cover["analysis_type"] = "Environmental"
        cover["coc_number"] = generate_coc_number()
        cover["po_number"] = generate_po_number()
        cover["report_title"] = "CERTIFICATE OF ANALYSIS"
        cover["comments"] = "None"
        cover["signatory_name"] = ""
        cover["signatory_title"] = "Lab Manager"

    cover["project_name"] = st.text_input("Project Name", value=cover.get("project_name",""))
    cover["client_name"] = st.text_input("Client Name", value=cover.get("client_name",""))
    cover["street"] = st.text_input("Street Address", value=cover.get("street",""))
    cover["city"] = st.text_input("City", value=cover.get("city",""))
    cover["state"] = st.text_input("State/Province", value=cover.get("state",""))
    cover["zip"] = st.text_input("Zip Code", value=cover.get("zip",""))
    cover["country"] = st.text_input("Country", value=cover.get("country",""))
    cover["analysis_type"] = st.text_input("Analysis Type", value=cover.get("analysis_type","Environmental"))
    cover["comments"] = st.text_area("Comments/Narrative", value=cover.get("comments","None"))

    # rebuild address
    cover["address_line"] = (
        cover["street"] + ", " + cover["city"] + ", " +
        cover["state"] + " " + cover["zip"] + ", " + cover["country"]
    )

    sample_type = st.selectbox("Sample Type", options=["GW","DW","WW","IW","SW"], index=0)
    try:
        dt = datetime.datetime.strptime(cover["date_samples_received"], "%m/%d/%Y")
        date_str = dt.strftime("%Y%m%d")
    except:
        date_str = datetime.date.today().strftime("%Y%m%d")
    cover["work_order"] = f"{sample_type}-{date_str}-0001"

    st.subheader("Lab Manager Signatory")
    cover["signatory_name"] = st.text_input("Lab Manager Name", value=cover.get("signatory_name",""))
    cover["signatory_title"] = st.text_input("Lab Manager Title", value=cover.get("signatory_title","Lab Manager"))

    render_nav_buttons()

def render_sample_summary_page():
    st.header("Sample Summary")
    p1 = st.session_state["page1_data"]
    # Guarantee 'samples' is present
    p1.setdefault("samples", [])

    if "report_id" not in p1:
        p1["report_id"] = "".join(random.choices("0123456789", k=7))
        p1["report_date"] = datetime.date.today().strftime("%m/%d/%Y")
        p1["client_name"] = st.session_state["cover_data"].get("client_name","")
        p1["client_address"] = st.session_state["cover_data"].get("address_line","")
        p1["project_id"] = "PJ" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))

    with st.form("sample_form", clear_on_submit=True):
        lab_id = st.text_input("Lab ID (blank=auto)", "")
        s_id = st.text_input("Sample ID","")
        mat = st.text_input("Matrix","Water")
        d_collect = st.text_input("Date Collected", datetime.date.today().strftime("%m/%d/%Y"))
        d_recv = st.text_input("Date Received", datetime.date.today().strftime("%m/%d/%Y"))
        if st.form_submit_button("Add Sample"):
            if not lab_id.strip():
                lab_id = generate_id()
            p1["samples"].append({
                "lab_id": lab_id,
                "sample_id": s_id,
                "matrix": mat,
                "date_collected": d_collect,
                "date_received": d_recv
            })

    st.write("**Current Water Samples:**")
    if p1["samples"]:
        for i, s_ in enumerate(p1["samples"], 1):
            st.write(f"{i}. Lab ID: {s_['lab_id']}, Sample ID: {s_['sample_id']}, Matrix: {s_['matrix']}, "
                     f"Collected: {s_['date_collected']}, Received: {s_['date_received']}")
    else:
        st.info("No samples yet.")

    render_nav_buttons()

def render_analytical_results_page():
    st.header("Analytical Results")
    p2 = st.session_state["page2_data"]
    p2.setdefault("results", [])

    if "workorder_name" not in p2:
        p2["workorder_name"] = st.session_state["cover_data"].get("work_order","WO-UNKNOWN")
        p2["global_analysis_date"] = datetime.date.today().strftime("%m/%d/%Y") + " 10:00"
        p2["report_id"] = st.session_state["page1_data"].get("report_id","0000000")
        p2["report_date"] = st.session_state["page1_data"].get("report_date",datetime.date.today().strftime("%m/%d/%Y"))

    st.text(f"Work Order: {p2['workorder_name']}")
    st.text(f"Report ID: {p2['report_id']}")
    st.text(f"Report Date: {p2['report_date']}")
    st.text(f"Global Analysis Date: {p2['global_analysis_date']}")

    analyte = st.selectbox("Parameter (Analyte)", list(analyte_to_methods.keys()))
    method = st.selectbox("Method", analyte_to_methods[analyte])

    with st.form("analytical_form", clear_on_submit=True):
        st.write(f"Selected Analyte: {analyte}")
        st.write(f"Selected Method: {method}")

        sample_lab_ids = [s_["lab_id"] for s_ in st.session_state["page1_data"].get("samples",[])]
        if sample_lab_ids:
            chosen_lab_id = st.selectbox("Lab ID", sample_lab_ids)
            # find sample id
            s_id = ""
            for s_ in st.session_state["page1_data"]["samples"]:
                if s_["lab_id"] == chosen_lab_id:
                    s_id = s_["sample_id"]
                    break
            st.write(f"Corresponding Sample ID: {s_id}")
        else:
            chosen_lab_id = st.text_input("Lab ID","")
            s_id = ""

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            df = st.text_input("DF","")
        with c2:
            mdl = st.text_input("MDL","")
        with c3:
            pql = st.text_input("PQL","")
        with c4:
            res = st.text_input("Result","ND")
        un = st.selectbox("Unit", ["mg/L","µg/L","µS/cm","none"])

        if st.form_submit_button("Add Analytical Result"):
            if chosen_lab_id:
                p2["results"].append({
                    "lab_id": chosen_lab_id,
                    "sample_id": s_id,
                    "parameter": analyte,
                    "analysis": method,
                    "df": df,
                    "mdl": mdl,
                    "pql": pql,
                    "result": res,
                    "unit": un
                })

    st.write("**Current Analytical Results:**")
    if p2["results"]:
        for i, r_ in enumerate(p2["results"],1):
            st.write(f"{i}. Lab ID: {r_['lab_id']} (Sample ID: {r_.get('sample_id','')}), "
                     f"Parameter: {r_['parameter']}, Analysis: {r_['analysis']}, DF: {r_['df']}, "
                     f"MDL: {r_['mdl']}, PQL: {r_['pql']}, Result: {r_['result']} {r_['unit']}")
    else:
        st.info("No results yet.")

    render_nav_buttons()

def render_quality_control_page():
    st.header("Quality Control Data")
    p3 = st.session_state["page3_data"]
    p3.setdefault("qc_entries", [])

    # pick analyte, method
    analyte = st.selectbox("QC Parameter (Analyte)", list(analyte_to_methods.keys()))
    method = st.selectbox("QC Method", analyte_to_methods[analyte])

    with st.form("qc_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            q_unit = st.text_input("Unit","mg/L")
        with c2:
            q_mdl = st.text_input("MDL","0.0010")
        with c3:
            q_pql = st.text_input("PQL","0.005")
        with c4:
            q_qual = st.text_input("Lab Qualifier","")
        blank_conc = st.text_input("Method Blank Conc.","")

        if st.form_submit_button("Add QC Entry"):
            q_batch = generate_qc_batch()
            mb = generate_method_blank()
            p3["qc_entries"].append({
                "qc_batch": q_batch,
                "qc_method": method,
                "parameter": analyte,
                "unit": q_unit,
                "mdl": q_mdl,
                "pql": q_pql,
                "blank_result": blank_conc,
                "lab_qualifier": q_qual,
                "method_blank": mb
            })

    st.write("**Current QC Data:**")
    if p3["qc_entries"]:
        for i, qc_ in enumerate(p3["qc_entries"],1):
            st.write(f"{i}. QC Batch: {qc_['qc_batch']}, Method: {qc_['qc_method']}, "
                     f"Parameter: {qc_['parameter']}, Unit: {qc_['unit']}, MDL: {qc_['mdl']}, "
                     f"PQL: {qc_['pql']}, Blank: {qc_['blank_result']}, Lab Qualifier: {qc_['lab_qualifier']}")
    else:
        st.info("No QC entries yet.")

    render_nav_buttons()

#####################################
# PDF GENERATION
#####################################
class MyPDF(FPDF):
    pass


def create_pdf_report(lab_name, lab_address, lab_email, lab_phone, cover_data, page1_data, page2_data, page3_data):

    pdf = PDF("P", "mm", "A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_text_color(0, 0, 0)
    effective_width = 180
    total_pages = 4  # Cover, Page 1, Page 2, Page 3


    # IMPORTANT: Use a Unicode font for characters like "₃"
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "DejaVuSans-Italic.ttf", uni=True)
    pdf.set_font("DejaVu", "", 10)



    # ---------------------------
    # 0. COVER PAGE
    # ---------------------------
    pdf.add_page()

    # Insert the KELP logo at the top-left
    try:
        pdf.image("kelp_logo.png", x=10, y=5, w=50)
    except Exception as e:
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_xy(10, 10)
        pdf.cell(30, 10, "[LOGO]", border=0, ln=0, align="L")
    
    # Move down to leave space after the logo
    
    #pdf.set_xy(140, 5)  # Shift up to align with the logo
    #pdf.set_font("DejaVu", "B", 12)
    #pdf.cell(0, 5, "KELP Laboratory", ln=True, align="R")
    
    pdf.set_font("DejaVu", "", 10)
    pdf.set_xy(140,8)
    pdf.cell(0, 5, "520 Mercury Dr, Sunnyvale, CA 94085", ln=True, align="R")
    
    pdf.set_x(140)
    pdf.cell(0, 5, "Email: kelp@ketoslab.com", ln=True, align="R")
    
    pdf.set_x(140)
    pdf.cell(0, 5, "Phone: (408) 461-8860", ln=True, align="R")
    
    # Add more space before the title so it doesn't clash with the header
    pdf.ln(30)

    # Centered Report Title
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "CERTIFICATE OF ANALYSIS", ln=True, align="C")
    pdf.ln(4)
                          
    left_width = 90
    right_width = 90

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
    # Print the full combined address (Street, City, State, Zip, Country)
    pdf.multi_cell(effective_width - 40, 6, cover_data["address_line"], border=1, align="L")
    pdf.ln(2)

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
    pdf.cell(effective_width, 6, f"Client: {cover_data['client_name']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Address: {cover_data['address_line']}", ln=True, align="L")
    pdf.ln(4)
    
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    headers = ["Lab ID", "Sample ID", "Matrix", "Date Collected", "Date Received"]
    widths = [30, 40, 30, 40, 40]  # Sum = 180 (page-wide)
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
    # 2. PAGE 2: ANALYTICAL RESULTS (Separate table for each Lab ID and Sample ID)
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
    
    # Group results by a tuple (lab_id, sample_id)
    results_by_lab = defaultdict(list)
    for r_ in page2_data["results"]:
        key = (r_["lab_id"], r_.get("sample_id", ""))
        results_by_lab[key].append(r_)
    
    # Define column widths so that total width = 180 mm
    widths2 = [40, 35, 20, 20, 20, 30, 15]
    
    for (lab_id, sample_id), results_list in results_by_lab.items():
        header_text = f"Analytical Results for Lab ID: {lab_id} ( Sample ID: {sample_id} )"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 8, header_text, ln=True, align="L")
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        headers2 = ["Parameter", "Analysis", "DF", "MDL", "PQL", "Result", "Unit"]
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
    
    # Define column widths for QC table (set total = 180 mm)
    widths_qc = [45, 20, 20, 20, 40, 35]
    
    for method, qcs in qc_by_method.items():
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 5, f"QC Batch: {qcs[0]['qc_batch']}", ln=True, align="L")
        pdf.cell(0, 5, f"QC Analysis (Method): {method}", ln=True, align="L")
        pdf.cell(0, 5, f"Method Blank: {qcs[0]['method_blank']}", ln=True, align="L")
        pdf.ln(3)
    
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        headers_qc = ["Parameter", "Unit", "MDL", "PQL", "Method Blank Conc.", "Lab Qualifier"]
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


# MAIN APP

def main():
    st.title("Water Quality COA")


    # Render the top nav
    render_navbar()
    if st.button("🔄 Refresh / Start Over"):
        reset_app()
    page_container = st.container()

    # Decide page

    page_idx = st.session_state.current_page
    if page_idx == 0:
        render_cover_page()
    elif page_idx == 1:
        render_sample_summary_page()
    elif page_idx == 2:
        render_analytical_results_page()
    elif page_idx == 3:
        render_quality_control_page()


    # If last page, show generate
    if st.session_state.current_page == len(PAGES) - 1:
        st.markdown("### All pages completed.")
        if st.button("Generate PDF"):
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
            st.download_button("Download PDF",
                data=pdf_bytes,
                file_name="COA_Report.pdf",
                mime="application/pdf",
                key="dl_pdf_btn")

if __name__ == "__main__":
    main()
