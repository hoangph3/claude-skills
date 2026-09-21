# claude-skills

Kho lưu các Claude Code skill cá nhân — mỗi skill là một thư mục con dưới
`skills/`, có thể cài vào bất kỳ project nào cần dùng.

## Cài một skill vào project

Copy (hoặc symlink) thư mục skill vào `.claude/skills/` của project:

```bash
cp -r skills/<ten-skill> /path/to/project/.claude/skills/
# hoặc symlink để tự động nhận bản cập nhật từ repo này
ln -s "$(pwd)/skills/<ten-skill>" /path/to/project/.claude/skills/<ten-skill>
```

Sau khi cài, gõ `/<ten-skill>` trong Claude Code ở project đó để gọi skill.

## Danh sách skill

| Skill | Mô tả |
|---|---|
| [`gen-doc`](skills/gen-doc/SKILL.md) | Soạn tài liệu `.docx` chuẩn văn bản hành chính (đề án, kế hoạch, hồ sơ giải pháp/bàn giao...) — mục lục tự động, bảng biểu chuẩn, kèm sơ đồ minh họa vẽ bằng matplotlib. |

## Thêm skill mới

Tạo thư mục `skills/<ten-skill>/` với file `SKILL.md` (frontmatter `name` +
`description`, nội dung hướng dẫn quy trình), thêm mọi file phụ trợ (script,
template, tài liệu tham khảo) cùng thư mục, rồi cập nhật bảng ở trên.
