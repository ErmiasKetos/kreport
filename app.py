import streamlit as st
from fpdf import FPDF
import datetime
import io
import random
import string
import requests
from collections import defaultdict
import math

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

def generate_coc_number():
    return "COC-" + ''.join(random.choices("0123456789", k=6))

def generate_po_number():
    return "PO-KL" + datetime.datetime.today().strftime("%Y%m") + ''.join(random.choices("0123456789", k=4))

def get_date_input(label, default_str=""):
    """
    Wrapper for st.date_input that handles default string in '%m/%d/%Y' format.
    Returns a string formatted as '%m/%d/%Y'.
    """
    if default_str:
        try:
            default_date = datetime.datetime.strptime(default_str, "%m/%d/%Y").date()
        except Exception:
            default_date = datetime.date.today()
    else:
        default_date = datetime.date.today()
    selected_date = st.date_input(label, value=default_date)
    return selected_date.strftime("%m/%d/%Y")

def address_autofill_field(label, default=""):
    query = st.text_input(label, value=default, key=label)
    suggestions = []
    address_details = None
    if len(query) >= 3:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 3,
            "countrycodes": "us" 
        }
        headers = {"User-Agent": "YourAppName/1.0 (your.email@example.com)"}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            results = response.json()
            for candidate in results:
                addr = candidate.get("address", {})
                full_address = candidate.get("display_name", "")
                house = addr.get("house_number", "")
                road = addr.get("road", "")
                street = f"{house} {road}".strip() if house or road else ""
                suggestions.append((full_address, street, addr))
        else:
            st.error("Error fetching address suggestions from Nominatim.")
    if suggestions:
        display_names = [s[0] for s in suggestions]
        selected = st.selectbox(f"Select a suggested {label.lower()}:", display_names, key=label+"_suggestions")
        for disp, street_val, addr in suggestions:
            if disp == selected:
                address_details = addr
                selected_street = street_val
                break
        return selected_street, address_details
    return query, None

# Helper function to draw a table row with text wrapping
def draw_table_row(pdf, data, widths, line_height=5, border=1, align='C', fill=False):
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    max_lines = 1
    for text, w in zip(data, widths):
        text_width = pdf.get_string_width(text)
        lines = math.ceil(text_width / w)
        if lines < 1:
            lines = 1
        if lines > max_lines:
            max_lines = lines
    cell_height = line_height * max_lines
    x = x_start
    for text, w in zip(data, widths):
        pdf.set_xy(x, y_start)
        pdf.multi_cell(w, line_height, text, border=border, align=align, fill=fill)
        x += w
    pdf.set_xy(x_start, y_start + cell_height)

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
# 1) Initialization
#####################################
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_page = 0
    st.session_state.setdefault("cover_data", {})
    st.session_state.setdefault("page1_data", {})
    st.session_state.setdefault("page2_data", {})
    st.session_state.setdefault("page3_data", {})

#####################################
# 2) NAVBAR
#####################################
def render_navbar():
    progress = int((st.session_state.current_page + 1) / len(PAGES) * 100)
    st.markdown(f"""
    <div style="width: 100%; background-color: #eee; border-radius: 4px; margin-bottom: 16px;">
      <div style="height: 16px; background: linear-gradient(90deg, #2196F3, #4CAF50); width: {progress}%;">
      </div>
    </div>
    """, unsafe_allow_html=True)
    nav_cols = st.columns(len(PAGES))
    for i, page_name in enumerate(PAGES):
        btn_key = f"nav_btn_{page_name.replace(' ','_')}_{i}"
        if nav_cols[i].button(page_name, key=btn_key):
            st.session_state.current_page = i

