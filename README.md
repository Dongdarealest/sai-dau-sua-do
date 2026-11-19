# Kho bài học Sai Đâu Sửa Đó — Content engine học tiếng Anh mở

Học tiếng Anh từ lỗi người Việt hay mắc. Mỗi ngày sửa một lỗi nhỏ.

- **56 bài học** hiển thị trên web • **62 bài** trong API • **852 từ** trong từ điển • **3 lộ trình** • **6 Reel** đính kèm trong bài
- Trang mới: **Từ điển** (/tu-dien/), **Bảng lộ trình** (/bang-lo-trinh/), **Thư viện chủ đề** (/thu-vien-chu-de/), **Luyện nói** (/luyen-noi/). Mỗi bài học có thêm chế độ Học từng cụm.
- Trang Facebook: https://www.facebook.com/profile.php?id=61596506009854
- Group: https://www.facebook.com/groups/4387154551501983

## API mở

Toàn bộ dữ liệu học tiếng Anh của Trang, công khai dưới dạng file JSON tĩnh, không cần đăng ký, không cần khóa, không mất phí. Tài liệu đầy đủ cho lập trình viên ở trang [/api/](/api/).

Dùng ngay:

```js
const BASE = "https://dongdarealest.github.io/sai-dau-sua-do/api/v1/";
const data = await (await fetch(BASE + "lessons.json")).json();
const detail = await (await fetch(BASE + "lessons/loi-001.json")).json();
```

| Đầu dữ liệu | Nội dung |
|---|---|
| `/api/v1/meta.json` | Phiên bản, số lượng, nguồn, giấy phép |
| `/api/v1/lessons.json` | Danh sách gọn toàn bộ bài học |
| `/api/v1/lessons/{slug}.json` | Chi tiết đầy đủ 1 bài học |
| `/api/v1/dictionary.json` | Toàn bộ từ điển tiếng Việt |
| `/api/v1/search-index.json` | Chỉ mục tìm kiếm |
| `/api/v1/paths.json` | Lộ trình học |
| `/api/openapi.yaml` | Định nghĩa OpenAPI cho mọi đầu dữ liệu |
| `/api/` | Trang tài liệu cho lập trình viên |

## Giấy phép

- Code tạo trang web: MIT, xem file `LICENSE`.
- Nội dung bài học, bảng nghĩa tiếng Việt, ảnh bài học, lộ trình: CC BY 4.0, xem file `LICENSE-CONTENT.md`.
- Ghi công khi dùng lại nội dung: “Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang.”
- Tên Trang, logo chữ S kèm dấu tick và slogan không thuộc giấy phép mở.

## Đóng góp

Báo lỗi dữ liệu bằng issue, đề xuất bài mới bằng pull request. Nghĩa mới phải kiểm chứng bằng Cambridge hoặc Oxford trước khi gửi.

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

### Sửa phát âm (6 bài)

- [Lỗi #004: comfortable đọc mấy âm?](loi-004/)
- [Mẫu câu #003: 3 cặp âm dễ nhầm](mau-cau-003/)
- [Lỗi #002: bored và boring](loi-002/)
- [Quiz #002: boring hay bored?](quiz-002/)
- [Quiz nhanh #001: Chữ nào trong debt là chữ câm?](quiz-nhanh-001/)
- [Quiz nhanh #005: Wednesday đọc thế nào?](quiz-nhanh-005/)

## Cập nhật sau mỗi bài đăng

Dữ liệu bài học nằm trong 1 tệp duy nhất `lessons.json`. Sau mỗi bài đăng lên Facebook:

1. Viết file JSON của bài mới (đúng schema trong `CAP-NHAT-SITE.md`).
2. Chạy `python3 update_site.py --lesson /tmp/bai-moi.json`. Script thêm bài,
   dựng lại toàn bộ trang rồi đẩy lên GitHub Pages.

Trang này chạy bằng GitHub Pages, sinh từ `lessons.json` bằng `generate_site.py`.
