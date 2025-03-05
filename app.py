import streamlit as st
from fpdf import FPDF
import datetime
import io
import random
import string

# Comprehensive analyte-to-method mapping for water quality tests.
analyte_to_methods = {
    "Aluminum": ["EPA 200.7", "Method A"],
    "Antimony": ["EPA 200.8", "Method X"],
    "Arsenic": ["EPA 200.8", "Method X"],
    "Barium": ["EPA 200.7", "Method B"],
    "Beryllium": ["EPA 200.7", "Method C"],
    "Cadmium": ["EPA 200.8", "Method Y"],
    "Chromium": ["EPA 200.7", "Method D"],
    "Copper": ["EPA 200.7", "Method E"],
    "Lead": ["EPA 200.8", "Method F"],
    "Mercury": ["EPA 245.1", "Method G"],
    "Nickel": ["EPA 200.7", "Method H"],
    "Selenium": ["EPA 200.7", "Method I"],
    "Silver": ["EPA 200.7", "Method J"],
    "Thallium": ["EPA 200.8", "Method K"],
    "Zinc": ["EPA 200.7", "Method L"],
}

# Helper function to generate a short random ID with a prefix.
def generate_id(prefix, length=4):
    return prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def main():
    st.title("Water Quality COA (NELAC/NELAP Compliant) with Cover Page")

    # -----------------------------------
    # 0. Cover Page
    # -----------------------------------
    st.header("Cover Page (Inspired by the ALS Canada Screenshot)")
    if "cover_data" not in st.session_state:
        st.session_state["cover_data"] = {
            "lab_name": "KELP Laboratory",
            "work_order": "E02320209",
            "page_info": "Page: 1 of 1",
            "project_name": "Alberta Environment and Parks",
            "client_name": "City of Edmonton",
            "address_line": "9450 - 17 Ave NW\nEdmonton AB Canada T6N 1M9",
            "phone": "111-999-8889",
            "date_samples_received": datetime.date.today().strftime("%m-%d-%Y"),
            "date_reported": datetime.date.today().strftime("%m-%d-%Y"),
            "analysis_type": "Environmental",
            "coc_number": "ABS 271",
            "po_number": "ABS 271",
            "report_title": "CERTIFICATE OF ANALYSIS",
            "comments": "None",
            "signatories": [
                {"name": "Jane Doe", "title": "Lab Manager", "location": "Operations, Edmonton"},
                {"name": "John Smith", "title": "Lab Supervisor - Environmental", "location": "Operations, Edmonton"},
                {"name": "Ramy Galabzi", "title": "Project Manager", "location": "Operations, Edmonton"}
            ]
        }

    st.subheader("Cover Page Fields")
    st.session_state["cover_data"]["lab_name"] = st.text_input("Lab Name (Top Left)", value=st.session_state["cover_data"]["lab_name"])
    st.session_state["cover_data"]["work_order"] = st.text_input("Work Order", value=st.session_state["cover_data"]["work_order"])
    st.session_state["cover_data"]["page_info"] = st.text_input("Page Info (e.g. 'Page: 1 of 1')", value=st.session_state["cover_data"]["page_info"])
    st.session_state["cover_data"]["project_name"] = st.text_input("Project Name", value=st.session_state["cover_data"]["project_name"])
    st.session_state["cover_data"]["analysis_type"] = st.text_input("Analysis Type", value=st.session_state["cover_data"]["analysis_type"])
    st.session_state["cover_data"]["client_name"] = st.text_input("Client Name", value=st.session_state["cover_data"]["client_name"])
    st.session_state["cover_data"]["address_line"] = st.text_area("Address Line(s)", value=st.session_state["cover_data"]["address_line"])
    st.session_state["cover_data"]["phone"] = st.text_input("Phone", value=st.session_state["cover_data"]["phone"])
    st.session_state["cover_data"]["date_samples_received"] = st.text_input("Date Samples Received", value=st.session_state["cover_data"]["date_samples_received"])
    st.session_state["cover_data"]["date_reported"] = st.text_input("Date Reported", value=st.session_state["cover_data"]["date_reported"])
    st.session_state["cover_data"]["coc_number"] = st.text_input("COC #", value=st.session_state["cover_data"]["coc_number"])
    st.session_state["cover_data"]["po_number"] = st.text_input("PO #", value=st.session_state["cover_data"]["po_number"])
    st.session_state["cover_data"]["report_title"] = st.text_input("Report Title", value=st.session_state["cover_data"]["report_title"])
    st.session_state["cover_data"]["comments"] = st.text_area("Comments", value=st.session_state["cover_data"]["comments"])

    st.markdown("---")

    # ====================
    # 1. Page 1: SAMPLE SUMMARY
    # ====================
    st.header("Page 1: SAMPLE SUMMARY")
    if "page1_data" not in st.session_state:
        st.session_state["page1_data"] = {
            "report_id": "1064819",
            "report_date": datetime.date.today().strftime("%m/%d/%Y"),
            "client_name": "City of Atlantic Beach",
            "client_address": "902 Assisi Lane, Atlantic Beach, FL 32233",
            "project_id": generate_id("PJ-"),
            "samples": []
        }
    st.subheader("Report & Client Info")
    st.session_state["page1_data"]["report_id"] = st.text_input("Report ID (Page 1)", value=st.session_state["page1_data"]["report_id"])
    st.session_state["page1_data"]["report_date"] = st.text_input("Report Date (Page 1)", value=st.session_state["page1_data"]["report_date"])
    st.session_state["page1_data"]["client_name"] = st.text_input("Client Name (Page 1)", value=st.session_state["page1_data"]["client_name"])
    st.session_state["page1_data"]["client_address"] = st.text_input("Client Address (Page 1)", value=st.session_state["page1_data"]["client_address"])
    st.text("Project ID (Auto-generated):")
    st.session_state["page1_data"]["project_id"] = st.text_input("Project ID (Page 1)", value=st.session_state["page1_data"]["project_id"])

    st.subheader("Add Sample Summary Row")
    with st.form("page1_samples_form", clear_on_submit=True):
        sample_lab_id = st.text_input("Lab ID (Leave blank for auto-generation)", value="")
        sample_id = st.text_input("Sample ID", value="")
        matrix = st.text_input("Matrix", value="Water")
        date_collected = st.text_input("Date Collected", value="06/17/2021 09:40")
        date_received = st.text_input("Date Received", value="06/18/2021 12:20")
        if st.form_submit_button("Add Sample (Page 1)"):
            if not sample_lab_id.strip():
                sample_lab_id = generate_id("LS-")
            st.session_state["page1_data"]["samples"].append({
                "lab_id": sample_lab_id,
                "sample_id": sample_id,
                "matrix": matrix,
                "date_collected": date_collected,
                "date_received": date_received
            })
    if st.session_state["page1_data"]["samples"]:
        st.write("**Current Samples (Page 1):**")
        for i, s in enumerate(st.session_state["page1_data"]["samples"], 1):
            st.write(f"{i}. Lab ID: {s['lab_id']}, Sample ID: {s['sample_id']}, Matrix: {s['matrix']}, "
                     f"Collected: {s['date_collected']}, Received: {s['date_received']}")
    else:
        st.info("No samples added for Sample Summary.")
    st.markdown("---")

    # ====================
    # 2. Page 2: ANALYTICAL RESULTS
    # ====================
    st.header("Page 2: ANALYTICAL RESULTS")
    if "page2_data" not in st.session_state:
        st.session_state["page2_data"] = {
            "workorder_name": "J2108213 Priority Pollutants",
            "global_analysis_date": "06/25/2021 17:00",
            "results": [],
            "report_id": st.session_state["page1_data"]["report_id"],
            "report_date": st.session_state["page1_data"]["report_date"]
        }
    st.session_state["page2_data"]["workorder_name"] = st.text_input("Workorder Name (Page 2)", value=st.session_state["page2_data"]["workorder_name"])
    st.session_state["page2_data"]["global_analysis_date"] = st.text_input("Global Analysis Date (Page 2)", value=st.session_state["page2_data"]["global_analysis_date"])

    st.subheader("Add Analytical Result (Page 2)")
    with st.form("page2_results_form", clear_on_submit=True):
        lab_ids = [s["lab_id"] for s in st.session_state["page1_data"]["samples"]]
        if lab_ids:
            result_lab_id = st.selectbox("Select Lab ID", options=lab_ids)
        else:
            result_lab_id = st.text_input("Lab ID", value="")
        selected_parameter = st.selectbox("Parameter (Analyte)", options=list(analyte_to_methods.keys()))
        selected_method = st.selectbox("Analysis (Method)", options=analyte_to_methods[selected_parameter])
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            dilution_factor = st.text_input("DF", value="")
        with col2:
            mdl_value = st.text_input("MDL", value="")
        with col3:
            pql_value = st.text_input("PQL", value="")
        with col4:
            result_value = st.text_input("Result", value="ND")
        unit_value = st.selectbox("Unit", options=["mg/L", "µg/L", "µS/cm", "none"])

        if st.form_submit_button("Add Analytical Result (Page 2)"):
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
        for i, r in enumerate(st.session_state["page2_data"]["results"], 1):
            st.write(f"{i}. Lab ID: {r['lab_id']}, Parameter: {r['parameter']}, Analysis: {r['analysis']}, "
                     f"DF: {r['df']}, MDL: {r['mdl']}, PQL: {r['pql']}, Result: {r['result']} {r['unit']}")
    else:
        st.info("No analytical results added yet.")
    st.markdown("---")

    # ====================
    # 3. Page 3: QUALITY CONTROL DATA
    # ====================
    st.header("Page 3: QUALITY CONTROL DATA")
    if "page3_data" not in st.session_state:
        st.session_state["page3_data"] = { "qc_entries": [] }
    st.subheader("Add QC Data Entry (Page 3)")
    with st.form("page3_qc_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            qc_batch = st.text_input("QC Batch", value="DGMj/1712")
        with col2:
            qc_method = st.text_input("QC Method", value="EPA 200.8")
        col3, col4 = st.columns(2)
        with col3:
            qc_parameter = st.text_input("Parameter", value="Beryllium")
        with col4:
            qc_blank = st.text_input("Blank Result", value="0.0010 mg/L U")
        if st.form_submit_button("Add QC Entry (Page 3)"):
            if qc_batch.strip():
                st.session_state["page3_data"]["qc_entries"].append({
                    "qc_batch": qc_batch,
                    "qc_method": qc_method,
                    "parameter": qc_parameter,
                    "blank_result": qc_blank
                })
    if st.session_state["page3_data"]["qc_entries"]:
        st.write("**Current QC Data Entries (Page 3):**")
        for i, q in enumerate(st.session_state["page3_data"]["qc_entries"], 1):
            st.write(f"{i}. QC Batch: {q['qc_batch']}, Method: {q['qc_method']}, Parameter: {q['parameter']}, Blank: {q['blank_result']}")
    else:
        st.info("No QC data entries added yet.")
    st.markdown("---")

    # ====================
    # 4. Page 4: QC DATA CROSS REFERENCE TABLE
    # ====================
    st.header("Page 4: QC DATA CROSS REFERENCE TABLE")
    if "page4_data" not in st.session_state:
        st.session_state["page4_data"] = { "cross_refs": [] }
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
        st.write("**Current Cross Reference Entries (Page 4):**")
        for i, c in enumerate(st.session_state["page4_data"]["cross_refs"], 1):
            st.write(f"{i}. Lab ID: {c['lab_id']}, Sample ID: {c['sample_id']}, Prep Method: {c['prep_method']}, "
                     f"Analysis Method: {c['analysis_method']}, Prep Batch: {c['prep_batch']}, Batch Analysis: {c['batch_analysis']}")
    else:
        st.info("No cross reference entries added yet.")
    st.markdown("---")

    # ====================
    # Generate PDF (Now 5 pages total: Cover + 4 existing)
    # ====================
    if st.button("Generate 5-Page COA PDF (Cover + 4 pages)"):
        pdf_bytes = create_multi_page_pdf(
            lab_name=lab_name_input,
            lab_address=lab_address_input,
            lab_email=lab_email_input,
            lab_phone=lab_phone_input,
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

# -------------------------------------------------------------------
# PDF Generation Function: 5 pages total (Cover Page + 4 existing pages)
# -------------------------------------------------------------------
def create_multi_page_pdf(lab_name, lab_address, lab_email, lab_phone,
                          cover_data,
                          page1_data, page2_data, page3_data, page4_data):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # Effective page width after 15 mm margins
    effective_width = 180

    # ============================
    # COVER PAGE (New "Page 0")
    # ============================
    pdf.add_page()
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 14)
    # Top left: KELP Laboratory
    pdf.cell(0, 8, cover_data["lab_name"], ln=True, align="L")
    pdf.ln(4)

    # Title: "CERTIFICATE OF ANALYSIS" (or user-defined)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, cover_data["report_title"], ln=True, align="C")
    pdf.ln(6)

    # Right side or top row fields
    # We'll place them as key-value lines
    pdf.set_font("Arial", "", 10)
    pdf.cell(effective_width, 6, f"Work Order: {cover_data['work_order']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Page Info: {cover_data['page_info']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Project: {cover_data['project_name']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Analysis Type: {cover_data['analysis_type']}", ln=True, align="L")
    pdf.ln(2)

    # Next column
    pdf.cell(effective_width, 6, f"Client: {cover_data['client_name']}", ln=True, align="L")
    # For address, multi-line
    pdf.multi_cell(effective_width, 6, f"Address:\n{cover_data['address_line']}")
    pdf.ln(2)

    pdf.cell(effective_width, 6, f"Phone: {cover_data['phone']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Date Samples Received: {cover_data['date_samples_received']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"Date Reported: {cover_data['date_reported']}", ln=True, align="L")
    pdf.ln(2)

    pdf.cell(effective_width, 6, f"PO #: {cover_data['po_number']}", ln=True, align="L")
    pdf.cell(effective_width, 6, f"COC #: {cover_data['coc_number']}", ln=True, align="L")
    pdf.ln(4)

    # Comments
    pdf.set_font("Arial", "B", 10)
    pdf.cell(effective_width, 6, "Comments / Case Narrative", ln=True, align="L")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(effective_width, 5, cover_data["comments"])
    pdf.ln(4)

    # Hard-coded disclaimers or lines
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(effective_width, 4, "This cover page is an additional reference. "
                                       "The official Certificate of Analysis starts on the next page. "
                                       "No part of this cover page or any page in this document shall be reproduced, "
                                       "except in full, without the written consent of KELP Laboratory.")
    pdf.ln(4)

    # Signatories block
    pdf.set_font("Arial", "B", 10)
    pdf.cell(effective_width, 6, "Signatories", ln=True, align="L")
    pdf.set_font("Arial", "", 9)
    for signatory in cover_data["signatories"]:
        line_text = f"{signatory['name']}, {signatory['title']}   {signatory['location']}"
        pdf.cell(effective_width, 5, line_text, ln=True, align="L")
    pdf.ln(6)

    # ============================
    # PAGE 1: SAMPLE SUMMARY
    # ============================
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 6, lab_name, ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, lab_address, ln=True, align="R")
    pdf.cell(0, 5, f"Email: {lab_email}   Phone: {lab_phone}", ln=True, align="R")
    pdf.ln(4)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "CERTIFICATE OF ANALYSIS", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Arial", "", 10)
    pdf.cell(180, 6, f"Report ID: {page1_data['report_id']}", ln=True, align="L")
    pdf.cell(180, 6, f"Report Date: {page1_data['report_date']}", ln=True, align="L")
    pdf.cell(180, 6, f"Client: {page1_data['client_name']}", ln=True, align="L")
    pdf.cell(180, 6, f"Address: {page1_data['client_address']}", ln=True, align="L")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(180, 8, "SAMPLE SUMMARY", ln=True, align="L")
    pdf.ln(2)
    pdf.set_font("Arial", "B", 10)
    headers = ["Lab ID", "Sample ID", "Matrix", "Date Collected", "Date Received"]
    widths = [30, 40, 30, 40, 40]  # sum to 180
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    pdf.set_font("Arial", "", 10)
    for s in page1_data["samples"]:
        row_vals = [s["lab_id"], s["sample_id"], s["matrix"], s["date_collected"], s["date_received"]]
        for val, w in zip(row_vals, widths):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # ============================
    # PAGE 2: ANALYTICAL RESULTS
    # ============================
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(180, 8, "ANALYTICAL RESULTS", ln=True, align="L")
    pdf.ln(3)

    pdf.set_font("Arial", "", 10)
    pdf.cell(180, 6, f"Report ID: {page2_data['report_id']}", ln=True, align="L")
    pdf.cell(180, 6, f"Report Date: {page2_data['report_date']}", ln=True, align="L")
    pdf.cell(180, 6, f"Analysis Date: {page2_data['global_analysis_date']}", ln=True, align="L")
    pdf.cell(180, 6, f"Work Order: {page2_data['workorder_name']}", ln=True, align="L")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers2 = ["Lab ID", "Parameter", "Analysis", "DF", "MDL", "PQL", "Result", "Unit"]
    widths2 = [25, 35, 30, 15, 15, 15, 30, 15]  # total = 180
    for h, w in zip(headers2, widths2):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)

    pdf.set_font("Arial", "", 10)
    for r in page2_data["results"]:
        row_data = [r["lab_id"], r["parameter"], r["analysis"], r["df"], r["mdl"], r["pql"], r["result"], r["unit"]]
        for val, w in zip(row_data, widths2):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # ============================
    # PAGE 3: QUALITY CONTROL DATA
    # ============================
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(180, 8, "QUALITY CONTROL DATA", ln=True, align="L")
    pdf.ln(3)

    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers3 = ["QC Batch", "QC Method", "Parameter", "Blank Result"]
    widths3 = [35, 35, 40, 70]  # total = 180
    for h, w in zip(headers3, widths3):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)

    pdf.set_font("Arial", "", 10)
    for q in page3_data["qc_entries"]:
        row_vals = [q["qc_batch"], q["qc_method"], q["parameter"], q["blank_result"]]
        for val, w in zip(row_vals, widths3):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # ============================
    # PAGE 4: QC DATA CROSS REFERENCE TABLE
    # ============================
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(180, 8, "QC DATA CROSS REFERENCE TABLE", ln=True, align="L")
    pdf.ln(3)

    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers4 = ["Lab ID", "Sample ID", "Prep Method", "Analysis Method", "Prep Batch", "Batch Analysis"]
    widths4 = [25, 30, 30, 30, 35, 30]  # total = 180
    for h, w in zip(headers4, widths4):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)

    pdf.set_font("Arial", "", 10)
    for c in page4_data["cross_refs"]:
        row_vals = [c["lab_id"], c["sample_id"], c["prep_method"], c["analysis_method"], c["prep_batch"], c["batch_analysis"]]
        for val, w in zip(row_vals, widths4):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # Disclaimer
    pdf.ln(8)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "This report shall not be reproduced, except in full, without the written consent of KELP Laboratory. "
                         "Results pertain only to the samples tested and conform to NELAC/NELAP/ELAP standards.")

    # Page footer
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    total_pages = 5  # cover + 4
    pdf.cell(0, 10, f"Page {pdf.page_no()} of {total_pages}", 0, 0, "C")

    # Return PDF
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()

if __name__ == "__main__":
    main()
