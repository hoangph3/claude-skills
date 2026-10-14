#!/usr/bin/env python3
"""mdtool: markdown là NGUỒN DUY NHẤT của tài liệu; mọi định dạng khác chỉ do tool này sinh ra.

    md  ->  docx  ->  pdf      (pdf cần LibreOffice: soffice)
    md  ->  html               (xem trên trình duyệt)

Lệnh:
    python3 tools/mdtool.py build  my_module            # md -> docx + html
    python3 tools/mdtool.py build  my_module --pdf      # md -> docx + html + pdf
    python3 tools/mdtool.py verify my_module            # kiểm tra docx/html khớp md
    python3 tools/mdtool.py build  my_module/md/01_example.md   # một file

Thư mục module: <module>/md/**/*.md là nguồn; kết quả ghi vào <module>/out/{docx,html,pdf}/.
Chỉ sửa file .md. Không sửa tay file trong out/ (lần build sau sẽ ghi đè).
Chi tiết cú pháp: tools/README.md.
"""
import argparse, html, os, re, shutil, subprocess, sys

# ---------------------------------------------------------------- parser
INLINE = re.compile(r"\\(.)|`([^`]+)`|\*\*(.+?)\*\*|\*(.+?)\*|<br\s*/?>")


def inline(s):
    """-> list[(kind, text)] ; kind: t | b | i | c | br"""
    out, pos = [], 0
    for m in INLINE.finditer(s):
        if m.start() > pos:
            out.append(("t", s[pos:m.start()]))
        esc, code, bold, ital = m.group(1), m.group(2), m.group(3), m.group(4)
        if esc is not None:
            out.append(("t", esc))
        elif code is not None:
            out.append(("c", code))
        elif bold is not None:
            out += [("b", t) if k == "t" else (k, t) for k, t in inline(bold)]
        elif ital is not None:
            out += [("i", t) if k == "t" else (k, t) for k, t in inline(ital)]
        else:
            out.append(("br", ""))
        pos = m.end()
    if pos < len(s):
        out.append(("t", s[pos:]))
    return out


def plain(runs):
    return "".join("\n" if k == "br" else t for k, t in runs)


