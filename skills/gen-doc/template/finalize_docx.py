"""Bring a pandoc-generated docx closer to the official Vietnamese văn bản
hành chính format (thể thức theo Nghị định 30/2020/NĐ-CP, mô phỏng theo Kế
hoạch 315-KH/TWĐTN-KHCN): letterhead block (quốc hiệu tiêu ngữ, + tên đơn vị /
số hiệu văn bản nếu có), bold + shaded table header rows that don't split
across a page break, and a "Nơi nhận / Ký tên" block at the end.

Run AFTER fix_docx.py (grid-fix + ToC-heading-translate) and BEFORE
update_toc.py (the UNO-based TOC field update), so the TOC page numbers
reflect the final layout.

Usage:
    python3 finalize_docx.py FILE.docx [options]

Options (all optional -- omit --org for a generic, organization-neutral
letterhead/signature suitable for a pure "nội dung chương trình" document):
    --org "TECH JUNIOR"                 Tên đơn vị ban hành (khối trái letterhead)
    --doc-no "01/2026/ĐA-TJ"            Số hiệu văn bản (dưới tên đơn vị)
    --city "Hà Nội"                     Địa danh trong dòng ngày tháng
    --date "10 tháng 9 năm 2026"        Ngày tháng ban hành
    --sign-title "ĐẠI DIỆN TECH JUNIOR" Chức danh người ký (khối chữ ký cuối)
    --recipients "Bên A;Bên B;Lưu VT"   Danh sách "Nơi nhận", phân cách bằng ;
"""
import argparse
import re
import shutil
import sys
import zipfile

CONTENT_WIDTH = 9071  # twips, matches page margins in reference.docx


def bold_run(run_xml):
    if '<w:rPr/>' in run_xml:
        return run_xml.replace('<w:rPr/>', '<w:rPr><w:b/></w:rPr>', 1)
    if '<w:rPr></w:rPr>' in run_xml:
        return run_xml.replace('<w:rPr></w:rPr>', '<w:rPr><w:b/></w:rPr>', 1)
    if '<w:rPr>' in run_xml:
        return run_xml.replace('<w:rPr>', '<w:rPr><w:b/>', 1)
    return run_xml.replace('<w:r>', '<w:r><w:rPr><w:b/></w:rPr>', 1)


def style_header_row(row_xml):
    row_xml = re.sub(r'^<w:tr\b([^>]*)>', r'<w:tr\1><w:trPr><w:tblHeader /></w:trPr>', row_xml, count=1)

    def cell_repl(m):
        cell = m.group(0)
        if '<w:tcPr>' in cell:
            cell = cell.replace('<w:tcPr>', '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="D9D9D9" />', 1)
        elif '<w:tcPr/>' in cell:
            cell = cell.replace('<w:tcPr/>', '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="D9D9D9" /></w:tcPr>', 1)
        cell = re.sub(r'<w:r>(?:(?!</w:r>).)*?</w:r>', lambda rm: bold_run(rm.group(0)), cell, flags=re.S)
        if '<w:jc' not in cell:
            cell = re.sub(r'(<w:pPr>)', r'\1<w:jc w:val="center" />', cell, count=1)
        return cell

    row_xml = re.sub(r'<w:tc>(?:(?!</w:tc>).)*?</w:tc>', cell_repl, row_xml, flags=re.S)
    return row_xml


def add_cant_split(row_xml):
    # Prevent a row from splitting across a page break -- combined with the
    # repeated header row, a split row otherwise leaves a spurious-looking
    # blank row where the continuation used to render.
    if '<w:trPr>' in row_xml:
        return row_xml.replace('<w:trPr>', '<w:trPr><w:cantSplit />', 1)
    if '<w:trPr/>' in row_xml:
        return row_xml.replace('<w:trPr/>', '<w:trPr><w:cantSplit /></w:trPr>', 1)
    return re.sub(r'^<w:tr\b([^>]*)>', r'<w:tr\1><w:trPr><w:cantSplit /></w:trPr>', row_xml, count=1)


def style_table_headers(xml):
    def tbl_repl(m):
        tbl = m.group(0)
        rows = list(re.finditer(r'<w:tr\b(?:(?!</w:tr>).)*?</w:tr>', tbl, re.S))
        if not rows:
            return tbl
        out = tbl[:rows[0].start()]
        for i, row_m in enumerate(rows):
            row_xml = row_m.group(0)
            if i == 0:
                row_xml = style_header_row(row_xml)
            row_xml = add_cant_split(row_xml)
            out += row_xml
            next_start = rows[i + 1].start() if i + 1 < len(rows) else len(tbl)
            out += tbl[row_m.end():next_start]
        return out

    return re.sub(r'<w:tbl>.*?</w:tbl>', tbl_repl, xml, flags=re.S)


