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
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Table, TableStyle,
    Paragraph, Spacer, Image, PageBreak, Flowable
)
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

# ─── BRAND PALETTE ───────────────────────────────────────────────────────────
NAVY     = HexColor("#1F4E79")
TEAL     = HexColor("#3A9ABF")
DKGRAY   = HexColor("#4A5568")
MDGRAY   = HexColor("#718096")
LTGRAY   = HexColor("#E2E8F0")
VLGRAY   = HexColor("#F7FAFC")
BORDER   = HexColor("#CBD5E0")
HDRBLUE  = HexColor("#2C5F8A")
HDRFILL  = HexColor("#2C5F8A")
ROWALT   = HexColor("#F0F4F8")
ACCENT   = HexColor("#EBF5FB")
BLK      = HexColor("#1A202C")
WHT      = HexColor("#FFFFFF")
TEALLT   = HexColor("#E6F4F9")

PW, PH = letter
MG = 0.6 * inch
CW = PW - 2 * MG  # usable content width ≈ 6.8"


# ─── STYLES ──────────────────────────────────────────────────────────────────
def _s():
    """Build paragraph styles."""
    S = {}
    # Body text
    S['b9']  = ParagraphStyle('b9',  fontName='Helvetica',      fontSize=9,   leading=12, textColor=BLK)
    S['b8']  = ParagraphStyle('b8',  fontName='Helvetica',      fontSize=8,   leading=11, textColor=BLK)
    S['b7']  = ParagraphStyle('b7',  fontName='Helvetica',      fontSize=7,   leading=9.5,textColor=BLK)
    S['b6']  = ParagraphStyle('b6',  fontName='Helvetica',      fontSize=6.5, leading=8.5,textColor=BLK)
    # Bold
    S['bb9'] = ParagraphStyle('bb9', fontName='Helvetica-Bold',  fontSize=9,   leading=12, textColor=BLK)
    S['bb8'] = ParagraphStyle('bb8', fontName='Helvetica-Bold',  fontSize=8,   leading=11, textColor=BLK)
    S['bb7'] = ParagraphStyle('bb7', fontName='Helvetica-Bold',  fontSize=7,   leading=9.5,textColor=BLK)
    # Navy bold (labels)
    S['lbl'] = ParagraphStyle('lbl', fontName='Helvetica-Bold',  fontSize=8,   leading=11, textColor=NAVY)
    S['lbl7']= ParagraphStyle('lbl7',fontName='Helvetica-Bold',  fontSize=7,   leading=9,  textColor=NAVY)
    # Values
    S['val'] = ParagraphStyle('val', fontName='Helvetica',       fontSize=8,   leading=11, textColor=BLK)
    S['val7']= ParagraphStyle('val7',fontName='Helvetica',       fontSize=7,   leading=9,  textColor=BLK)
    # Titles
    S['title']= ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=13,  leading=16, textColor=NAVY, alignment=TA_CENTER)
    S['stitle']= ParagraphStyle('stitle',fontName='Helvetica-Bold',fontSize=11,leading=14, textColor=NAVY, alignment=TA_CENTER)
    S['sect'] = ParagraphStyle('sect',fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=NAVY)
    # Table header
    S['th']   = ParagraphStyle('th',  fontName='Helvetica-Bold', fontSize=6.5, leading=8.5,textColor=WHT, alignment=TA_CENTER)
    S['thl']  = ParagraphStyle('thl', fontName='Helvetica-Bold', fontSize=6.5, leading=8.5,textColor=WHT, alignment=TA_LEFT)
    # Table data
    S['td']   = ParagraphStyle('td',  fontName='Helvetica',      fontSize=7,   leading=9.5,textColor=BLK, alignment=TA_CENTER)
    S['tdl']  = ParagraphStyle('tdl', fontName='Helvetica',      fontSize=7,   leading=9.5,textColor=BLK, alignment=TA_LEFT)
    S['tdr']  = ParagraphStyle('tdr', fontName='Helvetica',      fontSize=7,   leading=9.5,textColor=BLK, alignment=TA_RIGHT)
    S['tdb']  = ParagraphStyle('tdb', fontName='Helvetica-Bold', fontSize=7,   leading=9.5,textColor=BLK, alignment=TA_CENTER)
    # Footer
    S['ft']   = ParagraphStyle('ft',  fontName='Helvetica',      fontSize=6.5, leading=8,  textColor=MDGRAY)
    S['ital'] = ParagraphStyle('ital',fontName='Helvetica-Oblique',fontSize=7, leading=9,  textColor=MDGRAY)
    # Qualifier
    S['qc']   = ParagraphStyle('qc', fontName='Helvetica-Bold',  fontSize=7.5, leading=10, textColor=NAVY)
    S['qd']   = ParagraphStyle('qd', fontName='Helvetica',       fontSize=7,   leading=9.5,textColor=BLK)
    return S

ST = _s()

# ─── LAB CONSTANTS ───────────────────────────────────────────────────────────
LAB = {
    "name": "KETOS Environmental Lab Services",
    "entity": "KETOS INC.",
    "addr": ["520 Mercury Dr", "Sunnyvale, California 94085"],
    "phone": "(408) 550-2162",
    "email": "info@ketoslab.com",
}

QUALIFIERS = [
    ("B",  "Analyte found in the associated method or preparation blank."),
    ("D",  "Surrogate not recoverable due to necessary dilution of the sample."),
    ("E",  "Reportable value outside calibration range but within instrument linear range. Consider estimated."),
    ("H",  "Recommended holding time for the analyte has been exceeded."),
    ("J",  "Value between MDL and PQL — reported concentration is estimated."),
    ("NA", "Not Analyzed."),
    ("N/A","Not Applicable."),
    ("ND", "Not Detected at or above the PQL/RL (or MDL if reported to the MDL)."),
    ("NR", "Not recoverable — native sample concentration &gt; 4× spike concentration added."),
    ("R",  "%RPD between duplicates exceeds laboratory control chart limits."),
    ("S",  "Spike recovery outside established method/laboratory control limits."),
    ("X",  "Pattern identification value within pattern range but atypical of standard pattern."),
]

DEFINITIONS = [
    ("<b>DF</b> — Dilution Factor applied to the reported data due to dilution of the sample aliquot."),
    ("<b>ND</b> — Not Detected at or above adjusted reporting limit."),
    ("<b>MDL</b> — Adjusted Method Detection Limit."),
    ("<b>PQL / RL / LOQ</b> — Practical Quantitation Limit / Reporting Limit. Laboratory-determined value 2–5× above MDL."),
    ("<b>LCS(D)</b> — Laboratory Control Sample (Duplicate)."),
    ("<b>MS(D)</b> — Matrix Spike (Duplicate)."),
    ("<b>RPD</b> — Relative Percent Difference."),
    ("<b>Accuracy / Bias (% Recovery)</b> — Closeness of agreement between an observed and accepted reference value."),
    ("<b>Blank (Method/Preparation Blank)</b> — Analyte-free matrix processed identically to samples; documents contamination from analytical process."),
    ("<b>Precision (%RPD)</b> — Agreement among replicate/duplicate measurements without regard to the known value."),
]

DISCLAIMER = "This report shall not be reproduced, except in full, without the written approval of KETOS INC."


# ─── HELPER FLOWABLES ────────────────────────────────────────────────────────
class HLine(Flowable):
    """Horizontal rule."""
    def __init__(self, w, color=BORDER, thick=0.5):
        Flowable.__init__(self)
        self.width, self.color, self.thick = w, color, thick
        self.height = thick + 2
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, 1, self.width, 1)


