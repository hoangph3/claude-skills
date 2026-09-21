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

**Quan trọng — tránh lỗi chữ tràn ra ngoài border (lỗi hay gặp nhất):**
không được đoán số ký tự/dòng bằng mắt hay hard-code `fontsize` cố định cho
mọi box. Luôn đo bbox chữ thật bằng renderer của matplotlib, bọc dòng rồi co
cỡ chữ tới khi vừa khung — dùng đúng khung hàm `fit_text()` dưới đây, không
tự viết lại logic wrap thủ công:

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import textwrap

def fit_text(ax, fig, text, max_w_data, max_h_data, fontsize, weight="normal", min_fontsize=6.5):
    """Bọc dòng + giảm cỡ chữ tới khi khối text vừa bên trong (max_w_data,
    max_h_data) tính theo tọa độ dữ liệu của ax, đo bằng bbox thực tế."""
    renderer = fig.canvas.get_renderer()
    fs = fontsize
    while fs >= min_fontsize:
        best_lines = None
        # quét độ rộng ký tự từ RỘNG xuống HẸP -> chọn cách bọc ÍT DÒNG NHẤT
        # vẫn vừa khung (quét ngược lại, từ hẹp lên, sẽ chọn nhầm cách bọc
        # kiểu "ransom note" 1-2 từ/dòng dù không cần thiết)
        for chars in range(60, 5, -1):
            wrapped = textwrap.fill(text, width=chars, break_long_words=False)
            probe = ax.text(0, 0, wrapped, fontsize=fs, weight=weight, ha="center", va="center")
            bbox_data = probe.get_window_extent(renderer=renderer).transformed(ax.transData.inverted())
            probe.remove()
            if bbox_data.width <= max_w_data and bbox_data.height <= max_h_data:
                best_lines = wrapped
                break
        if best_lines is not None:
            return best_lines, fs
        fs -= 0.5
    return textwrap.fill(text, width=14), min_fontsize


def box(ax, fig, xy, w, h, text, fc, ec=LINE, fontsize=10.5, weight="normal", pad=0.12):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.1, edgecolor=ec, facecolor=fc))
    wrapped, fs = fit_text(ax, fig, text, w - pad, h - pad, fontsize, weight)
    ax.text(x + w/2, y + h/2, wrapped, ha="center", va="center",
        fontsize=fs, color=INK, weight=weight, linespacing=1.3)

def arrow(ax, p1, p2, lw=1.1, color=LINE):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>",
        mutation_scale=12, linewidth=lw, color=color, shrinkA=2, shrinkB=2))
```

`fit_text` cần `fig.canvas.draw()` đã chạy ít nhất 1 lần trước khi gọi (để
`get_renderer()` có sẵn) — gọi ngay sau khi tạo `fig, ax = plt.subplots(...)`
và set `xlim`/`ylim`.

Luôn `ax.axis("off")`, đặt tiêu đề sơ đồ bằng `ax.text(...)` căn giữa phía
trên (không dùng `ax.set_title` mặc định để kiểm soát font/size đồng bộ với
phần còn lại), lưu bằng:

```python
plt.tight_layout()
plt.savefig("img/ten-file.png", dpi=220, bbox_inches="tight", facecolor="white")
```

## Quy tắc bắt buộc tránh lỗi hay gặp

- Luôn dùng `fit_text()`/`box()` ở trên cho mọi chữ đặt trong khung — không
  tự đoán `fontsize` hay tự viết `textwrap.fill(width=...)` một lần rồi hy
  vọng vừa; đây là nguyên nhân chính gây tràn chữ ra ngoài border.
- Nhãn lớp/nhóm (label đứng ngoài box, không nằm trong khung) đặt **phía
  trên** dải box bằng `va="bottom"` ngay sát cạnh trên, không đặt bên trái
  sát box đầu tiên — nếu text nhãn dài hơn bề rộng box đầu hàng, chữ sẽ đè
  lên nhau (lỗi hay gặp thứ nhì).
- Luôn xem lại ảnh bằng `Read` sau khi sinh (1 lần), kiểm tra không còn chữ
  chạm/tràn viền box hoặc chồng lên box khác, rồi mới nhúng vào tài liệu.
- Không vẽ quá 3 sơ đồ trong 1 tài liệu trừ khi nội dung thật sự cần — sơ đồ
  dùng để làm rõ cấu trúc/tiến độ, không phải trang trí.
- Chiều rộng nhúng vào docx: `{width=6.3in}` (vừa khít lề trang A4 theo
  `reference.docx` của template) — không để mặc định (ảnh gốc có thể tràn lề).