#####################################
# 3) Next/Back Buttons
#####################################
def render_nav_buttons():
    col1, col2 = st.columns([1, 1])
    if st.session_state.current_page > 0:
        if col1.button("Back", key=f"back_{st.session_state.current_page}"):
            st.session_state.current_page -= 1
            st.rerun()
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
        cover["date_samples_received"] = ""
        cover["date_reported"] = ""
        cover["analysis_type"] = "Environmental"
        cover["coc_number"] = generate_coc_number()
        cover["po_number"] = generate_po_number()
        cover["report_title"] = "CERTIFICATE OF ANALYSIS"
        cover["comments"] = "None"
        cover["signatory_name"] = ""
        cover["signatory_title"] = "Lab Manager"
    cover["project_name"] = st.text_input("Project Name", value=cover.get("project_name", ""))
    cover["client_name"] = st.text_input("Client Name", value=cover.get("client_name", ""))
    selected_street, addr_details = address_autofill_field("Street Address", default=cover.get("street", ""))
    cover["street"] = selected_street
    if addr_details:
        cover["city"] = addr_details.get("city", addr_details.get("town", addr_details.get("village", "")))
        cover["state"] = addr_details.get("state", "")
        cover["zip"] = addr_details.get("postcode", "")
        cover["country"] = addr_details.get("country", "")
    else:
        cover["city"] = st.text_input("City", value=cover.get("city", ""))
        cover["state"] = st.text_input("State/Province", value=cover.get("state", ""))
        cover["zip"] = st.text_input("Zip Code", value=cover.get("zip", ""))
        cover["country"] = st.text_input("Country", value=cover.get("country", ""))
    cover["analysis_type"] = st.text_input("Analysis Type", value=cover.get("analysis_type", "Environmental"))
    cover["date_samples_received"] = get_date_input("Date Samples Received", default_str=cover.get("date_samples_received", ""))
    cover["date_reported"] = get_date_input("Date Reported", default_str=cover.get("date_reported", datetime.date.today().strftime("%m/%d/%Y")))
    cover["comments"] = st.text_area("Comments/Narrative", value=cover.get("comments", "None"))
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

