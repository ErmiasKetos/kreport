import streamlit as st
from fpdf import FPDF
import datetime
import io
import random
import string
import requests
from collections import defaultdict

def reset_app():
    """Clears all session state variables and reloads the app."""
    st.session_state.clear()  # This removes all session state variables
    st.rerun()  # Use this instead of st.experimental_rerun()


#####################################
# PDF Class for Page Numbers
#####################################
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        # If you have DejaVu fonts, use them:
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", 0, 0, "C")

#####################################
# Helper Functions
#####################################
def generate_id(prefix="LS", length=6):
    return prefix + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

def generate_qc_batch():
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    digits = ''.join(random.choices("0123456789", k=3))
    return letters + digits

def generate_method_blank():
    letters = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = ''.join(random.choices("0123456789", k=5))
    return letters + digits

def generate_coc_number():
    return "COC-" + ''.join(random.choices("0123456789", k=8))



#####################################
# Streamlit UI Functions
#####################################

PAGES = ["Cover Page", "Sample Summary", "Analytical Results", "Quality Control"]
#Predefined lists for selecting parameters
analyte_to_methods = {
    "Total Dissolved Solids": ["EPA 160.1", "SM 2540C"],
    "Total Suspended Solids": ["EPA 160.2", "SM 2540D"],
    "pH": ["EPA 150.1", "SM 4500-H+ B"],
    "Conductivity": ["EPA 120.1", "SM 2510B"],
    "Turbidity": ["EPA 180.1", "SM 2130B"],
    "Chlorine": ["EPA 330.5", "SM 4500-Cl G"],
    "Dissolved Oxygen": ["EPA 360.1", "SM 4500-O G"],
    "BOD": ["EPA 405.1", "SM 5210B"],
    "COD": ["EPA 410.4", "SM 5220D"],
    "Oil and Grease": ["EPA 1664", "SM 5520B"],
    "Total Coliform": ["SM 9221B", "SM 9221F"],
    "Fecal Coliform": ["SM 9222D", "SM 9222G"],
    "Enterococcus": ["EPA 1600", "SM 9230B"],
    "Nitrate": ["EPA 300.0", "SM 4500-NO3- E"],
    "Nitrite": ["EPA 354.1", "SM 4500-NO2- B"],
    "Ammonia": ["EPA 350.1", "SM 4500-NH3 G"],
    "TKN": ["EPA 351.2", "SM 4500-Norg D"],
    "Phosphorus": ["EPA 365.1", "SM 4500-P F"],
    "Sulfate": ["EPA 300.0", "SM 4500-SO4 2- E"],
    "Chloride": ["EPA 300.0", "SM 4500-Cl- E"],
    "Fluoride": ["EPA 340.2", "SM 4500-F- C"],
    "Bromide": ["EPA 300.0", "SM 4500-Br- B"],
    "Calcium": ["EPA 200.7", "SM 3120B"],
    "Magnesium": ["EPA 200.7", "SM 3120B"],
    "Sodium": ["EPA 200.7", "SM 3120B"],
    "Potassium": ["EPA 200.7", "SM 3120B"],
    "Iron": ["EPA 200.7", "SM 3120B"],
    "Manganese": ["EPA 200.7", "SM 3120B"],
    "Aluminum": ["EPA 200.7", "SM 3120B"],
    "Arsenic": ["EPA 200.8", "SM 3113B"],
    "Cadmium": ["EPA 200.8", "SM 3113B"],
    "Chromium": ["EPA 200.8", "SM 3113B"],
    "Copper": ["EPA 200.8", "SM 3113B"],
    "Lead": ["EPA 200.8", "SM 3113B"],
    "Mercury": ["EPA 245.1", "SM 3112B"],
    "Nickel": ["EPA 200.8", "SM 3113B"],
    "Selenium": ["EPA 200.8", "SM 3113B"],
    "Silver": ["EPA 200.8", "SM 3113B"],
    "Zinc": ["EPA 200.7", "SM 3120B"],
    "Benzene": ["EPA 624", "SM 6200B"],
    "Toluene": ["EPA 624", "SM 6200B"],
    "Ethylbenzene": ["EPA 624", "SM 6200B"],
    "Xylene": ["EPA 624", "SM 6200B"],
    "MTBE": ["EPA 624", "SM 6200B"],
    "Naphthalene": ["EPA 625", "SM 6250B"],
    "Phenanthrene": ["EPA 625", "SM 6250B"],
    "Anthracene": ["EPA 625", "SM 6250B"],
    "Pyrene": ["EPA 625", "SM 6250B"],
    "Benzo(a)anthracene": ["EPA 625", "SM 6250B"],
    "Chrysene": ["EPA 625", "SM 6250B"],
    "Benzo(b)fluoranthene": ["EPA 625", "SM 6250B"],
    "Benzo(k)fluoranthene": ["EPA 625", "SM 6250B"],
    "Benzo(a)pyrene": ["EPA 625", "SM 6250B"],
    "Indeno(1,2,3-cd)pyrene": ["EPA 625", "SM 6250B"],
    "Dibenz(a,h)anthracene": ["EPA 625", "SM 6250B"],
    "Benzo(g,h,i)perylene": ["EPA 625", "SM 6250B"],
    "PCB": ["EPA 608", "SM 608"],
    "Pesticides": ["EPA 608", "SM 608"],
    "Herbicides": ["EPA 632", "SM 632"],
    "VOCs": ["EPA 624", "SM 6200B"],
    "SVOCs": ["EPA 625", "SM 6250B"],
    "Metals": ["EPA 200.8", "SM 3113B"],
    "Cyanide": ["EPA 335.4", "SM 4500-CN- E"],
    "Sulfide": ["EPA 376.1", "SM 4500-S2- D"],
    "Asbestos": ["EPA 100.2", "SM 2550"],
    "Color": ["SM 2120B"],
    "Odor": ["SM 2150B"],
    "Taste": ["SM 2160"],
    "Surfactants": ["EPA 420.1", "SM 5540C"],
    "Phenols": ["EPA 420.2", "SM 5530C"],
    "Radioactivity": ["EPA 900.0", "SM 7110C"],
    "TOC": ["SM 5310B"],
    "DOC": ["SM 5310B"],
    "Purgeable Halocarbons": ["EPA 601", "SM 6200B"],
    "Extractable Organohalides": ["EPA 625", "SM 6250B"],
    "Aldehydes": ["EPA 556", "SM 6200B"],
    "Ketones": ["EPA 624", "SM 6200B"],
    "Alcohols": ["EPA 603", "SM 6200B"],
    "Organic Acids": ["EPA 625", "SM 6250B"],
    "PCBs": ["EPA 608", "SM 608"],
    "Pesticides": ["EPA 608", "SM 608"],
    "Herbicides": ["EPA 632", "SM 632"],
    "Dioxins and Furans": ["EPA 1613", "SM 1613"],
    "PAHs": ["EPA 625", "SM 6250B"],
    "BTEX": ["EPA 624", "SM 6200B"],
    "TPH": ["EPA 8015", "SM 8015"],
    "Oil and Grease": ["EPA 1664", "SM 5520B"],
    "Fecal Coliform":  ["SM 9222D", "SM 9222G"],
    "Total Coliform": ["SM 9221B", "SM 9221F"],
    "E. coli": ["SM 9223B"],
    "Enterococcus": ["EPA 1600", "SM 9230B"],
    "Radioactivity": ["EPA 900.0", "SM 7110C"],
    "Radon": ["EPA 913", "SM 7500-Rn"],
    "Strontium-90": ["EPA 905", "SM 7500-Sr"],
    "Tritium": ["EPA 906", "SM 4500-H3"],
    "Gross Alpha/Beta": ["EPA 900", "SM 7110B"],
    "Radium-226": ["EPA 903", "SM 7500-Ra"],
    "Radium-228": ["EPA 904", "SM 7500-Ra"],
    "Uranium": ["EPA 200.8", "SM 3125"],
    "Plutonium": ["EPA 909", "SM 7500-Pu"],
    "Americium": ["EPA 910", "SM 7500-Am"],
}


