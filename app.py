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
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", 0, 0, "C")

#####################################
# Helper Functions
#####################################

def generate_id(prefix="LS", length=6):
    """Generate a short random alphanumeric ID."""
    return prefix + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

def generate_qc_batch():
    """Generate QC Batch in the format ABC123."""
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    digits = ''.join(random.choices("0123456789", k=3))
    return letters + digits

def generate_method_blank():
    """Generate Method Blank in the format AB12345."""
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
# Navigation: Define Page Titles and Order
#####################################
pages = ["Cover Page", "Sample Summary", "Analytical Results", "Quality Control Data"]

# Initialize current page if not set
if "current_page" not in st.session_state:
    st.session_state.current_page = 0

def render_navbar():
    cols = st.columns(len(pages))
    for i, col in enumerate(cols):
        # Create a button for each page
        if col.button(pages[i], key=f"nav_{i}"):
            st.session_state.current_page = i

    # Optionally, show a progress bar (e.g., a simple gradient)
    progress = (st.session_state.current_page + 1) / len(pages)
    st.progress(progress)

#####################################
# Page Functions
#####################################
def cover_page():
    st.header("Cover Page Fields (Optional Edits)")
    st.text_input("Project Name", key="project_name", value=st.session_state["cover_data"].get("project_name", ""))
    st.text_input("Client Name", key="client_name", value=st.session_state["cover_data"].get("client_name", ""))
    st.text_input("Street Address", key="street", value=st.session_state["cover_data"].get("street", ""))
    st.text_input("City", key="city", value=st.session_state["cover_data"].get("city", ""))
    st.text_input("State/Province/Region", key="state", value=st.session_state["cover_data"].get("state", ""))
    st.text_input("Postal/Zip Code", key="zip", value=st.session_state["cover_data"].get("zip", ""))
    st.text_input("Country", key="country", value=st.session_state["cover_data"].get("country", ""))
    st.text_input("Analysis Type", key="analysis_type", value=st.session_state["cover_data"].get("analysis_type", "Environmental"))
    st.text_area("Comments / Narrative", key="comments", value=st.session_state["cover_data"].get("comments", "None"))
    # Combine address fields for PDF generation
    st.session_state["cover_data"]["address_line"] = (
        st.session_state["cover_data"].get("street", "") + ", " +
        st.session_state["cover_data"].get("city", "") + ", " +
        st.session_state["cover_data"].get("state", "") + " " +
        st.session_state["cover_data"].get("zip", "") + ", " +
        st.session_state["cover_data"].get("country", "")
    )
    st.text("Auto-generated Work Order: " + st.session_state["cover_data"]["work_order"])
    st.subheader("Lab Manager Signatory")
    st.text_input("Lab Manager Name", key="signatory_name", value=st.session_state["cover_data"].get("signatory_name", ""))
    st.text_input("Lab Manager Title", key="signatory_title", value=st.session_state["cover_data"].get("signatory_title", "Lab Manager"))
    if st.button("Next"):
        st.session_state.current_page += 1

def sample_summary_page():
    st.header("Page 1: SAMPLE SUMMARY")
    st.info("Report ID, Report Date, Client Name, and Client Address are taken from Cover Page.")
    with st.form("page1_samples_form", clear_on_submit=True):
        sample_lab_id = st.text_input("Lab ID (Leave blank for auto-gen)")
        sample_id = st.text_input("Sample ID")
        matrix = st.text_input("Matrix", value="Water")
        sample_date_collected = st.text_input("Date Collected", value=datetime.date.today().strftime("%m/%d/%Y"))
        sample_date_received = st.text_input("Date Received", value=datetime.date.today().strftime("%m/%d/%Y"))
        if st.form_submit_button("Add Water Sample"):
            if not sample_lab_id.strip():
                sample_lab_id = generate_id()
            if "samples" not in st.session_state["page1_data"]:
                st.session_state["page1_data"]["samples"] = []
            st.session_state["page1_data"]["samples"].append({
                "lab_id": sample_lab_id,
                "sample_id": sample_id,
                "matrix": matrix,
                "date_collected": sample_date_collected,
                "date_received": sample_date_received
            })
    if st.session_state["page1_data"].get("samples"):
        st.write("**Current Water Samples:**")
        for i, s in enumerate(st.session_state["page1_data"]["samples"], 1):
            st.write(f"{i}. Lab ID: {s['lab_id']}, Sample ID: {s['sample_id']}, Matrix: {s['matrix']}, Collected: {s['date_collected']}, Received: {s['date_received']}")
    else:
        st.info("No water samples added yet.")
    if st.button("Next"):
        st.session_state.current_page += 1

