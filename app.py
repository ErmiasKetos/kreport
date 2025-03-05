import streamlit as st
from fpdf import FPDF
import datetime
import io

# Predefined analytes and their available methods (update as needed)
available_methods = {
    "Nickel": ["SW6010B", "Method2"],
    "Zinc": ["SW6010B", "Method2"],
    "Potassium": ["SW6010B", "Method2"],
    "Mercury": ["SW7470A", "MethodA"],
    "Arsenic": ["MethodX", "MethodY"],
    "Cadmium": ["MethodX", "MethodY"],
    "Copper": ["SW6010B", "MethodZ"],
    "Lead": ["SW6010B", "MethodZ"],
    # … add more analytes as needed
}

def main():
    st.title("COA PDF Generator")
    st.write("Generate a Certificate of Analysis (COA) PDF report inspired by your attached sample.")

    # --- Report Header Information ---
    st.header("Report Information")
    lab_name = st.text_input("Laboratory Name", value="Peace River Coal Inc.")
    lab_address = st.text_input("Laboratory Address", value="PO Box 919 - 13 Heavy Industrial Park, Tumbler Ridge BC Canada V0C 2W0")
    lab_contact = st.text_input("Laboratory Contact", value="Larry Hantler / Tasnia Tarannum")
    work_order = st.text_input("Work Order No.", value="FJ2301068")
    client_name = st.text_input("Client", value="Peace River Coal Inc.")
    project_name = st.text_input("Project", value="Tumbler Ridge")
    date_samples_received = st.date_input("Date Samples Received", value=datetime.date.today())
    date_analysis_commenced = st.date_input("Date Analysis Commenced", value=datetime.date.today())
    issue_date = st.date_input("Issue Date", value=datetime.date.today())
    
    st.markdown("---")
    
    # --- General Comments Section ---
    st.header("General Comments / Case Narrative")
    general_comments = st.text_area("General Comments", 
        value=("The analytical methods used are developed using internationally recognized reference methods. "
               "Where a reported < result is higher than the LOR, this may be due to sample dilution or insufficient sample volume. "
               "Refer to the attached Quality Control Interpretive Report for further details."))
    
    st.markdown("---")
    
    # --- Analyte Entry Section with Dependent Dropdowns ---
    st.header("Analyte Entries")
    st.write("Select the analyte and its corresponding method, then enter DF, MDL, and the result.")
    
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
        unit = st.selectbox("Unit", options=["mg/L", "µg/L", "µS/cm", "none"])
        submit_analyte = st.form_submit_button("Add Analyte")
        if submit_analyte:
            st.session_state["analytes"].append({
                "analyte": analyte,
                "method": method,
                "df": df_value,
                "mdl": mdl_value,
                "result": result_value,
                "unit": unit
            })
    
    if st.session_state["analytes"]:
        st.write("### Analyte List")
        for idx, entry in enumerate(st.session_state["analytes"], start=1):
            st.write(f"{idx}. {entry['analyte']} - {entry['method']} | DF: {entry['df']}, MDL: {entry['mdl']}, "
                     f"Result: {entry['result']} {entry['unit']}")
    else:
        st.info("No analytes added yet.")
    
    st.markdown("---")
    
    # --- Generate PDF Button ---
    if st.button("Generate COA PDF"):
        pdf_bytes = create_pdf_report(
            lab_name, lab_address, lab_contact, work_order, client_name, project_name,
            date_samples_received.strftime("%d-%b-%Y"),
            date_analysis_commenced.strftime("%d-%b-%Y"),
            issue_date.strftime("%d-%b-%Y"),
            general_comments,
            st.session_state["analytes"]
        )
        st.download_button("Download PDF", data=pdf_bytes, file_name="COA_Report.pdf", mime="application/pdf")


def create_pdf_report(lab_name, lab_address, lab_contact, work_order, client_name, project_name,
                      date_samples_received, date_analysis_commenced, issue_date,
                      general_comments, analytes_list):
    pdf = FPDF()
    pdf.add_page()
    
    # --- Certificate Title and Header ---
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(0, 0, 128)
    pdf.cell(0, 10, "CERTIFICATE OF ANALYSIS", ln=True, align="C")
    pdf.ln(2)
    
    # Work order and page info
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Work Order: {work_order}", ln=True)
    pdf.cell(0, 8, "Page: 1 of 6", ln=True)  # Static page info; can be automated if multi-page
    pdf.ln(3)
    
    # Horizontal line
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # --- Laboratory Information ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Laboratory Information:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, lab_name, ln=True)
    pdf.cell(0, 8, lab_address, ln=True)
    pdf.cell(0, 8, f"Contact: {lab_contact}", ln=True)
    pdf.ln(3)
    
    # --- Client/Project Information ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Client / Project Information:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Client: {client_name}", ln=True)
    pdf.cell(0, 8, f"Project: {project_name}", ln=True)
    pdf.cell(0, 8, f"Date Samples Received: {date_samples_received}", ln=True)
    pdf.cell(0, 8, f"Date Analysis Commenced: {date_analysis_commenced}", ln=True)
    pdf.cell(0, 8, f"Issue Date: {issue_date}", ln=True)
    pdf.ln(5)
    
    # --- General Comments / Narrative ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "General Comments:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, general_comments)
    pdf.ln(5)
    
    # --- Analytical Results Table ---
    pdf.set_font("Arial", "B", 11)
    # Set header background color
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(35, 8, "Analyte", 1, 0, "C", fill=True)
    pdf.cell(30, 8, "Method", 1, 0, "C", fill=True)
    pdf.cell(20, 8, "DF", 1, 0, "C", fill=True)
    pdf.cell(20, 8, "MDL", 1, 0, "C", fill=True)
    pdf.cell(35, 8, "Result", 1, 0, "C", fill=True)
    pdf.cell(30, 8, "Unit", 1, 1, "C", fill=True)
    
    pdf.set_font("Arial", "", 11)
    for entry in analytes_list:
        pdf.cell(35, 8, str(entry["analyte"]), 1, 0, "C")
        pdf.cell(30, 8, str(entry["method"]), 1, 0, "C")
        pdf.cell(20, 8, str(entry["df"]), 1, 0, "C")
        pdf.cell(20, 8, str(entry["mdl"]), 1, 0, "C")
        pdf.cell(35, 8, str(entry["result"]), 1, 0, "C")
        pdf.cell(30, 8, str(entry["unit"]), 1, 1, "C")
    
    pdf.ln(10)
    
    # --- Footer: Disclaimer and Signatories ---
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 5, "This report supersedes any previous report(s) with this reference. "
                          "Results apply only to the sample(s) as received. This document shall not be reproduced, except in full.")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Signatories:", ln=True)
    pdf.ln(2)
    pdf.cell(80, 8, "________________________", ln=0, align="C")
    pdf.cell(80, 8, "________________________", ln=1, align="C")
    pdf.cell(80, 8, "Authorized Signatory", ln=0, align="C")
    pdf.cell(80, 8, "Laboratory Manager", ln=1, align="C")
    
    # --- Page Footer with Page Number (optional) ---
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} of 6", 0, 0, "C")
    
    # --- Export PDF to Bytes Buffer ---
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.read()


if __name__ == "__main__":
    main()