def get_date_input(label, default_value=None):
    """
    Displays a date input field in Streamlit.

    Args:
        label (str): The label for the date input field.
        default_value (str, optional): The default date value in "MM/DD/YYYY" format.
            If None, defaults to today's date.

    Returns:
        datetime.date: The selected date as a datetime.date object.  Returns None
                       if the user doesn't select a date.
    """
    if default_value:
        try:
            default_date = datetime.datetime.strptime(default_value, "%m/%d/%Y").date()
        except ValueError:
            st.error(f"Invalid default date format. Please use MM/DD/YYYY.  Using today's date.")
            default_date = datetime.date.today()
    else:
        default_date = datetime.date.today()

    selected_date = st.date_input(label, default_date)
    return selected_date.strftime("%m/%d/%Y") #return as string in consistent format


def render_navbar():
    """Renders the navigation bar at the top of the app."""
    cols = st.columns(len(PAGES))
    for i, page_name in enumerate(PAGES):
        if cols[i].button(page_name):
            st.session_state.current_page = i
            st.rerun()  # Use st.rerun() for consistency

def render_nav_buttons():
    """Renders the navigation buttons at the bottom of each page."""
    cols = st.columns(3)  # Create three columns for layout
    if st.session_state.current_page > 0:
        if cols[0].button("Previous"):
            st.session_state.current_page -= 1
            st.rerun()
    cols[1].empty()  # Leave the middle column empty for spacing
    if st.session_state.current_page < len(PAGES) - 1:
        if cols[2].button("Next"):
            st.session_state.current_page += 1
            st.rerun()

