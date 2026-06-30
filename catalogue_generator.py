"""
Shynex Green Solutions — Institutional Product Catalogue Generator
Generates a fully branded multi-page PDF from live D1 product data.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                 Paragraph, Spacer, Table, TableStyle,
                                 PageBreak, HRFlowable, NextPageTemplate)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.flowables import Flowable
import io, datetime, re
from collections import OrderedDict

# ── Page geometry ──────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4          # 595.27 × 841.89 pt
LM = RM = 14 * mm
TM = 16 * mm
BM = 14 * mm
W  = PAGE_W - LM - RM       # usable width ≈ 167 mm

# ── Brand colours ──────────────────────────────────────────────────────────────
C_GREEN   = colors.HexColor("#1b6e2e")
C_GREEN2  = colors.HexColor("#145224")
C_GREEN3  = colors.HexColor("#0d3d1a")
C_GLITE   = colors.HexColor("#e8f5e9")
C_GLITE2  = colors.HexColor("#f1f8f2")
C_AMBER   = colors.HexColor("#f57f17")
C_AMBER2  = colors.HexColor("#ffe082")
C_WHITE   = colors.white
C_BLACK   = colors.HexColor("#1a1a1a")
C_GREY    = colors.HexColor("#718096")
C_DGREY   = colors.HexColor("#4a5568")
C_LINE    = colors.HexColor("#c8e6c9")
C_LINE2   = colors.HexColor("#e2e8f0")

# ── Category accent colours ────────────────────────────────────────────────────
CAT_COLORS = {
    "CLEANING CHEMICALS & DETERGENTS":  colors.HexColor("#1b6e2e"),
    "CLEANING EQUIPMENT & TOOLS":       colors.HexColor("#1565c0"),
    "TISSUE & PAPER HYGIENE":           colors.HexColor("#e65100"),
    "DUSTBINS & WASTE MANAGEMENT":      colors.HexColor("#6a1b9a"),
    "AIR FRESHENERS & PEST CONTROL":    colors.HexColor("#00796b"),
    "DISPOSABLE ITEMS":                 colors.HexColor("#c62828"),
    "PACKAGING MATERIALS":              colors.HexColor("#827717"),
    "MATS & FLOOR COVERINGS":           colors.HexColor("#33691e"),
    "PLASTIC UTILITY ITEMS":            colors.HexColor("#01579b"),
    "BULK/CONTRACT SUPPLY":             colors.HexColor("#4e342e"),
}

CAT_ORDER = [
    "CLEANING CHEMICALS & DETERGENTS",
    "CLEANING EQUIPMENT & TOOLS",
    "TISSUE & PAPER HYGIENE",
    "DUSTBINS & WASTE MANAGEMENT",
    "AIR FRESHENERS & PEST CONTROL",
    "DISPOSABLE ITEMS",
    "PACKAGING MATERIALS",
    "MATS & FLOOR COVERINGS",
    "PLASTIC UTILITY ITEMS",
    "BULK/CONTRACT SUPPLY",
]

# ── Paragraph helpers ──────────────────────────────────────────────────────────
def _s(nm, **kw):  return ParagraphStyle(nm, fontName='Helvetica',      **kw)
def _sb(nm, **kw): return ParagraphStyle(nm, fontName='Helvetica-Bold', **kw)

def p(t,   **kw): return Paragraph(str(t), _s("_",    **kw))
def pb(t,  **kw): return Paragraph(str(t), _sb("_b",  **kw))
def pc(t,  **kw): return Paragraph(str(t), _s("_c",   alignment=TA_CENTER, **kw))
def pbc(t, **kw): return Paragraph(str(t), _sb("_bc", alignment=TA_CENTER, **kw))
def pr(t,  **kw): return Paragraph(str(t), _s("_r",   alignment=TA_RIGHT,  **kw))
def pbr(t, **kw): return Paragraph(str(t), _sb("_br", alignment=TA_RIGHT,  **kw))


def _clean(text):
    """Fix UTF-8 mojibake artifacts that appear as â, Ã, etc."""
    text = str(text)
    # en dash / em dash variants
    text = text.replace("â", "–")
    text = text.replace("â", "—")
    text = text.replace("â", "–")
    text = text.replace("â", "—")
    # common standalone artifact: â followed by space
    text = re.sub(r'â\s', '– ', text)
    text = text.replace("â", "–")
    text = text.replace("Ã—", "×")
    text = text.replace("Ã", "×")
    # Strip non-printable except common unicode
    text = ''.join(c for c in text if c >= ' ' or c in '\t\n')
    return text.strip()


def _wrap_name(name, max_chars=36):
    """Split name into up to 2 lines for card display."""
    if len(name) <= max_chars:
        return name, ''
    words = name.split(' ')
    line1 = ''
    for i, w in enumerate(words):
        candidate = (line1 + ' ' + w).strip()
        if len(candidate) <= max_chars:
            line1 = candidate
        else:
            line2 = ' '.join(words[i:])
            if len(line2) > max_chars:
                line2 = line2[:max_chars - 1] + '…'
            return line1, line2
    return line1, ''


# ── Page callbacks ─────────────────────────────────────────────────────────────
def _on_interior_page(canv, doc):
    canv.saveState()

    # Header bar (top of page)
    canv.setFillColor(C_GREEN)
    canv.rect(LM, PAGE_H - TM + 1.5 * mm, W, 11 * mm, fill=1, stroke=0)
    canv.setFillColor(C_AMBER)
    canv.rect(LM, PAGE_H - TM + 1.5 * mm, 4 * mm, 11 * mm, fill=1, stroke=0)
    canv.setFillColor(C_WHITE)
    canv.setFont("Helvetica-Bold", 8.5)
    canv.drawString(LM + 7 * mm, PAGE_H - TM + 6 * mm, "SHYNEX GREEN SOLUTIONS")
    canv.setFont("Helvetica", 7.5)
    canv.drawRightString(LM + W, PAGE_H - TM + 6 * mm,
                         "Institutional Product Catalogue  2026")

    # Footer line + text
    canv.setStrokeColor(C_LINE)
    canv.setLineWidth(0.5)
    canv.line(LM, BM + 3.5 * mm, LM + W, BM + 3.5 * mm)
    canv.setFillColor(C_GREY)
    canv.setFont("Helvetica", 6.5)
    canv.drawString(LM, BM + 1 * mm,
        "www.shynexgreensolutions.com  |  +91 81252 42828  |  customerservices@shynexgreensolutions.com")
    canv.setFillColor(C_GREEN)
    canv.setFont("Helvetica-Bold", 8)
    canv.drawRightString(LM + W, BM + 1 * mm, f"Page  {doc.page}")

    canv.restoreState()


def _on_cover_page(canv, doc):
    pass  # cover draws itself


# ── Cover page ─────────────────────────────────────────────────────────────────
class CoverPage(Flowable):
    def wrap(self, aw, ah):
        return (PAGE_W, PAGE_H)

    def draw(self):
        c = self.canv

        # Full green background
        c.setFillColor(C_GREEN)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # Dark overlay — top half
        c.setFillColor(C_GREEN3)
        c.rect(0, PAGE_H * 0.52, PAGE_W, PAGE_H * 0.48, fill=1, stroke=0)

        # Decorative circles (top-right corner)
        c.setFillColor(C_GREEN2)
        c.circle(PAGE_W - 3 * mm, PAGE_H - 3 * mm, 68 * mm, fill=1, stroke=0)
        c.setFillColor(C_GREEN3)
        c.circle(PAGE_W - 3 * mm, PAGE_H - 3 * mm, 52 * mm, fill=1, stroke=0)
        c.setFillColor(C_GREEN)
        c.circle(PAGE_W - 3 * mm, PAGE_H - 3 * mm, 38 * mm, fill=1, stroke=0)

        # Decorative circle bottom-left
        c.setFillColor(C_GREEN2)
        c.circle(8 * mm, 8 * mm, 40 * mm, fill=1, stroke=0)

        # Amber left stripe
        c.setFillColor(C_AMBER)
        c.rect(0, 0, 7 * mm, PAGE_H, fill=1, stroke=0)

        # Amber horizontal divider
        c.setFillColor(C_AMBER)
        c.rect(7 * mm, PAGE_H * 0.43, PAGE_W - 7 * mm, 2.5 * mm, fill=1, stroke=0)

        # Dark contact band (bottom)
        c.setFillColor(C_GREEN3)
        c.rect(0, 0, PAGE_W, 40 * mm, fill=1, stroke=0)
        c.setFillColor(C_AMBER)
        c.rect(0, 0, 7 * mm, 40 * mm, fill=1, stroke=0)   # keep amber stripe

        # ── Text content ──────────────────────────────────────────────────────

        # Company name
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(20 * mm, PAGE_H * 0.74, "SHYNEX GREEN")
        c.setFont("Helvetica-Bold", 32)
        c.drawString(20 * mm, PAGE_H * 0.68, "SOLUTIONS")

        # Tagline
        c.setFillColor(C_AMBER)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, PAGE_H * 0.63, "Clean.   Green.   Professional.")

        # Catalogue heading
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(20 * mm, PAGE_H * 0.54, "INSTITUTIONAL PRODUCT CATALOGUE")

        # Year badge
        c.setFillColor(C_AMBER)
        c.roundRect(20 * mm, PAGE_H * 0.475, 23 * mm, 8 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(23.5 * mm, PAGE_H * 0.49, str(datetime.date.today().year))

        # Products / categories pill
        c.setFillColor(C_WHITE)
        c.roundRect(47 * mm, PAGE_H * 0.475, 62 * mm, 8 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(C_GREEN)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50 * mm, PAGE_H * 0.49, "107+ Products  |  9 Categories")

        # GSTIN / MSME line
        c.setFillColor(C_GLITE)
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, PAGE_H * 0.44,
                     "GSTIN: 36FFGPB8631L1Z6  |  MSME Registered  |  Hyderabad, Telangana")

        # ── Bottom contact strip ───────────────────────────────────────────────
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(20 * mm, 28 * mm, "www.shynexgreensolutions.com")

        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, 20 * mm, "+91 81252 42828")
        c.drawString(65 * mm, 20 * mm, "customerservices@shynexgreensolutions.com")

        c.setFillColor(C_GLITE)
        c.setFont("Helvetica", 7.5)
        c.drawString(20 * mm, 13 * mm,
                     "H.No.5-12/100/140/T NC Sun Rise Apts, Sai Ambica Colony, Ameenpur, Hyderabad – 502032")

        c.setFillColor(C_AMBER2)
        c.setFont("Helvetica", 7)
        c.drawString(20 * mm, 7 * mm,
                     "Manufactured by: Abhishii Life Sciences Pvt. Ltd.")


# ── Back cover ─────────────────────────────────────────────────────────────────
class BackCoverPage(Flowable):
    def wrap(self, aw, ah):
        return (PAGE_W, PAGE_H)

    def draw(self):
        c = self.canv

        # Full green background
        c.setFillColor(C_GREEN)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # Decorative concentric circles (centre-top)
        c.setFillColor(C_GREEN2)
        c.circle(PAGE_W / 2, PAGE_H * 0.80, 80 * mm, fill=1, stroke=0)
        c.setFillColor(C_GREEN3)
        c.circle(PAGE_W / 2, PAGE_H * 0.80, 60 * mm, fill=1, stroke=0)
        c.setFillColor(C_GREEN)
        c.circle(PAGE_W / 2, PAGE_H * 0.80, 42 * mm, fill=1, stroke=0)

        # Bottom circle
        c.setFillColor(C_GREEN2)
        c.circle(15 * mm, 15 * mm, 35 * mm, fill=1, stroke=0)

        # Amber right stripe
        c.setFillColor(C_AMBER)
        c.rect(PAGE_W - 7 * mm, 0, 7 * mm, PAGE_H, fill=1, stroke=0)

        # Amber horizontal line
        c.setFillColor(C_AMBER)
        c.rect(0, PAGE_H * 0.46, PAGE_W - 7 * mm, 2.5 * mm, fill=1, stroke=0)

        # Dark footer band
        c.setFillColor(C_GREEN3)
        c.rect(0, 0, PAGE_W - 7 * mm, 30 * mm, fill=1, stroke=0)

        # Heading
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(PAGE_W / 2 - 3 * mm, PAGE_H * 0.79, "GET IN TOUCH")

        c.setFillColor(C_GLITE)
        c.setFont("Helvetica", 10)
        c.drawCentredString(PAGE_W / 2 - 3 * mm, PAGE_H * 0.73,
                            "Request a quote, place an order, or just say hello.")

        # Contact boxes
        contacts = [
            ("Phone",   "+91 81252 42828"),
            ("Email",   "customerservices@shynexgreensolutions.com"),
            ("Web",     "www.shynexgreensolutions.com"),
            ("Hours",   "Monday – Saturday  |  10:00 AM – 6:00 PM"),
        ]
        by = PAGE_H * 0.60
        for label, val in contacts:
            c.setFillColor(C_GREEN2)
            c.roundRect(LM, by - 7.5 * mm, PAGE_W - LM - RM - 7 * mm,
                        10 * mm, 2 * mm, fill=1, stroke=0)
            c.setFillColor(C_AMBER)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(LM + 4 * mm, by - 2.5 * mm, f"{label}:")
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica", 9)
            c.drawString(LM + 22 * mm, by - 2.5 * mm, val)
            by -= 15 * mm

        # Address line
        c.setFillColor(C_GLITE)
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(PAGE_W / 2 - 3 * mm, PAGE_H * 0.14,
            "H.No.5-12/100/140/T NC Sun Rise Apts, Sai Ambica Colony, Ameenpur, Hyderabad – 502032")

        # Tagline
        c.setFillColor(C_AMBER)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(PAGE_W / 2 - 3 * mm, PAGE_H * 0.08,
                            "Clean.   Green.   Professional.")

        # Legal footer
        c.setFillColor(C_GLITE)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(PAGE_W / 2 - 3 * mm, PAGE_H * 0.038,
            "Manufactured by: Abhishii Life Sciences Pvt. Ltd.  |  "
            "GSTIN: 36FFGPB8631L1Z6  |  MSME Registered")


# ── Category banner ────────────────────────────────────────────────────────────
class CategoryBanner(Flowable):
    def __init__(self, name, number, count, accent):
        Flowable.__init__(self)
        self._name   = name
        self._number = number
        self._count  = count
        self._accent = accent

    def wrap(self, aw, ah):
        return (W, 30 * mm)

    def draw(self):
        c = self.canv
        w = W
        h = 30 * mm

        # Main green background
        c.setFillColor(C_GREEN)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Right accent panel
        c.setFillColor(self._accent)
        c.rect(w * 0.68, 0, w * 0.32, h, fill=1, stroke=0)

        # Left amber stripe
        c.setFillColor(C_AMBER)
        c.rect(0, 0, 5 * mm, h, fill=1, stroke=0)

        # Number badge (amber circle)
        cx, cy = 17 * mm, h / 2
        c.setFillColor(C_AMBER)
        c.circle(cx, cy, 10 * mm, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(cx, cy - 5, str(self._number).zfill(2))

        # Category name
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(32 * mm, h * 0.63, self._name)

        # Product count sub-label
        c.setFillColor(C_AMBER2)
        c.setFont("Helvetica", 9)
        c.drawString(32 * mm, h * 0.28, f"{self._count} products in this category")

        # Diagonal decorative lines on right accent panel
        c.setStrokeColor(C_GREEN2)
        c.setLineWidth(1.2)
        for i in range(7):
            xs = w * 0.70 + i * 7 * mm
            c.line(xs, 0, xs - 8 * mm, h)

        # MSME / GSTIN small text
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 7)
        c.drawRightString(w - 4 * mm, h * 0.65, "MSME REGISTERED")
        c.setFillColor(C_AMBER2)
        c.setFont("Helvetica", 6.5)
        c.drawRightString(w - 4 * mm, h * 0.38, "GSTIN: 36FFGPB8631L1Z6")


# ── Product card ───────────────────────────────────────────────────────────────
CARD_W  = W / 2         # two-column grid
CARD_H  = 30 * mm       # fixed card height

class ProductCard(Flowable):
    def __init__(self, prod, accent):
        Flowable.__init__(self)
        self._prod   = prod
        self._accent = accent

    def wrap(self, aw, ah):
        return (CARD_W, CARD_H)

    def draw(self):
        c = self.canv
        w = CARD_W - 4 * mm    # inner card width (2mm margin each side)
        h = CARD_H - 3 * mm    # inner card height (1.5mm margin top+bottom)
        prod = self._prod

        name  = _clean(prod.get('name', ''))
        sku   = prod.get('sku', '')
        unit  = prod.get('unit', 'Nos')
        price = float(prod.get('price', 0))
        gst   = float(prod.get('gst_pct', 18))
        price_incl = price * (1 + gst / 100)

        # Translate so card has 2mm left margin and 1.5mm bottom margin
        c.saveState()
        c.translate(2 * mm, 1.5 * mm)

        # White card background with border
        c.setFillColor(C_WHITE)
        c.setStrokeColor(C_LINE)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 2 * mm, fill=1, stroke=1)

        # Accent header strip (top 8.5mm)
        header_h = 8.5 * mm
        c.setFillColor(self._accent)
        c.roundRect(0, h - header_h, w, header_h, 2 * mm, fill=1, stroke=0)
        # Fill lower half of rounded rect to make it flat at the bottom of header
        c.rect(0, h - header_h, w, header_h / 2, fill=1, stroke=0)

        # SKU in header
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(3 * mm, h - 5.5 * mm, sku)

        # Price badge (top-right of header)
        badge_w = 24 * mm
        c.setFillColor(C_AMBER)
        c.roundRect(w - badge_w - 2 * mm, h - 7.5 * mm,
                    badge_w, 6 * mm, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(w - badge_w / 2 - 2 * mm, h - 5 * mm,
                            f"Rs.{price:,.0f}")

        # Product name (body)
        line1, line2 = _wrap_name(name, max_chars=34)
        c.setFillColor(C_BLACK)
        if line2:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(3 * mm, h - 13 * mm, line1)
            c.setFont("Helvetica", 7.5)
            c.drawString(3 * mm, h - 17 * mm, line2)
        else:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(3 * mm, h - 14 * mm, line1)

        # Divider above footer
        c.setStrokeColor(C_LINE)
        c.setLineWidth(0.4)
        c.line(2 * mm, 8.5 * mm, w - 2 * mm, 8.5 * mm)

        # Footer area (light green tint)
        c.setFillColor(C_GLITE)
        c.roundRect(0, 0, w, 8 * mm, 2 * mm, fill=1, stroke=0)
        c.rect(0, 4 * mm, w, 4 * mm, fill=1, stroke=0)   # flatten top of rounded rect

        # Unit label
        c.setFillColor(C_DGREY)
        c.setFont("Helvetica", 7.5)
        c.drawString(3 * mm, 2.5 * mm, f"Unit: {unit}")

        # GST-inclusive price
        c.setFillColor(C_GREEN)
        c.setFont("Helvetica-Bold", 7)
        c.drawRightString(w - 2.5 * mm, 2.5 * mm,
                          f"Incl. GST ({int(gst)}%): Rs.{price_incl:,.0f}")

        c.restoreState()


def _build_product_grid(products, accent):
    """Returns a 2-column Table of ProductCards."""
    rows = []
    row  = []
    for prod in products:
        cell = Table([[ProductCard(prod, accent)]], colWidths=[CARD_W])
        cell.setStyle(TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        row.append(cell)
        if len(row) == 2:
            rows.append(row[:])
            row = []
    if row:
        empty = Table([['']], colWidths=[CARD_W], style=TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        row.append(empty)
        rows.append(row)

    grid = Table(rows, colWidths=[CARD_W, CARD_W])
    grid.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return grid


# ── Main entry point ───────────────────────────────────────────────────────────
def generate_catalogue_pdf(products_data):
    """
    products_data : list of dicts with keys sku, name, unit, price, gst_pct, category
    Returns       : bytes (PDF)
    """
    buf = io.BytesIO()

    # Group by category
    cats = OrderedDict()
    for prod in products_data:
        cat = prod.get("category", "UNCATEGORIZED").upper()
        cats.setdefault(cat, []).append(prod)

    sorted_cats = sorted(cats.keys(),
        key=lambda x: CAT_ORDER.index(x) if x in CAT_ORDER else 99)

    total_products = sum(len(cats[c]) for c in sorted_cats)

    # ── Document setup ────────────────────────────────────────────────────────
    doc = BaseDocTemplate(buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM)

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id='cover',
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)

    # Interior frame clears the 11mm header + 9mm footer
    interior_frame = Frame(LM, BM + 8 * mm, W,
                           PAGE_H - TM - BM - 20 * mm, id='interior')

    doc.addPageTemplates([
        PageTemplate(id='Cover',    frames=[cover_frame],    onPage=_on_cover_page),
        PageTemplate(id='Interior', frames=[interior_frame], onPage=_on_interior_page),
    ])

    story = []

    # ── 1. Cover ──────────────────────────────────────────────────────────────
    story.append(CoverPage())
    story.append(NextPageTemplate('Interior'))
    story.append(PageBreak())

    # ── 2. TOC ────────────────────────────────────────────────────────────────
    story.append(pb("TABLE OF CONTENTS",
        fontSize=15, textColor=C_GREEN, spaceAfter=2 * mm))
    story.append(HRFlowable(width="100%", thickness=2.5,
        color=C_AMBER, spaceAfter=3 * mm))

    toc_rows = [[
        pb("#",          fontSize=8.5, textColor=C_WHITE, alignment=TA_CENTER),
        pb("Category",   fontSize=8.5, textColor=C_WHITE),
        pb("Products",   fontSize=8.5, textColor=C_WHITE, alignment=TA_CENTER),
    ]]
    for i, cat in enumerate(sorted_cats, 1):
        toc_rows.append([
            pc(str(i),          fontSize=9.5, textColor=C_BLACK),
            p(cat.title(),      fontSize=9.5, textColor=C_BLACK),
            pc(str(len(cats[cat])), fontSize=9.5, textColor=C_BLACK),
        ])
    toc_rows.append([
        pc("", fontSize=9),
        pb("TOTAL PRODUCTS", fontSize=9.5, textColor=C_WHITE, alignment=TA_CENTER),
        pbc(str(total_products), fontSize=9.5, textColor=C_WHITE),
    ])

    toc_cmds = [
        ("BACKGROUND",    (0, 0),  (-1, 0),   C_GREEN),
        ("BACKGROUND",    (0, -1), (-1, -1),  C_GREEN),
        ("BOX",           (0, 0),  (-1, -1),  0.5, C_LINE),
        ("VALIGN",        (0, 0),  (-1, -1),  "MIDDLE"),
        ("TOPPADDING",    (0, 0),  (-1, -1),  5),
        ("BOTTOMPADDING", (0, 0),  (-1, -1),  5),
        ("LEFTPADDING",   (0, 0),  (-1, -1),  7),
        ("RIGHTPADDING",  (0, 0),  (-1, -1),  7),
    ]
    for idx in range(1, len(toc_rows) - 1):
        bg = C_WHITE if idx % 2 == 1 else C_GLITE
        toc_cmds.append(("BACKGROUND", (0, idx), (-1, idx), bg))
        toc_cmds.append(("LINEBELOW",  (0, idx), (-1, idx), 0.3, C_LINE))

    toc_tbl = Table(toc_rows, colWidths=[12 * mm, W - 32 * mm, 20 * mm])
    toc_tbl.setStyle(TableStyle(toc_cmds))
    story.append(toc_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── About panel ───────────────────────────────────────────────────────────
    about_tbl = Table([
        [pb("ABOUT SHYNEX GREEN SOLUTIONS",
            fontSize=10, textColor=C_WHITE),
         pb("GSTIN: 36FFGPB8631L1Z6",
            fontSize=8, textColor=C_AMBER2, alignment=TA_RIGHT)],
        [p("Shynex Green Solutions is a Hyderabad-based B2B institutional hygiene supply company "
           "serving hospitals, hotels, offices, and commercial establishments across Telangana. "
           "We supply cleaning chemicals, equipment, tissue & paper hygiene, waste management, "
           "and facility maintenance products — all manufactured by Abhishii Life Sciences Pvt. Ltd.",
           fontSize=8.5, textColor=C_BLACK, leading=13), ""],
    ], colWidths=[W * 0.65, W * 0.35])
    about_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  C_GREEN),
        ("BACKGROUND",    (0, 1), (-1, 1),  C_GLITE),
        ("SPAN",          (0, 1), (1, 1)),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_LINE),
    ]))
    story.append(about_tbl)
    story.append(Spacer(1, 3 * mm))

    # Highlights row
    highlights_data = [[
        pb("✔  MSME Registered",     fontSize=8.5, textColor=C_GREEN),
        pb("✔  GST Compliant",        fontSize=8.5, textColor=C_GREEN),
        pb("✔  24/7 AI Quotation",    fontSize=8.5, textColor=C_GREEN),
        pb("✔  Same-Day Response",    fontSize=8.5, textColor=C_GREEN),
    ]]
    hl_tbl = Table(highlights_data, colWidths=[W / 4] * 4)
    hl_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_GLITE),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_LINE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C_LINE),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
    ]))
    story.append(hl_tbl)
    story.append(PageBreak())

    # ── 3. Category sections ──────────────────────────────────────────────────
    for cat_num, cat_name in enumerate(sorted_cats, 1):
        products = cats[cat_name]
        accent   = CAT_COLORS.get(cat_name, C_GREEN)

        story.append(CategoryBanner(
            name=cat_name.title(),
            number=cat_num,
            count=len(products),
            accent=accent,
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(_build_product_grid(products, accent))
        story.append(PageBreak())

    # ── 4. Back cover ─────────────────────────────────────────────────────────
    story.append(NextPageTemplate('Cover'))
    story.append(PageBreak())
    story.append(BackCoverPage())

    doc.build(story)
    return buf.getvalue()
