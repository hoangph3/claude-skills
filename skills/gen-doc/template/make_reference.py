"""Build a pandoc --reference-doc template matching Vietnamese thesis/đề án
formatting conventions: Times New Roman, size 13 body / 14 headings, 1.5 line
spacing, justified body text, standard binding margins (trái 3cm để đóng gáy)."""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

BLACK = RGBColor(0, 0, 0)

d = docx.Document()

# ---- page setup: A4, standard thesis margins ----
section = d.sections[0]
section.page_height = Cm(29.7)
section.page_width = Cm(21.0)
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(2.0)
section.left_margin = Cm(3.0)
section.right_margin = Cm(2.0)


def set_font(style, name='Times New Roman', size=13, bold=False, italic=False, color=BLACK):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.italic = italic
    style.font.color.rgb = color
    rpr = style.element.get_or_add_rPr()
    rFonts = rpr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), name)


# ---- Normal (body text) ----
normal = d.styles['Normal']
set_font(normal, size=13)
pf = normal.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
pf.space_after = Pt(6)
pf.space_before = Pt(0)
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ---- Title ----
title = d.styles['Title']
set_font(title, size=16, bold=True)
title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(12)
title.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

# ---- Headings 1-4 ----
h1 = d.styles['Heading 1']
set_font(h1, size=14, bold=True)
h1.paragraph_format.space_before = Pt(18)
h1.paragraph_format.space_after = Pt(8)
h1.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
h1.paragraph_format.keep_with_next = True

h2 = d.styles['Heading 2']
set_font(h2, size=13, bold=True)
h2.paragraph_format.space_before = Pt(12)
h2.paragraph_format.space_after = Pt(6)
h2.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
h2.paragraph_format.keep_with_next = True

h3 = d.styles['Heading 3']
set_font(h3, size=13, bold=True, italic=True)
h3.paragraph_format.space_before = Pt(10)
h3.paragraph_format.space_after = Pt(4)
h3.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
h3.paragraph_format.keep_with_next = True

h4 = d.styles['Heading 4']
set_font(h4, size=13, bold=True)
h4.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

# ---- block quote (used for callouts / ghi chú) ----
try:
    bq = d.styles['Block Text']
except KeyError:
    bq = d.styles['Quote']
set_font(bq, size=13, italic=True)
bq.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
bq.paragraph_format.left_indent = Cm(1.0)

# ---- table text / table caption ----
try:
    tbl_normal = d.styles['Table Text']
except KeyError:
    tbl_normal = d.styles.add_style('Table Text', docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
set_font(tbl_normal, size=12)
tbl_normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
tbl_normal.paragraph_format.space_after = Pt(2)

# ---- ToC style ----
for i in range(1, 3):
    try:
        toc = d.styles['TOC %d' % i]
        set_font(toc, size=13)
    except KeyError:
        pass

# ---- pandoc emits paragraphs styled "FirstParagraph" / "Compact", which this
# base template doesn't define; Word/LO then falls back to docDefaults' THEME
# font (minorHAnsi, a sans serif) instead of Normal's Times New Roman. Define
# them explicitly, based on Normal, so every paragraph pandoc can emit resolves
# to the same font regardless of which style name it happens to use.
for extra_name in ('FirstParagraph', 'Compact'):
    try:
        st = d.styles[extra_name]
    except KeyError:
        st = d.styles.add_style(extra_name, docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = normal
    set_font(st, size=13)
    st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ---- inline/block code: pandoc emits inline `code` spans with character
# style "VerbatimChar" and fenced code blocks with paragraph style
# "SourceCode" -- neither exists in a bare python-docx template, so both fall
# back to the sans-serif theme font mid-sentence. Define them as monospace
# (Courier New) so code reads as code, distinct from Times New Roman body
# text, instead of silently breaking to a random font.
try:
    verbatim_char = d.styles['VerbatimChar']
except KeyError:
    verbatim_char = d.styles.add_style('VerbatimChar', docx.enum.style.WD_STYLE_TYPE.CHARACTER)
set_font(verbatim_char, name='Courier New', size=12)

try:
    source_code = d.styles['SourceCode']
except KeyError:
    source_code = d.styles.add_style('SourceCode', docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
source_code.base_style = normal
set_font(source_code, name='Courier New', size=11)
source_code.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
source_code.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
source_code.paragraph_format.left_indent = Cm(0.5)

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reference.docx')
d.save(OUT)

# ---- belt-and-suspenders: rewrite the theme's major/minor Latin fonts AND
# docDefaults' theme font refs to Times New Roman directly. Covers any
# pandoc-emitted style name (known or not) that falls through to the theme
# font instead of an explicit style, which is what caused body text to render
# in a sans-serif despite Normal correctly specifying Times New Roman.
import re
import shutil
import zipfile

tmp = OUT + '.tmp'
with zipfile.ZipFile(OUT, 'r') as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'word/theme/theme1.xml':
            text = data.decode('utf-8')
            text = re.sub(r'(<a:latin typeface=")[^"]*(")', r'\1Times New Roman\2', text)
            data = text.encode('utf-8')
        elif item.filename == 'word/styles.xml':
            text = data.decode('utf-8')
            text = text.replace(
                '<w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorEastAsia" '
                'w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi" />',
                '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
                'w:eastAsia="Times New Roman" w:cs="Times New Roman" />',
            )
            # pandoc emits <w:tblStyle w:val="Table"/> on every table, but this
            # template only defines "TableGrid" (id differs) -- the undefined
            # reference makes LibreOffice mis-render column widths (only the
            # first column shows). Clone TableGrid's definition as "Table".
            m = re.search(
                r'<w:style w:type="table" w:styleId="TableGrid">.*?</w:style>',
                text,
            )
            assert m, 'TableGrid style not found to clone'
            table_style = (
                m.group(0)
                .replace('w:styleId="TableGrid"', 'w:styleId="Table"', 1)
                .replace('w:val="Table Grid"', 'w:val="Table"', 1)
            )
            text = text.replace(m.group(0), m.group(0) + table_style, 1)
            data = text.encode('utf-8')
        zout.writestr(item, data)
shutil.move(tmp, OUT)
print('reference.docx written (theme + docDefaults patched)')
