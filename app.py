import streamlit as st
from fpdf import FPDF
import datetime
import io

# Example dictionary for dependent dropdown (Analyte -> Methods).
analyte_to_methods = {
    "Nickel": ["SW6010B", "EPA 200.7", "Method2"],
    "Zinc": ["SW6010B", "EPA 200.7", "Method2"],
    "Potassium": ["SW6010B", "EPA 200.7"],
    "Mercury": ["SW7470A", "EPA 245.1"],
    "Arsenic": ["EPA 200.8", "MethodX"],
    "Cadmium": ["EPA 200.8", "MethodY"],
    "Copper": ["SW6010B", "EPA 200.7"],
    "Lead": ["SW6010B", "EPA 200.8"],
    # ... Add more as needed
}

def main():
    st.title("Apex-Style Analytical Report Generator")

    st.write(
        "This app creates a PDF report with a layout inspired by the Apex Laboratories example, "
        "including a dependent dropdown for Analyte → Method."
    )

    # -------------------------------------------------------------------
    # 1. Lab & Report Header
    # -------------------------------------------------------------------
    st.header("Laboratory & Report Header")
    lab_name = st.text_input("Lab Name", value="Apex Laboratories LLC")
    lab_address = st.text_input("Lab Address", value="6700 S.W. Sandburg Street, Tigard OR 97223")
    lab_phone = st.text_input("Lab Phone", value="(503) 718-2323")
    lab_fax = st.text_input("Lab Fax", value="(503) 624-1649")
    report_number = st.text_input("Report #", value="AA1137-01")
    date_reported = st.date_input("Date Reported", value=datetime.date.today())
    project_manager = st.text_input("Project Manager / Reviewer", value="Jason Wadsock, Project Manager")

    st.markdown("---")

    # -------------------------------------------------------------------
    # 2. Client / Project Info
    # -------------------------------------------------------------------
    st.header("Client & Project Info")
    client_name = st.text_input("Client Name", value="GQ Consulting")
    client_address = st.text_input("Client Address", value="16800 SW 65th Ave, Suite 201, Lake Oswego, OR 97035")
    project_name = st.text_input("Project Name", value="Parkland Park & Rec")
    sample_matrix = st.text_input("Sample Matrix", value="Drinking Water")
    # Additional fields from screenshot
    date_sampled = st.date_input("Date Sampled", value=datetime.date.today())
    # Possibly a field for "Purchase Order" or "Project #"
    purchase_order = st.text_input("Purchase Order / Project #", value="")
    # user can also specify "Sample ID" or "Field ID"
    field_id = st.text_input("Client Field ID", value="1-40-B-7-A10 (AA#1157-01)")

    st.markdown("---")

    # -------------------------------------------------------------------
    # 3. Analyte Table (with Dependent Dropdown)
    # -------------------------------------------------------------------
    st.header("Analyte Entries (Parameters)")
    if "analytes" not in st.session_state:
        st.session_state["analytes"] = []

    with st.form("analyte_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_analyte = st.selectbox("Analyte", list(analyte_to_methods.keys()))
        with col2:
            possible_methods = analyte_to_methods[selected_analyte]
            selected_method = st.selectbox("Method", possible_methods)

        col3, col4, col5, col6, col7 = st.columns(5)
        with col3:
            detection_limit = st.text_input("Detection Limit", value="0.0050")
        with col4:
            result_value = st.text_input("Result", value="ND")
        with col5:
            unit_value = st.text_input("Unit", value="mg/L")
        with col6:
            dilution_factor = st.text_input("Dilution Factor", value="")
        with col7:
            date_analyzed = st.text_input("Date Analyzed", value="")

        method_ref = st.text_input("Method Ref / Type", value="EPA 200.8 (ICP-MS)")
        # optional: date/time of method or additional fields
        st.write("Optionally, specify any additional fields below (MDL, PQL, etc.)")

        if st.form_submit_button("Add Analyte"):
            st.session_state["analytes"].append({
                "analyte": selected_analyte,
                "method": selected_method,
                "detection_limit": detection_limit,
                "result": result_value,
                "unit": unit_value,
                "dilution_factor": dilution_factor,
                "date_analyzed": date_analyzed,
                "method_ref": method_ref
            })

    if st.session_state["analytes"]:
        st.write("**Current Analytes**")
        for idx, entry in enumerate(st.session_state["analytes"], 1):
            st.write(
                f"{idx}. **{entry['analyte']}**  "
                f"(Method: {entry['method']} | "
                f"Detection Limit: {entry['detection_limit']} | "
                f"Result: {entry['result']} {entry['unit']} | "
                f"Dilution: {entry['dilution_factor']} | "
                f"Analyzed: {entry['date_analyzed']} | "
                f"Method Ref: {entry['method_ref']})"
            )
    else:
        st.info("No analytes added yet.")

    st.markdown("---")

    # -------------------------------------------------------------------
    # 4. Generate PDF
    # -------------------------------------------------------------------
    if st.button("Generate Apex-Style PDF"):
        pdf_bytes = create_pdf_report(
            lab_name=lab_name,
            lab_address=lab_address,
            lab_phone=lab_phone,
            lab_fax=lab_fax,
            report_number=report_number,
            date_reported=date_reported.strftime("%m/%d/%Y"),
            project_manager=project_manager,
            client_name=client_name,
            client_address=client_address,
            project_name=project_name,
            sample_matrix=sample_matrix,
            date_sampled=date_sampled.strftime("%m/%d/%Y"),
            purchase_order=purchase_order,
            field_id=field_id,
            analytes_list=st.session_state["analytes"],
        )
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="ApexStyleReport.pdf",
            mime="application/pdf"
        )