def render_cover_page():
    """Renders the cover page form."""
    st.header("Cover Page Information")
    if "cover_data" not in st.session_state:
        st.session_state["cover_data"] = {
            "report_id": generate_id(),
            "report_date": datetime.date.today().strftime("%m/%d/%Y"),
            "client_name": "",
            "address_line": "",
            "phone": "",
            "project_name": "",
            "work_order": "",
            "analysis_type": "",
            "coc_number": "",
            "po_number": "",
            "date_samples_received": "",
            "comments": "",
            "signatory_name": "",
            "signatory_title": "",
        }

    cover_data = st.session_state["cover_data"]

    with st.form("cover_form"):
        cover_data["client_name"] = st.text_input("Client Name", cover_data["client_name"])
        cover_data["address_line"] = st.text_input("Address", cover_data["address_line"])
        cover_data["phone"] = st.text_input("Phone", cover_data["phone"])
        cover_data["project_name"] = st.text_input("Project Name", cover_data["project_name"])
        cover_data["work_order"] = st.text_input("Work Order #", cover_data["work_order"])
        cover_data["analysis_type"] = st.text_input("Analysis Type", cover_data["analysis_type"])
        cover_data["coc_number"] = st.text_input("COC #", cover_data["coc_number"])
        cover_data["po_number"] = st.text_input("PO #", cover_data["po_number"])
        cover_data["date_samples_received"] = get_date_input("Date Samples Received", cover_data["date_samples_received"])
        cover_data["comments"] = st.text_area("Comments / Case Narrative", cover_data["comments"], height=100)
        cover_data["signatory_name"] = st.text_input("Signatory Name", cover_data["signatory_name"])
        cover_data["signatory_title"] = st.text_input("Signatory Title", cover_data["signatory_title"])
        # Report ID and Date are set automatically and not editable
        st.text_input("Report ID", value=cover_data["report_id"], disabled=True)
        st.text_input("Report Date", value=cover_data["report_date"], disabled=True)

        submitted = st.form_submit_button("Save Cover Page Data")
        if submitted:
            st.success("Cover Page data saved!")

    render_nav_buttons()



