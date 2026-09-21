"""Post-process a pandoc-generated docx:
1. Translate the "Table of Contents" heading to Vietnamese.
2. Fix tables where pandoc emitted an empty <w:tblGrid/> (and tblW w=0) --
   LibreOffice then only renders the first column. Inject an explicit,
   evenly-split grid sized to the number of cells in the table's first row.
"""
import re
import sys
import zipfile
import shutil

path = sys.argv[1]
tmp = path + '.tmp'

TOTAL_WIDTH = 9350  # twentieths of a point, ~6.5in usable body width


def fix_tables(xml):
    def repl(m):
        tbl = m.group(0)
        if '<w:tblGrid />' not in tbl and '<w:tblGrid/>' not in tbl:
            return tbl  # already has explicit columns
        first_row = re.search(r'<w:tr\b.*?</w:tr>', tbl, re.S)
        if not first_row:
            return tbl
        ncols = len(re.findall(r'<w:tc\b', first_row.group(0)))
        if ncols == 0:
            return tbl
        col_w = TOTAL_WIDTH // ncols
        grid = '<w:tblGrid>' + ''.join('<w:gridCol w:w="%d" />' % col_w for _ in range(ncols)) + '</w:tblGrid>'
        tbl = re.sub(r'<w:tblGrid\s*/>', grid, tbl)
        tbl = re.sub(r'<w:tblW w:type="pct" w:w="0\.0" />', '<w:tblW w:type="pct" w:w="5000.0" />', tbl)
        return tbl

    return re.sub(r'<w:tbl>.*?</w:tbl>', repl, xml, flags=re.S)


with zipfile.ZipFile(path, 'r') as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    fixed_count = 0
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'word/document.xml':
            text = data.decode('utf-8')
            text = text.replace('Table of Contents', 'MỤC LỤC')
            before = text.count('<w:tblGrid />') + text.count('<w:tblGrid/>')
            text = fix_tables(text)
            after = text.count('<w:tblGrid />') + text.count('<w:tblGrid/>')
            fixed_count = before - after
            data = text.encode('utf-8')
        zout.writestr(item, data)

shutil.move(tmp, path)
print('fixed %d table(s) with missing grid; ToC title translated' % fixed_count)