# ─── PDF BUILDER ─────────────────────────────────────────────────────────────
class KelpCOA:
    def __init__(self, d, logo_bytes=None, sig_bytes=None, coc_bytes=None):
        self.d = d
        self.logo_bytes = logo_bytes
        self.sig_bytes = sig_bytes
        self.coc_bytes = coc_bytes
        self._pg = [0]
        self._total = d.get("total_page_count", 12)

    def _img_buf(self, raw):
        b = io.BytesIO(raw); b.seek(0); b.name = 'img.png'; return b

    def _logo(self, mw=1.5*inch, mh=0.7*inch):
        if self.logo_bytes:
            im = PILImage.open(io.BytesIO(self.logo_bytes))
            iw, ih = im.size; s = min(mw/iw, mh/ih)
            return Image(self._img_buf(self.logo_bytes), width=iw*s, height=ih*s)
        return Paragraph('<font color="#1F4E79" size="15"><b>KETOS</b></font><br/>'
                         '<font color="#3A9ABF" size="6.5">ENVIRONMENTAL LAB SERVICES</font>',
                         ParagraphStyle('lgo', fontSize=15, leading=17))

    # ── Page header: logo left, lab info right, title centered, thin rule ──
    def _hdr(self, title):
        items = []
        # Top bar: logo + lab address
        logo = self._logo()
        addr = Paragraph(
            f'<font size="7" color="#4A5568">{LAB["entity"]}<br/>'
            f'{LAB["addr"][0]}<br/>{LAB["addr"][1]}<br/>'
            f'Tel: {LAB["phone"]}  |  {LAB["email"]}</font>',
            ParagraphStyle('addr', fontSize=7, leading=9, alignment=TA_RIGHT, textColor=DKGRAY))
        bar = Table([[logo, addr]], colWidths=[CW*0.45, CW*0.55], hAlign='LEFT')
        bar.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'BOTTOM'),
                                 ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
        items.append(bar)
        items.append(Spacer(1, 4))
        items.append(HLine(CW, NAVY, 1.2))
        items.append(Spacer(1, 6))
        items.append(Paragraph(title, ST['title']))
        items.append(Spacer(1, 2))
        items.append(HLine(CW, LTGRAY, 0.4))
        items.append(Spacer(1, 8))
        return items

    # ── Data table with proper headers ──
    def _tbl(self, hdrs, rows, cw, result_col=None):
        """Professional data table: navy header, alternating rows, wrapping text."""
        # Normalize column widths to exactly fill CW
        total = sum(cw)
        if total > 0:
            cw = [w * CW / total for w in cw]
        data = [[Paragraph(h, ST['thl'] if i==0 else ST['th']) for i,h in enumerate(hdrs)]]
        for row in rows:
            data.append([
                Paragraph(str(v) if v else '', ST['tdl'] if ci==0 else (ST['tdb'] if result_col and ci==result_col else ST['td']))
                for ci, v in enumerate(row)])

        t = Table(data, colWidths=cw, hAlign='LEFT', repeatRows=1)
        cmds = [
            ('BACKGROUND', (0,0), (-1,0), HDRFILL),
            ('TEXTCOLOR',  (0,0), (-1,0), WHT),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0),(-1,-1), 3),
            ('LEFTPADDING',(0,0), (-1,-1), 4),
            ('RIGHTPADDING',(0,0),(-1,-1), 4),
            ('LINEBELOW',  (0,0), (-1,0), 0.8, NAVY),
            ('LINEBELOW',  (0,-1),(-1,-1), 0.5, BORDER),
            ('LINEAFTER',  (0,0), (-2,-1), 0.2, HexColor("#E2E8F0")),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0: cmds.append(('BACKGROUND',(0,i),(-1,i), ROWALT))
            cmds.append(('LINEBELOW',(0,i),(-1,i), 0.2, LTGRAY))
        t.setStyle(TableStyle(cmds))
        return t

    # ── Info grid (label-value pairs) ──
    def _info(self, pairs, cw=None):
        """pairs = [[(lbl,val),(lbl,val)], ...] — rows of pairs"""
        data = []
        for row in pairs:
            r = []
            for lbl, val in row:
                r.append(Paragraph(f'<b>{lbl}</b>' if lbl else '', ST['lbl7']))
                r.append(Paragraph(str(val), ST['val7']))
            data.append(r)
        nc = len(data[0]) if data else 4
        if cw is None:
            cw = [CW/nc] * nc
        t = Table(data, colWidths=cw, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),1.5),('BOTTOMPADDING',(0,0),(-1,-1),1.5),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),3),
        ]))
        return t

    # ── Prep/Batch info bar (light blue strip) ──
    def _batchbar(self, items_dict):
        cells = []
        for k, v in items_dict.items():
            cells.append(Paragraph(f'<b>{k}</b> {v}', ST['bb7']))
        n = len(cells)
        t = Table([cells], colWidths=[CW/n]*n, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), TEALLT),
            ('BOX',(0,0),(-1,0), 0.4, BORDER),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),5),
        ]))
        return t

    # ── Build PDF ──
    def build(self):
        buf = io.BytesIO()
        doc = BaseDocTemplate(buf, pagesize=letter,
            leftMargin=MG, rightMargin=MG, topMargin=0.5*inch, bottomMargin=0.55*inch,
            title=f"KELP COA — WO {self.d.get('work_order','')}")
        frame = Frame(MG, 0.55*inch, CW, PH - 0.5*inch - 0.55*inch, id='main')
        pg = self._pg; total = self._total
        def on_page(canvas, doc_):
            pg[0] += 1
            canvas.saveState()
            # Footer
            canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.4)
            canvas.line(MG, 0.5*inch, PW-MG, 0.5*inch)
            canvas.setFont("Helvetica", 6); canvas.setFillColor(MDGRAY)
            canvas.drawString(MG, 0.36*inch, DISCLAIMER)
            canvas.drawRightString(PW-MG, 0.36*inch, f"Page {pg[0]} of {total}")
            canvas.restoreState()
        doc.addPageTemplates([PageTemplate(id='all', frames=[frame], onPage=on_page)])

        story = self._pg_cover()
        story.append(PageBreak())
        story += self._pg_narrative()
        story.append(PageBreak())
        story += self._pg_result_summary()
        for samp in self.d.get('samples', []):
            story.append(PageBreak())
            story += self._pg_analytical(samp)
        story.append(PageBreak())
        story += self._pg_qc_mb()
        story.append(PageBreak())
        story += self._pg_qc_lcs()
        story.append(PageBreak())
        story += self._pg_qualifiers()
        story.append(PageBreak())
        story += self._pg_receipt()
        story.append(PageBreak())
        story += self._pg_login()
        story.append(PageBreak())
        story += self._pg_coc()
        doc.build(story)
        return buf.getvalue()

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 1: COVER LETTER
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_cover(self):
        s = []
        s.append(Spacer(1, 6))

        # ── Top banner: Logo left | Lab info right (like Pace Analytical) ──
        logo = self._logo(mw=1.8*inch, mh=0.8*inch)
        lab_info = Paragraph(
            f'<font size="8"><b>{LAB["entity"]}</b></font><br/>'
            f'<font size="7" color="#4A5568">{LAB["addr"][0]}<br/>'
            f'{LAB["addr"][1]}<br/>'
            f'Tel: {LAB["phone"]}<br/>'
            f'{LAB["email"]}</font>',
            ParagraphStyle('labaddr', fontSize=7, leading=9.5, alignment=TA_RIGHT, textColor=DKGRAY))
        banner = Table([[logo, lab_info]], colWidths=[CW*0.5, CW*0.5], hAlign='LEFT')
        banner.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ]))
        s.append(banner)
        s.append(Spacer(1, 4))
        s.append(HLine(CW, NAVY, 1.5))
        s.append(Spacer(1, 20))

        # ── Date ──
        rpt_date = self.d.get('report_date','')
        s.append(Paragraph(str(rpt_date), ST['b9']))
        s.append(Spacer(1, 18))

        # ── Recipient block ──
        contact = self.d.get('client_contact','')
        company = self.d.get('client_company','')
        addr = self.d.get('client_address','')
        csz = self.d.get('client_city_state_zip','')
        for line in [contact, company, addr, csz]:
            if line:
                s.append(Paragraph(line, ST['b9']))
        s.append(Spacer(1, 18))

        # ── RE block ──
        proj = self.d.get('project_name','')
        wo = self.d.get('work_order','')
        re_style = ParagraphStyle('re', parent=ST['b9'], leftIndent=36)
        s.append(Paragraph(f'RE:&nbsp;&nbsp;&nbsp;Project: &nbsp;<b>{proj}</b>', ST['b9']))
        s.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;KELP Work Order No.: &nbsp;<b>{wo}</b>', ST['b9']))
        s.append(Spacer(1, 18))

        # ── Salutation + body ──
        s.append(Paragraph(f"Dear {contact}:", ST['b9']))
        s.append(Spacer(1, 10))

        body_s = ParagraphStyle('cbody', parent=ST['b9'], fontSize=9.5, leading=14.5,
                                 alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=6)
        recv = self.d.get('date_received_text','')
        elap = self.d.get('elap_number','XXXX')
        phone = self.d.get('lab_phone_display', LAB['phone'])

        s.append(Paragraph(
            f"Enclosed are the analytical results for sample(s) received by the laboratory on "
            f"{recv}. The results relate only to the samples included in this report. Results "
            f"reported herein conform to the applicable TNI/NELAC Standards and the laboratory's "
            f"Quality Manual, where applicable, unless otherwise noted in the body of the report.", body_s))
        s.append(Paragraph(
           
            f"If you have any questions concerning this report, please feel free to contact us at {phone}.", body_s))
        s.append(Spacer(1, 24))

        # ── Signature block: "Sincerely," then sig image then name/title ──
        s.append(Paragraph("Sincerely,", ST['b9']))
        s.append(Spacer(1, 4))
        if self.sig_bytes:
            # Constrain signature to reasonable size and left-align
            im = PILImage.open(io.BytesIO(self.sig_bytes))
            iw, ih = im.size
            max_w, max_h = 1.8*inch, 0.55*inch
            scale = min(max_w / iw, max_h / ih)
            sig_w, sig_h = iw * scale, ih * scale
            sig_img = Image(self._img_buf(self.sig_bytes), width=sig_w, height=sig_h)
            sig_img.hAlign = 'LEFT'
            s.append(sig_img)
        else:
            s.append(Spacer(1, 30))
        s.append(Spacer(1, 2))
        s.append(HLine(2.4*inch, NAVY, 0.5))
        s.append(Spacer(1, 2))
        s.append(Paragraph(f"<b>{self.d.get('approver_name','')}</b>", ST['bb9']))
        s.append(Paragraph(self.d.get('approver_title',''), ST['b8']))
        s.append(Paragraph(str(self.d.get('approval_date','')), ST['b8']))

        # ── Bottom: Disclaimer + accreditation ──
         #s.append(Spacer(1, 30))
        # s.append(HLine(CW, LTGRAY, 0.3))
        # s.append(Spacer(1, 4))
        # disc_s = ParagraphStyle('disc2', parent=ST['b7'], textColor=MDGRAY, alignment=TA_CENTER)
        # s.append(Paragraph(DISCLAIMER, disc_s))
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 2: CASE NARRATIVE
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_narrative(self):
        s = self._hdr("CASE NARRATIVE")
        # Info block
        s.append(self._info([
            [("Client:", self.d.get('client_company','')), ("Work Order:", self.d.get('work_order',''))],
            [("Project:", self.d.get('project_name','')),  ("Report Date:", str(self.d.get('report_date','')))],
        ], cw=[0.7*inch, 2.5*inch, 0.9*inch, CW-4.1*inch]))
        s.append(Spacer(1, 6))
        s.append(HLine(CW, LTGRAY, 0.4))
        s.append(Spacer(1, 10))

        bs = ParagraphStyle('nb', parent=ST['b9'], spaceBefore=6, spaceAfter=4, leftIndent=4, rightIndent=4)
        custom = self.d.get('case_narrative_custom','')
        if custom:
            s.append(Paragraph(custom, bs))

        if self.d.get('qc_met', True):
            s.append(Paragraph(
                "Water samples were received without an intact Chain of Custody (COC). "
                "Documentation was missing or incomplete upon arrival.", bs))
        if not self.d.get('method_blank_corrected', False):
            s.append(Paragraph(
                "Analysis followed standard methodologies. All Quality Control (QC) metrics met acceptance criteria unless otherwise flagged. Unless otherwise indicated, no results have been method blank or field blank corrected.", bs))
        s.append(Paragraph(
            "Results relate exclusively to the samples as received and tested by the laboratory.", bs))
      
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 3: SAMPLE RESULT SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_result_summary(self):
        s = self._hdr("SAMPLE RESULT SUMMARY")
        # Top info
        s.append(self._info([
            [("Report prepared for:", self.d.get('client_contact','')),
             ("Date Received:", self.d.get('date_received_text',''))],
            [("", self.d.get('client_company','')),
             ("Date Reported:", str(self.d.get('report_date','')))],
        ], cw=[1.3*inch, 2.2*inch, 1.1*inch, CW-4.6*inch]))
        s.append(Spacer(1, 10))

        for samp in self.d.get('samples', []):
            # Sample sub-header
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

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYTICAL RESULTS (per sample)
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_analytical(self, samp):
        s = self._hdr("ANALYTICAL RESULTS")

        # Sample info bar (like Pace Analytical)
        csid = samp.get('client_sample_id','')
        lsid = samp.get('lab_sample_id','')
        mx   = samp.get('matrix','Water')
        ds   = samp.get('date_sampled','')
        recv = self.d.get('date_received_text','')

        info_bar = Table([[
            Paragraph(f'<b>Sample:</b> {csid}', ST['bb7']),
            Paragraph(f'<b>Lab ID:</b> {lsid}', ST['bb7']),
            Paragraph(f'<b>Collected:</b> {ds}', ST['bb7']),
            Paragraph(f'<b>Received:</b> {recv}', ST['bb7']),
            Paragraph(f'<b>Matrix:</b> {mx}', ST['bb7']),
        ]], colWidths=[CW*0.22, CW*0.22, CW*0.22, CW*0.18, CW*0.16], hAlign='LEFT')
        info_bar.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), ACCENT),
            ('BOX',(0,0),(-1,0), 0.5, NAVY),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),4),
        ]))
        s.append(info_bar)
        s.append(Spacer(1, 8))

        # Results grouped by prep method
        for pg in samp.get('prep_groups', []):
            pm  = pg.get('prep_method','')
            pbi = pg.get('prep_batch_id','')
            pdt = pg.get('prep_date_time','')
            pa  = pg.get('prep_analyst','')

            # Method header
            s.append(self._batchbar({
                "Prep Method:": pm, "Prep Batch:": pbi,
                "Prep Date/Time:": pdt, "Prep Analyst:": pa,
            }))
            s.append(Spacer(1, 2))

            hdrs = ["Parameters", "Analysis\nMethod", "DF", "MDL", "PQL",
                     "Results", "Q", "Units", "Analyzed", "Analyst", "Analytical\nBatch"]
            cw = [CW*0.17, CW*0.10, CW*0.04, CW*0.07, CW*0.07,
                  CW*0.09, CW*0.04, CW*0.06, CW*0.13, CW*0.06, CW*0.10]
            rows = []
            for r in pg.get('results',[]):
                rows.append([
                    r.get('parameter',''), r.get('method',''), r.get('df','1'),
                    r.get('mdl',''), r.get('pql',''), r.get('result',''),
                    r.get('qualifier',''), r.get('unit','mg/L'),
                    r.get('analyzed_time',''), r.get('analyst',''), r.get('analytical_batch',''),
                ])
            s.append(self._tbl(hdrs, rows, cw, result_col=5))
            s.append(Spacer(1, 10))

        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # QC: METHOD BLANKS
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_qc_mb(self):
        s = self._hdr("QUALITY CONTROL DATA — Method Blanks")
        for mb in self.d.get('mb_batches',[]):
            s.append(self._batchbar({
                "Prep Method:": mb.get('prep_method',''),
                "Analytical Method:": mb.get('analytical_method',''),
                "Prep Batch:": mb.get('prep_batch',''),
                "Analytical Batch:": mb.get('analytical_batch',''),
            }))
            s.append(self._info([
                [("Matrix:", mb.get('matrix','Water')), ("Units:", mb.get('units','mg/L')),
                 ("Prep Date:", mb.get('prep_date','')), ("Analyzed:", mb.get('analyzed_date',''))],
            ], cw=[0.5*inch, 1.2*inch, 0.5*inch, 1.2*inch, 0.7*inch, 1.2*inch, 0.7*inch, CW-6*inch]))
            s.append(Spacer(1, 4))

            hdrs = ["Parameters", "MDL", "PQL", "Blank Result", "Qualifier"]
            cw = [CW*0.35, CW*0.15, CW*0.15, CW*0.18, CW*0.17]
            rows = [[r.get('parameter',''), r.get('mdl',''), r.get('pql',''),
                      r.get('mb_conc','ND'), r.get('qualifier','')]
                     for r in mb.get('results',[])]
            s.append(self._tbl(hdrs, rows, cw))
            s.append(Spacer(1, 14))
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # QC: LCS/LCSD
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_qc_lcs(self):
        s = self._hdr("QUALITY CONTROL DATA — LCS/LCSD")
        s.append(Paragraph("Raw values are used in quality control assessment.", ST['ital']))
        s.append(Spacer(1, 6))

        for lcs in self.d.get('lcs_batches',[]):
            s.append(self._batchbar({
                "Prep Method:": lcs.get('prep_method',''),
                "Analytical Method:": lcs.get('analytical_method',''),
                "Prep Batch:": lcs.get('prep_batch',''),
                "Analytical Batch:": lcs.get('analytical_batch',''),
            }))
            s.append(self._info([
                [("Matrix:", lcs.get('matrix','Water')), ("Units:", lcs.get('units','mg/L')),
                 ("Prep Date:", lcs.get('prep_date','')), ("Analyzed:", lcs.get('analyzed_date',''))],
            ], cw=[0.5*inch, 1.2*inch, 0.5*inch, 1.2*inch, 0.7*inch, 1.2*inch, 0.7*inch, CW-6*inch]))
            s.append(Spacer(1, 4))

            hdrs = ["Parameters", "MDL", "PQL", "Spike\nConc.", "LCS\n% Rec",
                     "LCSD\n% Rec", "RPD", "% Rec\nLimits", "%RPD\nLimit", "Qual"]
            cw = [CW*0.17, CW*0.08, CW*0.08, CW*0.09, CW*0.09,
                  CW*0.09, CW*0.08, CW*0.12, CW*0.10, CW*0.07]
            rows = []
            for r in lcs.get('results',[]):
                rows.append([
                    r.get('parameter',''), r.get('mdl',''), r.get('pql',''),
                    r.get('spike_conc',''), r.get('lcs_recovery',''),
                    r.get('lcsd_recovery',''), r.get('rpd',''),
                    r.get('recovery_limits','80-120'), r.get('rpd_limits','20'), r.get('qualifier',''),
                ])
            s.append(self._tbl(hdrs, rows, cw))
            s.append(Spacer(1, 14))
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # QUALIFIERS & DEFINITIONS
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_qualifiers(self):
        s = self._hdr("QUALIFIERS AND DEFINITIONS")

        s.append(Paragraph('<b>DEFINITIONS</b>', ST['sect']))
        s.append(HLine(CW, NAVY, 0.4))
        s.append(Spacer(1, 4))
        for d in DEFINITIONS:
            s.append(Paragraph(d, ParagraphStyle('def', parent=ST['b7'], spaceBefore=1.5, spaceAfter=1.5, leftIndent=6)))
        s.append(Spacer(1, 10))

        s.append(Paragraph('<b>ANALYTE QUALIFIERS</b>', ST['sect']))
        s.append(HLine(CW, NAVY, 0.4))
        s.append(Spacer(1, 4))

        qdata = [[Paragraph(f'<b>{c}</b>', ST['qc']), Paragraph(f'— {d}', ST['qd'])] for c, d in QUALIFIERS]
        qt = Table(qdata, colWidths=[0.4*inch, CW-0.4*inch-8], hAlign='LEFT')
        qt.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
            ('LEFTPADDING',(0,0),(0,-1),8),('LEFTPADDING',(1,0),(1,-1),4),
            ('LINEBELOW',(0,0),(-1,-2), 0.2, LTGRAY),
        ]))
        s.append(qt)
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # SAMPLE RECEIPT CHECKLIST
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_receipt(self):
        s = self._hdr("SAMPLE RECEIPT CHECKLIST")
        rc = self.d.get('receipt', {})

        # Header info
        s.append(self._info([
            [("Client:", self.d.get('client_company','')),
             ("Date/Time Received:", rc.get('date_time_received',''))],
            [("Project:", self.d.get('project_name','')),
             ("Received By:", rc.get('received_by',''))],
            [("Work Order:", self.d.get('work_order','')),
             ("Carrier:", rc.get('carrier_name',''))],
        ], cw=[0.8*inch, 2*inch, 1.3*inch, CW-4.1*inch]))
        s.append(Spacer(1, 8))

        sections = [
            ("Chain of Custody (COC) Information", [
                ("Chain of custody present?", rc.get("coc_present","")),
                ("COC signed when relinquished and received?", rc.get("coc_signed","")),
                ("COC agrees with sample labels?", rc.get("coc_agrees","")),
                ("Custody seals intact on sample bottles?", rc.get("custody_seals_bottles","")),
            ]),
            ("Sample Receipt Information", [
                ("Custody seals intact on shipping container/cooler?", rc.get("custody_seals_cooler","")),
                ("Shipping container/cooler in good condition?", rc.get("cooler_good","")),
                ("Samples in proper container/bottle?", rc.get("proper_container","")),
                ("Sample containers intact?", rc.get("containers_intact","")),
                ("Sufficient sample volume for indicated test?", rc.get("sufficient_volume","")),
            ]),
            ("Preservation and Hold Time Information", [
                ("All samples received within holding time?", rc.get("within_holding_time","")),
                ("Container/Temp blank temperature in compliance?", f'{rc.get("temp_compliance","")}  (Temp: {rc.get("temperature","")} °C)'),
                ("Water-VOA vials have zero headspace?", rc.get("voa_headspace","")),
                ("Water-pH acceptable upon receipt?", rc.get("ph_acceptable","")),
            ]),
        ]
        for title, items in sections:
            s.append(Paragraph(f'<b>{title}</b>', ParagraphStyle('sh', parent=ST['sect'], spaceBefore=6, spaceAfter=2)))
            s.append(HLine(CW, LTGRAY, 0.3))
            s.append(Spacer(1, 2))
            data = [[Paragraph(q, ST['b8']), Paragraph(str(a), ST['bb8'])] for q, a in items]
            ct = Table(data, colWidths=[3.8*inch, CW-3.8*inch], hAlign='LEFT')
            ct.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
                ('LEFTPADDING',(0,0),(0,-1),10),('LEFTPADDING',(1,0),(1,-1),6),
                ('LINEBELOW',(0,0),(-1,-2), 0.15, LTGRAY),
            ]))
            s.append(ct)

        s.append(Spacer(1, 8))
        s.append(Paragraph(f'<b>Comments:</b> {rc.get("receipt_comments","")}', ST['b8']))
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGIN SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_login(self):
        s = self._hdr("SAMPLE CROSS-REFERENCE / LOGIN SUMMARY")
        ls = self.d.get('login_summary',{})

        s.append(self._info([
            [("Client:", self.d.get('client_company','')), ("QC Level:", ls.get('qc_level','II'))],
            [("Project:", self.d.get('project_name','')),  ("TAT:", ls.get('tat_requested',''))],
            [("Work Order:", self.d.get('work_order','')), ("Received:", ls.get('date_received_login',''))],
        ], cw=[0.8*inch, 2.2*inch, 0.8*inch, CW-3.8*inch]))
        s.append(Spacer(1, 6))
        s.append(HLine(CW, NAVY, 0.4))
        s.append(Spacer(1, 6))

        hdrs = ["Lab Sample ID", "Client\nSample ID", "Collection\nDate/Time", "Matrix",
                 "Disposal\nDate", "Tests Requested"]
        cw = [CW*0.16, CW*0.15, CW*0.14, CW*0.08, CW*0.12, CW*0.35]
        rows = []
        for samp in self.d.get('samples',[]):
            tests = ", ".join([pg.get('analytical_method','') for pg in samp.get('prep_groups',[])])
            rows.append([
                samp.get('lab_sample_id',''), samp.get('client_sample_id',''),
                samp.get('date_sampled',''), samp.get('matrix','Water'),
                samp.get('disposal_date',''), tests,
            ])
        s.append(self._tbl(hdrs, rows, cw))
        return s

    # ═══════════════════════════════════════════════════════════════════════════
    # CHAIN OF CUSTODY
    # ═══════════════════════════════════════════════════════════════════════════
    def _pg_coc(self):
        s = self._hdr("CHAIN OF CUSTODY")
        if self.coc_bytes:
            im = PILImage.open(io.BytesIO(self.coc_bytes))
            iw, ih = im.size
            mw, mh = CW, PH - 2.5*inch
            sc = min(mw/iw, mh/ih)
            s.append(Image(self._img_buf(self.coc_bytes), width=iw*sc, height=ih*sc))
        else:
            s.append(Spacer(1, 2*inch))
            s.append(Paragraph("(Upload Chain of Custody scan in the application)",
                               ParagraphStyle('ph', parent=ST['b9'], alignment=TA_CENTER, textColor=MDGRAY)))
        return s


