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
    st.session_state.clear()
    st.rerun()

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
    """Wrapper for st.date_input that handles '%m/%d/%Y' format."""
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

def draw_table_row(pdf, data, widths, line_height=5, border=1, align='C', fill=False):
    """
    Draws a row of multi-cell columns with text wrapping.
    """
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    max_lines = 1
    for text, w in zip(data, widths):
        text_width = pdf.get_string_width(text)
        # A rough estimate of how many lines we might need:
        lines = math.ceil(text_width / (w - 2))  # subtract a bit for padding
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
    # Move the cursor to the end of the row
    pdf.set_xy(x_start, y_start + cell_height)


# Some example analytes & methods
analyte_to_methods = {
    "Alkalinity": ["SM 2320 B-1997"],
    "Ammonia": ["SM 4500-NH₃ C"],
    "Calcium": ["EPA 200.5", "EPA 200.7"],
    # etc...
}

PAGES = ["Cover Page", "Sample Summary", "Analytical Results", "Quality Control Data"]

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_page = 0
    st.session_state.setdefault("cover_data", {})
    st.session_state.setdefault("page1_data", {})
    st.session_state.setdefault("page2_data", {})
    st.session_state.setdefault("page3_data", {})

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

    cover["project_name"] = st.text_input("Project Name", value=cover.get("project_name",""))
    cover["client_name"] = st.text_input("Client Name", value=cover.get("client_name",""))
    street, addr_details = address_autofill_field("Street Address", default=cover.get("street", ""))
    cover["street"] = street
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

    cover["analysis_type"] = st.text_input("Analysis Type", value=cover.get("analysis_type","Environmental"))
    cover["date_samples_received"] = get_date_input("Date Samples Received", default_str=cover.get("date_samples_received", ""))
    cover["date_reported"] = get_date_input("Date Reported", default_str=cover.get("date_reported",""))
    cover["comments"] = st.text_area("Comments/Narrative", value=cover.get("comments","None"))
    cover["address_line"] = (cover["street"] + ", " + cover["city"] + ", " +
                             cover["state"] + " " + cover["zip"] + ", " + cover["country"])
    sample_type = st.selectbox("Sample Type", ["GW","DW","WW","IW","SW"], 0)
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
        d_collect = get_date_input("Date Collected", "")
        d_recv = get_date_input("Date Received", st.session_state["cover_data"].get("date_samples_received",""))
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
            col1, col2 = st.columns([4,1])
            with col1:
                st.write(f"{i+1}) Lab ID: {s_['lab_id']}, Sample ID: {s_['sample_id']}, "
                         f"Matrix: {s_['matrix']}, Date Collected: {s_['date_collected']}, "
                         f"Date Received: {s_['date_received']}")
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
        p2["workorder_name"] = st.session_state["cover_data"].get("work_order","WO-UNKNOWN")
        p2["report_id"] = st.session_state["page1_data"].get("report_id","0000000")
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
        sample_lab_ids = [s_["lab_id"] for s_ in st.session_state["page1_data"].get("samples",[])]
        if sample_lab_ids:
            chosen_lab_id = st.selectbox("Lab ID", sample_lab_ids)
            s_id = next((s_["sample_id"] for s_ in st.session_state["page1_data"]["samples"]
                         if s_["lab_id"] == chosen_lab_id), "")
            st.write(f"Corresponding Sample ID: {s_id}")
        else:
            chosen_lab_id = st.text_input("Lab ID","")
            s_id = ""

        analysis_date = get_date_input("Analysis Date", datetime.date.today().strftime("%m/%d/%Y"))
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
        for i, row_ in enumerate(p2["results"]):
            col1, col2 = st.columns([4,1])
            with col1:
                st.write(f"{i+1}) Lab ID: {row_['lab_id']} (Sample ID: {row_.get('sample_id','')}), "
                         f"Parameter: {row_['parameter']}, Analysis: {row_['analysis']}, DF: {row_['df']}, "
                         f"MDL: {row_['mdl']}, PQL: {row_['pql']}, Result: {row_['result']} {row_['unit']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_anal_{i}"):
                    del p2["results"][i]
                    st.rerun()
    else:
        st.info("No results yet.")

    render_nav_buttons()

def render_quality_control_page():
    st.header("Quality Control Data")
    p3 = st.session_state["page3_data"]
    p3.setdefault("qc_entries", [])

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
        for i, qc_ in enumerate(p3["qc_entries"]):
            col1, col2 = st.columns([4,1])
            with col1:
                st.write(f"{i+1}) QC Batch: {qc_['qc_batch']}, Method: {qc_['qc_method']}, "
                         f"Parameter: {qc_['parameter']}, Unit: {qc_['unit']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_qc_{i}"):
                    del p3["qc_entries"][i]
                    st.rerun()
    else:
        st.info("No QC entries yet.")
    render_nav_buttons()

