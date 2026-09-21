# Prompt soạn tài liệu bàn giao dự án (chuẩn văn bản hành chính)

Dùng nội dung dưới đây làm system/prompt khi nhờ AI (hoặc làm checklist khi tự
viết) soạn một tài liệu bàn giao dự án — đề án, kế hoạch, hồ sơ bàn giao —
theo đúng chuẩn để build ra `.docx` bằng `build.sh` trong thư mục này.

---

## Yêu cầu văn phong

- Văn bản hành chính chuẩn: khô, khách quan, không dùng ngôn từ marketing/AI
  ("tuyệt vời", "đột phá", icon, emoji...).
- Câu ngắn, rõ ràng, mỗi đoạn một ý. Ưu tiên liệt kê/bảng biểu hơn văn xuôi dài
  khi trình bày số liệu, quy trình, cơ cấu.
- Không dùng markdown code-block (```), không dùng blockquote (`>`), không
  chèn ảnh — pipeline này chỉ style văn bản/bảng/mục lục.
- Tham khảo văn phong các văn bản hành chính thật (kế hoạch, thể lệ, quyết
  định của cơ quan nhà nước/đoàn thể) nếu có, để đúng quy ước ngành.

## Cấu trúc file markdown

```
---
title: "TÊN TÀI LIỆU IN HOA"
---

# TÊN TÀI LIỆU IN HOA (trùng với title)

Ngày soạn: DD/MM/YYYY

Phiên bản: vX.Y

Mục đích tài liệu: 1-2 câu nêu tài liệu dùng để làm gì, cho ai.

---

## PHẦN I. TÊN PHẦN

### 1.1. Tên mục con

Nội dung...

---

## PHẦN II. THỂ LỆ / QUY ĐỊNH (nếu có)

**Điều 1. Tên điều**

1. Khoản 1...
2. Khoản 2...

**Điều 2. Tên điều**

a) Điểm a...
b) Điểm b...

---

## PHẦN III. ...
```

Quy tắc đánh số:
- `## PHẦN <số La Mã>. TÊN PHẦN` — cấp 1 (xuất hiện trong mục lục).
- `### <số>.<số>. Tên mục` — cấp 2 (xuất hiện trong mục lục, do `--toc-depth=2`).
- `**Điều N. Tên điều**` — dùng bold thay vì heading cho các điều khoản trong
  phần Thể lệ/Quy định, để không làm loãng mục lục (mục lục chỉ nên liệt kê
  cấp Phần + mục con, không liệt kê từng Điều).
- Dùng `---` (ngang) để ngăn cách giữa các PHẦN lớn — tạo khoảng trắng rõ ràng
  khi render.

## Bảng biểu

Dùng cú pháp bảng Markdown chuẩn (pipe table):

```
| Cột 1 | Cột 2 | Cột 3 |
|---|---|---|
| Dữ liệu | Dữ liệu | Dữ liệu |
```

Pipeline tự động: in đậm + tô nền xám hàng tiêu đề, căn giữa hàng tiêu đề, khóa
không cho một dòng bị ngắt giữa 2 trang, và lặp lại hàng tiêu đề nếu bảng tràn
trang. Không cần tự làm những việc này trong nội dung markdown.

## Những gì KHÔNG cần viết tay (pipeline tự thêm)

- Letterhead (quốc hiệu tiêu ngữ / tên đơn vị / số hiệu / ngày tháng) — truyền
  qua tham số dòng lệnh, không viết trong markdown.
- Mục lục (`MỤC LỤC`) — pipeline tự chèn và tự tính số trang.
- Khối "Nơi nhận / Ký tên" ở cuối — truyền qua tham số dòng lệnh.
- Số trang, kiểu chữ, giãn dòng — do `reference.docx` quyết định.

## Checklist trước khi build

1. Không còn icon/emoji trong nội dung.
2. Không còn văn phong quảng cáo ("tốt nhất", "hàng đầu", câu cảm thán).
3. Số liệu trong bảng khớp với số liệu nêu trong văn xuôi liên quan (đối
   chiếu chéo — đây là lỗi hay gặp nhất khi sửa nội dung nhiều lần).
4. Nếu tài liệu có thể dùng cho nhiều đối tượng nhận khác nhau (ví dụ: bản có
   nêu tên đối tác cụ thể và bản không nêu tên để dùng nội bộ/công khai), tách
   thành 2 file markdown riêng thay vì cố gắng dùng chung 1 file với biến thể
   — dễ kiểm tra, dễ review.
5. Chạy `build.sh`, mở PDF xuất ra kiểm tra: trang bìa/mục lục, ít nhất 1 bảng
   có tràn trang (kiểm tra hàng tiêu đề lặp lại đúng, không có dòng trống ảo),
   trang chữ ký cuối.

## Ví dụ tham khảo

Xem `../codechamp-2026-ho-so-ban-giao.docx` (bản có tên đơn vị cụ thể) và
`../codechamp-2026-noi-dung-chuong-trinh.docx` (bản trung lập, không nêu tên
đơn vị) — cả hai build từ cùng bộ công cụ trong thư mục này, chỉ khác tham số
truyền cho `finalize_docx.py`.
