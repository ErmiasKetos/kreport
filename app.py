import streamlit as st
from fpdf import FPDF
import datetime
import io
import uuid
import random

# Predefined analytes and their available methods (example; modify as needed)
available_methods = {
    "Nickel": ["EPA 200.7", "SW6010B"],
    "Zinc": ["EPA 200.7", "SW6010B"],
    "Potassium": ["EPA 200.7", "SW6010B"],
    "Mercury": ["EPA 245.1", "SW7470A"],
    "Arsenic": ["EPA 200.8", "MethodX"],
    "Cadmium": ["EPA 200.8", "MethodY"],
    "Copper": ["SW6010B", "EPA 200.7"],
    "Lead": ["SW6010B", "EPA 200.8"],
}

def main():
    st.title("NELAP/NELAC-Style Water Quality COA Generator")
    st.write(
        "This app creates a NELAP/NELAC-inspired Certificate of Analysis for water samples, "
        "with auto-generated Work Order and Lab Sample IDs."
    )

    # -------------------------------------------------------------------
    # 1. Basic Lab/Accreditation Info
    # -------------------------------------------------------------------
    st.header("Laboratory & Accreditation")
    lab_name = st.text_input("Lab Name", value="KELP")
    lab_address = st.text_input("Lab Address", value="520 Mercury Dr, Sunnyvale, CA 94085")
    lab_email = st.text_input("Lab Email", value="contact@ketos.co")
    accreditation_number = st.text_input("Accreditation Number", value="NELAP Cert # CA-XXXX")
    # Additional disclaimers or references
    accreditation_disclaimer = st.text_area(
        "Accreditation Disclaimer",
        value=(
            "All analyses were performed under the lab's NELAP accreditation. "
            "Methods conform to TNI/NELAC standards. Results apply only to the sample(s) tested."
        ),
    )

    st.markdown("---")

    # -------------------------------------------------------------------
    # 2. Auto-generated IDs
    # -------------------------------------------------------------------
    st.header("IDs (Auto-Generated)")
    # Generate random short strings for Work Order and Lab Sample ID
    # For example, "WO-8A3F" and "LS-9B1C"
    if "work_order" not in st.session_state:
        st.session_state["work_order"] = "WO-" + str(uuid.uuid4())[:4].upper()
    if "lab_sample_id" not in st.session_state:
        st.session_state["lab_sample_id"] = "LS-" + str(uuid.uuid4())[:4].upper()

    st.write(f"**Work Order**: {st.session_state['work_order']}")
    st.write(f"**Lab Sample ID**: {st.session_state['lab_sample_id']}")
    st.info("Refresh the app if you want new auto-generated IDs, or customize below.")
    custom_work_order = st.text_input("Override / Custom Work Order?", value=st.session_state["work_order"])
    custom_lab_id = st.text_input("Override / Custom Lab Sample ID?", value=st.session_state["lab_sample_id"])

    st.markdown("---")

    # -------------------------------------------------------------------
    # 3. Sample / Client Info
    # -------------------------------------------------------------------
    st.header("Sample & Client Info")
    page_number = st.text_input("Page Number (e.g., '1 of 3')", value="1 of 1")
    client_name = st.text_input("Client Name", value="Peace River Coal Inc.")
    project_name = st.text_input("Project Name", value="Tumbler Ridge")
    sample_condition = st.text_input("Sample Condition (e.g., 'Received at 4°C, in good condition')",
                                     value="Received at 4°C, properly preserved")
    sample_temp = st.text_input("Sample Temp (°C)", value="4.0")
    # sub-matrix / matrix
    sub_matrix = st.text_input("Sub-Matrix", value="Water")
    matrix = st.text_input("Matrix", value="Water")

    st.markdown("---")

    # -------------------------------------------------------------------
    # 4. Dates
    # -------------------------------------------------------------------
    st.header("Dates")
    collection_date = st.date_input("Collection Date", value=datetime.date.today())
    receipt_date = st.date_input("Date Received", value=datetime.date.today())
    analysis_date = st.date_input("Analysis Date", value=datetime.date.today())

    st.markdown("---")

    # -------------------------------------------------------------------
    # 5. Analyte Data
    # -------------------------------------------------------------------
    st.header("Analyte Entries (Results)")
    st.write("Select analyte, method, DF, MDL, result, and unit. Add as many as needed.")

    if "analytes" not in st.session_state:
        st.session_state["analytes"] = []

    with st.form("analyte_form", clear_on_submit=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            analyte = st.selectbox("Analyte", options=list(available_methods.keys()))
        with c2:
            method = st.selectbox("Method", options=available_methods[analyte])
        with c3:
            df_value = st.text_input("DF", value="")
        with c4:
            mdl_value = st.text_input("MDL", value="")
        with c5:
            result_value = st.text_input("Result", value="")
        unit = st.selectbox("Unit", ["mg/L", "µg/L", "µS/cm", "none"])

        submitted = st.form_submit_button("Add Analyte")
        if submitted:
            st.session_state["analytes"].append(
                {
                    "analyte": analyte,
                    "method": method,
                    "df": df_value,
                    "mdl": mdl_value,
                    "result": result_value,
                    "unit": unit,
                }
            )

    if st.session_state["analytes"]:
        st.write("**Current Analytes**")
        for idx, entry in enumerate(st.session_state["analytes"], start=1):
            st.write(
                f"{idx}. {entry['analyte']} ({entry['method']}) "
                f"DF: {entry['df']}, MDL: {entry['mdl']}, "
                f"Result: {entry['result']} {entry['unit']}"
            )
    else:
        st.info("No analytes added yet.")

    st.markdown("---")

    # -------------------------------------------------------------------
    # 6. General Comments / Additional Disclaimers
    # -------------------------------------------------------------------
    st.header("Additional Comments / Disclaimers")
    general_comments = st.text_area(
        "Enter any general or specific disclaimers:",
        value=(
            "Results are compliant with NELAC standards. "
            "All holding times and method QC requirements were met, unless otherwise noted."
        ),
    )

    st.markdown("---")

    # -------------------------------------------------------------------
    # 7. Generate PDF
    # -------------------------------------------------------------------
    if st.button("Generate NELAP COA PDF"):
        pdf_data = create_pdf_report(
            page_number=page_number,
            work_order=custom_work_order,
            lab_sample_id=custom_lab_id,
            lab_name=lab_name,
            lab_address=lab_address,
            lab_email=lab_email,
            accreditation_number=accreditation_number,
            accreditation_disclaimer=accreditation_disclaimer,
            client_name=client_name,
            project_name=project_name,
            sample_condition=sample_condition,
            sample_temp=sample_temp,
            sub_matrix=sub_matrix,
            matrix=matrix,
            collection_date=collection_date,
            receipt_date=receipt_date,
            analysis_date=analysis_date,
            analytes_list=st.session_state["analytes"],
            general_comments=general_comments,
        )
        st.download_button(
            "Download PDF",
            data=pdf_data,
            file_name="NELAP_COA_Report.pdf",
            mime="application/pdf",
        )


def create_pdf_report(
    page_number,
    work_order,
    lab_sample_id,
    lab_name,
    lab_address,
    lab_email,
    accreditation_number,
    accreditation_disclaimer,
    client_name,
    project_name,
    sample_condition,
    sample_temp,
    sub_matrix,
    matrix,
    collection_date,
    receipt_date,
    analysis_date,
    analytes_list,
    general_comments,
):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()

    # ------------------ HEADER SECTION ------------------
    pdf.set_font("Arial", "", 10)

    # Row 1: Page, Work Order, Client
    pdf.cell(40, 6, f"Page: {page_number}", border=0, align="L")
    pdf.cell(70, 6, f"Work Order: {work_order}", border=0, align="L")
    pdf.cell(0, 6, f"Client: {client_name}", border=0, align="R", ln=1)

    # Row 2: Project
    pdf.cell(40, 6, "", border=0)
    pdf.cell(70, 6, "", border=0)
    pdf.cell(0, 6, f"Project: {project_name}", border=0, align="R", ln=1)

    pdf.ln(2)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Title
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "NELAP/NELAC Environmental Laboratory Report", ln=1, align="L")

    # Sub-matrix, Matrix
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Sub-Matrix: {sub_matrix}", ln=1)
    pdf.cell(0, 5, f"Matrix: {matrix}", ln=1)
    pdf.ln(2)

    # Table heading for sample info
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(40, 6, "Lab Sample ID", 1, 0, "C", fill=True)
    pdf.cell(40, 6, "Sample Condition", 1, 0, "C", fill=True)
    pdf.cell(40, 6, "Receipt Date", 1, 0, "C", fill=True)
    pdf.cell(30, 6, "Sample Temp (°C)", 1, 0, "C", fill=True)
    pdf.cell(0, 6, "Analysis Date", 1, 1, "C", fill=True)

    # Row with sample info
    pdf.set_font("Arial", "", 9)
    pdf.cell(40, 6, str(lab_sample_id), 1, 0, "C")
    pdf.cell(40, 6, str(sample_condition), 1, 0, "C")
    pdf.cell(40, 6, receipt_date.strftime("%Y-%m-%d"), 1, 0, "C")
    pdf.cell(30, 6, str(sample_temp), 1, 0, "C")
    pdf.cell(0, 6, analysis_date.strftime("%Y-%m-%d"), 1, 1, "C")

    pdf.ln(3)

    # Additional row for collection date if desired
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 6, "Collection Date", 1, 1, "C", fill=True)

    pdf.set_font("Arial", "", 9)
    pdf.cell(50, 6, collection_date.strftime("%Y-%m-%d"), 1, 1, "C")

    pdf.ln(3)

    # ------------------ ANALYTE TABLE ------------------
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(40, 6, "Analyte", 1, 0, "C", fill=True)
    pdf.cell(40, 6, "Method", 1, 0, "C", fill=True)
    pdf.cell(20, 6, "DF", 1, 0, "C", fill=True)
    pdf.cell(20, 6, "MDL", 1, 0, "C", fill=True)
    pdf.cell(35, 6, "Result", 1, 0, "C", fill=True)
    pdf.cell(35, 6, "Unit", 1, 1, "C", fill=True)

    pdf.set_font("Arial", "", 9)
    for item in analytes_list:
        pdf.cell(40, 6, str(item["analyte"]), 1, 0, "C")
        pdf.cell(40, 6, str(item["method"]), 1, 0, "C")
        pdf.cell(20, 6, str(item["df"]), 1, 0, "C")
        pdf.cell(20, 6, str(item["mdl"]), 1, 0, "C")
        pdf.cell(35, 6, str(item["result"]), 1, 0, "C")
        pdf.cell(35, 6, str(item["unit"]), 1, 1, "C")

    pdf.ln(5)

    # ------------------ LAB INFO & ACCREDITATION ------------------
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "Laboratory & Accreditation Information", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, lab_name, ln=1)
    pdf.cell(0, 5, lab_address, ln=1)
    pdf.cell(0, 5, lab_email, ln=1)
    pdf.cell(0, 5, accreditation_number, ln=1)
    pdf.ln(3)
    pdf.multi_cell(0, 5, accreditation_disclaimer)
    pdf.ln(3)

    # ------------------ ADDITIONAL COMMENTS ------------------
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "General Comments / Disclaimers", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, general_comments)
    pdf.ln(3)

    # ------------------ FOOTER / SIGNATURES ------------------
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(
        0,
        4,
        "All analyses and QC performed in compliance with TNI/NELAC standards. "
        "This document shall not be reproduced, except in full, without written approval from the lab."
    )
    pdf.ln(4)

    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, "Signatories:", ln=1)
    pdf.ln(3)
    pdf.cell(60, 5, "________________________", ln=0, align="C")
    pdf.cell(60, 5, "________________________", ln=1, align="C")
    pdf.cell(60, 5, "Authorized Signatory", ln=0, align="C")
    pdf.cell(60, 5, "Quality Manager", ln=1, align="C")

    # Page number at bottom
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}", 0, 0, "C")

    # Output PDF to buffer
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()


if __name__ == "__main__":
    main()
