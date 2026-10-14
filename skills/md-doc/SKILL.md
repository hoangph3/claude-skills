---
name: md-doc
description: Soạn tài liệu MỘT LẦN bằng markdown rồi build ra .docx, .html (xem trên trình duyệt) và .pdf, đảm bảo nội dung giống hệt nhau ở mọi định dạng. Dùng khi người dùng muốn viết tài liệu dưới 1 định dạng duy nhất (md) rồi dùng tool convert md -> docx -> pdf, hoặc cần nhiều bản (docx, pdf, web) mà nội dung phải đồng bộ — giáo án, tài liệu học viên, hướng dẫn, quy trình, báo cáo nhiều file.
---

# Viết markdown một lần, build ra docx / html / pdf

Nguyên tắc: **markdown là nguồn duy nhất**. Mọi định dạng khác (docx, html, pdf)
đều do tool sinh ra từ md, không ai viết hay sửa tay. Nhờ vậy nội dung luôn
đồng bộ, và có lệnh `verify` để kiểm tra điều đó.

```
md  ->  docx  ->  pdf        (pdf cần LibreOffice)
md  ->  html                 (xem trên trình duyệt)
```

Khác với skill `gen-doc` (văn bản hành chính: quốc hiệu, khối ký tên, Times New
Roman, không có code block), skill này dành cho tài liệu thông thường có thể có
code, bảng, hộp lưu ý, ô trống để ghi chú. Cần văn bản hành chính chuẩn thì dùng
`gen-doc`.

Skill này nằm trong repo `claude-skills`, được cài vào project bằng cách copy.
Vị trí cài đặt thay đổi theo từng project nên **không dùng đường dẫn tuyệt đối
cố định**: xác định thư mục chứa chính `SKILL.md` này (thường là
`.claude/skills/md-doc/`) rồi dùng thay cho `<SKILL_DIR>` bên dưới.

## Quy trình

### Bước 1 — Dựng khung thư mục

Mỗi bộ tài liệu là một "module": thư mục có `md/` (nguồn) và `out/` (kết quả do tool sinh).

```
<module>/
├── md/                 ← nguồn, chỉ sửa ở đây (thư mục con tùy ý)
└── out/{docx,html,pdf}/   ← do tool sinh, build lần sau ghi đè
```

### Bước 2 — Viết nội dung bằng markdown

Đọc `<SKILL_DIR>/tools/README.md` để biết **tập con markdown được hỗ trợ**: front
matter, tiêu đề 3 cấp, đậm/nghiêng/code, danh sách một cấp, bảng pipe (có chỉnh
tỷ lệ cột và xuống dòng trong ô bằng `<br>`), khối code, hộp lưu ý (`> `), ô trống
ghi chú (`::: notebox`), ngắt trang (`\newpage`). Ngoài tập này thì không được
chuyển đúng (ví dụ danh sách lồng nhau chưa hỗ trợ), nên đừng dùng.

Luôn viết thẳng vào `.md`. Không viết một script sinh nội dung rồi ghi thẳng ra
docx: làm vậy là tạo ra nguồn thứ hai và mất tính nhất quán.

### Bước 3 — Build

```bash
pip install python-docx        # một lần
python3 <SKILL_DIR>/tools/mdtool.py build  <module>          # md -> docx + html
python3 <SKILL_DIR>/tools/mdtool.py build  <module> --pdf    # thêm docx -> pdf
```

Chỉ build một file: truyền đường dẫn file `.md`. Mở `<module>/out/html/index.html`
để xem trên trình duyệt.

PDF cần LibreOffice (`soffice`). Kiểm tra bằng `which soffice`; nếu chưa có thì
báo người dùng cài (`sudo apt install libreoffice-writer`), không tự bỏ qua bước pdf
mà không nói.

### Bước 4 — Kiểm tra nhất quán

```bash
python3 <SKILL_DIR>/tools/mdtool.py verify <module>
```

`verify` so từng đoạn, ô bảng, dòng code giữa md và docx (đúng thứ tự, đúng số
lượng) và kiểm tra html chứa đủ nội dung. Phải ra `0 file lệch`. Nếu lệch: không
sửa file trong `out/`, sửa md (hoặc báo lỗi tool) rồi build lại.

`verify` chỉ bảo đảm **chữ khớp nhau**, không thay cho việc nhìn bố cục. Khi có
`--pdf`, đổi pdf ra ảnh (`pdftoppm -png -r 70 file.pdf page`) và xem vài trang đại
diện: bảng dài, trang có code, ô ghi chú.

## Ghi chú

- Không sửa tay file trong `out/`. Nếu người dùng ghi chú lên docx lúc dạy/họp thì
  bảo họ **Save As** sang thư mục riêng, đừng lưu đè.
- Các tài liệu viết cho người khác đọc (giáo án, tài liệu học viên) nên để cùng một
  nguồn md; bản dành cho học viên chỉ khác ở file md riêng, không khác ở tool.
- Tránh emoji màu như ⭐ trong nội dung: LibreOffice trên Linux thường thiếu font emoji nên hiện thành ô vuông khi xuất pdf. Dùng ký tự thường (★ ☐ ✎) thì hiện đúng ở mọi định dạng.
- Muốn đổi giao diện docx (font, màu) thì sửa trong `tools/mdtool.py` (hàm
  `build_docx`) và `CSS` cho html, rồi build lại toàn bộ để các file vẫn cùng một kiểu.
