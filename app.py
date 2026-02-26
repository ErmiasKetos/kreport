"""
KELP COA Generator — Streamlit + ReportLab (fixed)
=================================================
Fixes included:
1) NO stylesheet alias collisions (use unique style names: kelp_*).
2) Tables render page-wide (Frame uses doc.width/doc.height + zero paddings).
3) Two-pass page count footer "Page X of Y" via custom Canvas.
"""

import io
from datetime import datetime, date

import streamlit as st

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.pdfgen import canvas as rl_canvas


# ──────────────────────────────────────────────────────────────────────────────
# BRAND / COLORS
# ──────────────────────────────────────────────────────────────────────────────

BRAND = HexColor("#005F86")   # KETOS blue-teal
BORDER = HexColor("#A0AEC0")  # cool gray
ROWALT = HexColor("#F0F4F8")
TEALLT = HexColor("#E6F4F9")
DARK = HexColor("#2D3748")
BLK = HexColor("#1A202C")
WHT = HexColor("#FFFFFF")

PW, PH = letter
MG = 0.6 * inch
CW = PW - 2 * MG  # content width if you want to use it outside doc.width


# ──────────────────────────────────────────────────────────────────────────────
# STYLES (FIXED: no "h1"/"h2" alias collisions)
# ──────────────────────────────────────────────────────────────────────────────

def make_styles():
    ss = getSampleStyleSheet()

    def add(name: str, parent: str, **kw):
        # Use unique names only. Do NOT use h1/h2/b9 etc. because ReportLab sample
        # stylesheet already has aliases like "h1".
        ss.add(ParagraphStyle(name=name, parent=ss[parent], **kw))

    add("kelp_h1", "Heading1",
        fontName="Helvetica-Bold", fontSize=16, leading=18,
        textColor=BRAND, spaceAfter=8)

    add("kelp_h2", "Heading2",
        fontName="Helvetica-Bold", fontSize=12, leading=14,
        textColor=BRAND, spaceBefore=6, spaceAfter=4)

    add("kelp_b10", "BodyText",
        fontName="Helvetica", fontSize=10, leading=12,
        textColor=BLK)

    add("kelp_b9", "BodyText",
        fontName="Helvetica", fontSize=9, leading=11,
        textColor=BLK)

    add("kelp_b8", "BodyText",
        fontName="Helvetica", fontSize=8, leading=10,
        textColor=BLK)

    add("kelp_bb10", "BodyText",
        fontName="Helvetica-Bold", fontSize=10, leading=12,
        textColor=BLK)

    add("kelp_bb9", "BodyText",
        fontName="Helvetica-Bold", fontSize=9, leading=11,
        textColor=BLK)

    add("kelp_bb8", "BodyText",
        fontName="Helvetica-Bold", fontSize=8, leading=10,
        textColor=BLK)

    return ss


ST = make_styles()


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def safe(v, default=""):
    return v if v not in (None, "") else default

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

def img_from_bytes(b, width=None, height=None):
    bio = io.BytesIO(b)
    im = Image(bio)
    if width is not None:
        im.drawWidth = width
    if height is not None:
        im.drawHeight = height
    return im


# ──────────────────────────────────────────────────────────────────────────────
# PDF GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