# ═══════════════════════════════════════════════════════════════════════════════
# KELP ANALYTE CATALOG — Built from KELP CA ELAP Price List
# ═══════════════════════════════════════════════════════════════════════════════
# Structured as {method: [analytes]} for dropdown population.
# Source: KELP_CA_ELAP__PriceList__New_Price_List_with_SKU_92425.csv
KELP_ANALYTE_CATALOG = {
    "EPA 200.8": [
        "Aluminum", "Antimony", "Arsenic", "Barium", "Beryllium", "Cadmium",
        "Chromium", "Cobalt", "Copper", "Lead", "Manganese", "Mercury",
        "Molybdenum", "Nickel", "Selenium", "Silver", "Thallium", "Thorium",
        "Uranium", "Vanadium", "Zinc",
    ],
    "EPA 6020B": [
        "Aluminum", "Antimony", "Arsenic", "Barium", "Beryllium", "Boron",
        "Cadmium", "Calcium", "Chromium", "Cobalt", "Copper", "Iron", "Lead",
        "Magnesium", "Manganese", "Mercury", "Nickel", "Potassium", "Selenium",
        "Silicon", "Silver", "Sodium", "Thallium", "Uranium", "Vanadium", "Zinc",
    ],
    "EPA 300.1": [
        "Bromate", "Bromide", "Chlorate", "Chloride", "Chlorite", "Fluoride",
        "Nitrate", "Nitrite", "Phosphate, Ortho", "Sulfate",
    ],
    "EPA 1633A": ["PFAS 3-Compound", "PFAS 18-Compound", "PFAS 25-Compound", "PFAS 40-Compound"],
    "EPA 537.1": ["PFAS 3-Compound", "PFAS 14-Compound", "PFAS 18-Compound"],
    "EPA 533":   ["PFAS 25-Compound"],
    "EPA 314.0": ["Perchlorate"],
    "EPA 314.2": ["Perchlorate"],
    "EPA 218.6": ["Chromium (VI)"],
    "EPA 150.1": ["pH"],
    "EPA 150.2": ["pH"],
    "EPA 120.1": ["Conductivity"],
    "EPA 130.1": ["Hardness - Total"],
    "EPA 180.1": ["Turbidity"],
    "EPA 350.1": ["Ammonia (as N)"],
    "EPA 351.2": ["Kjeldahl Nitrogen, Total"],
    "EPA 365.1": ["Phosphorus, Total"],
    "EPA 410.4": ["Chemical Oxygen Demand"],
    "EPA 415.1": ["Total Organic Carbon"],
    "EPA 415.3": ["Total Organic Carbon", "Dissolved Organic Carbon"],
    "SM 2320B":  ["Alkalinity"],
    "SM 2340C":  ["Hardness - Total"],
    "SM 2510B":  ["Conductivity"],
    "SM 2540B":  ["Total Solids"],
    "SM 2540C":  ["Total Dissolved Solids"],
    "SM 2540D":  ["Total Suspended Solids"],
    "SM 2550B":  ["Temperature"],
    "SM 3500-CaB": ["Calcium - Total"],
    "SM 3500-MgB": ["Magnesium - Total"],
    "SM 4500-CN E": ["Cyanide, Total"],
    "SM 4500-CN I": ["Cyanide, Available"],
    "SM 4500-Cl F": ["Chlorine, Free - DPD", "Chlorine, Total - DPD"],
    "SM 4500-Cl G": ["Chloramines (Monochloramine)", "Chlorine, Combined", "Chlorine, Free"],
    "SM 4500-ClO2 E": ["Chlorine Dioxide"],
    "SM 4500-O":  ["Dissolved Oxygen"],
    "SM 4500-S2-D": ["Sulfide (as S)"],
    "SM 4500-SO3": ["Sulfite (as SO3)"],
    "SM 5210B":  ["BOD (5-day)", "BOD, Carbonaceous"],
    "SM 5540C":  ["Surfactants (MBAS)"],
    "SW-846 9012B": ["Cyanide, Total"],
}

