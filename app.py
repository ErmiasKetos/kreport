import streamlit as st
from fpdf import FPDF
import datetime
import io

def main():
    st.title("Water Quality Report Generator")
    st.write(
        """
        This app lets you enter sample and analyte data then generate a PDF report 
        styled similar to your sample lab reports.
        """
    )

    # Lab information (fixed for this app)
    lab_name = "KELP"
    lab_address = "520 Mercury Dr, Sunnyvale"
    lab_email = "info@ketos.co"
    report_date = datetime.date.today().strftime("%m/%d/%Y")

    # Client and sample metadata
    client_name = st.text_input("Client Name", value="KELP INC.")
    project_id = st.text_input("Project/Sample ID", value="2501095")
    sample_location = st.text_input("Sample Location", value="Site Location")
    date_sampled = st.date_input("Date Sampled", value=datetime.date.today())
    time_sampled = st.text_input("Time Sampled", value="09:00 AM")

    st.markdown("---")
    st.subheader("Analyte Entries")
    st.write("Add the analytes you want to include in this report.")

    # Initialize analytes list in session_state if not already present
    if "analytes" not in st.session_state:
        st.session_state["analytes"] = []

    # Form to add new analyte entry
    with st.form("analyte_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        analyte = col1.text_input("Analyte", value="")
        method = col2.text_input("Method", value="")
        df_value = col3.text_input("DF", value="")
        mdl_value = col4.text_input("MDL", value="")
        result_value = col5.text_input("Result", value="")
        unit = st.selectbox("Unit", options=["mg/L", "µg/L", "µS/cm", "none"])
        submitted = st.form_submit_button("Add Analyte")
        if submitted and analyte.strip():
            st.session_state["analytes"].append({
                "analyte": analyte,
                "method": method,
                "df": df_value,
                "mdl": mdl_value,
                "result": result_value,
                "unit": unit
            })

    # Display current list of analytes
    if st.session_state["analytes"]:
        st.write("### Current Analytes")
        for idx, entry in enumerate(st.session_state["analytes"], 1):
            st.write(
                f"{idx}. Analyte: {entry['analyte']}, Method: {entry['method']}, "
                f"DF: {entry['df']}, MDL: {entry['mdl']}, Result: {entry['result']} {entry['unit']}"
            )
    else:
        st.info("No analytes added yet.")

    st.markdown("---")
    # Button to generate and download the PDF report
    if st.button("Generate PDF Report"):
        pdf_bytes = create_pdf_report(
            lab_name,
            lab_address,
            lab_email,
            client_name,
            project_id,
            sample_location,
            date_sampled,
            time_sampled,
            st.session_state["analytes"],
            report_date,
        )
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="WaterQualityReport.pdf",
            mime="application/pdf"
        )

def create_pdf_report(
    lab_name,
    lab_address,
    lab_email,
    client_name,
    project_id,
    sample_location,
    date_sampled,
    time_sampled,
    analytes_list,
    report_date
):
    pdf = FPDF()
    pdf.add_page()

    # Header (lab info)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"{lab_name} Laboratory", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, lab_address, ln=True, align="C")
    pdf.cell(0, 10, lab_email, ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    # Report date and client/sample info
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Report Date: {report_date}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Client and Sample Information:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Client Name: {client_name}", ln=True)
    pdf.cell(0, 8, f"Project/Sample ID: {project_id}", ln=True)
    pdf.cell(0, 8, f"Sample Location: {sample_location}", ln=True)
    pdf.cell(0, 8, f"Date/Time Sampled: {date_sampled} {time_sampled}", ln=True)
    pdf.ln(10)

    # Table header for analytes
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Analyte", 1, 0, "C")
    pdf.cell(30, 10, "Method", 1, 0, "C")
    pdf.cell(20, 10, "DF", 1, 0, "C")
    pdf.cell(20, 10, "MDL", 1, 0, "C")
    pdf.cell(40, 10, "Result", 1, 0, "C")
    pdf.cell(40, 10, "Unit", 1, 1, "C")

    # Table rows for each analyte
    pdf.set_font("Arial", "", 12)
    for item in analytes_list:
        pdf.cell(40, 10, str(item["analyte"]), 1, 0, "C")
        pdf.cell(30, 10, str(item["method"]), 1, 0, "C")
        pdf.cell(20, 10, str(item["df"]), 1, 0, "C")
        pdf.cell(20, 10, str(item["mdl"]), 1, 0, "C")
        pdf.cell(40, 10, str(item["result"]), 1, 0, "C")
        pdf.cell(40, 10, str(item["unit"]), 1, 1, "C")

    # Footer/disclaimer section
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0,
        5,
        "Disclaimer: This report is generated based on the data entered by the user. "
        "All results are provided for informational purposes only."
    )
    pdf.ln(5)
    pdf.cell(0, 5, "Approved by: ___________________  Director - Drinking Water Compliance", ln=True)

    # Save PDF to bytes buffer for download
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.read()

if __name__ == "__main__":
    main()
