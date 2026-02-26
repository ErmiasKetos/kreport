"""
KELP COA Generator v2 — Streamlit Cloud Application
=====================================================
KETOS Environmental Lab Platform (KELP)
Certificate of Analysis (COA) PDF Generator

Complete redesign using ReportLab Platypus layout engine for proper
text wrapping, pagination, and professional formatting.

Pages:
  1.  Cover Letter
  2.  Case Narrative
  3.  Sample Result Summary
  4+. Sample Results (detail per sample)
  MB  Method Blank Summary Report
  LCS LCS/LCSD Summary Report
  Q   Laboratory Qualifiers and Definitions
  RC  Sample Receipt Checklist
  LS  Login Summary Report
  CoC Chain of Custody (uploaded image)
"""

import streamlit as st
import io, os, base64, copy, json
from datetime import datetime, date, time as time_type

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Table, TableStyle,
    Paragraph, Spacer, Image, PageBreak, KeepTogether, NextPageTemplate,
    Flowable
)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

# ============================================================================
# BRANDING
# ============================================================================
C_NAVY    = HexColor("#1F4E79")
C_TEAL    = HexColor("#4AAEC7")
C_SKY     = HexColor("#D6E4F0")
C_LTGRAY  = HexColor("#E8ECF0")
C_MGRAY   = HexColor("#F5F6F8")
C_DKGRAY  = HexColor("#6B7280")
C_BLACK   = HexColor("#1A1A1A")
C_WHITE   = HexColor("#FFFFFF")
C_ACCENT  = HexColor("#E6F2F8")
C_BORDER  = HexColor("#B0C4D8")
C_ROW_ALT = HexColor("#F8FAFB")

PW, PH = letter  # 612 x 792
MG = 0.65 * inch
CW = PW - 2 * MG  # content width

# ============================================================================
# PARAGRAPH STYLES
# ============================================================================
def _styles():
    """Build all paragraph styles."""
    s = {}
    s['body'] = ParagraphStyle('body', fontName='Helvetica', fontSize=9, leading=12, textColor=C_BLACK)
    s['body_sm'] = ParagraphStyle('body_sm', fontName='Helvetica', fontSize=7.5, leading=10, textColor=C_BLACK)
    s['body_xs'] = ParagraphStyle('body_xs', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=C_BLACK)
    s['bold'] = ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=C_BLACK)
    s['bold_sm'] = ParagraphStyle('bold_sm', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=C_BLACK)
    s['bold_xs'] = ParagraphStyle('bold_xs', fontName='Helvetica-Bold', fontSize=6.5, leading=8.5, textColor=C_BLACK)
    s['title'] = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=C_NAVY, alignment=TA_CENTER)
    s['subtitle'] = ParagraphStyle('subtitle', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=C_NAVY, alignment=TA_CENTER)
    s['section'] = ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=C_NAVY)
    s['th'] = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=C_WHITE, alignment=TA_CENTER)
    s['th_left'] = ParagraphStyle('th_left', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=C_WHITE, alignment=TA_LEFT)
    s['td'] = ParagraphStyle('td', fontName='Helvetica', fontSize=7.5, leading=10, textColor=C_BLACK, alignment=TA_CENTER)
    s['td_left'] = ParagraphStyle('td_left', fontName='Helvetica', fontSize=7.5, leading=10, textColor=C_BLACK, alignment=TA_LEFT)
    s['td_right'] = ParagraphStyle('td_right', fontName='Helvetica', fontSize=7.5, leading=10, textColor=C_BLACK, alignment=TA_RIGHT)
    s['td_bold'] = ParagraphStyle('td_bold', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=C_BLACK, alignment=TA_RIGHT)
    s['label'] = ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=C_NAVY)
    s['value'] = ParagraphStyle('value', fontName='Helvetica', fontSize=8, leading=11, textColor=C_BLACK)
    s['footer'] = ParagraphStyle('footer', fontName='Helvetica', fontSize=7, leading=9, textColor=C_DKGRAY)
    s['italic_xs'] = ParagraphStyle('italic_xs', fontName='Helvetica-Oblique', fontSize=6.5, leading=8, textColor=C_DKGRAY, alignment=TA_RIGHT)
    s['qual_code'] = ParagraphStyle('qual_code', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=C_NAVY)
    s['qual_def'] = ParagraphStyle('qual_def', fontName='Helvetica', fontSize=7.5, leading=10, textColor=C_BLACK)
    return s

STY = _styles()

# ============================================================================
# CONSTANTS
# ============================================================================
LAB_NAME_FULL = "KETOS Environmental Lab Services"
LAB_ENTITY = "KETOS INC."
LAB_ADDR = ["1063 S De Anza Blvd", "San Jose, California 95129"]
LAB_PHONE = "Tel: 408-603-5552"
LAB_EMAIL = "Email: kelp@ketos.com"

QUALIFIER_DEFS = [
    ("B", "Indicates when the analyte is found in the associated method or preparation blank"),
    ("D", "Surrogate is not recoverable due to the necessary dilution of the sample"),
    ("E", "Indicates the reportable value is outside of the calibration range of the instrument but within the linear range (unless otherwise noted). Values with an E qualifier should be considered estimated."),
    ("H", "Indicates that the recommended holding time for the analyte or compound has been exceeded"),
    ("J", "Indicates a value between the method MDL and PQL; the reported concentration should be considered estimated rather than quantitative"),
    ("NA", "Not Analyzed"),
    ("N/A", "Not Applicable"),
    ("ND", "Not Detected at a concentration greater than the PQL/RL or, if reported to the MDL, at greater than the MDL"),
    ("NR", "Not recoverable — matrix spike concentration is not recoverable due to a concentration within the original sample &gt; 4x the spike concentration"),
    ("R", "The %RPD between a duplicate set of samples is outside of the absolute values established by laboratory control charts"),
    ("S", "Spike recovery is outside of established method and/or laboratory control limits. Further explanation should be included in the case narrative."),
    ("X", "Value based on pattern identification is within the pattern range but not typical of the pattern found in standards"),
]

TERM_DEFS = [
    ("Accuracy/Bias (% Recovery)", "The closeness of agreement between an observed value and an accepted reference value."),
    ("Blank (Method/Preparation Blank)", "MB/PB — An analyte-free matrix to which all reagents are added in the same volumes/proportions as used in sample processing, used to document contamination from the analytical process."),
    ("Duplicate", "A field sample and/or laboratory QC sample prepared in duplicate following all of the same processes and procedures used on the original sample (sample duplicate, LCSD, MSD)."),
    ("Laboratory Control Sample (LCS/LCSD)", "A known matrix spiked with compounds representative of the target analyte(s), used to document laboratory performance."),
    ("Matrix", "The component or substrate containing the analyte of interest (e.g., groundwater, sediment, soil, waste water)."),
    ("Matrix Spike (MS/MSD)", "Client sample spiked with identical concentrations of target analyte(s) prior to sample preparation and analysis, used to document precision and bias of a method in a given sample matrix."),
    ("Method Detection Limit (MDL)", "The minimum concentration of a substance that can be measured and reported with a 99% confidence that the analyte concentration is greater than zero."),
    ("PQL/RL/LOQ", "A laboratory-determined value at 2 to 5 times above the MDL, reproducible at a 99% confidence level for accuracy and precision. Reflects all preparation and/or dilution factors."),
    ("Precision (%RPD)", "The agreement among a set of replicate/duplicate measurements without regard to the known value."),
    ("Units", "mg/L and mg/Kg (PPM), ug/L and ug/Kg (PPB), ug/m3, mg/m3, ppbv, ppmv, % (10,000 ppm), ug/Wipe."),
]


# ============================================================================
# HELPER: Horizontal rule flowable
# ============================================================================
class HRule(Flowable):
    def __init__(self, width, color=C_BORDER, thickness=0.75):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 1, self.width, 1)


class ThinLine(HRule):
    def __init__(self, width):
        super().__init__(width, C_LTGRAY, 0.4)


