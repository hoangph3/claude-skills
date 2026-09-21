"""Force-update a docx's Table of Contents field (page numbers + entries) via
a headless LibreOffice UNO connection, then save the file in place.

pandoc emits a TOC field with no cached result -- Word/LO only compute it when
the user opens the file and updates fields (F9 / "Update Table"). This script
does that update programmatically so the docx already shows a populated ToC.

Requires a headless LibreOffice instance listening on the given port; start
one with:
    soffice --headless --invisible --nocrashreport --nodefault --norestore \\
        --nologo --nofirststartwizard \\
        --accept="socket,host=localhost,port=2002;urp;" &

Usage:
    python3 update_toc.py FILE.docx [--port 2002]
"""
import argparse
import os
import sys

sys.path.insert(0, '/usr/lib/libreoffice/program')
import uno  # noqa: E402
from com.sun.star.beans import PropertyValue  # noqa: E402


def make_prop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--port', type=int, default=2002)
    args = ap.parse_args()

    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        'com.sun.star.bridge.UnoUrlResolver', local_context)
    ctx = resolver.resolve(
        'uno:socket,host=localhost,port=%d;urp;StarOffice.ComponentContext' % args.port)
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)

    url = 'file://' + os.path.abspath(args.path)
    doc = desktop.loadComponentFromURL(url, '_blank', 0, (make_prop('Hidden', True),))
    indexes = doc.getDocumentIndexes()
    for i in range(indexes.getCount()):
        indexes.getByIndex(i).update()
    doc.store()
    doc.close(False)
    print('ToC updated: %s' % args.path)


if __name__ == '__main__':
    main()
