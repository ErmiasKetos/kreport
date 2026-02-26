"""
KELP COA Generator — Streamlit Cloud Application
==================================================
KETOS Environmental Lab Platform (KELP)
Certificate of Analysis (COA) PDF Generator

Replicates the exact 12-page COA format per TNI/ISO 17025/ELAP standards:
  Page 1:  Cover Letter (signature, ELAP cert)
  Page 2:  Case Narrative
  Page 3:  Sample Result Summary
  Pages 4-6: Sample Results (detail per sample/prep method)
  Page 7:  MB Summary Report
  Page 8:  LCS/LCSD Summary Report
  Page 9:  Laboratory Qualifiers and Definitions
  Page 10: Sample Receipt Checklist
  Page 11: Login Summary Report
  Page 12: Chain of Custody (uploaded image)

Branding: KETOS Inc. — #1F4E79 dark blue, #4AAEC7 teal accent, Calibri font
"""

import streamlit as st
import io
import json
import copy
from datetime import datetime, date, time
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import os
import base64

# ============================================================================
# BRANDING & CONSTANTS
# ============================================================================
KETOS_DARK_BLUE = HexColor("#1F4E79")
KETOS_TEAL = HexColor("#4AAEC7")
KETOS_LIGHT_BLUE = HexColor("#D6E4F0")
KETOS_LIGHT_GRAY = HexColor("#D6DCE4")
KETOS_MED_GRAY = HexColor("#F2F2F2")
KETOS_WHITE = HexColor("#FFFFFF")
KETOS_BLACK = HexColor("#000000")
BORDER_BLUE = HexColor("#5B9BD5")

PAGE_W, PAGE_H = letter  # 612 x 792 pts
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

LAB_NAME = "KETOS Environmental Lab Services"
LAB_ENTITY = "KETOS INC."
LAB_ADDRESS_LINES = [
    "KETOS INC.",
    "1063 S De Anza Blvd",
    "San Jose, California 95129",
]
LAB_PHONE = "Tel: 408-603-5552"
LAB_EMAIL = "Email: kelp@ketos.com"

# Default qualifiers list per the sample COA
QUALIFIER_DEFINITIONS = [
    ("B", "Indicates when the analyte is found in the associated method or preparation blank"),
    ("D", "Surrogate is not recoverable due to the necessary dilution of the sample"),
    ("E", "Indicates the reportable value is outside of the calibration range of the instrument but within the linear range of the instrument (unless otherwise noted). Values reported with an E qualifier should be considered as estimated."),
    ("H", "Indicates that the recommended holding time for the analyte or compound has been exceeded"),
    ("J", "Indicates a value between the method MDL and PQL and that the reported concentration should be considered as estimated rather than the quantitative"),
    ("NA", "Not Analyzed"),
    ("N/A", "Not Applicable"),
    ("ND", "Not Detected at a concentration greater than the PQL/RL or, if reported to the MDL, at greater than the MDL."),
    ("NR", "Not recoverable — a matrix spike concentration is not recoverable due to a concentration within the original sample that is greater than four times the spike concentration added"),
    ("R", "The % RPD between a duplicate set of samples is outside of the absolute values established by laboratory control charts"),
    ("S", "Spike recovery is outside of established method and/or laboratory control limits. Further explanation of the use of this qualifier should be included within a case narrative"),
    ("X", "Used to indicate that a value based on pattern identification is within the pattern range but not typical of the pattern found in standards. Further explanation may or may not be provided within the sample footnote and/or the case narrative."),
]

DEFINITIONS = [
    ("Accuracy/Bias (% Recovery)", "The closeness of agreement between an observed value and an accepted reference value."),
    ("Blank (Method/Preparation Blank)", "MB/PB — An analyte-free matrix to which all reagents are added in the same volumes/proportions as used in sample processing. The method blank is used to document contamination resulting from the analytical process."),
    ("Duplicate", "A field sample and/or laboratory QC sample prepared in duplicate following all of the same processes and procedures used on the original sample (sample duplicate, LCSD, MSD)"),
    ("Laboratory Control Sample (LCS ad LCSD)", "A known matrix spiked with compounds representative of the target analyte(s). This is used to document laboratory performance."),
    ("Matrix", "The component or substrate that contains the analyte of interest (e.g., — groundwater, sediment, soil, waste water, etc)"),
    ("Matrix Spike (MS/MSD)", "Client sample spiked with identical concentrations of target analyte(s). The spiking occurs prior to the sample preparation and analysis. They are used to document the precision and bias of a method in a given sample matrix."),
    ("Method Detection Limit (MDL)", "The minimum concentration of a substance that can be measured and reported with a 99% confidence that the analyte concentration is greater than zero"),
    ("Practical Quantitation Limit/Reporting Limit/Limit of Quantitation (PQL/RL/LOQ)", "A laboratory determined value at 2 to 5 times above the MDL that can be reproduced in a manner that results in a 99% confidence level that the result is both accurate and precise. PQLs/RLs/LOQs reflect all preparation factors and/or dilution factors that have been applied to the sample during the preparation and/or analytical processes."),
    ("Precision (%RPD)", "The agreement among a set of replicate/duplicate measurements without regard to known value of the replicates"),
    ("Units", "The unit of measure used to express the reported result — mg/L and mg/Kg (equivalent to PPM — parts per million in liquid and solid), ug/L and ug/Kg (equivalent to PPB — parts per billion in liquid and solid), ug/m3, mg/m3, ppbv and ppmv (all units of measure for reporting concentrations in air), % (equivalent to 10000 ppm or 1,000,000 ppb), ug/Wipe (concentration found on the surface of a single Wipe usually taken over a 100cm2 surface)"),
]


