# Kho bài học Sai Đâu Sửa Đó

Học tiếng Anh từ lỗi người Việt hay mắc. Mỗi ngày sửa một lỗi nhỏ.

- **21 bài học** • **3 lộ trình** • **2 Reel** đính kèm trong bài
- Mỗi bài có thể nằm trong nhiều lộ trình. Tổng số bài học là 21, không tính trùng.
- Trang Facebook: https://www.facebook.com/profile.php?id=61596506009854
- Group: https://www.facebook.com/groups/4387154551501983

## Lộ trình

### Học lại từ đầu (7 bài)

- [Lỗi #001: borrow và lend](loi-001/)
- [Quiz #001: borrow hay lend?](quiz-001/)
- [Lỗi #002: bored và boring](loi-002/)
- [Quiz #002: boring hay bored?](quiz-002/)
- [Lỗi #003: say và tell](loi-003/)
- [Mẫu câu #001: xin nghỉ phép](mau-cau-001/)
- [Mẫu câu #002: giới thiệu bản thân](mau-cau-002/)

### Tiếng Anh đi làm (5 bài)

- [Lỗi #001: borrow và lend](loi-001/)
- [Lỗi #003: say và tell](loi-003/)
- [Mẫu câu #001: xin nghỉ phép](mau-cau-001/)
- [Mẫu câu #002: giới thiệu bản thân](mau-cau-002/)
- [Quiz #001: borrow hay lend?](quiz-001/)

### Sửa phát âm (5 bài)

- [Lỗi #004: comfortable đọc mấy âm?](loi-004/)
- [Mẫu câu #003: 3 cặp âm dễ nhầm](mau-cau-003/)
- [Lỗi #002: bored và boring](loi-002/)
- [Quiz #002: boring hay bored?](quiz-002/)
- [Quiz nhanh #001: Chữ nào trong debt là chữ câm?](quiz-nhanh-001/)

## Cập nhật sau mỗi bài đăng

Dữ liệu bài học nằm trong 1 tệp duy nhất `lessons.json`. Sau mỗi bài đăng lên Facebook:

1. Viết file JSON của bài mới (đúng schema trong `CAP-NHAT-SITE.md`).
2. Chạy `python3 update_site.py --lesson /tmp/bai-moi.json`. Script thêm bài,
   dựng lại toàn bộ trang rồi đẩy lên GitHub Pages.

Trang này chạy bằng GitHub Pages, sinh từ `lessons.json` bằng `generate_site.py`.