def parse(text):
    front, body = {}, text
    if text.startswith("---\n"):
        end = text.index("\n---", 4)
        for ln in text[4:end].split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                front[k.strip()] = v.strip()
        body = text[end + 4:].lstrip("\n")
    lines = body.split("\n")
    blocks, i = [], 0
    special = re.compile(r"^(#{1,3} |> |```|::: ?notebox|\\newpage|\|)")
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
        elif ln.strip() == "\\newpage":
            blocks.append(("pagebreak",)); i += 1
        elif ln.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            blocks.append(("code", "\n".join(lines[i + 1:j]))); i = j + 1
        elif re.match(r"^::: ?notebox", ln):
            m = re.search(r"height=([\d.]+)", ln)
            j = i + 1
            while lines[j].strip() != ":::":
                j += 1
            label = " ".join(x.strip() for x in lines[i + 1:j] if x.strip())
            blocks.append(("notebox", float(m.group(1)) if m else 2.5, label)); i = j + 1
        elif re.match(r"^#{1,3} ", ln):
            lv = len(ln.split(" ", 1)[0])
            blocks.append(("h", lv, inline(ln[lv + 1:]))); i += 1
        elif ln.startswith("> "):
            j, buf = i, []
            while j < len(lines) and lines[j].startswith("> "):
                buf.append(lines[j][2:]); j += 1
            blocks.append(("quote", inline(" ".join(buf)))); i = j
        elif ln.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            rows = [[c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", r.strip())[1:-1]] for r in lines[i:j]]
            seps = rows[1]
            widths = [max(len(s.strip()), 1) for s in seps]
            header = [inline(c) for c in rows[0]]
            body_rows = [[inline(c) for c in r] for r in rows[2:]]
            blocks.append(("table", header, body_rows, widths)); i = j
        elif re.match(r"^(- |\d+\. )", ln):
            ordered = bool(re.match(r"^\d+\. ", ln))
            pat = re.compile(r"^\d+\. " if ordered else r"^- ")
            items, j = [], i
            while j < len(lines) and pat.match(lines[j]):
                items.append(inline(pat.sub("", lines[j], count=1))); j += 1
            blocks.append(("ol" if ordered else "ul", items)); i = j
        else:
            j, buf = i, []
            while j < len(lines) and lines[j].strip() and not special.match(lines[j]) and not re.match(r"^(- |\d+\. )", lines[j]):
                buf.append(lines[j].strip()); j += 1
            blocks.append(("p", inline(" ".join(buf)))); i = j
    return front, blocks


# ---------------------------------------------------------------- expected text (dùng cho verify)
def expected(front, blocks, numbered=True):
    """Danh sách chuỗi mà mọi định dạng phải chứa, theo đúng thứ tự."""
    out = [front.get("title", ""), front.get("subtitle", ""), front.get("tagline", ""), front.get("meta", "")]
    for b in blocks:
        k = b[0]
        if k == "h" or k == "p" or k == "quote":
            out.append(plain(b[-1] if k != "h" else b[2]))
        elif k in ("ul", "ol"):
            for n, it in enumerate(b[1], 1):
                out.append((f"{n}. " if k == "ol" and numbered else "") + plain(it))
        elif k == "table":
            out += [plain(c) for c in b[1]]
            for r in b[2]:
                out += [plain(c) for c in r]
        elif k == "code":
            out.append(b[1])
        elif k == "notebox":
            out.append("✎ " + b[2])
    return [norm(x) for x in out if norm(x)]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- docx
def build_docx(front, blocks, path):
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    FONT = "Calibri"
    base = float(front.get("fontsize", 11))
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(1.8)
    PAGE_W = 17.4

    def set_font(style, size, bold=False, color=None):
        style.font.name = FONT; style.font.size = Pt(size); style.font.bold = bold
        if color:
            style.font.color.rgb = RGBColor(*color)
        rpr = style.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); rpr.append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), FONT)

    set_font(doc.styles["Normal"], base)
    doc.styles["Normal"].paragraph_format.space_after = Pt(4)
    set_font(doc.styles["Title"], 24, True, (0x1F, 0x3A, 0x5F))
    set_font(doc.styles["Heading 1"], 17, True, (0x1F, 0x3A, 0x5F))
    set_font(doc.styles["Heading 2"], 14, True, (0x2E, 0x74, 0xB5))
    set_font(doc.styles["Heading 3"], 12, True, (0x40, 0x40, 0x40))

    def shade(el, fill):
        pr = el.get_or_add_tcPr() if hasattr(el, "get_or_add_tcPr") else el.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
        pr.append(shd)

    def runs(par, rs, size=None, bold=False, color=None):
        for k, t in rs:
            if k == "br":
                par.add_run().add_break(); continue
            r = par.add_run(t)
            r.bold = bold or k == "b"
            r.italic = k == "i"
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = RGBColor(*color)
            if k == "c":
                r.font.name = "Consolas"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
                r.font.size = Pt((size or base) - 1)

    def spacer():
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # front matter
    if front.get("title"):
        doc.add_paragraph(front["title"], style="Title")
    if front.get("subtitle"):
        p = doc.add_paragraph(); runs(p, [("t", front["subtitle"])], size=base + 3, bold=True, color=(0x2E, 0x74, 0xB5))
    if front.get("tagline"):
        p = doc.add_paragraph(); r = p.add_run(front["tagline"]); r.italic = True
    if front.get("meta"):
        p = doc.add_paragraph(); runs(p, [("t", front["meta"])], size=9.5, color=(0x66, 0x66, 0x66))

    for b in blocks:
        k = b[0]
        if k == "h":
            h = doc.add_heading("", b[1]); runs(h, b[2])
        elif k == "p":
            runs(doc.add_paragraph(), b[1])
        elif k == "ul":
            for it in b[1]:
                runs(doc.add_paragraph(style="List Bullet"), it)
        elif k == "ol":
            for n, it in enumerate(b[1], 1):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.6)
                p.paragraph_format.space_after = Pt(2)
                runs(p, [("t", f"{n}. ")] + it)
        elif k == "code":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.3); p.paragraph_format.space_after = Pt(8)
            shade(p._p, "F2F2F2")
            ls = b[1].split("\n")
            for n, ln in enumerate(ls):
                r = p.add_run(ln if ln else " ")
                r.font.name = "Consolas"; r.font.size = Pt(9.5)
                r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
                if n < len(ls) - 1:
                    r.add_break()
        elif k == "quote":
            t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
            c = t.rows[0].cells[0]; shade(c._tc, "FFF4CE")
            runs(c.paragraphs[0], b[1]); spacer()
        elif k == "notebox":
            t = doc.add_table(rows=1, cols=1); t.style = "Table Grid"
            row = t.rows[0]
            h = OxmlElement("w:trHeight"); h.set(qn("w:val"), str(int(b[1] * 567))); h.set(qn("w:hRule"), "atLeast")
            row._tr.get_or_add_trPr().append(h)
            c = row.cells[0]; shade(c._tc, "FFFEF5")
            r = c.paragraphs[0].add_run("✎ " + b[2]); r.italic = True; r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0x88, 0x88, 0x88); spacer()
        elif k == "table":
            header, rows, widths = b[1], b[2], b[3]
            tot = sum(widths); cw = [PAGE_W * w / tot for w in widths]
            fs = max(base - 1.5, 9)
            t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, h in enumerate(header):
                c = t.rows[0].cells[i]; shade(c._tc, "1F3A5F")
                runs(c.paragraphs[0], h, size=fs, bold=True, color=(255, 255, 255))
            for r in rows:
                cells = t.add_row().cells
                for i, v in enumerate(r):
                    para = cells[i].paragraphs[0]; para.paragraph_format.space_after = Pt(2)
                    runs(para, v, size=fs)
            t.autofit = False
            tblpr = t._tbl.tblPr
            lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblpr.append(lay)
            for i, w in enumerate(cw):
                t.columns[i].width = Cm(w)
            for row in t.rows:
                trpr = row._tr.get_or_add_trPr(); trpr.append(OxmlElement("w:cantSplit"))
                for i, w in enumerate(cw):
                    row.cells[i].width = Cm(w)
            spacer()
        elif k == "pagebreak":
            doc.add_page_break()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)