# ============================================================================
# SESSION STATE DEFAULTS
# ============================================================================
def init_session():
    """Initialize all session state variables with sensible defaults."""
    defaults = {
        # Lab / Report Info
        "elap_number": "XXXX",
        "lab_phone_display": "(408) 603-5552",
        "report_date": date.today(),
        "work_order": "",
        "total_page_count": 12,

        # Client Info
        "client_contact": "",
        "client_company": "",
        "client_address": "",
        "client_city_state_zip": "",
        "client_phone": "",
        "client_email": "",
        "project_name": "",
        "project_number": "",
        "client_id": "",

        # Cover Letter
        "num_samples_text": "1",
        "date_received_text": "",
        "approver_name": "Ermias L",
        "approver_title": "Lab Director",
        "approval_date": date.today(),

        # Case Narrative
        "case_narrative_custom": "",
        "qc_met": True,
        "method_blank_corrected": False,

        # Samples  (list of dicts)
        "samples": [],

        # QC — Method Blank batches
        "mb_batches": [],

        # QC — LCS/LCSD batches
        "lcs_batches": [],

        # Sample Receipt Checklist
        "receipt": {
            "date_time_received": "",
            "received_by": "",
            "physically_logged_by": "",
            "checklist_completed_by": "",
            "carrier_name": "Client Drop Off",
            "coc_present": "Yes",
            "coc_signed": "Yes",
            "coc_agrees": "Yes",
            "custody_seals_bottles": "Not Present",
            "custody_seals_cooler": "Not Present",
            "cooler_good": "Yes",
            "proper_container": "Yes",
            "containers_intact": "Yes",
            "sufficient_volume": "Yes",
            "within_holding_time": "Yes",
            "temp_compliance": "No",
            "temperature": "",
            "voa_headspace": "No VOA vials submitted",
            "ph_acceptable": "No",
            "ph_checked_by": "",
            "ph_adjusted_by": "",
            "receipt_comments": "",
        },

        # Login Summary
        "login_summary": {
            "client_id_code": "",
            "qc_level": "II",
            "tat_requested": "Standard",
            "date_received_login": "",
            "time_received_login": "",
            "report_due_date": "",
            "login_comments": "",
        },

        # Uploaded images
        "logo_bytes": None,
        "signature_bytes": None,
        "coc_image_bytes": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================================
# PDF BUILDER  (ReportLab)
# ============================================================================
class KelpCOA:
    """Builds the multi-page COA PDF using ReportLab low-level canvas."""

    def __init__(self, data: dict, logo_bytes=None, sig_bytes=None, coc_bytes=None):
        self.d = data
        self.logo_bytes = logo_bytes
        self.sig_bytes = sig_bytes
        self.coc_bytes = coc_bytes
        self.buf = io.BytesIO()
        self.page_num = 0
        self.total_pages = data.get("total_page_count", 12)

    def build(self) -> bytes:
        c = canvas.Canvas(self.buf, pagesize=letter)
        c.setTitle(f"KELP COA — WO {self.d.get('work_order','')}")

        self._page_cover_letter(c)
        self._page_case_narrative(c)
        self._page_sample_result_summary(c)
        self._pages_sample_results(c)
        self._page_mb_summary(c)
        self._page_lcs_lcsd_summary(c)
        self._page_qualifiers(c)
        self._page_receipt_checklist(c)
        self._page_login_summary(c)
        self._page_coc(c)

        c.save()
        return self.buf.getvalue()

    # ---- helpers ----
    def _new_page(self, c):
        if self.page_num > 0:
            c.showPage()
        self.page_num += 1

    def _draw_logo(self, c, x, y, max_w=1.5*inch, max_h=0.9*inch):
        if self.logo_bytes:
            img = PILImage.open(io.BytesIO(self.logo_bytes))
            iw, ih = img.size
            scale = min(max_w / iw, max_h / ih)
            draw_w, draw_h = iw * scale, ih * scale
            tmp = io.BytesIO(self.logo_bytes)
            c.drawImage(
                tmp, x, y - draw_h, width=draw_w, height=draw_h,
                preserveAspectRatio=True, mask='auto'
            )
            return draw_h
        else:
            # Fallback: draw text logo
            c.setFont("Helvetica-Bold", 18)
            c.setFillColor(KETOS_DARK_BLUE)
            c.drawString(x, y - 20, "KETOS")
            c.setFont("Helvetica", 7)
            c.setFillColor(KETOS_TEAL)
            c.drawString(x, y - 30, "ENVIRONMENTAL LAB SERVICES")
            c.setFillColor(black)
            return 35

    def _draw_footer(self, c):
        y = 0.5 * inch
        c.setFont("Helvetica", 8)
        c.setFillColor(black)
        c.drawString(MARGIN, y, f"Total Page Count:  {self.total_pages}")
        c.drawRightString(PAGE_W - MARGIN, y, f"Page {self.page_num} of {self.total_pages}")

    def _draw_header_with_logo(self, c, title=None):
        """Draw the KETOS logo in the top-left + optional centered title. Returns y below header."""
        logo_h = self._draw_logo(c, MARGIN, PAGE_H - 0.6*inch)
        y = PAGE_H - 0.6*inch - logo_h - 0.15*inch
        if title:
            c.setFont("Helvetica-Bold", 13)
            c.setFillColor(black)
            c.drawCentredString(PAGE_W / 2, y, title)
            y -= 24
        return y

    def _draw_line(self, c, y, x1=None, x2=None):
        if x1 is None: x1 = MARGIN
        if x2 is None: x2 = PAGE_W - MARGIN
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.line(x1, y, x2, y)

    def _field_row(self, c, y, label, value, x=MARGIN, label_w=120, font_size=9):
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(x, y, label)
        c.setFont("Helvetica", font_size)
        c.drawString(x + label_w, y, str(value))
        return y - 14

    def _draw_table(self, c, y, headers, rows, col_widths, x_start=None,
                    header_bg=KETOS_LIGHT_GRAY, font_size=8, row_height=14,
                    header_font_size=8, bold_cols=None, align=None):
        """
        Draw a simple table at (x_start, y). Returns y below the table.
        `bold_cols` — set of column indices to bold.
        `align` — list of 'L','C','R' per column.
        """
        if x_start is None:
            x_start = MARGIN
        if bold_cols is None:
            bold_cols = set()
        if align is None:
            align = ['L'] * len(headers)

        num_cols = len(headers)
        total_w = sum(col_widths)

        # Header
        c.setFillColor(header_bg)
        c.rect(x_start, y - row_height, total_w, row_height, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", header_font_size)
        cx = x_start
        for i, h in enumerate(headers):
            pad = 3
            if align[i] == 'C':
                c.drawCentredString(cx + col_widths[i]/2, y - row_height + 4, h)
            elif align[i] == 'R':
                c.drawRightString(cx + col_widths[i] - pad, y - row_height + 4, h)
            else:
                c.drawString(cx + pad, y - row_height + 4, h)
            cx += col_widths[i]
        y -= row_height

        # Draw header bottom line
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.line(x_start, y, x_start + total_w, y)

        # Rows
        for row in rows:
            y -= row_height
            if y < 0.8*inch:
                self._draw_footer(c)
                self._new_page(c)
                y = self._draw_header_with_logo(c)
                y -= 10
            cx = x_start
            for i, val in enumerate(row):
                pad = 3
                if i in bold_cols:
                    c.setFont("Helvetica-Bold", font_size)
                else:
                    c.setFont("Helvetica", font_size)
                text = str(val) if val is not None else ""
                if align[i] == 'C':
                    c.drawCentredString(cx + col_widths[i]/2, y + 3, text)
                elif align[i] == 'R':
                    c.drawRightString(cx + col_widths[i] - pad, y + 3, text)
                else:
                    c.drawString(cx + pad, y + 3, text)
                cx += col_widths[i]
            # Row bottom line
            c.setStrokeColor(KETOS_LIGHT_GRAY)
            c.setLineWidth(0.3)
            c.line(x_start, y, x_start + total_w, y)

        return y

    # ================================================================
    # PAGE 1: COVER LETTER
    # ================================================================
    def _page_cover_letter(self, c):
        self._new_page(c)
        # Logo
        logo_h = self._draw_logo(c, MARGIN, PAGE_H - 0.5*inch, max_w=1.8*inch, max_h=1.1*inch)

        y = PAGE_H - 0.5*inch - logo_h - 0.25*inch

        # Lab address block
        c.setFont("Helvetica", 9)
        for line in [self.d.get("client_contact", ""), LAB_ENTITY] + LAB_ADDRESS_LINES[1:] + [LAB_PHONE, LAB_EMAIL]:
            if line:
                c.drawString(MARGIN, y, line)
                y -= 13

        # RE: line
        y -= 6
        c.drawString(MARGIN, y, f"RE: {self.d.get('project_name','')}")
        y -= 20

        # Work Order
        c.drawCentredString(PAGE_W / 2, y, f"Work Order No.:  {self.d.get('work_order','')}")
        y -= 40

        # Dear ...
        c.setFont("Helvetica", 10)
        contact = self.d.get("client_contact", "Valued Client")
        c.drawString(MARGIN + 20, y, f"Dear {contact}:")
        y -= 24

        # Body paragraphs
        num_samp = self.d.get("num_samples_text", "1")
        recv_date = self.d.get("date_received_text", "")
        body1 = f"KELP received {num_samp} sample(s) on {recv_date} for the analyses presented in the following Report."
        body2 = "All data for associated QC met EPA or laboratory specification(s) except where noted in the case narrative."
        elap = self.d.get("elap_number", "XXXX")
        phone = self.d.get("lab_phone_display", "(408) 603-5552")
        body3 = f"KELP is certified by the State of California, ELAP #{elap}. If you have any questions regarding these test results, please feel free to contact the Project Management Team at {phone}."

        for txt in [body1, "", body2, "", body3]:
            if txt == "":
                y -= 10
            else:
                # Word-wrap manually at ~85 chars
                words = txt.split()
                line = ""
                for w in words:
                    if len(line + " " + w) > 90:
                        c.drawString(MARGIN + 20, y, line.strip())
                        y -= 14
                        line = w
                    else:
                        line = line + " " + w if line else w
                if line:
                    c.drawString(MARGIN + 20, y, line.strip())
                    y -= 14

        y -= 30
        # Signature
        if self.sig_bytes:
            sig_img = io.BytesIO(self.sig_bytes)
            c.drawImage(sig_img, MARGIN + 20, y - 60, width=1.5*inch, height=0.8*inch,
                        preserveAspectRatio=True, mask='auto')
            y_sig = y - 65
        else:
            y_sig = y - 20

        # Approval date on right
        approval_date = self.d.get("approval_date", "")
        c.setFont("Helvetica", 10)
        c.drawString(PAGE_W/2 + 40, y_sig + 15, str(approval_date))
        self._draw_line(c, y_sig + 10, PAGE_W/2 + 40, PAGE_W/2 + 180)
        c.drawString(PAGE_W/2 + 40, y_sig - 2, "Date")

        # Approver name/title on left
        self._draw_line(c, y_sig + 10, MARGIN + 20, MARGIN + 180)
        c.drawString(MARGIN + 20, y_sig - 2, self.d.get("approver_name", ""))
        c.drawString(MARGIN + 20, y_sig - 14, self.d.get("approver_title", ""))

        self._draw_footer(c)

    # ================================================================
    # PAGE 2: CASE NARRATIVE
    # ================================================================
    def _page_case_narrative(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c)

        # Date right-aligned
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(PAGE_W - MARGIN, y, f"Date:  {self.d.get('report_date','')}")
        y -= 5
        self._draw_line(c, y)
        y -= 16

        # Client / Project / WO
        y = self._field_row(c, y, "Client:", self.d.get("client_company", ""))
        y = self._field_row(c, y, "Project:", self.d.get("project_name", ""))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN, y, "Work Order:")
        y -= 14
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, y, str(self.d.get("work_order", "")))

        # CASE NARRATIVE centered title
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(PAGE_W/2, y, "CASE NARRATIVE")
        y -= 8
        self._draw_line(c, y)
        y -= 18

        # Boilerplate paragraphs
        c.setFont("Helvetica", 9)
        paras = []
        if self.d.get("qc_met", True):
            paras.append("Unless otherwise indicated in the following narrative, no issues encountered with the receiving, preparation, analysis or reporting of the results associated with this work order.")
        if not self.d.get("method_blank_corrected", False):
            paras.append("Unless otherwise indicated in the following narrative, no results have been method and/or field blank corrected.")
        paras.append("Reported results relate only to the items/samples tested by the laboratory.")
        paras.append("This report shall not be reproduced, except in full, without the written approval of KETOS INC.")

        custom = self.d.get("case_narrative_custom", "")
        if custom:
            paras.insert(0, custom)

        for txt in paras:
            y -= 4
            words = txt.split()
            line = ""
            for w in words:
                if len(line + " " + w) > 95:
                    c.drawString(MARGIN + 10, y, line.strip())
                    y -= 13
                    line = w
                else:
                    line = line + " " + w if line else w
            if line:
                c.drawString(MARGIN + 10, y, line.strip())
                y -= 13
            y -= 6

        self._draw_footer(c)

    # ================================================================
    # PAGE 3: SAMPLE RESULT SUMMARY
    # ================================================================
    def _page_sample_result_summary(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c, "Sample Result Summary")
        y -= 10

        # Report prepared for / dates
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN, y, "Report prepared for:")
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 120, y, self.d.get("client_contact", ""))
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(PAGE_W - MARGIN, y, f"Date Received: {self.d.get('date_received_text','')}")
        y -= 13
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 120, y, self.d.get("client_company", ""))
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(PAGE_W - MARGIN, y, f"Date Reported: {self.d.get('report_date','')}")
        y -= 18

        samples = self.d.get("samples", [])
        for samp in samples:
            # Sample header line
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN, y, samp.get("client_sample_id", ""))
            wo = self.d.get("work_order", "")
            lab_id = samp.get("lab_sample_id", "")
            c.drawRightString(PAGE_W - MARGIN, y, lab_id)
            y -= 4
            self._draw_line(c, y)
            y -= 4

            # Table
            headers = ["Parameters:", "Analysis Method", "DF", "MDL", "PQL", "Results", "Unit"]
            col_w = [170, 80, 35, 55, 55, 55, 40]
            align = ['L', 'C', 'C', 'C', 'C', 'R', 'C']
            results = samp.get("results", [])
            rows = []
            for r in results:
                rows.append([
                    r.get("parameter", ""),
                    r.get("method", ""),
                    r.get("df", "1"),
                    r.get("mdl", ""),
                    r.get("pql", ""),
                    r.get("result", ""),
                    r.get("unit", "mg/L"),
                ])
            y = self._draw_table(c, y, headers, rows, col_w, align=align)
            y -= 16

        self._draw_footer(c)

    # ================================================================
    # PAGES 4+: SAMPLE RESULTS (detailed, per sample per prep method)
    # ================================================================
    def _pages_sample_results(self, c):
        samples = self.d.get("samples", [])
        for samp in samples:
            self._new_page(c)
            y = self._draw_header_with_logo(c, "SAMPLE RESULTS")
            y -= 6

            # Report prepared for + dates header
            c.setFont("Helvetica-Bold", 8)
            c.drawString(MARGIN, y, "Report prepared for:")
            c.setFont("Helvetica", 8)
            c.drawString(MARGIN + 105, y, self.d.get("client_contact", ""))
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(PAGE_W-MARGIN, y, f"Date/Time Received: {self.d.get('date_received_text','')}")
            y -= 12
            c.setFont("Helvetica", 8)
            c.drawString(MARGIN + 105, y, self.d.get("client_company", ""))
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(PAGE_W-MARGIN, y, f"Date Reported: {self.d.get('report_date','')}")
            y -= 14

            # Client Sample Info box
            box_y = y
            c.setStrokeColor(black)
            c.setLineWidth(0.5)
            info_h = 72
            c.rect(MARGIN, box_y - info_h, CONTENT_W, info_h, fill=0, stroke=1)

            inner_y = box_y - 12
            left_x = MARGIN + 5
            mid_x = PAGE_W / 2

            fields_left = [
                ("Client Sample ID:", samp.get("client_sample_id", "")),
                ("Project Name/Location:", self.d.get("project_name", "")),
                ("Project Number:", self.d.get("project_number", "")),
                ("Date/Time Sampled:", samp.get("date_sampled", "")),
                ("SDG:", samp.get("sdg", "")),
            ]
            fields_right = [
                ("Lab Sample ID:", samp.get("lab_sample_id", "")),
                ("Sample Matrix:", samp.get("matrix", "Water")),
            ]
            for lbl, val in fields_left:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(left_x, inner_y, lbl)
                c.setFont("Helvetica", 8)
                c.drawString(left_x + 115, inner_y, str(val))
                inner_y -= 12

            inner_y2 = box_y - 12
            for lbl, val in fields_right:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(mid_x, inner_y2, lbl)
                c.setFont("Helvetica", 8)
                c.drawString(mid_x + 90, inner_y2, str(val))
                inner_y2 -= 12

            y = box_y - info_h - 8

            # Prep method groups
            prep_groups = samp.get("prep_groups", [])
            for pg in prep_groups:
                if y < 1.5*inch:
                    self._draw_footer(c)
                    self._new_page(c)
                    y = self._draw_header_with_logo(c, "SAMPLE RESULTS")
                    y -= 10

                # Prep method header (light blue bar)
                prep_h = 28
                c.setFillColor(KETOS_LIGHT_BLUE)
                c.rect(MARGIN, y - prep_h, CONTENT_W, prep_h, fill=1, stroke=1)
                c.setFillColor(black)
                c.setFont("Helvetica-Bold", 8)
                c.drawString(MARGIN + 5, y - 12, f"Prep Method:   {pg.get('prep_method','')}")
                c.drawString(MARGIN + 5, y - 24, f"Prep Batch ID:  {pg.get('prep_batch_id','')}")
                c.setFont("Helvetica-Bold", 8)
                mid = PAGE_W / 2 + 30
                c.drawString(mid, y - 12, f"Prep Batch Date/Time:")
                c.setFont("Helvetica", 8)
                c.drawString(mid + 130, y - 12, pg.get("prep_date_time", ""))
                c.setFont("Helvetica-Bold", 8)
                c.drawString(mid, y - 24, f"Prep Analyst:")
                c.setFont("Helvetica", 8)
                c.drawString(mid + 130, y - 24, pg.get("prep_analyst", ""))
                y -= prep_h + 2

                # Results table
                headers = ["Parameters:", "Analysis\nMethod", "DF", "MDL", "PQL", "Results", "Q", "Units", "Analyzed Time", "By", "Analytical\nBatch"]
                col_w = [110, 55, 25, 42, 42, 50, 20, 35, 72, 28, 55]
                align_list = ['L','C','C','C','C','R','C','C','C','C','C']
                rows = []
                for r in pg.get("results", []):
                    rows.append([
                        r.get("parameter",""),
                        r.get("method",""),
                        r.get("df","1"),
                        r.get("mdl",""),
                        r.get("pql",""),
                        r.get("result",""),
                        r.get("qualifier",""),
                        r.get("unit","mg/L"),
                        r.get("analyzed_time",""),
                        r.get("analyst",""),
                        r.get("analytical_batch",""),
                    ])
                y = self._draw_table(c, y, headers, rows, col_w, align=align_list,
                                     bold_cols={5}, font_size=7.5, header_font_size=7)
                y -= 14

            self._draw_footer(c)

    # ================================================================
    # PAGE 7: MB SUMMARY REPORT
    # ================================================================
    def _page_mb_summary(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c, "MB Summary Report")
        y -= 6

        mb_batches = self.d.get("mb_batches", [])
        for mb in mb_batches:
            if y < 1.5*inch:
                self._draw_footer(c)
                self._new_page(c)
                y = self._draw_header_with_logo(c, "MB Summary Report")
                y -= 10

            # Batch header
            hdr_fields = [
                [("Work Order:", mb.get("work_order", self.d.get("work_order",""))),
                 ("Prep Method:", mb.get("prep_method","")),
                 ("Prep Date:", mb.get("prep_date","")),
                 ("Prep Batch:", mb.get("prep_batch",""))],
                [("Matrix:", mb.get("matrix","Water")),
                 ("Analytical Method:", mb.get("analytical_method","")),
                 ("Analyzed Date:", mb.get("analyzed_date","")),
                 ("Analytical Batch:", mb.get("analytical_batch",""))],
                [("Units:", mb.get("units","mg/L")), ("",""), ("",""), ("","")],
            ]
            for row_fields in hdr_fields:
                cx = MARGIN
                c.setFont("Helvetica-Bold", 8)
                for lbl, val in row_fields:
                    c.setFont("Helvetica-Bold", 8)
                    c.drawString(cx, y, lbl)
                    c.setFont("Helvetica", 8)
                    c.drawString(cx + 80, y, str(val))
                    cx += CONTENT_W / 4
                y -= 13
            y -= 4

            headers = ["Parameters", "MDL", "PQL", "Method Blank\nConc.", "Lab\nQualifier"]
            col_w = [140, 55, 55, 80, 60]
            align_list = ['L','C','C','C','C']
            rows = []
            for r in mb.get("results", []):
                rows.append([
                    r.get("parameter",""),
                    r.get("mdl",""),
                    r.get("pql",""),
                    r.get("mb_conc","ND"),
                    r.get("qualifier",""),
                ])
            y = self._draw_table(c, y, headers, rows, col_w, align=align_list)
            y -= 18

        self._draw_footer(c)

    # ================================================================
    # PAGE 8: LCS/LCSD SUMMARY
    # ================================================================
    def _page_lcs_lcsd_summary(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c, "LCS/LCSD Summary Report")

        # Subtitle
        c.setFont("Helvetica-Oblique", 7)
        c.drawRightString(PAGE_W - MARGIN, y + 18, "Raw values are used in quality control assessment.")
        y -= 6

        lcs_batches = self.d.get("lcs_batches", [])
        for lcs in lcs_batches:
            if y < 1.5*inch:
                self._draw_footer(c)
                self._new_page(c)
                y = self._draw_header_with_logo(c, "LCS/LCSD Summary Report")
                y -= 10

            # Batch header
            hdr_fields = [
                [("Work Order:", lcs.get("work_order", self.d.get("work_order",""))),
                 ("Prep Method:", lcs.get("prep_method","")),
                 ("Prep Date:", lcs.get("prep_date","")),
                 ("Prep Batch:", lcs.get("prep_batch",""))],
                [("Matrix:", lcs.get("matrix","Water")),
                 ("Analytical Method:", lcs.get("analytical_method","")),
                 ("Analyzed Date:", lcs.get("analyzed_date","")),
                 ("Analytical Batch:", lcs.get("analytical_batch",""))],
                [("Units:", lcs.get("units","mg/L")), ("",""), ("",""), ("","")],
            ]
            for row_fields in hdr_fields:
                cx = MARGIN
                for lbl, val in row_fields:
                    c.setFont("Helvetica-Bold", 8)
                    c.drawString(cx, y, lbl)
                    c.setFont("Helvetica", 8)
                    c.drawString(cx + 80, y, str(val))
                    cx += CONTENT_W / 4
                y -= 13
            y -= 4

            headers = ["Parameters","MDL","PQL","Method\nBlank Conc.","Spike\nConc.",
                       "LCS %\nRecovery","LCSD %\nRecovery","LCS/LCSD\n% RPD",
                       "%\nRecovery\nLimits","% RPD\nLimits","Lab\nQualifier"]
            col_w = [80, 38, 38, 48, 38, 44, 44, 44, 48, 38, 40]
            align_list = ['L','C','C','C','C','C','C','C','C','C','C']
            rows = []
            for r in lcs.get("results", []):
                rows.append([
                    r.get("parameter",""),
                    r.get("mdl",""),
                    r.get("pql",""),
                    r.get("mb_conc","ND"),
                    r.get("spike_conc",""),
                    r.get("lcs_recovery",""),
                    r.get("lcsd_recovery",""),
                    r.get("rpd",""),
                    r.get("recovery_limits","80 - 120"),
                    r.get("rpd_limits","20"),
                    r.get("qualifier",""),
                ])
            y = self._draw_table(c, y, headers, rows, col_w, align=align_list,
                                 font_size=7, header_font_size=6.5, row_height=13)
            y -= 18

        self._draw_footer(c)

    # ================================================================
    # PAGE 9: QUALIFIERS & DEFINITIONS
    # ================================================================
    def _page_qualifiers(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c, "Laboratory Qualifiers and Definitions")
        y -= 6

        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "DEFINITIONS:")
        y -= 8

        # Definitions box
        c.setStrokeColor(black)
        c.setLineWidth(0.5)

        def_start_y = y
        c.setFont("Helvetica", 7.5)
        y -= 6
        for term, defn in DEFINITIONS:
            if y < 1.2*inch:
                break
            c.setFont("Helvetica-Bold", 7.5)
            text = f"{term}"
            c.drawString(MARGIN + 5, y, text)
            c.setFont("Helvetica", 7.5)
            # wrap definition
            words = (f" — {defn}").split()
            line = ""
            x_off = MARGIN + 5 + c.stringWidth(text, "Helvetica-Bold", 7.5)
            first_line = True
            for w in words:
                test = line + " " + w if line else w
                if c.stringWidth(test, "Helvetica", 7.5) > (CONTENT_W - 15 - (x_off - MARGIN - 5 if first_line else 0)):
                    if first_line:
                        c.drawString(x_off, y, line)
                        first_line = False
                    else:
                        c.drawString(MARGIN + 5, y, line)
                    y -= 10
                    line = w
                else:
                    line = test
            if line:
                if first_line:
                    c.drawString(x_off, y, line)
                else:
                    c.drawString(MARGIN + 5, y, line)
                y -= 10
            y -= 4

        y -= 8
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "LABORATORY QUALIFIERS:")
        y -= 6

        c.setStrokeColor(black)
        c.rect(MARGIN, y - 200, CONTENT_W, 200 + (y - (y-200))/200 * 10, stroke=1, fill=0)

        y -= 10
        for code, desc in QUALIFIER_DEFINITIONS:
            if y < 0.8*inch:
                break
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(MARGIN + 8, y, code)
            c.setFont("Helvetica", 7.5)
            # Wrap
            max_w = CONTENT_W - 50
            words = (f" — {desc}").split()
            line = ""
            for w in words:
                test = line + " " + w if line else w
                if c.stringWidth(test, "Helvetica", 7.5) > max_w:
                    c.drawString(MARGIN + 35, y, line)
                    y -= 10
                    line = w
                else:
                    line = test
            if line:
                c.drawString(MARGIN + 35, y, line)
                y -= 10
            y -= 2

        self._draw_footer(c)

    # ================================================================
    # PAGE 10: SAMPLE RECEIPT CHECKLIST
    # ================================================================
    def _page_receipt_checklist(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c, "Sample Receipt Checklist")
        y -= 10

        rcpt = self.d.get("receipt", {})

        # Header fields
        left_fields = [
            ("Client Name:", self.d.get("client_company","")),
            ("Project Name:", self.d.get("project_name","")),
            ("Work Order No.:", self.d.get("work_order","")),
        ]
        right_fields = [
            ("Date and Time Received:", rcpt.get("date_time_received","")),
            ("Received By:", rcpt.get("received_by","")),
            ("Physically Logged By:", rcpt.get("physically_logged_by","")),
            ("Checklist Completed By:", rcpt.get("checklist_completed_by","")),
            ("Carrier Name:", rcpt.get("carrier_name","")),
        ]

        for i, (lbl, val) in enumerate(left_fields):
            c.setFont("Helvetica", 9)
            c.drawString(MARGIN, y, f"{lbl}  ")
            c.setFont("Helvetica", 9)
            c.drawString(MARGIN + 110, y, str(val))
            if i < len(right_fields):
                rl, rv = right_fields[i]
                c.drawString(PAGE_W/2 + 20, y, f"{rl}  {rv}")
            y -= 14
        # remaining right fields
        for i in range(len(left_fields), len(right_fields)):
            rl, rv = right_fields[i]
            c.drawString(PAGE_W/2 + 20, y, f"{rl}  {rv}")
            y -= 14

        y -= 8
        # Section: Chain of Custody
        sections = [
            ("Chain of Custody (COC) Information", [
                ("Chain of custody present?", rcpt.get("coc_present","")),
                ("Chain of custody signed when relinquished and received?", rcpt.get("coc_signed","")),
                ("Chain of custody agrees with sample labels?", rcpt.get("coc_agrees","")),
                ("Custody seals intact on sample bottles?", rcpt.get("custody_seals_bottles","")),
            ]),
            ("Sample Receipt Information", [
                ("Custody seals intact on shipping container/cooler?", rcpt.get("custody_seals_cooler","")),
                ("Shipping Container/Cooler In Good Condition?", rcpt.get("cooler_good","")),
                ("Samples in proper container/bottle?", rcpt.get("proper_container","")),
                ("Samples containers intact?", rcpt.get("containers_intact","")),
                ("Sufficient sample volume for indicated test?", rcpt.get("sufficient_volume","")),
            ]),
            ("Sample Preservation and Hold Time (HT) Information", [
                ("All samples received within holding time?", rcpt.get("within_holding_time","")),
                ("Container/Temp Blank temperature in compliance?", f"{rcpt.get('temp_compliance','')}          Temperature:  {rcpt.get('temperature','')}  °C"),
                ("Water-VOA vials have zero headspace?", rcpt.get("voa_headspace","")),
                ("Water-pH acceptable upon receipt?", rcpt.get("ph_acceptable","")),
            ]),
        ]
        for sec_title, items in sections:
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(PAGE_W/2, y, sec_title)
            y -= 3
            self._draw_line(c, y, MARGIN + 60, PAGE_W - MARGIN - 60)
            y -= 14
            for q, a in items:
                c.setFont("Helvetica", 9)
                c.drawString(MARGIN + 20, y, q)
                c.setFont("Helvetica", 9)
                c.drawString(PAGE_W/2 + 60, y, str(a))
                y -= 14
            y -= 6

        # pH checked/adjusted
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 20, y, f"pH Checked by:  {rcpt.get('ph_checked_by','')}")
        c.drawString(PAGE_W/2 + 20, y, f"pH Adjusted by:  {rcpt.get('ph_adjusted_by','')}")
        y -= 18

        # Comments
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "Comments:")
        y -= 14
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 10, y, rcpt.get("receipt_comments",""))

        self._draw_footer(c)

    # ================================================================
    # PAGE 11: LOGIN SUMMARY REPORT
    # ================================================================
    def _page_login_summary(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c, "Login Summary Report")
        y -= 10

        ls = self.d.get("login_summary", {})
        # Header fields
        left = [
            ("Client ID:", f"{ls.get('client_id_code','')}    {self.d.get('client_company','')}"),
            ("Project Name:", self.d.get("project_name","")),
            ("Project #:", self.d.get("project_number","")),
            ("Report Due Date:", ls.get("report_due_date","")),
        ]
        right = [
            ("QC Level:", ls.get("qc_level","II")),
            ("TAT Requested:", ls.get("tat_requested","")),
            ("Date Received:", ls.get("date_received_login","")),
            ("Time Received:", ls.get("time_received_login","")),
        ]
        for i in range(max(len(left), len(right))):
            if i < len(left):
                lbl, val = left[i]
                c.setFont("Helvetica-Bold", 8)
                c.drawString(MARGIN, y, lbl)
                c.setFont("Helvetica", 8)
                c.drawString(MARGIN + 95, y, str(val))
            if i < len(right):
                rl, rv = right[i]
                c.setFont("Helvetica-Bold", 8)
                c.drawString(PAGE_W/2 + 80, y, rl)
                c.setFont("Helvetica", 8)
                c.drawString(PAGE_W/2 + 175, y, str(rv))
            y -= 14

        # Comments
        y -= 4
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN, y, "Comments:")
        y -= 14
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN, y, f"Work Order # :    {self.d.get('work_order','')}")
        y -= 18
        self._draw_line(c, y)
        y -= 4

        # Sample table
        headers = ["WO Sample ID", "Client\nSample ID", "Collection\nDate/Time", "Matrix",
                    "Scheduled\nDisposal", "Sample\nOn Hold", "Test\nOn Hold", "Requested\nTests", "Subbed"]
        col_w = [72, 62, 62, 40, 55, 42, 35, 80, 40]
        align_list = ['L','L','C','C','C','C','C','L','C']
        rows = []
        for samp in self.d.get("samples", []):
            tests = ", ".join([pg.get("prep_method","") for pg in samp.get("prep_groups",[])])
            rows.append([
                samp.get("lab_sample_id",""),
                samp.get("client_sample_id",""),
                samp.get("date_sampled",""),
                samp.get("matrix","Water"),
                samp.get("disposal_date",""),
                "", "",
                tests,
                "",
            ])
        y = self._draw_table(c, y, headers, rows, col_w, align=align_list,
                             font_size=7, header_font_size=6.5)
        self._draw_footer(c)

    # ================================================================
    # PAGE 12: CHAIN OF CUSTODY
    # ================================================================
    def _page_coc(self, c):
        self._new_page(c)
        y = self._draw_header_with_logo(c)

        if self.coc_bytes:
            coc_img = io.BytesIO(self.coc_bytes)
            img = PILImage.open(io.BytesIO(self.coc_bytes))
            iw, ih = img.size
            max_w = CONTENT_W
            max_h = PAGE_H - 2*inch
            scale = min(max_w / iw, max_h / ih)
            draw_w, draw_h = iw * scale, ih * scale
            x = MARGIN + (CONTENT_W - draw_w) / 2
            c.drawImage(coc_img, x, y - draw_h - 10, width=draw_w, height=draw_h,
                        preserveAspectRatio=True, mask='auto')
        else:
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(PAGE_W/2, PAGE_H/2, "CHAIN OF CUSTODY")
            c.setFont("Helvetica", 10)
            c.drawCentredString(PAGE_W/2, PAGE_H/2 - 20, "(Upload CoC image in the application)")

        self._draw_footer(c)


