"""
zen-skills PDF Catalog Generator  v2
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
import datetime

# ─── Fonts ────────────────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont('TH', r'C:\Windows\Fonts\leelawad.ttf'))
pdfmetrics.registerFont(TTFont('Emoji', r'C:\Windows\Fonts\seguiemj.ttf'))

def clean(text):
    """Replace chars unsupported by Leelawadee with safe alternatives."""
    return text.replace('→', '>').replace('←', '<').replace('↔', '<>')

def me(text):
    """Wrap emoji codepoints with <font name='Emoji'>...</font> for inline rendering."""
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
    'orange':  colors.HexColor('#BF360C'),
    'pink':    colors.HexColor('#AD1457'),
    'gold':    colors.HexColor('#F57F17'),
    'card_bg': colors.HexColor('#F8FAFC'),
    'border':  colors.HexColor('#CBD5E1'),
    'text':    colors.HexColor('#1E293B'),
    'muted':   colors.HexColor('#64748B'),
    'white':   colors.white,
    'light':   colors.HexColor('#EEF2FF'),
    # owner accent
    'zen':     colors.HexColor('#1565C0'),
    '9arm':    colors.HexColor('#1B5E20'),
    'matt':    colors.HexColor('#4527A0'),
    'karp':    colors.HexColor('#BF360C'),
    'doc':     colors.HexColor('#006064'),
}

# Tier colors
TIER_COLORS = {
    'S+': colors.HexColor('#B71C1C'),
    'S':  colors.HexColor('#E65100'),
    'A':  colors.HexColor('#1565C0'),
    'B':  colors.HexColor('#2E7D32'),
    'C':  colors.HexColor('#546E7A'),
}

TIER_BG = {
    'S+': colors.HexColor('#FFEBEE'),
    'S':  colors.HexColor('#FFF3E0'),
    'A':  colors.HexColor('#E3F2FD'),
    'B':  colors.HexColor('#E8F5E9'),
    'C':  colors.HexColor('#ECEFF1'),
}

# Skill type colors
TYPE_COLORS = {
    '💉': colors.HexColor('#6A1B9A'),
    '🏗️': colors.HexColor('#1565C0'),
    '🔍': colors.HexColor('#0D47A1'),
    '🔥': colors.HexColor('#E65100'),
    '📝': colors.HexColor('#00695C'),
    '🔧': colors.HexColor('#37474F'),
}

PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
CW = PAGE_W - 2 * MARGIN   # content width

# ─── Styles ──────────────────────────────────────────────────────────────────
def S(name, **kw):
    kw.setdefault('fontName', 'TH')
    return ParagraphStyle(name, **kw)

STYLES = {
    # Section banners
    'sec_title':  S('st', fontSize=22, leading=30, textColor=C['white'], spaceBefore=0, spaceAfter=2),
    'sec_sub':    S('ss', fontSize=11, leading=16, textColor=colors.HexColor('#B3E5FC'), spaceBefore=0),
    # Install
    'h1':         S('h1', fontSize=19, leading=26, textColor=C['navy'], spaceBefore=14, spaceAfter=6),
    'h2':         S('h2', fontSize=13, leading=20, textColor=C['blue'], spaceBefore=10, spaceAfter=4),
    'step':       S('step', fontSize=12, leading=20, textColor=C['blue'], spaceBefore=8, spaceAfter=4),
    'body':       S('bd', fontSize=10, leading=15, textColor=C['text'], spaceAfter=3, alignment=TA_JUSTIFY),
    'body_sm':    S('bsm', fontSize=9, leading=14, textColor=C['muted']),
    'mono':       S('mn', fontName='Courier', fontSize=9, leading=14,
                    textColor=colors.HexColor('#1A237E'),
                    backColor=colors.HexColor('#E8EAF6'),
                    leftIndent=6, spaceBefore=2, spaceAfter=4),
    # Card header
    'skill_name': S('sn', fontSize=14, leading=19, textColor=C['white'], spaceBefore=0),
    'skill_cmd':  S('sc', fontSize=9.5, leading=14, textColor=colors.HexColor('#B3E5FC')),
    # Tier / Type labels
    'label_tiny': S('lt', fontSize=7.5, leading=11, textColor=C['muted']),
    'tier_text':  S('tt', fontSize=12, leading=16, textColor=C['white'], alignment=TA_CENTER),
    # Body fields
    'field_lbl':  S('fl', fontSize=8, leading=11, textColor=C['blue2'], spaceBefore=4, spaceAfter=1),
    'field_body': S('fb', fontSize=9.5, leading=14, textColor=C['text'], spaceAfter=3, alignment=TA_JUSTIFY),
    # Tier defs
    'tier_def_hd': S('tdh', fontSize=15, leading=22, textColor=C['navy'], spaceBefore=10, spaceAfter=4),
    'tier_def_b':  S('tdb', fontSize=10, leading=15, textColor=C['text']),
    # TOC
    'toc_h':      S('toch', fontSize=12, leading=18, textColor=C['blue'], spaceBefore=8),
    'toc_item':   S('toci', fontSize=10, leading=16, textColor=C['text']),
}

# ─── Career tag colors by career keyword ─────────────────────────────────────
CAREER_TAG_COLORS = {
    'Developer':   (colors.HexColor('#1565C0'), colors.HexColor('#E3F2FD')),
    'Senior Dev':  (colors.HexColor('#0D47A1'), colors.HexColor('#BBDEFB')),
    'Tech Lead':   (colors.HexColor('#4527A0'), colors.HexColor('#EDE7F6')),
    'Architect':   (colors.HexColor('#4A148C'), colors.HexColor('#F3E5F5')),
    'AI Engineer': (colors.HexColor('#006064'), colors.HexColor('#E0F7FA')),
    'ML Engineer': (colors.HexColor('#00695C'), colors.HexColor('#E0F2F1')),
    'QA Engineer': (colors.HexColor('#1B5E20'), colors.HexColor('#E8F5E9')),
    'DevOps':      (colors.HexColor('#BF360C'), colors.HexColor('#FBE9E7')),
    'SRE':         (colors.HexColor('#BF360C'), colors.HexColor('#FBE9E7')),
    'Data':        (colors.HexColor('#880E4F'), colors.HexColor('#FCE4EC')),
    'PM':          (colors.HexColor('#E65100'), colors.HexColor('#FFF3E0')),
    'Designer':    (colors.HexColor('#AD1457'), colors.HexColor('#FCE4EC')),
    'Marketing':   (colors.HexColor('#F57F17'), colors.HexColor('#FFFDE7')),
    'Writer':      (colors.HexColor('#2E7D32'), colors.HexColor('#E8F5E9')),
    'Student':     (colors.HexColor('#37474F'), colors.HexColor('#ECEFF1')),
    'Manager':     (colors.HexColor('#4E342E'), colors.HexColor('#EFEBE9')),
    'Finance':     (colors.HexColor('#1A237E'), colors.HexColor('#E8EAF6')),
    'Operations':  (colors.HexColor('#33691E'), colors.HexColor('#F1F8E9')),
    'Content':     (colors.HexColor('#6A1B9A'), colors.HexColor('#F3E5F5')),
    'Game Dev':    (colors.HexColor('#004D40'), colors.HexColor('#E0F2F1')),
    'Startup':     (colors.HexColor('#E65100'), colors.HexColor('#FFF3E0')),
    'Power User':  (colors.HexColor('#546E7A'), colors.HexColor('#ECEFF1')),
    'Everyone':    (colors.HexColor('#1B5E20'), colors.HexColor('#E8F5E9')),
}

def career_pill(career_str):
    """Build career tag pills from comma-sep string."""
    tags = [t.strip() for t in career_str.split(',')]
    cells = []
    for tag in tags:
        # find best matching key
        fg, bg = colors.HexColor('#37474F'), colors.HexColor('#ECEFF1')
        for k, (f, b) in CAREER_TAG_COLORS.items():
            if k.lower() in tag.lower():
                fg, bg = f, b
                break
        p = Paragraph(tag, ParagraphStyle('ptag', fontName='TH',
            fontSize=8, leading=11, textColor=fg))
        cell_t = Table([[p]], colWidths=[None])
        cell_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 7),
            ('RIGHTPADDING', (0,0), (-1,-1), 7),
            ('BOX', (0,0), (-1,-1), 0.5, fg),
            ('ROUNDEDCORNERS', [10,10,10,10]),
        ]))
        cells.append(cell_t)
    # lay them out in a row
    if not cells:
        return Paragraph('—', STYLES['field_body'])
    row_table = Table([cells], colWidths=[None]*len(cells), hAlign='LEFT')
    row_table.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return row_table

def tier_badge(tier):
    color = TIER_COLORS.get(tier, C['muted'])
    bg = TIER_BG.get(tier, colors.HexColor('#ECEFF1'))
    p = Paragraph(f'<b>{tier}</b>', ParagraphStyle('tb', fontName='TH',
        fontSize=11, leading=15, textColor=color, alignment=TA_CENTER))
    t = Table([[p]], colWidths=[1.2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('BOX', (0,0), (-1,-1), 1.5, color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    return t

def type_badge(type_emoji, type_name):
    tc = TYPE_COLORS.get(type_emoji, C['muted'])
    p = Paragraph(me(f'{type_emoji} {type_name}'), ParagraphStyle('typb', fontName='TH',
        fontSize=8.5, leading=12, textColor=tc))
    t = Table([[p]])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('BOX', (0,0), (-1,-1), 0.8, tc),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    return t

# ─── Page decorator ──────────────────────────────────────────────────────────
def on_page(canvas, doc):
    if doc.page == 1:
        # Cover bg
        canvas.saveState()
        canvas.setFillColor(C['navy'])
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # accent stripe
        canvas.setFillColor(C['blue2'])
        canvas.rect(0, PAGE_H*0.44, PAGE_W, 0.35*cm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor('#42A5F5'))
        canvas.rect(0, PAGE_H*0.44 - 0.15*cm, PAGE_W, 0.12*cm, fill=1, stroke=0)
        # Title
        canvas.setFont('TH', 52)
        canvas.setFillColor(C['white'])
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.60, 'zen-skills')
        canvas.setFont('TH', 20)
        canvas.setFillColor(colors.HexColor('#90CAF9'))
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.54, 'คู่มือ Skill Collection สำหรับ Claude Code')
        # Stats bar
        canvas.setFillColor(colors.HexColor('#162032'))
        canvas.roundRect(MARGIN*2, PAGE_H*0.37, CW - MARGIN*2, 3.0*cm, 8, fill=1, stroke=0)
        stats = [('5', 'ผู้สร้าง'), ('48+', 'สกิลรวม'), ('5', 'Tiers'), ('∞', 'ความเป็นไปได้')]
        col_w = (CW - MARGIN*2) / len(stats)
        for i, (num, lbl) in enumerate(stats):
            x = MARGIN*2 + col_w*i + col_w/2
            canvas.setFont('TH', 20)
            canvas.setFillColor(colors.HexColor('#42A5F5'))
            canvas.drawCentredString(x, PAGE_H*0.43, num)
            canvas.setFont('TH', 9)
            canvas.setFillColor(colors.HexColor('#90CAF9'))
            canvas.drawCentredString(x, PAGE_H*0.405, lbl)
        canvas.setFont('TH', 9)
        canvas.setFillColor(colors.HexColor('#546E7A'))
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.33, f'Updated: {datetime.datetime.now().strftime("%d %B %Y")}')
        canvas.setFillColor(colors.HexColor('#42A5F5'))
        canvas.drawCentredString(PAGE_W/2, PAGE_H*0.305, 'github.com/zennnne/zen-skills')
        canvas.restoreState()
        return
    canvas.saveState()
    canvas.setFillColor(C['navy'])
    canvas.rect(0, PAGE_H - 0.75*cm, PAGE_W, 0.75*cm, fill=1, stroke=0)
    canvas.setFont('TH', 7.5)
    canvas.setFillColor(colors.HexColor('#90CAF9'))
    canvas.drawString(MARGIN, PAGE_H - 0.52*cm, 'zen-skills Catalog')
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.52*cm, 'Claude Code Skill Collection')
    canvas.setFillColor(C['border'])
    canvas.rect(MARGIN, 0.55*cm, CW, 0.02*cm, fill=1, stroke=0)
    canvas.setFont('TH', 7.5)
    canvas.setFillColor(C['muted'])
    canvas.drawCentredString(PAGE_W/2, 0.35*cm, f'— {doc.page} —')
    canvas.restoreState()

# ─── Section banner ──────────────────────────────────────────────────────────
def section_banner(emoji, title, subtitle, owner_key):
    bg = C.get(owner_key, C['blue'])
    inner = Table([
        [Paragraph(me(f'{emoji}  {title}'), STYLES['sec_title'])],
        [Paragraph(subtitle, STYLES['sec_sub'])],
    ], colWidths=[CW - 32])
    inner.setStyle(TableStyle([
        ('TOPPADDING', (0,0),(-1,-1), 4), ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0),(-1,-1), 0), ('RIGHTPADDING', (0,0),(-1,-1), 0),
    ]))
    outer = Table([[inner]], colWidths=[CW])
    outer.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), bg),
        ('TOPPADDING', (0,0),(-1,-1), 14), ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING', (0,0),(-1,-1), 16), ('RIGHTPADDING', (0,0),(-1,-1), 16),
        ('ROUNDEDCORNERS', [6,6,0,0]),
    ]))
    return outer

# ─── Skill Card ──────────────────────────────────────────────────────────────
def skill_card(data, owner_key):
    accent = C.get(owner_key, C['blue'])

    # ── header
    tier_b = tier_badge(data['tier'])
    type_b = type_badge(data['type_emoji'], data['type_name'])
    name_p = Paragraph(f'/{data["name"]}', STYLES['skill_name'])
    cmd_p  = Paragraph(data['cmd'], STYLES['skill_cmd'])

    header_rows = [
        [name_p, '', tier_b],
        [cmd_p, type_b, ''],
    ]
    hdr = Table(header_rows, colWidths=[CW*0.52, CW*0.32, CW*0.16])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), accent),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (0,-1), 14),
        ('LEFTPADDING', (1,0), (1,-1), 6),
        ('RIGHTPADDING', (-1,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (0,0), (0,0)),
        ('SPAN', (2,0), (2,1)),
    ]))

    # ── body fields
    FIELD_COLORS = {
        'ทำอะไร':           colors.HexColor('#1565C0'),
        'ใช้ยังไง':         colors.HexColor('#00695C'),
        'เหมาะกับสถานการณ์': colors.HexColor('#6A1B9A'),
    }
    fields = [
        ('ทำอะไร',            clean(data['what'])),
        ('ใช้ยังไง',          clean(data['how_to_use'])),
        ('เหมาะกับสถานการณ์', clean(data['when'])),
    ]
    body_rows = []
    for lbl, content in fields:
        lc = FIELD_COLORS.get(lbl, C['blue'])
        lbl_p = Paragraph(f'<b>{lbl}</b>', ParagraphStyle('lx', fontName='TH',
            fontSize=8, leading=11, textColor=lc))
        cnt_p = Paragraph(content, STYLES['field_body'])
        row = Table([[lbl_p, cnt_p]], colWidths=[2.1*cm, CW - 2.1*cm])
        row.setStyle(TableStyle([
            ('TOPPADDING', (0,0),(-1,-1), 6),
            ('BOTTOMPADDING', (0,0),(-1,-1), 6),
            ('LEFTPADDING', (0,0),(0,-1), 12),
            ('LEFTPADDING', (1,0),(1,-1), 8),
            ('RIGHTPADDING', (-1,0),(-1,-1), 12),
            ('VALIGN', (0,0),(-1,-1), 'TOP'),
            ('LINEBELOW', (0,0),(-1,-1), 0.3, C['border']),
        ]))
        body_rows.append([row])

    # ── careers row
    career_pills = career_pill(data['careers'])
    career_label = Paragraph('<b>สายงาน</b>', ParagraphStyle('cl', fontName='TH',
        fontSize=8, leading=11, textColor=colors.HexColor('#1B5E20')))
    career_row = Table([[career_label, career_pills]],
                       colWidths=[2.1*cm, CW - 2.1*cm])
    career_row.setStyle(TableStyle([
        ('TOPPADDING', (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(0,-1), 12),
        ('LEFTPADDING', (1,0),(1,-1), 8),
        ('RIGHTPADDING', (-1,0),(-1,-1), 12),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
    ]))
    body_rows.append([career_row])

    body_t = Table(body_rows, colWidths=[CW])
    body_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), C['card_bg']),
        ('TOPPADDING', (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING', (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
    ]))

    outer = Table([[hdr], [body_t]], colWidths=[CW])
    outer.setStyle(TableStyle([
        ('TOPPADDING', (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING', (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('BOX', (0,0),(-1,-1), 1.2, accent),
        ('ROUNDEDCORNERS', [6,6,6,6]),
    ]))
    return outer

# ─── Skill Data ──────────────────────────────────────────────────────────────
# type_emoji + type_name  (see definition page)
# tier: S+, S, A, B, C

SKILLS = {
  'zen': [
    dict(
      name='harvest-insights', tier='S+', type_emoji='🔧', type_name='Utility',
      cmd='/harvest-insights',
      what='สั่งให้ claude หาเนื้อหาที่มีประโยชน์น่าเก็บไว้ใน memory/skill พร้อมแยกเป็นเรื่องๆ, ร่าง draft และไล่ถาม user ทีละตัวว่าอยากเก็บไหม ได้ insights ที่สำคัญ ได้สกิล หรือจะใช้หลังสอนงานมันก็ได้ สกิลเดียวแต่สะดวกสุดๆ!!',
      how_to_use='รันตอนจบ session ที่มี research, debug pattern ใหม่, หรือ user สอน Claude บางอย่าง ตอบ save / skip / edit ทีละข้อ ไม่ batch',
      when='session มี WebSearch, user แก้ Claude หลายครั้ง, หรือเรียนรู้ workflow ใหม่ที่จะใช้อีก — ถ้า session routine ไม่จำเป็น',
      careers='Everyone',
    ),
    dict(
      name='craft-skill', tier='S', type_emoji='🏗️', type_name='Builder',
      cmd='/craft-skill [topic]',
      what='ค้นก่อนว่ามีคนทำ skill นี้แล้วยัง ถ้ายังก็วิจัยหาข้อมูล ร่าง SKILL.md ใหม่ แล้วทดสอบกับ fresh Claude จริงๆ ก่อน save — มี 6 phase ครบ ทำให้ skill ที่ได้ใช้งานได้จริง ไม่ใช่แค่ดูดี',
      how_to_use='บอก topic เช่น /craft-skill "git rebase strategy" จะ scout GitHub ก่อน ถ้าไม่มีค่อย research เอง แล้วให้อนุมัติก่อน save',
      when='อยากเก็บ how-to ที่เพิ่งเรียนรู้ไว้ใช้ใน session อื่น — เหมาะกับทุก topic ที่จะทำซ้ำ',
      careers='Everyone',
    ),
    dict(
      name='reviewing-code', tier='S', type_emoji='🔍', type_name='Reviewer',
      cmd='/reviewing-code [path] [--scope] [--no-validate]',
      what='ส่ง 4 agents วิ่งพร้อมกัน แต่ละตัว focus คนละด้าน: correctness, security, performance, maintainability — มี judge กรอง false positive ก่อนสรุป ได้รายงาน prioritized พร้อม fix ดีกว่า review คนเดียวมากๆ',
      how_to_use='รันที่ project root หรือระบุ /reviewing-code src/ --scope=bugs,security มี --no-validate ถ้าต้องการ fast mode (เสี่ยง false positive มากขึ้น)',
      when='ก่อน merge PR สำคัญ, code health check รายไตรมาส, หรือ hand off codebase ให้ทีมใหม่ — ครอบคลุมกว่า /auditing-security แต่ไม่ deep เท่าด้าน security',
      careers='Developer, Tech Lead, QA Engineer',
    ),
    dict(
      name='auditing-security', tier='S', type_emoji='🔍', type_name='Reviewer',
      cmd='/auditing-security [path] [--guidelines file]',
      what='ส่ง 8 security specialist agents ตรวจพร้อมกัน ครอบ OWASP Top 10, injection, auth bypass, crypto, race conditions และอีกเยอะ — ได้รายงาน CVSS-scored พร้อม remediation roadmap จัดลำดับตามความเสี่ยงเลย',
      how_to_use='รัน /auditing-security src/ ใช้เวลา 5-10 นาที ได้รายงาน risk-scored พร้อม remediation roadmap สามารถเพิ่ม --guidelines ใส่ custom policy ได้',
      when='ก่อน release สำคัญ, compliance audit (PCI/SOC2), CVE scan บน dependencies — ไม่ใช้สำหรับ general bug hunting, ใช้ /reviewing-code แทน',
      careers='Developer, DevOps, Tech Lead',
    ),
    dict(
      name='designing-subagent-systems', tier='S', type_emoji='🔍', type_name='Reviewer',
      cmd='/designing-subagent-systems',
      what='ช่วยเลือก "shape" ของ multi-agent workflow ว่าควรเป็น sequential / parallel / orchestrator-workers หรืออะไร พร้อม brief templates และ anti-patterns 13 ข้อที่พบบ่อย — ก่อน implement จริงดีมากๆ',
      how_to_use='อธิบาย task ที่ต้องการ delegate เช่น "มี N tasks อิสระกัน อยากทำ parallel" จะได้ workflow shape + brief templates + cost estimate (~15× vs single-agent)',
      when='ออกแบบ automation pipeline, วิเคราะห์ว่า multi-agent คุ้มหรือเปล่า, หรือ debug ว่าทำไม agents ช้า/แพง/ผิด',
      careers='AI Engineer, Tech Lead, Architect',
    ),
    dict(
      name='crafting-skills-deeply', tier='A', type_emoji='🏗️', type_name='Builder',
      cmd='/crafting-skills-deeply [topic]',
      what='เหมือน /craft-skill แต่ heavy-duty — แตก topic ออกเป็น subtopics แล้วส่ง parallel researchers ค้นพร้อมกัน มี critique loop กับ skill-critic ด้วย ใช้ tokens เยอะกว่า ~15x แต่ skill ที่ได้มีคุณภาพสูงกว่ามาก',
      how_to_use='รันเมื่อ topic span หลาย subtopic หรือต้องการ citation จะถาม source (web/local/mix) และ rigor level ก่อน research ถ้า topic ง่าย fallback กลับไป /craft-skill อัตโนมัติ',
      when='Topic ยาก, ต้องการ citation-backed claims, หรือ skill จะถูกใช้บ่อยมากจนคุ้มค่า cost — ถ้าธรรมดาใช้ /craft-skill ประหยัดกว่า',
      careers='Everyone',
    ),
    dict(
      name='designing-agent-roles', tier='A', type_emoji='🔍', type_name='Reviewer',
      cmd='/designing-agent-roles',
      what='ออกแบบแต่ละ agent ในระบบ — กำหนด tools แค่ที่จำเป็น เลือก model tier ให้ประหยัด cost 60-70% และเขียน system prompt ให้ถูก จบแล้วได้ YAML frontmatter + prompt body พร้อม save เลย',
      how_to_use='บอก role ที่ต้องการเช่น "ออกแบบ code-reviewer agent ที่ read-only" จะได้ frontmatter yaml + system prompt body พร้อม quick checklist ก่อน save',
      when='สร้าง multi-agent workflow ใหม่ หรือ optimize agent เดิมที่ได้ tool เกินความจำเป็น — ใช้คู่กับ /designing-subagent-systems',
      careers='AI Engineer, Tech Lead, Developer',
    ),
    dict(
      name='wahahaha', tier='A', type_emoji='🔧', type_name='Utility',
      cmd='/wahahaha',
      what='Wizard ตั้งค่าทุกอย่างในครั้งเดียว — ถามทีละ plugin ว่าอยากได้ไหม ตอบใช่/ไม่แล้วมันจัดการให้หมดเลย ไม่ต้องจำคำสั่ง install เอง ใช้ครั้งเดียวพอต่อเครื่อง',
      how_to_use='รัน /wahahaha ทันทีหลัง install zen-skills — มันจะถามทีละตัว: session log, karpathy, mattpocock, document-skills, 9arm ตอบใช่/ไม่ทีละอัน',
      when='ครั้งแรกบนเครื่องใหม่หรือหลัง format — ประหยัดเวลาแทนที่จะจำคำสั่ง /plugin install ทั้งหมด',
      careers='Everyone',
    ),
    dict(
      name='extracting-youtube-transcript', tier='A', type_emoji='🔧', type_name='Utility',
      cmd='/extracting-youtube-transcript [YouTube URL]',
      what='วาง YouTube link แล้วได้ transcript ทั้งวิดีโอออกมาเป็นไฟล์ทันที — ใช้ Playwright คลิกเอง ไม่ถูก IP block เหมือน API ตรง สรุป lecture หรือ podcast ยาวๆ ได้เลยโดยไม่ต้องฟังทั้งคลิป',
      how_to_use='วาง YouTube URL เช่น /extracting-youtube-transcript https://youtube.com/watch?v=xxx รอสักครู่ได้ summary + transcript file — รองรับทั้ง youtube.com และ youtu.be',
      when='สรุป lecture, tutorial, podcast บน YouTube หรือ quote เนื้อหาวิดีโอ — ใช้ไม่ได้กับ live stream หรือวิดีโอที่ไม่มี caption',
      careers='Everyone',
    ),
    dict(
      name='audit-skills', tier='A', type_emoji='🔍', type_name='Reviewer',
      cmd='/audit-skills',
      what='สแกน skills ทั้งหมดหา description ที่มีปัญหา: คลุมเครือเกินไป ขาด trigger keyword หรือ overlap กัน — เสนอ fix พร้อม before/after diff แล้วถาม approve ทีละอัน ทำให้ Claude trigger skill ถูกตัวมากขึ้น',
      how_to_use='รัน /audit-skills ได้เลย scan ~/.claude/skills/ และ ~/.claude/plugins/marketplaces/ ตอบ apply/skip/edit ทีละรายการ — ไม่แก้ official Anthropic skills',
      when='หลัง install skills ใหม่เยอะ หรือรู้สึกว่า Claude ไม่ trigger skill ที่ถูกต้อง เหมาะทำ monthly maintenance',
      careers='Developer, Power User',
    ),
    dict(
      name='setup-session-log', tier='A', type_emoji='🔧', type_name='Utility',
      cmd='/setup-session-log',
      what='ติดตั้ง session logging system ครั้งเดียว — copy hook scripts และ register ใน settings.json แล้วทุก session จะ auto-summarize ด้วย Haiku ให้เอง ไม่ต้องทำเองอีกเลย',
      how_to_use='รัน /setup-session-log ครั้งเดียว (หรือผ่าน /wahahaha ที่รวมขั้นนี้ไว้แล้ว) จะ copy hooks, สร้าง ~/.claude/session_log/, เพิ่ม hook ใน settings.json',
      when='ครั้งแรกบนเครื่องใหม่หรือหลัง reinstall Claude Code — ถ้าใช้ /wahahaha แล้วขั้นนี้ถูกรวมไปแล้ว ไม่ต้องรันซ้ำ',
      careers='Developer, Power User',
    ),
    dict(
      name='updating-plugins', tier='B', type_emoji='🔧', type_name='Utility',
      cmd='/updating-plugins',
      what='อัปเดต plugins 4 ตัวในคำสั่งเดียว แต่ละตัวมีวิธี update ต่างกัน มันจัดการให้หมด แล้วบอกด้วยว่ามี skill ใหม่ไหนที่ยังไม่ได้ install — restart Claude Code หลังรันก็พร้อมใช้',
      how_to_use='รัน /updating-plugins ได้เลย ไม่ต้อง argument — ควร restart Claude Code หลังรัน เพื่อให้ update มีผล',
      when='รันเป็นประจำทุกเดือน หรือเมื่อต้องการ skill ใหม่จาก plugins',
      careers='Developer, Power User',
    ),
    dict(
      name='session-summary', tier='B', type_emoji='📝', type_name='Writer',
      cmd='/session-summary [date | session-id]',
      what='เติม placeholder ใน daily log ที่ Haiku summarize ไม่สำเร็จ — อ่าน transcript แล้วสรุป: title, สิ่งที่ทำ, decisions, mistakes, followup ครบ ใช้ตอน auto-summary failed หรือ backfill log เก่า',
      how_to_use='รัน /session-summary เพื่อ fill วันนี้ หรือระบุ /session-summary 2025-05-20 แก้ไขเฉพาะ placeholder ที่ค้าง ไม่แตะ entry ที่ fill แล้ว',
      when='เห็น "auto-summary failed" ใน session log, หลัง session ยาวที่ hook timeout, หรือ backfill log เก่า',
      careers='Developer, Power User',
    ),
    dict(
      name='session-index', tier='B', type_emoji='📝', type_name='Writer',
      cmd='/session-index [YYYY-MM]',
      what='สร้าง monthly index รวม title, date, status, mistakes ของทุก session เป็น table ค้นได้ มี stats summary และ tag recurring mistakes — รันตอนสิ้นเดือนหรือเมื่อต้องการค้นหา session เก่า',
      how_to_use='รัน /session-index เพื่อ generate เดือนปัจจุบัน หรือ /session-index 2025-04 สำหรับเดือนอื่น — overwrite ไฟล์เดิมถ้ามี',
      when='รันตอนสิ้นเดือนหรือเมื่อต้องการค้นหา session เก่า — recurring mistake tags ช่วย harvest-insights ระยะยาว',
      careers='Developer, Power User',
    ),
    dict(
      name='applying-3-act-structure', tier='B', type_emoji='📝', type_name='Writer',
      cmd='/applying-3-act-structure',
      what='วิเคราะห์หรือวาง outline narrative ด้วย three-act framework — บอกได้ว่า story ติดขัดตรงไหน หรือช่วย plan key beats ตั้งแต่ Inciting Incident ยัน Denouement ใช้ได้กับ story, screenplay, หรือ presentation',
      how_to_use='วาง draft story หรืออธิบาย premise แล้วรัน — จะวิเคราะห์ว่าแต่ละ act ทำงานถูกต้องไหม หรือช่วย outline ใหม่',
      when='เขียน story, screenplay, presentation, หรือ diagnose ว่า narrative ติดขัดตรงไหน เช่น saggy middle',
      careers='Writer, Content, Game Dev, PM',
    ),
    dict(
      name='cleaning-sessions', tier='C', type_emoji='🔧', type_name='Utility',
      cmd='/cleaning-sessions [days]',
      what='ลบ .jsonl transcript เก่ากว่า N วันเพื่อประหยัด disk — dry run ก่อนบอกว่าจะลบกี่ไฟล์ขนาดเท่าไหร่ แล้วถาม confirm อีกครั้ง ไม่แตะ memory / skills / settings',
      how_to_use='รัน /cleaning-sessions หรือ /cleaning-sessions 30 จะแสดงจำนวนไฟล์และขนาด แล้วถามยืนยัน',
      when='disk เริ่มเต็ม หรือ housekeeping ประจำเดือน — session เก่ากว่า 30 วันมักไม่จำเป็น',
      careers='Developer, Power User',
    ),
  ],

  '9arm': [
    dict(
      name='scrutinize', tier='S+', type_emoji='🔍', type_name='Reviewer',
      cmd='Agent(subagent_type="9arm-skills:scrutinize", prompt="scrutinize [PR/plan/change]...")',
      what='review แบบคนนอก — ตั้งคำถามก่อนว่า change นี้ควรมีอยู่จริงไหม แล้ว trace code path จากต้นจนจบจริงๆ ทุก finding มี evidence ชัดเจน ไม่ rubber-stamp เลย เหมาะมากสำหรับ PR สำคัญหรือ architecture decision',
      how_to_use='วิธีที่ถูกต้อง: spawn agent เข้ามา scrutinize เช่น Agent(subagent_type="9arm-skills:scrutinize", prompt="scrutinize this PR diff: [diff]") ผ่าน 4 ขั้น: Intent → Trace call graph → Verify edge cases → Report (verdict: ship/fix/rework/reject)',
      when='ก่อน merge PR สำคัญ, review architecture decision, หรือต้องการ second opinion ที่ไม่ลำเอียง — Claude auto-trigger เมื่อ user ขอ review/sanity-check',
      careers='Developer, Tech Lead, Architect',
    ),
    dict(
      name='debug-mantra', tier='S', type_emoji='💉', type_name='Discipline Injector',
      cmd='/debug-mantra',
      what='ปลูก 4 mantra ให้ Claude ก่อน debug: reproduce ก่อน > รู้ fail path > falsify hypothesis > ทุก run คือ breadcrumb — Claude จะไม่เสนอ fix จนกว่าจะ reproduce ได้จริง ตัดปัญหาเดาสุ่มไปได้เลย',
      how_to_use='รัน /debug-mantra แล้วอธิบาย bug — Claude ท่อง mantra 4 ข้อ verbatim แล้วทำตามลำดับเคร่ง: สร้าง repro → trace fail path → list hypotheses 3-5 → falsify ทีละตัว → บันทึก ledger ทุก experiment',
      when='Debug bug ยากหรือ flaky bug ที่หาสาเหตุไม่เจอ — โดยเฉพาะ bug ที่เดา hypothesis แล้วผิดซ้ำๆ ใช้คู่กับ /post-mortem หลังหา fix ได้',
      careers='Developer, SRE',
    ),
    dict(
      name='post-mortem', tier='A', type_emoji='📝', type_name='Writer',
      cmd='/post-mortem',
      what='เขียน engineering record ของ bug ที่ fix แล้ว — root cause, mechanism, fix commit, validation ครบ ระบุ function names, file paths, SHA ชัดเจน เพื่อให้ engineer คนต่อไปหาเจอได้เร็วโดยไม่ต้อง debug ซ้ำ',
      how_to_use='รัน /post-mortem หลัง fix validated แล้วเท่านั้น ต้องมีครบ 4 อย่าง: reliable repro + known root cause + fix commit + validated fix Claude ตรวจก่อน draft จากนั้นสามารถส่งต่อ output ให้ /management-talk ได้',
      when='หลัง debug session fix สำเร็จ ก่อนปิด ticket — ไม่ใช้กับ trivial fix (typo) หรือ customer outage (ต้องการ incident report แยก)',
      careers='Developer, SRE, Tech Lead',
    ),
    dict(
      name='management-talk', tier='A', type_emoji='📝', type_name='Writer',
      cmd='/management-talk',
      what='แปลง technical content เป็นภาษาที่ PM/VP อ่านได้ เลือก channel ได้เลย: Slack brief, standup note, email, JIRA comment — แต่ละ format จัดให้เหมาะอัตโนมัติ ไม่ต้องเขียนเอง',
      how_to_use='วาง technical text หรือ JIRA key แล้วบอก channel เช่น "rewrite for Slack" หรือ "update for VP" Claude ถาม channel ถ้าไม่ชัดเจน แล้ว draft ให้ review ก่อน post',
      when='Update status ให้ PM/VP/director, เขียน standup note ที่ non-technical อ่านได้, หรือ translate post-mortem สำหรับ leadership',
      careers='Developer, Tech Lead, Manager, PM',
    ),
  ],

  'matt': [
    dict(
      name='grill-me', tier='S+', type_emoji='🔥', type_name='Challenger',
      cmd='/grill-me',
      what='ให้ Claude ถาม hard questions กับ plan ของเราอย่าง relentless ไม่รับคำตอบกำกวม — จนครบทุก decision branch และ edge case เหมาะมากก่อน present ให้ team หรือก่อนจะ commit ทำอะไรจริงๆ',
      how_to_use='วาง plan/design แล้วรัน /grill-me — Claude จะถาม "hard questions" ต่อเนื่องเรื่อง tradeoffs, edge cases, assumptions จนครบทุก branch ของ decision tree',
      when='ก่อน present plan ให้ team, ก่อน commit ไป architecture สำคัญ, หรือเมื่ออยากตรวจสอบว่าคิดครบแล้วหรือยัง',
      careers='Everyone',
    ),
    dict(
      name='grill-with-docs', tier='S+', type_emoji='🔥', type_name='Challenger',
      cmd='/grill-with-docs',
      what='เหมือน /grill-me แต่ cross-reference กับ CONTEXT.md และ ADRs ของ project ด้วย — ตรวจว่า plan สอดคล้องกับ domain model ที่ตกลงกันไว้ไหม แล้วเสนออัปเดต docs เมื่อตัดสินใจเรื่องใหม่',
      how_to_use='ใช้ใน project ที่มี CONTEXT.md หรือ docs/adr/ วาง plan แล้ว Claude จะ cross-reference กับ existing decisions แล้ว propose อัปเดต docs เมื่อตัดสินใจเรื่องใหม่',
      when='ก่อน implement feature ใหม่ใน project ที่มี established domain model, หรือ ensure consistency กับ architecture decisions',
      careers='Senior Dev, Tech Lead, Architect',
    ),
    dict(
      name='handoff', tier='S+', type_emoji='📝', type_name='Writer',
      cmd='/handoff',
      what='สรุป session ยาวๆ เป็น handoff document พร้อมให้ session ใหม่รับช่วงต่อทันที — ประหยัด tokens มาก ไม่ต้อง re-explain ทุกอย่างใหม่ ใช้ทุกครั้งที่ context เกือบเต็มหรือก่อนหยุดงาน',
      how_to_use='รัน /handoff เมื่อ session กำลัง end ระบุ "What will the next session be used for?" Claude จะ compile: current state + decisions made + next steps → handoff doc',
      when='Session ยาวและจะ continue ใน session ใหม่, handoff งานให้ colleague ที่ใช้ Claude Code, หรือ document state ก่อนหยุดงาน',
      careers='Everyone',
    ),
    dict(
      name='tdd', tier='A', type_emoji='💉', type_name='Discipline Injector',
      cmd='/tdd',
      what='บังคับ TDD จริงๆ — Claude เขียน failing test ก่อนเสมอ แล้ว implement จนผ่าน แล้ว refactor วนซ้ำ ไม่ข้ามขั้น ได้ code ที่ testable และมี regression test ติดมาด้วยทุกครั้ง',
      how_to_use='บอก feature ที่จะทำ Claude จะเขียน failing test ก่อนเสมอ แล้ว implement จนผ่าน วนจนครบ acceptance criteria — เหมาะกับ project ที่มี test runner อยู่แล้ว',
      when='Implement feature ใหม่ที่ต้องการ reliability สูง, fix bug ที่ต้องการ regression test, หรือ build code ที่ testable',
      careers='Developer, QA Engineer',
    ),
    dict(
      name='diagnose', tier='A', type_emoji='🔥', type_name='Challenger',
      cmd='/diagnose',
      what='guide ผ่าน 6 ขั้นตอน debug อย่างเป็นระบบ: reproduce > minimize > hypothesize > instrument > fix > regression test — ครบกว่า /debug-mantra เพราะรวม fix และ test ไว้ในตัวด้วย',
      how_to_use='อธิบาย bug หรือ performance regression ที่พบ Claude จะ guide ผ่าน 6 ขั้นตอน สร้าง minimal repro, list hypotheses, instrument, fix, และ write regression test',
      when='Debug bug หรือ performance regression ใช้คู่กับ /debug-mantra ได้ถ้าต้องการ mantra discipline เพิ่มเติม',
      careers='Developer, QA Engineer, SRE',
    ),
    dict(
      name='improve-codebase-architecture', tier='A', type_emoji='🔍', type_name='Reviewer',
      cmd='/improve-codebase-architecture',
      what='วิเคราะห์ codebase ด้วย domain language จาก CONTEXT.md และ ADRs แล้วแนะนำ refactoring ที่ทำให้ code testable และ navigate ได้ง่ายขึ้น — concrete steps ไม่ใช่แค่ advice กว้างๆ',
      how_to_use='รันใน project ที่มี CONTEXT.md หรือ ADR docs จะวิเคราะห์ coupling, cohesion, naming, แล้วเสนอ concrete refactoring steps',
      when='Codebase เริ่ม messy หรือยาก navigate, ก่อน major feature ที่ต้องการ foundation ดี, หรือ quarterly architecture review',
      careers='Senior Dev, Tech Lead, Architect',
    ),
    dict(
      name='prototype', tier='A', type_emoji='🏗️', type_name='Builder',
      cmd='/prototype',
      what='สร้าง throwaway prototype เร็วๆ เพื่อ explore design ก่อน commit จริง — มี 2 mode: terminal app สำหรับ test logic หรือ UI หลาย version ให้เปรียบเทียบ แล้วค่อย discard หรือ refine ต่อ',
      how_to_use='บอก design question เช่น "prototype state machine สำหรับ checkout flow" Claude สร้าง runnable code ให้ play with แล้ว discard หรือ refine ต่อ',
      when='ก่อน implement UI ที่ยังไม่แน่ใจ design, ทดสอบ data model ก่อน migration, หรือ explore API design โดยไม่ commit ใน codebase จริง',
      careers='Developer, Designer, PM',
    ),
    dict(
      name='write-a-skill', tier='A', type_emoji='🏗️', type_name='Builder',
      cmd='/write-a-skill',
      what='ช่วยสร้าง SKILL.md โดย guide ผ่าน structure ที่ถูกต้อง — ใช้เมื่อรู้ content แล้วและต้องการแค่ help ด้าน format ถ้ายังไม่รู้ content ใช้ /craft-skill แทน (มี research phase)',
      how_to_use='รัน /write-a-skill แล้วบอก skill ที่ต้องการ Claude จะ guide สร้าง SKILL.md structure ที่ถูกต้อง สำหรับ topic ที่ต้อง research ก่อน ใช้ /craft-skill แทน',
      when='รู้ content ที่จะใส่แล้วและต้องการ help กับ structure หรือ convert existing doc เป็น skill format',
      careers='Everyone',
    ),
    dict(
      name='zoom-out', tier='B', type_emoji='🔧', type_name='Utility',
      cmd='/zoom-out',
      what='ถ้า deep ลึกจน lost ใน code — /zoom-out แล้ว Claude อธิบายว่าส่วนนี้ fit ใน big picture ยังไง มี connection กับส่วนอื่นอย่างไร ดีมากตอนเพิ่งเข้า project ใหม่หรือกลับมาหลังหยุดนาน',
      how_to_use='รัน /zoom-out เมื่อรู้สึก lost ใน code Claude จะอธิบายว่า code ส่วนนี้ fit ใน big picture ยังไง มี connection กับส่วนอื่นอย่างไร',
      when='เพิ่งเข้าร่วม project ใหม่ หรือ deep ลึกใน detail จนลืม context รวม',
      careers='Developer, Student',
    ),
    dict(
      name='to-prd', tier='B', type_emoji='📝', type_name='Writer',
      cmd='/to-prd',
      what='แปลง conversation ที่คุยเรื่อง requirement ไว้เป็น PRD format พร้อม publish ไปยัง issue tracker — compile ทุกอย่างที่คุยกันมาเป็น structured document ที่ stakeholders อ่านได้เลย',
      how_to_use='หลัง discuss feature จนครบแล้ว รัน /to-prd Claude จะ compile เนื้อหาเป็น PRD structure พร้อม publish ให้ถ้ามี issue tracker integration',
      when='หลัง requirements gathering, document feature ก่อน development, หรือ handoff requirements ให้ทีม',
      careers='PM, Tech Lead, Developer',
    ),
    dict(
      name='handoff', tier='S+', type_emoji='📝', type_name='Writer',
      cmd='/handoff',
      what='สรุป session ยาวๆ เป็น handoff document พร้อมให้ session ใหม่รับช่วงต่อทันที — ประหยัด tokens มาก ไม่ต้อง re-explain ทุกอย่างใหม่ ใช้ทุกครั้งที่ context เกือบเต็มหรือก่อนหยุดงาน',
      how_to_use='รัน /handoff เมื่อ session กำลัง end ระบุ "What will the next session be used for?" Claude จะ compile: current state + decisions made + next steps → handoff doc',
      when='Session ยาวและจะ continue ใน session ใหม่, handoff งานให้ colleague ที่ใช้ Claude Code, หรือ document state ก่อนหยุดงาน',
      careers='Everyone',
    ),
    dict(
      name='caveman', tier='C', type_emoji='💉', type_name='Discipline Injector',
      cmd='/caveman',
      what='ตัดทุก filler word ออก ลด token ~75% — Claude ตอบสั้นมากตลอด session เช่น "file found. error line 42. fix: change x > y" ปิดได้ตลอดด้วยการบอก back to normal',
      how_to_use='รัน /caveman เพื่อเปิด mode ปิดด้วยการบอก "back to normal" Claude ตอบสั้นมากตลอด session',
      when='Session ยาวที่ context เต็ม, ต้องการ rapid iteration — ไม่เหมาะกับ explanation หรือ creative tasks',
      careers='Developer, Power User',
    ),
  ],

  'karp': [
    dict(
      name='karpathy-guidelines', tier='S+', type_emoji='💉', type_name='Discipline Injector',
      cmd='(auto-invoked เมื่อเขียน/review code)',
      what='ฉีด 4 behavioral rules จาก Andrej Karpathy เข้า Claude ก่อน code: คิดก่อน code, เปลี่ยนน้อยที่สุด, simplicity first, success criteria ชัด — ตัดปัญหา over-engineer และ scope creep ได้ดีมาก',
      how_to_use='ไม่ต้อง invoke เอง — Claude apply อัตโนมัติเมื่อ coding สามารถ /karpathy-guidelines เพื่อ remind ให้ follow อย่างเคร่งครัด เหมาะเป็นพิเศษเมื่อ Claude เริ่ม over-engineer',
      when='Apply ตลอดเวลาเมื่อ coding สำคัญเมื่อ: implement feature ที่ไม่แน่ใจ scope, refactor code ที่อาจ break, หรือเมื่อ Claude เริ่มเพิ่ม feature โดยไม่ได้ขอ',
      careers='Developer',
    ),
  ],

  'doc': [
    dict(
      name='xlsx', tier='S+', type_emoji='🏗️', type_name='Builder',
      cmd='/xlsx',
      what='บอก layout เป็นภาษาคนแล้วได้ Excel spreadsheet ที่พร้อมใช้ — ครอบ formula, conditional formatting, chart, pivot table ทำให้ "สร้าง budget tracker" หรือ "sales report มี chart" เป็นเรื่องง่าย',
      how_to_use='บอก layout เช่น "สร้าง monthly budget tracker" หรือ "ทำ sales report ที่มี chart" Claude generate .xlsx file พร้อมใช้',
      when='ต้องการ spreadsheet ที่ซับซ้อน มี formula, conditional formatting, หรือ chart — ไม่ใช่แค่ table ธรรมดา',
      careers='Everyone',
    ),
    dict(
      name='docx', tier='S+', type_emoji='🏗️', type_name='Builder',
      cmd='/docx',
      what='สร้าง Word document ด้วย styles, tables, headers ที่ format ถูกต้อง — บอก structure แล้วได้ .docx ที่แก้ต่อได้ใน Word ทันที เหมาะสำหรับ document ที่ต้องส่งหรือต้องการ rich formatting',
      how_to_use='บอก document structure เช่น "สร้าง project proposal template" หรือ "report ที่มี table of contents" ได้ .docx ที่ format ถูกต้อง',
      when='ต้องการ document ที่ rich formatting, tables, หรือต้องส่งในรูป .docx',
      careers='Everyone',
    ),
    dict(
      name='web-artifacts-builder', tier='S+', type_emoji='🏗️', type_name='Builder',
      cmd='/web-artifacts-builder',
      what='สร้าง HTML/CSS/JS ที่เปิดใน browser ได้เลยโดยไม่ต้อง deploy — data visualization, interactive tool, UI prototype ได้หมด บอก idea แล้วได้ demo ทันที ไม่ต้อง setup อะไรเลย',
      how_to_use='บอก UI component หรือ web app เช่น "สร้าง data visualization dashboard" หรือ "calculator ที่ใช้ browser ได้ทันที"',
      when='ต้องการ demo UI, interactive prototype, หรือ one-page tool ที่ใช้ได้ใน browser โดยไม่ต้อง deploy',
      careers='Developer, Designer, PM, Researcher',
    ),
    dict(
      name='claude-api', tier='S+', type_emoji='🔧', type_name='Utility',
      cmd='/claude-api',
      what='ช่วย build, debug, optimize app ที่ใช้ Anthropic SDK — มาพร้อม prompt caching, tool use, batch processing ครบ auto-trigger เมื่อ code import anthropic หรือเมื่อถามเรื่อง Claude API',
      how_to_use='บอก feature เช่น "สร้าง chatbot ด้วย Claude API พร้อม caching" หรือ "migrate จาก claude-2 ไป claude-sonnet-4-6" จะได้ code พร้อม best practices',
      when='Build app ที่ใช้ Anthropic SDK, migrate model versions, optimize caching, หรือ implement tool use/batch',
      careers='AI Engineer, Developer',
    ),
    dict(
      name='pptx', tier='S', type_emoji='🏗️', type_name='Builder',
      cmd='/pptx',
      what='บอก topic และจำนวน slides แล้วได้ PowerPoint deck พร้อม layout, theme, chart — ได้ .pptx ที่ edit ต่อได้ใน PowerPoint หรือ Google Slides ทันที ทำ deck ทั้ง deck ในไม่กี่นาที',
      how_to_use='บอก topic และจำนวน slides เช่น "สร้าง 10-slide deck เรื่อง AI trends" หรือ "สร้าง pitch deck สำหรับ startup"',
      when='ต้องการ presentation ที่ editable ใน PowerPoint/Google Slides หรือ generate deck จาก content อย่างรวดเร็ว',
      careers='Everyone',
    ),
    dict(
      name='pdf', tier='S', type_emoji='🏗️', type_name='Builder',
      cmd='/pdf',
      what='สร้างหรือแปรรูป PDF ด้วย Python — create, merge, split, extract text/table, password protect ได้ทุกอย่าง บอกว่าต้องการทำอะไรกับ PDF แล้วได้ solution ทันที',
      how_to_use='บอกว่าต้องการทำอะไรกับ PDF เช่น "สร้าง invoice PDF" หรือ "extract tables จาก PDF นี้"',
      when='ต้องการ PDF ที่ format สวย, แยก/รวม PDF, หรือ extract ข้อมูลจาก PDF',
      careers='Developer, Data, Operations',
    ),
    dict(
      name='mcp-builder', tier='S', type_emoji='🏗️', type_name='Builder',
      cmd='/mcp-builder',
      what='สร้าง MCP server ให้ Claude connect กับ external system ได้ — database, API, custom tool ได้ทุกอย่าง ได้ server code พร้อม config สำหรับ settings.json ง่ายกว่าเขียนเองมาก',
      how_to_use='บอก tool ที่ต้องการ add เช่น "สร้าง MCP server ที่ query database" จะได้ server code พร้อม config สำหรับ settings.json',
      when='ต้องการ connect Claude กับ external systems, databases, APIs, หรือ add custom tools',
      careers='AI Engineer, Developer, DevOps',
    ),
    dict(
      name='skill-creator', tier='A', type_emoji='🏗️', type_name='Builder',
      cmd='/skill-creator',
      what='Official Anthropic version ของการสร้าง skill — guided process ตาม best practices ที่ Anthropic recommend ถ้าต้องการ research phase ด้วยใช้ /craft-skill แทน',
      how_to_use='บอก skill ที่ต้องการสร้าง Claude จะ guide ผ่าน structured creation process — alternative ของ /craft-skill จาก zen-skills',
      when='สร้าง skill ใหม่ด้วย official Anthropic structure — ถ้าต้องการ research + evaluation ใช้ /craft-skill แทน',
      careers='Everyone',
    ),
    dict(
      name='frontend-design', tier='A', type_emoji='🏗️', type_name='Builder',
      cmd='/frontend-design',
      what='รับ design requirement หรือ mockup แล้ว implement เป็น frontend code ที่ production-ready — component structure, styling, responsive, accessibility ครบ ไม่ต้อง translate spec เอง',
      how_to_use='บอก design requirement หรือวาง mockup Claude จะ implement เป็น code ที่ production-ready',
      when='Implement UI design หรือ improve visual presentation ของ web app',
      careers='Developer, Designer',
    ),
    dict(
      name='webapp-testing', tier='A', type_emoji='🔍', type_name='Reviewer',
      cmd='/webapp-testing',
      what='ทดสอบ web app ผ่าน browser automation — คลิก navigate กรอก form หา UI regression ได้ test report โดยไม่ต้องเขียน test script เอง เหมาะก่อน deploy หรือหลัง code change',
      how_to_use='บอก URL หรือ component ที่ต้องการ test Claude จะ automate browser และ report results',
      when='Verify web app ทำงานถูกต้องก่อน deploy หรือหลัง code change',
      careers='QA Engineer, Developer',
    ),
    dict(
      name='doc-coauthoring', tier='A', type_emoji='📝', type_name='Writer',
      cmd='/doc-coauthoring',
      what='เขียน technical doc ร่วมกัน — ให้ draft หรือ outline แล้ว Claude expand, polish, และ keep terminology consistent ตลอด เหมาะกับ README, runbook, หรือ wiki ที่ต้องการ quality สูง',
      how_to_use='ให้ draft หรือ outline แล้ว Claude ช่วย expand, polish, และ ensure consistent terminology',
      when='เขียน technical documentation ที่มีคุณภาพสูง หรือ collaborate ใน large doc',
      careers='Writer, PM, Developer, Operations',
    ),
    dict(
      name='canvas-design', tier='B', type_emoji='🏗️', type_name='Builder',
      cmd='/canvas-design',
      what='ออกแบบ graphics และ visual content ผ่าน Claude Canvas — layouts, illustrations, design systems บอก requirement แล้วได้ visual ทันที เหมาะสำหรับ explore design concept เร็วๆ',
      how_to_use='บอก design requirement เช่น "สร้าง logo concept สำหรับ startup" Claude จะ generate visual',
      when='Visual design draft หรือ explore design concepts',
      careers='Designer, Marketing, Startup',
    ),
    dict(
      name='brand-guidelines', tier='B', type_emoji='🏗️', type_name='Builder',
      cmd='/brand-guidelines',
      what='สร้าง brand guidelines ครบ — colors, typography, logo usage, tone of voice บอก brand attributes แล้วได้ document ที่ share ทีมหรือ designer ได้เลย',
      how_to_use='บอก brand attributes เช่น "สร้าง brand guide สำหรับ B2B SaaS fintech startup"',
      when='Launch product ใหม่, rebrand, หรือต้องการ consistent brand identity',
      careers='Designer, Marketing, Startup',
    ),
    dict(
      name='theme-factory', tier='B', type_emoji='🏗️', type_name='Builder',
      cmd='/theme-factory',
      what='สร้าง color palette และ design tokens สำหรับ UI — dark/light mode, component themes บอก mood หรือ brand direction แล้วได้ consistent color system พร้อมใช้',
      how_to_use='บอก mood หรือ brand direction เช่น "สร้าง dark theme สำหรับ developer tool"',
      when='ต้องการ consistent color system หรือ theme สำหรับ app',
      careers='Frontend Dev, Designer',
    ),
    dict(
      name='internal-comms', tier='B', type_emoji='📝', type_name='Writer',
      cmd='/internal-comms',
      what='ช่วยเขียน internal announcement, memo, all-hands update ให้ clear และ professional — บอก topic กับ audience แล้วได้ draft ที่ปรับ tone ตาม channel และ hierarchy',
      how_to_use='บอก topic และ audience เช่น "เขียน all-hands update เรื่อง Q3 roadmap change"',
      when='สื่อสาร change สำคัญในองค์กรหรือทีม',
      careers='Manager, Tech Lead, PM, Operations',
    ),
    dict(
      name='algorithmic-art', tier='C', type_emoji='🏗️', type_name='Builder',
      cmd='/algorithmic-art',
      what='สร้าง generative art ด้วย code — geometric patterns, fractals, particle systems บอก style แล้วได้ code ที่รันแล้วเห็น visual ทันที เหมาะสำหรับ creative coding หรือ visualization',
      how_to_use='บอก style หรือ pattern เช่น "สร้าง Mandelbrot set visualization แบบ colorful"',
      when='Creative code art, visualizations, หรือ generative design',
      careers='Game Dev, Designer, Content',
    ),
    dict(
      name='slack-gif-creator', tier='C', type_emoji='🏗️', type_name='Builder',
      cmd='/slack-gif-creator',
      what='สร้าง custom GIF สำหรับ Slack reactions หรือ team emojis — บอก concept แล้วได้ animated GIF ที่ upload ไปใช้ใน team ได้เลย',
      how_to_use='บอก concept เช่น "สร้าง celebration GIF สำหรับ team"',
      when='ต้องการ custom Slack emoji สำหรับ team culture',
      careers='Everyone',
    ),
  ],
}

# ─── Tier & Type Definition Pages ────────────────────────────────────────────
def build_definitions_page():
    items = []
    items.append(Spacer(1, 0.8*cm))
    items.append(Paragraph('ก่อนอ่าน: นิยาม Tier & Skill Type', STYLES['h1']))
    items.append(HRFlowable(width=CW, thickness=2, color=C['blue'], spaceAfter=14))

    # ── Tier Section
    items.append(Paragraph(me('🏅') + ' ระดับ Tier', STYLES['h2']))
    items.append(Paragraph(
        'ทุก skill มี tier rating ที่บอกว่า "คุ้มค่าแค่ไหนที่จะมีไว้" '
        '— ไม่ได้วัดความยากหรือความซับซ้อน แต่วัดว่า impact ต่อชีวิต developer ใน workflow จริง',
        STYLES['body']))
    items.append(Spacer(1, 6))

    tier_defs = [
        ('S+', 'ต้องมี — ดีมาก impact สูง เปลี่ยนวิธีทำงานจริง',
         'harvest-insights, scrutinize, karpathy-guidelines, handoff'),
        ('S',  'ดีมาก — แต่อาจเฉพาะทางหรือ cost สูง ไม่ใช่ทุกคนต้องใช้',
         'craft-skill, reviewing-code, auditing-security, debug-mantra'),
        ('A',  'ดี — มีประโยชน์ในบริบทที่เหมาะสม แนะนำสำหรับ use case ที่ตรง',
         'designing-agent-roles, post-mortem, tdd, prototype'),
        ('B',  'มีประโยชน์ — แต่ optional ใช้เมื่อต้องการ specific task',
         'session-summary, updating-plugins, zoom-out, to-prd'),
        ('C',  'Niche / fun — ไม่จำเป็น แต่ดีในบริบทพิเศษ',
         'caveman, algorithmic-art, cleaning-sessions'),
    ]
    tier_rows = []
    for tier, desc, examples in tier_defs:
        tc = TIER_COLORS[tier]
        bg = TIER_BG[tier]
        badge = Paragraph(f'<b>{tier}</b>', ParagraphStyle('tb2', fontName='TH',
            fontSize=13, leading=18, textColor=tc, alignment=TA_CENTER))
        desc_p = Paragraph(f'<b>{desc}</b>', ParagraphStyle('td', fontName='TH',
            fontSize=10, leading=15, textColor=C['text']))
        eg_p = Paragraph(f'ตัวอย่าง: {examples}', ParagraphStyle('te', fontName='TH',
            fontSize=8.5, leading=13, textColor=C['muted']))
        tier_rows.append([badge, Table([[desc_p],[eg_p]], colWidths=[CW - 2.2*cm - 30])])

    tt = Table(tier_rows, colWidths=[2.2*cm, CW - 2.2*cm])
    for i, (tier, _, _) in enumerate(tier_defs):
        tc = TIER_COLORS[tier]
        bg = TIER_BG[tier]
        tt.setStyle(TableStyle([
            ('BACKGROUND', (0,i),(0,i), bg),
            ('BOX', (0,i),(0,i), 1.5, tc),
        ]))
    tt.setStyle(TableStyle([
        ('TOPPADDING', (0,0),(-1,-1), 8), ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(0,-1), 8), ('LEFTPADDING', (1,0),(1,-1), 12),
        ('RIGHTPADDING', (-1,0),(-1,-1), 8),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0),(-1,-2), 0.5, C['border']),
        ('BOX', (0,0),(-1,-1), 1, C['border']),
        ('ROWBACKGROUNDS', (1,0),(1,-1), [C['card_bg'], C['white']]),
    ]))
    items.append(tt)
    items.append(Spacer(1, 18))

    # ── Type Section
    items.append(Paragraph(me('🏷️') + ' ประเภท Skill Type', STYLES['h2']))
    items.append(Paragraph(
        'แต่ละ skill มี "ประเภทการใช้งาน" — บอกว่า invoke แล้วจะได้อะไร ต้องทำยังไง',
        STYLES['body']))
    items.append(Spacer(1, 6))

    type_defs = [
        ('💉', 'Discipline Injector',
         'เปลี่ยน behavior ของ Claude ตลอด session — invoke แล้ว Claude ทำตาม rules จนจบ เหมือนตั้ง mode ให้ทำอย่างเป็นระเบียบ',
         'debug-mantra, karpathy-guidelines, tdd, caveman'),
        ('🏗️', 'Builder',
         'สร้าง output ใหม่จาก scratch — input: requirements > output: file / document / code / design',
         'craft-skill, xlsx, docx, pdf, pptx, web-artifacts-builder'),
        ('🔍', 'Reviewer',
         'วิเคราะห์ ตรวจสอบ และแนะนำ — input: code / plan / codebase > output: findings + next steps',
         'scrutinize, reviewing-code, auditing-security, improve-codebase-architecture'),
        ('🔥', 'Challenger',
         'ตั้งคำถาม stress-test และหา root cause — ไม่รับ assumption ง่ายๆ force ให้คิดลึกกว่าเดิม',
         'grill-me, grill-with-docs, diagnose'),
        ('📝', 'Writer',
         'เขียน docs สรุป และส่งต่อ — input: session / bug / conversation > output: structured document',
         'handoff, post-mortem, session-summary, management-talk'),
        ('🔧', 'Utility',
         'setup maintenance และเครื่องมือ — one-off operation ที่ไม่เปลี่ยน behavior ของ Claude',
         'wahahaha, harvest-insights, extracting-youtube-transcript, updating-plugins'),
    ]
    type_rows = []
    for emoji, name, desc, examples in type_defs:
        tc = TYPE_COLORS.get(emoji, C['muted'])
        badge_p = Paragraph(me(emoji), ParagraphStyle('emj', fontName='Emoji',
            fontSize=18, leading=22, alignment=TA_CENTER))
        name_p = Paragraph(f'<b>{name}</b>', ParagraphStyle('tn', fontName='TH',
            fontSize=10, leading=14, textColor=tc))
        desc_p = Paragraph(desc, ParagraphStyle('tde', fontName='TH',
            fontSize=9, leading=13, textColor=C['text']))
        eg_p = Paragraph(f'เช่น: {examples}', ParagraphStyle('teg', fontName='TH',
            fontSize=8, leading=12, textColor=C['muted']))
        right = Table([[name_p],[desc_p],[eg_p]], colWidths=[(CW/2) - 1.8*cm - 30])
        right.setStyle(TableStyle([
            ('TOPPADDING', (0,0),(-1,-1), 2), ('BOTTOMPADDING', (0,0),(-1,-1), 1),
            ('LEFTPADDING', (0,0),(-1,-1), 0), ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ]))
        type_rows.append([badge_p, right])

    # 2-column layout
    half = len(type_rows) // 2 + len(type_rows) % 2
    col1_rows = type_rows[:half]
    col2_rows = type_rows[half:]
    # pad
    while len(col2_rows) < len(col1_rows):
        col2_rows.append(['', ''])

    def make_mini_table(rows):
        t = Table(rows, colWidths=[1.8*cm, (CW/2) - 1.8*cm - 16])
        t.setStyle(TableStyle([
            ('TOPPADDING', (0,0),(-1,-1), 7), ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('LEFTPADDING', (0,0),(0,-1), 6), ('LEFTPADDING', (1,0),(1,-1), 8),
            ('RIGHTPADDING', (-1,0),(-1,-1), 6),
            ('VALIGN', (0,0),(-1,-1), 'TOP'),
            ('LINEBELOW', (0,0),(-1,-2), 0.3, C['border']),
            ('BOX', (0,0),(-1,-1), 0.8, C['border']),
            ('ROWBACKGROUNDS', (0,0),(-1,-1), [C['card_bg'], C['white']]),
        ]))
        return t

    grid = Table([[make_mini_table(col1_rows), Spacer(0.3*cm, 1), make_mini_table(col2_rows)]],
                 colWidths=[CW/2 - 4, 0.3*cm, CW/2 - 4])
    grid.setStyle(TableStyle([
        ('TOPPADDING', (0,0),(-1,-1), 0), ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING', (0,0),(-1,-1), 0), ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('VALIGN', (0,0),(-1,-1), 'TOP'),
    ]))
    items.append(grid)
    return items

# ─── Installation Page ───────────────────────────────────────────────────────
def build_install_page():
    items = []
    items.append(Spacer(1, 0.8*cm))
    items.append(Paragraph('การติดตั้ง zen-skills', STYLES['h1']))
    items.append(HRFlowable(width=CW, thickness=2, color=C['blue'], spaceAfter=12))

    # Note
    note = Table([[Paragraph(
        me('⚠️  ') + '<b>หมายเหตุ:</b> zen-skills เป็น private repo — ต้องทำ <b>gh auth login</b> ก่อนนะ',
        ParagraphStyle('nt', fontName='TH', fontSize=10.5, leading=16, textColor=colors.HexColor('#7B341E'))
    )]], colWidths=[CW])
    note.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#FFF8E1')),
        ('BOX', (0,0),(-1,-1), 1.5, colors.HexColor('#F9A825')),
        ('TOPPADDING', (0,0),(-1,-1), 10), ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING', (0,0),(-1,-1), 14), ('RIGHTPADDING', (0,0),(-1,-1), 14),
    ]))
    items.append(note)
    items.append(Spacer(1, 10))

    steps = [
        ('1', 'เพิ่ม marketplace', '/plugin marketplace add zennnne/zen-skills'),
        ('2', 'ติดตั้ง plugin',   '/plugin install zen-skills@zen-skills'),
        ('3', 'รัน wahahaha',     '/wahahaha'),
    ]
    for num, title, cmd in steps:
        items.append(Paragraph(f'<b>ขั้นที่ {num}</b> — {title}', STYLES['step']))
        items.append(Paragraph(cmd, STYLES['mono']))
        items.append(Spacer(1, 4))

    items.append(Spacer(1, 10))
    items.append(Paragraph(me('🧙 /wahahaha — ทำอะไรให้บ้าง?'), STYLES['h2']))
    items.append(Paragraph(
        'หลัง install แล้ว /wahahaha เป็น onboarding wizard ที่จะถามทีละขั้น '
        'ให้เลือกว่าจะติดตั้งอะไรบ้าง:',
        STYLES['body']))
    items.append(Spacer(1, 6))

    wahaha_steps = [
        ('📝', 'Session Log System',
         'auto-summarize ทุก session ด้วย Haiku → เก็บเป็น daily log ที่ ~/.claude/session_log/'),
        ('🎓', 'andrej-karpathy-skills',
         'behavioral guidelines ลด LLM coding mistakes — think before coding, surgical changes, simplicity first'),
        ('🔷', 'mattpocock-skills',
         'TypeScript, TDD, PRD, prototype, architecture, grilling skills จาก Matt Pocock'),
        ('📄', 'document-skills',
         'PDF, Excel, Word, PowerPoint, canvas design, MCP builder (official Anthropic skills)'),
        ('🐾', '9arm-skills',
         'debug mantra, post-mortem, scrutinize, management talk จาก 9arm (thananon)'),
    ]
    rows = []
    for emoji, name, desc in wahaha_steps:
        rows.append([
            Paragraph(me(emoji), ParagraphStyle('we', fontName='Emoji', fontSize=16, leading=20, alignment=TA_CENTER)),
            Table([[
                Paragraph(f'<b>{name}</b>', ParagraphStyle('wn', fontName='TH', fontSize=10.5, leading=15, textColor=C['blue'])),
                Paragraph(desc, ParagraphStyle('wd', fontName='TH', fontSize=9, leading=13, textColor=C['text'])),
            ]], colWidths=[CW - 2.2*cm - 30])
        ])
    wt = Table(rows, colWidths=[2.2*cm, CW - 2.2*cm])
    wt.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), C['light']),
        ('BOX', (0,0),(-1,-1), 1, C['blue']),
        ('LINEBELOW', (0,0),(-1,-2), 0.3, C['border']),
        ('TOPPADDING', (0,0),(-1,-1), 8), ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(0,-1), 8), ('LEFTPADDING', (1,0),(1,-1), 12),
        ('RIGHTPADDING', (-1,0),(-1,-1), 12),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
    ]))
    items.append(wt)
    items.append(Spacer(1, 12))
    items.append(Paragraph(
        me('✅') + '  เพียงแค่นี้ก็พร้อมใช้งานแล้วค่ะ! Skills จะ auto-trigger เมื่อพูดถึง keyword '
        'ที่เกี่ยวข้อง หรือ invoke ด้วย /skill-name โดยตรง',
        ParagraphStyle('ok', fontName='TH', fontSize=11, leading=18, textColor=C['green'], spaceBefore=8)
    ))
    return items

# ─── Owner Section ──────────────────────────────────────────────────────────
OWNERS = [
    ('zen',  '🏠', "zennnne's Skills",       '16 skills • core workflow & automation', 'zen'),
    ('9arm', '⚙️', "9arm's Skills",          '4 skills • engineering discipline',       '9arm'),
    ('matt', '🔷', "mattpocock's Skills",    '11 skills • dev workflow & TypeScript',   'matt'),
    ('karp', '🎓', "Andrej Karpathy's Skills",'1 skill • coding discipline',            'karp'),
    ('doc',  '📄', 'document-skills',        '17 skills • official Anthropic tools',    'doc'),
]

def build_owner_section(key, emoji, title, subtitle, color_key):
    items = []
    items.append(PageBreak())
    items.append(section_banner(emoji, title, subtitle, color_key))
    items.append(Spacer(1, 12))
    seen = set()
    for skill in SKILLS.get(key, []):
        uid = skill['name']
        if uid in seen:
            continue
        seen.add(uid)
        card = skill_card(skill, color_key)
        items.append(KeepTogether([card, Spacer(1, 10)]))
    return items

# ─── Build PDF ───────────────────────────────────────────────────────────────
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 0.75*cm, bottomMargin=MARGIN + 0.4*cm,
        title='zen-skills Catalog', author='zennnne',
    )
    story = []
    # Cover (blank spacer — drawn on canvas)
    # frame height = PAGE_H - topMargin - bottomMargin
    frame_h = PAGE_H - (MARGIN + 0.75*cm) - (MARGIN + 0.4*cm)
    story.append(Spacer(1, frame_h - 1*cm))
    story.append(PageBreak())
    # Install
    story.extend(build_install_page())
    story.append(PageBreak())
    # Definitions
    story.extend(build_definitions_page())
    # Owner sections
    for key, emoji, title, sub, ckey in OWNERS:
        story.extend(build_owner_section(key, emoji, title, sub, ckey))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF saved: {output_path}')

if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    build_pdf(r'C:\Users\User\OneDrive\Desktop\zen-skills-catalog.pdf')