# ---------------------------------------------------------------- html
CSS = """
:root{--bg:#fff;--fg:#1d2433;--mut:#667;--navy:#1f3a5f;--blue:#2e74b5;--code:#f2f2f2;--line:#c9ced6;--callout:#fff4ce;--note:#fffef5}
@media(prefers-color-scheme:dark){:root{--bg:#14181f;--fg:#e4e8ef;--mut:#9aa4b2;--navy:#9cc2f0;--blue:#7fb3ea;--code:#1f2530;--line:#38404d;--callout:#3a3320;--note:#1b1f27}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,"Segoe UI",Roboto,Calibri,sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 80px}
h1{color:var(--navy);font-size:1.7rem;margin:2rem 0 .6rem}h2{color:var(--blue);font-size:1.35rem;margin:1.8rem 0 .5rem}h3{font-size:1.1rem;margin:1.2rem 0 .4rem}
header.doc h1.title{font-size:2rem;margin:.2rem 0}header.doc .sub{color:var(--blue);font-weight:700;font-size:1.2rem}header.doc .meta{color:var(--mut);font-size:.85rem}
pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:12px;overflow-x:auto;font:14px/1.45 ui-monospace,Consolas,Menlo,monospace}
code{background:var(--code);border-radius:4px;padding:1px 5px;font:.92em ui-monospace,Consolas,Menlo,monospace}pre code{background:none;padding:0}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;margin:.6rem 0 1rem;font-size:.95rem}
th{background:var(--navy);color:#fff;text-align:left}@media(prefers-color-scheme:dark){th{color:#14181f}}
th,td{border:1px solid var(--line);padding:6px 9px;vertical-align:top}
.callout{background:var(--callout);border-radius:6px;padding:10px 14px;margin:.8rem 0}
.notebox{border:1.5px dashed var(--line);background:var(--note);border-radius:6px;padding:8px 12px;margin:.8rem 0;color:var(--mut);font-style:italic}
.pb{border:0;border-top:2px dotted var(--line);margin:2rem 0}
@media print{.pb{break-after:page;border:0}}
nav.index a{display:block;padding:8px 0;color:var(--blue);text-decoration:none;border-bottom:1px solid var(--line)}
@media(max-width:600px){body{font-size:15px}}
"""