def para(text, bold=False, italic=False, center=True, size=None):
    ppr = '<w:pPr>'
    if center:
        ppr += '<w:jc w:val="center" />'
    ppr += '</w:pPr>'
    rpr = ''
    if bold or italic or size:
        rpr = '<w:rPr>'
        if bold:
            rpr += '<w:b />'
        if italic:
            rpr += '<w:i />'
        if size:
            rpr += '<w:sz w:val="%d" /><w:szCs w:val="%d" />' % (size, size)
        rpr += '</w:rPr>'
    return '<w:p>%s<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (ppr, rpr, text)


def para_left(text, bold=False, italic=False):
    rpr = ''
    if bold or italic:
        rpr = '<w:rPr>'
        if bold:
            rpr += '<w:b />'
        if italic:
            rpr += '<w:i />'
        rpr += '</w:rPr>'
    return '<w:p><w:pPr><w:jc w:val="left" /></w:pPr><w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (rpr, text)


def borderless_table(left_col_xml, right_col_xml, left_w, right_w):
    return (
        '<w:tbl>'
        '<w:tblPr>'
        '<w:tblW w:type="dxa" w:w="%d" />' % CONTENT_WIDTH +
        '<w:tblBorders>'
        '<w:top w:val="nil" /><w:left w:val="nil" /><w:bottom w:val="nil" /><w:right w:val="nil" />'
        '<w:insideH w:val="nil" /><w:insideV w:val="nil" />'
        '</w:tblBorders>'
        '<w:tblLook w:val="0000" />'
        '</w:tblPr>'
        '<w:tblGrid><w:gridCol w:w="%d" /><w:gridCol w:w="%d" /></w:tblGrid>' % (left_w, right_w) +
        '<w:tr>'
        '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d" /></w:tcPr>%s</w:tc>' % (left_w, left_col_xml) +
        '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d" /></w:tcPr>%s</w:tc>' % (right_w, right_col_xml) +
        '</w:tr>'
        '</w:tbl>'
    )


def build_letterhead(args):
    date_line = 'Ngày %s' % args.date if not args.city else '%s, ngày %s' % (args.city, args.date)
    if args.org:
        left = para_left(args.org, bold=True)
        if args.doc_no:
            left += para_left('Số: %s' % args.doc_no)
        right = (
            para('CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', bold=True) +
            para('Độc lập – Tự do – Hạnh phúc', bold=True) +
            para('–––––––––––––––', size=18) +
            para(date_line, italic=True)
        )
        return borderless_table(left, right, 3200, 5871) + '<w:p />'
    # No đơn vị name: centered quốc hiệu tiêu ngữ only, no left column.
    return (
        para('CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', bold=True) +
        para('Độc lập – Tự do – Hạnh phúc', bold=True) +
        para('–––––––––––––––', size=18) +
        para(date_line, italic=True) +
        '<w:p />'
    )


def build_signature(args):
    recipients = [r.strip() for r in args.recipients.split(';') if r.strip()] if args.recipients else \
        ['Ban tổ chức', 'Lưu hồ sơ']
    left = para_left('Nơi nhận:', bold=True)
    for i, r in enumerate(recipients):
        r = r.rstrip('.;')
        punct = '.' if i == len(recipients) - 1 else ';'
        left += para_left('- %s%s' % (r, punct))
    sign_title = args.sign_title or 'BAN TỔ CHỨC'
    right = para(sign_title, bold=True) + para('(Ký, ghi rõ họ tên%s)' % (' và đóng dấu' if args.org else ''), italic=True)
    right += para('') + para('') + para('')
    return '<w:p />' + borderless_table(left, right, 3200, 5871)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('path')
    p.add_argument('--org', default='', help='Tên đơn vị ban hành, vd "TECH JUNIOR". Bỏ trống = letterhead trung lập.')
    p.add_argument('--doc-no', default='', help='Số hiệu văn bản, vd "01/2026/ĐA-TJ"')
    p.add_argument('--city', default='Hà Nội', help='Địa danh trong dòng ngày tháng')
    p.add_argument('--date', default='', required=True, help='Ngày tháng, vd "10 tháng 9 năm 2026"')
    p.add_argument('--sign-title', default='', help='Chức danh người ký, vd "ĐẠI DIỆN TECH JUNIOR"')
    p.add_argument('--recipients', default='', help='Danh sách Nơi nhận, phân cách bằng ";"')
    args = p.parse_args()

    tmp = args.path + '.tmp2'
    letterhead_xml = build_letterhead(args)
    signature_xml = build_signature(args)

    with zipfile.ZipFile(args.path, 'r') as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                text = data.decode('utf-8')
                n_tables_before = len(re.findall(r'<w:tbl>', text))
                text = style_table_headers(text)
                text = text.replace('<w:body>', '<w:body>' + letterhead_xml, 1)
                text = re.sub(r'<w:sectPr\b', signature_xml + '<w:sectPr', text, count=1)
                data = text.encode('utf-8')
                print('styled header row on %d table(s); inserted letterhead + signature block' % n_tables_before)
            zout.writestr(item, data)

    shutil.move(tmp, args.path)


if __name__ == '__main__':
    main()