def create_pdf_report(
    lab_name,
    lab_address,
    lab_phone,
    lab_fax,
    report_number,
    date_reported,
    project_manager,
    client_name,
    client_address,
    project_name,
    sample_matrix,
    date_sampled,
    purchase_order,
    field_id,
    analytes_list
):
    pdf = FPDF()
    pdf.add_page()

    # ------------------ APEX LAB HEADER ------------------
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, lab_name, ln=1, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, lab_address, ln=1, align="R")
    pdf.cell(0, 5, f"Phone: {lab_phone}   Fax: {lab_fax}", ln=1, align="R")
    pdf.ln(3)

    # Title line
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "ANALYTICAL REPORT", ln=1, align="C")
    pdf.ln(2)

    # Horizontal line
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # Subheader
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "ANALYTICAL SAMPLE RESULTS", ln=1, align="C")
    pdf.ln(3)

    # Info row (similar to top row in screenshot)
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 5, f"Client: {client_name}", border=0)
    pdf.cell(0, 5, f"Report ID: {report_number}", border=0, ln=1)
    pdf.cell(100, 5, f"Address: {client_address}", border=0)
    pdf.cell(0, 5, f"Date Reported: {date_reported}", border=0, ln=1)
    pdf.cell(100, 5, f"Project: {project_name}", border=0)
    pdf.cell(0, 5, f"Project Manager: {project_manager}", border=0, ln=1)
    pdf.ln(4)

    # Another horizontal line
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Show some sample details
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"Sample Matrix: {sample_matrix}", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Date Sampled: {date_sampled}", ln=1)
    pdf.cell(0, 5, f"Purchase Order: {purchase_order}", ln=1)
    pdf.cell(0, 5, f"Field ID: {field_id}", ln=1)
    pdf.ln(4)

    # Table heading
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    headers = ["Analyte", "Result", "Unit", "Det. Limit", "Dilution", "Method", "Date Analyzed", "Method Ref"]
    col_widths = [30, 20, 10, 20, 20, 25, 30, 40]

    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln(7)

    pdf.set_font("Arial", "", 9)
    # Rows
    for row in analytes_list:
        # each row has analyte, result, unit, detection_limit, dilution_factor, method, date_analyzed, method_ref
        # we can reorder them to match the columns
        row_data = [
            row["analyte"],
            row["result"],
            row["unit"],
            row["detection_limit"],
            row["dilution_factor"],
            row["method"],
            row["date_analyzed"],
            row["method_ref"]
        ]
        for val, w in zip(row_data, col_widths):
            pdf.cell(w, 7, str(val), border=1, align="C")
        pdf.ln(7)

    pdf.ln(5)
    # Disclaimer / notes
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(
        0,
        4,
        "ND = Not Detected above detection limit. "
        "Results are reported on an as-received basis. "
        "This report relates only to the samples tested. "
        "It shall not be reproduced, except in full, without written approval from the lab."
    )
    pdf.ln(5)

    # Signature
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "Apex Laboratories", ln=1)
    pdf.cell(0, 5, project_manager, ln=1)

    # Page number at bottom
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} of 1", 0, 0, "C")

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()


if __name__ == "__main__":
    main()