def hrun(rs):
    o = []
    for k, t in rs:
        e = html.escape(t)
        o.append({"t": e, "b": f"<strong>{e}</strong>", "i": f"<em>{e}</em>", "c": f"<code>{e}</code>", "br": "<br>"}[k])
    return "".join(o)


def build_html(front, blocks, path, title_fallback=""):
    out = []
    t = front.get("title", title_fallback)
    out.append('<header class="doc">')
    if t: out.append(f'<h1 class="title">{html.escape(t)}</h1>')
    if front.get("subtitle"): out.append(f'<div class="sub">{html.escape(front["subtitle"])}</div>')
    if front.get("tagline"): out.append(f'<p><em>{html.escape(front["tagline"])}</em></p>')
    if front.get("meta"): out.append(f'<div class="meta">{html.escape(front["meta"])}</div>')
    out.append("</header>")
    for b in blocks:
        k = b[0]
        if k == "h": out.append(f"<h{b[1]}>{hrun(b[2])}</h{b[1]}>")
        elif k == "p": out.append(f"<p>{hrun(b[1])}</p>")
        elif k == "ul": out.append("<ul>" + "".join(f"<li>{hrun(i)}</li>" for i in b[1]) + "</ul>")
        elif k == "ol": out.append("<ol>" + "".join(f"<li>{hrun(i)}</li>" for i in b[1]) + "</ol>")
        elif k == "code": out.append(f"<pre><code>{html.escape(b[1])}</code></pre>")
        elif k == "quote": out.append(f'<div class="callout">{hrun(b[1])}</div>')
        elif k == "notebox": out.append(f'<div class="notebox" style="min-height:{b[1]}cm">✎ {html.escape(b[2])}</div>')
        elif k == "pagebreak": out.append('<hr class="pb">')
        elif k == "table":
            tot = sum(b[3])
            cols = "".join(f'<col style="width:{100 * w / tot:.1f}%">' for w in b[3])
            head = "".join(f"<th>{hrun(c)}</th>" for c in b[1])
            rows = "".join("<tr>" + "".join(f"<td>{hrun(c)}</td>" for c in r) + "</tr>" for r in b[2])
            out.append(f'<div class="tw"><table><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')
    page = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(t or title_fallback)}</title><style>{CSS}</style></head><body><main>' + "\n".join(out) + "</main></body></html>")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf8").write(page)


def build_index(module_dir, items):
    name = os.path.basename(os.path.abspath(module_dir))
    links = "".join(f'<a href="{html.escape(r)}">{html.escape(r[:-5])}</a>' for r in items)
    page = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(name)}</title><style>{CSS}</style></head><body><main><h1>{html.escape(name)}</h1><nav class=\"index\">{links}</nav></main></body></html>")
    open(os.path.join(module_dir, "out", "html", "index.html"), "w", encoding="utf8").write(page)


# ---------------------------------------------------------------- pdf (docx -> pdf)
def soffice_bin():
    for n in ("soffice", "libreoffice"):
        p = shutil.which(n)
        if p:
            return p
    return None


