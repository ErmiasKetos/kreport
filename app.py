"""
KELP COA Generator v3 — Production Streamlit Application
==========================================================
KETOS Environmental Lab Platform
Certificate of Analysis PDF Generator

Design philosophy: Clean, professional environmental lab COA following
industry best practices from Pace Analytical, Eurofins, and TestAmerica.
Uses ReportLab Platypus for automatic layout, wrapping, and pagination.

Pages:
  1.  Cover Letter
  2.  Case Narrative
  3.  Sample Result Summary
  4+. Analytical Results (detail per sample, grouped by method)
  5.  Quality Control Data — Method Blanks
  6.  Quality Control Data — LCS/LCSD
  7.  Qualifiers and Definitions
  8.  Sample Receipt Checklist
  9.  Login Summary / Sample Cross-Reference
  10. Chain of Custody (uploaded scan)
"""

import streamlit as st
import io, os, base64, copy
from datetime import datetime, date, time as time_type

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY

from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas as pdfcanvas


# ─── BRAND / COLORS ───────────────────────────────────────────────────────────

BRAND    = HexColor("#005F86")   # KETOS blue-teal
BORDER   = HexColor("#A0AEC0")   # cool gray
LIGHT    = HexColor("#F7FAFC")   # near white
MID      = HexColor("#EDF2F7")   # light gray
DARK     = HexColor("#2D3748")   # dark gray
ROWALT   = HexColor("#F0F4F8")
ACCENT   = HexColor("#EBF5FB")
BLK      = HexColor("#1A202C")
WHT      = HexColor("#FFFFFF")
TEALLT   = HexColor("#E6F4F9")

PW, PH = letter
MG = 0.6 * inch
CW = PW - 2 * MG  # usable content width ≈ 6.8"


# ─── STYLES ──────────────────────────────────────────────────────────────────

def make_styles():
    ss = getSampleStyleSheet()

    def P(name, parent, **kw):
        ss.add(ParagraphStyle(name=name, parent=ss[parent], **kw))

    P('h1', 'Heading1', fontName='Helvetica-Bold', fontSize=16, leading=18,
      textColor=BRAND, spaceAfter=8)
    P('h2', 'Heading2', fontName='Helvetica-Bold', fontSize=12, leading=14,
      textColor=BRAND, spaceBefore=6, spaceAfter=4)
    P('b10', 'BodyText', fontName='Helvetica', fontSize=10, leading=12,
      textColor=BLK)
    P('b9', 'BodyText', fontName='Helvetica', fontSize=9, leading=11,
      textColor=BLK)
    P('b8', 'BodyText', fontName='Helvetica', fontSize=8, leading=10,
      textColor=BLK)
    P('bb10', 'BodyText', fontName='Helvetica-Bold', fontSize=10, leading=12,
      textColor=BLK)
    P('bb9', 'BodyText', fontName='Helvetica-Bold', fontSize=9, leading=11,
      textColor=BLK)
    P('bb8', 'BodyText', fontName='Helvetica-Bold', fontSize=8, leading=10,
      textColor=BLK)
    P('small', 'BodyText', fontName='Helvetica', fontSize=7.5, leading=9,
      textColor=BLK)
    P('small_ital', 'BodyText', fontName='Helvetica-Oblique', fontSize=7.5,
      leading=9, textColor=BLK)
    P('note', 'BodyText', fontName='Helvetica', fontSize=8, leading=10,
      textColor=DARK, leftIndent=10, spaceBefore=2, spaceAfter=2)

    return ss

ST = make_styles()


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def fmt_date(x):
    if isinstance(x, (datetime, date)):
        return x.strftime("%Y-%m-%d")
    return str(x) if x else ""

def fmt_dt(x):
    if isinstance(x, datetime):
        return x.strftime("%Y-%m-%d %H:%M")
    if isinstance(x, date):
        return x.strftime("%Y-%m-%d")
    return str(x) if x else ""