def render_sample_summary_page():
    """Renders the sample summary page."""
    st.header("Sample Summary")
    if "page1_data" not in st.session_state:
        st.session_state["page1_data"] = {
            "report_id": generate_id(),
            "report_date": datetime.date.today().strftime("%m/%d/%Y"),
            "samples": [],
        }
    page1_data = st.session_state["page1_data"]

    with st.form("sample_form", clear_on_submit=True):
        lab_id = st.text_input("Lab ID", generate_id("LIMS"))
        sample_id = st.text_input("Sample ID")
        matrix = st.selectbox("Matrix", ["Water", "Soil", "Air", "Other"])
        date_collected = get_date_input("Date Collected")
        date_received = get_date_input("Date Received")

        if st.form_submit_button("Add Sample"):
            page1_data["samples"].append({
                "lab_id": lab_id,
                "sample_id": sample_id,
                "matrix": matrix,
                "date_collected": date_collected,
                "date_received": date_received,
            })

    st.write("**Current Samples:**")
    if page1_data["samples"]:
        for i, sample in enumerate(page1_data["samples"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** Lab ID: {sample['lab_id']}, Sample ID: {sample['sample_id']}, "
                         f"Matrix: {sample['matrix']}, Date Collected: {sample['date_collected']}, "
                         f"Date Received: {sample['date_received']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_sample_{i}"):
                    del page1_data["samples"][i]
                    st.rerun()
    else:
        st.info("No samples added yet.")

    # Display Report ID and Report Date (from shared state)
    st.text_input("Report ID", value=page1_data["report_id"], disabled=True)
    st.text_input("Report Date", value=page1_data["report_date"], disabled=True)
    render_nav_buttons()



def render_analytical_results_page():
    """Renders the analytical results page."""
    st.header("Analytical Results")
    if "page2_data" not in st.session_state:
        st.session_state["page2_data"] = {
            "report_id": generate_id(),
            "report_date": datetime.date.today().strftime("%m/%d/%Y"),
            "workorder_name": st.session_state["cover_data"].get("work_order",""), #default
            "results": [],
        }
    p2 = st.session_state["page2_data"]
    p2["workorder_name"] = st.text_input("Work Order #",p2["workorder_name"])

    # pick analyte, method
    analyte = st.selectbox("Analyte", list(analyte_to_methods.keys()))
    method = st.selectbox("Method", analyte_to_methods[analyte])
    
    with st.form("analysis_form", clear_on_submit=True):
        # Conditionally display Lab ID dropdown
        sample_lab_ids = [s_["lab_id"] for s_ in st.session_state["page1_data"].get("samples",[])]
        if sample_lab_ids:
            chosen_lab_id = st.selectbox("Lab ID", sample_lab_ids)
            s_id = next((s_["sample_id"] for s_ in st.session_state["page1_data"]["samples"] if s_["lab_id"] == chosen_lab_id), "")
            st.write(f"Corresponding Sample ID: {s_id}")
        else:
            chosen_lab_id = st.text_input("Lab ID","")
            s_id = ""
    
        
        analysis_date = get_date_input("Analysis Date", datetime.date.today().strftime("%m/%d/%Y"))
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            df = st.text_input("DF","")
        with c2:
            mdl = st.text_input("MDL","")
        with c3:
            pql = st.text_input("PQL","")
        with c4:
            res = st.text_input("Result","ND")
        un = st.selectbox("Unit", ["mg/L","µg/L","µS/cm","none"])
    
        if st.form_submit_button("Add Analytical Result"):
            if chosen_lab_id:
                p2["results"].append({
                    "lab_id": chosen_lab_id,
                    "sample_id": s_id,
                    "analysis_date": analysis_date,  # Store the analysis date per sample
                    "parameter": analyte,
                    "analysis": method,
                    "df": df,
                    "mdl": mdl,
                    "pql": pql,
                    "result": res,
                    "unit": un
                })

  
    st.write("**Current Analytical Results:**")
    if p2["results"]:
        for i, r_ in enumerate(p2["results"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** Lab ID: {r_['lab_id']} (Sample ID: {r_.get('sample_id','')}), "
                         f"Parameter: {r_['parameter']}, Analysis: {r_['analysis']}, DF: {r_['df']}, "
                         f"MDL: {r_['mdl']}, PQL: {r_['pql']}, Result: {r_['result']} {r_['unit']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_result_{i}"):
                    del p2["results"][i]
                    st.rerun()
    else:
        st.info("No results yet.")


    render_nav_buttons()

def render_quality_control_page():
    st.header("Quality Control Data")
    p3 = st.session_state["page3_data"]
    p3.setdefault("qc_entries", [])

    # pick analyte, method
    analyte = st.selectbox("QC Parameter (Analyte)", list(analyte_to_methods.keys()))
    method = st.selectbox("QC Method", analyte_to_methods[analyte])

    with st.form("qc_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            q_unit = st.text_input("Unit","mg/L")
        with c2:
            q_mdl = st.text_input("MDL","0.0010")
        with c3:
            q_pql = st.text_input("PQL","0.005")
        with c4:
            q_qual = st.text_input("Lab Qualifier","")
        blank_conc = st.text_input("Method Blank Conc.","")

        if st.form_submit_button("Add QC Entry"):
            q_batch = generate_qc_batch()
            mb = generate_method_blank()
            p3["qc_entries"].append({
                "qc_batch": q_batch,
                "qc_method": method,
                "parameter": analyte,
                "unit": q_unit,
                "mdl": q_mdl,
                "pql": q_pql,
                "blank_result": blank_conc,
                "lab_qualifier": q_qual,
                "method_blank": mb
            })

    st.write("**Current QC Data:**")
    if p3["qc_entries"]:
        for i, qc_ in enumerate(p3["qc_entries"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** QC Batch: {qc_['qc_batch']}, Method: {qc_['qc_method']}, "
                         f"Parameter: {qc_['parameter']}, Unit: {qc_['unit']}, MDL:                          f"PQL: {qc_['pql']}, Blank Result: {qc_['blank_result']}, Lab Qualifier: {qc_['lab_qualifier']}, Method Blank: {qc_['method_blank']}")
            with col2:
                if st.button(f"❌ Remove", key=f"del_qc_{i}"):
                    del p3["qc_entries"][i]
                    st.rerun()
    else:
        st.info("No QC data added yet.")
    render_nav_buttons()



#####################################
# PDF Report Generation
#####################################

def create_pdf_report(lab_name, lab_address, lab_email, lab_phone,
                      cover_data, page1_data, page2_data, page3_data):
    """Generates the full PDF report.

    Args:
        lab_name (str): Name of the laboratory.
        lab_address (str): Address of the laboratory.
        lab_email (str): Email of the laboratory.
        lab_phone (str): Phone number of the laboratory.
        cover_data (dict): Data from the cover page.
        page1_data (dict): Data from the sample summary page.
        page2_data (dict): Data from the analytical results page.
        page3_data (dict): Data from the quality control page.

    Returns:
        bytes: The PDF report as a byte stream.
    """
    pdf = PDF()  # Use the custom PDF class
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "DejaVuSans-Oblique.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    # Cover Page
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Water Quality Analysis Report", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 6, f"Report ID: {cover_data['report_id']}", 0, 1, "L")
    pdf.cell(0, 6, f"Report Date: {cover_data['report_date']}", 0, 1, "L")
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 8, "Client Information", 0, 1, "L")
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 6, f"Client Name: {cover_data['client_name']}", 0, 1, "L")
    pdf.cell(0, 6, f"Address: {cover_data['address_line']}", 0, 1, "L")
    pdf.cell(0, 6, f"Phone: {cover_data['phone']}", 0, 1, "L")
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 8, "Project Information", 0, 1, "L")
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 6, f"Project Name: {cover_data['project_name']}", 0, 1, "L")
    pdf.cell(0, 6, f"Work Order #: {cover_data['work_order']}", 0, 1, "L")
    pdf.cell(0, 6, f"Analysis Type: {cover_data['analysis_type']}", 0, 1, "L")
    pdf.cell(0, 6, f"COC #: {cover_data['coc_number']}", 0, 1, "L")
    pdf.cell(0, 6, f"PO #: {cover_data['po_number']}", 0, 1, "L")
    pdf.cell(0, 6, f"Date Samples Received: {cover_data['date_samples_received']}", 0, 1, "L")
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 8, "Comments / Case Narrative", 0, 1, "L")
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 6, cover_data['comments'], 0, 'L')
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 8, "Laboratory Information", 0, 1, "L")
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 6, f"Laboratory Name: {lab_name}", 0, 1, "L")
    pdf.cell(0, 6, f"Address: {lab_address}", 0, 1, "L")
    pdf.cell(0, 6, f"Email: {lab_email}", 0, 1, "L")
    pdf.cell(0, 6, f"Phone: {lab_phone}", 0, 1, "L")
    pdf.ln(10)
    pdf.cell(0, 6, f"Signatory Name: {cover_data['signatory_name']}", 0, 1, "L")
    pdf.cell(0, 6, f"Signatory Title: {cover_data['signatory_title']}", 0, 1, "L")

    # Sample Summary Page
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Sample Summary", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(30, 8, "Lab ID", 1, 0, "C")
    pdf.cell(30, 8, "Sample ID", 1, 0, "C")
    pdf.cell(25, 8, "Matrix", 1, 0, "C")
    pdf.cell(40, 8, "Date Collected", 1, 0, "C")
    pdf.cell(40, 8, "Date Received", 1, 1, "C")
    pdf.set_font("DejaVu", size=12)
    for sample in page1_data["samples"]:
        pdf.cell(30, 6, sample["lab_id"], 1, 0, "C")
        pdf.cell(30, 6, sample["sample_id"], 1, 0, "C")
        pdf.cell(25, 6, sample["matrix"], 1, 0, "C")
        pdf.cell(40, 6, sample["date_collected"], 1, 0, "C")
        pdf.cell(40, 6, sample["date_received"], 1, 1, "C")

    # Analytical Results Page
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Analytical Results", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(30, 8, "Lab ID", 1, 0, "C")
    pdf.cell(30, 8, "Sample ID", 1, 0, "C")
    pdf.cell(30, 8, "Analysis Date", 1, 0, "C")  # Add Analysis Date
    pdf.cell(40, 8, "Parameter", 1, 0, "C")
    pdf.cell(30, 8, "Analysis", 1, 0, "C")
    pdf.cell(20, 8, "DF", 1, 0, "C")
    pdf.cell(20, 8, "MDL", 1, 0, "C")
    pdf.cell(20, 8, "PQL", 1, 0, "C")
    pdf.cell(20, 8, "Result", 1, 0, "C")
    pdf.cell(20,8,"Unit",1,1,"C")
    pdf.set_font("DejaVu", size=12)
    for result in page2_data["results"]:
        pdf.cell(30, 6, result["lab_id"], 1, 0, "C")
        pdf.cell(30, 6, result.get("sample_id",""), 1, 0, "C")
        pdf.cell(30, 6, result["analysis_date"], 1, 0, "C")  # Display Analysis Date
        pdf.cell(40, 6, result["parameter"], 1, 0, "C")
        pdf.cell(30, 6, result["analysis"], 1, 0, "C")
        pdf.cell(20, 6, result["df"], 1, 0, "C")
        pdf.cell(20, 6, result["mdl"], 1, 0, "C")
        pdf.cell(20, 6, result["pql"], 1, 0, "C")
        pdf.cell(20, 6, result["result"], 1, 0, "C")
        pdf.cell(20,6,result["unit"],1,1,"C")

    # Quality Control Data Page
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Quality Control Data", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(30, 8, "QC Batch", 1, 0, "C")
    pdf.cell(30, 8, "QC Method", 1, 0, "C")
    pdf.cell(40, 8, "Parameter", 1, 0, "C")
    pdf.cell(20, 8, "Unit", 1, 0, "C")
    pdf.cell(20, 8, "MDL", 1, 0, "C")
    pdf.cell(20, 8, "PQL", 1, 0, "C")
    pdf.cell(30, 8, "Blank Result", 1, 0, "C")
    pdf.cell(30, 8, "Lab Qualifier", 1, 0, "C")
    pdf.cell(30,8,"Method Blank",1,1,"C")
    pdf.set_font("DejaVu", size=12)
    for qc_entry in page3_data["qc_entries"]:
        pdf.cell(30, 6, qc_entry["qc_batch"], 1, 0, "C")
        pdf.cell(30, 6, qc_entry["qc_method"], 1, 0, "C")
        pdf.cell(40, 6, qc_entry["parameter"], 1, 0, "C")
        pdf.cell(20, 6, qc_entry["unit"], 1, 0, "C")
        pdf.cell(20, 6, qc_entry["mdl"], 1, 0, "C")
        pdf.cell(20, 6, qc_entry["pql"], 1, 0, "C")
        pdf.cell(30, 6, qc_entry["blank_result"], 1, 0, "C")
        pdf.cell(30, 6, qc_entry["lab_qualifier"], 1, 0, "C")
        pdf.cell(30,6,qc_entry["method_blank"],1,1,"C")

    # Add a page break before the disclaimer if there are more than 3 pages
    if pdf.page_no() > 3:
        pdf.add_page()

    # Disclaimer Page
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Disclaimer", 0, 1, "C")
    pdf.set_font("DejaVu", size=10)
    disclaimer_text = """
    The analysis performed at KELP Laboratory were done using accepted laboratory 
    practices and meet the quality assurance requirements of the NELAC program 
    unless otherwise noted.  This report is for the exclusive use of the client 
    and is not intended for use by any other party.  Results relate only to the 
    samples as received.  KELP Laboratory assumes no responsibility for the 
    representativeness of the sample, or for the manner in which the sample 
    was collected, handled, and/or stored. This report shall not be reproduced 
    except in full, without written approval of KELP Laboratory.
    """
    pdf.multi_cell(0, 5, disclaimer_text, 0, 'J')

    # Laboratory Information Footer on all pages.
    pdf.set_y(-20)
    pdf.set_font("DejaVu", size=10)  # Smaller font size for footer
    pdf.cell(0, 5, f"{lab_name} - {lab_address} - {lab_email} - {lab_phone}", 0, 0, "C")

    # Create the PDF object
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()



