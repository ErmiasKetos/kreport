import streamlit as st
from fpdf import FPDF
import datetime
import io

# Predefined analytes and their available methods (example list; modify as needed)
available_methods = {
    "Nickel": ["SW6010B", "Method2"],
    "Zinc": ["SW6010B", "Method2"],
    "Potassium": ["SW6010B", "Method2"],
    "Mercury": ["SW7470A", "MethodA"],
    "Arsenic": ["MethodX", "MethodY"],
    "Cadmium": ["MethodX", "MethodY"],
    "Copper": ["SW6010B", "MethodZ"],
    "Lead": ["SW6010B", "MethodZ"],
}

def main():
    st.title("COA PDF Generator (ALS-Style Layout)")
    st.write(
        "Generate a Certificate of Analysis (COA) PDF report inspired by your attached sample/screenshot."
    )

    # --- Top-level user inputs ---
    st.header("Report / Sample Information")
    page_number = st.text_input("Page Number (e.g., '3 of 6')", value="3 of 6")
    work_order = st.text_input("Work Order", value="FJ2301068")
    client_name = st.text_input("Client Name", value="Peace River Coal Inc.")
    project_name = st.text_input("Project Name", value="Tumbler Ridge")
    # Could store the sub-matrix/matrix if you want them to appear in the PDF
    sub_matrix = st.text_input("Sub-Matrix", value="Water")
    matrix = st.text_input("Matrix", value="Water")

    st.markdown("---")
    # Lab info
    st.header("Lab Information")
    lab_name = st.text_input("Lab Name", value="KELP")
    lab_address = st.text_input("Lab Address", value="520 Mercury Dr, Sunnyvale, CA 94085")
    lab_email = st.text_input("Lab Email", value="contact@ketos.co")

    st.markdown("---")
    # Date info
    st.header("Dates & Additional Info")
    collection_date = st.date_input("Collection Date", value=datetime.date.today())
    analysis_date = st.date_input("Analysis Date", value=datetime.date.today())
    # Possibly for "Client Sample ID" vs "Lab Sample ID"
    client_sample_id = st.text_input("Client Sample ID", value="DWTF")
    lab_sample_id = st.text_input("Lab Sample ID", value="FJ2301068-001")

    st.markdown("---")
    # General Comments
    st.header("General Comments / Narrative")
    general_comments = st.text_area(
        "Enter narrative or disclaimers:",
        value=(
            "The analytical methods used are developed using internationally recognized reference methods. "
            "Where a reported < result is higher than the LOR, this may be due to sample dilution or insufficient sample volume. "
            "Refer to the attached Quality Control Interpretive Report for further details."
        ),
    )

    st.markdown("---")
    # Analyte input
    st.header("Analyte Entries")
    st.write("Select the analyte and method, then enter DF, MDL, Result, and pick the unit.")

    if "analytes" not in st.session_state:
        st.session_state["analytes"] = []

    with st.form("analyte_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            analyte = st.selectbox("Analyte", options=list(available_methods.keys()))
        with col2:
            method = st.selectbox("Method", options=available_methods[analyte])
        with col3:
            df_value = st.text_input("DF", value="")
        with col4:
            mdl_value = st.text_input("MDL", value="")
        with col5:
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
        st.write("### Current Analytes")
        for idx, entry in enumerate(st.session_state["analytes"], 1):
            st.write(
                f"{idx}. {entry['analyte']} - {entry['method']} | "
                f"DF: {entry['df']}, MDL: {entry['mdl']}, "
                f"Result: {entry['result']} {entry['unit']}"
            )
    else:
        st.info("No analytes added yet.")

    st.markdown("---")
    if st.button("Generate PDF"):
        pdf_data = create_pdf_report(
            page_number,
            work_order,
            client_name,
            project_name,
            sub_matrix,
            matrix,
            lab_name,
            lab_address,
            lab_email,
            collection_date,
            analysis_date,
            client_sample_id,
            lab_sample_id,
            general_comments,
            st.session_state["analytes"],
        )
        st.download_button(
            "Download PDF",
            data=pdf_data,
            file_name="COA_Report.pdf",
            mime="application/pdf",
        )


def create_pdf_report(
    page_number,
    work_order,
    client_name,
    project_name,
    sub_matrix,
    matrix,
    lab_name,
    lab_address,
    lab_email,
    collection_date,
    analysis_date,
    client_sample_id,
    lab_sample_id,
    general_comments,
    analytes_list,
):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()

    # -- Header row with Page, Work Order, Client, Project --
    pdf.set_font("Arial", "", 10)
    # Row 1
    pdf.cell(40, 6, f"Page: {page_number}", border=0, align="L")
    pdf.cell(70, 6, f"Work Order: {work_order}", border=0, align="L")
    pdf.cell(0, 6, f"Client: {client_name}", border=0, align="R", ln=1)

    # Row 2
    pdf.cell(40, 6, "", border=0)
    pdf.cell(70, 6, "", border=0)
    pdf.cell(0, 6, f"Project: {project_name}", border=0, align="R", ln=1)

    # Horizontal line
    pdf.ln(2)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # -- Title: Analytical Results --
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Analytical Results", ln=1, align="L")

    # Sub-Matrix / Matrix row
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Sub-Matrix: {sub_matrix}", ln=1)
    pdf.cell(0, 5, f"Matrix: {matrix}", ln=1)
    pdf.ln(2)

    # Table heading row for sample info
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 6, "Client sample ID", 1, 0, "C", fill=True)
    pdf.cell(40, 6, "Lab sample ID", 1, 0, "C", fill=True)
    pdf.cell(40, 6, "Collection Date", 1, 0, "C", fill=True)
    pdf.cell(40, 6, "Analysis Date", 1, 0, "C", fill=True)
    pdf.cell(0, 6, "", 1, 1, "C", fill=True)  # Empty cell to align with screenshot style

    # Table row with actual sample info
    pdf.set_font("Arial", "", 9)
    pdf.cell(50, 6, str(client_sample_id), 1, 0, "C")
    pdf.cell(40, 6, str(lab_sample_id), 1, 0, "C")
    pdf.cell(40, 6, collection_date.strftime("%Y-%m-%d"), 1, 0, "C")
    pdf.cell(40, 6, analysis_date.strftime("%Y-%m-%d"), 1, 0, "C")
    pdf.cell(0, 6, "", 1, 1, "C")

    pdf.ln(3)

    # -- The big results table: CAS #, Method, LOR, Unit, DF, etc. 
    #   For simplicity, we'll just do: Analyte, Method, DF, MDL, Result, Unit
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(40, 6, "Analyte", 1, 0, "C", fill=True)
    pdf.cell(30, 6, "Method", 1, 0, "C", fill=True)
    pdf.cell(25, 6, "DF", 1, 0, "C", fill=True)
    pdf.cell(25, 6, "MDL", 1, 0, "C", fill=True)
    pdf.cell(35, 6, "Result", 1, 0, "C", fill=True)
    pdf.cell(35, 6, "Unit", 1, 1, "C", fill=True)

    pdf.set_font("Arial", "", 9)
    for item in analytes_list:
        pdf.cell(40, 6, str(item["analyte"]), 1, 0, "C")
        pdf.cell(30, 6, str(item["method"]), 1, 0, "C")
        pdf.cell(25, 6, str(item["df"]), 1, 0, "C")
        pdf.cell(25, 6, str(item["mdl"]), 1, 0, "C")
        pdf.cell(35, 6, str(item["result"]), 1, 0, "C")
        pdf.cell(35, 6, str(item["unit"]), 1, 1, "C")

    pdf.ln(5)

    # -- Lab Info Section
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "Lab Information", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, lab_name, ln=1)
    pdf.cell(0, 5, lab_address, ln=1)
    pdf.cell(0, 5, lab_email, ln=1)
    pdf.ln(4)

    # -- General Comments / Narrative
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "General Comments / Narrative", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, general_comments)
    pdf.ln(3)

    # -- Footer / disclaimers
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(
        0,
        4,
        "Disclaimer: This report supersedes any previous report(s) with this reference. "
        "Results apply only to the sample(s) as received. This document shall not be reproduced, except in full."
    )
    pdf.ln(5)

    # Signatures
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, "Signatories:", ln=1)
    pdf.ln(3)
    pdf.cell(60, 5, "________________________", ln=0, align="C")
    pdf.cell(60, 5, "________________________", ln=1, align="C")
    pdf.cell(60, 5, "Authorized Signatory", ln=0, align="C")
    pdf.cell(60, 5, "Lab Manager", ln=1, align="C")

    # Page number at bottom
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}", 0, 0, "C")

    # Output
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()


if __name__ == "__main__":
    main()
