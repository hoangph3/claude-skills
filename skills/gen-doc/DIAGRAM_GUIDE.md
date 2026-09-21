# Hướng dẫn vẽ sơ đồ minh họa cho tài liệu hành chính

Dùng khi tài liệu (đề án, hồ sơ giải pháp, kế hoạch...) cần hình vẽ trực quan
kèm theo bảng biểu/văn xuôi. Mục tiêu: sơ đồ **khô, formal, đơn sắc**, đúng
tinh thần văn bản hành chính — không phải trực quan kiểu marketing/landing
page (không gradient sặc sỡ, không icon 3D, không hiệu ứng bóng đổ).

## Công cụ

Dùng Python + matplotlib (`Agg` backend, không cần GUI), xuất PNG DPI cao
(200–220), nhúng vào Markdown bằng `![caption](img/ten-file.png){width=6.3in}`
rồi build qua pipeline trong `template/` (pandoc nhúng ảnh vào .docx tự động,
không cần thao tác thủ công gì thêm).

Kiểm tra `python3 -c "import matplotlib"` trước; nếu thiếu:
`pip install --break-system-packages matplotlib`.

## Bảng màu chuẩn (đơn sắc, phân biệt bằng độ đậm nhạt của xám-xanh)

```python
INK = "#1a1a1a"       # màu chữ
LINE = "#4d4d4d"      # màu viền / mũi tên
FILL_1 = "#eef1f4"    # khối cấp 1 (nhạt nhất — vd: lớp người dùng, vai trò cao nhất)
FILL_2 = "#dfe6ea"    # khối cấp 2
FILL_3 = "#c9d4da"    # khối cấp 3 (đậm nhất — vd: lớp hạ tầng, cấp thấp nhất)
FILL_ACCENT = "#e8ecef"  # dải ngang gộp nhiều ý (băng thông tin)
```

Không dùng màu có sắc độ nổi bật (đỏ/cam/xanh lá) trừ khi sơ đồ thật sự cần
phân loại cảnh báo (vd: mức độ rủi ro) — khi đó chỉ dùng thêm 1 màu bổ trợ,
tối đa 2 sắc trong toàn bộ tài liệu.

## Loại sơ đồ hay dùng và khi nào chọn loại nào

| Loại sơ đồ | Dùng khi | Cách vẽ |
|---|---|---|
| Sơ đồ khối phân lớp (layered boxes + mũi tên dọc) | Trình bày kiến trúc hệ thống, luồng xử lý theo tầng | Mỗi lớp 1 hàng ngang các box cùng `fill`, nhãn lớp đặt phía trên hàng (không đặt bên trái để tránh chồng chữ với box đầu hàng) |
| Sơ đồ cây phân cấp (1 box gốc → nhiều box con, mũi tên tỏa ra) | Trình bày cơ cấu tổ chức, phân quyền, phân cấp quản lý | 1 box trên cùng, dùng `FancyArrowPatch` tỏa xuống các box con canh đều khoảng cách |
| Gantt đơn giản (thanh ngang theo trục thời gian) | Trình bày tiến độ/kế hoạch triển khai theo giai đoạn | Mỗi giai đoạn 1 thanh `FancyBboxPatch` nằm ngang, trục X là đơn vị thời gian (tuần/tháng), nhãn giai đoạn viết bên phải thanh |
| Sơ đồ quy trình (flow ngang/dọc có rẽ nhánh) | Trình bày quy trình nghiệp vụ nhiều bước, có điểm quyết định | Box hình chữ nhật bo góc cho bước xử lý, mũi tên nối tuần tự; nếu có điểm rẽ nhánh dùng nhãn text trên mũi tên ghi rõ điều kiện |

## Khung hàm dùng lại (rút gọn từ `make_diagrams.py` mẫu)

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

def box(ax, xy, w, h, text, fc, ec=LINE, fontsize=10.5, weight="normal"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.1, edgecolor=ec, facecolor=fc))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
        fontsize=fontsize, color=INK, weight=weight, linespacing=1.35)

def arrow(ax, p1, p2, lw=1.1, color=LINE):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>",
        mutation_scale=12, linewidth=lw, color=color, shrinkA=2, shrinkB=2))
```

Luôn `ax.axis("off")`, đặt tiêu đề sơ đồ bằng `ax.text(...)` căn giữa phía
trên (không dùng `ax.set_title` mặc định để kiểm soát font/size đồng bộ với
phần còn lại), lưu bằng:

```python
plt.tight_layout()
plt.savefig("img/ten-file.png", dpi=220, bbox_inches="tight", facecolor="white")
```

## Quy tắc bắt buộc tránh lỗi hay gặp

- Nhãn lớp/nhóm đặt **phía trên** dải box, không đặt bên trái sát box đầu
  tiên — nếu text nhãn dài hơn bề rộng box đầu hàng, chữ sẽ đè lên nhau.
- Luôn xem lại ảnh bằng `Read` sau khi sinh (1 lần), sửa nếu chữ tràn ra
  ngoài khung hoặc chồng lên nhau, rồi mới nhúng vào tài liệu.
- Không vẽ quá 3 sơ đồ trong 1 tài liệu trừ khi nội dung thật sự cần — sơ đồ
  dùng để làm rõ cấu trúc/tiến độ, không phải trang trí.
- Chiều rộng nhúng vào docx: `{width=6.3in}` (vừa khít lề trang A4 theo
  `reference.docx` của template) — không để mặc định (ảnh gốc có thể tràn lề).