def analytical_results_page():
    st.header("Page 2: ANALYTICAL RESULTS")
    st.text(f"Work Order: {st.session_state['page2_data']['workorder_name']}")
    st.text(f"Report ID: {st.session_state['page2_data']['report_id']}")
    st.text(f"Report Date: {st.session_state['page2_data']['report_date']}")
    st.text(f"Global Analysis Date: {st.session_state['page2_data']['global_analysis_date']}")
    # Dependent dropdowns outside the form for dynamic updates
    selected_parameter = st.selectbox("Parameter (Analyte)", options=list(analyte_to_methods.keys()), key="analyte")
    selected_method = st.selectbox("Analysis (Method)", options=analyte_to_methods[selected_parameter], key="method")
    st.subheader("Add Analytical Result")
    with st.form("page2_results_form", clear_on_submit=True):
        st.write(f"Selected Analyte: {selected_parameter}")
        st.write(f"Selected Method: {selected_method}")
        lab_ids = [s["lab_id"] for s in st.session_state["page1_data"].get("samples", [])]
        if lab_ids:
            result_lab_id = st.selectbox("Select Lab ID", options=lab_ids, key="result_lab_id")
            sample_id_val = next((s["sample_id"] for s in st.session_state["page1_data"]["samples"] if s["lab_id"] == result_lab_id), "")
            st.text(f"Corresponding Sample ID: {sample_id_val}")
        else:
            result_lab_id = st.text_input("Lab ID")
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
            if "results" not in st.session_state["page2_data"]:
                st.session_state["page2_data"]["results"] = []
            st.session_state["page2_data"]["results"].append({
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
    if st.session_state["page2_data"].get("results"):
        st.write("**Current Analytical Results:**")
        for i, r in enumerate(st.session_state["page2_data"]["results"], 1):
            st.write(f"{i}. Lab ID: {r['lab_id']}, Sample ID: {r.get('sample_id','')}, Parameter: {r['parameter']}, Analysis: {r['analysis']}, DF: {r['df']}, MDL: {r['mdl']}, PQL: {r['pql']}, Result: {r['result']} {r['unit']}")
    else:
        st.info("No analytical results added yet.")
    if st.button("Next"):
        st.session_state.current_page += 1

def qc_data_page():
    st.header("Page 3: QUALITY CONTROL DATA")
    st.text(f"Work Order: {st.session_state['page2_data']['workorder_name']}")
    st.text(f"Report ID: {st.session_state['page2_data']['report_id']}")
    st.text(f"Report Date: {st.session_state['page2_data']['report_date']}")
    st.text(f"Global Analysis Date: {st.session_state['page2_data']['global_analysis_date']}")
    # Dependent dropdowns for QC parameter and method outside the form
    qc_selected_analyte = st.selectbox("QC Parameter (Analyte)", options=list(analyte_to_methods.keys()), key="qc_analyte")
    qc_selected_method = st.selectbox("QC Analysis (Method)", options=analyte_to_methods[qc_selected_analyte], key="qc_method")
    st.subheader("Add QC Data Entry")
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
            qc_batch = generate_qc_batch()         # e.g., "ABC123"
            method_blank = generate_method_blank()   # e.g., "AB12345"
            if "qc_entries" not in st.session_state["page3_data"]:
                st.session_state["page3_data"]["qc_entries"] = []
            st.session_state["page3_data"]["qc_entries"].append({
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
    if st.session_state["page3_data"].get("qc_entries"):
        st.write("**Current QC Data:**")
        for i, qc in enumerate(st.session_state["page3_data"]["qc_entries"], 1):
            st.write(
                f"{i}. QC Batch: {qc['qc_batch']}, Method: {qc['qc_method']}, Parameter: {qc['parameter']}, "
                f"Unit: {qc['unit']}, MDL: {qc['mdl']}, PQL: {qc['pql']}, Method Blank Conc.: {qc['blank_result']}, "
                f"Lab Qualifier: {qc['lab_qualifier']}"
            )
    else:
        st.info("No QC data entries yet.")
    if st.button("Next"):
        st.session_state.current_page += 1

#####################################
# Navigation and Page Rendering
#####################################
def render_page():
    st.markdown("<style> .progress-step {padding: 5px 10px; border-radius: 5px; margin-right: 5px; cursor: pointer;}"
                ".progress-step.active {background: linear-gradient(90deg, #36D1DC, #5B86E5); color: white;}"
                ".progress-step.inactive {background: #E0E0E0; color: #555555;}"
                "</style>", unsafe_allow_html=True)
    nav_cols = st.columns(len(pages))
    for i, col in enumerate(nav_cols):
        # Each step is a clickable button styled with custom CSS
        if i == st.session_state.current_page:
            btn_label = f'<div class="progress-step active">{pages[i]}</div>'
        else:
            btn_label = f'<div class="progress-step inactive">{pages[i]}</div>'
        if col.button("", key=f"nav_{i}", help=pages[i]):
            st.session_state.current_page = i
        # Render the label as HTML
        col.markdown(btn_label, unsafe_allow_html=True)
    
    # Render the current page
    if st.session_state.current_page == 0:
        cover_page()
    elif st.session_state.current_page == 1:
        sample_summary_page()
    elif st.session_state.current_page == 2:
        analytical_results_page()
    elif st.session_state.current_page == 3:
        qc_data_page()

#####################################
# MAIN APP
#####################################
def main():
    st.title("Water Quality COA Generator")
    # Initialize session_state for cover, page1, page2, page3 if not present
    if "cover_data" not in st.session_state:
        # Auto-generate COC # and PO #
        auto_coc_number = "COC-" + ''.join(random.choices("0123456789", k=6))
        auto_po_number = "PO-KL" + datetime.datetime.today().strftime("%Y%m") + ''.join(random.choices("0123456789", k=4))
        auto_work_order = "WO-" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        default_date = datetime.date.today().strftime("%m/%d/%Y")
        st.session_state["cover_data"] = {
            "lab_name": "KELP Laboratory",
            "work_order": auto_work_order,
            "project_name": "",
            "client_name": "",
            "street": "",
            "city": "",
            "state": "",
            "zip": "",
            "country": "",
            "phone": "",
            "date_samples_received": default_date,
            "date_reported": default_date,
            "analysis_type": "Environmental",
            "coc_number": auto_coc_number,
            "po_number": auto_po_number,
            "report_title": "CERTIFICATE OF ANALYSIS",
            "comments": "None",
            "signatory_name": "",
            "signatory_title": "Lab Manager",
        }
    if "page1_data" not in st.session_state:
        st.session_state["page1_data"] = {
            "report_id": ''.join(random.choices("0123456789", k=7)),
            "report_date": datetime.date.today().strftime("%m/%d/%Y"),
            "client_name": st.session_state["cover_data"]["client_name"],
            "client_address": "",  # Will be derived from cover_data
            "project_id": "PJ-" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4)),
            "samples": []
        }
        # Copy client info from cover_data
        st.session_state["page1_data"]["client_name"] = st.session_state["cover_data"]["client_name"]
        st.session_state["page1_data"]["client_address"] = st.session_state["cover_data"]["address_line"]
    if "page2_data" not in st.session_state:
        st.session_state["page2_data"] = {
            "workorder_name": st.session_state["cover_data"]["work_order"],
            "global_analysis_date": datetime.date.today().strftime("%m/%d/%Y") + " 10:00",
            "results": [],
            "report_id": st.session_state["page1_data"]["report_id"],
            "report_date": st.session_state["page1_data"]["report_date"]
        }
    if "page3_data" not in st.session_state:
        st.session_state["page3_data"] = {"qc_entries": []}
    
    render_page()

if __name__ == "__main__":
    main()
