"""
zen-session-log PDF — ระบบบันทึก Session อัตโนมัติ
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
import datetime

pdfmetrics.registerFont(TTFont('TH',    r'C:\Windows\Fonts\leelawad.ttf'))
pdfmetrics.registerFont(TTFont('Emoji', r'C:\Windows\Fonts\seguiemj.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
try:
    pdfmetrics.registerFont(TTFont('TH-Bold', r'C:\Windows\Fonts\leelawadbd.ttf'))
    registerFontFamily('TH', normal='TH', bold='TH-Bold', italic='TH', boldItalic='TH-Bold')
except Exception:
    registerFontFamily('TH', normal='TH', bold='TH', italic='TH', boldItalic='TH')

def me(text):
    result, in_emoji = [], False
    for ch in text:
        cp = ord(ch)
        is_e = (0x1F300 <= cp <= 0x1FFFF or 0x2600 <= cp <= 0x27BF or
                0x2300 <= cp <= 0x23FF or 0xFE00 <= cp <= 0xFE0F or cp == 0x20E3)
        if is_e:
            if not in_emoji:
                result.append('<font name="Emoji">')
                in_emoji = True
            result.append(ch)
        else:
            if in_emoji:
                result.append('</font>')
                in_emoji = False
            result.append(ch)
    if in_emoji:
        result.append('</font>')
    return ''.join(result)

# ─── Colors ──────────────────────────────────────────────────────────────────
C = {
    'navy':    colors.HexColor('#0D1B2A'),
    'blue':    colors.HexColor('#1565C0'),
    'blue2':   colors.HexColor('#1E88E5'),
    'teal':    colors.HexColor('#00897B'),
    'green':   colors.HexColor('#2E7D32'),
    'purple':  colors.HexColor('#6A1B9A'),
    'orange':  colors.HexColor('#E65100'),
    'red':     colors.HexColor('#B71C1C'),
    'card_bg': colors.HexColor('#F8FAFC'),
    'border':  colors.HexColor('#CBD5E1'),
    'text':    colors.HexColor('#1E293B'),
    'muted':   colors.HexColor('#64748B'),
    'white':   colors.white,
    'light':   colors.HexColor('#EEF2FF'),
    'lg':      colors.HexColor('#E8F5E9'),
    'lb':      colors.HexColor('#E3F2FD'),
    'lo':      colors.HexColor('#FFF3E0'),
    'lp':      colors.HexColor('#F3E5F5'),
    'lt':      colors.HexColor('#E0F2F1'),
    'code_bg': colors.HexColor('#1E2A3A'),
    'code_tx': colors.HexColor('#E2E8F0'),
    'code_cm': colors.HexColor('#64748B'),
    'code_k':  colors.HexColor('#93C5FD'),
    'code_s':  colors.HexColor('#86EFAC'),
}

PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
CW = PAGE_W - 2 * MARGIN

# ─── Styles ──────────────────────────────────────────────────────────────────
def S(name, **kw):
    kw.setdefault('fontName', 'TH')
    return ParagraphStyle(name, **kw)

ST = {
    'h1':      S('h1', fontSize=20, leading=28, textColor=C['navy'], spaceBefore=10, spaceAfter=6),
    'h2':      S('h2', fontSize=14, leading=20, textColor=C['blue'], spaceBefore=10, spaceAfter=4),
    'h3':      S('h3', fontSize=11, leading=16, textColor=C['navy'], spaceBefore=8,  spaceAfter=3),
    'body':    S('bd', fontSize=10, leading=15, textColor=C['text'], spaceAfter=4,   alignment=TA_JUSTIFY),
    'body_c':  S('bdc',fontSize=10, leading=15, textColor=C['text'], spaceAfter=4,   alignment=TA_CENTER),
    'sm':      S('sm', fontSize=9,  leading=13, textColor=C['muted'],spaceAfter=2),
    'mono':    S('mn', fontName='TH', fontSize=8.5, leading=13,
                 textColor=C['code_tx'], backColor=C['code_bg'],
                 leftIndent=10, rightIndent=10, spaceBefore=2, spaceAfter=2),
    'mono_lbl':S('ml', fontName='Courier', fontSize=8, leading=12, textColor=C['code_k']),
    'caption': S('cap',fontSize=8.5, leading=12, textColor=C['muted'], alignment=TA_CENTER, spaceBefore=2),
    'sec_t':   S('st', fontSize=22, leading=30, textColor=C['white']),
    'sec_s':   S('ss', fontSize=11, leading=16, textColor=colors.HexColor('#B3E5FC')),
    'badge':   S('ba', fontSize=9,  leading=13, textColor=C['white'], alignment=TA_CENTER),
    'pill':    S('pl', fontSize=8,  leading=11, textColor=C['blue'],  alignment=TA_CENTER),
    'field_l': S('fl', fontSize=8,  leading=11, textColor=C['blue2'], spaceBefore=3),
    'field_b': S('fb', fontSize=9.5,leading=14, textColor=C['text']),
    'bul':     S('bu', fontSize=10, leading=15, textColor=C['text'], leftIndent=14, spaceAfter=3),
    'bul_sm':  S('bs', fontSize=9,  leading=13, textColor=C['text'], leftIndent=12, spaceAfter=2),
}

# ─── Helper: info box ────────────────────────────────────────────────────────
def info_box(label, body_paras, accent=None, bg=None):
    accent = accent or C['blue']
    bg     = bg     or C['lb']
    rows   = [[Paragraph(f'<b>{label}</b>', ParagraphStyle('ibl',
                fontName='TH', fontSize=8.5, leading=12, textColor=accent))]]
    for p in body_paras:
        rows.append([p])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,0), bg),
        ('BACKGROUND',    (0,1),(-1,-1), C['card_bg']),
        ('BOX',           (0,0),(-1,-1), 1, accent),
        ('LINEBELOW',     (0,0),(0,0), 1, accent),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('ROUNDEDCORNERS',[4,4,4,4]),
    ]))
    return t

def code_box(lines):
    """Dark-themed code block."""
    rows = [[Paragraph(l, ST['mono'])] for l in lines]
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C['code_bg']),
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ('BOX',           (0,0),(-1,-1), 1, C['border']),
        ('ROUNDEDCORNERS',[4,4,4,4]),
    ]))
    return t

def path_pill(path_str):
    p = Paragraph(path_str, ParagraphStyle('pp', fontName='Courier',
        fontSize=8.5, leading=12, textColor=C['blue'],
        backColor=C['lb'], leftIndent=8, rightIndent=8))
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), C['lb']),
        ('BOX', (0,0),(-1,-1), 1, C['blue']),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    return t

# ─── Custom Flowable: Flow Diagram ───────────────────────────────────────────
class FlowDiagram(Flowable):
    """Draws the session-end pipeline flow diagram."""
    def __init__(self, width, height):
        super().__init__()
        self.width  = width
        self.height = height

    def draw(self):
        c  = self.canv
        w  = self.width
        h  = self.height
        bh = 1.0 * cm
        bw = 3.2 * cm
        gap = 0.7 * cm

        # ── Top row: 3 pipeline stages ────────────────────────────────────────
        stages = [
            ('ปิด\nSession',              C['navy'], C['white']),
            ('session-logger\n.ps1',      C['blue'], C['white']),
            ('session-\nsummarizer.ps1',  C['teal'], C['white']),
        ]
        total_top = 3 * bw + 2 * gap
        x_start   = (w - total_top) / 2
        y_top     = h - bh - 0.5 * cm

        cx_list = []
        for i, (label, bg, fg) in enumerate(stages):
            bx = x_start + i * (bw + gap)
            cx = bx + bw / 2
            cx_list.append(cx)
            c.setFillColor(bg)
            c.roundRect(bx, y_top, bw, bh, 5, fill=1, stroke=0)
            c.setFillColor(fg)
            c.setFont('TH', 9)
            lines = label.split('\n')
            if len(lines) == 1:
                c.drawCentredString(cx, y_top + bh / 2 - 4, lines[0])
            else:
                c.drawCentredString(cx, y_top + bh * 0.67 - 4, lines[0])
                c.drawCentredString(cx, y_top + bh * 0.27 - 4, lines[1])

        # ── Arrows between top-row boxes ──────────────────────────────────────
        mid_y = y_top + bh / 2
        for i in range(len(stages) - 1):
            x1 = cx_list[i] + bw / 2
            x2 = cx_list[i + 1] - bw / 2
            c.setStrokeColor(C['muted'])
            c.setFillColor(C['muted'])
            c.setLineWidth(1.2)
            c.line(x1, mid_y, x2 - 0.18 * cm, mid_y)
            path = c.beginPath()
            path.moveTo(x2, mid_y)
            path.lineTo(x2 - 0.22 * cm, mid_y + 0.1 * cm)
            path.lineTo(x2 - 0.22 * cm, mid_y - 0.1 * cm)
            path.close()
            c.setLineWidth(0)
            c.drawPath(path, fill=1, stroke=0)

        # "SessionEnd Hook" label — above arrow, between box 0 and box 1
        hook_x = (cx_list[0] + cx_list[1]) / 2
        c.setFillColor(C['muted'])
        c.setFont('TH', 7)
        c.drawCentredString(hook_x, y_top + bh + 0.1 * cm, 'SessionEnd Hook')

        # ── Vertical drop from summarizer to branch point ─────────────────────
        sum_x    = cx_list[2]
        branch_y = y_top - 1.2 * cm      # well below top-row boxes

        c.setStrokeColor(C['teal'])
        c.setLineWidth(1.5)
        c.line(sum_x, y_top, sum_x, branch_y)

        # ── Output boxes: middle box anchored at sum_x ────────────────────────
        out_bw  = 3.0 * cm
        out_bh  = 1.3 * cm
        out_gap = 0.5 * cm
        # anchor: out_centers[1] = sum_x
        ox_mid   = sum_x - out_bw / 2
        ox_left  = ox_mid - out_bw - out_gap
        ox_right = ox_mid + out_bw + out_gap
        oy = branch_y - 0.4 * cm - out_bh

        out_boxes = [ox_left, ox_mid, ox_right]
        out_centers = [ox + out_bw / 2 for ox in out_boxes]

        outputs = [
            ('session_log/\nYYYY-MM-DD.md', C['blue'],   C['lb'], C['blue']),
            ('recent_\ndigest.md',           C['green'],  C['lg'], C['green']),
            ('extracted_\nmistakes.md',      C['purple'], C['lp'], C['purple']),
        ]
        for i, (label, fg, bg, border) in enumerate(outputs):
            ox = out_boxes[i]
            cx = out_centers[i]
            c.setFillColor(bg)
            c.roundRect(ox, oy, out_bw, out_bh, 5, fill=1, stroke=0)
            c.setStrokeColor(border)
            c.setLineWidth(1.0)
            c.roundRect(ox, oy, out_bw, out_bh, 5, fill=0, stroke=1)
            c.setFillColor(fg)
            c.setFont('TH', 8)
            lines = label.split('\n')
            c.drawCentredString(cx, oy + out_bh * 0.65 - 3, lines[0])
            c.drawCentredString(cx, oy + out_bh * 0.27 - 3, lines[1])

        # ── Horizontal branch + drops to output boxes ─────────────────────────
        c.setStrokeColor(C['teal'])
        c.setLineWidth(1.5)
        # horizontal spanning all 3 outputs
        c.line(out_centers[0], branch_y, out_centers[2], branch_y)
        # vertical drops from branch to each output box top
        for cx in out_centers:
            c.line(cx, branch_y, cx, oy + out_bh + 0.05 * cm)
            # arrowhead pointing down
            c.setFillColor(C['teal'])
            c.setLineWidth(0)
            path = c.beginPath()
            path.moveTo(cx, oy + out_bh)
            path.lineTo(cx - 0.1 * cm, oy + out_bh + 0.18 * cm)
            path.lineTo(cx + 0.1 * cm, oy + out_bh + 0.18 * cm)
            path.close()
            c.drawPath(path, fill=1, stroke=0)

        # ── Output labels ─────────────────────────────────────────────────────
        label_data = [
            ('Haiku fills summary\n+ Sonnet digest', C['blue'],   out_centers[0]),
            ('Sonnet 1-line\ntakeaway/session', C['green'],  out_centers[1]),
            ('Haiku extracts\nhigh-impact rules', C['purple'], out_centers[2]),
        ]
        for label, clr, cx in label_data:
            c.setFillColor(clr)
            c.setFont('TH', 7)
            for j, ln in enumerate(label.split('\n')):
                c.drawCentredString(cx, oy - 0.35*cm - j*0.28*cm, ln)

# ─── Custom Flowable: Retention Bar ──────────────────────────────────────────
class RetentionBar(Flowable):
    """Shows retention period visually."""
    def __init__(self, width, label, days, max_days, color):
        super().__init__()
        self.width    = width
        self.height   = 1.2 * cm
        self.label    = label
        self.days     = days
        self.max_days = max_days
        self.color    = color

    def draw(self):
        c    = self.canv
        w    = self.width
        bh   = 0.45 * cm
        by   = (self.height - bh) / 2
        ratio = self.days / self.max_days
        bar_w = (w - 3.5*cm) * ratio

        # Background track
        c.setFillColor(colors.HexColor('#E2E8F0'))
        c.roundRect(2.5*cm, by, w - 3.5*cm, bh, 4, fill=1, stroke=0)
        # Filled portion
        c.setFillColor(self.color)
        if bar_w > 0:
            c.roundRect(2.5*cm, by, bar_w, bh, 4, fill=1, stroke=0)
        # Label
        c.setFillColor(C['text'])
        c.setFont('TH', 8.5)
        c.drawString(0, by + bh/2 - 4, self.label)
        # Days text
        c.setFillColor(self.color)
        c.setFont('TH', 9)
        c.drawString(2.5*cm + bar_w + 0.15*cm, by + bh/2 - 4, f'{self.days} วัน')

# ─── Section Banner ──────────────────────────────────────────────────────────
def section_banner(emoji, title, subtitle, bg_color):
    inner = Table([
        [Paragraph(me(f'{emoji}  {title}'), ST['sec_t'])],
        [Paragraph(subtitle, ST['sec_s'])],
    ], colWidths=[CW - 32])
    inner.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))
    outer = Table([[inner]], colWidths=[CW])
    outer.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg_color),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 16),
        ('RIGHTPADDING',  (0,0),(-1,-1), 16),
        ('ROUNDEDCORNERS',[6,6,0,0]),
    ]))
    return outer

# ─── Page decorator ──────────────────────────────────────────────────────────
def on_page(canvas, doc):
    if doc.page == 1:
        canvas.saveState()
        canvas.setFillColor(C['navy'])
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setFillColor(C['blue2'])
        canvas.rect(0, PAGE_H*0.42, PAGE_W, 0.35*cm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor('#42A5F5'))
        canvas.rect(0, PAGE_H*0.42 - 0.15*cm, PAGE_W, 0.12*cm, fill=1, stroke=0)

        canvas.setFont('TH', 46)
        canvas.setFillColor(C['white'])
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.60, 'zen-session-log')
        canvas.setFont('TH', 18)
        canvas.setFillColor(colors.HexColor('#90CAF9'))
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.54, 'ระบบบันทึก Session อัตโนมัติ')
        canvas.setFont('TH', 11)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.33,
            f'Updated: {datetime.datetime.now().strftime("%d %B %Y")}')
        canvas.setFillColor(colors.HexColor('#42A5F5'))
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.305, 'github.com/zennnne/zen-skills')
        canvas.restoreState()
        return

    canvas.saveState()
    canvas.setFillColor(C['navy'])
    canvas.rect(0, PAGE_H - 0.75*cm, PAGE_W, 0.75*cm, fill=1, stroke=0)
    canvas.setFont('TH', 7.5)
    canvas.setFillColor(colors.HexColor('#90CAF9'))
    canvas.drawString(MARGIN, PAGE_H - 0.52*cm, 'zen-session-log')
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.52*cm, 'ระบบบันทึก Session อัตโนมัติ')
    canvas.setFillColor(C['border'])
    canvas.rect(MARGIN, 0.55*cm, CW, 0.02*cm, fill=1, stroke=0)
    canvas.setFont('TH', 7.5)
    canvas.setFillColor(C['muted'])
    canvas.drawCentredString(PAGE_W/2, 0.35*cm, f'— {doc.page} —')
    canvas.restoreState()

# ─── Page 2: ภาพรวมระบบ ──────────────────────────────────────────────────────
def build_overview():
    items = []
    items.append(Spacer(1, 0.6*cm))
    items.append(Paragraph('ภาพรวมระบบ', ST['h1']))
    items.append(HRFlowable(width=CW, thickness=2, color=C['blue'], spaceAfter=10))
    items.append(Paragraph(
        'เมื่อ session Claude Code ปิด — SessionEnd hook จะทำงานอัตโนมัติ '
        'โดยไม่ต้องสั่งอะไรเพิ่ม ระบบจะสรุป session นั้นด้วย AI '
        'แล้วกระจายผลลัพธ์ไปยัง 3 ไฟล์ตามวัตถุประสงค์ที่ต่างกัน',
        ST['body']))
    items.append(Spacer(1, 0.4*cm))
    items.append(FlowDiagram(CW, 7.2*cm))
    items.append(Paragraph('Pipeline ที่ทำงานทุกครั้งที่ปิด session', ST['caption']))
    items.append(Spacer(1, 0.6*cm))

    # 3-column summary cards
    card_data = [
        ('📄', 'session_log/', 'YYYY-MM-DD.md', C['blue'],  C['lb'],
         'บันทึก session ทีละตัว\nอ่านรายละเอียดเต็ม'),
        ('📋', 'recent_digest', '.md',           C['green'], C['lg'],
         'rolling digest 7 วัน\nเห็นภาพรวมเร็ว'),
        ('🧠', 'extracted_', 'mistakes.md',     C['purple'],C['lp'],
         'กฎจากความผิดพลาด\nเก็บ 180 วัน'),
    ]
    cells = []
    for emoji, name1, name2, fg, bg, desc in card_data:
        inner_rows = [
            [Paragraph(me(emoji), ParagraphStyle('ce', fontName='Emoji',
                fontSize=22, leading=26, alignment=TA_CENTER))],
            [Paragraph(f'<b>{name1}</b>', ParagraphStyle('cn', fontName='TH',
                fontSize=10, leading=13, textColor=fg, alignment=TA_CENTER))],
            [Paragraph(name2, ParagraphStyle('cn2', fontName='Courier',
                fontSize=8, leading=11, textColor=fg, alignment=TA_CENTER))],
            [Spacer(1, 4)],
            [Paragraph(desc, ParagraphStyle('cd', fontName='TH',
                fontSize=8.5, leading=13, textColor=C['text'], alignment=TA_CENTER))],
        ]
        inner = Table(inner_rows, colWidths=[CW/3 - 0.4*cm])
        inner.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('BOX',           (0,0),(-1,-1), 1.5, fg),
            ('TOPPADDING',    (0,0),(-1,-1), 10),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('LEFTPADDING',   (0,0),(-1,-1), 6),
            ('RIGHTPADDING',  (0,0),(-1,-1), 6),
            ('ROUNDEDCORNERS',[6,6,6,6]),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ]))
        cells.append(inner)

    grid = Table([cells], colWidths=[CW/3]*3)
    grid.setStyle(TableStyle([
        ('LEFTPADDING',   (0,0),(-1,-1), 4),
        ('RIGHTPADDING',  (0,0),(-1,-1), 4),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    items.append(grid)
    items.append(Spacer(1, 0.5*cm))

    # Who does what
    items.append(Paragraph('ใครทำอะไร', ST['h2']))
    who_data = [
        ('Haiku',  C['blue'],  C['lb'],
         'สรุปเนื้อหา session — เขียน Title, Goal, What done, Decisions, Mistakes, Followup ลง session_log และ extract feedback rules'),
        ('Sonnet', C['teal'], C['lt'],
         'เขียน 1-line takeaway สำหรับ recent_digest.md — ประมวลภาพรวมของ session ในประโยคเดียว'),
    ]
    for model, fg, bg, desc in who_data:
        row = Table([[
            Paragraph(f'<b>{model}</b>', ParagraphStyle('wm', fontName='TH',
                fontSize=10, leading=13, textColor=fg, alignment=TA_CENTER)),
            Paragraph(desc, ST['body']),
        ]], colWidths=[2.0*cm, CW - 2.0*cm])
        row.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(0,0), bg),
            ('BACKGROUND',    (1,0),(1,0), C['card_bg']),
            ('BOX',           (0,0),(-1,-1), 1, fg),
            ('TOPPADDING',    (0,0),(-1,-1), 8),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('LEFTPADDING',   (0,0),(0,0), 6),
            ('LEFTPADDING',   (1,0),(1,0), 10),
            ('RIGHTPADDING',  (0,0),(-1,-1), 10),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('ROUNDEDCORNERS',[4,4,4,4]),
        ]))
        items.append(row)
        items.append(Spacer(1, 4))

    return items

# ─── Page 3: session_log ──────────────────────────────────────────────────────
def build_session_log_page():
    items = []
    items.append(PageBreak())
    items.append(section_banner('📄', 'session_log', 'daily log ที่บันทึกทุก session', C['blue']))
    items.append(Spacer(1, 10))

    items.append(Paragraph('คืออะไร?', ST['h2']))
    items.append(Paragraph(
        'ไฟล์ Markdown รายวันที่เก็บ session ทุกอันของวันนั้น '
        'แต่ละ session มี ID เฉพาะ + สรุปที่ Haiku เขียน '
        'ใช้ดูว่าวันนี้ทำอะไรบ้าง หรือหา session เก่าเพื่อกลับมาอ่าน context',
        ST['body']))

    items.append(Paragraph('ตำแหน่งไฟล์', ST['h2']))
    items.append(path_pill('~/.claude/session_log/YYYY/MM/YYYY-MM-DD.md'))
    items.append(Spacer(1, 6))
    items.append(Paragraph(
        'ตัวอย่าง: <font name="Courier" size="9">~/.claude/session_log/2026/05/2026-05-29.md</font> '
        '— ทุก session ที่ปิดในวันนั้นจะ append ลงไฟล์เดิม', ST['body']))

    items.append(Paragraph('โครงสร้างแต่ละ entry', ST['h2']))
    items.append(code_box([
        '## Session 14:28 - `3b0929b3` (completed)',
        '- <b>Title:</b> แก้ pom.xml หลัง teammate merge พัง',
        '- <b>Status:</b> completed',
        '',
        '### Goal',
        'ให้ Jetty server restart สำเร็จที่ port 8080',
        '',
        '### What done',
        '- แก้ pom.xml conflict section ใน &lt;build&gt;&lt;plugins&gt;',
        '- restart Jetty server และ verify ที่ port 8080',
        '',
        '### Decisions',
        '- <b>Context:</b> ต้องเลือกระหว่าง revert หรือ manual fix',
        '  <b>Decision:</b> manual fix เพราะรู้ว่า conflict ตรงไหน',
        '  <b>Consequences:</b> เร็วกว่า revert + recommit',
        '',
        '### Mistakes',
        '- <b>what:</b> ไม่ได้เช็ก pom.xml ก่อน restart server',
        '  <b>why:</b> assume ว่า merge ไม่กระทบ build config',
        '  <b>fix:</b> เช็ก pom.xml ก่อน restart เสมอ',
        '  <b>rule:</b> merge แล้ว error ให้เช็ก build config ก่อน',
        '',
        '### Followup',
        '- ทำ connection pooling ต่อ',
    ]))
    items.append(Spacer(1, 8))

    # Field descriptions
    items.append(Paragraph('ความหมายของแต่ละ field', ST['h2']))
    fields = [
        ('Session ID',  'ย่อจาก UUID ใช้ reference ใน memory/skills อื่น'),
        ('Goal',        'สิ่งที่ user ต้องการในตอนเริ่ม session'),
        ('What done',   'bullet list สิ่งที่ทำสำเร็จจริง'),
        ('Decisions',   'context + ตัดสินใจอะไร + ผลที่ตามมา'),
        ('Mistakes',    'ข้อผิดพลาด + สาเหตุ + วิธีแก้ + กฎที่ generalize ได้ — สำคัญที่สุด'),
        ('Followup',    'งานที่ยังค้างหรือต้องทำต่อ'),
    ]
    rows = []
    for field, desc in fields:
        is_mistakes = 'Mistakes' in field
        rows.append([
            Paragraph(f'<b>{field}</b>', ParagraphStyle('ff', fontName='TH',
                fontSize=9, leading=13,
                textColor=C['red'] if is_mistakes else C['blue'])),
            Paragraph(desc, ParagraphStyle('fd', fontName='TH',
                fontSize=9, leading=13, textColor=C['text'])),
        ])
    ft = Table(rows, colWidths=[2.8*cm, CW - 2.8*cm])
    ft.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C['card_bg']),
        ('BOX',           (0,0),(-1,-1), 1, C['border']),
        ('LINEBELOW',     (0,0),(-1,-2), 0.3, C['border']),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(0,-1), 10),
        ('LEFTPADDING',   (1,0),(1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('BACKGROUND',    (0,4),(1,4), colors.HexColor('#FFF5F5')),
    ]))
    items.append(ft)
    items.append(Spacer(1, 10))

    # Lifecycle
    items.append(info_box('Lifecycle', [
        Paragraph('สร้างโดย: session-logger.ps1 (skeleton) > session-summarizer.ps1 (Haiku fills content)', ST['body']),
        Paragraph('Retention: ไม่มีการลบอัตโนมัติ — เก็บตลอด แนะนำให้รัน /cleaning-sessions เป็นประจำ', ST['body']),
        Paragraph('ถ้า Haiku ทำงานไม่สำเร็จ: จะเห็น placeholder "(auto-summary failed)" — รัน /session-summary เพื่อ fill เอง', ST['body']),
    ], accent=C['blue'], bg=C['lb']))

    return items

# ─── Page 4: recent_digest.md ─────────────────────────────────────────────────
def build_digest_page():
    items = []
    items.append(PageBreak())
    items.append(section_banner('📋', 'recent_digest.md', 'rolling 7-day digest — เห็นภาพรวม session เร็วๆ', C['green']))
    items.append(Spacer(1, 10))

    items.append(Paragraph('คืออะไร?', ST['h2']))
    items.append(Paragraph(
        'ไฟล์ index ที่เก็บ 1 ประโยคต่อ session ย้อนหลัง 7 วัน '
        'Claude โหลดไฟล์นี้เข้า memory เพื่อรู้ว่าช่วง 7 วันที่ผ่านมาทำอะไรมาบ้าง '
        'โดยไม่ต้องเปิดอ่าน session_log ทั้งหมด ประหยัด context มาก',
        ST['body']))
    items.append(Paragraph(
        me('⚠️') + '  <b>Lower trust</b> — Sonnet อาจตีความ session ผิด '
        'ถ้าต้องการรายละเอียดที่เชื่อถือได้ให้เปิด session_log ตรงๆ',
        ParagraphStyle('warn', fontName='TH', fontSize=9.5, leading=14,
            textColor=C['orange'], backColor=C['lo'],
            leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4)))

    items.append(Paragraph('ตำแหน่งไฟล์', ST['h2']))
    items.append(path_pill('~/.claude/projects/<USERPROFILE-as-key>/memory/auto/recent_digest.md'))
    items.append(Spacer(1, 4))
    items.append(Paragraph(
        'ตัวอย่าง: <font name="Courier" size="9">'
        '~/.claude/projects/C--Users-User/memory/auto/recent_digest.md</font>',
        ST['body']))

    items.append(Paragraph('format ของไฟล์', ST['h2']))
    items.append(code_box([
        '<font color="#64748B">--- (frontmatter) ---</font>',
        'name: Recent session digest',
        'type: reference',
        '<font color="#64748B">---</font>',
        '',
        '<font color="#64748B"># Recent session digest</font>',
        '',
        '<font color="#64748B">## Entries</font>',
        '<font color="#64748B">&lt;!-- digest:start --&gt;</font>',
        '- 2026-05-29 14:28 | `3b0929b3` | แก้ pom.xml หลัง teammate merge พัง แล้ว restart Jetty สำเร็จ',
        '- 2026-05-29 16:04 | `fe6f071d` | สร้าง PDF catalog ของ zen-skills แล้ว push ขึ้น GitHub สำเร็จ',
        '- 2026-05-29 19:41 | `4b056ab1` | ลบคอลัมน์ Tier ออกจาก README ของ zen-skills แล้ว push ขึ้น GitHub',
        '<font color="#64748B">&lt;!-- digest:end --&gt;</font>',
    ]))
    items.append(Spacer(1, 6))

    # Retention timeline
    items.append(Paragraph('การหมุนเวียน entry (Rotation)', ST['h2']))
    items.append(Paragraph(
        'ทุกครั้งที่ session-summarizer เขียน entry ใหม่ มันจะ prune '
        'entry ที่เก่ากว่า 7 วันออกอัตโนมัติ ทำให้ไฟล์เล็กเสมอ',
        ST['body']))
    items.append(RetentionBar(CW, 'recent_digest.md', 7, 180, C['green']))
    items.append(RetentionBar(CW, 'extracted_mistakes.md', 180, 180, C['purple']))
    items.append(Paragraph('เส้น retention ของ 2 ไฟล์เปรียบเทียบกัน (scale 0-180 วัน)', ST['caption']))
    items.append(Spacer(1, 10))

    # Lifecycle
    items.append(info_box('Lifecycle', [
        Paragraph('เขียนโดย: Sonnet (--effort medium) ทุกครั้งที่ session ปิด', ST['body']),
        Paragraph('ต้องการ: ไฟล์ต้องมีอยู่แล้ว — ถ้าไม่มีระบบจะ skip เงียบๆ '
                  '(setup-session-log สร้างให้อัตโนมัติ)', ST['body']),
        Paragraph('format: <font name="Courier" size="9">'
                  '- YYYY-MM-DD HH:MM | `session-id-short` | takeaway</font>', ST['body']),
    ], accent=C['green'], bg=C['lg']))

    return items

# ─── Page 5: extracted_mistakes.md ───────────────────────────────────────────
def build_mistakes_page():
    items = []
    items.append(PageBreak())
    items.append(section_banner('🧠', 'extracted_mistakes.md',
                                'กฎที่ extract จากความผิดพลาด — เก็บข้ามเดือน', C['purple']))
    items.append(Spacer(1, 10))

    items.append(Paragraph('คืออะไร?', ST['h2']))
    items.append(Paragraph(
        'ทุก session ที่ปิด Haiku จะอ่าน transcript และถามตัวเองว่า '
        '"มี rule ที่ HIGH-IMPORTANCE พอที่จะเก็บข้ามไว้ session อื่นไหม?" '
        'ถ้ามี จะ append เข้าไฟล์นี้ เพื่อให้ Claude รู้ว่าเคยผิดอะไรมาและอย่าทำซ้ำ',
        ST['body']))

    # Criteria box
    items.append(Paragraph('เงื่อนไขที่ Haiku จะ extract (เข้มงวดมาก)', ST['h2']))
    criteria = [
        ('เพิ่ม',  C['green'], C['lg'],
         'Rule ที่มี "always" / "never" — กฎที่ชัดเจนและ apply ได้ทุกครั้ง'),
        ('เพิ่ม',  C['green'], C['lg'],
         'Recurring class of mistake — ผิดแบบเดิมซ้ำๆ ข้ามหลาย session'),
        ('เพิ่ม',  C['green'], C['lg'],
         'Non-obvious gotcha — ข้อผิดพลาดที่ไม่ obvious และจะเกิดซ้ำถ้าไม่รู้'),
        ('ไม่เพิ่ม', C['red'], colors.HexColor('#FFF5F5'),
         'Generic principles — เช่น "ตรวจสอบก่อนทำ" ที่รู้อยู่แล้ว'),
        ('ไม่เพิ่ม', C['red'], colors.HexColor('#FFF5F5'),
         'Session routine ธรรมดา — ไม่มีข้อผิดพลาดสำคัญ'),
    ]
    crows = []
    for tag, tc, bg, desc in criteria:
        crows.append([
            Paragraph(f'<b>{tag}</b>', ParagraphStyle('ct', fontName='TH',
                fontSize=8.5, leading=12, textColor=tc, alignment=TA_CENTER)),
            Paragraph(desc, ParagraphStyle('cd', fontName='TH',
                fontSize=9, leading=13, textColor=C['text'])),
        ])
    ct = Table(crows, colWidths=[1.8*cm, CW - 1.8*cm])
    ct.setStyle(TableStyle([
        ('BOX',           (0,0),(-1,-1), 1, C['border']),
        ('LINEBELOW',     (0,0),(-1,-2), 0.3, C['border']),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(0,-1), 6),
        ('LEFTPADDING',   (1,0),(1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('BACKGROUND',    (0,0),(1,2), C['lg']),
        ('BACKGROUND',    (0,3),(1,4), colors.HexColor('#FFF5F5')),
    ]))
    items.append(ct)
    items.append(Spacer(1, 8))

    items.append(Paragraph('ตัวอย่าง entry', ST['h2']))
    items.append(code_box([
        '## 2026-05-29 14:28 - merge-then-restart',
        '- <b>Rule:</b> แก้ไข pom.xml และ dependencies ก่อน restart dev server',
        '  ไม่ใช่ restart แล้วหวังว่าจะออกมาดี',
        '- <b>Why:</b> Dependency conflicts ทำให้เกิด runtime crashes ที่ซ่อนอยู่',
        '  ใน startup logs ที่ดูเหมือน success',
        '- <b>Source session:</b> `3b0929b3-a544-4e13-...`',
    ]))
    items.append(Spacer(1, 6))

    items.append(Paragraph('ตำแหน่งไฟล์', ST['h2']))
    items.append(path_pill('~/.claude/projects/<USERPROFILE-as-key>/memory/auto/extracted_mistakes.md'))
    items.append(Spacer(1, 8))

    items.append(info_box('Lifecycle', [
        Paragraph('เขียนโดย: Haiku ทุกครั้งที่ session ปิด — แต่จะเพิ่ม entry เฉพาะเมื่อมีกฎสำคัญเท่านั้น', ST['body']),
        Paragraph('Rotation: prune entry ที่เก่ากว่า 180 วัน อัตโนมัติ', ST['body']),
        Paragraph('ต้องการ: ถ้าไฟล์ไม่มี Haiku จะสร้างเองได้ แต่ directory auto/ ต้องมีก่อน '
                  '(setup-session-log สร้างให้)', ST['body']),
        Paragraph(me('⚠️') + '  Lower trust — Haiku อาจ misjudge importance '
                  'ควร verify ก่อน apply rule สำคัญ', ParagraphStyle('w2', fontName='TH',
                      fontSize=9, leading=13, textColor=C['orange'])),
    ], accent=C['purple'], bg=C['lp']))

    return items

# ─── Page 6: Quick Reference ─────────────────────────────────────────────────
def build_quickref():
    items = []
    items.append(PageBreak())
    items.append(Spacer(1, 0.6*cm))
    items.append(Paragraph('Quick Reference', ST['h1']))
    items.append(HRFlowable(width=CW, thickness=2, color=C['blue'], spaceAfter=12))

    # 3-file comparison table
    headers = ['', 'session_log', 'recent_digest', 'extracted_mistakes']
    rows = [
        ['ใครเขียน', 'Haiku', 'Sonnet', 'Haiku'],
        ['เมื่อไร',  'ทุก session', 'ทุก session', 'เฉพาะ session มีกฎสำคัญ'],
        ['เก็บนานแค่ไหน', 'ตลอดไป*', '7 วัน', '180 วัน'],
        ['วัตถุประสงค์', 'รายละเอียดเต็ม', 'ภาพรวมเร็ว', 'กฎข้ามเดือน'],
        ['ความน่าเชื่อถือ', 'สูง', 'ปานกลาง', 'ปานกลาง'],
        ['path', 'session_log/\nYYYY/MM/DD.md',
                 'memory/auto/\nrecent_digest.md',
                 'memory/auto/\nextracted_mistakes.md'],
    ]

    col_colors = [None, C['lb'], C['lg'], C['lp']]
    header_colors = [C['navy'], C['blue'], C['green'], C['purple']]

    header_row = []
    for i, h in enumerate(headers):
        header_row.append(Paragraph(f'<b>{h}</b>', ParagraphStyle('qh', fontName='TH',
            fontSize=9.5, leading=13, textColor=C['white'] if i > 0 else C['white'],
            alignment=TA_CENTER)))

    table_data = [header_row]
    for row in rows:
        tr = [Paragraph(f'<b>{row[0]}</b>', ParagraphStyle('rl', fontName='TH',
                fontSize=9, leading=13, textColor=C['text']))]
        for j, cell in enumerate(row[1:]):
            tr.append(Paragraph(cell, ParagraphStyle('rc', fontName='TH',
                fontSize=9, leading=13, textColor=C['text'], alignment=TA_CENTER)))
        table_data.append(tr)

    qt = Table(table_data, colWidths=[2.6*cm, (CW-2.6*cm)/3, (CW-2.6*cm)/3, (CW-2.6*cm)/3])
    style = [
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('BOX',           (0,0),(-1,-1), 1, C['border']),
        ('LINEBELOW',     (0,0),(-1,-2), 0.3, C['border']),
        ('LINEBEFORE',    (1,0),(-1,-1), 0.3, C['border']),
        # Header row
        ('BACKGROUND',    (0,0),(0,0), C['navy']),
        ('BACKGROUND',    (1,0),(1,0), C['blue']),
        ('BACKGROUND',    (2,0),(2,0), C['green']),
        ('BACKGROUND',    (3,0),(3,0), C['purple']),
        # Column tints
        ('ROWBACKGROUNDS', (1,1),(1,-1), [C['lb']]),
        ('ROWBACKGROUNDS', (2,1),(2,-1), [C['lg']]),
        ('ROWBACKGROUNDS', (3,1),(3,-1), [C['lp']]),
        # Row label column
        ('BACKGROUND',    (0,1),(-1,-1), C['card_bg']),
        ('ROWBACKGROUNDS', (0,1),(0,-1), [C['card_bg'], colors.HexColor('#F1F5F9')]),
    ]
    # reapply column tints over row backgrounds
    for r in range(1, len(table_data)):
        style.append(('BACKGROUND', (1,r),(1,r), C['lb']))
        style.append(('BACKGROUND', (2,r),(2,r), C['lg']))
        style.append(('BACKGROUND', (3,r),(3,r), C['lp']))
    qt.setStyle(TableStyle(style))
    items.append(qt)
    items.append(Paragraph('* session_log ไม่มี auto-purge — รัน /cleaning-sessions เพื่อลบ transcript เก่า', ST['caption']))
    items.append(Spacer(1, 0.8*cm))

    # Skills ที่เกี่ยวข้อง
    items.append(Paragraph('Skills ที่เกี่ยวข้อง', ST['h2']))
    skill_rows = [
        ('/setup-session-log',   'ติดตั้งระบบทั้งหมดครั้งแรก รวม memory/auto/ files'),
        ('/session-summary',     'backfill session ที่ Haiku summarize ไม่สำเร็จ'),
        ('/session-index',       'สร้าง monthly index ของ session_log'),
        ('/harvest-insights',    'สกัด insights จาก session ปัจจุบันลง memory/skill'),
        ('/cleaning-sessions',   'ลบ transcript เก่าเพื่อประหยัด disk'),
    ]
    sr_rows = []
    for cmd, desc in skill_rows:
        sr_rows.append([
            Paragraph(cmd, ParagraphStyle('sc', fontName='Courier',
                fontSize=9, leading=13, textColor=C['blue'])),
            Paragraph(desc, ST['body']),
        ])
    st_t = Table(sr_rows, colWidths=[4.5*cm, CW - 4.5*cm])
    st_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C['card_bg']),
        ('BOX',           (0,0),(-1,-1), 1, C['border']),
        ('LINEBELOW',     (0,0),(-1,-2), 0.3, C['border']),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,0),(1,-1), [C['lb'], C['card_bg']]),
    ]))
    items.append(st_t)

    return items

# ─── Build PDF ────────────────────────────────────────────────────────────────
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 0.75*cm, bottomMargin=MARGIN + 0.4*cm,
        title='zen-session-log', author='zennnne',
    )
    story = []
    frame_h = PAGE_H - (MARGIN + 0.75*cm) - (MARGIN + 0.4*cm)
    story.append(Spacer(1, frame_h - 1*cm))
    story.append(PageBreak())
    story.extend(build_overview())
    story.extend(build_session_log_page())
    story.extend(build_digest_page())
    story.extend(build_mistakes_page())
    story.extend(build_quickref())
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF saved: {output_path}')

if __name__ == '__main__':
    import sys, io, os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'zen-session_log-detail.pdf')
    build_pdf(out)
