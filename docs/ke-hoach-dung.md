# Kế hoạch dựng API mở Kho bài học

Tài liệu kế hoạch, chưa dựng gì lên web thật. Mọi bước đều làm sau khi agent tối ưu web báo xong và deploy xong, vì cùng sửa `generate_site.py` nên không được làm song song với agent đó.

## Thứ tự làm

1. Agent tối ưu web deploy xong phương án A, phương án B và chỉ mục tìm kiếm nạp lười. Chờ báo xong hẳn rồi mới bắt đầu.
2. Dựng API theo các bước dưới đây, deploy 1 lần, kiểm chứng live.
3. Sau đó mới dựng giao diện mới đã duyệt. Giao diện mới thay mẫu trang, trang tài liệu `/api/` dùng chung mẫu trang nên sẽ tự nhận giao diện mới khi dựng lại toàn bộ.

Nếu agent thiết kế xong trước và cần dựng gấp thì đổi thứ tự bước 2 và bước 3 cho nhau cũng được, vì API chỉ thêm hàm mới và file mới, không sửa mẫu trang cũ. Dù đổi thứ tự nào cũng phải làm nối tiếp nhau, không làm song song.

## Các bước

### Bước 1: thêm hàm sinh API vào generate_site.py

Độ khó: trung bình. Thêm các hàm mới, không sửa hàm cũ.

1. `build_api_meta(data)`: sinh `api/v1/meta.json` từ số liệu thật, đếm từ `lessons.json` và bảng `VI_GLOSSARY`, không ghi số cố định trong code.
2. `build_api_lessons(data)`: sinh `api/v1/lessons.json`, danh sách gọn 62 bài theo schema trong đặc tả.
3. `build_api_lesson_detail(data)`: sinh 62 file `api/v1/lessons/{slug}.json`, mỗi file là 1 bài đầy đủ kèm khối `meta.source`.
4. `build_api_dictionary()`: sinh `api/v1/dictionary.json` từ bảng `VI_GLOSSARY`, chuyển mỗi nghĩa dạng mảng thành dạng object có `pos`, `meaning`, `example_en`, `example_vi`.
5. `build_api_paths(data)`: sinh `api/v1/paths.json` từ `site.paths` trong `lessons.json`.
6. `build_api_docs(data)`: sinh trang tài liệu `api/index.html` dùng chung mẫu trang của web, nội dung lấy từ đặc tả này, gồm ví dụ fetch và 4 app ví dụ.
7. `build_api_search_index(data)`: sinh `api/v1/search-index.json` từ chỉ mục tìm kiếm sẵn có, giữ nguyên schema.

Nguồn sự thật duy nhất vẫn là `lessons.json` và bảng `VI_GLOSSARY` trong `generate_site.py`. API không tạo ra nguồn dữ liệu thứ 2, chỉ chiếu dữ liệu sẵn có ra dạng khác.

### Bước 2: đưa thư mục api vào deploy

Độ khó: dễ. Thêm `api` vào `keep_dirs` và thêm các đường dẫn `/api/`, `/api/v1/meta.json`, `/api/v1/lessons.json`, `/api/v1/dictionary.json` vào `sitemap.xml`. Không đổi đường dẫn bài học cũ, không dời thư mục nào.

### Bước 3: thêm test API

Độ khó: trung bình. Thêm test mới vào `tests/test_site.py`, chạy cùng bộ test cũ:

1. Mọi file API đều là JSON hợp lệ, đọc được bằng `json.load`.
2. `lessons.json` của API có đúng 62 bài, mỗi bài đủ 13 trường của schema danh sách gọn.
3. Mỗi `slug` trong danh sách đều có file chi tiết `lessons/{slug}.json` tương ứng.
4. `dictionary.json` có đúng 852 từ, mỗi từ có ít nhất 1 nghĩa, mỗi nghĩa có `pos` và `meaning` bằng tiếng Việt.
5. Mọi file đều có khối `meta.source` với tên Trang, link web, link Facebook, giấy phép và câu ghi công.
6. Không có link bài học cũ nào đổi. So sánh `sitemap.xml` trước và sau, chỉ thêm đường dẫn mới.