def docx_to_pdf(docx_path, pdf_dir):
    sb = soffice_bin()
    if not sb:
        sys.exit("Không có LibreOffice. Cài bằng:  sudo apt install libreoffice-writer   rồi chạy lại với --pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    subprocess.run([sb, "--headless", "--convert-to", "pdf", "--outdir", pdf_dir, docx_path], check=True, capture_output=True)


# ---------------------------------------------------------------- điều phối
def collect(target):
    """target: thư mục module (có md/) hoặc một file .md -> list[(module_dir, md_path)]"""
    if os.path.isfile(target):
        md_dir = os.path.dirname(os.path.abspath(target))
        mod = md_dir
        while mod != "/" and os.path.basename(mod) != "md":
            mod = os.path.dirname(mod)
        return [(os.path.dirname(mod) if mod != "/" else md_dir, os.path.abspath(target))]
    md_root = os.path.join(target, "md")
    files = []
    for r, _, fs in os.walk(md_root):
        files += [os.path.join(r, f) for f in fs if f.endswith(".md")]
    return [(os.path.abspath(target), os.path.abspath(f)) for f in sorted(files)]


def rel_out(module, md_path, sub, ext):
    rel = os.path.relpath(md_path, os.path.join(module, "md"))
    return os.path.join(module, "out", sub, os.path.splitext(rel)[0] + ext)


def cmd_build(args):
    items = collect(args.target)
    if not items:
        sys.exit("Không tìm thấy file .md")
    htmls = {}
    for module, md in items:
        front, blocks = parse(open(md, encoding="utf8").read())
        d = rel_out(module, md, "docx", ".docx")
        build_docx(front, blocks, d)
        h = rel_out(module, md, "html", ".html")
        build_html(front, blocks, h, title_fallback=os.path.basename(md))
        htmls.setdefault(module, []).append(os.path.relpath(h, os.path.join(module, "out", "html")))
        if args.pdf:
            docx_to_pdf(d, os.path.dirname(rel_out(module, md, "pdf", ".pdf")))
        print("ok", os.path.relpath(md, module))
    for module, rels in htmls.items():
        build_index(module, rels)


def docx_texts(path):
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    d = Document(path)
    out = []
    for el in d.element.body.iterchildren():
        if el.tag.endswith("}p"):
            out.append(Paragraph(el, d).text)
        elif el.tag.endswith("}tbl"):
            for row in Table(el, d).rows:
                for c in row.cells:
                    out.append(c.text)
    return [norm(x) for x in out if norm(x)]


def html_text(path):
    from html.parser import HTMLParser
    class P(HTMLParser):
        def __init__(s): super().__init__(); s.t = []; s.skip = 0
        def handle_starttag(s, tag, a):
            if tag in ("style", "script"): s.skip += 1
            if tag == "br": s.t.append(" ")
        def handle_endtag(s, tag):
            if tag in ("style", "script"): s.skip -= 1
        def handle_data(s, d):
            if not s.skip: s.t.append(d)
    p = P(); p.feed(open(path, encoding="utf8").read())
    return norm("".join(p.t))


def cmd_verify(args):
    bad = 0
    items = collect(args.target)
    for module, md in items:
        front, blocks = parse(open(md, encoding="utf8").read())
        exp = expected(front, blocks)
        problems = []
        d = rel_out(module, md, "docx", ".docx")
        if not os.path.exists(d):
            problems.append("thiếu docx (chạy build)")
        else:
            got = docx_texts(d)
            # so khớp theo thứ tự: mỗi chuỗi expected phải là chuỗi con của chuỗi docx tương ứng
            # (code block trong docx là 1 đoạn; bảng nhiều ô; số lượng và thứ tự phải giống hệt)
            if len(got) != len(exp):
                problems.append(f"docx: số đoạn khác nhau (md {len(exp)} / docx {len(got)})")
            else:
                for n, (a, b) in enumerate(zip(exp, got)):
                    if a != b:
                        problems.append(f"docx: đoạn {n} khác: md={a[:60]!r} docx={b[:60]!r}"); break
        h = rel_out(module, md, "html", ".html")
        if not os.path.exists(h):
            problems.append("thiếu html (chạy build)")
        else:
            ht = html_text(h)
            miss = [e for e in expected(front, blocks, numbered=False) if e not in ht]
            if miss:
                problems.append(f"html: thiếu {len(miss)} đoạn, ví dụ {miss[0][:60]!r}")
        print(("LỖI " if problems else "khớp ") + os.path.relpath(md, module))
        for pr in problems:
            print("    -", pr)
        bad += bool(problems)
    print("Tổng:", len(items), "file,", bad, "file lệch")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("target"); b.add_argument("--pdf", action="store_true", help="docx -> pdf (cần LibreOffice)")
    v = sub.add_parser("verify"); v.add_argument("target")
    a = ap.parse_args()
    {"build": cmd_build, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    main()
