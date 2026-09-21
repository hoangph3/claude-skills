#!/usr/bin/env bash
# Convert a markdown file into a formatted .docx following the Vietnamese
# "văn bản hành chính" style (Times New Roman, thể thức chuẩn, mục lục, bảng
# biểu rõ ràng) -- see PROMPT.md for the markdown conventions to write to.
#
# Usage:
#   ./build.sh INPUT.md OUTPUT.docx [--org "TECH JUNIOR"] [--doc-no "01/2026/ĐA-TJ"] \
#       [--city "Hà Nội"] [--date "10 tháng 9 năm 2026"] [--sign-title "ĐẠI DIỆN TECH JUNIOR"] \
#       [--recipients "Bên A;Bên B;Lưu VT"]
#
# Requires: pandoc, libreoffice (soffice), python3 with python-docx installed.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$1"; shift
OUTPUT="$1"; shift

if [ ! -f "$DIR/reference.docx" ]; then
  echo "reference.docx missing, generating it..."
  python3 "$DIR/make_reference.py"
fi

mkdir -p "$(dirname "$OUTPUT")"
pandoc "$INPUT" --reference-doc="$DIR/reference.docx" -o "$OUTPUT" --standalone --toc --toc-depth=2
python3 "$DIR/fix_docx.py" "$OUTPUT"

# --date is required by finalize_docx.py; default to today in Vietnamese form
# if the caller didn't pass one.
if [[ "$*" != *"--date"* ]]; then
  DEFAULT_DATE="$(LC_ALL=vi_VN.UTF-8 date +'%d tháng %m năm %Y' 2>/dev/null || date +'%d/%m/%Y')"
  set -- "$@" --date "$DEFAULT_DATE"
fi
python3 "$DIR/finalize_docx.py" "$OUTPUT" "$@"

# Update the ToC field -- needs a headless LibreOffice listener. Start one if
# none is already up on port 2002.
PORT=2002
if ! (echo > /dev/tcp/localhost/$PORT) 2>/dev/null; then
  echo "Starting headless LibreOffice listener on port $PORT..."
  soffice --headless --invisible --nocrashreport --nodefault --norestore \
    --nologo --nofirststartwizard \
    --accept="socket,host=localhost,port=$PORT;urp;" >/tmp/soffice_build.log 2>&1 &
  disown
  for i in $(seq 1 15); do
    (echo > /dev/tcp/localhost/$PORT) 2>/dev/null && break
    sleep 1
  done
fi
python3 "$DIR/update_toc.py" "$OUTPUT" --port "$PORT"

echo "Done: $OUTPUT"
