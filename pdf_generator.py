from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, 
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

# ── EXACT colours extracted from SGS-EST125-Sample.pdf ───────────────────────
# Original: header = #002854 (navy). Replaced with Shynex green everywhere.
BRAND     = colors.HexColor("#1b6e2e")   # dark green — replaces #002854 navy
ROW_ALT   = colors.HexColor("#F5F7F9")   # alternating row bg (unchanged)
ROW_TOT   = colors.HexColor("#E8F5E9")   # total row bg (unchanged — already green)
LINE      = colors.HexColor("#E2E8F0")   # row divider lines (unchanged)
WHITE     = colors.white
BLACK     = colors.HexColor("#1a1a1a")
DGREY     = colors.HexColor("#4a5568")
GREY      = colors.HexColor("#718096")

def S(nm, **kw):  return ParagraphStyle(nm, fontName='Helvetica',      **kw)
def SB(nm, **kw): return ParagraphStyle(nm, fontName='Helvetica-Bold',  **kw)

def p(t,  **kw): return Paragraph(t, S("_",  **kw))
def pb(t, **kw): return Paragraph(t, SB("_b", **kw))
def pc(t, **kw): return Paragraph(t, S("_c",  alignment=TA_CENTER, **kw))
def pr(t, **kw): return Paragraph(t, S("_r",  alignment=TA_RIGHT,  **kw))
def pbc(t,**kw): return Paragraph(t, SB("_bc",alignment=TA_CENTER, **kw))
def pbr(t,**kw): return Paragraph(t, SB("_br",alignment=TA_RIGHT,  **kw))

