import streamlit as st
from fpdf import FPDF
import datetime
import io

# For dependent dropdown: example analytes mapped to methods.
analyte_to_methods = {
    "Nickel": ["SW6010B", "EPA 200.7", "Method2"],
    "Zinc": ["SW6010B", "EPA 200.7", "Method2"],
    "Potassium": ["SW6010B", "EPA 200.7"],
    "Mercury": ["SW7470A", "EPA 245.1"],
    "Arsenic": ["EPA 200.8", "MethodX"],
    "Cadmium": ["EPA 200.8", "MethodY"],
    "Copper": ["SW6010B", "EPA 200.7"],
    "Lead": ["SW6010B", "EPA 200.8"],
    # Add additional analytes and methods as needed.
}

def main():
    st.title("NELAC/NELAP Compliant Water Quality COA Generator")
    st.write("""
        This app generates a multi‐page Certificate of Analysis (COA) report compliant with NELAC/NELAP/ELAP standards.
        The PDF will include:
        1. SAMPLE SUMMARY  
        2. ANALYTICAL RESULTS  
        3. QUALITY CONTROL DATA  
        4. QC DATA CROSS REFERENCE TABLE
    """)

    # =====================
    # PAGE 1: SAMPLE SUMMARY
    # =====================
    st.header("Page 1: SAMPLE SUMMARY")
    if "page1_data" not in st.session_state:
        st.session_state["page1_data"] = {
            "report_id": "1064819",
            "report_date": datetime.date.today().strftime("%m/%d/%Y"),
            "client_name": "City of Atlantic Beach",
            "client_address": "902 Assisi Lane, Atlantic Beach, FL 32233",
            "samples": []  # List to hold each sample summary row.
        }

    st.subheader("Report & Client Info")
    st.session_state["page1_data"]["report_id"] = st.text_input("Report ID", value=st.session_state["page1_data"]["report_id"])
    st.session_state["page1_data"]["report_date"] = st.text_input("Report Date", value=st.session_state["page1_data"]["report_date"])
    st.session_state["page1_data"]["client_name"] = st.text_input("Client Name", value=st.session_state["page1_data"]["client_name"])
    st.session_state["page1_data"]["client_address"] = st.text_input("Client Address", value=st.session_state["page1_data"]["client_address"])

    st.subheader("Add Sample Summary Row")
    with st.form("page1_samples_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            lab_id = st.text_input("Lab ID", value="")
        with col2:
            sample_id = st.text_input("Sample ID", value="")
        with col3:
            matrix = st.text_input("Matrix", value="Water")
        with col4:
            date_collected = st.text_input("Date Collected", value="06/17/2021 09:40")
        date_received = st.text_input("Date Received", value="06/18/2021 12:20")
        if st.form_submit_button("Add Sample"):
            if lab_id.strip():
                st.session_state["page1_data"]["samples"].append({
                    "lab_id": lab_id,
                    "sample_id": sample_id,
                    "matrix": matrix,
                    "date_collected": date_collected,
                    "date_received": date_received
                })
    if st.session_state["page1_data"]["samples"]:
        st.write("**Current Samples:**")
        for i, s in enumerate(st.session_state["page1_data"]["samples"], 1):
            st.write(f"{i}. Lab ID: {s['lab_id']}, Sample ID: {s['sample_id']}, Matrix: {s['matrix']}, Collected: {s['date_collected']}, Received: {s['date_received']}")
    else:
        st.info("No samples added for Sample Summary.")

    st.markdown("---")

    # =====================
    # PAGE 2: ANALYTICAL RESULTS
    # =====================
    st.header("Page 2: ANALYTICAL RESULTS")
    if "page2_data" not in st.session_state:
        st.session_state["page2_data"] = {
            "workorder_name": "J2108213 Priority Pollutants",
            "results": []
        }
    st.session_state["page2_data"]["workorder_name"] = st.text_input("Workorder Name", value=st.session_state["page2_data"]["workorder_name"])

    st.subheader("Add Analytical Result")
    with st.form("page2_results_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            lab_id = st.text_input("Lab ID", value="")
        with col2:
            parameter = st.text_input("Parameter", value="")
        with col3:
            result = st.text_input("Result", value="ND")
        col4, col5 = st.columns(2)
        with col4:
            dilution_factor = st.text_input("Dilution Factor (DF)", value="")
        with col5:
            method_used = st.text_input("Method", value="EPA 200.8")
        analysis_date = st.text_input("Analysis Date", value="06/25/2021 17:00")
        if st.form_submit_button("Add Analytical Result"):
            if lab_id.strip():
                st.session_state["page2_data"]["results"].append({
                    "lab_id": lab_id,
                    "parameter": parameter,
                    "result": result,
                    "df": dilution_factor,
                    "method": method_used,
                    "analysis_date": analysis_date
                })
    if st.session_state["page2_data"]["results"]:
        st.write("**Current Analytical Results:**")
        for i, r in enumerate(st.session_state["page2_data"]["results"], 1):
            st.write(f"{i}. Lab ID: {r['lab_id']}, Parameter: {r['parameter']}, Result: {r['result']}, DF: {r['df']}, Method: {r['method']}, Date: {r['analysis_date']}")
    else:
        st.info("No analytical results added yet.")

    st.markdown("---")

    # =====================
    # PAGE 3: QUALITY CONTROL DATA
    # =====================
    st.header("Page 3: QUALITY CONTROL DATA")
    if "page3_data" not in st.session_state:
        st.session_state["page3_data"] = { "qc_entries": [] }
    st.subheader("Add QC Data Entry")
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
        st.write("**Current QC Data Entries:**")
        for i, q in enumerate(st.session_state["page3_data"]["qc_entries"], 1):
            st.write(f"{i}. QC Batch: {q['qc_batch']}, Method: {q['qc_method']}, Parameter: {q['parameter']}, Blank: {q['blank_result']}")
    else:
        st.info("No QC data entries added yet.")

    st.markdown("---")

    # =====================
    # PAGE 4: QUALITY CONTROL DATA CROSS REFERENCE TABLE
    # =====================
    st.header("Page 4: QC DATA CROSS REFERENCE TABLE")
    if "page4_data" not in st.session_state:
        st.session_state["page4_data"] = { "cross_refs": [] }
    st.subheader("Add Cross Reference Entry")
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
        if st.form_submit_button("Add Cross Reference"):
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
        st.write("**Current Cross Reference Entries:**")
        for i, c in enumerate(st.session_state["page4_data"]["cross_refs"], 1):
            st.write(f"{i}. Lab ID: {c['lab_id']}, Sample ID: {c['sample_id']}, Prep Method: {c['prep_method']}, "
                     f"Analysis Method: {c['analysis_method']}, Prep Batch: {c['prep_batch']}, Batch Analysis: {c['batch_analysis']}")
    else:
        st.info("No cross reference entries added yet.")

    st.markdown("---")

    # =====================
    # Generate 4-Page PDF
    # =====================
    if st.button("Generate 4-Page COA PDF"):
        pdf_bytes = create_multi_page_pdf(
            page1_data=st.session_state["page1_data"],
            page2_data=st.session_state["page2_data"],
            page3_data=st.session_state["page3_data"],
            page4_data=st.session_state["page4_data"]
        )
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="MultiPage_COA.pdf",
            mime="application/pdf"
        )

# -------------------------------------------------------------------
# PDF Generation Function: Creates 4 pages with elegant formatting
# -------------------------------------------------------------------
def create_multi_page_pdf(page1_data, page2_data, page3_data, page4_data):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # ---- PAGE 1: SAMPLE SUMMARY ----
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "CERTIFICATE OF ANALYSIS", ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Report ID: {page1_data['report_id']}    Report Date: {page1_data['report_date']}", ln=True, align="L")
    pdf.cell(0, 6, f"Client: {page1_data['client_name']}", ln=True, align="L")
    pdf.cell(0, 6, f"Address: {page1_data['client_address']}", ln=True, align="L")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "SAMPLE SUMMARY", ln=True, align="L")
    pdf.ln(2)

    # Table headers for sample summary
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers = ["Lab ID", "Sample ID", "Matrix", "Date Collected", "Date Received"]
    widths = [30, 40, 30, 40, 40]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    pdf.set_font("Arial", "", 10)
    for s in page1_data["samples"]:
        row = [s["lab_id"], s["sample_id"], s["matrix"], s["date_collected"], s["date_received"]]
        for val, w in zip(row, widths):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # ---- PAGE 2: ANALYTICAL RESULTS ----
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "ANALYTICAL RESULTS", ln=True, align="L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Workorder: {page2_data['workorder_name']}", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers2 = ["Lab ID", "Parameter", "Result", "DF", "Method", "Analysis Date"]
    widths2 = [30, 40, 30, 15, 40, 35]
    for h, w in zip(headers2, widths2):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    pdf.set_font("Arial", "", 10)
    for r in page2_data["results"]:
        row = [r["lab_id"], r["parameter"], r["result"], r["df"], r["method"], r["analysis_date"]]
        for val, w in zip(row, widths2):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # ---- PAGE 3: QUALITY CONTROL DATA ----
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "QUALITY CONTROL DATA", ln=True, align="L")
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers3 = ["QC Batch", "QC Method", "Parameter", "Blank Result"]
    widths3 = [35, 35, 40, 70]
    for h, w in zip(headers3, widths3):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    pdf.set_font("Arial", "", 10)
    for q in page3_data["qc_entries"]:
        row = [q["qc_batch"], q["qc_method"], q["parameter"], q["blank_result"]]
        for val, w in zip(row, widths3):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    # ---- PAGE 4: QC DATA CROSS REFERENCE TABLE ----
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "QC DATA CROSS REFERENCE TABLE", ln=True, align="L")
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers4 = ["Lab ID", "Sample ID", "Prep Method", "Analysis Method", "Prep Batch", "Batch Analysis"]
    widths4 = [25, 30, 30, 30, 35, 35]
    for h, w in zip(headers4, widths4):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)
    pdf.set_font("Arial", "", 10)
    for c in page4_data["cross_refs"]:
        row = [c["lab_id"], c["sample_id"], c["prep_method"], c["analysis_method"], c["prep_batch"], c["batch_analysis"]]
        for val, w in zip(row, widths4):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    pdf.ln(8)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "This report shall not be reproduced, except in full, without the written consent of the laboratory. "
                         "Results pertain only to the samples tested and conform to NELAC/NELAP/ELAP standards.")
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} of 4", 0, 0, "C")

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()

if __name__ == "__main__":
    main()