def render_sample_summary_page():
    st.header("Sample Summary")
    p1 = st.session_state["page1_data"]
    p1.setdefault("samples", [])
    if "report_id" not in p1:
        p1["report_id"] = "".join(random.choices("0123456789", k=7))
        p1["report_date"] = datetime.date.today().strftime("%m/%d/%Y")
        p1["client_name"] = st.session_state["cover_data"].get("client_name", "")
        p1["client_address"] = st.session_state["cover_data"].get("address_line", "")
        p1["project_id"] = "PJ" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
    with st.form("sample_form", clear_on_submit=True):
        lab_id = st.text_input("Lab ID (blank=auto)", "")
        s_id = st.text_input("Sample ID", "")
        mat = st.text_input("Matrix", "Water")
        d_collect = get_date_input("Date Collected", "")
        d_recv = get_date_input("Date Received", st.session_state["cover_data"].get("date_samples_received", ""))
        if st.form_submit_button("Add Sample"):
            if not lab_id.strip():
                lab_id = generate_id()
            if not st.session_state["cover_data"].get("date_samples_received"):
                st.session_state["cover_data"]["date_samples_received"] = d_recv
            p1["samples"].append({
                "lab_id": lab_id,
                "sample_id": s_id,
                "matrix": mat,
                "date_collected": d_collect,
                "date_received": d_recv
            })
    st.write("**Current Water Samples:**")
    if p1["samples"]:
        for i, s_ in enumerate(p1["samples"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** Lab ID: {s_['lab_id']}, Sample ID: {s_['sample_id']}, Matrix: {s_['matrix']}, "
                         f"Collected: {s_['date_collected']}, Received: {s_['date_received']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_sample_{i}"):
                    del p1["samples"][i]
                    st.rerun()
    else:
        st.info("No samples yet.")
    render_nav_buttons()

def render_analytical_results_page():
    st.header("Analytical Results")
    p2 = st.session_state["page2_data"]
    p2.setdefault("results", [])
    if "workorder_name" not in p2:
        p2["workorder_name"] = st.session_state["cover_data"].get("work_order", "WO-UNKNOWN")
        p2["report_id"] = st.session_state["page1_data"].get("report_id", "0000000")
        p2["report_date"] = st.session_state["page1_data"].get("report_date", datetime.date.today().strftime("%m/%d/%Y"))
    st.text(f"Work Order: {p2['workorder_name']}")
    st.text(f"Report ID: {p2['report_id']}")
    st.text(f"Report Date: {p2['report_date']}")
    st.text("Analysis Date will be shown per sample.")
    analyte = st.selectbox("Parameter (Analyte)", list(analyte_to_methods.keys()))
    method = st.selectbox("Method", analyte_to_methods[analyte])
    with st.form("analytical_form", clear_on_submit=True):
        st.write(f"Selected Analyte: {analyte}")
        st.write(f"Selected Method: {method}")
        sample_lab_ids = [s_["lab_id"] for s_ in st.session_state["page1_data"].get("samples", [])]
        if sample_lab_ids:
            chosen_lab_id = st.selectbox("Lab ID", sample_lab_ids)
            s_id = next((s_["sample_id"] for s_ in st.session_state["page1_data"]["samples"] if s_["lab_id"] == chosen_lab_id), "")
            st.write(f"Corresponding Sample ID: {s_id}")
        else:
            chosen_lab_id = st.text_input("Lab ID", "")
            s_id = ""
        analysis_date = get_date_input("Analysis Date", datetime.date.today().strftime("%m/%d/%Y"))
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            df = st.text_input("DF", "")
        with c2:
            mdl = st.text_input("MDL", "")
        with c3:
            pql = st.text_input("PQL", "")
        with c4:
            res = st.text_input("Result", "ND")
        un = st.selectbox("Unit", ["mg/L", "µg/L", "µS/cm", "none"])
        if st.form_submit_button("Add Analytical Result"):
            if chosen_lab_id:
                p2["results"].append({
                    "lab_id": chosen_lab_id,
                    "sample_id": s_id,
                    "analysis_date": analysis_date,
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
        for i, r_ in enumerate(p2["results"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** Lab ID: {r_['lab_id']} (Sample ID: {r_.get('sample_id', '')}), "
                         f"Parameter: {r_['parameter']}, Analysis: {r_['analysis']}, DF: {r_['df']}, "
                         f"MDL: {r_['mdl']}, PQL: {r_['pql']}, Result: {r_['result']} {r_['unit']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_result_{i}"):
                    del p2["results"][i]
                    st.rerun()
    else:
        st.info("No results yet.")
    render_nav_buttons()

def render_quality_control_page():
    st.header("Quality Control Data")
    p3 = st.session_state["page3_data"]
    p3.setdefault("qc_entries", [])
    # QC form: includes "Method Blank", "LCS", and "MS"
    qc_type = st.selectbox("QC Type", options=["Method Blank", "LCS", "MS"])
    analyte = st.selectbox("QC Parameter (Analyte)", list(analyte_to_methods.keys()))
    method = st.selectbox("QC Method", analyte_to_methods[analyte])
    with st.form("qc_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            q_unit = st.text_input("Unit", "mg/L")
        with c2:
            q_mdl = st.text_input("MDL", "0.0010")
        with c3:
            q_pql = st.text_input("PQL", "0.005")
        with c4:
            q_qual = st.text_input("Lab Qualifier", "")
        blank_conc = st.text_input("Method Blank Conc.", "")
        if qc_type == "LCS":
            spike_conc = st.text_input("Spike Conc.", "")
            lcs_recovery = st.text_input("LCS % Recovery", "")
            lcsd_recovery = st.text_input("LCSD % Recovery", "")
            rpd_lcs = st.text_input("LCS/LCSD % RPD", "")
            recovery_limits = st.text_input("% Recovery Limits", "")
            rpd_limits = st.text_input("% RPD Limits", "")
        elif qc_type == "MS":
            sample_conc = st.text_input("Sample Concentration", "")
            spike_conc = st.text_input("Spike Conc.", "")
            ms_recovery = st.text_input("MS % Recovery", "")
            msd_recovery = st.text_input("MSD % Recovery", "")
            rpd_ms = st.text_input("MS/MSD % RPD", "")
            recovery_limits = st.text_input("% Recovery Limits", "")
            rpd_limits = st.text_input("% RPD Limits", "")
        if st.form_submit_button("Add QC Entry"):
            q_batch = generate_qc_batch()
            if qc_type == "Method Blank":
                entry = {
                    "qc_type": "MB",
                    "qc_batch": q_batch,
                    "qc_method": method,
                    "parameter": analyte,
                    "unit": q_unit,
                    "mdl": q_mdl,
                    "pql": q_pql,
                    "method_blank": blank_conc,
                    "lab_qualifier": q_qual
                }
            elif qc_type == "LCS":
                entry = {
                    "qc_type": "LCS",
                    "qc_batch": q_batch,
                    "qc_method": method,
                    "parameter": analyte,
                    "unit": q_unit,
                    "mdl": q_mdl,
                    "pql": q_pql,
                    "lab_qualifier": q_qual,
                    "spike_conc": spike_conc,
                    "lcs_recovery": lcs_recovery,
                    "lcsd_recovery": lcsd_recovery,
                    "rpd_lcs": rpd_lcs,
                    "recovery_limits": recovery_limits,
                    "rpd_limits": rpd_limits
                }
            else:  # MS
                entry = {
                    "qc_type": "MS",
                    "qc_batch": q_batch,
                    "qc_method": method,
                    "parameter": analyte,
                    "unit": q_unit,
                    "mdl": q_mdl,
                    "pql": q_pql,
                    "lab_qualifier": q_qual,
                    "sample_conc": sample_conc,
                    "spike_conc": spike_conc,
                    "ms_recovery": ms_recovery,
                    "msd_recovery": msd_recovery,
                    "rpd_ms": rpd_ms,
                    "recovery_limits": recovery_limits,
                    "rpd_limits": rpd_limits
                }
            p3["qc_entries"].append(entry)
    st.write("**Current QC Data:**")
    if p3["qc_entries"]:
        for i, qc in enumerate(p3["qc_entries"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** QC Batch: {qc['qc_batch']}, Method: {qc['qc_method']}, Parameter: {qc['parameter']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_qc_{i}"):
                    del p3["qc_entries"][i]
                    st.rerun()
    else:
        st.info("No QC entries yet.")
    render_nav_buttons()

#####################################
# PDF GENERATION
#####################################
def create_pdf_report(lab_name, lab_address, lab_email, lab_phone, cover_data, page1_data, page2_data, page3_data):
    pdf = PDF("P", "mm", "A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    p2 = page2_data if page2_data else {"results": []}
    effective_width = 180  # page width for tables
    total_pages = 4
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "DejaVuSans-Italic.ttf", uni=True)
    pdf.set_font("DejaVu", "", 10)

    # ---------------------------
    # 0. COVER PAGE
    # ---------------------------
    pdf.add_page()
    try:
        pdf.image("kelp_logo.png", x=10, y=5, w=50)
    except Exception as e:
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_xy(10, 10)
        pdf.cell(30, 10, "[LOGO]", border=0, ln=0, align="L")
    pdf.set_font("DejaVu", "", 10)
    pdf.set_xy(140,8)
    pdf.cell(0, 5, "520 Mercury Dr, Sunnyvale, CA 94085", ln=True, align="R")
    pdf.set_x(140)
    pdf.cell(0, 5, "Email: kelp@ketoslab.com", ln=True, align="R")
    pdf.set_x(140)
    pdf.cell(0, 5, "Phone: (408) 461-8860", ln=True, align="R")
    pdf.ln(30)
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
    if p2.get("results"):
        first_analysis_date = p2["results"][0].get("analysis_date", "N/A")
    else:
        first_analysis_date = "N/A"
    table_row("Work Order:", cover_data.get("work_order", "N/A"))
    table_row("Project:", cover_data.get("project_name", "N/A"))
    table_row("Analysis Type:", cover_data.get("analysis_type", "N/A"))
    table_row("COC #:", cover_data.get("coc_number", "N/A"))
    table_row("PO #:", cover_data.get("po_number", "N/A"))
    table_row("Date Samples Received:", cover_data.get("date_samples_received", "N/A"))
    table_row("Date Reported:", cover_data.get("report_date", datetime.date.today().strftime("%m/%d/%Y")))
    table_row("Analysis Date:", first_analysis_date)  
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
    try:
        pdf.image("kelp_logo.png", x=10, y=5, w=30)
    except Exception as e:
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_xy(10, 10)
        pdf.cell(30, 10, "[LOGO]", border=0, ln=0, align="R")
    pdf.ln(20)
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
    # 2. PAGE 2: ANALYTICAL RESULTS
    # ---------------------------
    pdf.add_page()
    try:
        pdf.image("kelp_logo.png", x=10, y=5, w=30)
    except Exception as e:
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_xy(10, 10)
        pdf.cell(30, 10, "[LOGO]", border=0, ln=0, align="R")
    pdf.ln(20)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "ANALYTICAL RESULTS", ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(effective_width, 6, f"Report ID: {page2_data['report_id']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Report Date: {page2_data['report_date']}", ln=True, align="L")
    if p2["results"]:
        first_analysis_date = p2["results"][0].get("analysis_date", "N/A")
    else:
        first_analysis_date = "N/A"
    pdf.cell(effective_width, 6, f"Analysis Date: {first_analysis_date}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Work Order: {page2_data['workorder_name']}", ln=True, align="L")
    pdf.ln(4)
    results_by_lab = defaultdict(list)
    for r_ in page2_data["results"]:
        key = (r_["lab_id"], r_.get("sample_id", ""))
        results_by_lab[key].append(r_)
    widths2 = [30, 35, 30, 15, 15, 15, 30, 15]
    for (lab_id, sample_id), results_list in results_by_lab.items():
        header_text = f"Analytical Results for Lab ID: {lab_id} ( Sample ID: {sample_id} )"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 8, header_text, ln=True, align="L")
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        headers2 = ["Analysis Date", "Parameter", "Analysis", "DF", "MDL", "PQL", "Result", "Unit"]
        for h, w in zip(headers2, widths2):
            pdf.cell(w, 7, h, border=1, align="C", fill=True)
        pdf.ln(7)
        pdf.set_font("DejaVu", "", 10)
        for row in results_list:
            row_data = [
                row["analysis_date"],
                row["parameter"],
                row["analysis"],
                row["df"],
                row["mdl"],
                row["pql"],
                row["result"],
                row["unit"]
            ]
            for val, w in zip(row_data, widths2):
                pdf.cell(w, 7, str(val), border=1, align="C")
            pdf.ln(7)
        pdf.ln(10)
    
    # ---------------------------
    # 3. PAGE 3: QUALITY CONTROL DATA
    # ---------------------------
    pdf.add_page()
    try:
        pdf.image("kelp_logo.png", x=10, y=5, w=30)
    except Exception as e:
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_xy(10, 10)
        pdf.cell(30, 10, "[LOGO]", border=0, ln=0, align="L")
    pdf.ln(20)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "QUALITY CONTROL DATA", ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, f"Work Order: {page2_data['workorder_name']}", ln=True, align="L")
    pdf.cell(0, 5, f"Report ID: {page2_data['report_id']}", ln=True, align="L")
    pdf.cell(0, 5, f"Report Date: {page2_data['report_date']}", ln=True, align="L")
    pdf.ln(5)
    # For each QC entry, print header info and draw its corresponding table
    for qc in page3_data["qc_entries"]:
         pdf.set_font("DejaVu", "B", 10)
         header_text = f"QC Analysis (Method): {qc['qc_method']} | Parameter: {qc['parameter']}"
         pdf.multi_cell(effective_width, 5, header_text, border=0, align="L")
         pdf.multi_cell(effective_width, 5, f"QC Batch: {qc['qc_batch']}", border=0, align="L")
         # Move the unit outside the table
         pdf.multi_cell(effective_width, 5, f"Unit: {qc['unit']}", border=0, align="L")
         pdf.ln(3)
         if qc["qc_type"] == "MB":
             table_title = "Method Blank Data"
             pdf.multi_cell(effective_width, 5, f"QC Batch: {qc['qc_batch']}", border=0, align="L")
             pdf.set_font("DejaVu", "B", 9)
             pdf.multi_cell(effective_width, 5, table_title, border=0, align="L")
             pdf.ln(2)
             headers_mb = ["Parameter", "MDL", "PQL", "Method Blank Conc.", "Lab Qualifier"]
             num_cols = len(headers_mb)
             col_width = effective_width / num_cols
             draw_table_row(pdf, headers_mb, [col_width]*num_cols, line_height=5, border=1, align='C', fill=True)
             row = [qc["parameter"], qc["mdl"], qc["pql"], qc["method_blank"], qc["lab_qualifier"]]
             draw_table_row(pdf, row, [col_width]*num_cols, line_height=5, border=1, align='C', fill=False)
             pdf.ln(3)
         elif qc["qc_type"] == "LCS":
             table_title = "LCS Data"
             pdf.set_font("DejaVu", "B", 9)
             pdf.multi_cell(effective_width, 5, table_title, border=0, align="L")
             pdf.ln(2)
             headers_lcs = ["Parameter", "MDL", "PQL", "Spike Conc.", "LCS % Rec.", "LCSD % Rec.", "LCS/LCSD % RPD", "% Rec. Limits", "% RPD Limits", "Lab Qualifier"]
             num_cols = len(headers_lcs)
             col_width = effective_width / num_cols
             draw_table_row(pdf, headers_lcs, [col_width]*num_cols, line_height=5, border=1, align='C', fill=True)
             row = [qc["parameter"], qc["mdl"], qc["pql"], qc["spike_conc"], qc["lcs_recovery"], qc["lcsd_recovery"], qc["rpd_lcs"], qc["recovery_limits"], qc["rpd_limits"], qc["lab_qualifier"]]
             draw_table_row(pdf, row, [col_width]*num_cols, line_height=5, border=1, align='C', fill=False)
             pdf.ln(3)
         elif qc["qc_type"] == "MS":
             table_title = "MS Data"
             pdf.set_font("DejaVu", "B", 9)
             pdf.multi_cell(effective_width, 5, table_title, border=0, align="L")
             pdf.ln(2)
             headers_ms = ["Parameter", "MDL", "PQL", "Samp Conc.", "Spike Conc.", "MS % Rec.", "MSD % Rec.", "MS/MSD % RPD", "% Rec. Limits", "% RPD Limits", "Lab Qualifier"]
             num_cols = len(headers_ms)
             col_width = effective_width / num_cols
             draw_table_row(pdf, headers_ms, [col_width]*num_cols, line_height=5, border=1, align='C', fill=True)
             row = [qc["parameter"], qc["mdl"], qc["pql"], qc["sample_conc"], qc["spike_conc"], qc["ms_recovery"], qc["msd_recovery"], qc["rpd_ms"], qc["recovery_limits"], qc["rpd_limits"], qc["lab_qualifier"]]
             draw_table_row(pdf, row, [col_width]*num_cols, line_height=5, border=1, align='C', fill=False)
             pdf.ln(3)
         pdf.ln(5)
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
    render_navbar()
    if st.button("🔄 Refresh / Start Over"):
        reset_app()
    page_container = st.container()
    page_idx = st.session_state.current_page
    if page_idx == 0:
        render_cover_page()
    elif page_idx == 1:
        render_sample_summary_page()
    elif page_idx == 2:
        render_analytical_results_page()
    elif page_idx == 3:
        render_quality_control_page()
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