# Flat list of all unique analyte names for freeform selectbox
ALL_ANALYTES = sorted(set(a for lst in KELP_ANALYTE_CATALOG.values() for a in lst))
ALL_METHODS  = sorted(KELP_ANALYTE_CATALOG.keys())

# Default units per method family
METHOD_UNITS = {
    "EPA 200.8": "mg/L", "EPA 6020B": "mg/L", "EPA 300.1": "mg/L",
    "EPA 1633A": "ng/L", "EPA 537.1": "ng/L", "EPA 533": "ng/L",
    "EPA 314.0": "µg/L", "EPA 314.2": "µg/L", "EPA 218.6": "µg/L",
    "EPA 150.1": "S.U.", "EPA 150.2": "S.U.",
    "EPA 120.1": "µmhos/cm", "SM 2510B": "µmhos/cm",
    "EPA 130.1": "mg/L", "SM 2340C": "mg/L",
    "EPA 180.1": "NTU",
    "EPA 350.1": "mg/L", "EPA 351.2": "mg/L", "EPA 365.1": "mg/L",
    "EPA 410.4": "mg/L", "EPA 415.1": "mg/L", "EPA 415.3": "mg/L",
    "SM 2320B": "mg/L", "SM 2540B": "mg/L", "SM 2540C": "mg/L",
    "SM 2540D": "mg/L", "SM 2550B": "°C",
    "SM 5210B": "mg/L", "SM 5540C": "mg/L",
}

