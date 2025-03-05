import streamlit as st
from fpdf import FPDF
import datetime
import io

# -------------------------------
# Custom PDF Class with Header and Footer
# -------------------------------
class PDF(FPDF):
    def header(self):
        # Lab header information
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, f"{self.lab_name} Laboratory", ln=True, align="C")
        self.set_font("Arial", "", 12)
        self.cell(0, 10, self.lab_address, ln=True, align="C")
        self.cell(0, 10, self.lab_email, ln=True, align="C")
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        # Position footer 15 mm from bottom
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

# -------------------------------
# Predefined analyte-method mapping (from your attached list)
# Adjust the dictionary as needed.
# -------------------------------
analyte_methods = {
    "Nitrite as N": ["E300.0", "Alternate N-Method"],
    "Nitrate as N": ["E300.0", "Alternate Nitrate Method"],
    "Copper": ["SW6010B"],
    "Zinc": ["SW6010B"],
    "Iron": ["SW6010B"],
    "Manganese": ["SW6010B"],
    "o-Phosphate as P": ["E300.0"],
    "Sulfate": ["E300.0"],
    "Calcium Hardness (as CaCO3)": ["SM2340B"],
    "Total Hardness (as CaCO3)": ["SM2340B"],
    "Molybdenum": ["SW6010B"],
    "Potassium": ["SW6010B"],
    "Silica": ["SW6010B"],
    "Nickel": ["SW6010B"],
    "Mercury": ["SW7470A"],
    "Arsenic": ["SW6010B"],
    "Cadmium": ["SW6010B"],
    "Lead": ["SW6010B"],
}

# -------------------------------
# Main Streamlit Application
# -------------------------------
def main():
    st.title("Water Quality Report Generator")
    st.write(
        """
        This app lets you enter sample metadata, choose analytes and methods from a dropdown list,
        and add additional details to generate a PDF report styled similarly to your sample lab reports.
        """
    )

    # Fixed Lab Information
    lab_name = "KELP"
    lab_address = "520 Mercury Dr, Sunnyvale"
    lab_email = "info@ketos.co"
    report_date = datetime.date.today().strftime("%m/%d/%Y")
    
    # Report metadata inputs
    st.subheader("Report Information")
    client_name = st.text_input("Client Name", value="KETOS INC.")
    work_order = st.text_input("Work Order No.", value="2212087")
    project_id = st.text_input("Project/Sample ID", value="SampleID-001")
    sample_location = st.text_input("Sample Location", value="Site Location")
    date_sampled = st.date_input("Date Sampled", value=datetime.date.today())
    time_sampled = st.text_input("Time Sampled", value="09:00 AM")
    date_received = st.date_input("Date Received", value=datetime.date.today())
    date_reported = st.date_input("Date Reported", value=datetime.date.today())
    
    case_narrative = st.text_area("Case Narrative", value="Enter any narrative or notes here...")

    st.markdown("---")
    st.subheader("Analyte Entries")
    st.write("Add the analytes to be included in the report. Use the dropdown to select analyte and method.")

    # Initialize analytes list in session_state if not present
    if "analytes" not in st.session_state:
        st.session_state["analytes"] = []

    # Form to add a new analyte entry
    with st.form("analyte_form", clear_on_submit=True):
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        # Dropdown for analyte selection
        selected_analyte = col1.selectbox("Analyte", options=list(analyte_methods.keys()))
        # Dropdown for method, options depend on analyte selection
        selected_method = col2.selectbox("Method", options=analyte_methods[selected_analyte])
        
        df_value = col3.text_input("DF", value="")
        mdl_value = col4.text_input("MDL", value="")
        result_value = col5.text_input("Result", value="")
        unit = col6.selectbox("Unit", options=["mg/L", "µg/L", "µS/cm", "none"])
        
        submitted = st.form_submit_button("Add Analyte")
        if submitted:
            st.session_state["analytes"].append({
                "analyte": selected_analyte,
                "method": selected_method,
                "df": df_value,
                "mdl": mdl_value,
                "result": result_value,
                "unit": unit
            })

    # Display current list of analytes
    if st.session_state["analytes"]:
        st.write("### Current Analyte Entries")
        for idx, entry in enumerate(st.session_state["analytes"], 1):
            st.write(
                f"{idx}. {entry['analyte']} ({entry['method']}), DF: {entry['df']}, "
                f"MDL: {entry['mdl']}, Result: {entry['result']} {entry['unit']}"
            )
    else:
        st.info("No analyte entries added yet.")

    st.markdown("---")
    # Button to generate PDF
    if st.button("Generate PDF Report"):
        pdf_bytes = create_pdf_report(
            lab_name, lab_address, lab_email,
            client_name, work_order, project_id, sample_location,
            date_sampled, time_sampled, date_received, date_reported,
            report_date, case_narrative, st.session_state["analytes"]
        )
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="WaterQualityReport.pdf",
            mime="application/pdf"
        )