# MAIN APP

def main():
    st.title("Water Quality COA")


    # Render the top nav
    render_navbar()
    if st.button("🔄 Refresh / Start Over"):
        reset_app()
    page_container = st.container()

    # Initialize session state variables
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "page3_data" not in st.session_state:
        st.session_state["page3_data"] = {} # Initialize page 3 data

    # Decide page

    page_idx = st.session_state.current_page
    if page_idx == 0:
        render_cover_page()
    elif page_idx == 1:
        render_sample_summary_page()
    elif page_idx == 2:
        render_analytical_results_page()
    elif page_idx == 3:
        render_quality_control_page()


    # If last page, show generate
    if st.session_state.current_page == len(PAGES) - 1:
        st.markdown("### All pages completed.")
        if st.button("Generate PDF"):
            pdf_bytes = create_pdf_report(
                lab_name="KELP Laboratory",
                lab_address="520 Mercury Dr, Sunnyvale, CA 94085",
                lab_email="kelp@ketoslab.com",
                lab_phone="(408) 461-8860",
                cover_data=st.session_state["cover_data"],
                page1_data=st.session_state["page1_data"],
                page2_data=st.session_state["page2_data"],
                page3_data=st.session_state["page3_data"],
            )
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"Water_Quality_Report_{datetime.date.today()}.pdf",
                mime="application/pdf",
            )



if __name__ == "__main__":
    main()
