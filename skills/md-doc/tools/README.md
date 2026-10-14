# mdtool – markdown là nguồn duy nhất

Nội dung chỉ được viết ở **một nơi: file `.md`**. Mọi định dạng khác do tool sinh ra, nên luôn giống hệt nhau.

```
md  ──►  docx  ──►  pdf        (pdf cần LibreOffice)
md  ──►  html                  (xem trên trình duyệt)
```

## Cấu trúc thư mục một module

```
my_module/
├── md/                      ← NGUỒN. Chỉ sửa ở đây
│   ├── 01_example.md, 02_other.md …               (tài liệu chính)
│   └── handouts/H01_example.md …                  (thư mục con cũng được)
└── out/                     ← KẾT QUẢ. Do tool sinh, build lần sau sẽ ghi đè
    ├── docx/  (cùng cấu trúc thư mục như md/)
    ├── html/  (có index.html để mở nhanh)
    └── pdf/   (chỉ có khi build với --pdf)
```

## Cài đặt (một lần)

```bash
pip install python-docx                 # md -> docx, html, verify
sudo apt install libreoffice-writer     # chỉ cần nếu muốn docx -> pdf
```

## Lệnh

```bash
python3 tools/mdtool.py build  my_module          # md -> docx + html
python3 tools/mdtool.py build  my_module --pdf    # md -> docx + html + pdf
python3 tools/mdtool.py build  my_module/md/01_example.md   # chỉ một file
python3 tools/mdtool.py verify my_module          # kiểm tra docx và html khớp md
```

`verify` so từng đoạn, từng ô bảng, từng dòng code giữa md và docx (đúng thứ tự, đúng số lượng),
và kiểm tra html chứa đủ nội dung. Có lệch thì báo file và đoạn lệch, thoát với mã lỗi 1.

Xem html: mở `my_module/out/html/index.html` bằng trình duyệt.

## Quy trình sửa nội dung

1. Sửa file `.md` trong `md/`.
2. `build` lại.
3. `verify` để chắc mọi định dạng khớp.

**Không sửa tay** file trong `out/`: build lần sau sẽ ghi đè, và `verify` sẽ báo lệch.
Ghi chú khi dạy (gõ hoặc vẽ lên docx) thì **Save As ra một thư mục riêng** (ví dụ `ghi_chu/`),
đừng lưu đè lên file trong `out/`.

## Cú pháp markdown được hỗ trợ

Tool chỉ hiểu tập con này (đủ cho giáo án). Dùng ngoài tập này thì sẽ không được chuyển đúng.

| Việc | Viết như thế này |
|---|---|
| Tiêu đề file | Đầu file có khối `---` … `---` với các dòng `title:`, `subtitle:`, `tagline:`, `meta:`, `fontsize:` |
| Mục | `#`, `##`, `###` (3 cấp) |
| Chữ đậm, nghiêng, code | `**đậm**`, `*nghiêng*`, `` `code` `` |
| Danh sách | `- mục` hoặc `1. mục` (một cấp) |
| Bảng | Bảng pipe. Dòng phân cách `\|-----\|----\|`: độ dài gạch ngang quyết định tỷ lệ độ rộng cột. Xuống dòng trong ô: `<br>`. Ký tự `\|` trong ô: `\\\|` |
| Khối code | Rào bằng ba dấu ``` |
| Hộp lưu ý | Dòng bắt đầu bằng `> ` |
| Ô trống để ghi chú | `::: notebox height=2.6` rồi một dòng nhãn rồi `:::` (height tính bằng cm) |
| Ngắt trang | Một dòng chỉ có `\newpage` |
| Ký tự đặc biệt | Muốn hiện dấu `*`, `` ` ``, `\` thì thêm `\` phía trước |

Ví dụ ô ghi chú:

```
::: notebox height=2.6
Ghi chú của thầy:
:::
```