# ============================================================================
# STREAMLIT UI
# ============================================================================
def main():
    st.set_page_config(
        page_title="KELP COA Generator",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
    <style>
    .stApp { font-family: 'Calibri', 'Segoe UI', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #1F4E79 0%, #4AAEC7 100%);
        padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #D6E4F0; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .section-header {
        background-color: #1F4E79; color: white;
        padding: 0.5rem 1rem; border-radius: 5px; margin: 1rem 0 0.5rem 0;
        font-weight: bold;
    }
    div[data-testid="stSidebar"] { background-color: #f8f9fa; }
    .stButton > button {
        background: linear-gradient(135deg, #1F4E79, #4AAEC7);
        color: white; border: none; font-weight: bold;
    }
    .stButton > button:hover { background: linear-gradient(135deg, #163a5c, #3a9bb5); }
    </style>
    """, unsafe_allow_html=True)

    init_session()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 KELP — Certificate of Analysis Generator</h1>
        <p>KETOS Environmental Lab Platform &nbsp;|&nbsp; TNI / ISO 17025 / ELAP Compliant</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar — File uploads
    with st.sidebar:
        st.markdown("### 📁 File Uploads")
        logo_file = st.file_uploader("KELP Logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_up")
        if logo_file:
            st.session_state.logo_bytes = logo_file.read()
            st.image(st.session_state.logo_bytes, width=200)

        sig_file = st.file_uploader("Approver Signature (PNG/JPG)", type=["png","jpg","jpeg"], key="sig_up")
        if sig_file:
            st.session_state.signature_bytes = sig_file.read()
            st.image(st.session_state.signature_bytes, width=150)

        coc_file = st.file_uploader("Chain of Custody Scan (PNG/JPG/PDF)", type=["png","jpg","jpeg"], key="coc_up")
        if coc_file:
            st.session_state.coc_image_bytes = coc_file.read()
            st.success("CoC uploaded ✓")

        st.divider()
        st.markdown("### ⚙️ Settings")
        st.session_state.elap_number = st.text_input("ELAP #", st.session_state.elap_number)
        st.session_state.lab_phone_display = st.text_input("Lab Phone", st.session_state.lab_phone_display)

    # ---- Main Content in Tabs ----
    tabs = st.tabs([
        "📋 Report Info",
        "🧫 Samples & Results",
        "🔬 QC Data",
        "📦 Receipt & Login",
        "📄 Generate COA"
    ])

    # ============================
    # TAB 1: REPORT INFO
    # ============================
    with tabs[0]:
        st.markdown('<div class="section-header">Client Information</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.client_contact = st.text_input("Contact Name", st.session_state.client_contact)
            st.session_state.client_company = st.text_input("Company", st.session_state.client_company)
            st.session_state.client_address = st.text_input("Address", st.session_state.client_address)
            st.session_state.client_email = st.text_input("Email", st.session_state.client_email)
        with c2:
            st.session_state.project_name = st.text_input("Project Name", st.session_state.project_name)
            st.session_state.project_number = st.text_input("Project Number", st.session_state.project_number)
            st.session_state.work_order = st.text_input("Work Order #", st.session_state.work_order)
            st.session_state.client_id = st.text_input("Client ID", st.session_state.client_id)

        st.markdown('<div class="section-header">Report Details</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.session_state.report_date = st.date_input("Report Date", st.session_state.report_date)
            st.session_state.num_samples_text = st.text_input("Number of Samples", st.session_state.num_samples_text)
            st.session_state.date_received_text = st.text_input("Date Received (as displayed)", st.session_state.date_received_text, placeholder="January 13, 2022")
        with c4:
            st.session_state.approver_name = st.text_input("Approver Name", st.session_state.approver_name)
            st.session_state.approver_title = st.text_input("Approver Title", st.session_state.approver_title)
            st.session_state.approval_date = st.date_input("Approval Date", st.session_state.approval_date)

        st.markdown('<div class="section-header">Case Narrative</div>', unsafe_allow_html=True)
        st.session_state.qc_met = st.checkbox("All QC met EPA specifications", st.session_state.qc_met)
        st.session_state.method_blank_corrected = st.checkbox("Results are method/field blank corrected", st.session_state.method_blank_corrected)
        st.session_state.case_narrative_custom = st.text_area(
            "Custom Narrative (optional — appears first)",
            st.session_state.case_narrative_custom, height=80
        )

    # ============================
    # TAB 2: SAMPLES & RESULTS
    # ============================
    with tabs[1]:
        st.markdown('<div class="section-header">Samples</div>', unsafe_allow_html=True)
        samples = st.session_state.samples

        num_samples = st.number_input("Number of samples", min_value=0, max_value=50,
                                       value=len(samples), step=1)
        # Adjust list length
        while len(samples) < num_samples:
            samples.append({
                "client_sample_id": "",
                "lab_sample_id": "",
                "matrix": "Water",
                "date_sampled": "",
                "sdg": "",
                "disposal_date": "",
                "results": [],
                "prep_groups": [],
            })
        while len(samples) > num_samples:
            samples.pop()

        for si, samp in enumerate(samples):
            with st.expander(f"🧪 Sample {si+1}: {samp.get('lab_sample_id','(new)')}", expanded=(si==0)):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    samp["client_sample_id"] = st.text_input("Client Sample ID", samp.get("client_sample_id",""), key=f"csid_{si}")
                    samp["lab_sample_id"] = st.text_input("Lab Sample ID", samp.get("lab_sample_id",""), key=f"lsid_{si}")
                with sc2:
                    samp["matrix"] = st.selectbox("Matrix", ["Water","Soil","Air","Other"], index=0, key=f"mx_{si}")
                    samp["date_sampled"] = st.text_input("Date/Time Sampled", samp.get("date_sampled",""), key=f"ds_{si}")
                with sc3:
                    samp["sdg"] = st.text_input("SDG", samp.get("sdg",""), key=f"sdg_{si}")
                    samp["disposal_date"] = st.text_input("Scheduled Disposal", samp.get("disposal_date",""), key=f"disp_{si}")

                # Summary results (for page 3)
                st.markdown("**Summary Results** (Page 3 — Sample Result Summary)")
                n_res = st.number_input("# of result rows", min_value=0, max_value=50,
                                        value=len(samp.get("results",[])), key=f"nres_{si}")
                while len(samp["results"]) < n_res:
                    samp["results"].append({"parameter":"","method":"","df":"1","mdl":"","pql":"","result":"","unit":"mg/L"})
                while len(samp["results"]) > n_res:
                    samp["results"].pop()

                for ri, r in enumerate(samp["results"]):
                    rc = st.columns([3,2,1,1,1,1,1])
                    r["parameter"] = rc[0].text_input("Param", r.get("parameter",""), key=f"rp_{si}_{ri}")
                    r["method"] = rc[1].text_input("Method", r.get("method",""), key=f"rm_{si}_{ri}")
                    r["df"] = rc[2].text_input("DF", r.get("df","1"), key=f"rd_{si}_{ri}")
                    r["mdl"] = rc[3].text_input("MDL", r.get("mdl",""), key=f"rmdl_{si}_{ri}")
                    r["pql"] = rc[4].text_input("PQL", r.get("pql",""), key=f"rpql_{si}_{ri}")
                    r["result"] = rc[5].text_input("Result", r.get("result",""), key=f"rr_{si}_{ri}")
                    r["unit"] = rc[6].text_input("Unit", r.get("unit","mg/L"), key=f"ru_{si}_{ri}")

                st.divider()

                # Detailed prep groups (for pages 4-6)
                st.markdown("**Detailed Results by Prep Method** (Pages 4+ — Sample Results)")
                n_pg = st.number_input("# of Prep Method groups", min_value=0, max_value=10,
                                       value=len(samp.get("prep_groups",[])), key=f"npg_{si}")
                while len(samp["prep_groups"]) < n_pg:
                    samp["prep_groups"].append({
                        "prep_method":"","prep_batch_id":"","prep_date_time":"","prep_analyst":"",
                        "results":[]
                    })
                while len(samp["prep_groups"]) > n_pg:
                    samp["prep_groups"].pop()

                for pi, pg in enumerate(samp["prep_groups"]):
                    st.markdown(f"**Prep Group {pi+1}**")
                    pc = st.columns(4)
                    pg["prep_method"] = pc[0].text_input("Prep Method", pg.get("prep_method",""), key=f"pm_{si}_{pi}")
                    pg["prep_batch_id"] = pc[1].text_input("Prep Batch ID", pg.get("prep_batch_id",""), key=f"pbi_{si}_{pi}")
                    pg["prep_date_time"] = pc[2].text_input("Prep Date/Time", pg.get("prep_date_time",""), key=f"pdt_{si}_{pi}")
                    pg["prep_analyst"] = pc[3].text_input("Prep Analyst", pg.get("prep_analyst",""), key=f"pa_{si}_{pi}")

                    n_pr = st.number_input("# results in group", min_value=0, max_value=50,
                                           value=len(pg.get("results",[])), key=f"npr_{si}_{pi}")
                    while len(pg["results"]) < n_pr:
                        pg["results"].append({
                            "parameter":"","method":"","df":"1","mdl":"","pql":"","result":"",
                            "qualifier":"","unit":"mg/L","analyzed_time":"","analyst":"","analytical_batch":""
                        })
                    while len(pg["results"]) > n_pr:
                        pg["results"].pop()

                    for pri, pr in enumerate(pg["results"]):
                        prc = st.columns([2,1.5,0.5,1,1,1,0.5,0.7,1.5,0.7,1])
                        pr["parameter"] = prc[0].text_input("Param", pr.get("parameter",""), key=f"prp_{si}_{pi}_{pri}")
                        pr["method"] = prc[1].text_input("AMethod", pr.get("method",""), key=f"prm_{si}_{pi}_{pri}")
                        pr["df"] = prc[2].text_input("DF", pr.get("df","1"), key=f"prd_{si}_{pi}_{pri}")
                        pr["mdl"] = prc[3].text_input("MDL", pr.get("mdl",""), key=f"prmdl_{si}_{pi}_{pri}")
                        pr["pql"] = prc[4].text_input("PQL", pr.get("pql",""), key=f"prpql_{si}_{pi}_{pri}")
                        pr["result"] = prc[5].text_input("Result", pr.get("result",""), key=f"prr_{si}_{pi}_{pri}")
                        pr["qualifier"] = prc[6].text_input("Q", pr.get("qualifier",""), key=f"prq_{si}_{pi}_{pri}")
                        pr["unit"] = prc[7].text_input("Unit", pr.get("unit","mg/L"), key=f"pru_{si}_{pi}_{pri}")
                        pr["analyzed_time"] = prc[8].text_input("Analyzed", pr.get("analyzed_time",""), key=f"prat_{si}_{pi}_{pri}")
                        pr["analyst"] = prc[9].text_input("By", pr.get("analyst",""), key=f"prby_{si}_{pi}_{pri}")
                        pr["analytical_batch"] = prc[10].text_input("ABatch", pr.get("analytical_batch",""), key=f"prab_{si}_{pi}_{pri}")

    # ============================
    # TAB 3: QC DATA
    # ============================
    with tabs[2]:
        st.markdown('<div class="section-header">Method Blank (MB) Batches</div>', unsafe_allow_html=True)
        mb_batches = st.session_state.mb_batches
        n_mb = st.number_input("# of MB batches", 0, 20, len(mb_batches), key="n_mb")
        while len(mb_batches) < n_mb:
            mb_batches.append({"prep_method":"","analytical_method":"","prep_date":"","analyzed_date":"",
                               "prep_batch":"","analytical_batch":"","matrix":"Water","units":"mg/L",
                               "results":[]})
        while len(mb_batches) > n_mb:
            mb_batches.pop()

        for mi, mb in enumerate(mb_batches):
            with st.expander(f"MB Batch {mi+1}: {mb.get('prep_method','')} / {mb.get('analytical_method','')}"):
                mc = st.columns(4)
                mb["prep_method"] = mc[0].text_input("Prep Method", mb.get("prep_method",""), key=f"mbpm_{mi}")
                mb["analytical_method"] = mc[1].text_input("Analytical Method", mb.get("analytical_method",""), key=f"mbam_{mi}")
                mb["prep_date"] = mc[2].text_input("Prep Date", mb.get("prep_date",""), key=f"mbpd_{mi}")
                mb["analyzed_date"] = mc[3].text_input("Analyzed Date", mb.get("analyzed_date",""), key=f"mbad_{mi}")
                mc2 = st.columns(4)
                mb["prep_batch"] = mc2[0].text_input("Prep Batch", mb.get("prep_batch",""), key=f"mbpb_{mi}")
                mb["analytical_batch"] = mc2[1].text_input("Analytical Batch", mb.get("analytical_batch",""), key=f"mbab_{mi}")
                mb["matrix"] = mc2[2].text_input("Matrix", mb.get("matrix","Water"), key=f"mbmx_{mi}")
                mb["units"] = mc2[3].text_input("Units", mb.get("units","mg/L"), key=f"mbun_{mi}")

                n_mbr = st.number_input("# results", 0, 50, len(mb.get("results",[])), key=f"nmbr_{mi}")
                while len(mb["results"]) < n_mbr:
                    mb["results"].append({"parameter":"","mdl":"","pql":"","mb_conc":"ND","qualifier":""})
                while len(mb["results"]) > n_mbr:
                    mb["results"].pop()
                for ri, r in enumerate(mb["results"]):
                    rc = st.columns(5)
                    r["parameter"] = rc[0].text_input("Param", r.get("parameter",""), key=f"mbrp_{mi}_{ri}")
                    r["mdl"] = rc[1].text_input("MDL", r.get("mdl",""), key=f"mbrm_{mi}_{ri}")
                    r["pql"] = rc[2].text_input("PQL", r.get("pql",""), key=f"mbrpq_{mi}_{ri}")
                    r["mb_conc"] = rc[3].text_input("MB Conc.", r.get("mb_conc","ND"), key=f"mbrc_{mi}_{ri}")
                    r["qualifier"] = rc[4].text_input("Qual", r.get("qualifier",""), key=f"mbrqu_{mi}_{ri}")

        st.markdown('<div class="section-header">LCS/LCSD Batches</div>', unsafe_allow_html=True)
        lcs_batches = st.session_state.lcs_batches
        n_lcs = st.number_input("# of LCS/LCSD batches", 0, 20, len(lcs_batches), key="n_lcs")
        while len(lcs_batches) < n_lcs:
            lcs_batches.append({"prep_method":"","analytical_method":"","prep_date":"","analyzed_date":"",
                                "prep_batch":"","analytical_batch":"","matrix":"Water","units":"mg/L",
                                "results":[]})
        while len(lcs_batches) > n_lcs:
            lcs_batches.pop()

        for li, lcs in enumerate(lcs_batches):
            with st.expander(f"LCS/LCSD Batch {li+1}: {lcs.get('prep_method','')} / {lcs.get('analytical_method','')}"):
                lc = st.columns(4)
                lcs["prep_method"] = lc[0].text_input("Prep Method", lcs.get("prep_method",""), key=f"lpm_{li}")
                lcs["analytical_method"] = lc[1].text_input("Analytical Method", lcs.get("analytical_method",""), key=f"lam_{li}")
                lcs["prep_date"] = lc[2].text_input("Prep Date", lcs.get("prep_date",""), key=f"lpd_{li}")
                lcs["analyzed_date"] = lc[3].text_input("Analyzed Date", lcs.get("analyzed_date",""), key=f"lad_{li}")
                lc2 = st.columns(4)
                lcs["prep_batch"] = lc2[0].text_input("Prep Batch", lcs.get("prep_batch",""), key=f"lpb_{li}")
                lcs["analytical_batch"] = lc2[1].text_input("Analytical Batch", lcs.get("analytical_batch",""), key=f"lab_{li}")
                lcs["matrix"] = lc2[2].text_input("Matrix", lcs.get("matrix","Water"), key=f"lmx_{li}")
                lcs["units"] = lc2[3].text_input("Units", lcs.get("units","mg/L"), key=f"lun_{li}")

                n_lr = st.number_input("# results", 0, 50, len(lcs.get("results",[])), key=f"nlr_{li}")
                while len(lcs["results"]) < n_lr:
                    lcs["results"].append({"parameter":"","mdl":"","pql":"","mb_conc":"ND","spike_conc":"",
                                           "lcs_recovery":"","lcsd_recovery":"","rpd":"",
                                           "recovery_limits":"80 - 120","rpd_limits":"20","qualifier":""})
                while len(lcs["results"]) > n_lr:
                    lcs["results"].pop()
                for ri, r in enumerate(lcs["results"]):
                    rc = st.columns([2,1,1,1,1,1,1,1,1.2,0.8,0.8])
                    r["parameter"] = rc[0].text_input("Param", r.get("parameter",""), key=f"lrp_{li}_{ri}")
                    r["mdl"] = rc[1].text_input("MDL", r.get("mdl",""), key=f"lrm_{li}_{ri}")
                    r["pql"] = rc[2].text_input("PQL", r.get("pql",""), key=f"lrpq_{li}_{ri}")
                    r["mb_conc"] = rc[3].text_input("MB", r.get("mb_conc","ND"), key=f"lrc_{li}_{ri}")
                    r["spike_conc"] = rc[4].text_input("Spike", r.get("spike_conc",""), key=f"lrs_{li}_{ri}")
                    r["lcs_recovery"] = rc[5].text_input("LCS%", r.get("lcs_recovery",""), key=f"lrlcs_{li}_{ri}")
                    r["lcsd_recovery"] = rc[6].text_input("LCSD%", r.get("lcsd_recovery",""), key=f"lrlcsd_{li}_{ri}")
                    r["rpd"] = rc[7].text_input("RPD", r.get("rpd",""), key=f"lrrpd_{li}_{ri}")
                    r["recovery_limits"] = rc[8].text_input("Rec Lim", r.get("recovery_limits","80 - 120"), key=f"lrrl_{li}_{ri}")
                    r["rpd_limits"] = rc[9].text_input("RPD Lim", r.get("rpd_limits","20"), key=f"lrrpl_{li}_{ri}")
                    r["qualifier"] = rc[10].text_input("Q", r.get("qualifier",""), key=f"lrq_{li}_{ri}")

    # ============================
    # TAB 4: RECEIPT & LOGIN
    # ============================
    with tabs[3]:
        st.markdown('<div class="section-header">Sample Receipt Checklist (Page 10)</div>', unsafe_allow_html=True)
        rcpt = st.session_state.receipt
        rc1, rc2 = st.columns(2)
        with rc1:
            rcpt["date_time_received"] = st.text_input("Date/Time Received", rcpt["date_time_received"], key="rdt")
            rcpt["received_by"] = st.text_input("Received By", rcpt["received_by"], key="rrb")
            rcpt["physically_logged_by"] = st.text_input("Physically Logged By", rcpt["physically_logged_by"], key="rplb")
            rcpt["checklist_completed_by"] = st.text_input("Checklist Completed By", rcpt["checklist_completed_by"], key="rccb")
            rcpt["carrier_name"] = st.text_input("Carrier Name", rcpt["carrier_name"], key="rcn")
        with rc2:
            yes_no = ["Yes", "No", "Not Present", "N/A"]
            rcpt["coc_present"] = st.selectbox("CoC present?", yes_no, index=yes_no.index(rcpt.get("coc_present","Yes")), key="rcp")
            rcpt["coc_signed"] = st.selectbox("CoC signed?", yes_no, index=yes_no.index(rcpt.get("coc_signed","Yes")), key="rcs")
            rcpt["coc_agrees"] = st.selectbox("CoC agrees with labels?", yes_no, index=yes_no.index(rcpt.get("coc_agrees","Yes")), key="rca")
            rcpt["custody_seals_bottles"] = st.selectbox("Seals on bottles?", yes_no, index=yes_no.index(rcpt.get("custody_seals_bottles","Not Present")), key="rcsb")
            rcpt["custody_seals_cooler"] = st.selectbox("Seals on cooler?", yes_no, index=yes_no.index(rcpt.get("custody_seals_cooler","Not Present")), key="rcsc")

        rc3, rc4 = st.columns(2)
        with rc3:
            rcpt["cooler_good"] = st.selectbox("Cooler good condition?", yes_no, index=0, key="rcg")
            rcpt["proper_container"] = st.selectbox("Proper containers?", yes_no, index=0, key="rpc")
            rcpt["containers_intact"] = st.selectbox("Containers intact?", yes_no, index=0, key="rci")
            rcpt["sufficient_volume"] = st.selectbox("Sufficient volume?", yes_no, index=0, key="rsv")
        with rc4:
            rcpt["within_holding_time"] = st.selectbox("Within holding time?", yes_no, index=0, key="rwh")
            rcpt["temp_compliance"] = st.selectbox("Temp compliance?", ["Yes","No"], key="rtc")
            rcpt["temperature"] = st.text_input("Temperature (°C)", rcpt["temperature"], key="rtemp")
            voa_opts = ["No VOA vials submitted", "Yes", "No"]
            rcpt["voa_headspace"] = st.selectbox("VOA headspace?", voa_opts, key="rvoa")
            rcpt["ph_acceptable"] = st.selectbox("pH acceptable?", ["Yes","No"], key="rph")

        rc5, rc6 = st.columns(2)
        with rc5:
            rcpt["ph_checked_by"] = st.text_input("pH Checked By", rcpt["ph_checked_by"], key="rphc")
        with rc6:
            rcpt["ph_adjusted_by"] = st.text_input("pH Adjusted By", rcpt["ph_adjusted_by"], key="rpha")
        rcpt["receipt_comments"] = st.text_area("Receipt Comments", rcpt["receipt_comments"], key="rcom")

        st.divider()
        st.markdown('<div class="section-header">Login Summary (Page 11)</div>', unsafe_allow_html=True)
        ls = st.session_state.login_summary
        lc1, lc2 = st.columns(2)
        with lc1:
            ls["client_id_code"] = st.text_input("Client ID Code", ls["client_id_code"], key="lsci")
            ls["qc_level"] = st.selectbox("QC Level", ["I","II","III","IV"], index=1, key="lsqc")
            ls["report_due_date"] = st.text_input("Report Due Date", ls["report_due_date"], key="lsrd")
        with lc2:
            ls["tat_requested"] = st.text_input("TAT Requested", ls["tat_requested"], key="lstat")
            ls["date_received_login"] = st.text_input("Date Received", ls["date_received_login"], key="lsdr")
            ls["time_received_login"] = st.text_input("Time Received", ls["time_received_login"], key="lstr")
        ls["login_comments"] = st.text_input("Login Comments", ls.get("login_comments",""), key="lsc")

    # ============================
    # TAB 5: GENERATE
    # ============================
    with tabs[4]:
        st.markdown('<div class="section-header">Preview & Generate PDF</div>', unsafe_allow_html=True)

        # Count pages
        n_sample_pages = len(st.session_state.samples)
        total_est = 3 + n_sample_pages + 5  # cover + case + summary + sample pages + MB + LCS + quals + receipt + login + coc
        st.session_state.total_page_count = total_est

        st.info(f"Estimated total pages: **{total_est}**  (Cover + Case Narrative + Summary + {n_sample_pages} Sample pages + MB + LCS/LCSD + Qualifiers + Receipt + Login + CoC)")

        # Summary of entered data
        with st.expander("📊 Data Summary", expanded=True):
            st.write(f"**Work Order:** {st.session_state.work_order}")
            st.write(f"**Client:** {st.session_state.client_company} — {st.session_state.client_contact}")
            st.write(f"**Project:** {st.session_state.project_name}")
            st.write(f"**Samples:** {len(st.session_state.samples)}")
            st.write(f"**MB Batches:** {len(st.session_state.mb_batches)}")
            st.write(f"**LCS Batches:** {len(st.session_state.lcs_batches)}")
            st.write(f"**Logo:** {'✅' if st.session_state.logo_bytes else '❌ (text fallback)'}")
            st.write(f"**Signature:** {'✅' if st.session_state.signature_bytes else '❌'}")
            st.write(f"**CoC Image:** {'✅' if st.session_state.coc_image_bytes else '❌ (placeholder)'}")

        if st.button("🖨️  Generate COA PDF", type="primary", use_container_width=True):
            with st.spinner("Generating PDF..."):
                data = {
                    "elap_number": st.session_state.elap_number,
                    "lab_phone_display": st.session_state.lab_phone_display,
                    "report_date": str(st.session_state.report_date),
                    "work_order": st.session_state.work_order,
                    "total_page_count": st.session_state.total_page_count,
                    "client_contact": st.session_state.client_contact,
                    "client_company": st.session_state.client_company,
                    "project_name": st.session_state.project_name,
                    "project_number": st.session_state.project_number,
                    "num_samples_text": st.session_state.num_samples_text,
                    "date_received_text": st.session_state.date_received_text,
                    "approver_name": st.session_state.approver_name,
                    "approver_title": st.session_state.approver_title,
                    "approval_date": str(st.session_state.approval_date),
                    "qc_met": st.session_state.qc_met,
                    "method_blank_corrected": st.session_state.method_blank_corrected,
                    "case_narrative_custom": st.session_state.case_narrative_custom,
                    "samples": st.session_state.samples,
                    "mb_batches": st.session_state.mb_batches,
                    "lcs_batches": st.session_state.lcs_batches,
                    "receipt": st.session_state.receipt,
                    "login_summary": st.session_state.login_summary,
                }
                builder = KelpCOA(
                    data,
                    logo_bytes=st.session_state.logo_bytes,
                    sig_bytes=st.session_state.signature_bytes,
                    coc_bytes=st.session_state.coc_image_bytes,
                )
                pdf_bytes = builder.build()

            st.success(f"✅ COA generated — {len(pdf_bytes):,} bytes, {st.session_state.total_page_count} pages")

            wo = st.session_state.work_order or "DRAFT"
            filename = f"KELP_COA_{wo}_{date.today().strftime('%Y%m%d')}.pdf"

            st.download_button(
                label=f"⬇️ Download {filename}",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )

            # Inline preview
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px"></iframe>',
                        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