# -------------------------------
# Function to Create PDF Report
# -------------------------------
def create_pdf_report(
    lab_name, lab_address, lab_email,
    client_name, work_order, project_id, sample_location,
    date_sampled, time_sampled, date_received, date_reported,
    report_date, case_narrative, analytes_list
):
    # Create an instance of our custom PDF class and pass lab info to it
    pdf = PDF()
    pdf.lab_name = lab_name
    pdf.lab_address = lab_address
    pdf.lab_email = lab_email

    pdf.add_page()

    # Report metadata block (below header)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Report Date: {report_date}", ln=True)
    pdf.cell(0, 8, f"Work Order No.: {work_order}", ln=True)
    pdf.cell(0, 8, f"Client: {client_name}", ln=True)
    pdf.cell(0, 8, f"Project/Sample ID: {project_id}", ln=True)
    pdf.cell(0, 8, f"Sample Location: {sample_location}", ln=True)
    pdf.cell(0, 8, f"Date/Time Sampled: {date_sampled} {time_sampled}", ln=True)
    pdf.cell(0, 8, f"Date Received: {date_received}", ln=True)
    pdf.cell(0, 8, f"Date Reported: {date_reported}", ln=True)
    pdf.ln(10)
    
    # Analyte Table Header
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Analyte", 1, 0, "C")
    pdf.cell(30, 10, "Method", 1, 0, "C")
    pdf.cell(20, 10, "DF", 1, 0, "C")
    pdf.cell(20, 10, "MDL", 1, 0, "C")
    pdf.cell(40, 10, "Result", 1, 0, "C")
    pdf.cell(40, 10, "Unit", 1, 1, "C")

    # Analyte Table Rows
    pdf.set_font("Arial", "", 12)
    for item in analytes_list:
        pdf.cell(40, 10, str(item["analyte"]), 1, 0, "C")
        pdf.cell(30, 10, str(item["method"]), 1, 0, "C")
        pdf.cell(20, 10, str(item["df"]), 1, 0, "C")
        pdf.cell(20, 10, str(item["mdl"]), 1, 0, "C")
        pdf.cell(40, 10, str(item["result"]), 1, 0, "C")
        pdf.cell(40, 10, str(item["unit"]), 1, 1, "C")
    
    pdf.ln(10)
    # Case Narrative Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "CASE NARRATIVE", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, case_narrative)
    
    pdf.ln(10)
    # Disclaimer / Approval section
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0, 5,
        "Disclaimer: This report is generated based on user-entered data. "
        "Results are for informational purposes only. This report shall not be reproduced, "
        "except in full, without written approval."
    )
    pdf.ln(5)
    pdf.cell(0, 5, "Approved by: ___________________  Director - Drinking Water Compliance", ln=True)

    # Output the PDF to a bytes buffer
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.read()

if __name__ == "__main__":
    main()