class COAGenerator:
    def __init__(self, data: dict, logo_bytes: bytes | None = None, coc_pdf_bytes: bytes | None = None):
        self.d = data
        self.logo_bytes = logo_bytes
        self.coc_pdf_bytes = coc_pdf_bytes

    # Header/Footer
    def _draw_header(self, c: rl_canvas.Canvas):
        c.setFillColor(BLK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MG, PH - 0.35 * inch, "KETOS Environmental Laboratory Services (KELP)")
        c.setFont("Helvetica", 8)
        c.drawRightString(PW - MG, PH - 0.35 * inch, f"Work Order: {safe(self.d.get('work_order',''))}")

        c.setStrokeColor(BORDER)
        c.setLineWidth(0.6)
        c.line(MG, PH - 0.42 * inch, PW - MG, PH - 0.42 * inch)

    def _draw_footer(self, c: rl_canvas.Canvas, pg: int, total: int):
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.6)
        c.line(MG, 0.45 * inch, PW - MG, 0.45 * inch)

        c.setFont("Helvetica", 7.5)
        c.setFillColor(DARK)
        c.drawString(MG, 0.30 * inch, "This report shall not be reproduced except in full, without written approval of KELP.")
        c.drawRightString(PW - MG, 0.30 * inch, f"Page {pg} of {total}")

    # Table helper
    def _tbl(self, headers, rows, col_widths, result_col=None, repeat=True):
        data = [headers] + rows
        t = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1 if repeat else 0)
        style = [
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHT),
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("FONTSIZE", (0, 1), (-1, -1), 8.0),
            ("FONT", (0, 1), (-1, -1), "Helvetica"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
        # alternate shading
        for r in range(1, len(data)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), ROWALT))
        if result_col is not None:
            style.append(("FONT", (result_col, 1), (result_col, -1), "Helvetica-Bold"))
        t.setStyle(TableStyle(style))
        return t

    # Sections
    def _logo_bar(self, doc_width: float):
        logo_cell = ""
        if self.logo_bytes:
            try:
                logo_cell = img_from_bytes(self.logo_bytes, width=1.6 * inch, height=0.55 * inch)
            except Exception:
                logo_cell = ""

        addr = Paragraph(
            "<b>KETOS Environmental Laboratory Services (KELP)</b><br/>"
            "Sunnyvale, CA • ISO/IEC 17025 Aligned • CA ELAP / NELAP Path<br/>"
            "support@ketos.co • ketos.co",
            ST["kelp_b9"],
        )
        bar = Table([[logo_cell, addr]], colWidths=[doc_width * 0.45, doc_width * 0.55], hAlign="LEFT")
        bar.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return bar

    def _case_info_table(self, doc_width: float):
        d = self.d
        data = [
            [Paragraph("<b>Client</b>", ST["kelp_bb9"]), safe(d.get("client_company", "")),
             Paragraph("<b>Report Date</b>", ST["kelp_bb9"]), fmt_date(d.get("report_date", ""))],
            [Paragraph("<b>Client Contact</b>", ST["kelp_bb9"]), safe(d.get("client_contact", "")),
             Paragraph("<b>Date Received</b>", ST["kelp_bb9"]), safe(d.get("date_received_text", ""))],
            [Paragraph("<b>Project</b>", ST["kelp_bb9"]), safe(d.get("project_name", "")),
             Paragraph("<b>Matrix</b>", ST["kelp_bb9"]), safe(d.get("matrix", ""))],
            [Paragraph("<b>Work Order</b>", ST["kelp_bb9"]), safe(d.get("work_order", "")),
             Paragraph("<b>Sampling Date</b>", ST["kelp_bb9"]), safe(d.get("sampling_date_text", ""))],
        ]
        # keep same structure, but ensure final col fills remainder
        cw = [1.3 * inch, 2.2 * inch, 1.1 * inch, max(1.0, doc_width - (1.3 + 2.2 + 1.1) * inch)]
        t = Table(data, colWidths=cw, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    def _cover_letter(self, doc_width: float):
        d = self.d
        s = []
        s.append(self._logo_bar(doc_width))
        s.append(Spacer(1, 12))
        s.append(Paragraph("Certificate of Analysis (COA)", ST["kelp_h1"]))
        s.append(self._case_info_table(doc_width))
        s.append(Spacer(1, 12))

        intro = (
            "KETOS Environmental Laboratory Services (KELP) is pleased to provide the analytical results "
            "for the samples submitted under this work order. All analyses were performed in accordance with "
            "applicable EPA methods and internal quality assurance procedures aligned to ISO/IEC 17025 principles. "
            "Results are reported with method detection limits (MDLs) and practical quantitation limits (PQLs) "
            "as applicable."
        )
        s.append(Paragraph(intro, ST["kelp_b10"]))
        s.append(Spacer(1, 10))

        sign = (
            f"<b>Prepared by:</b> {safe(d.get('prepared_by',''))}<br/>"
            f"<b>Title:</b> {safe(d.get('prepared_by_title',''))}<br/>"
            f"<b>Reviewed by:</b> {safe(d.get('reviewed_by',''))}<br/>"
            f"<b>Title:</b> {safe(d.get('reviewed_by_title',''))}"
        )
        s.append(Paragraph(sign, ST["kelp_b10"]))
        s.append(Spacer(1, 16))

        s.append(Paragraph("Notes", ST["kelp_h2"]))
        notes = d.get("notes", [
            "Sample results apply only to the items tested.",
            "This report shall not be reproduced except in full, without written approval.",
            "Unless otherwise specified, results are reported on an as-received basis.",
        ])
        for n in notes:
            s.append(Paragraph(f"• {n}", ST["kelp_b10"]))

        return s

    def _case_narrative(self):
        d = self.d
        s = []
        s.append(Paragraph("Case Narrative", ST["kelp_h1"]))
        text = d.get("case_narrative", "") or (
            "Samples were received in good condition unless otherwise noted. "
            "Holding times were met for all analyses performed. Quality control criteria "
            "were reviewed and found acceptable. Any deviations are documented in the QA/QC "
            "section of this report."
        )
        for para in text.split("\n\n"):
            p = para.strip()
            if p:
                s.append(Paragraph(p, ST["kelp_b10"]))
                s.append(Spacer(1, 8))
        return s

    def _sample_result_summary(self, doc_width: float):
        d = self.d
        s = []
        s.append(Paragraph("Sample Result Summary", ST["kelp_h1"]))

        hdrs = ["Client Sample ID", "Lab Sample ID", "Matrix", "Collection Date/Time", "Receipt Temp", "Status"]
        cw = [doc_width * 0.20, doc_width * 0.14, doc_width * 0.14, doc_width * 0.22, doc_width * 0.12, doc_width * 0.18]
        rows = []
        for samp in d.get("samples", []):
            rows.append([
                samp.get("client_sample_id", ""),
                samp.get("lab_sample_id", ""),
                samp.get("matrix", d.get("matrix", "")),
                samp.get("collection_dt", ""),
                samp.get("receipt_temp", ""),
                samp.get("status", ""),
            ])
        s.append(self._tbl(hdrs, rows, cw))
        s.append(Spacer(1, 10))
        return s

    def _analytical_results(self, doc_width: float):
        d = self.d
        s = []
        s.append(Paragraph("Analytical Results", ST["kelp_h1"]))
        s.append(Paragraph(
            "Detailed analytical results are presented below by sample. "
            "Values reported as “ND” indicate non-detects at the stated MDL.",
            ST["kelp_b10"]
        ))
        s.append(Spacer(1, 10))

        for samp in d.get("samples", []):
            csid = samp.get("client_sample_id", "")
            lsid = samp.get("lab_sample_id", "")

            right_style = ParagraphStyle("kelp_right", parent=ST["kelp_bb8"], alignment=TA_RIGHT)
            sh = Table([[
                Paragraph(f"<b>Sample:</b> {csid}", ST["kelp_bb8"]),
                Paragraph(f"<b>Lab ID:</b> {lsid}", right_style),
            ]], colWidths=[doc_width * 0.5, doc_width * 0.5], hAlign="LEFT")
            sh.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TEALLT),
                ("BOX", (0, 0), (-1, 0), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            s.append(sh)
            s.append(Spacer(1, 2))

            hdrs = ["Parameters", "Method", "DF", "MDL", "PQL", "Results", "Units"]
            # Keep your original relative structure, but base it on doc_width
            # and make sure it sums to doc_width.
            fixed = [1.0 * inch, 0.45 * inch, 0.75 * inch, 0.75 * inch, 0.85 * inch, 0.7 * inch]
            param_w = max(1.0, doc_width - sum(fixed))
            cw = [param_w] + fixed

            rows = []
            for r in samp.get("results", []):
                rows.append([
                    r.get("parameter", ""),
                    r.get("method", ""),
                    r.get("df", "1"),
                    r.get("mdl", ""),
                    r.get("pql", ""),
                    r.get("result", ""),
                    r.get("unit", "mg/L"),
                ])

            s.append(self._tbl(hdrs, rows, cw, result_col=5))
            s.append(Spacer(1, 10))

        return s

    def _qualifiers(self, doc_width: float):
        s = []
        s.append(Paragraph("Qualifiers and Definitions", ST["kelp_h1"]))
        quals = self.d.get("qualifiers") or [
            ("ND", "Not detected at or above the method detection limit (MDL)."),
            ("PQL", "Practical quantitation limit."),
            ("J", "Estimated value; reported between the MDL and PQL or affected by QC."),
            ("U", "Analyte not detected; reported at the MDL."),
        ]
        hdrs = ["Qualifier", "Definition"]
        cw = [1.0 * inch, max(1.0, doc_width - 1.0 * inch)]
        rows = [[q, d] for q, d in quals]
        s.append(self._tbl(hdrs, rows, cw, repeat=False))
        return s

    # Build
    def build(self) -> bytes:
        buf = io.BytesIO()

        doc = BaseDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=MG,
            rightMargin=MG,
            topMargin=0.5 * inch,
            bottomMargin=0.55 * inch,
            title=f"KELP COA — WO {safe(self.d.get('work_order',''))}",
        )

        # ✅ CRITICAL FIX: frame uses doc geometry and NO paddings (no “hidden shrink”)
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="main",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

        # Two-pass page count via canvas
        generator = self

        class PageCounterCanvas(rl_canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                self._saved_page_states.append(dict(self.__dict__))
                total_pages = len(self._saved_page_states)

                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    generator._draw_header(self)
                    generator._draw_footer(self, self._pageNumber, total_pages)
                    super().showPage()

                super().save()

        doc.addPageTemplates([
            PageTemplate(id="coa", frames=[frame])
        ])

        # Build story (note: use doc.width everywhere for tables)
        w = doc.width
        story = []
        story.extend(self._cover_letter(w))
        story.append(PageBreak())
        story.extend(self._case_narrative())
        story.append(PageBreak())
        story.extend(self._sample_result_summary(w))
        story.append(PageBreak())
        story.extend(self._analytical_results(w))
        story.append(PageBreak())
        story.extend(self._qualifiers(w))

        doc.build(story, canvasmaker=PageCounterCanvas)
        return buf.getvalue()


# ──────────────────────────────────────────────────────────────────────────────
# STREAMLIT APP
# ──────────────────────────────────────────────────────────────────────────────

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
        "case_narrative": "",
        "notes": [],
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
                ],
            }
        ],
        "qualifiers": [],
    }


def main():
    st.set_page_config(page_title="KELP COA Generator", layout="wide")
    st.title("KELP COA PDF Generator")

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

        st.divider()
        logo = st.file_uploader("Upload Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

    st.caption("This demo keeps a simple data payload. In your production app, you’ll likely edit samples/results via an editable grid.")

    if st.button("Generate COA PDF"):
        logo_bytes = logo.read() if logo else None
        pdf_bytes = COAGenerator(data, logo_bytes=logo_bytes).build()

        st.success("COA generated.")
        st.download_button(
            "Download COA PDF",
            data=pdf_bytes,
            file_name=f"KELP_COA_{data['work_order']}.pdf",
            mime="application/pdf",
        )


if __name__ == "__main__":
    main()
