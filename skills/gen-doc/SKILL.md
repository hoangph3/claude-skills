---
name: gen-doc
description: Soạn tài liệu chuẩn văn bản hành chính (.docx) — đề án, kế hoạch, hồ sơ giải pháp, hồ sơ bàn giao, hồ sơ đáp ứng yêu cầu kỹ thuật... — có mục lục tự động, bảng biểu chuẩn, kèm sơ đồ minh họa. Dùng khi người dùng yêu cầu "làm tài liệu/hồ sơ/đề án", "trình bày dạng doc/docx", "soạn văn bản formal", hoặc khi output trước đó là artifact/markdown nhưng người dùng muốn đổi sang .docx chuẩn.
---

# Soạn tài liệu .docx chuẩn văn bản hành chính, có sơ đồ minh họa

Skill này đóng gói quy trình đã dùng để tạo hồ sơ giải pháp LMS (ví dụ đầu
tiên dùng skill này) — áp dụng được cho **bất kỳ loại tài liệu nào** cần
định dạng .docx chuẩn, không riêng gì hồ sơ LMS.

Skill này nằm trong repo `claude-skills` cá nhân (nhiều skill khác nhau, mỗi
skill 1 thư mục con dưới `skills/`), có thể được cài vào một project bằng
cách copy hoặc symlink thư mục `gen-doc/` này vào `.claude/skills/gen-doc/`
của project đó. Vì vị trí cài đặt thay đổi theo từng project, **không dùng
đường dẫn tuyệt đối cố định** — trước khi build, xác định thư mục chứa chính
`SKILL.md` này (thường là `.claude/skills/gen-doc/` trong project hiện tại;
nếu không thấy, tìm bằng
`find / -maxdepth 8 -path "*/skills/gen-doc/template/build.sh" 2>/dev/null`)
rồi dùng đường dẫn đó thay cho `<SKILL_DIR>` trong các lệnh dưới đây.

## Quy trình 4 bước

### Bước 1 — Xác định khung nội dung

Hỏi/đọc ngữ cảnh để biết: tài liệu để làm gì (đề án nộp thầu, kế hoạch nội
bộ, hồ sơ bàn giao...), cho ai đọc, có cần nêu tên đơn vị cụ thể hay bản
trung lập. Nếu thiếu thông tin quan trọng (tên đơn vị, người ký, nơi nhận)
mà không suy luận được từ ngữ cảnh, hỏi người dùng 1 câu gọn — nếu người
dùng nói "không cần" thì build bản trung lập (bỏ `--org`), không hỏi lại.

### Bước 2 — Viết nội dung theo `template/PROMPT.md`

Đọc kỹ `<SKILL_DIR>/template/PROMPT.md` trước khi viết — đây là
checklist bắt buộc: văn phong hành chính khô/khách quan, cấu trúc
`## PHẦN <La Mã>. TÊN PHẦN` / `### <số>.<số> Tên mục`, bảng biểu dùng pipe
table chuẩn, không markdown code-block/blockquote, không icon/emoji, không
literal ảnh nếu không quyết định trước bố cục.

Đặt nội dung + ảnh sơ đồ trong 1 thư mục làm việc riêng (không dùng lại thư
mục `output/` cho file trung gian), ví dụ:
`scratchpad/<ten-tai-lieu>/noi-dung.md` và `scratchpad/<ten-tai-lieu>/img/`.

### Bước 3 — Vẽ sơ đồ minh họa (nếu nội dung có phần đáng vẽ)

Đọc `<SKILL_DIR>/DIAGRAM_GUIDE.md` để lấy bảng màu, khung hàm
matplotlib và quy tắc tránh lỗi chồng chữ. Luôn `Read` lại ảnh 1 lần sau khi
sinh trước khi nhúng vào markdown bằng `![caption](img/ten-file.png){width=6.3in}`.

Không phải tài liệu nào cũng cần sơ đồ — chỉ vẽ khi có nội dung thực sự dạng
kiến trúc/quy trình/tổ chức/tiến độ đáng trực quan hóa; văn bản thuần quy
định/điều khoản thì không cần.

### Bước 4 — Build và kiểm tra

```bash
cd <thư mục chứa noi-dung.md>
bash <SKILL_DIR>/template/build.sh \
  noi-dung.md "Ten-tai-lieu.docx" \
  --city "Hà Nội" \
  --date "<ngày hiện tại, dạng 'DD tháng M năm YYYY'>" \
  [--org "TÊN ĐƠN VỊ"] [--doc-no "SỐ HIỆU"] [--sign-title "CHỨC DANH NGƯỜI KÝ"] \
  --recipients "Bên A;Lưu hồ sơ"
```

Yêu cầu công cụ hệ thống (cài 1 lần cho môi trường, kiểm tra trước khi build):

```bash
which pandoc soffice pdftoppm || sudo apt-get install -y pandoc libreoffice-writer poppler-utils
python3 -c "import docx" 2>/dev/null || pip install --break-system-packages python-docx
python3 -c "import matplotlib" 2>/dev/null || pip install --break-system-packages matplotlib
```

Sau khi build, xuất PDF xem trước và kiểm tra ít nhất: trang bìa/letterhead,
mục lục (số trang đúng), 1 bảng có tràn trang, trang có sơ đồ (ảnh không vỡ
layout, không tràn lề), trang ký tên cuối:

```bash
soffice --headless --convert-to pdf --outdir . "Ten-tai-lieu.docx"
pdftoppm -png -r 100 "Ten-tai-lieu.pdf" page
```

Dùng `Read` để xem 3-4 trang đại diện (bìa, 1 trang có bảng, 1 trang có sơ đồ,
trang cuối) — sửa nội dung/sơ đồ nếu phát hiện lỗi, rồi build lại. Không lặp
vòng kiểm tra quá 2 lần trừ khi phát hiện lỗi rõ ràng.

Cuối cùng copy file `.docx` hoàn thiện vào `output/` trong thư mục dự án để
người dùng dễ lấy (tạo thư mục nếu chưa có), báo đường dẫn cho người dùng.

## Ghi chú

- Bộ công cụ trong `template/` là toolchain có sẵn (không tự sửa `reference.docx`,
  `finalize_docx.py`... trừ khi người dùng yêu cầu đổi style gốc — xem
  `template/README.md` để hiểu vai trò từng file nếu cần chỉnh).
- Nếu người dùng yêu cầu định dạng khác .docx (PDF trực tiếp, slide, trang
  web) thì đây không phải skill phù hợp — quay lại quy trình thông thường
  (Artifact cho web, hoặc hỏi công cụ phù hợp).