def safe(v, default=""):
    return v if v not in (None, "") else default

def img_from_bytes(b, width=None, height=None):
    bio = io.BytesIO(b)
    im = Image(bio)
    if width:
        im.drawWidth = width
    if height:
        im.drawHeight = height
    return im

def as_par(v, style='b9'):
    return Paragraph(str(v), ST[style])


# ─── MAIN PDF GENERATOR ──────────────────────────────────────────────────────

class COAGenerator:
    def __init__(self, data: dict, logo_bytes: bytes | None = None,
                 coc_pdf_bytes: bytes | None = None):
        self.d = data
        self.logo_bytes = logo_bytes
        self.coc_pdf_bytes = coc_pdf_bytes
        self._pg = [0]
        self._total = [0]

    # ── Header / Footer ───────────────────────────────────────────────────────

    def _draw_header(self, c: pdfcanvas.Canvas):
        c.setFillColor(BLK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MG, PH - 0.35*inch, "KETOS Environmental Laboratory Services (KELP)")
        c.setFont("Helvetica", 8)
        c.drawRightString(PW - MG, PH - 0.35*inch, f"Work Order: {safe(self.d.get('work_order',''))}")

        c.setStrokeColor(BORDER)
        c.setLineWidth(0.6)
        c.line(MG, PH - 0.42*inch, PW - MG, PH - 0.42*inch)

    def _draw_footer(self, c: pdfcanvas.Canvas, pg: int, total: int):
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.6)
        c.line(MG, 0.45*inch, PW - MG, 0.45*inch)

        c.setFont("Helvetica", 7.5)
        c.setFillColor(DARK)
        c.drawString(MG, 0.30*inch, "This report shall not be reproduced except in full, without written approval of KELP.")
        c.drawRightString(PW - MG, 0.30*inch, f"Page {pg} of {total}")

    # ── Table Factory ─────────────────────────────────────────────────────────

    def _tbl(self, headers, rows, col_widths, result_col=None, repeat=True):
        data = [headers] + rows
        t = Table(data, colWidths=col_widths, hAlign='LEFT', repeatRows=1 if repeat else 0)
        style = [
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8.5),
            ('TEXTCOLOR', (0,0), (-1,0), WHT),
            ('BACKGROUND', (0,0), (-1,0), BRAND),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.4, BORDER),
            ('FONTSIZE', (0,1), (-1,-1), 8.0),
            ('FONT', (0,1), (-1,-1), 'Helvetica'),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]
        # alternate row shading
        for r in range(1, len(data)):
            if r % 2 == 0:
                style.append(('BACKGROUND', (0,r), (-1,r), ROWALT))
        if result_col is not None:
            style.append(('FONT', (result_col,1), (result_col,-1), 'Helvetica-Bold'))
        t.setStyle(TableStyle(style))
        return t

    # ── Sections ──────────────────────────────────────────────────────────────

    def _logo_bar(self):
        logo = ""
        if self.logo_bytes:
            try:
                logo = img_from_bytes(self.logo_bytes, width=1.6*inch, height=0.55*inch)
            except Exception:
                logo = ""
        addr = Paragraph(
            "<b>KETOS Environmental Laboratory Services (KELP)</b><br/>"
            "Sunnyvale, CA • ISO/IEC 17025 Aligned • CA ELAP / NELAP Path<br/>"
            "support@ketos.co • ketos.co",
            ST['b9']
        )
        bar = Table([[logo, addr]], colWidths=[CW*0.45, CW*0.55], hAlign='LEFT')
        bar.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),
            ('BOTTOMPADDING',(0,0),(-1,-1),0),
        ]))
        return bar

    def _case_info_table(self):
        d = self.d
        data = [
            [Paragraph("<b>Client</b>", ST['bb9']), safe(d.get('client_company','')),
             Paragraph("<b>Report Date</b>", ST['bb9']), fmt_date(d.get('report_date',''))],
            [Paragraph("<b>Client Contact</b>", ST['bb9']), safe(d.get('client_contact','')),
             Paragraph("<b>Date Received</b>", ST['bb9']), safe(d.get('date_received_text',''))],
            [Paragraph("<b>Project</b>", ST['bb9']), safe(d.get('project_name','')),
             Paragraph("<b>Matrix</b>", ST['bb9']), safe(d.get('matrix',''))],
            [Paragraph("<b>Work Order</b>", ST['bb9']), safe(d.get('work_order','')),
             Paragraph("<b>Sampling Date</b>", ST['bb9']), safe(d.get('sampling_date_text',''))],
        ]
        cw = [1.3*inch, 2.2*inch, 1.1*inch, CW-4.6*inch]
        t = Table(data, colWidths=cw, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),0.4,BORDER),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('BACKGROUND',(0,0),(-1,-1),WHT),
            ('LEFTPADDING',(0,0),(-1,-1),4),
            ('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),3),
            ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ]))
        return t

    def _cover_letter(self):
        d = self.d
        s = []
        s.append(self._logo_bar())
        s.append(Spacer(1, 12))
        s.append(Paragraph("Certificate of Analysis (COA)", ST['h1']))
        s.append(self._case_info_table())
        s.append(Spacer(1, 12))

        intro = (
            "KETOS Environmental Laboratory Services (KELP) is pleased to provide the analytical results "
            "for the samples submitted under this work order. All analyses were performed in accordance with "
            "applicable EPA methods and internal quality assurance procedures aligned to ISO/IEC 17025 principles. "
            "Results are reported with method detection limits (MDLs) and practical quantitation limits (PQLs) "
            "as applicable."
        )
        s.append(Paragraph(intro, ST['b10']))
        s.append(Spacer(1, 10))

        sign = f"""
        <b>Prepared by:</b> {safe(d.get('prepared_by',''))}<br/>
        <b>Title:</b> {safe(d.get('prepared_by_title',''))}<br/>
        <b>Reviewed by:</b> {safe(d.get('reviewed_by',''))}<br/>
        <b>Title:</b> {safe(d.get('reviewed_by_title',''))}
        """
        s.append(Paragraph(sign, ST['b10']))
        s.append(Spacer(1, 16))

        s.append(Paragraph("<b>Notes</b>", ST['h2']))
        notes = d.get('notes', [
            "Sample results apply only to the items tested.",
            "This report shall not be reproduced except in full, without written approval.",
            "Unless otherwise specified, results are reported on an as-received basis."
        ])
        for n in notes:
            s.append(Paragraph(f"• {n}", ST['b10']))

        return s

    def _case_narrative(self):
        d = self.d
        s = []
        s.append(Paragraph("Case Narrative", ST['h1']))
        text = d.get('case_narrative','')
        if not text:
            text = (
                "Samples were received in good condition unless otherwise noted. "
                "Holding times were met for all analyses performed. Quality control criteria "
                "were reviewed and found acceptable. Any deviations are documented in the QA/QC "
                "section of this report."
            )
        for para in text.split("\n\n"):
            s.append(Paragraph(para.strip(), ST['b10']))
            s.append(Spacer(1, 8))
        return s

    def _sample_result_summary(self):
        d = self.d
        s = []
        s.append(Paragraph("Sample Result Summary", ST['h1']))
        hdrs = ["Client Sample ID", "Lab Sample ID", "Matrix", "Collection Date/Time", "Receipt Temp", "Status"]
        cw = [CW*0.20, CW*0.14, CW*0.14, CW*0.22, CW*0.12, CW*0.18]
        rows = []
        for samp in d.get('samples', []):
            rows.append([
                samp.get('client_sample_id',''),
                samp.get('lab_sample_id',''),
                samp.get('matrix', d.get('matrix','')),
                samp.get('collection_dt',''),
                samp.get('receipt_temp',''),
                samp.get('status',''),
            ])
        s.append(self._tbl(hdrs, rows, cw))
        s.append(Spacer(1, 10))
        return s

    def _analytical_results(self):
        d = self.d
        s = []
        s.append(Paragraph("Analytical Results", ST['h1']))
        s.append(Paragraph(
            "Detailed analytical results are presented below by sample. "
            "Values reported as “ND” indicate non-detects at the stated MDL.",
            ST['b10']
        ))
        s.append(Spacer(1, 10))

        for samp in d.get('samples', []):
            csid = samp.get('client_sample_id','')
            lsid = samp.get('lab_sample_id','')
            sh = Table([[
                Paragraph(f'<b>Sample:</b> {csid}', ST['bb8']),
                Paragraph(f'<b>Lab ID:</b> {lsid}', ParagraphStyle('r', parent=ST['bb8'], alignment=TA_RIGHT)),
            ]], colWidths=[CW*0.5, CW*0.5], hAlign='LEFT')
            sh.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0), TEALLT),
                ('BOX',(0,0),(-1,0), 0.4, BORDER),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
                ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ]))
            s.append(sh)
            s.append(Spacer(1, 2))

            hdrs = ["Parameters", "Method", "DF", "MDL", "PQL", "Results", "Units"]
            cw = [CW-4.5*inch, 1.0*inch, 0.45*inch, 0.75*inch, 0.75*inch, 0.85*inch, 0.7*inch]
            rows = [[r.get('parameter',''), r.get('method',''), r.get('df','1'),
                      r.get('mdl',''), r.get('pql',''), r.get('result',''), r.get('unit','mg/L')]
                     for r in samp.get('results',[])]
            s.append(self._tbl(hdrs, rows, cw, result_col=5))
            s.append(Spacer(1, 10))
        return s

    def _qc_blanks(self):
        d = self.d
        s = []
        s.append(Paragraph("Quality Control Data — Method Blanks", ST['h1']))
        rows = d.get('qc_blanks', [])
        if not rows:
            s.append(Paragraph("No blank data provided.", ST['b10']))
            return s
        hdrs = ["QC ID", "Method", "Analyte", "Result", "MDL", "Units", "Pass/Fail"]
        cw = [CW*0.14, CW*0.12, CW*0.30, CW*0.12, CW*0.10, CW*0.10, CW*0.12]
        body = [[r.get('qc_id',''), r.get('method',''), r.get('analyte',''),
                 r.get('result',''), r.get('mdl',''), r.get('unit',''), r.get('status','')]
                for r in rows]
        s.append(self._tbl(hdrs, body, cw))
        return s

    def _qc_lcs(self):
        d = self.d
        s = []
        s.append(Paragraph("Quality Control Data — LCS / LCSD", ST['h1']))
        rows = d.get('qc_lcs', [])
        if not rows:
            s.append(Paragraph("No LCS/LCSD data provided.", ST['b10']))
            return s
        hdrs = ["QC ID", "Method", "Analyte", "%Rec", "Limits", "RPD", "RPD Limits", "Pass/Fail"]
        cw = [CW*0.12, CW*0.12, CW*0.26, CW*0.10, CW*0.12, CW*0.10, CW*0.10, CW*0.08]
        body = [[r.get('qc_id',''), r.get('method',''), r.get('analyte',''),
                 r.get('rec',''), r.get('rec_limits',''), r.get('rpd',''),
                 r.get('rpd_limits',''), r.get('status','')]
                for r in rows]
        s.append(self._tbl(hdrs, body, cw))
        return s

    def _qualifiers(self):
        s = []
        s.append(Paragraph("Qualifiers and Definitions", ST['h1']))
        quals = self.d.get('qualifiers', [
            ("ND", "Not detected at or above the method detection limit (MDL)."),
            ("PQL", "Practical quantitation limit."),
            ("J", "Estimated value; reported between the MDL and PQL or affected by QC."),
            ("U", "Analyte not detected; reported at the MDL."),
        ])
        hdrs = ["Qualifier", "Definition"]
        cw = [1.0*inch, CW-1.0*inch]
        rows = [[q, d] for q, d in quals]
        s.append(self._tbl(hdrs, rows, cw, repeat=False))
        return s

    def _receipt_checklist(self):
        s = []
        s.append(Paragraph("Sample Receipt Checklist", ST['h1']))
        items = self.d.get('receipt_checklist', [
            ("Containers intact / no leaks", "Yes"),
            ("Proper preservation", "Yes"),
            ("Samples labeled", "Yes"),
            ("Cooler temperature within range", "Yes"),
            ("COC complete", "Yes"),
        ])
        hdrs = ["Checklist Item", "Observation"]
        cw = [CW*0.75, CW*0.25]
        rows = [[a, b] for a, b in items]
        s.append(self._tbl(hdrs, rows, cw, repeat=False))
        return s

    def _login_summary(self):
        s = []
        s.append(Paragraph("Login Summary / Sample Cross-Reference", ST['h1']))
        rows = self.d.get('login_summary', [])
        if not rows:
            s.append(Paragraph("No login summary data provided.", ST['b10']))
            return s
        hdrs = ["Client Sample ID", "Lab Sample ID", "Matrix", "Containers", "Preservation", "Comments"]
        cw = [CW*0.18, CW*0.14, CW*0.14, CW*0.12, CW*0.16, CW*0.26]
        body = [[r.get('client_sample_id',''), r.get('lab_sample_id',''),
                 r.get('matrix',''), r.get('containers',''),
                 r.get('preservation',''), r.get('comments','')]
                for r in rows]
        s.append(self._tbl(hdrs, body, cw))
        return s

    def _coc_appendix(self):
        s = []
        s.append(Paragraph("Chain of Custody (Appendix)", ST['h1']))
        if not self.coc_pdf_bytes:
            s.append(Paragraph("No COC file uploaded.", ST['b10']))
            return s
        s.append(Paragraph(
            "The Chain of Custody is provided as an attachment in the uploaded PDF. "
            "Streamlit Cloud builds this report PDF; COC merging is typically handled downstream "
            "or via external PDF merge logic (PyPDF2).",
            ST['b10']
        ))
        return s

    # ── Build PDF ─────────────────────────────────────────────────────────────

    def build(self) -> bytes:
        buf = io.BytesIO()

        doc = BaseDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=MG,
            rightMargin=MG,
            topMargin=0.5*inch,
            bottomMargin=0.55*inch,
            title=f"KELP COA — WO {self.d.get('work_order','')}"
        )

        # ✅ FIX: Use doc geometry (not hard-coded MG/CW) + remove frame padding.
        # This prevents Platypus from laying tables into a smaller “inner box”
        # which makes them look compressed.
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='main',
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

        pg = self._pg
        total = self._total

        def on_page(c, doc_):
            pg[0] += 1
            c.saveState()
            self._draw_header(c)
            self._draw_footer(c, pg[0], total[0])
            c.restoreState()

        def on_page_count(c, doc_):
            pass

        doc.addPageTemplates([
            PageTemplate(id='coa', frames=[frame], onPage=on_page, onPageEnd=on_page_count)
        ])

        story = []
        story.extend(self._cover_letter())
        story.append(PageBreak())
        story.extend(self._case_narrative())
        story.append(PageBreak())
        story.extend(self._sample_result_summary())
        story.append(PageBreak())
        story.extend(self._analytical_results())
        story.append(PageBreak())
        story.extend(self._qc_blanks())
        story.append(PageBreak())
        story.extend(self._qc_lcs())
        story.append(PageBreak())
        story.extend(self._qualifiers())
        story.append(PageBreak())
        story.extend(self._receipt_checklist())
        story.append(PageBreak())
        story.extend(self._login_summary())
        story.append(PageBreak())
        story.extend(self._coc_appendix())

        # two-pass total pages
        self._pg[0] = 0
        self._total[0] = 0

        class PageCounter(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._page_states = []

            def showPage(self):
                self._page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                self._page_states.append(dict(self.__dict__))
                num_pages = len(self._page_states)
                total[0] = num_pages
                for state in self._page_states:
                    self.__dict__.update(state)
                    self._draw_header(self)
                    self._draw_footer(self, self._pageNumber, num_pages)
                    super().showPage()
                super().save()

        doc.build(story, canvasmaker=PageCounter)
        return buf.getvalue()


# ─── STREAMLIT APP ───────────────────────────────────────────────────────────

def default_data():
    return {
        "work_order": "WO-000001",
        "client_company": "Example Client, Inc.",
        "client_contact": "John Doe",
        "project_name": "Drinking Water Compliance",
        "matrix": "Water",
        "report_date": date.today(),
        "date_received_text": fmt_date(date.today()),
        "sampling_date_text": fmt_date(date.today()),
        "prepared_by": "KELP Analyst",
        "prepared_by_title": "Laboratory Analyst",
        "reviewed_by": "KELP QA",
        "reviewed_by_title": "QA Manager",
        "samples": [
            {
                "client_sample_id": "SAMPLE-1",
                "lab_sample_id": "KELP-0001",
                "matrix": "Water",
                "collection_dt": fmt_dt(datetime.now()),
                "receipt_temp": "4°C",
                "status": "Received",
                "results": [
                    {"parameter": "Chromium (Total)", "method": "EPA 200.8", "df": "1", "mdl": "0.5", "pql": "1.0", "result": "ND", "unit": "µg/L"},
                    {"parameter": "Lead", "method": "EPA 200.8", "df": "1", "mdl": "0.2", "pql": "0.5", "result": "0.8", "unit": "µg/L"},
                ]
            }
        ],
        "qc_blanks": [],
        "qc_lcs": [],
        "qualifiers": [],
        "receipt_checklist": [],
        "login_summary": [],
        "case_narrative": "",
        "notes": []
    }

def main():
    st.set_page_config(page_title="KELP COA Generator", layout="wide")
    st.title("KELP COA PDF Generator")

    st.markdown("Fill in basic metadata and sample results, then generate a COA PDF.")

    data = default_data()

    with st.sidebar:
        st.header("Report Metadata")
        data["work_order"] = st.text_input("Work Order", data["work_order"])
        data["client_company"] = st.text_input("Client Company", data["client_company"])
        data["client_contact"] = st.text_input("Client Contact", data["client_contact"])
        data["project_name"] = st.text_input("Project Name", data["project_name"])
        data["matrix"] = st.text_input("Matrix", data["matrix"])
        data["prepared_by"] = st.text_input("Prepared By", data["prepared_by"])
        data["prepared_by_title"] = st.text_input("Prepared By Title", data["prepared_by_title"])
        data["reviewed_by"] = st.text_input("Reviewed By", data["reviewed_by"])
        data["reviewed_by_title"] = st.text_input("Reviewed By Title", data["reviewed_by_title"])

        logo = st.file_uploader("Upload Logo (PNG/JPG)", type=["png","jpg","jpeg"])
        coc = st.file_uploader("Upload COC PDF (optional)", type=["pdf"])

    # In a production app, you would create editable tables for samples/results.
    # This demo keeps a simple example payload.

    if st.button("Generate COA PDF"):
        logo_bytes = logo.read() if logo else None
        coc_bytes = coc.read() if coc else None
        pdf = COAGenerator(data, logo_bytes=logo_bytes, coc_pdf_bytes=coc_bytes).build()
        st.success("COA generated.")
        st.download_button(
            "Download COA PDF",
            data=pdf,
            file_name=f"KELP_COA_{data['work_order']}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