def create_pdf_report(lab_name, lab_address, lab_email, lab_phone, cover_data, page1_data, page2_data, page3_data):
    pdf = PDF("P", "mm", "A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "DejaVuSans-Italic.ttf", uni=True)
    pdf.set_font("DejaVu", "", 10)
    effective_width = 180
    total_pages = 4

    # -- PAGE 1: Cover Page
    #  (omitted for brevity; you can keep your existing code for the cover page)

    # -- PAGE 2: Sample Summary
    #  (omitted for brevity; you can keep your existing code for the sample summary)

    # -- PAGE 3: Analytical Results
    #  (omitted for brevity; you can keep your existing code for the analytical results)

    # -- PAGE 4: QUALITY CONTROL DATA
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "QUALITY CONTROL DATA", ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, f"Work Order: {page2_data.get('workorder_name','')}", ln=True, align="L")
    pdf.cell(0, 5, f"Report ID: {page2_data.get('report_id','')}", ln=True, align="L")
    pdf.cell(0, 5, f"Report Date: {page2_data.get('report_date','')}", ln=True, align="L")
    pdf.ln(5)

    # Predefine column widths for each type of table to avoid overlap
    # 1) Method Blank: 5 columns
    mb_widths = [30, 15, 15, 70, 50]  # sum=180
    # 2) LCS: 10 columns
    lcs_widths = [25, 15, 15, 20, 20, 20, 20, 20, 10, 15]  # sum=180
    # 3) MS: 11 columns
    ms_widths = [20, 15, 15, 15, 20, 20, 20, 20, 15, 10, 10]  # sum=180

    # Go through each QC entry
    for qc_ in page3_data.get("qc_entries", []):
        pdf.set_font("DejaVu", "B", 10)
        # Left-justify the QC header info
        pdf.multi_cell(0, 5, f"QC Analysis (Method): {qc_['qc_method']} | Parameter: {qc_['parameter']}", 0, 'L')
        pdf.multi_cell(0, 5, f"QC Batch: {qc_['qc_batch']}", 0, 'L')
        pdf.multi_cell(0, 5, f"Unit: {qc_['unit']}", 0, 'L')
        pdf.ln(3)

        if qc_["qc_type"] == "MB":
            # Method Blank table
            pdf.set_font("DejaVu", "B", 9)
            pdf.multi_cell(0, 5, "Method Blank Data", 0, 'L')
            pdf.ln(2)
            headers_mb = ["Parameter", "MDL", "PQL", "Method Blank Conc.", "Lab Qualifier"]
            # Draw the header row
            draw_table_row(pdf, headers_mb, mb_widths, line_height=5, border=1, align='C', fill=True)
            # Now the data row
            pdf.set_font("DejaVu", "", 9)
            row_data = [
                qc_["parameter"],
                qc_["mdl"],
                qc_["pql"],
                qc_["method_blank"],
                qc_["lab_qualifier"]
            ]
            draw_table_row(pdf, row_data, mb_widths, line_height=5, border=1, align='C', fill=False)
            pdf.ln(5)

        elif qc_["qc_type"] == "LCS":
            # LCS table
            pdf.set_font("DejaVu", "B", 9)
            pdf.multi_cell(0, 5, "LCS Data", 0, 'L')
            pdf.ln(2)
            headers_lcs = ["Parameter", "MDL", "PQL", "Spike Conc.", "LCS % Rec.", "LCSD % Rec.",
                           "LCS/LCSD % RPD", "% Rec. Limits", "% RPD Limits", "Lab Qualifier"]
            draw_table_row(pdf, headers_lcs, lcs_widths, line_height=5, border=1, align='C', fill=True)
            pdf.set_font("DejaVu", "", 9)
            row_data = [
                qc_["parameter"], qc_["mdl"], qc_["pql"], qc_["spike_conc"], qc_["lcs_recovery"],
                qc_["lcsd_recovery"], qc_["rpd_lcs"], qc_["recovery_limits"], qc_["rpd_limits"],
                qc_["lab_qualifier"]
            ]
            draw_table_row(pdf, row_data, lcs_widths, line_height=5, border=1, align='C', fill=False)
            pdf.ln(5)

        else:  # MS
            # MS table
            pdf.set_font("DejaVu", "B", 9)
            pdf.multi_cell(0, 5, "MS Data", 0, 'L')
            pdf.ln(2)
            headers_ms = ["Parameter", "MDL", "PQL", "Samp Conc.", "Spike Conc.", "MS % Rec.",
                          "MSD % Rec.", "MS/MSD % RPD", "% Rec. Limits", "% RPD Limits", "Lab Qualifier"]
            draw_table_row(pdf, headers_ms, ms_widths, line_height=5, border=1, align='C', fill=True)
            pdf.set_font("DejaVu", "", 9)
            row_data = [
                qc_["parameter"], qc_["mdl"], qc_["pql"], qc_.get("sample_conc",""),
                qc_["spike_conc"], qc_.get("ms_recovery",""), qc_.get("msd_recovery",""),
                qc_.get("rpd_ms",""), qc_["recovery_limits"], qc_["rpd_limits"], qc_["lab_qualifier"]
            ]
            draw_table_row(pdf, row_data, ms_widths, line_height=5, border=1, align='C', fill=False)
            pdf.ln(5)

        pdf.ln(5)

    pdf.ln(8)
    pdf.set_font("DejaVu", "I", 8)
    pdf.multi_cell(0, 5,
        "This report shall not be reproduced, except in full, without the written consent of KELP Laboratory. "
        "Test results reported relate only to the samples as received by the laboratory."
    )
    pdf.set_y(-15)
    pdf.set_font("DejaVu", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} of {total_pages}", 0, 0, "C")

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()

def main():
    st.title("Water Quality COA")
    render_navbar()
    if st.button("🔄 Refresh / Start Over"):
        reset_app()

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
