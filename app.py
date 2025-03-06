import streamlit as st
from fpdf import FPDF
import datetime
import io
import random
import string

#####################################
# Helper Data & Functions
#####################################

# Mapping of analyte to list of possible methods
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

def generate_id(prefix, length=4):
    """Generate a short random ID with the given prefix."""
    return prefix + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

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
    lab_email = "info@ketos.co"
    lab_phone = "(xxx) xxx-xxxx"
    
    auto_work_order = generate_id("WO-")
    auto_coc_number = generate_id("COC-")
    default_date = datetime.date.today().strftime("%m/%d/%Y")  # default for sample dates

    #####################################
    # 0. Cover Page Data
    #####################################
    if "cover_data" not in st.session_state:
        st.session_state["cover_data"] = {
            "lab_name": lab_name,  # fixed
            "work_order": auto_work_order,
            "project_name": "Alberta Environment and Parks",
            "client_name": "City of Edmonton",
            "address_line": "9450 - 17 Ave NW\nEdmonton AB Canada T6N 1M9",
            "phone": "111-999-8889",
            "date_samples_received": default_date,
            "date_reported": default_date,
            "analysis_type": "Environmental",
            "coc_number": auto_coc_number,
            "po_number": "ABS 271",
            "report_title": "CERTIFICATE OF ANALYSIS",
            "comments": "None",
            "signatory_name": "John Smith",
            "signatory_title": "Lab Manager",
        }
    st.header("Cover Page Fields (Optional Edits)")
    st.session_state["cover_data"]["project_name"] = st.text_input("Project Name", value=st.session_state["cover_data"]["project_name"])
    st.session_state["cover_data"]["client_name"] = st.text_input("Client Name", value=st.session_state["cover_data"]["client_name"])
    st.session_state["cover_data"]["address_line"] = st.text_area("Address", value=st.session_state["cover_data"]["address_line"])
    st.session_state["cover_data"]["analysis_type"] = st.text_input("Analysis Type", value=st.session_state["cover_data"]["analysis_type"])
    st.session_state["cover_data"]["comments"] = st.text_area("Comments / Narrative", value=st.session_state["cover_data"]["comments"])
    
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
            "project_id": generate_id("PJ-"),
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
                sample_lab_id = generate_id("LS-")
            st.session_state["page1_data"]["samples"].append({
                "lab_id": sample_lab_id,
                "sample_id": sample_id,
                "matrix": matrix,
                "date_collected": sample_date_collected,
                "date_received": sample_date_received
            })
    
    if st.session_state["page1_data"]["samples"]:
        st.write("**Current Water Samples (Page 1):**")
        for i, s in enumerate(st.session_state["page1_data"]["samples"], 1):
            st.write(f"{i}. Lab ID: {s['lab_id']}, Sample ID: {s['sample_id']}, Matrix: {s['matrix']}, "
                     f"Collected: {s['date_collected']}, Received: {s['date_received']}")
    else:
        st.info("No water samples added yet.")
    
    st.markdown("---")
    
    #####################################
    # 2. PAGE 2: ANALYTICAL RESULTS
    #####################################
    if "page2_data" not in st.session_state:
        st.session_state["page2_data"] = {
            "workorder_name": auto_work_order,
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
        unit_value = st.selectbox("Unit", ["mg/L", "µg/L", "µS/cm", "none"])
    
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
        for i, r in enumerate(st.session_state["page2_data"]["results"], 1):
            st.write(f"{i}. Lab ID: {r['lab_id']}, Parameter: {r['parameter']}, Analysis: {r['analysis']}, "
                     f"DF: {r['df']}, MDL: {r['mdl']}, PQL: {r['pql']}, Result: {r['result']} {r['unit']}")
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
    
        if st.form_submit_button("Add QC Entry"):
            if qc_batch.strip():
                st.session_state["page3_data"]["qc_entries"].append({
                    "qc_batch": qc_batch,
                    "qc_method": qc_method,
                    "parameter": qc_parameter,
                    "blank_result": qc_blank
                })
    
    if st.session_state["page3_data"]["qc_entries"]:
        st.write("**Current QC Data (Page 3):**")
        for i, q in enumerate(st.session_state["page3_data"]["qc_entries"], 1):
            st.write(f"{i}. QC Batch: {q['qc_batch']}, Method: {q['qc_method']}, Parameter: {q['parameter']}, Blank: {q['blank_result']}")
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
        for i, c in enumerate(st.session_state["page4_data"]["cross_refs"], 1):
            st.write(f"{i}. Lab ID: {c['lab_id']}, Sample ID: {c['sample_id']}, "
                     f"Prep Method: {c['prep_method']}, Analysis Method: {c['analysis_method']}, "
                     f"Prep Batch: {c['prep_batch']}, Batch Analysis: {c['batch_analysis']}")
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
                      cover_data,
                      page1_data, page2_data, page3_data, page4_data):
    pdf = FPDF("P", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_text_color(0, 0, 0)   # ensure black text
    effective_width = 180
    total_pages = 5  # cover + 4 pages

    # ---------------------------
    # 0. COVER PAGE
    # ---------------------------
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, cover_data["report_title"], ln=True, align="C")
    pdf.ln(4)
    
    # We use no headings, just 2-col table for global info
    # We'll color the label cells with a light gray, data cells with white fill
    left_width = effective_width / 2
    right_width = effective_width / 2

    # Function to print a label->data row
    def table_row(label_text, data_text):
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(240, 240, 240)  # label cell color
        pdf.cell(left_width, 6, label_text, border=1, ln=0, align="L", fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_fill_color(255, 255, 255)  # data cell color
        pdf.cell(right_width, 6, data_text, border=1, ln=1, align="L", fill=True)

    # Table: Work Order, Project, Analysis Type, COC #, PO #, Date Samples Received, Date Reported
    table_row("Work Order:", cover_data["work_order"])
    table_row("Project:", cover_data["project_name"])
    table_row("Analysis Type:", cover_data["analysis_type"])
    table_row("COC #:", cover_data["coc_number"])
    table_row("PO #:", cover_data["po_number"])
    table_row("Date Samples Received:", cover_data["date_samples_received"])
    table_row("Date Reported:", cover_data["date_reported"])
    pdf.ln(4)

    # Another table for client info
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Client Name:", border=1, align="L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(effective_width - 40, 6, cover_data["client_name"], border=1, ln=True, align="L", fill=True)

    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Address:", border=1, align="L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(255, 255, 255)
    # multi_cell for address
    start_y = pdf.get_y()
    pdf.multi_cell(effective_width - 40, 6, cover_data["address_line"], border=1, align="L")
    end_y = pdf.get_y()
    pdf.ln(2 if (end_y - start_y) < 12 else 0)

    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 6, "Phone:", border=1, align="L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(effective_width - 40, 6, cover_data["phone"], border=1, ln=True, align="L", fill=True)
    pdf.ln(4)

    # Comments
    pdf.set_font("Arial", "B", 10)
    pdf.cell(effective_width, 6, "Comments / Case Narrative", ln=True, align="L")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(effective_width, 5, cover_data["comments"], border=1)
    pdf.ln(4)

    # Signature text above the signature
    pdf.set_font("Arial", "", 10)
    signature_text = (
        "All data for associated QC met EPA or laboratory specification(s) except where noted in the case narrative. "
        "This report supersedes any previous report(s) with this reference. Results apply to the sample(s) as submitted. "
        "This document shall not be reproduced, except in full."
    )
    pdf.multi_cell(effective_width, 5, signature_text, border=0)
    pdf.ln(2)

    # Insert the signature image (adjust name, x/y, width as needed)
    current_y = pdf.get_y()
    try:
        pdf.image("lab_managersign.jpg", x=15, y=current_y, w=30)  # or .png if you have .png
        # Move the cursor below the image
        pdf.set_y(current_y + 5)
    except:
        pdf.cell(0, 5, "[Signature image not found]", ln=True)

    # Name & Title under the signature
    pdf.ln(5)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 5, f"{cover_data['signatory_name']}", ln=True, align="L")
    pdf.cell(0, 5, f"{cover_data['signatory_title']}",ln=True, align="L")

    # ---------------------------
    # 1. PAGE 1: SAMPLE SUMMARY
    # ---------------------------
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
    widths = [30, 40, 30, 40, 40]  # total=180
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    
    pdf.set_font("Arial", "", 10)
    for s in page1_data["samples"]:
        row_vals = [s["lab_id"], s["sample_id"], s["matrix"], s["date_collected"], s["date_received"]]
        for val, w in zip(row_vals, widths):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)
    
    # ---------------------------
    # 2. PAGE 2: ANALYTICAL RESULTS
    # ---------------------------
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
    widths2 = [25, 35, 30, 15, 15, 15, 30, 15]  # sum=180
    for h, w in zip(headers2, widths2):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    
    pdf.set_font("Arial", "", 10)
    for r in page2_data["results"]:
        row_data = [r["lab_id"], r["parameter"], r["analysis"], r["df"], r["mdl"], r["pql"], r["result"], r["unit"]]
        for val, w in zip(row_data, widths2):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)
    
    # ---------------------------
    # 3. PAGE 3: QUALITY CONTROL DATA
    # ---------------------------
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(180, 8, "QUALITY CONTROL DATA", ln=True, align="L")
    pdf.ln(3)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers3 = ["QC Batch", "QC Method", "Parameter", "Blank Result"]
    widths3 = [35, 35, 40, 70]  # sum=180
    for h, w in zip(headers3, widths3):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    
    pdf.set_font("Arial", "", 10)
    for q in page3_data["qc_entries"]:
        row_vals = [q["qc_batch"], q["qc_method"], q["parameter"], q["blank_result"]]
        for val, w in zip(row_vals, widths3):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)
    
    # ---------------------------
    # 4. PAGE 4: QC DATA CROSS REFERENCE TABLE
    # ---------------------------
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(180, 8, "QC DATA CROSS REFERENCE TABLE", ln=True, align="L")
    pdf.ln(3)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers4 = ["Lab ID", "Sample ID", "Prep Method", "Analysis Method", "Prep Batch", "Batch Analysis"]
    widths4 = [25, 30, 30, 30, 35, 30]  # sum=180
    for h, w in zip(headers4, widths4):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    
    pdf.set_font("Arial", "", 10)
    for c in page4_data["cross_refs"]:
        row_vals = [c["lab_id"], c["sample_id"], c["prep_method"], c["analysis_method"], c["prep_batch"], c["batch_analysis"]]
        for val, w in zip(row_vals, widths4):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)
    
    pdf.ln(8)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "This report shall not be reproduced, except in full, without the written consent of KELP Laboratory. "
                         "Results pertain only to the samples tested and conform to NELAC/NELAP/ELAP standards.")
    
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} of {total_pages}", 0, 0, "C")
    
    # Return the PDF as bytes
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()

if __name__ == "__main__":
    main()
