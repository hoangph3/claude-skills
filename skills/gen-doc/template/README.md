# Bộ công cụ gen tài liệu bàn giao (.docx chuẩn văn bản hành chính)

Chuyển 1 file markdown thành `.docx` theo chuẩn: Times New Roman, size 13/1.5
line spacing, letterhead (quốc hiệu tiêu ngữ + tên đơn vị tùy chọn), mục lục
tự động tính số trang, bảng biểu có hàng tiêu đề in đậm/tô nền và không bị vỡ
qua trang, khối "Nơi nhận / Ký tên" ở cuối.

Dùng khi cần soạn: đề án, kế hoạch, hồ sơ bàn giao dự án, thể lệ chương trình...

## Cài đặt (một lần)

```bash
sudo apt-get install -y pandoc libreoffice poppler-utils
pip install python-docx
```

## Cách dùng

1. Viết nội dung theo cấu trúc mô tả trong [`PROMPT.md`](./PROMPT.md).
2. Build:

```bash
./build.sh noi-dung.md ra-file.docx \
  --org "TECH JUNIOR" \
  --doc-no "01/2026/ĐA-TJ" \
  --city "Hà Nội" \
  --date "10 tháng 9 năm 2026" \
  --sign-title "ĐẠI DIỆN TECH JUNIOR" \
  --recipients "Đối tác A;Đối tác B;Lưu VT"
```

Bỏ `--org` (và `--doc-no`, `--sign-title`) nếu muốn bản **trung lập**, không
nêu tên đơn vị cụ thể — dùng cho tài liệu nội dung thuần túy, không gắn với
một pháp nhân nào (ví dụ khi cần chia sẻ nội dung chương trình mà không tiện
nhắc tên đối tác).

3. Kiểm tra bằng cách xuất PDF xem trước:

```bash
soffice --headless --convert-to pdf --outdir /tmp ra-file.docx
```

## Các file trong bộ này

| File | Vai trò |
|---|---|
| `make_reference.py` | Sinh `reference.docx` (style template: font, size, margin) — chỉ cần chạy lại nếu muốn đổi style gốc |
| `reference.docx` | Style template đã build sẵn, `build.sh` dùng trực tiếp |
| `fix_docx.py` | Sửa 2 lỗi của pandoc: dịch tiêu đề "Table of Contents" → "MỤC LỤC", và vá bảng bị mất `tblGrid` (lỗi khiến bảng chỉ hiện đúng 1 cột) |
| `finalize_docx.py` | Chèn letterhead + khối ký tên, in đậm/tô nền hàng tiêu đề bảng, khóa không cho dòng bảng vỡ qua trang |
| `update_toc.py` | Cập nhật trường Mục lục (nội dung + số trang) qua LibreOffice UNO, để mở file lên là thấy mục lục đầy đủ ngay, không cần tự bấm cập nhật |
| `build.sh` | Chạy toàn bộ pipeline trên theo đúng thứ tự |
| `PROMPT.md` | Hướng dẫn/checklist viết nội dung markdown đúng chuẩn để build |

## Vì sao cần `update_toc.py` (bước hay bị bỏ sót)

pandoc chỉ tạo *khung* trường Mục lục trong `.docx`, không tự tính nội dung —
Word/LibreOffice chỉ điền nội dung khi người dùng mở file và bấm "Cập nhật
trường" (F9). `update_toc.py` làm việc này tự động bằng cách mở file qua
LibreOffice ở chế độ ẩn, gọi lệnh cập nhật, rồi lưu lại — để người nhận mở file
là thấy mục lục đầy đủ ngay, không cần biết thao tác F9.

## Biết trước: những lỗi đã gặp và cách pipeline xử lý

- **Bảng chỉ hiện đúng 1 cột**: do pandoc thỉnh thoảng xuất bảng với
  `<w:tblGrid />` rỗng — `fix_docx.py` tự dò và vá lại độ rộng cột.
- **Dòng bảng trống ảo ở chỗ ngắt trang**: xảy ra khi bật "lặp lại hàng tiêu
  đề mỗi trang" mà một dòng dữ liệu lại bị ngắt giữa trang — `finalize_docx.py`
  khóa `cantSplit` cho mọi dòng để tránh việc này.
- **Font không phải Times New Roman dù đã set trong style**: do pandoc emit
  một số đoạn văn với style "FirstParagraph"/"Compact" không có trong
  `reference.docx` gốc, khiến nó rơi về theme font (sans-serif) — style những
  paragraph style đó tường minh trong `make_reference.py` đã sửa việc này.
