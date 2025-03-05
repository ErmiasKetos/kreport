import streamlit as st
from fpdf import FPDF
import datetime
import io

def main():
    st.title("Sample Results PDF Generator")

    st.write("This app will generate a PDF report styled like your Torrent Lab screenshot.")

    # -----------------------------
    # 1. Basic Fields (Top Section)
    # -----------------------------
    st.header("Report Information")
    report_prepared_for = st.text_input("Report Prepared For", value="Ermias Leggesse, KETOS INC.")
    date_time_received = st.text_input("Date/Time Received", value="12/05/22, 12:56 pm")
    date_reported = st.text_input("Date Reported", value="12/08/22")

    # -----------------------------
    # 2. Sample Information
    # -----------------------------
    st.header("Sample Information")
    client_sample_id = st.text_input("Client Sample ID", value="Toyot-Ind-12052022")
    project_name = st.text_input("Project Name", value="")
    project_number = st.text_input("Project #", value="")
    sample_date = st.text_input("Sample Date", value="12/05/22")
    lab_sample_id = st.text_input("Lab Sample ID", value="2212087-001A")
    sample_matrix = st.text_input("Sample Matrix", value="Aqueous")
    sdg = st.text_input("SDG", value="")
    prep_batch_id = st.text_input("Prep Batch ID", value="1147246")
    prep_batch_datetime = st.text_input("Prep Batch Date/Time", value="12/07/22, 12:15:00 PM")
    prep_analyst = st.text_input("Prep Analyst", value="BJAY")

    # -----------------------------
    # 3. Parameters Table
    # -----------------------------
    st.header("Parameters (Analytes) Table")

    # Initialize a place to store parameter rows
    if "parameters" not in st.session_state:
        st.session_state["parameters"] = []

    with st.form("add_parameter_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            parameter = st.text_input("Parameter", value="")
        with col2:
            analysis_method = st.text_input("Analysis Method", value="SW6010B")
        with col3:
            df_value = st.text_input("DF", value="")
        with col4:
            mdl_value = st.text_input("MDL", value="")
        with col5:
            pql_value = st.text_input("PQL", value="")
        
        col6, col7, col8, col9 = st.columns(4)
        with col6:
            result_value = st.text_input("Result", value="")
        with col7:
            unit_value = st.text_input("Unit", value="mg/L")
        with col8:
            analyzed_date = st.text_input("Analyzed Date", value="12/08/22, 13:18")
        with col9:
            analyzed_by = st.text_input("Analyzed By", value="AT")
        
        analytical_batch = st.text_input("Analytical Batch", value="471280")

        submit_button = st.form_submit_button("Add Parameter")
        if submit_button and parameter.strip():
            st.session_state["parameters"].append({
                "parameter": parameter,
                "analysis_method": analysis_method,
                "df": df_value,
                "mdl": mdl_value,
                "pql": pql_value,
                "result": result_value,
                "unit": unit_value,
                "analyzed_date": analyzed_date,
                "analyzed_by": analyzed_by,
                "analytical_batch": analytical_batch
            })

    # Display the current parameters
    if st.session_state["parameters"]:
        st.write("**Current Parameters:**")
        for idx, p in enumerate(st.session_state["parameters"], start=1):
            st.write(
                f"{idx}. **{p['parameter']}** | "
                f"Method: {p['analysis_method']}, "
                f"DF: {p['df']}, MDL: {p['mdl']}, PQL: {p['pql']}, "
                f"Result: {p['result']} {p['unit']}, "
                f"Analyzed Date: {p['analyzed_date']}, "
                f"Analyzed By: {p['analyzed_by']}, "
                f"Batch: {p['analytical_batch']}"
            )
    else:
        st.info("No parameters added yet.")

    st.markdown("---")

    # -----------------------------
    # 4. Generate PDF
    # -----------------------------
    if st.button("Generate PDF"):
        pdf_bytes = create_pdf(
            report_prepared_for,
            date_time_received,
            date_reported,
            client_sample_id,
            project_name,
            project_number,
            sample_date,
            lab_sample_id,
            sample_matrix,
            sdg,
            prep_batch_id,
            prep_batch_datetime,
            prep_analyst,
            st.session_state["parameters"]
        )
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="SampleResults.pdf",
            mime="application/pdf"
        )