# KELP qualifiers (from the Qualifiers & Definitions page)
KELP_QUALIFIERS = ["","B","D","E","H","J","NA","N/A","ND","NR","R","S","X"]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: format date objects to string for PDF
# ═══════════════════════════════════════════════════════════════════════════════
def _fmt_date(val, fmt="%m/%d/%Y"):
    """Convert date/datetime to string; pass through strings."""
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime(fmt)
    if isinstance(val, date):
        return val.strftime(fmt)
    return str(val)

def _fmt_datetime(d_val, t_val, fmt="%m/%d/%Y %H:%M"):
    """Combine a date and time into formatted string."""
    if d_val is None:
        return ""
    if isinstance(d_val, date) and isinstance(t_val, time_type):
        return datetime.combine(d_val, t_val).strftime(fmt)
    if isinstance(d_val, date):
        return d_val.strftime("%m/%d/%Y")
    return str(d_val)


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═══════════════════════════════════════════════════════════════════════════════
def _safe_date(val):
    """Coerce any value to a date object for st.date_input, or return today."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str) and val:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return date.today()

def _safe_time(val):
    """Coerce any value to a time object for st.time_input, or return None."""
    if isinstance(val, time_type):
        return val
    if isinstance(val, datetime):
        return val.time()
    if isinstance(val, str) and val:
        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p"):
            try:
                return datetime.strptime(val, fmt).time()
            except ValueError:
                continue
    return None

def init_session():
    defaults = {
        "elap_number": "XXXX", "lab_phone_display": "(408) 550-2162",
        "report_date": date.today(), "work_order": "", "total_page_count": 12,
        "client_contact": "", "client_company": "", "client_address": "",
        "client_city_state_zip": "", "client_phone": "", "client_email": "",
        "project_name": "", "project_number": "", "client_id": "",
        "num_samples_text": "1", "date_received": date.today(),
        "approver_name": "Ermias L", "approver_title": "Lab Director",
        "approval_date": date.today(),
        "case_narrative_custom": "", "qc_met": True, "method_blank_corrected": False,
        # TNI 5.10.11c — non-accredited test flagging
        "has_non_accredited_tests": False,
        # TNI 5.10.11d — results outside calibration range
        "has_results_outside_cal": False,
        # TNI 4.5.5 — subcontracted work
        "has_subcontracted": False, "subcontractor_lab": "",
        # Sample condition deviations (TNI 5.8.7.2)
        "sample_condition_notes": "",
        "samples": [], "mb_batches": [], "lcs_batches": [],
        "receipt": {
            "date_received_receipt": date.today(), "time_received_receipt": None,
            "received_by":"","physically_logged_by":"",
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
            "date_received_login": date.today(),
            "report_due_date": None,
            "login_comments":"",
        },
        "logo_bytes": None, "signature_bytes": None, "coc_image_bytes": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _method_selectbox(container, label, current, key):
    """Selectbox for method with 'Other' freeform fallback."""
    opts = [""] + ALL_METHODS + ["── Other (type below) ──"]
    idx = 0
    if current in ALL_METHODS:
        idx = ALL_METHODS.index(current) + 1
    sel = container.selectbox(label, opts, index=idx, key=key)
    if sel.startswith("──"):
        sel = container.text_input("Custom method", current, key=f"{key}_custom")
    return sel


def _analyte_selectbox(container, label, current, method, key):
    """Selectbox for analyte filtered by selected method, with freeform."""
    if method and method in KELP_ANALYTE_CATALOG:
        opts = [""] + KELP_ANALYTE_CATALOG[method] + ["── Other ──"]
    else:
        opts = [""] + ALL_ANALYTES + ["── Other ──"]
    idx = 0
    if current in opts:
        idx = opts.index(current)
    sel = container.selectbox(label, opts, index=idx, key=key)
    if sel.startswith("──"):
        sel = container.text_input("Custom analyte", current, key=f"{key}_custom")
    return sel


def _qualifier_selectbox(container, label, current, key):
    """Selectbox for data qualifiers."""
    idx = KELP_QUALIFIERS.index(current) if current in KELP_QUALIFIERS else 0
    return container.selectbox(label, KELP_QUALIFIERS, index=idx, key=key)


def _unit_for_method(method):
    """Return default unit for a given method."""
    return METHOD_UNITS.get(method, "mg/L")


def main():
    st.set_page_config(page_title="KELP COA Generator", page_icon="🧪", layout="wide")

    st.markdown("""<style>
    .stApp { font-family: 'Calibri','Segoe UI',sans-serif; }
    .main-hdr { background: linear-gradient(135deg, #1F4E79 0%, #3A9ABF 100%); padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 1.5rem; color: white; }
    .main-hdr h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-hdr p { color: #D6E4F0; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .sec-hdr { background-color: #1F4E79; color: white; padding: 0.5rem 1rem; border-radius: 5px; margin: 1rem 0 0.5rem 0; font-weight: bold; }
    div[data-testid="stSidebar"] { background-color: #f8f9fa; }
    .stButton > button { background: linear-gradient(135deg, #1F4E79, #3A9ABF); color: white; border: none; font-weight: bold; }
    </style>""", unsafe_allow_html=True)

    init_session()

    st.markdown("""<div class="main-hdr">
        <h1>🧪 KELP — Certificate of Analysis Generator</h1>
        <p>KETOS Environmental Lab Platform &nbsp;|&nbsp; TNI / ISO 17025 / ELAP Compliant</p>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 📁 File Uploads")
        logo_file = st.file_uploader("KELP Logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_up")
        if logo_file: st.session_state.logo_bytes = logo_file.read(); st.image(st.session_state.logo_bytes, width=200)
        sig_file = st.file_uploader("Approver Signature", type=["png","jpg","jpeg"], key="sig_up")
        if sig_file: st.session_state.signature_bytes = sig_file.read(); st.image(st.session_state.signature_bytes, width=150)
        coc_file = st.file_uploader("Chain of Custody Scan", type=["png","jpg","jpeg"], key="coc_up")
        if coc_file: st.session_state.coc_image_bytes = coc_file.read(); st.success("CoC uploaded ✓")
        st.divider()
        st.markdown("### ⚙️ Settings")
        st.session_state.elap_number = st.text_input("ELAP #", st.session_state.elap_number)
        st.session_state.lab_phone_display = st.text_input("Lab Phone", st.session_state.lab_phone_display)

    tabs = st.tabs(["📋 Report Info", "🧫 Samples & Results", "🔬 QC Data", "📦 Receipt & Login", "📄 Generate COA"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: Report Info
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown('<div class="sec-hdr">Client Information</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.client_contact = st.text_input("Contact Name", st.session_state.client_contact)
            st.session_state.client_company = st.text_input("Company", st.session_state.client_company)
            st.session_state.client_address = st.text_input("Address", st.session_state.client_address)
            st.session_state.client_city_state_zip = st.text_input("City/State/ZIP", st.session_state.get('client_city_state_zip',''))
        with c2:
            st.session_state.project_name = st.text_input("Project Name", st.session_state.project_name)
            st.session_state.project_number = st.text_input("Project Number", st.session_state.project_number)
            st.session_state.work_order = st.text_input("Work Order #", st.session_state.work_order)
            st.session_state.client_id = st.text_input("Client ID", st.session_state.client_id)

        st.markdown('<div class="sec-hdr">Report Details</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.session_state.report_date = st.date_input("Report Date", _safe_date(st.session_state.report_date))
            st.session_state.num_samples_text = st.text_input("Number of Samples", st.session_state.num_samples_text)
            st.session_state.date_received = st.date_input("Date Received", _safe_date(st.session_state.date_received))
        with c4:
            st.session_state.approver_name = st.text_input("Approver Name", st.session_state.approver_name)
            st.session_state.approver_title = st.text_input("Approver Title", st.session_state.approver_title)
            st.session_state.approval_date = st.date_input("Approval Date", _safe_date(st.session_state.approval_date))

        st.markdown('<div class="sec-hdr">Case Narrative & Compliance</div>', unsafe_allow_html=True)
        st.session_state.qc_met = st.checkbox("All QC met EPA specifications", st.session_state.qc_met)
        st.session_state.method_blank_corrected = st.checkbox("Results blank corrected", st.session_state.method_blank_corrected)
        # TNI 5.10.11c — non-accredited test flagging
        st.session_state.has_non_accredited_tests = st.checkbox(
            "Report contains non-accredited tests (TNI 5.10.11c)", st.session_state.has_non_accredited_tests,
            help="If checked, non-accredited tests will be clearly identified on the report.")
        # TNI 5.10.11d — outside calibration range
        st.session_state.has_results_outside_cal = st.checkbox(
            "Results outside calibration range present (TNI 5.10.11d)", st.session_state.has_results_outside_cal,
            help="Numerical results outside the calibration range will be flagged with 'E' qualifier.")
        # TNI 4.5.5 — subcontracted work
        st.session_state.has_subcontracted = st.checkbox(
            "Work subcontracted to external lab (TNI 4.5.5)", st.session_state.has_subcontracted)
        if st.session_state.has_subcontracted:
            st.session_state.subcontractor_lab = st.text_input(
                "Subcontractor Laboratory Name & ELAP #", st.session_state.subcontractor_lab,
                placeholder="e.g., ABC Labs, ELAP #1234")
        # TNI 5.8.7.2 — sample condition deviations
        st.session_state.sample_condition_notes = st.text_area(
            "Sample Condition Notes / Deviations (TNI 5.8.7.2)",
            st.session_state.sample_condition_notes, height=60,
            help="Document any sample condition issues: damaged containers, improper preservation, exceeded hold times, etc.")
        st.session_state.case_narrative_custom = st.text_area(
            "Additional Case Narrative (optional)", st.session_state.case_narrative_custom, height=80)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: Samples & Results — with analyte catalog dropdowns
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown('<div class="sec-hdr">Samples</div>', unsafe_allow_html=True)
        st.caption("💡 Select a method first — the analyte dropdown filters automatically from the KELP price list catalog.")
        samples = st.session_state.samples
        num_s = st.number_input("Number of samples", 0, 50, len(samples), step=1)
        _empty_samp = {"client_sample_id":"","lab_sample_id":"","matrix":"Water",
                       "date_sampled":None,"time_sampled":None,"sdg":"",
                       "disposal_date":None,"results":[],"prep_groups":[]}
        while len(samples) < num_s: samples.append(copy.deepcopy(_empty_samp))
        while len(samples) > num_s: samples.pop()

        for si, samp in enumerate(samples):
            with st.expander(f"🧪 Sample {si+1}: {samp.get('lab_sample_id','(new)')}", expanded=(si==0)):
                sc = st.columns(3)
                samp["client_sample_id"]=sc[0].text_input("Client Sample ID",samp.get("client_sample_id",""),key=f"csid_{si}")
                samp["lab_sample_id"]=sc[0].text_input("Lab Sample ID",samp.get("lab_sample_id",""),key=f"lsid_{si}")
                samp["matrix"]=sc[1].selectbox("Matrix",["Water","Soil","Air","Other"],key=f"mx_{si}")
                # Date pickers for sample dates
                samp["date_sampled"]=sc[1].date_input("Date Sampled", _safe_date(samp.get("date_sampled")), key=f"ds_{si}")
                samp["time_sampled"]=sc[1].time_input("Time Sampled", _safe_time(samp.get("time_sampled")), key=f"ts_{si}")
                samp["sdg"]=sc[2].text_input("SDG",samp.get("sdg",""),key=f"sdg_{si}")
                samp["disposal_date"]=sc[2].date_input("Disposal Date", _safe_date(samp.get("disposal_date")), key=f"disp_{si}")

                # ── Summary Results (Page 3) ──
                st.markdown("**Summary Results** (Page 3)")
                nr = st.number_input("# result rows",0,50,len(samp.get("results",[])),key=f"nr_{si}")
                _empty_r = {"parameter":"","method":"","df":"1","mdl":"","pql":"","result":"","unit":"mg/L"}
                while len(samp["results"]) < nr: samp["results"].append(copy.deepcopy(_empty_r))
                while len(samp["results"]) > nr: samp["results"].pop()
                for ri, r in enumerate(samp["results"]):
                    rc = st.columns([3,2,1,1,1,1,1])
                    r["method"] = _method_selectbox(rc[1], "Method", r.get("method",""), f"rm_{si}_{ri}")
                    r["parameter"] = _analyte_selectbox(rc[0], "Param", r.get("parameter",""), r["method"], f"rp_{si}_{ri}")
                    r["df"]=rc[2].text_input("DF",r.get("df","1"),key=f"rd_{si}_{ri}")
                    r["mdl"]=rc[3].text_input("MDL",r.get("mdl",""),key=f"rmdl_{si}_{ri}")
                    r["pql"]=rc[4].text_input("PQL",r.get("pql",""),key=f"rpql_{si}_{ri}")
                    r["result"]=rc[5].text_input("Result",r.get("result",""),key=f"rr_{si}_{ri}")
                    r["unit"]=rc[6].text_input("Unit",r.get("unit",_unit_for_method(r["method"])),key=f"ru_{si}_{ri}")

                st.divider()
                # ── Detailed Results by Prep Method (Pages 4+) ──
                st.markdown("**Detailed Results by Prep Method** (Pages 4+)")
                npg = st.number_input("# Prep groups",0,10,len(samp.get("prep_groups",[])),key=f"npg_{si}")
                _empty_pg = {"prep_method":"","prep_batch_id":"","prep_date":None,"prep_time":None,"prep_analyst":"","results":[]}
                while len(samp["prep_groups"]) < npg: samp["prep_groups"].append(copy.deepcopy(_empty_pg))
                while len(samp["prep_groups"]) > npg: samp["prep_groups"].pop()
                for pi, pg in enumerate(samp["prep_groups"]):
                    st.markdown(f"**Prep Group {pi+1}**")
                    pc = st.columns(5)
                    pg["prep_method"]=pc[0].text_input("Prep Method",pg.get("prep_method",""),key=f"pm_{si}_{pi}")
                    pg["prep_batch_id"]=pc[1].text_input("Prep Batch ID",pg.get("prep_batch_id",""),key=f"pbi_{si}_{pi}")
                    pg["prep_date"]=pc[2].date_input("Prep Date", _safe_date(pg.get("prep_date")), key=f"pdt_{si}_{pi}")
                    pg["prep_time"]=pc[3].time_input("Prep Time", _safe_time(pg.get("prep_time")), key=f"ptt_{si}_{pi}")
                    pg["prep_analyst"]=pc[4].text_input("Prep Analyst",pg.get("prep_analyst",""),key=f"pa_{si}_{pi}")

                    npr = st.number_input("# results",0,50,len(pg.get("results",[])),key=f"npr_{si}_{pi}")
                    _empty_pr = {"parameter":"","method":"","df":"1","mdl":"","pql":"","result":"",
                                 "qualifier":"","unit":"mg/L","analyzed_date":None,"analyzed_time":None,
                                 "analyst":"","analytical_batch":"","is_accredited":True}
                    while len(pg["results"]) < npr: pg["results"].append(copy.deepcopy(_empty_pr))
                    while len(pg["results"]) > npr: pg["results"].pop()
                    for pri, pr in enumerate(pg["results"]):
                        prc = st.columns([2,1.5,0.5,1,1,1,0.5,0.7,1.2,0.5,0.7,1])
                        pr["method"] = _method_selectbox(prc[1], "AMethod", pr.get("method",""), f"prm_{si}_{pi}_{pri}")
                        pr["parameter"] = _analyte_selectbox(prc[0], "Param", pr.get("parameter",""), pr["method"], f"prp_{si}_{pi}_{pri}")
                        pr["df"]=prc[2].text_input("DF",pr.get("df","1"),key=f"prd_{si}_{pi}_{pri}")
                        pr["mdl"]=prc[3].text_input("MDL",pr.get("mdl",""),key=f"prmdl_{si}_{pi}_{pri}")
                        pr["pql"]=prc[4].text_input("PQL",pr.get("pql",""),key=f"prpql_{si}_{pi}_{pri}")
                        pr["result"]=prc[5].text_input("Result",pr.get("result",""),key=f"prr_{si}_{pi}_{pri}")
                        pr["qualifier"] = _qualifier_selectbox(prc[6], "Q", pr.get("qualifier",""), f"prq_{si}_{pi}_{pri}")
                        pr["unit"]=prc[7].text_input("Unit",pr.get("unit",_unit_for_method(pr["method"])),key=f"pru_{si}_{pi}_{pri}")
                        pr["analyzed_date"]=prc[8].date_input("Analyzed", _safe_date(pr.get("analyzed_date")), key=f"prad_{si}_{pi}_{pri}")
                        pr["analyzed_time"]=prc[9].time_input("Time", _safe_time(pr.get("analyzed_time")), key=f"prat_{si}_{pi}_{pri}")
                        pr["analyst"]=prc[10].text_input("By",pr.get("analyst",""),key=f"prby_{si}_{pi}_{pri}")
                        pr["analytical_batch"]=prc[11].text_input("ABatch",pr.get("analytical_batch",""),key=f"prab_{si}_{pi}_{pri}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: QC Data — with catalog dropdowns and date pickers
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown('<div class="sec-hdr">Method Blank (MB) Batches</div>', unsafe_allow_html=True)
        mbs = st.session_state.mb_batches
        nmb = st.number_input("# MB batches",0,20,len(mbs),key="nmb")
        _empty_mb = {"prep_method":"","analytical_method":"","prep_date":None,
                     "analyzed_date":None,"prep_batch":"","analytical_batch":"",
                     "matrix":"Water","units":"mg/L","results":[]}
        while len(mbs) < nmb: mbs.append(copy.deepcopy(_empty_mb))
        while len(mbs) > nmb: mbs.pop()
        for mi, mb in enumerate(mbs):
            with st.expander(f"MB Batch {mi+1}: {mb.get('prep_method','')}"):
                mc=st.columns(4)
                mb["prep_method"]=mc[0].text_input("Prep",mb.get("prep_method",""),key=f"mbpm_{mi}")
                mb["analytical_method"] = _method_selectbox(mc[1], "Analytical", mb.get("analytical_method",""), f"mbam_{mi}")
                mb["prep_date"]=mc[2].date_input("Prep Date", _safe_date(mb.get("prep_date")), key=f"mbpd_{mi}")
                mb["analyzed_date"]=mc[3].date_input("Analyzed Date", _safe_date(mb.get("analyzed_date")), key=f"mbad_{mi}")
                mc2=st.columns(4)
                mb["prep_batch"]=mc2[0].text_input("Prep Batch",mb.get("prep_batch",""),key=f"mbpb_{mi}")
                mb["analytical_batch"]=mc2[1].text_input("An. Batch",mb.get("analytical_batch",""),key=f"mbab_{mi}")
                mb["matrix"]=mc2[2].selectbox("Matrix",["Water","Soil","Air","Other"],key=f"mbmx_{mi}")
                mb["units"]=mc2[3].text_input("Units",mb.get("units",_unit_for_method(mb.get("analytical_method",""))),key=f"mbun_{mi}")
                nmbr=st.number_input("# results",0,50,len(mb.get("results",[])),key=f"nmbr_{mi}")
                while len(mb["results"]) < nmbr: mb["results"].append({"parameter":"","mdl":"","pql":"","mb_conc":"ND","qualifier":""})
                while len(mb["results"]) > nmbr: mb["results"].pop()
                for ri, r in enumerate(mb["results"]):
                    rc=st.columns(5)
                    r["parameter"] = _analyte_selectbox(rc[0], "Param", r.get("parameter",""), mb.get("analytical_method",""), f"mbrp_{mi}_{ri}")
                    r["mdl"]=rc[1].text_input("MDL",r.get("mdl",""),key=f"mbrm_{mi}_{ri}")
                    r["pql"]=rc[2].text_input("PQL",r.get("pql",""),key=f"mbrpq_{mi}_{ri}")
                    r["mb_conc"]=rc[3].text_input("MB Conc.",r.get("mb_conc","ND"),key=f"mbrc_{mi}_{ri}")
                    r["qualifier"] = _qualifier_selectbox(rc[4], "Qual", r.get("qualifier",""), f"mbrqu_{mi}_{ri}")

        st.markdown('<div class="sec-hdr">LCS/LCSD Batches</div>', unsafe_allow_html=True)
        lbs = st.session_state.lcs_batches
        nlcs = st.number_input("# LCS batches",0,20,len(lbs),key="nlcs")
        _empty_lcs = {"prep_method":"","analytical_method":"","prep_date":None,
                      "analyzed_date":None,"prep_batch":"","analytical_batch":"",
                      "matrix":"Water","units":"mg/L","results":[]}
        while len(lbs) < nlcs: lbs.append(copy.deepcopy(_empty_lcs))
        while len(lbs) > nlcs: lbs.pop()
        for li, lcs_b in enumerate(lbs):
            with st.expander(f"LCS Batch {li+1}: {lcs_b.get('prep_method','')}"):
                lc=st.columns(4)
                lcs_b["prep_method"]=lc[0].text_input("Prep",lcs_b.get("prep_method",""),key=f"lpm_{li}")
                lcs_b["analytical_method"] = _method_selectbox(lc[1], "Analytical", lcs_b.get("analytical_method",""), f"lam_{li}")
                lcs_b["prep_date"]=lc[2].date_input("Prep Date", _safe_date(lcs_b.get("prep_date")), key=f"lpd_{li}")
                lcs_b["analyzed_date"]=lc[3].date_input("Analyzed Date", _safe_date(lcs_b.get("analyzed_date")), key=f"lad_{li}")
                lc2=st.columns(4)
                lcs_b["prep_batch"]=lc2[0].text_input("Prep Batch",lcs_b.get("prep_batch",""),key=f"lpb_{li}")
                lcs_b["analytical_batch"]=lc2[1].text_input("An. Batch",lcs_b.get("analytical_batch",""),key=f"lab_{li}")
                lcs_b["matrix"]=lc2[2].selectbox("Matrix",["Water","Soil","Air","Other"],key=f"lmx_{li}")
                lcs_b["units"]=lc2[3].text_input("Units",lcs_b.get("units",_unit_for_method(lcs_b.get("analytical_method",""))),key=f"lun_{li}")
                nlr=st.number_input("# results",0,50,len(lcs_b.get("results",[])),key=f"nlr_{li}")
                _empty_lr = {"parameter":"","mdl":"","pql":"","spike_conc":"","lcs_recovery":"",
                             "lcsd_recovery":"","rpd":"","recovery_limits":"80-120","rpd_limits":"20","qualifier":""}
                while len(lcs_b["results"]) < nlr: lcs_b["results"].append(copy.deepcopy(_empty_lr))
                while len(lcs_b["results"]) > nlr: lcs_b["results"].pop()
                for ri, r in enumerate(lcs_b["results"]):
                    rc=st.columns([2,1,1,1,1,1,1,1,1.2,0.8])
                    r["parameter"] = _analyte_selectbox(rc[0], "Param", r.get("parameter",""), lcs_b.get("analytical_method",""), f"lrp_{li}_{ri}")
                    r["mdl"]=rc[1].text_input("MDL",r.get("mdl",""),key=f"lrm_{li}_{ri}")
                    r["pql"]=rc[2].text_input("PQL",r.get("pql",""),key=f"lrpq_{li}_{ri}")
                    r["spike_conc"]=rc[3].text_input("Spike",r.get("spike_conc",""),key=f"lrs_{li}_{ri}")
                    r["lcs_recovery"]=rc[4].text_input("LCS%",r.get("lcs_recovery",""),key=f"lrlcs_{li}_{ri}")
                    r["lcsd_recovery"]=rc[5].text_input("LCSD%",r.get("lcsd_recovery",""),key=f"lrlcsd_{li}_{ri}")
                    r["rpd"]=rc[6].text_input("RPD",r.get("rpd",""),key=f"lrrpd_{li}_{ri}")
                    r["recovery_limits"]=rc[7].text_input("RecLim",r.get("recovery_limits","80-120"),key=f"lrrl_{li}_{ri}")
                    r["rpd_limits"]=rc[8].text_input("RPDLim",r.get("rpd_limits","20"),key=f"lrrpl_{li}_{ri}")
                    r["qualifier"] = _qualifier_selectbox(rc[9], "Q", r.get("qualifier",""), f"lrq_{li}_{ri}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: Receipt & Login — with date/time pickers
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown('<div class="sec-hdr">Sample Receipt Checklist</div>', unsafe_allow_html=True)
        rcd = st.session_state.receipt
        rc1, rc2 = st.columns(2)
        with rc1:
            rcd["date_received_receipt"]=st.date_input("Date Received", _safe_date(rcd.get("date_received_receipt")), key="rdt_d")
            rcd["time_received_receipt"]=st.time_input("Time Received", _safe_time(rcd.get("time_received_receipt")), key="rdt_t")
            rcd["received_by"]=st.text_input("Received By",rcd["received_by"],key="rrb")
            rcd["carrier_name"]=st.text_input("Carrier",rcd["carrier_name"],key="rcn")
        with rc2:
            yn = ["Yes","No","Not Present","N/A"]
            rcd["coc_present"]=st.selectbox("CoC present?",yn,index=yn.index(rcd.get("coc_present","Yes")),key="rcp")
            rcd["coc_signed"]=st.selectbox("CoC signed?",yn,index=yn.index(rcd.get("coc_signed","Yes")),key="rcs")
            rcd["coc_agrees"]=st.selectbox("CoC agrees?",yn,index=yn.index(rcd.get("coc_agrees","Yes")),key="rca")
        rc3, rc4 = st.columns(2)
        with rc3:
            rcd["custody_seals_bottles"]=st.selectbox("Seals on bottles?",yn,index=yn.index(rcd.get("custody_seals_bottles","Not Present")),key="rcsb")
            rcd["cooler_good"]=st.selectbox("Cooler good?",yn,index=0,key="rcg")
            rcd["proper_container"]=st.selectbox("Proper containers?",yn,index=0,key="rpc")
            rcd["containers_intact"]=st.selectbox("Containers intact?",yn,index=0,key="rci")
        with rc4:
            rcd["sufficient_volume"]=st.selectbox("Sufficient volume?",yn,index=0,key="rsv")
            rcd["within_holding_time"]=st.selectbox("Within holding time?",yn,index=0,key="rwh")
            rcd["temp_compliance"]=st.selectbox("Temp compliance?",["Yes","No"],key="rtc")
            rcd["temperature"]=st.text_input("Temperature (°C)",rcd["temperature"],key="rtemp")
        rcd["voa_headspace"]=st.selectbox("VOA headspace?",["No VOA vials submitted","Yes","No"],key="rvoa")
        rcd["ph_acceptable"]=st.selectbox("pH acceptable?",["Yes","No"],key="rph")
        rcd["receipt_comments"]=st.text_area("Receipt Comments",rcd["receipt_comments"],key="rcom",height=60)

        st.divider()
        st.markdown('<div class="sec-hdr">Login Summary</div>', unsafe_allow_html=True)
        ls = st.session_state.login_summary
        lc1, lc2 = st.columns(2)
        with lc1:
            ls["qc_level"]=st.selectbox("QC Level",["I","II","III","IV"],index=1,key="lsqc")
            ls["report_due_date"]=st.date_input("Report Due Date", _safe_date(ls.get("report_due_date")), key="lsrd")
        with lc2:
            ls["tat_requested"]=st.selectbox("TAT",["Standard (5-10 Day)","1-Day Rush","2-Day Rush","3-Day Rush","4-Day Rush"],key="lstat")
            ls["date_received_login"]=st.date_input("Date Received (Login)", _safe_date(ls.get("date_received_login")), key="lsdr")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5: Generate COA
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[4]:
        st.markdown('<div class="sec-hdr">Generate COA PDF</div>', unsafe_allow_html=True)
        nsp = len(st.session_state.samples)
        total_est = 3 + nsp + 5 + 1
        st.session_state.total_page_count = total_est
        st.info(f"Estimated pages: **{total_est}**")

        # TNI compliance checklist
        with st.expander("✅ TNI/ELAP Compliance Check", expanded=False):
            checks = [
                ("Lab name & address on header", True),
                ("ELAP accreditation number", bool(st.session_state.elap_number and st.session_state.elap_number != "XXXX")),
                ("Client name & address", bool(st.session_state.client_contact)),
                ("Work Order / unique ID", bool(st.session_state.work_order)),
                ("Date of report", bool(st.session_state.report_date)),
                ("Date(s) of sample receipt", bool(st.session_state.date_received)),
                ("Sample IDs (lab + client)", nsp > 0),
                ("Method identification", any(r.get("method") for s in st.session_state.samples for r in s.get("results",[]))),
                ("MDL & PQL reported", True),
                ("Units of measurement", True),
                ("Date/time of analysis (≤72hr HT)", True),
                ("Analyst identification", True),
                ("QC data (MB, LCS/LCSD)", len(st.session_state.mb_batches) > 0 or len(st.session_state.lcs_batches) > 0),
                ("Qualifiers & definitions page", True),
                ("Sample receipt checklist", True),
                ("Chain of Custody image", bool(st.session_state.coc_image_bytes)),
                ("Approved signature", bool(st.session_state.signature_bytes)),
                ("Non-accredited tests flagged (if any)", not st.session_state.has_non_accredited_tests or True),
                ("Subcontractor identified (if any)", not st.session_state.has_subcontracted or bool(st.session_state.subcontractor_lab)),
            ]
            for label, ok in checks:
                st.write(f"{'✅' if ok else '⚠️'} {label}")
            passed = sum(1 for _,ok in checks if ok)
            st.progress(passed / len(checks), text=f"{passed}/{len(checks)} items complete")

        with st.expander("📊 Summary", expanded=True):
            st.write(f"**WO:** {st.session_state.work_order} | **Client:** {st.session_state.client_company} | **Project:** {st.session_state.project_name}")
            st.write(f"**Samples:** {nsp} | **MB:** {len(st.session_state.mb_batches)} | **LCS:** {len(st.session_state.lcs_batches)}")
            st.write(f"**Logo:** {'✅' if st.session_state.logo_bytes else '❌ text'} | **Sig:** {'✅' if st.session_state.signature_bytes else '❌'} | **CoC:** {'✅' if st.session_state.coc_image_bytes else '❌'}")

        if st.button("🖨️  Generate COA PDF", type="primary", use_container_width=True):
            with st.spinner("Generating PDF..."):
                data = {}
                for k in ["elap_number","lab_phone_display","report_date","work_order","total_page_count",
                           "client_contact","client_company","client_address","client_city_state_zip",
                           "project_name","project_number","num_samples_text",
                           "approver_name","approver_title","approval_date",
                           "qc_met","method_blank_corrected","case_narrative_custom",
                           "has_non_accredited_tests","has_results_outside_cal",
                           "has_subcontracted","subcontractor_lab","sample_condition_notes",
                           "samples","mb_batches","lcs_batches","receipt","login_summary"]:
                    v = st.session_state.get(k,'')
                    data[k] = str(v) if isinstance(v, (date, datetime)) else v

                # Convert date fields to display strings
                data["date_received_text"] = _fmt_date(st.session_state.date_received)

                # Convert date objects deep inside samples/batches to strings for PDF
                for samp in data.get("samples", []):
                    samp["date_sampled"] = _fmt_datetime(samp.get("date_sampled"), samp.get("time_sampled"))
                    samp["disposal_date"] = _fmt_date(samp.get("disposal_date"))
                    for pg in samp.get("prep_groups", []):
                        pg["prep_date_time"] = _fmt_datetime(pg.get("prep_date"), pg.get("prep_time"))
                        for pr in pg.get("results", []):
                            pr["analyzed_time"] = _fmt_datetime(pr.get("analyzed_date"), pr.get("analyzed_time"))
                for mb in data.get("mb_batches", []):
                    mb["prep_date"] = _fmt_date(mb.get("prep_date"))
                    mb["analyzed_date"] = _fmt_date(mb.get("analyzed_date"))
                for lcs_b in data.get("lcs_batches", []):
                    lcs_b["prep_date"] = _fmt_date(lcs_b.get("prep_date"))
                    lcs_b["analyzed_date"] = _fmt_date(lcs_b.get("analyzed_date"))
                # Receipt dates
                rcd = data.get("receipt", {})
                rcd["date_time_received"] = _fmt_datetime(
                    rcd.get("date_received_receipt"), rcd.get("time_received_receipt"))
                # Login summary dates
                ls = data.get("login_summary", {})
                ls["date_received_login"] = _fmt_date(ls.get("date_received_login"))
                ls["report_due_date"] = _fmt_date(ls.get("report_due_date"))

                builder = KelpCOA(data, st.session_state.logo_bytes,
                                  st.session_state.signature_bytes, st.session_state.coc_image_bytes)
                pdf_bytes = builder.build()

            st.success(f"✅ COA generated — {len(pdf_bytes):,} bytes")
            wo = st.session_state.work_order or "DRAFT"
            fn = f"KELP_COA_{wo}_{date.today().strftime('%Y%m%d')}.pdf"
            st.download_button(f"⬇️ Download {fn}", pdf_bytes, fn, "application/pdf", use_container_width=True)
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px"></iframe>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