### Bước 4: sinh thử trên máy local

Độ khó: dễ. Chạy `generate_site.py` trên máy local, kiểm tra:

1. Thư mục `api/` sinh đủ file: `index.html`, `v1/meta.json`, `v1/lessons.json`, `v1/lessons/` đủ 62 file, `v1/dictionary.json`, `v1/search-index.json`, `v1/paths.json`.
2. Đo kích thước thật từng file, đối chiếu với số ước lượng trong đặc tả: danh sách bài khoảng 29 KB, từ điển khoảng 36 KB.
3. Mở trang tài liệu `/api/` trên máy local, bấm thử các ví dụ fetch trong trang, chắc chắn code mẫu chạy được.

### Bước 5: deploy và kiểm chứng live

Độ khó: dễ. Deploy bằng `deploy_github_pages.py` chạy dòng lệnh, không import. Kiểm tra head trên remote trước khi đẩy, không force push, không dùng pipeline che mã lỗi, không chạy 2 lần deploy song song. Sau deploy, kiểm chứng live bằng curl:

1. `https://dongdarealest.github.io/sai-dau-sua-do/api/v1/meta.json` trả 200 và JSON hợp lệ.
2. `https://dongdarealest.github.io/sai-dau-sua-do/api/v1/lessons.json` trả 200, đủ 62 bài.
3. `https://dongdarealest.github.io/sai-dau-sua-do/api/v1/lessons/loi-001.json` trả 200, đủ trường chi tiết.
4. `https://dongdarealest.github.io/sai-dau-sua-do/api/v1/dictionary.json` trả 200, đủ 852 từ.
5. `https://dongdarealest.github.io/sai-dau-sua-do/api/` trả 200, trang tài liệu hiển thị đúng.
6. Mở 1 link bài học cũ, ví dụ `/loi-009/`, chắc chắn vẫn trả 200 và nội dung không đổi.

### Bước 6: viết lại README và thêm giấy phép

Độ khó: dễ. Viết lại `README.md` ở gốc repo theo dàn ý trong đặc tả, thêm 2 file giấy phép: `LICENSE` với toàn văn MIT cho code, `LICENSE-CONTENT.md` với toàn văn và link CC BY 4.0 cho nội dung. Commit riêng 1 lần, ghi rõ trong thông điệp commit là công bố API mở.

### Bước 7: rà lại thư mục giao-trinh trước khi công bố

Độ khó: dễ, bắt buộc. Kiểm tra từng file trong thư mục `giao-trinh/` của repo, chắc chắn không còn file sản phẩm trả phí nào nằm lẫn trong đó. Chỉ nội dung miễn phí đã đăng mới được công bố. Nếu phát hiện file trả phí thì dời ra khỏi repo trước khi công bố API.

### Bước 8: đăng bài giới thiệu API lên Trang

Việc của parent sau khi deploy xong, không thuộc bước dựng. Nội dung bài: Trang vừa mở API cho lập trình viên, kèm link trang tài liệu `/api/` ở bình luận đầu tiên. Caption dưới 60 chữ theo luật caption của Trang.

## Rủi ro cần tránh

1. Cây thư mục gốc chỉ thêm 1 thư mục `api`, các file API nằm gọn trong đó. Không sinh 852 file từ riêng lẻ, vì như vậy cây thư mục lại dài thêm đúng kiểu Đông vừa chê.
2. Không đổi tên trường hay xóa trường trong `lessons.json` để phục vụ API. API chiếu dữ liệu cũ ra dạng mới, nguồn dữ liệu không đổi.
3. Không nhận công của nguồn ngoài. Phiên âm lấy từ dictionaryapi.dev, nghĩa dự phòng lấy từ Wiktionary, dịch máy lấy từ MyMemory, tất cả đều ghi rõ nguồn trong đặc tả và trong trang tài liệu.
4. Không hứa hẹn máy chủ hay tìm kiếm phía máy chủ. API là file tĩnh, ai hỏi thì trả lời đúng như vậy.
5. Không công bố khi chưa rà thư mục `giao-trinh`. Đây là bước kiểm tra cuối cùng trước khi mở công khai.