# ============================================================================
# PDF BUILDER
# ============================================================================
class KelpCOABuilder:
    """Builds a multi-page COA PDF using Platypus flowables."""

    def __init__(self, data, logo_bytes=None, sig_bytes=None, coc_bytes=None):
        self.d = data
        self.logo_bytes = logo_bytes
        self.sig_bytes = sig_bytes
        self.coc_bytes = coc_bytes
        self.page_num = [0]
        self.total_pages = data.get("total_page_count", 12)

    def build(self) -> bytes:
        buf = io.BytesIO()
        doc = BaseDocTemplate(buf, pagesize=letter,
                              leftMargin=MG, rightMargin=MG,
                              topMargin=MG, bottomMargin=0.6*inch,
                              title=f"KELP COA — WO {self.d.get('work_order','')}")

        frame = Frame(MG, 0.6*inch, CW, PH - MG - 0.6*inch, id='main')
        page_num_holder = self.page_num
        total = self.total_pages

        def _on_page(canvas, doc_):
            page_num_holder[0] += 1
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(C_DKGRAY)
            # Footer line
            canvas.setStrokeColor(C_BORDER)
            canvas.setLineWidth(0.4)
            canvas.line(MG, 0.55*inch, PW - MG, 0.55*inch)
            canvas.drawString(MG, 0.38*inch, f"Total Page Count: {total}")
            canvas.drawRightString(PW - MG, 0.38*inch, f"Page {page_num_holder[0]} of {total}")
            canvas.restoreState()

        doc.addPageTemplates([PageTemplate(id='all', frames=[frame], onPage=_on_page)])

        story = []
        story += self._cover_letter()
        story.append(PageBreak())
        story += self._case_narrative()
        story.append(PageBreak())
        story += self._sample_result_summary()
        for samp in self.d.get("samples", []):
            story.append(PageBreak())
            story += self._sample_results_detail(samp)
        story.append(PageBreak())
        story += self._mb_summary()
        story.append(PageBreak())
        story += self._lcs_lcsd_summary()
        story.append(PageBreak())
        story += self._qualifiers_page()
        story.append(PageBreak())
        story += self._receipt_checklist()
        story.append(PageBreak())
        story += self._login_summary()
        story.append(PageBreak())
        story += self._coc_page()

        doc.build(story)
        return buf.getvalue()

    # ---- shared builders ----
    def _make_image_buf(self, raw_bytes):
        """Create a seeked BytesIO suitable for reportlab Platypus Image."""
        buf = io.BytesIO(raw_bytes)
        buf.seek(0)
        buf.name = 'image.png'  # reportlab checks extension via .name
        return buf

    def _logo_flowable(self, max_w=1.6*inch, max_h=0.85*inch):
        if self.logo_bytes:
            img = PILImage.open(io.BytesIO(self.logo_bytes))
            iw, ih = img.size
            scale = min(max_w / iw, max_h / ih)
            return Image(self._make_image_buf(self.logo_bytes), width=iw*scale, height=ih*scale)
        else:
            return Paragraph(
                '<font color="#1F4E79" size="16"><b>KETOS</b></font>'
                '<br/><font color="#4AAEC7" size="7">ENVIRONMENTAL LAB SERVICES</font>',
                ParagraphStyle('logo', fontSize=16, leading=18))

    def _page_header(self, title_text):
        """Returns [logo, spacer, title, rule]"""
        items = []
        items.append(self._logo_flowable())
        items.append(Spacer(1, 6))
        items.append(Paragraph(title_text, STY['title']))
        items.append(Spacer(1, 3))
        items.append(HRule(CW, C_NAVY, 1))
        items.append(Spacer(1, 8))
        return items

    def _info_table(self, rows_data, col_widths=None):
        """Two-col label: value table for info blocks.
        rows_data = [(label, value), ...] or [[(l,v),(l,v)], ...] for multi-col"""
        if not rows_data:
            return Spacer(1, 1)
        # Detect if it's pairs or row-of-pairs
        if isinstance(rows_data[0], tuple):
            rows_data = [rows_data]  # single row

        table_data = []
        for row in rows_data:
            if isinstance(row, tuple):
                row = [row]
            t_row = []
            for lbl, val in row:
                t_row.append(Paragraph(f'<b>{lbl}</b>', STY['label']))
                t_row.append(Paragraph(str(val), STY['value']))
            table_data.append(t_row)

        n_cols = len(table_data[0])
        if col_widths is None:
            w = CW / n_cols
            col_widths = [w] * n_cols

        t = Table(table_data, colWidths=col_widths, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    def _data_table(self, headers, rows, col_widths, bold_result_col=None):
        """Build a professional data table with navy headers and alternating rows."""
        tdata = []
        # Header row
        h_row = [Paragraph(h, STY['th_left'] if i == 0 else STY['th']) for i, h in enumerate(headers)]
        tdata.append(h_row)

        for ri, row in enumerate(rows):
            t_row = []
            for ci, val in enumerate(row):
                v = str(val) if val is not None else ""
                if ci == 0:
                    sty = STY['td_left']
                elif bold_result_col is not None and ci == bold_result_col:
                    sty = STY['td_bold']
                else:
                    sty = STY['td']
                t_row.append(Paragraph(v, sty))
            tdata.append(t_row)

        t = Table(tdata, colWidths=col_widths, hAlign='LEFT', repeatRows=1)
        style_cmds = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), C_NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            # All cells
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Grid
            ('LINEBELOW', (0, 0), (-1, 0), 0.8, C_NAVY),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, C_BORDER),
            ('LINEAFTER', (0, 0), (-2, -1), 0.25, C_LTGRAY),
        ]
        # Alternating row colors
        for ri in range(1, len(tdata)):
            if ri % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, ri), (-1, ri), C_ROW_ALT))
            # Row bottom border
            style_cmds.append(('LINEBELOW', (0, ri), (-1, ri), 0.25, C_LTGRAY))

        t.setStyle(TableStyle(style_cmds))
        return t

    def _batch_header_table(self, fields_dict):
        """Two-row batch header in a light box. fields_dict has keys mapped to display."""
        row1 = []
        row2 = []
        for lbl, val in fields_dict.items():
            row1.append(Paragraph(f'<b>{lbl}</b>', STY['bold_xs']))
            row2.append(Paragraph(str(val), STY['body_sm']))
        n = len(row1)
        w = CW / n
        tdata = [row1, row2]
        t = Table(tdata, colWidths=[w]*n, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_ACCENT),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))
        return t

    # ================================================================
    # PAGE 1: COVER LETTER
    # ================================================================
    def _cover_letter(self):
        s = []
        s.append(self._logo_flowable(max_w=2*inch, max_h=1.1*inch))
        s.append(Spacer(1, 12))

        # Address block
        contact = self.d.get("client_contact", "")
        addr_lines = [contact, LAB_ENTITY] + LAB_ADDR + [LAB_PHONE, LAB_EMAIL]
        for line in addr_lines:
            if line:
                s.append(Paragraph(line, STY['body']))
        s.append(Spacer(1, 6))

        # RE: line
        s.append(Paragraph(f"RE: {self.d.get('project_name','')}", STY['bold']))
        s.append(Spacer(1, 14))

        # Work Order centered
        s.append(Paragraph(f"Work Order No.:  {self.d.get('work_order','')}", ParagraphStyle('wo', parent=STY['body'], alignment=TA_CENTER, fontSize=10)))
        s.append(Spacer(1, 24))

        # Greeting
        s.append(Paragraph(f"Dear {contact}:", STY['body']))
        s.append(Spacer(1, 10))

        # Body paragraphs
        recv = self.d.get("date_received_text", "")
        n_samp = self.d.get("num_samples_text", "1")
        elap = self.d.get("elap_number", "XXXX")
        phone = self.d.get("lab_phone_display", "(408) 603-5552")

        body_style = ParagraphStyle('body_letter', parent=STY['body'], fontSize=10, leading=14, alignment=TA_JUSTIFY, leftIndent=12, rightIndent=12)
        s.append(Paragraph(
            f"KELP received {n_samp} sample(s) on {recv} for the analyses presented in the following Report.",
            body_style))
        s.append(Spacer(1, 10))
        s.append(Paragraph(
            "All data for associated QC met EPA or laboratory specification(s) except where noted in the case narrative.",
            body_style))
        s.append(Spacer(1, 10))
        s.append(Paragraph(
            f"KELP is certified by the State of California, ELAP #{elap}. If you have any questions regarding these test results, please feel free to contact the Project Management Team at {phone}.",
            body_style))
        s.append(Spacer(1, 36))

        # Signature block
        sig_data = [['', '']]
        if self.sig_bytes:
            sig_img = Image(self._make_image_buf(self.sig_bytes), width=1.4*inch, height=0.7*inch)
            sig_data = [[sig_img, Paragraph(str(self.d.get("approval_date","")), STY['body'])]]
        else:
            sig_data = [['', Paragraph(str(self.d.get("approval_date","")), STY['body'])]]

        name = self.d.get("approver_name", "")
        title = self.d.get("approver_title", "")
        sig_data.append([Paragraph(f'<u>{"_"*30}</u>', STY['body']),
                         Paragraph(f'<u>{"_"*30}</u>', STY['body'])])
        sig_data.append([Paragraph(name, STY['bold']), Paragraph("Date", STY['bold'])])
        sig_data.append([Paragraph(title, STY['body']), Paragraph('', STY['body'])])

        sig_t = Table(sig_data, colWidths=[CW*0.45, CW*0.45], hAlign='LEFT')
        sig_t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        s.append(sig_t)
        return s

    # ================================================================
    # PAGE 2: CASE NARRATIVE
    # ================================================================
    def _case_narrative(self):
        s = self._page_header("CASE NARRATIVE")

        # Date right-aligned
        s.append(Paragraph(f'<b>Date:</b>  {self.d.get("report_date","")}', ParagraphStyle('dr', parent=STY['body'], alignment=TA_RIGHT)))
        s.append(HRule(CW, C_NAVY, 0.5))
        s.append(Spacer(1, 4))

        # Info rows
        info = [
            [("Client:", self.d.get("client_company","")), ("", "")],
            [("Project:", self.d.get("project_name","")), ("", "")],
            [("Work Order:", self.d.get("work_order","")), ("", "")],
        ]
        for row in info:
            s.append(self._info_table(row, col_widths=[0.8*inch, 3*inch, 0.5*inch, 1*inch]))
        s.append(Spacer(1, 4))
        s.append(HRule(CW, C_NAVY, 0.5))
        s.append(Spacer(1, 12))

        # Narrative body
        body_s = ParagraphStyle('cn_body', parent=STY['body'], fontSize=9.5, leading=14, spaceBefore=8, spaceAfter=4, leftIndent=8, rightIndent=8)

        custom = self.d.get("case_narrative_custom", "")
        if custom:
            s.append(Paragraph(custom, body_s))

        if self.d.get("qc_met", True):
            s.append(Paragraph(
                "Unless otherwise indicated in the following narrative, no issues encountered with the receiving, preparation, analysis or reporting of the results associated with this work order.",
                body_s))

        if not self.d.get("method_blank_corrected", False):
            s.append(Paragraph(
                "Unless otherwise indicated in the following narrative, no results have been method and/or field blank corrected.",
                body_s))

        s.append(Paragraph(
            "Reported results relate only to the items/samples tested by the laboratory.",
            body_s))
        s.append(Paragraph(
            "This report shall not be reproduced, except in full, without the written approval of KETOS INC.",
            body_s))
        return s

    # ================================================================
    # PAGE 3: SAMPLE RESULT SUMMARY
    # ================================================================
    def _sample_result_summary(self):
        s = self._page_header("Sample Result Summary")

        # Header info row
        contact = self.d.get("client_contact","")
        company = self.d.get("client_company","")
        recv = self.d.get("date_received_text","")
        rpt = self.d.get("report_date","")

        hdr = Table([
            [Paragraph('<b>Report prepared for:</b>', STY['label']),
             Paragraph(contact, STY['value']),
             Paragraph(f'<b>Date Received:</b>  {recv}', ParagraphStyle('r', parent=STY['label'], alignment=TA_RIGHT))],
            [Paragraph('', STY['label']),
             Paragraph(company, STY['value']),
             Paragraph(f'<b>Date Reported:</b>  {rpt}', ParagraphStyle('r', parent=STY['label'], alignment=TA_RIGHT))],
        ], colWidths=[1.3*inch, 2.5*inch, CW - 3.8*inch], hAlign='LEFT')
        hdr.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        s.append(hdr)
        s.append(Spacer(1, 10))

        for samp in self.d.get("samples", []):
            csid = samp.get("client_sample_id", "")
            lsid = samp.get("lab_sample_id", "")
            # Sample sub-header
            sh = Table([[
                Paragraph(f'<b>{csid}</b>', STY['bold']),
                Paragraph(f'<b>{lsid}</b>', ParagraphStyle('r', parent=STY['bold'], alignment=TA_RIGHT)),
            ]], colWidths=[CW*0.5, CW*0.5], hAlign='LEFT')
            sh.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,0), 0.5, C_NAVY),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
            ]))
            s.append(sh)
            s.append(Spacer(1, 3))

            # Results table
            headers = ["Parameters", "Analysis\nMethod", "DF", "MDL", "PQL", "Results", "Unit"]
            col_w = [2.2*inch, 0.8*inch, 0.4*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.5*inch]
            rows = []
            for r in samp.get("results", []):
                rows.append([r.get("parameter",""), r.get("method",""), r.get("df","1"),
                             r.get("mdl",""), r.get("pql",""), r.get("result",""), r.get("unit","mg/L")])
            s.append(self._data_table(headers, rows, col_w, bold_result_col=5))
            s.append(Spacer(1, 14))

        return s

    # ================================================================
    # SAMPLE RESULTS DETAIL
    # ================================================================
    def _sample_results_detail(self, samp):
        s = self._page_header("SAMPLE RESULTS")

        # Prepared-for header
        contact = self.d.get("client_contact","")
        company = self.d.get("client_company","")
        recv = self.d.get("date_received_text","")
        rpt = self.d.get("report_date","")

        hdr = Table([
            [Paragraph('<b>Report prepared for:</b>', STY['label']),
             Paragraph(contact, STY['value']),
             Paragraph(f'<b>Date/Time Received:</b>  {recv}', ParagraphStyle('r', parent=STY['label'], alignment=TA_RIGHT))],
            [Paragraph('', STY['label']),
             Paragraph(company, STY['value']),
             Paragraph(f'<b>Date Reported:</b>  {rpt}', ParagraphStyle('r', parent=STY['label'], alignment=TA_RIGHT))],
        ], colWidths=[1.3*inch, 2.2*inch, CW - 3.5*inch], hAlign='LEFT')
        hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),('LEFTPADDING',(0,0),(-1,-1),0)]))
        s.append(hdr)
        s.append(Spacer(1, 6))

        # Sample info box
        info_data = [
            [Paragraph('<b>Client Sample ID:</b>', STY['label']),
             Paragraph(samp.get("client_sample_id",""), STY['value']),
             Paragraph('<b>Lab Sample ID:</b>', STY['label']),
             Paragraph(samp.get("lab_sample_id",""), STY['value'])],
            [Paragraph('<b>Project Name/Location:</b>', STY['label']),
             Paragraph(self.d.get("project_name",""), STY['value']),
             Paragraph('<b>Sample Matrix:</b>', STY['label']),
             Paragraph(samp.get("matrix","Water"), STY['value'])],
            [Paragraph('<b>Project Number:</b>', STY['label']),
             Paragraph(self.d.get("project_number",""), STY['value']),
             Paragraph('', STY['label']),
             Paragraph('', STY['value'])],
            [Paragraph('<b>Date/Time Sampled:</b>', STY['label']),
             Paragraph(samp.get("date_sampled",""), STY['value']),
             Paragraph('', STY['label']),
             Paragraph('', STY['value'])],
            [Paragraph('<b>SDG:</b>', STY['label']),
             Paragraph(samp.get("sdg",""), STY['value']),
             Paragraph('', STY['label']),
             Paragraph('', STY['value'])],
        ]
        cw_info = [1.4*inch, 1.6*inch, 1.2*inch, CW - 4.2*inch]
        info_t = Table(info_data, colWidths=cw_info, hAlign='LEFT')
        info_t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.6, C_NAVY),
            ('BACKGROUND', (0,0), (-1,-1), C_WHITE),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
        ]))
        s.append(info_t)
        s.append(Spacer(1, 8))

        # Prep groups
        for pg in samp.get("prep_groups", []):
            # Prep method header bar
            prep_hdr = Table([
                [Paragraph(f'<b>Prep Method:</b>  {pg.get("prep_method","")}', STY['bold_sm']),
                 Paragraph(f'<b>Prep Batch Date/Time:</b>  {pg.get("prep_date_time","")}', STY['bold_sm'])],
                [Paragraph(f'<b>Prep Batch ID:</b>  {pg.get("prep_batch_id","")}', STY['bold_sm']),
                 Paragraph(f'<b>Prep Analyst:</b>  {pg.get("prep_analyst","")}', STY['bold_sm'])],
            ], colWidths=[CW*0.5, CW*0.5], hAlign='LEFT')
            prep_hdr.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C_SKY),
                ('BOX', (0,0), (-1,-1), 0.5, C_BORDER),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ]))
            s.append(prep_hdr)
            s.append(Spacer(1, 2))

            # Results table
            headers = ["Parameters", "Analysis\nMethod", "DF", "MDL", "PQL",
                       "Results", "Q", "Units", "Analyzed\nDate/Time", "By", "Analytical\nBatch"]
            col_w = [1.35*inch, 0.6*inch, 0.3*inch, 0.5*inch, 0.5*inch,
                     0.5*inch, 0.25*inch, 0.4*inch, 0.8*inch, 0.3*inch, 0.7*inch]
            rows = []
            for r in pg.get("results", []):
                rows.append([
                    r.get("parameter",""), r.get("method",""), r.get("df","1"),
                    r.get("mdl",""), r.get("pql",""), r.get("result",""),
                    r.get("qualifier",""), r.get("unit","mg/L"),
                    r.get("analyzed_time",""), r.get("analyst",""), r.get("analytical_batch",""),
                ])
            s.append(self._data_table(headers, rows, col_w, bold_result_col=5))
            s.append(Spacer(1, 12))

        return s

    # ================================================================
    # MB SUMMARY
    # ================================================================
    def _mb_summary(self):
        s = self._page_header("MB Summary Report")

        for mb in self.d.get("mb_batches", []):
            # Batch header
            bh = self._batch_header_table({
                "Work Order:": mb.get("work_order", self.d.get("work_order","")),
                "Prep Method:": mb.get("prep_method",""),
                "Prep Date:": mb.get("prep_date",""),
                "Prep Batch:": mb.get("prep_batch",""),
            })
            s.append(bh)
            bh2 = self._batch_header_table({
                "Matrix:": mb.get("matrix","Water"),
                "Analytical Method:": mb.get("analytical_method",""),
                "Analyzed Date:": mb.get("analyzed_date",""),
                "Analytical Batch:": mb.get("analytical_batch",""),
            })
            s.append(bh2)
            s.append(Paragraph(f'<b>Units:</b>  {mb.get("units","mg/L")}',
                               ParagraphStyle('u', parent=STY['body_sm'], spaceBefore=2, spaceAfter=4)))
            s.append(Spacer(1, 4))

            headers = ["Parameters", "MDL", "PQL", "Method Blank\nConc.", "Lab\nQualifier"]
            col_w = [2*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch]
            rows = []
            for r in mb.get("results", []):
                rows.append([r.get("parameter",""), r.get("mdl",""), r.get("pql",""),
                             r.get("mb_conc","ND"), r.get("qualifier","")])
            s.append(self._data_table(headers, rows, col_w))
            s.append(Spacer(1, 16))

        return s

    # ================================================================
    # LCS/LCSD SUMMARY
    # ================================================================
    def _lcs_lcsd_summary(self):
        s = self._page_header("LCS/LCSD Summary Report")
        s.append(Paragraph("Raw values are used in quality control assessment.", STY['italic_xs']))
        s.append(Spacer(1, 6))

        for lcs in self.d.get("lcs_batches", []):
            bh = self._batch_header_table({
                "Work Order:": lcs.get("work_order", self.d.get("work_order","")),
                "Prep Method:": lcs.get("prep_method",""),
                "Prep Date:": lcs.get("prep_date",""),
                "Prep Batch:": lcs.get("prep_batch",""),
            })
            s.append(bh)
            bh2 = self._batch_header_table({
                "Matrix:": lcs.get("matrix","Water"),
                "Analytical Method:": lcs.get("analytical_method",""),
                "Analyzed Date:": lcs.get("analyzed_date",""),
                "Analytical Batch:": lcs.get("analytical_batch",""),
            })
            s.append(bh2)
            s.append(Paragraph(f'<b>Units:</b>  {lcs.get("units","mg/L")}',
                               ParagraphStyle('u', parent=STY['body_sm'], spaceBefore=2, spaceAfter=4)))
            s.append(Spacer(1, 4))

            headers = ["Parameters", "MDL", "PQL", "MB\nConc.", "Spike\nConc.",
                       "LCS %\nRecov.", "LCSD %\nRecov.", "LCS/LCSD\n%RPD",
                       "% Recov.\nLimits", "%RPD\nLimits", "Lab\nQual."]
            col_w = [1.15*inch, 0.45*inch, 0.45*inch, 0.4*inch, 0.4*inch,
                     0.52*inch, 0.52*inch, 0.52*inch, 0.55*inch, 0.42*inch, 0.38*inch]
            rows = []
            for r in lcs.get("results", []):
                rows.append([
                    r.get("parameter",""), r.get("mdl",""), r.get("pql",""),
                    r.get("mb_conc","ND"), r.get("spike_conc",""),
                    r.get("lcs_recovery",""), r.get("lcsd_recovery",""), r.get("rpd",""),
                    r.get("recovery_limits","80 - 120"), r.get("rpd_limits","20"), r.get("qualifier",""),
                ])
            s.append(self._data_table(headers, rows, col_w))
            s.append(Spacer(1, 16))

        return s

    # ================================================================
    # QUALIFIERS & DEFINITIONS
    # ================================================================
    def _qualifiers_page(self):
        s = self._page_header("Laboratory Qualifiers and Definitions")

        # DEFINITIONS section
        s.append(Paragraph('<b>DEFINITIONS</b>', ParagraphStyle('dh', parent=STY['section'], spaceBefore=4, spaceAfter=4)))
        s.append(HRule(CW, C_NAVY, 0.5))
        s.append(Spacer(1, 4))

        for term, defn in TERM_DEFS:
            s.append(Paragraph(f'<b>{term}</b> — {defn}', ParagraphStyle('def', parent=STY['body_sm'], spaceBefore=2, spaceAfter=3, leftIndent=6)))

        s.append(Spacer(1, 10))
        s.append(Paragraph('<b>LABORATORY QUALIFIERS</b>', ParagraphStyle('qh', parent=STY['section'], spaceBefore=4, spaceAfter=4)))
        s.append(HRule(CW, C_NAVY, 0.5))
        s.append(Spacer(1, 4))

        # Qualifiers in a clean two-column table
        q_data = []
        for code, desc in QUALIFIER_DEFS:
            q_data.append([
                Paragraph(f'<b>{code}</b>', STY['qual_code']),
                Paragraph(f'— {desc}', STY['qual_def']),
            ])
        q_t = Table(q_data, colWidths=[0.5*inch, CW - 0.5*inch - 12], hAlign='LEFT')
        q_t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (0,-1), 10),
            ('LEFTPADDING', (1,0), (1,-1), 4),
            ('BOX', (0,0), (-1,-1), 0.5, C_BORDER),
            ('LINEBELOW', (0,0), (-1,-2), 0.25, C_LTGRAY),
            ('BACKGROUND', (0,0), (0,-1), C_ACCENT),
        ]))
        s.append(q_t)
        return s

    # ================================================================
    # SAMPLE RECEIPT CHECKLIST
    # ================================================================
    def _receipt_checklist(self):
        s = self._page_header("Sample Receipt Checklist")
        rcpt = self.d.get("receipt", {})

        # Header info
        left = [
            ("Client Name:", self.d.get("client_company","")),
            ("Project Name:", self.d.get("project_name","")),
            ("Work Order No.:", self.d.get("work_order","")),
        ]
        right = [
            ("Date/Time Received:", rcpt.get("date_time_received","")),
            ("Received By:", rcpt.get("received_by","")),
            ("Physically Logged By:", rcpt.get("physically_logged_by","")),
            ("Checklist Completed By:", rcpt.get("checklist_completed_by","")),
            ("Carrier Name:", rcpt.get("carrier_name","")),
        ]
        n_rows = max(len(left), len(right))
        hdr_data = []
        for i in range(n_rows):
            row = []
            if i < len(left):
                row += [Paragraph(f'<b>{left[i][0]}</b>', STY['label']), Paragraph(left[i][1], STY['value'])]
            else:
                row += [Paragraph('', STY['label']), Paragraph('', STY['value'])]
            if i < len(right):
                row += [Paragraph(f'<b>{right[i][0]}</b>', STY['label']), Paragraph(right[i][1], STY['value'])]
            else:
                row += [Paragraph('', STY['label']), Paragraph('', STY['value'])]
            hdr_data.append(row)

        ht = Table(hdr_data, colWidths=[1.1*inch, 1.5*inch, 1.5*inch, CW - 4.1*inch], hAlign='LEFT')
        ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),('LEFTPADDING',(0,0),(-1,-1),0)]))
        s.append(ht)
        s.append(Spacer(1, 10))

        # Checklist sections
        sections = [
            ("Chain of Custody (COC) Information", [
                ("Chain of custody present?", rcpt.get("coc_present","")),
                ("Chain of custody signed when relinquished and received?", rcpt.get("coc_signed","")),
                ("Chain of custody agrees with sample labels?", rcpt.get("coc_agrees","")),
                ("Custody seals intact on sample bottles?", rcpt.get("custody_seals_bottles","")),
            ]),
            ("Sample Receipt Information", [
                ("Custody seals intact on shipping container/cooler?", rcpt.get("custody_seals_cooler","")),
                ("Shipping Container/Cooler in good condition?", rcpt.get("cooler_good","")),
                ("Samples in proper container/bottle?", rcpt.get("proper_container","")),
                ("Samples containers intact?", rcpt.get("containers_intact","")),
                ("Sufficient sample volume for indicated test?", rcpt.get("sufficient_volume","")),
            ]),
            ("Sample Preservation and Hold Time (HT) Information", [
                ("All samples received within holding time?", rcpt.get("within_holding_time","")),
                ("Container/Temp Blank temperature in compliance?", f'{rcpt.get("temp_compliance","")}     Temperature: {rcpt.get("temperature","")} °C'),
                ("Water-VOA vials have zero headspace?", rcpt.get("voa_headspace","")),
                ("Water-pH acceptable upon receipt?", rcpt.get("ph_acceptable","")),
            ]),
        ]
        for sec_title, items in sections:
            s.append(Paragraph(f'<b><u>{sec_title}</u></b>',
                               ParagraphStyle('st', parent=STY['section'], alignment=TA_CENTER, spaceBefore=6, spaceAfter=4)))
            s.append(ThinLine(CW))
            s.append(Spacer(1, 3))

            tdata = []
            for q, a in items:
                tdata.append([Paragraph(q, STY['body']), Paragraph(str(a), ParagraphStyle('ua', parent=STY['body'], textColor=C_NAVY))])
            ct = Table(tdata, colWidths=[3.5*inch, CW - 3.5*inch], hAlign='LEFT')
            ct.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
                ('LEFTPADDING',(0,0),(0,-1),16),('LEFTPADDING',(1,0),(1,-1),8),
            ]))
            s.append(ct)
            s.append(Spacer(1, 4))

        # pH / Comments
        s.append(Spacer(1, 4))
        ph_data = [[
            Paragraph(f'pH Checked by: {rcpt.get("ph_checked_by","")}', STY['body']),
            Paragraph(f'pH Adjusted by: {rcpt.get("ph_adjusted_by","")}', STY['body']),
        ]]
        s.append(Table(ph_data, colWidths=[CW*0.5, CW*0.5], hAlign='LEFT'))
        s.append(Spacer(1, 8))
        s.append(Paragraph('<b>Comments:</b>', STY['section']))
        s.append(Paragraph(rcpt.get("receipt_comments",""), ParagraphStyle('cm', parent=STY['body'], leftIndent=8)))
        return s

    # ================================================================
    # LOGIN SUMMARY
    # ================================================================
    def _login_summary(self):
        s = self._page_header("Login Summary Report")

        ls = self.d.get("login_summary", {})
        hdr = [
            [Paragraph('<b>Client ID:</b>', STY['label']),
             Paragraph(f'{ls.get("client_id_code","")}    {self.d.get("client_company","")}', STY['value']),
             Paragraph('<b>QC Level:</b>', STY['label']),
             Paragraph(ls.get("qc_level","II"), STY['value'])],
            [Paragraph('<b>Project Name:</b>', STY['label']),
             Paragraph(self.d.get("project_name",""), STY['value']),
             Paragraph('<b>TAT Requested:</b>', STY['label']),
             Paragraph(ls.get("tat_requested",""), STY['value'])],
            [Paragraph('<b>Project #:</b>', STY['label']),
             Paragraph(self.d.get("project_number",""), STY['value']),
             Paragraph('<b>Date Received:</b>', STY['label']),
             Paragraph(ls.get("date_received_login",""), STY['value'])],
            [Paragraph('<b>Report Due Date:</b>', STY['label']),
             Paragraph(ls.get("report_due_date",""), STY['value']),
             Paragraph('<b>Time Received:</b>', STY['label']),
             Paragraph(ls.get("time_received_login",""), STY['value'])],
        ]
        ht = Table(hdr, colWidths=[1.2*inch, 2*inch, 1.2*inch, CW - 4.4*inch], hAlign='LEFT')
        ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),('LEFTPADDING',(0,0),(-1,-1),0)]))
        s.append(ht)
        s.append(Spacer(1, 4))

        s.append(Paragraph(f'<b>Comments:</b>', STY['section']))
        s.append(Paragraph(f'<b>Work Order #:</b>  {self.d.get("work_order","")}',
                           ParagraphStyle('wo', parent=STY['bold'], spaceBefore=4, spaceAfter=8)))
        s.append(HRule(CW, C_NAVY, 0.5))
        s.append(Spacer(1, 6))

        # Sample table
        headers = ["WO Sample ID", "Client\nSample ID", "Collection\nDate/Time", "Matrix",
                    "Scheduled\nDisposal", "Sample\nOn Hold", "Test\nOn Hold", "Requested\nTests", "Subbed"]
        col_w = [0.85*inch, 0.75*inch, 0.75*inch, 0.5*inch, 0.65*inch, 0.5*inch, 0.45*inch, 1.0*inch, 0.4*inch]
        rows = []
        for samp in self.d.get("samples", []):
            tests = ", ".join([pg.get("prep_method","") for pg in samp.get("prep_groups",[])])
            rows.append([
                samp.get("lab_sample_id",""), samp.get("client_sample_id",""),
                samp.get("date_sampled",""), samp.get("matrix","Water"),
                samp.get("disposal_date",""), "", "", tests, "",
            ])
        s.append(self._data_table(headers, rows, col_w))
        return s

    # ================================================================
    # COC PAGE
    # ================================================================
    def _coc_page(self):
        s = self._page_header("Chain of Custody")
        if self.coc_bytes:
            img = PILImage.open(io.BytesIO(self.coc_bytes))
            iw, ih = img.size
            max_w = CW
            max_h = PH - 2.5*inch
            scale = min(max_w / iw, max_h / ih)
            s.append(Image(self._make_image_buf(self.coc_bytes), width=iw*scale, height=ih*scale))
        else:
            s.append(Spacer(1, 2*inch))
            s.append(Paragraph("(Upload Chain of Custody scan in the application)", ParagraphStyle('ph', parent=STY['body'], alignment=TA_CENTER, textColor=C_DKGRAY)))
        return s