def in_words(n):
    ones=["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine",
          "Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen",
          "Seventeen","Eighteen","Nineteen"]
    tens=["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
    def say(x):
        if x<20: return ones[x]
        if x<100: return tens[x//10]+(" "+ones[x%10] if x%10 else "")
        if x<1000: return ones[x//100]+" Hundred"+(" "+say(x%100) if x%100 else "")
        if x<100000: return say(x//1000)+" Thousand"+(" "+say(x%1000) if x%1000 else "")
        if x<10000000: return say(x//100000)+" Lakh"+(" "+say(x%100000) if x%100000 else "")
        return say(x//10000000)+" Crore"+(" "+say(x%10000000) if x%10000000 else "")
    return say(int(round(n)))+" Rupees Only"

def generate_estimate_pdf(est_no, date_str, customer_name, customer_address,
                           items, output_path=None, valid_for="30 Days", terms=None):

    PAGE_W, PAGE_H = A4
    LM = RM = 14*mm
    W  = PAGE_W - LM - RM

    doc = SimpleDocTemplate(output_path, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=10*mm, bottomMargin=10*mm)
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # 1. HEADER BAR — dark green background, white text, NO logo
    #    Exact match to sample: company name bold white left,
    #    address lines right-aligned white
    # ══════════════════════════════════════════════════════════════════════════
    co_name = pb("SHYNEX GREEN SOLUTIONS",
                 fontSize=14, textColor=WHITE, leading=17)
    
    addr = p("H.No.5-12/100/140/T NC Sun Rise Apartments<br/>"
             "Sai Ambica Colony, Ameenpur, Hyderabad – 502032<br/>"
             "Ph: +91 8125242828 | nagaraju.v@shynexgreensolutions.com<br/>"
             "GSTIN: 36FFGPB8631L1Z6 | State: 36-Telangana",
             fontSize=8, textColor=WHITE, leading=12, alignment=TA_RIGHT)

    hdr_tbl = Table([[co_name, addr]], colWidths=[W*0.45, W*0.55])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), BRAND),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
        ("TOPPADDING",   (0,0),(-1,-1), 14),
        ("BOTTOMPADDING",(0,0),(-1,-1), 14),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 2. E S T I M A T E title — centred, dark green, no background
    # ══════════════════════════════════════════════════════════════════════════
    story.append(pb("E S T I M A T E",
        fontSize=13, textColor=BRAND, alignment=TA_CENTER, spaceAfter=4))

    # ══════════════════════════════════════════════════════════════════════════
    # 3. Meta box — light grey bg, Estimate For left | Estimate Details right
    # ══════════════════════════════════════════════════════════════════════════
    # Left column
    cust_lines = [
        p("Estimate For", fontSize=8, textColor=GREY),
        Spacer(1,3),
        pb(customer_name, fontSize=10, textColor=BLACK),
    ]
    if customer_address:
        cust_lines.append(p(customer_address, fontSize=8,
                            textColor=DGREY, leading=12))

    # Right column — key/value inner table
    kv = Table([
        [p("Estimate No.", fontSize=8, textColor=GREY, alignment=TA_RIGHT),
         pb(est_no,        fontSize=8, textColor=BLACK)],
        [p("Date",         fontSize=8, textColor=GREY, alignment=TA_RIGHT),
         pb(date_str,      fontSize=8, textColor=BLACK)],
        [p("Valid For",    fontSize=8, textColor=GREY, alignment=TA_RIGHT),
         pb(valid_for,     fontSize=8, textColor=BLACK)],
    ], colWidths=[24*mm, 38*mm])
    kv.setStyle(TableStyle([
        ("TOPPADDING",   (0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",  (0,0),(-1,-1),0),
        ("RIGHTPADDING", (0,0),(-1,-1),0),
    ]))
    det_lines = [
        p("Estimate Details", fontSize=8, textColor=GREY, alignment=TA_RIGHT),
        Spacer(1,3),
        kv,
    ]

    meta = Table([[cust_lines, det_lines]], colWidths=[W*0.52, W*0.48])
    meta.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), ROW_ALT),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("BOX",          (0,0),(-1,-1), 0.5, LINE),
    ]))
    story.append(meta)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 4. Items table
    # ══════════════════════════════════════════════════════════════════════════
    CW = [8*mm, 57*mm, 21*mm, 14*mm, 12*mm, 22*mm, 28*mm, 23*mm]

    def th(t, align=TA_CENTER):
        return Paragraph(f"<b>{t}</b>",
            SB("th", fontSize=8, textColor=WHITE, alignment=align, leading=10))

    headers = [th("#"), th("Item Name", TA_LEFT), th("HSN/SAC"),
               th("Qty"), th("Unit"), th("Price/Unit"), th("GST"), th("Amount")]

    subtotal = 0.0
    total_gst = 0.0
    rows = [headers]

    for i, it in enumerate(items, 1):
        base    = it['price'] * it['qty']
        gst_amt = round(base * it['gst_pct'] / 100, 2)
        amount  = base + gst_amt
        subtotal  += base
        total_gst += gst_amt
        rows.append([
            pc(str(i),      fontSize=8, textColor=BLACK, leading=11),
            p(it['name'],   fontSize=8, textColor=BLACK, leading=11),
            pc(str(it['hsn']), fontSize=8, textColor=BLACK, leading=11),
            pc(str(it['qty']), fontSize=8, textColor=BLACK, leading=11),
            pc(it.get('unit','Nos'), fontSize=8, textColor=BLACK, leading=11),
            pr(f"Rs.{it['price']:,.2f}",  fontSize=8, textColor=BLACK, leading=11),
            pr(f"Rs.{gst_amt:,.2f} ({it['gst_pct']}%)", fontSize=8, textColor=BLACK, leading=11),
            pr(f"Rs.{amount:,.2f}", fontSize=8, textColor=BLACK, leading=11),
        ])

    total_qty = sum(it['qty'] for it in items)
    grand_raw = subtotal + total_gst
    grand_int = round(grand_raw)
    round_off = grand_int - grand_raw

    rows.append([
        p("", fontSize=8),
        pb(f"{total_qty} items", fontSize=8, textColor=BLACK),
        p("", fontSize=8), p("", fontSize=8), p("", fontSize=8), p("", fontSize=8),
        pbr(f"Rs.{total_gst:,.2f}", fontSize=8, textColor=BLACK),
        pbr(f"Rs.{grand_raw:,.2f}", fontSize=8, textColor=BLACK),
    ])

    tbl = Table(rows, colWidths=CW, repeatRows=1)
    cmds = [
        ("BACKGROUND",   (0,0),(-1,0),   BRAND),
        ("LINEBELOW",    (0,0),(-1,0),   0.5, LINE),
        ("BACKGROUND",   (0,-1),(-1,-1), ROW_TOT),
        ("LINEABOVE",    (0,-1),(-1,-1), 1.0, BRAND),
        ("BOX",          (0,0),(-1,-1),  0.5, LINE),
        ("LEFTPADDING",  (0,0),(-1,-1),  4),
        ("RIGHTPADDING", (0,0),(-1,-1),  4),
        ("TOPPADDING",   (0,0),(-1,-1),  5),
        ("BOTTOMPADDING",(0,0),(-1,-1),  5),
        ("VALIGN",       (0,0),(-1,-1),  "MIDDLE"),
    ]
    for idx in range(1, len(rows)-1):
        bg = WHITE if idx % 2 == 1 else ROW_ALT
        cmds.append(("BACKGROUND", (0,idx),(-1,idx), bg))
        cmds.append(("LINEBELOW",  (0,idx),(-1,idx), 0.3, LINE))
    tbl.setStyle(TableStyle(cmds))
    story.append(tbl)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 5. Tax Breakdown + Amounts
    # ══════════════════════════════════════════════════════════════════════════
    half_gst = total_gst / 2

    tax_tbl = Table([
        [pb("Tax Breakdown", fontSize=8, textColor=WHITE), "","",""],
        [pb("Tax Type",        fontSize=8, textColor=BLACK),
         pbr("Taxable Amount", fontSize=8, textColor=BLACK),
         pbc("Rate",           fontSize=8, textColor=BLACK),
         pbr("Tax Amount",     fontSize=8, textColor=BLACK)],
        [p("SGST",fontSize=8,textColor=BLACK),
         pr(f"Rs.{subtotal:,.2f}",  fontSize=8,textColor=BLACK),
         pc("9%",fontSize=8,textColor=BLACK),
         pr(f"Rs.{half_gst:,.2f}", fontSize=8,textColor=BLACK)],
        [p("CGST",fontSize=8,textColor=BLACK),
         pr(f"Rs.{subtotal:,.2f}",  fontSize=8,textColor=BLACK),
         pc("9%",fontSize=8,textColor=BLACK),
         pr(f"Rs.{half_gst:,.2f}", fontSize=8,textColor=BLACK)],
    ], colWidths=[22*mm, 28*mm, 13*mm, 22*mm])
    tax_tbl.setStyle(TableStyle([
        ("SPAN",         (0,0),(-1,0)),
        ("BACKGROUND",   (0,0),(-1,0),  BRAND),
        ("BACKGROUND",   (0,1),(-1,1),  ROW_ALT),
        ("BACKGROUND",   (0,2),(-1,2),  WHITE),
        ("BACKGROUND",   (0,3),(-1,3),  ROW_ALT),
        ("LINEBELOW",    (0,1),(-1,1),  0.5, LINE),
        ("LINEBELOW",    (0,2),(-1,3),  0.3, LINE),
        ("BOX",          (0,0),(-1,-1), 0.5, LINE),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))

    amt_tbl = Table([
        [pb("Amounts", fontSize=8, textColor=WHITE), ""],
        [p("Sub Total",  fontSize=8,textColor=BLACK),
         pr(f"Rs.{grand_raw:,.2f}", fontSize=8,textColor=BLACK)],
        [p("Round Off",  fontSize=8,textColor=BLACK),
         pr(f"- Rs.{abs(round_off):.2f}", fontSize=8,textColor=BLACK)],
        [pb("TOTAL", fontSize=9, textColor=WHITE),
         pbr(f"Rs.{grand_int:,.0f}", fontSize=9, textColor=WHITE)],
    ], colWidths=[30*mm, 28*mm])
    amt_tbl.setStyle(TableStyle([
        ("SPAN",         (0,0),(-1,0)),
        ("BACKGROUND",   (0,0),(-1,0),  BRAND),
        ("BACKGROUND",   (0,1),(-1,1),  WHITE),
        ("BACKGROUND",   (0,2),(-1,2),  ROW_ALT),
        ("BACKGROUND",   (0,3),(-1,3),  BRAND),
        ("LINEBELOW",    (0,1),(-1,2),  0.3, LINE),
        ("BOX",          (0,0),(-1,-1), 0.5, LINE),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))

    gap = W - 85*mm - 58*mm
    story.append(Table([[tax_tbl, Spacer(gap,1), amt_tbl]],
        colWidths=[85*mm, gap, 58*mm],
        style=TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
        ])))
    story.append(Spacer(1, 3*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 6. Amount in Words
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Table([[
        pb("Estimate Amount In Words", fontSize=8, textColor=BLACK),
        p(in_words(grand_int), fontSize=8, textColor=BLACK),
    ]], colWidths=[52*mm, W-52*mm],
    style=TableStyle([
        ("BACKGROUND",  (0,0),(0,0),   ROW_ALT),
        ("BACKGROUND",  (1,0),(1,0),   WHITE),
        ("BOX",         (0,0),(-1,-1), 0.5, LINE),
        ("LINERIGHT",   (0,0),(0,0),   0.5, LINE),
        ("LEFTPADDING", (0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
    ])))
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 7. Bank / Terms / Signatory
    # ══════════════════════════════════════════════════════════════════════════
    if terms is None:
        terms = ["1. Payment: 100% advance before dispatch.",
                 "2. Quotation valid for 15 days from date of issue.",
                 "3. Prices are exclusive of delivery charges.",
                 "4. GST as applicable.",
                 "Thanks for doing business with us!"]

    foot = Table([[
        p("<b>Bank Details</b><br/>"
          "Name : SHYNEX GREEN SOLUTIONS<br/>"
          "Account No. : 16050200005400<br/>"
          "IFSC Code : FDRL0001605<br/>"
          "Bank : Federal Bank",
          fontSize=8, textColor=BLACK, leading=14),
        p("<b>Terms &amp; Conditions</b><br/>" + "<br/>".join(terms),
          fontSize=7.5, textColor=BLACK, leading=12),
        p("For : <b>SHYNEX GREEN SOLUTIONS</b><br/><br/>"
          "<i>System-Generated Estimate</i><br/>"
          "<i>Signature Not Required</i>",
          fontSize=8, textColor=GREY, alignment=TA_RIGHT, leading=13),
    ]], colWidths=[W*0.32, W*0.40, W*0.28])
    foot.setStyle(TableStyle([
        ("VALIGN",      (0,0),(-1,-1),"TOP"),
        ("LINEABOVE",   (0,0),(-1,0), 1.0, BRAND),
        ("LINERIGHT",   (0,0),(0,0),  0.5, LINE),
        ("LINERIGHT",   (1,0),(1,0),  0.5, LINE),
        ("TOPPADDING",  (0,0),(-1,-1),6),
        ("LEFTPADDING", (0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(foot)
    story.append(HRFlowable(width="100%", thickness=1.0,
                             color=BRAND, spaceBefore=6, spaceAfter=3))

    # ══════════════════════════════════════════════════════════════════════════
    # 8. Footer strip
    # ══════════════════════════════════════════════════════════════════════════
    story.append(p(
        "Shynex Green Solutions™  |  GSTIN: 36FFGPB8631L1Z6  |  MSME Registered  |  "
        "customerservices@shynexgreensolutions.com  |  +91 8125242828",
        fontSize=7, textColor=GREY, alignment=TA_CENTER))

    import io
    buf = io.BytesIO()
    doc_buf = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=10*mm, bottomMargin=10*mm)
    doc_buf.build(story)
    pdf_bytes = buf.getvalue()
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        print(f"✅  {output_path}")
    return pdf_bytes