def create_pdf(
    report_prepared_for,
    date_time_received,
    date_reported,
    client_sample_id,
    project_name,
    project_number,
    sample_date,
    lab_sample_id,
    sample_matrix,
    sdg,
    prep_batch_id,
    prep_batch_datetime,
    prep_analyst,
    parameters
):
    pdf = FPDF()
    pdf.add_page()

    # -- Title Section --
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SAMPLE RESULTS", ln=True, align="C")
    pdf.ln(2)

    # -- Subtitle / Lab Info
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 6, f"Report Prepared For: {report_prepared_for}", ln=True)
    pdf.cell(0, 6, f"Date/Time Received: {date_time_received}", ln=True)
    pdf.cell(0, 6, f"Date Reported: {date_reported}", ln=True)
    pdf.ln(4)

    # -- Horizontal line
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # -- Sample Info Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Sample Information", ln=True)
    pdf.set_font("Arial", "", 11)

    # We'll do a two-column layout for these fields
    # Left column
    left_info = [
        ("Client Sample ID", client_sample_id),
        ("Project Name", project_name),
        ("Project #", project_number),
        ("Sample Date", sample_date),
    ]
    # Right column
    right_info = [
        ("Lab Sample ID", lab_sample_id),
        ("Sample Matrix", sample_matrix),
        ("SDG", sdg),
        ("Prep Batch ID", prep_batch_id),
        ("Prep Batch Date/Time", prep_batch_datetime),
        ("Prep Analyst", prep_analyst)
    ]

    # We'll create a small function to draw a label-value pair
    def info_line(label, value, width_label=40, width_value=60):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(width_label, 6, f"{label}:", border=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(width_value, 6, str(value), border=0)

    # We can do 4 lines for left side, 5 lines for right side
    max_lines = max(len(left_info), len(right_info))
    for i in range(max_lines):
        pdf.set_font("Arial", "", 10)
        pdf.ln(6)  # new line
        if i < len(left_info):
            label_l, val_l = left_info[i]
            info_line(label_l, val_l)
        else:
            # empty
            pdf.cell(100, 6, "", border=0)

        if i < len(right_info):
            label_r, val_r = right_info[i]
            pdf.set_font("Arial", "B", 10)
            pdf.cell(40, 6, f"{label_r}:", border=0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, str(val_r), border=0)
        else:
            # empty
            pdf.cell(40, 6, "", border=0)
            pdf.cell(0, 6, "", border=0)

    pdf.ln(10)

    # -- Parameters Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Parameters:", ln=True)
    pdf.ln(2)

    # Table header
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    # param, analysis method, DF, MDL, PQL, result, unit, analyzed date, analyzed by, analytical batch
    header_cols = ["Parameter", "Analysis Method", "DF", "MDL", "PQL", "Result", "Unit", "Analyzed Date", "Analyzed By", "Analytical Batch"]
    col_widths = [28, 30, 12, 12, 12, 16, 14, 26, 16, 20]

    for h, w in zip(header_cols, col_widths):
        pdf.cell(w, 8, h, border=1, align="C", fill=True)
    pdf.ln(8)

    pdf.set_font("Arial", "", 10)
    for row in parameters:
        row_data = [
            row["parameter"],
            row["analysis_method"],
            row["df"],
            row["mdl"],
            row["pql"],
            row["result"],
            row["unit"],
            row["analyzed_date"],
            row["analyzed_by"],
            row["analytical_batch"]
        ]
        for val, w in zip(row_data, col_widths):
            pdf.cell(w, 8, str(val), border=1, align="C")
        pdf.ln(8)

    # Footer disclaimers or spacing
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, "All results relate only to the items/samples tested. "
                         "This report shall not be reproduced, except in full, without written approval.")
    
    # Convert PDF to bytes
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()


if __name__ == "__main__":
    main()