# ============================================================================
# STREAMLIT UI (unchanged from v1 except wiring to new builder)
# ============================================================================
def init_session():
    defaults = {
        "elap_number": "XXXX", "lab_phone_display": "(408) 603-5552",
        "report_date": date.today(), "work_order": "", "total_page_count": 12,
        "client_contact": "", "client_company": "", "client_address": "",
        "client_city_state_zip": "", "client_phone": "", "client_email": "",
        "project_name": "", "project_number": "", "client_id": "",
        "num_samples_text": "1", "date_received_text": "",
        "approver_name": "Ermias L", "approver_title": "Lab Director",
        "approval_date": date.today(),
        "case_narrative_custom": "", "qc_met": True, "method_blank_corrected": False,
        "samples": [], "mb_batches": [], "lcs_batches": [],
        "receipt": {
            "date_time_received":"","received_by":"","physically_logged_by":"",
            "checklist_completed_by":"","carrier_name":"Client Drop Off",
            "coc_present":"Yes","coc_signed":"Yes","coc_agrees":"Yes",
            "custody_seals_bottles":"Not Present","custody_seals_cooler":"Not Present",
            "cooler_good":"Yes","proper_container":"Yes","containers_intact":"Yes",
            "sufficient_volume":"Yes","within_holding_time":"Yes","temp_compliance":"No",
            "temperature":"","voa_headspace":"No VOA vials submitted","ph_acceptable":"No",
            "ph_checked_by":"","ph_adjusted_by":"","receipt_comments":"",
        },
        "login_summary": {
            "client_id_code":"","qc_level":"II","tat_requested":"Standard",
            "date_received_login":"","time_received_login":"",
            "report_due_date":"","login_comments":"",
        },
        "logo_bytes": None, "signature_bytes": None, "coc_image_bytes": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def main():
    st.set_page_config(page_title="KELP COA Generator", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

    st.markdown("""
    <style>
    .stApp { font-family: 'Calibri', 'Segoe UI', sans-serif; }
    .main-header { background: linear-gradient(135deg, #1F4E79 0%, #4AAEC7 100%); padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 1.5rem; color: white; }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #D6E4F0; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .section-header { background-color: #1F4E79; color: white; padding: 0.5rem 1rem; border-radius: 5px; margin: 1rem 0 0.5rem 0; font-weight: bold; }
    div[data-testid="stSidebar"] { background-color: #f8f9fa; }
    .stButton > button { background: linear-gradient(135deg, #1F4E79, #4AAEC7); color: white; border: none; font-weight: bold; }
    .stButton > button:hover { background: linear-gradient(135deg, #163a5c, #3a9bb5); }
    </style>
    """, unsafe_allow_html=True)

    init_session()

    st.markdown("""
    <div class="main-header">
        <h1>🧪 KELP — Certificate of Analysis Generator</h1>
        <p>KETOS Environmental Lab Platform &nbsp;|&nbsp; TNI / ISO 17025 / ELAP Compliant</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 📁 File Uploads")
        logo_file = st.file_uploader("KELP Logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_up")
        if logo_file: st.session_state.logo_bytes = logo_file.read(); st.image(st.session_state.logo_bytes, width=200)
        sig_file = st.file_uploader("Approver Signature (PNG/JPG)", type=["png","jpg","jpeg"], key="sig_up")
        if sig_file: st.session_state.signature_bytes = sig_file.read(); st.image(st.session_state.signature_bytes, width=150)
        coc_file = st.file_uploader("Chain of Custody Scan (PNG/JPG)", type=["png","jpg","jpeg"], key="coc_up")
        if coc_file: st.session_state.coc_image_bytes = coc_file.read(); st.success("CoC uploaded ✓")
        st.divider()
        st.markdown("### ⚙️ Settings")
        st.session_state.elap_number = st.text_input("ELAP #", st.session_state.elap_number)
        st.session_state.lab_phone_display = st.text_input("Lab Phone", st.session_state.lab_phone_display)

    tabs = st.tabs(["📋 Report Info", "🧫 Samples & Results", "🔬 QC Data", "📦 Receipt & Login", "📄 Generate COA"])

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
        st.session_state.case_narrative_custom = st.text_area("Custom Narrative (optional)", st.session_state.case_narrative_custom, height=80)

    with tabs[1]:
        st.markdown('<div class="section-header">Samples</div>', unsafe_allow_html=True)
        samples = st.session_state.samples
        num_samples = st.number_input("Number of samples", 0, 50, len(samples), step=1)
        while len(samples) < num_samples: samples.append({"client_sample_id":"","lab_sample_id":"","matrix":"Water","date_sampled":"","sdg":"","disposal_date":"","results":[],"prep_groups":[]})
        while len(samples) > num_samples: samples.pop()
        for si, samp in enumerate(samples):
            with st.expander(f"🧪 Sample {si+1}: {samp.get('lab_sample_id','(new)')}", expanded=(si==0)):
                sc1, sc2, sc3 = st.columns(3)
                with sc1: samp["client_sample_id"] = st.text_input("Client Sample ID", samp.get("client_sample_id",""), key=f"csid_{si}"); samp["lab_sample_id"] = st.text_input("Lab Sample ID", samp.get("lab_sample_id",""), key=f"lsid_{si}")
                with sc2: samp["matrix"] = st.selectbox("Matrix", ["Water","Soil","Air","Other"], index=0, key=f"mx_{si}"); samp["date_sampled"] = st.text_input("Date/Time Sampled", samp.get("date_sampled",""), key=f"ds_{si}")
                with sc3: samp["sdg"] = st.text_input("SDG", samp.get("sdg",""), key=f"sdg_{si}"); samp["disposal_date"] = st.text_input("Scheduled Disposal", samp.get("disposal_date",""), key=f"disp_{si}")
                st.markdown("**Summary Results** (Page 3)")
                n_res = st.number_input("# result rows", 0, 50, len(samp.get("results",[])), key=f"nres_{si}")
                while len(samp["results"]) < n_res: samp["results"].append({"parameter":"","method":"","df":"1","mdl":"","pql":"","result":"","unit":"mg/L"})
                while len(samp["results"]) > n_res: samp["results"].pop()
                for ri, r in enumerate(samp["results"]):
                    rc = st.columns([3,2,1,1,1,1,1])
                    r["parameter"]=rc[0].text_input("Param",r.get("parameter",""),key=f"rp_{si}_{ri}"); r["method"]=rc[1].text_input("Method",r.get("method",""),key=f"rm_{si}_{ri}"); r["df"]=rc[2].text_input("DF",r.get("df","1"),key=f"rd_{si}_{ri}"); r["mdl"]=rc[3].text_input("MDL",r.get("mdl",""),key=f"rmdl_{si}_{ri}"); r["pql"]=rc[4].text_input("PQL",r.get("pql",""),key=f"rpql_{si}_{ri}"); r["result"]=rc[5].text_input("Result",r.get("result",""),key=f"rr_{si}_{ri}"); r["unit"]=rc[6].text_input("Unit",r.get("unit","mg/L"),key=f"ru_{si}_{ri}")
                st.divider()
                st.markdown("**Detailed Results by Prep Method** (Pages 4+)")
                n_pg = st.number_input("# Prep Method groups", 0, 10, len(samp.get("prep_groups",[])), key=f"npg_{si}")
                while len(samp["prep_groups"]) < n_pg: samp["prep_groups"].append({"prep_method":"","prep_batch_id":"","prep_date_time":"","prep_analyst":"","results":[]})
                while len(samp["prep_groups"]) > n_pg: samp["prep_groups"].pop()
                for pi, pg in enumerate(samp["prep_groups"]):
                    st.markdown(f"**Prep Group {pi+1}**")
                    pc = st.columns(4)
                    pg["prep_method"]=pc[0].text_input("Prep Method",pg.get("prep_method",""),key=f"pm_{si}_{pi}"); pg["prep_batch_id"]=pc[1].text_input("Prep Batch ID",pg.get("prep_batch_id",""),key=f"pbi_{si}_{pi}"); pg["prep_date_time"]=pc[2].text_input("Prep Date/Time",pg.get("prep_date_time",""),key=f"pdt_{si}_{pi}"); pg["prep_analyst"]=pc[3].text_input("Prep Analyst",pg.get("prep_analyst",""),key=f"pa_{si}_{pi}")
                    n_pr = st.number_input("# results", 0, 50, len(pg.get("results",[])), key=f"npr_{si}_{pi}")
                    while len(pg["results"]) < n_pr: pg["results"].append({"parameter":"","method":"","df":"1","mdl":"","pql":"","result":"","qualifier":"","unit":"mg/L","analyzed_time":"","analyst":"","analytical_batch":""})
                    while len(pg["results"]) > n_pr: pg["results"].pop()
                    for pri, pr in enumerate(pg["results"]):
                        prc = st.columns([2,1.5,0.5,1,1,1,0.5,0.7,1.5,0.7,1])
                        pr["parameter"]=prc[0].text_input("Param",pr.get("parameter",""),key=f"prp_{si}_{pi}_{pri}"); pr["method"]=prc[1].text_input("AMethod",pr.get("method",""),key=f"prm_{si}_{pi}_{pri}"); pr["df"]=prc[2].text_input("DF",pr.get("df","1"),key=f"prd_{si}_{pi}_{pri}"); pr["mdl"]=prc[3].text_input("MDL",pr.get("mdl",""),key=f"prmdl_{si}_{pi}_{pri}"); pr["pql"]=prc[4].text_input("PQL",pr.get("pql",""),key=f"prpql_{si}_{pi}_{pri}"); pr["result"]=prc[5].text_input("Result",pr.get("result",""),key=f"prr_{si}_{pi}_{pri}"); pr["qualifier"]=prc[6].text_input("Q",pr.get("qualifier",""),key=f"prq_{si}_{pi}_{pri}"); pr["unit"]=prc[7].text_input("Unit",pr.get("unit","mg/L"),key=f"pru_{si}_{pi}_{pri}"); pr["analyzed_time"]=prc[8].text_input("Analyzed",pr.get("analyzed_time",""),key=f"prat_{si}_{pi}_{pri}"); pr["analyst"]=prc[9].text_input("By",pr.get("analyst",""),key=f"prby_{si}_{pi}_{pri}"); pr["analytical_batch"]=prc[10].text_input("ABatch",pr.get("analytical_batch",""),key=f"prab_{si}_{pi}_{pri}")

    with tabs[2]:
        st.markdown('<div class="section-header">Method Blank (MB) Batches</div>', unsafe_allow_html=True)
        mb_batches = st.session_state.mb_batches
        n_mb = st.number_input("# MB batches", 0, 20, len(mb_batches), key="n_mb")
        while len(mb_batches) < n_mb: mb_batches.append({"prep_method":"","analytical_method":"","prep_date":"","analyzed_date":"","prep_batch":"","analytical_batch":"","matrix":"Water","units":"mg/L","results":[]})
        while len(mb_batches) > n_mb: mb_batches.pop()
        for mi, mb in enumerate(mb_batches):
            with st.expander(f"MB Batch {mi+1}: {mb.get('prep_method','')} / {mb.get('analytical_method','')}"):
                mc=st.columns(4); mb["prep_method"]=mc[0].text_input("Prep Method",mb.get("prep_method",""),key=f"mbpm_{mi}"); mb["analytical_method"]=mc[1].text_input("Analytical Method",mb.get("analytical_method",""),key=f"mbam_{mi}"); mb["prep_date"]=mc[2].text_input("Prep Date",mb.get("prep_date",""),key=f"mbpd_{mi}"); mb["analyzed_date"]=mc[3].text_input("Analyzed Date",mb.get("analyzed_date",""),key=f"mbad_{mi}")
                mc2=st.columns(4); mb["prep_batch"]=mc2[0].text_input("Prep Batch",mb.get("prep_batch",""),key=f"mbpb_{mi}"); mb["analytical_batch"]=mc2[1].text_input("Analytical Batch",mb.get("analytical_batch",""),key=f"mbab_{mi}"); mb["matrix"]=mc2[2].text_input("Matrix",mb.get("matrix","Water"),key=f"mbmx_{mi}"); mb["units"]=mc2[3].text_input("Units",mb.get("units","mg/L"),key=f"mbun_{mi}")
                n_mbr = st.number_input("# results", 0, 50, len(mb.get("results",[])), key=f"nmbr_{mi}")
                while len(mb["results"]) < n_mbr: mb["results"].append({"parameter":"","mdl":"","pql":"","mb_conc":"ND","qualifier":""})
                while len(mb["results"]) > n_mbr: mb["results"].pop()
                for ri, r in enumerate(mb["results"]):
                    rc=st.columns(5); r["parameter"]=rc[0].text_input("Param",r.get("parameter",""),key=f"mbrp_{mi}_{ri}"); r["mdl"]=rc[1].text_input("MDL",r.get("mdl",""),key=f"mbrm_{mi}_{ri}"); r["pql"]=rc[2].text_input("PQL",r.get("pql",""),key=f"mbrpq_{mi}_{ri}"); r["mb_conc"]=rc[3].text_input("MB Conc.",r.get("mb_conc","ND"),key=f"mbrc_{mi}_{ri}"); r["qualifier"]=rc[4].text_input("Qual",r.get("qualifier",""),key=f"mbrqu_{mi}_{ri}")
        st.markdown('<div class="section-header">LCS/LCSD Batches</div>', unsafe_allow_html=True)
        lcs_batches = st.session_state.lcs_batches
        n_lcs = st.number_input("# LCS/LCSD batches", 0, 20, len(lcs_batches), key="n_lcs")
        while len(lcs_batches) < n_lcs: lcs_batches.append({"prep_method":"","analytical_method":"","prep_date":"","analyzed_date":"","prep_batch":"","analytical_batch":"","matrix":"Water","units":"mg/L","results":[]})
        while len(lcs_batches) > n_lcs: lcs_batches.pop()
        for li, lcs in enumerate(lcs_batches):
            with st.expander(f"LCS/LCSD Batch {li+1}: {lcs.get('prep_method','')} / {lcs.get('analytical_method','')}"):
                lc=st.columns(4); lcs["prep_method"]=lc[0].text_input("Prep Method",lcs.get("prep_method",""),key=f"lpm_{li}"); lcs["analytical_method"]=lc[1].text_input("Analytical Method",lcs.get("analytical_method",""),key=f"lam_{li}"); lcs["prep_date"]=lc[2].text_input("Prep Date",lcs.get("prep_date",""),key=f"lpd_{li}"); lcs["analyzed_date"]=lc[3].text_input("Analyzed Date",lcs.get("analyzed_date",""),key=f"lad_{li}")
                lc2=st.columns(4); lcs["prep_batch"]=lc2[0].text_input("Prep Batch",lcs.get("prep_batch",""),key=f"lpb_{li}"); lcs["analytical_batch"]=lc2[1].text_input("Analytical Batch",lcs.get("analytical_batch",""),key=f"lab_{li}"); lcs["matrix"]=lc2[2].text_input("Matrix",lcs.get("matrix","Water"),key=f"lmx_{li}"); lcs["units"]=lc2[3].text_input("Units",lcs.get("units","mg/L"),key=f"lun_{li}")
                n_lr = st.number_input("# results", 0, 50, len(lcs.get("results",[])), key=f"nlr_{li}")
                while len(lcs["results"]) < n_lr: lcs["results"].append({"parameter":"","mdl":"","pql":"","mb_conc":"ND","spike_conc":"","lcs_recovery":"","lcsd_recovery":"","rpd":"","recovery_limits":"80 - 120","rpd_limits":"20","qualifier":""})
                while len(lcs["results"]) > n_lr: lcs["results"].pop()
                for ri, r in enumerate(lcs["results"]):
                    rc=st.columns([2,1,1,1,1,1,1,1,1.2,0.8,0.8]); r["parameter"]=rc[0].text_input("Param",r.get("parameter",""),key=f"lrp_{li}_{ri}"); r["mdl"]=rc[1].text_input("MDL",r.get("mdl",""),key=f"lrm_{li}_{ri}"); r["pql"]=rc[2].text_input("PQL",r.get("pql",""),key=f"lrpq_{li}_{ri}"); r["mb_conc"]=rc[3].text_input("MB",r.get("mb_conc","ND"),key=f"lrc_{li}_{ri}"); r["spike_conc"]=rc[4].text_input("Spike",r.get("spike_conc",""),key=f"lrs_{li}_{ri}"); r["lcs_recovery"]=rc[5].text_input("LCS%",r.get("lcs_recovery",""),key=f"lrlcs_{li}_{ri}"); r["lcsd_recovery"]=rc[6].text_input("LCSD%",r.get("lcsd_recovery",""),key=f"lrlcsd_{li}_{ri}"); r["rpd"]=rc[7].text_input("RPD",r.get("rpd",""),key=f"lrrpd_{li}_{ri}"); r["recovery_limits"]=rc[8].text_input("Rec Lim",r.get("recovery_limits","80 - 120"),key=f"lrrl_{li}_{ri}"); r["rpd_limits"]=rc[9].text_input("RPD Lim",r.get("rpd_limits","20"),key=f"lrrpl_{li}_{ri}"); r["qualifier"]=rc[10].text_input("Q",r.get("qualifier",""),key=f"lrq_{li}_{ri}")

    with tabs[3]:
        st.markdown('<div class="section-header">Sample Receipt Checklist (Page 10)</div>', unsafe_allow_html=True)
        rcpt = st.session_state.receipt
        rc1, rc2 = st.columns(2)
        with rc1: rcpt["date_time_received"]=st.text_input("Date/Time Received",rcpt["date_time_received"],key="rdt"); rcpt["received_by"]=st.text_input("Received By",rcpt["received_by"],key="rrb"); rcpt["physically_logged_by"]=st.text_input("Physically Logged By",rcpt["physically_logged_by"],key="rplb"); rcpt["checklist_completed_by"]=st.text_input("Checklist Completed By",rcpt["checklist_completed_by"],key="rccb"); rcpt["carrier_name"]=st.text_input("Carrier Name",rcpt["carrier_name"],key="rcn")
        with rc2:
            yn = ["Yes","No","Not Present","N/A"]
            rcpt["coc_present"]=st.selectbox("CoC present?",yn,index=yn.index(rcpt.get("coc_present","Yes")),key="rcp"); rcpt["coc_signed"]=st.selectbox("CoC signed?",yn,index=yn.index(rcpt.get("coc_signed","Yes")),key="rcs"); rcpt["coc_agrees"]=st.selectbox("CoC agrees with labels?",yn,index=yn.index(rcpt.get("coc_agrees","Yes")),key="rca"); rcpt["custody_seals_bottles"]=st.selectbox("Seals on bottles?",yn,index=yn.index(rcpt.get("custody_seals_bottles","Not Present")),key="rcsb"); rcpt["custody_seals_cooler"]=st.selectbox("Seals on cooler?",yn,index=yn.index(rcpt.get("custody_seals_cooler","Not Present")),key="rcsc")
        rc3, rc4 = st.columns(2)
        with rc3: rcpt["cooler_good"]=st.selectbox("Cooler good condition?",yn,index=0,key="rcg"); rcpt["proper_container"]=st.selectbox("Proper containers?",yn,index=0,key="rpc"); rcpt["containers_intact"]=st.selectbox("Containers intact?",yn,index=0,key="rci"); rcpt["sufficient_volume"]=st.selectbox("Sufficient volume?",yn,index=0,key="rsv")
        with rc4: rcpt["within_holding_time"]=st.selectbox("Within holding time?",yn,index=0,key="rwh"); rcpt["temp_compliance"]=st.selectbox("Temp compliance?",["Yes","No"],key="rtc"); rcpt["temperature"]=st.text_input("Temperature (°C)",rcpt["temperature"],key="rtemp"); rcpt["voa_headspace"]=st.selectbox("VOA headspace?",["No VOA vials submitted","Yes","No"],key="rvoa"); rcpt["ph_acceptable"]=st.selectbox("pH acceptable?",["Yes","No"],key="rph")
        rc5, rc6 = st.columns(2)
        with rc5: rcpt["ph_checked_by"]=st.text_input("pH Checked By",rcpt["ph_checked_by"],key="rphc")
        with rc6: rcpt["ph_adjusted_by"]=st.text_input("pH Adjusted By",rcpt["ph_adjusted_by"],key="rpha")
        rcpt["receipt_comments"]=st.text_area("Receipt Comments",rcpt["receipt_comments"],key="rcom")
        st.divider()
        st.markdown('<div class="section-header">Login Summary (Page 11)</div>', unsafe_allow_html=True)
        ls = st.session_state.login_summary
        lc1, lc2 = st.columns(2)
        with lc1: ls["client_id_code"]=st.text_input("Client ID Code",ls["client_id_code"],key="lsci"); ls["qc_level"]=st.selectbox("QC Level",["I","II","III","IV"],index=1,key="lsqc"); ls["report_due_date"]=st.text_input("Report Due Date",ls["report_due_date"],key="lsrd")
        with lc2: ls["tat_requested"]=st.text_input("TAT Requested",ls["tat_requested"],key="lstat"); ls["date_received_login"]=st.text_input("Date Received",ls["date_received_login"],key="lsdr"); ls["time_received_login"]=st.text_input("Time Received",ls["time_received_login"],key="lstr")

    with tabs[4]:
        st.markdown('<div class="section-header">Preview &amp; Generate PDF</div>', unsafe_allow_html=True)
        n_sample_pages = len(st.session_state.samples)
        total_est = 3 + n_sample_pages + 5 + (1 if st.session_state.coc_image_bytes else 1)
        st.session_state.total_page_count = total_est
        st.info(f"Estimated total pages: **{total_est}**")
        with st.expander("📊 Data Summary", expanded=True):
            st.write(f"**Work Order:** {st.session_state.work_order}  |  **Client:** {st.session_state.client_company}  |  **Project:** {st.session_state.project_name}")
            st.write(f"**Samples:** {len(st.session_state.samples)}  |  **MB Batches:** {len(st.session_state.mb_batches)}  |  **LCS Batches:** {len(st.session_state.lcs_batches)}")
            st.write(f"**Logo:** {'✅' if st.session_state.logo_bytes else '❌ text fallback'}  |  **Signature:** {'✅' if st.session_state.signature_bytes else '❌'}  |  **CoC:** {'✅' if st.session_state.coc_image_bytes else '❌ placeholder'}")
        if st.button("🖨️  Generate COA PDF", type="primary", use_container_width=True):
            with st.spinner("Generating PDF..."):
                data = {k: (str(v) if isinstance(v, date) else v) for k, v in {
                    "elap_number": st.session_state.elap_number, "lab_phone_display": st.session_state.lab_phone_display,
                    "report_date": st.session_state.report_date, "work_order": st.session_state.work_order,
                    "total_page_count": st.session_state.total_page_count,
                    "client_contact": st.session_state.client_contact, "client_company": st.session_state.client_company,
                    "project_name": st.session_state.project_name, "project_number": st.session_state.project_number,
                    "num_samples_text": st.session_state.num_samples_text, "date_received_text": st.session_state.date_received_text,
                    "approver_name": st.session_state.approver_name, "approver_title": st.session_state.approver_title,
                    "approval_date": st.session_state.approval_date,
                    "qc_met": st.session_state.qc_met, "method_blank_corrected": st.session_state.method_blank_corrected,
                    "case_narrative_custom": st.session_state.case_narrative_custom,
                    "samples": st.session_state.samples, "mb_batches": st.session_state.mb_batches, "lcs_batches": st.session_state.lcs_batches,
                    "receipt": st.session_state.receipt, "login_summary": st.session_state.login_summary,
                }.items()}
                builder = KelpCOABuilder(data, st.session_state.logo_bytes, st.session_state.signature_bytes, st.session_state.coc_image_bytes)
                pdf_bytes = builder.build()
            st.success(f"✅ COA generated — {len(pdf_bytes):,} bytes")
            wo = st.session_state.work_order or "DRAFT"
            fn = f"KELP_COA_{wo}_{date.today().strftime('%Y%m%d')}.pdf"
            st.download_button(f"⬇️ Download {fn}", pdf_bytes, fn, "application/pdf", use_container_width=True)
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px"></iframe>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
