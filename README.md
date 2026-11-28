# Kho bài học Sai Đâu Sửa Đó: Content engine học tiếng Anh mở

Học tiếng Anh từ lỗi người Việt hay mắc. Mỗi ngày sửa một lỗi nhỏ.

- **110 bài học** hiển thị trên web • **118 bài** trong API • **852 từ** trong từ điển • **3 lộ trình** • **8 Reel** đính kèm trong bài
- Trang mới: **Từ điển** (/tu-dien/), **Bảng lộ trình** (/bang-lo-trinh/), **Thư viện chủ đề** (/thu-vien-chu-de/), **Luyện nói** (/luyen-noi/), **Luyện nghe** (/luyen-nghe/), **Luyện viết** (/luyen-viet/), **Luyện đọc** (/luyen-doc/), **Cộng đồng** (/cong-dong/). Mỗi bài học có thêm chế độ Học từng cụm.
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

### Học lại từ đầu (8 bài)

- [Lỗi #001: borrow và lend](loi-001/)
- [Quiz #001: borrow hay lend?](quiz-001/)
- [Lỗi #002: bored và boring](loi-002/)
- [Quiz #002: boring hay bored?](quiz-002/)
- [Lỗi #003: say và tell](loi-003/)
- [Mẫu câu #001: xin nghỉ phép](mau-cau-001/)
- [Mẫu câu #002: giới thiệu bản thân](mau-cau-002/)
- [Ngữ pháp B1/B2 #002: câu điều kiện loại 2](ngu-phap-b1-b2-002/)

### Tiếng Anh đi làm (10 bài)

- [Lỗi #001: borrow và lend](loi-001/)
- [Lỗi #003: say và tell](loi-003/)
- [Mẫu câu #001: xin nghỉ phép](mau-cau-001/)
- [Mẫu câu #002: giới thiệu bản thân](mau-cau-002/)
- [Quiz #001: borrow hay lend?](quiz-001/)
- [Ngữ pháp B1/B2 #002: câu điều kiện loại 2](ngu-phap-b1-b2-002/)
- [Lỗi #011: 25 years old](cau-nay-ai-cung-tung-noi-sai/)
- [Mẫu câu #010: make và do](mau-cau-010/)
- [Lỗi nhanh #008: reply và reply to](loi-nhanh-008/)
- [Quiz #011: make và do](quiz-011/)

### Sửa phát âm (7 bài)

- [Lỗi #004: comfortable đọc mấy âm?](loi-004/)
- [Mẫu câu #003: 3 cặp âm dễ nhầm](mau-cau-003/)
- [Lỗi #002: bored và boring](loi-002/)
- [Quiz #002: boring hay bored?](quiz-002/)
- [Quiz nhanh #001: Chữ nào trong debt là chữ câm?](quiz-nhanh-001/)
- [Quiz nhanh #005: Wednesday đọc thế nào?](quiz-nhanh-005/)
- [Quiz nhanh #006: Chữ nào câm trong receipt?](quiz-nhanh-006/)

Trang này chạy bằng GitHub Pages, sinh từ `lessons.json`.
