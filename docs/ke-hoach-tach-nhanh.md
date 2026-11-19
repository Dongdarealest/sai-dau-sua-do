# Kế hoạch tách nhánh: main làm mã nguồn, `gh-pages` phục vụ web

Ngày viết: 19/11/2026. Trạng thái: chỉ là thiết kế. Chưa tách nhánh, chưa đổi code, chưa deploy, chưa đổi cài đặt Pages.

## 0. Tóm tắt hướng đề xuất

Tách repo thành 2 nhánh. Nhánh `main` chỉ chứa mã nguồn và tài liệu. Nhánh `gh-pages` chỉ chứa web đã sinh. GitHub Pages chuyển sang phục vụ `gh-pages` ở cùng tên miền nên mọi URL giữ nguyên 100%, không cần chuyển hướng, không động vào link Facebook hay Google, không dời thư mục bài học nào.

Gốc `main` sau tách còn 8 mục. Gốc `gh-pages` giữ nguyên đúng cây web hiện tại. Thời điểm tách: sau khi API mở deploy xong lên `main`, trước khi giao diện mới deploy. Làm trong cửa sổ đêm từ 21:30 đến 07:00, tạm dừng cron đăng bài.

## 1. Trạng thái thật đã kiểm chứng ngày 19/11

Đọc trực tiếp bằng GitHub API, chỉ đọc, không đổi gì:

1. Nhánh mặc định là `main`. Pages đang phục vụ nhánh `main`, đường dẫn gốc, trạng thái built. Nhánh `gh-pages` chưa tồn tại, gọi ref trả 404.
2. Head `main` là commit 17cc4ce8, nội dung tối ưu web. Gốc remote có 64 thư mục và 10 file. Ghi chú: con số Đông thấy lúc 15:06 là 65 thư mục và 6 file, lúc đó chưa có 4 file gốc mới từ lần tối ưu là `styles.css`, `app.js`, `data.js`, `search-index.json`.
3. Thư mục local `web/` vừa là mã nguồn vừa là gốc site. Hàm `generate_site.py` ghi tại chỗ vào `web/`. Hàm `site_files()` trong `deploy_github_pages.py` chọn tập con để đẩy. Mã nguồn gồm script, test và tài liệu vận hành hiện KHÔNG nằm trên repo, chỉ có trên máy VM.
4. API mở đã sinh xong ở local, gồm `api/index.html`, `api/openapi.yaml`, `api/v1/` với các file `meta.json`, `lessons.json`, `dictionary.json`, `paths.json`, `search-index.json` và `api/v1/lessons/` cho từng bài. API chưa deploy, head `main` vẫn là 17cc4ce8.
5. Cron đăng bài gây deploy chạy lúc 07:00, 08:30, 10:00, 11:30, 13:00, 14:00, 15:00, 16:00, 17:30, 19:00, 20:30, 21:30. Cửa sổ không deploy dài nhất trong ngày là từ 21:30 đến 07:00, dài 9 tiếng 30 phút.
6. Không có repo git local trong workspace. Mọi thao tác git đều qua GitHub API bằng `gh_api`. Nhật ký deploy ghi trong `web/DEPLOY_LOG.md`, dòng cuối là commit 17cc4ce8 lúc 15:14.
7. Hai file giấy phép `LICENSE` và `LICENSE-CONTENT.md` đã có trong `web/` lúc 15:23 nhưng chưa lên remote, sẽ lên cùng lần deploy API.

## 2. Gốc `main` sau tách: 8 mục

1. `README.md`, mới, viết tay, đặt ở gốc workspace. Nội dung: giới thiệu dự án, link web live, link Facebook và Group, giới thiệu API mở, cách tra cứu, cách đóng góp, giấy phép. Không dùng bản `README.md` đã sinh trong `web/`, vì bản đó là trang giới thiệu của web, có số liệu bài học, thuộc về `gh-pages`.
2. `LICENSE`, giấy phép MIT cho code. Lấy từ `web/LICENSE`.
3. `LICENSE-CONTENT.md`, giấy phép CC BY 4.0 cho nội dung. Lấy từ `web/LICENSE-CONTENT.md`.
4. `CONTRIBUTING.md`, mới, ngắn. Nội dung: cách báo lỗi dữ liệu, cách đề xuất bài mới, quy tắc nội dung, quy tắc không gạch ngang trong chữ hiển thị.
5. `CHANGELOG.md`, mới. Nhật ký thay đổi công khai, ghi theo ngày, mỗi mục một dòng. Tài liệu nghiên cứu API đã nêu rõ lập trình viên cần nhật ký thay đổi công khai để tin dữ liệu không chết sau 3 tháng.
6. `web/`, mã nguồn sinh trang, dữ liệu, script, test và tài liệu vận hành. Danh sách đưa lên `main` ở mục 2.1.
7. `docs/`, tài liệu thiết kế và nghiên cứu đã chọn lọc. Danh sách ở mục 2.2.
8. `.gitignore`, mới. Loại `__pycache__/`, `node_modules/`, `backup/`, `_archive/`, `shots/`.

### 2.1. Nội dung thư mục `web/` trên `main`

Đưa lên `main` các file nguồn sau, giữ đúng đường dẫn con trong `web/`:

1. Script: `generate_site.py`, `update_site.py`, `deploy_github_pages.py`, `undo_deploy.py`, `sync_source_to_main.py` mới, viết ở bước 6.
2. Dữ liệu nguồn: `lessons.json`, `enrichment.json`.
3. Tài liệu vận hành: `CAP-NHAT-SITE.md`, `AUDIT-KYTHUAT.md`, `AUDIT-NOIDUNG.md`, `DEPLOY_LOG.md`.
4. Thư mục `tests/`, toàn bộ file test và script kiểm tra, trừ `tests/node_modules/`.
5. Tài nguyên nguồn: `fonts/` với các file `woff2`, `favicon.svg`, `giao-trinh/` với 2 file PDF đã tặng.
6. Hai file giấy phép `LICENSE` và `LICENSE-CONTENT.md` ở trong `web/` sẽ được copy ra gốc `main` khi đồng bộ, xem mục 2.3.

Không đưa lên `main` các file và thư mục sau, vì đó là web đã sinh, thuộc về `gh-pages`:

1. `index.html`, `styles.css`, `app.js`, `data.js`, `search-index.json`, `sitemap.xml`, `robots.txt`, `README.md` đã sinh trong `web/`.
2. Thư mục `api/` đã sinh, thư mục `images/` với các file `.jpg` đã nén.
3. Toàn bộ 61 thư mục trang có `index.html`, gồm thư mục bài học và thư mục tính năng, cùng các thư mục con của `lo-trinh/`.
4. Thư mục làm việc local: `__pycache__/`, `_archive/`, `backup/`, `shots/`, `tests/node_modules/`.

### 2.2. Nội dung thư mục `docs/` trên `main`

Chỉ đưa tài liệu đã hoàn thành và đã kiểm chứng, mỗi file giữ nguyên nội dung:

1. `api-spec.md`, `phan-nghien-cuu.md`, `ke-hoach-dung.md` từ thư mục `api/` trong workspace.
2. `20-trang-hoc-tieng-anh.md` từ thư mục `nghien-cuu/` trong workspace.
3. `quyet-dinh-duyet.md`, `de-xuat.md` từ thư mục `thiet-ke-moi/` trong workspace.
4. `ke-hoach-tach-nhanh.md`, chính tài liệu này, từ thư mục `toi-uu-cay-thu-muc/` trong workspace.

Ghi chú làm việc, lịch đăng bài, kế hoạch nội dung và file nháp vẫn ở lại workspace trên VM, không đưa lên repo.

### 2.3. Hai file giấy phép ở hai nơi

`LICENSE` và `LICENSE-CONTENT.md` cần có ở cả hai nhánh, với vai trò khác nhau. Trên `main`, hai file ở gốc là giấy phép của mã nguồn và nội dung. Trên `gh-pages`, hai file ở gốc là giấy phép đi kèm web đã sinh. File gốc duy nhất nằm trong `web/`. Script đồng bộ nguồn sẽ copy hai file này từ `web/` ra gốc `main` khi đồng bộ, còn script deploy web đã gồm hai file này trong danh sách đẩy lên `gh-pages`. Không sửa tay riêng từng bản, tránh hai bản lệch nhau.

## 3. Gốc `gh-pages`: giữ nguyên cây web hiện tại

Gốc `gh-pages` là đúng tập file mà `site_files()` đẩy hôm nay, không thêm, không bớt, không đổi tên:

1. File gốc: `index.html`, `lessons.json`, `README.md` đã sinh, `favicon.svg`, `sitemap.xml`, `robots.txt`, `styles.css`, `app.js`, `data.js`, `search-index.json`.
2. Thư mục trang: toàn bộ 61 thư mục có `index.html`, gồm bài học và trang tính năng, cùng thư mục con của `lo-trinh/`.
3. Thư mục tài nguyên: `fonts/`, `images/`, `giao-trinh/` với 2 file PDF.
4. Sau lần deploy API: thêm thư mục `api/` với `index.html`, `openapi.yaml`, `api/v1/` và các file JSON, thêm 2 file giấy phép ở gốc.

Như vậy sau lần deploy API, gốc `gh-pages` có 65 thư mục và 12 file. Mọi URL giữ nguyên vì Pages phục vụ `gh-pages` ở cùng tên miền `dongdarealest.github.io/sai-dau-sua-do/` và cùng đường dẫn như trước, ví dụ `/loi-009/`, `/tu-dien/`, `/api/v1/lessons.json`.

## 4. Vì sao không chọn gom thư mục bài học vào thư mục mẹ kèm chuyển hướng

Phương án thay thế là dời toàn bộ thư mục bài học vào một thư mục mẹ, ví dụ `bai-hoc/loi-001/`, và để lại ở URL cũ một file chuyển hướng. Đã đánh giá kỹ và không chọn, vì 5 lý do sau:

1. Gốc không sạch hơn. GitHub Pages cần một file ở đúng đường dẫn cũ để chuyển hướng, nên mỗi bài cũ vẫn cần một thư mục hoặc một file ở gốc. Gốc vẫn còn khoảng 55 mục chuyển hướng, chỉ là nội dung file đổi từ trang bài thành trang chuyển hướng. Điều Đông không thích là số lượng thư mục ở gốc, phương án này không giải quyết được điều đó.
2. Bảo trì tăng gấp đôi. Mỗi bài mới phải sinh 2 nơi: trang thật trong thư mục mẹ và file chuyển hướng ở URL cũ. Quên file chuyển hướng thì link cũ hỏng ngay. File chuyển hướng phải giữ mãi mãi vì 60 bài Facebook đã dẫn link cũ, không có ngày gỡ được.
3. Facebook xử lý chuyển hướng kém. Link xem trước trên Facebook do trình thu thập của Facebook tạo ra khi đọc thẻ OG ở URL được chia sẻ. File chuyển hướng bằng thẻ meta refresh không có thẻ OG của bài, trình thu thập có thể đọc trang chuyển hướng thay vì trang đích, làm hỏng xem trước của 60 bài đã đăng. Meta refresh không phải chuyển hướng 301 ở tầng máy chủ, Facebook không cam kết đi theo.
4. Google xử lý chuyển hướng meta refresh yếu hơn 301 thật. Thứ hạng và tín hiệu link chuyển chậm hơn, URL cũ có thể bị loại khỏi chỉ mục trong khi URL mới chưa kịp lên. Sitemap sẽ liệt kê URL mới trong khi lưu lượng vẫn đổ về URL cũ.
5. GitHub Pages không có chuyển hướng 301 ở tầng máy chủ. Không có file `_redirects`, không có `.htaccess`. Cách duy nhất còn lại là dùng plugin chuyển hướng của Jekyll, nhưng web hiện tại là HTML tĩnh thuần, không dùng Jekyll, không có front matter. Áp dụng plugin đó nghĩa là phải viết lại generator để sinh front matter cho mọi trang và dựa vào quá trình dựng Jekyll của GitHub, thêm một tầng dựng và một điểm hỏng mới, chỉ để làm việc mà nhánh `gh-pages` làm được ngay không cần chuyển hướng.

Kết luận: không chọn gom thư mục kèm chuyển hướng. Nhánh `gh-pages` giải quyết đúng gốc vấn đề mà không cần chuyển hướng nào, vì URL không đổi.

## 5. Vì sao không chọn repo site riêng

Phương án khác là giữ repo hiện tại làm mã nguồn và tạo repo mới cho web đã sinh. Không chọn, vì 3 lý do:

1. Tên miền live gắn với tên repo. Web hiện tại sống ở `dongdarealest.github.io/sai-dau-sua-do/`. Repo mới sẽ sống ở một đường dẫn khác, trừ khi repo cũ giữ lại file chuyển hướng, mà chuyển hướng đã bị loại ở mục 4, hoặc đổi tên repo, mà đổi tên làm hỏng mọi link git, link repo đã chia sẻ và lịch sử sao.
2. Hai repo nghĩa là hai nơi deploy, hai bộ quyền, hai nhật ký, gấp đôi chỗ có thể sai. Lịch đăng bài chạy 10 ca mỗi ngày, mỗi ca deploy, càng ít nơi deploy càng an toàn.
3. Nhánh `gh-pages` là cách làm chuẩn của chính GitHub cho đúng việc này: mã nguồn ở `main`, web ở `gh-pages`, cùng repo, cùng tên miền. Không cần phát minh lại.

## 6. Từng bước tách nhánh

Thứ tự bắt buộc: API deploy xong, rồi tách, rồi giao diện mới deploy. Không chạy 2 deploy song song ở bất kỳ bước nào. Mỗi bước xong phải kiểm chứng rồi mới sang bước sau.

### Bước 0. Deploy API lên `main` theo luồng cũ, rồi kiểm chứng

1. Agent dựng API chạy `deploy_github_pages.py` như hiện tại, đẩy lên `main`.
2. Kiểm chứng: đọc head `main` bằng API, phải là commit mới sau 17cc4ce8. Mở bằng curl `https://dongdarealest.github.io/sai-dau-sua-do/api/v1/meta.json` và `/api/v1/lessons.json`, cả hai trả 200. Mở trang chủ và một trang bài, cả hai trả 200.
3. Chỉ khi bước 0 xong mới bắt đầu tách. Nếu API deploy lỗi thì sửa API trước, không tách trong lúc API đang dở.

### Bước 1. Đóng băng deploy và lưu bản sao an toàn

1. Vào lúc 21:30, sau ca đáp án quiz, tạm dừng toàn bộ cron đăng bài gây deploy: 07:00, 08:30, 10:00, 11:30, 13:00, 14:00, 15:00, 16:00, 17:30, 19:00, 20:30, 21:30. Các cron chỉ đọc và giám sát như phát hiện sáng, outreach, tin thì không cần dừng vì không deploy.
2. Xác nhận không còn agent nào đang chạy deploy. Agent dựng API phải báo xong bước 0. Agent dựng giao diện mới chưa được deploy.
3. Copy `deploy_github_pages.py`, `undo_deploy.py` và `DEPLOY_LOG.md` vào `web/_archive/` kèm ngày, ví dụ `deploy_github_pages.py.2026-11-19.truoc-tach`. Đây là bản quay lui cho bước 9.
4. Kiểm chứng: đọc `DEPLOY_LOG.md`, dòng cuối phải là commit API ở bước 0. Đọc `web/_archive/`, đủ 3 file sao lưu.

### Bước 2. Tạo nhánh `gh-pages` từ head `main`

1. Gọi GitHub API tạo ref mới từ đúng head `main` hiện tại, không đổi file nào:

```
POST /repos/Dongdarealest/sai-dau-sua-do/git/refs
{"ref": "refs/heads/gh-pages", "sha": "<sha head main ở bước 0>"}
```

2. Kiểm chứng: gọi `GET /repos/Dongdarealest/sai-dau-sua-do/git/refs/heads/gh-pages`, sha trả về phải bằng đúng sha head `main`. Gọi cây của `gh-pages` ở chế độ đệ quy, số file phải bằng số file của `main`. Lúc này `gh-pages` và `main` có cùng một cây, web chưa đổi gì, chưa có rủi ro.

### Bước 3. Chuyển nguồn Pages sang `gh-pages` rồi kiểm chứng web còn sống

1. Chuyển nguồn Pages bằng API hoặc bằng giao diện web của GitHub ở Settings rồi Pages rồi Build and deployment rồi Branch. Bằng API:

```
PUT /repos/Dongdarealest/sai-dau-sua-do/pages
{"source": {"branch": "gh-pages", "path": "/"}}
```

2. Kiểm chứng: gọi `GET /repos/Dongdarealest/sai-dau-sua-do/pages`, trường nguồn phải ghi nhánh `gh-pages`, đường dẫn gốc. Chờ trạng thái build thành built.
3. Kiểm chứng bằng curl: trang chủ, `/loi-009/`, `/tu-dien/`, `/api/v1/meta.json`, `/api/v1/lessons.json` đều trả 200, nội dung đúng như trước khi chuyển. Trong lúc GitHub dựng lại từ nhánh mới, bản web cũ vẫn được phục vụ cho tới khi bản mới xong. Nếu sau 5 phút mà trang chủ vẫn lỗi thì quay lui ngay theo mục 9, vì lúc này `main` vẫn còn nguyên cây site.
4. Chỉ khi bước 3 xong mới được sang bước 4. Đây là điểm kiểm chứng quan trọng nhất của toàn bộ lần tách.

### Bước 4. Sửa script deploy và script hoàn tác sang nhắm `gh-pages`

Sửa 3 file trong `web/`, chỉ sửa local, chưa deploy gì:

1. `deploy_github_pages.py`:
   1. Thêm hằng `TARGET_BRANCH = "gh-pages"` ở đầu file, dùng hằng này cho mọi chỗ lấy head, tạo ref và cập nhật ref, thay cho biến `branch` lấy từ nhánh mặc định như hiện tại. Nhánh mặc định vẫn là `main`, nên không được dùng nhánh mặc định làm đích đẩy nữa.
   2. Sửa khối cuối file bật Pages: khi Pages chưa bật thì bật với nguồn `gh-pages`, không bật với `main`. Khi Pages đã bật thì chỉ đọc và in ra, không đổi gì.
   3. Giữ nguyên toàn bộ phần còn lại: đẩy cây đầy đủ, tái dùng blob trùng SHA, kiểm tra file tồn tại trước khi tạo blob, cảnh báo file ngoài danh sách, ghi `DEPLOY_LOG.md`, không force push.
2. `undo_deploy.py`:
   1. Đổi đích hoàn tác từ `refs/heads/main` sang `refs/heads/gh-pages`. Giữ nguyên `force=True` vì lùi ref là đi ngược, GitHub sẽ trả 422 nếu thiếu force.
   2. Chuỗi log hoàn tác vẫn đúng sau tách, vì `gh-pages` được tạo từ đúng head `main` nên mọi sha trong `DEPLOY_LOG.md` đều tồn tại trên `gh-pages`.
3. `CAP-NHAT-SITE.md`:
   1. Sửa mục nguyên tắc và mục deploy: deploy web đẩy lên `gh-pages`, mã nguồn đồng bộ lên `main` bằng script riêng ở bước 6, cron đăng bài chỉ deploy web, không bao giờ chạm `main`.
   2. Ghi rõ script `deploy_github_pages.py` vẫn cấm import như trước, chỉ chạy bằng dòng lệnh.
4. Kiểm chứng: đọc lại 3 file bằng mắt, tìm `TARGET_BRANCH` và `refs/heads/gh-pages`, xác nhận không còn chỗ nào ghi đích đẩy là `main`. Chạy `python3 -m py_compile` cho 2 file Python để chắc không lỗi cú pháp. Chưa chạy deploy ở bước này.

### Bước 5. Deploy thử lên `gh-pages` để chứng minh script nhắm đúng nhánh

1. Chạy `python3 deploy_github_pages.py --message "Kiểm chứng tách nhánh: deploy thử lên gh-pages, nội dung không đổi"` bằng dòng lệnh, từ thư mục `web/`.
2. Lần này nội dung không đổi so với cây remote nên commit mới có cùng cây với commit trước, chỉ khác sha commit. Đây là commit kiểm chứng, chấp nhận được, tên commit ghi rõ mục đích để sau này đọc log không nhầm với bài đăng.
3. Kiểm chứng: gọi `GET /repos/Dongdarealest/sai-dau-sua-do/commits/gh-pages`, head mới phải là commit vừa đẩy. Gọi head `main`, phải đứng yên ở commit bước 0, không đổi. Mở bằng curl trang chủ và `/loi-009/`, cả hai trả 200.
4. Nếu head `main` đổi hoặc commit thử không lên `gh-pages` thì dừng ngay, đọc lại bước 4, không sang bước 6.

### Bước 6. Viết 4 file gốc mới và script đồng bộ nguồn

1. Viết mới ở gốc workspace, chưa đẩy lên đâu:
   1. `README.md` theo dàn ý ở mục 2, mục 1.
   2. `CONTRIBUTING.md` theo dàn ý ở mục 2, mục 4.
   3. `CHANGELOG.md` theo dàn ý ở mục 2, mục 5, ghi dòng đầu là ngày tách nhánh và nội dung tách.
   4. `.gitignore` theo dàn ý ở mục 2, mục 8.
2. Chọn lọc tài liệu vào thư mục `docs/` trong workspace theo danh sách ở mục 2.2. Đọc lại từng file, bỏ mọi dòng ghi chú nội bộ chưa muốn công khai.
3. Viết mới `web/sync_source_to_main.py`, dùng đúng mẫu an toàn của `deploy_github_pages.py`:
   1. Đọc danh sách file nguồn ở mục 2.1, cộng 4 file gốc mới và thư mục `docs/`, cộng 2 file giấy phép copy từ `web/` ra gốc.
   2. Đọc head `main` làm commit cha, kiểm tra mọi file tồn tại trước khi tạo blob, tái dùng blob trùng SHA với cây remote, đẩy cây đầy đủ, không force push, ghi log riêng vào `web/SOURCE_SYNC_LOG.md` để không lẫn với `DEPLOY_LOG.md` của web.
   3. Script này chỉ chạy bằng dòng lệnh, không import, giống quy tắc của `deploy_github_pages.py`. Script từ chối chạy nếu phát hiện cron đăng bài đang chạy deploy, để hai lần đẩy không giẫm nhau.
4. Kiểm chứng: chạy script ở chế độ liệt kê trước, in danh sách file sẽ đẩy, đếm đủ file nguồn, xác nhận không có file web đã sinh nào lọt vào danh sách, ví dụ không có `loi-001/index.html`, không có `api/v1/lessons.json`, không có `images/`.

### Bước 7. Đồng bộ nguồn lên `main`, gốc `main` thành 8 mục

1. Chạy `python3 web/sync_source_to_main.py` bằng dòng lệnh. Lần này cây `main` được thay hoàn toàn bằng cây nguồn sạch, vì đẩy cây đầy đủ giống cơ chế deploy web.
2. Kiểm chứng: gọi `GET /repos/Dongdarealest/sai-dau-sua-do/contents/`, gốc `main` phải đúng 8 mục ở mục 2. Mở `https://github.com/Dongdarealest/sai-dau-sua-do`, trang repo phải hiện cây sạch, không còn 64 thư mục.
3. Kiểm chứng web không bị ảnh hưởng: gọi `GET /repos/Dongdarealest/sai-dau-sua-do/pages`, nguồn vẫn là `gh-pages`. Mở bằng curl trang chủ và `/loi-009/`, cả hai trả 200.
4. Kiểm chứng dữ liệu nguồn khớp web live: lấy sha blob của `web/lessons.json` trên `main` bằng API, so với sha blob của `lessons.json` trên `gh-pages`, hai sha phải bằng nhau vì cùng một nội dung.
5. Chỉ khi bước 7 xong mới được mở lại cron đăng bài.

### Bước 8. Mở lại cron đăng bài và lấy bài đăng đầu tiên làm bằng chứng sống

1. Mở lại toàn bộ cron đăng bài đã dừng ở bước 1.
2. Bài đăng đầu tiên sau khi mở lại sẽ chạy `update_site.py` rồi `deploy_github_pages.py` theo luồng mới. Kiểm chứng sau bài đó: head `gh-pages` phải tiến 1 commit, head `main` phải đứng yên, trang bài mới live ở URL đúng slug, trang chủ tăng 1 bài.
3. Nếu bài đó deploy lỗi thì ghi log, không đẩy tay, sửa theo đúng quy trình lỗi đã có trong `CAP-NHAT-SITE.md`.

### Bước 9. Bàn giao cho agent dựng giao diện mới

1. Giao diện mới dựng sau tách, deploy của nó nhắm `gh-pages` theo script đã sửa ở bước 4. Dặn rõ trong brief của agent dựng giao diện: không đổi đích đẩy, không đẩy lên `main`, kiểm chứng live bằng curl sau deploy.
2. Mọi thay đổi mã nguồn sinh trang trong đợt dựng giao diện, ví dụ sửa `generate_site.py`, sau khi xong phải chạy `sync_source_to_main.py` một lần để `main` có đúng bản mã nguồn đang chạy live.

## 7. Quy tắc vận hành sau tách, áp dụng lâu dài

1. Cron đăng bài chỉ deploy web lên `gh-pages`, không bao giờ chạm `main`. Cron gọi `update_site.py`, script này gọi `deploy_github_pages.py`, script deploy đã sửa ở bước 4 nên tự nhắm đúng nhánh.
2. Mọi thay đổi mã nguồn sinh trang, dữ liệu, test hay tài liệu vận hành đều đồng bộ lên `main` bằng `sync_source_to_main.py`, do parent hoặc agent chạy tay sau khi thay đổi xong. Không gắn đồng bộ nguồn vào cuối script deploy web, vì cron đăng bài chạy deploy web 10 ca mỗi ngày, gắn thêm sẽ làm cron chạm `main` và phá đúng ranh giới vừa dựng.
3. Mỗi tối kiểm tra một bất biến: sha blob của `web/lessons.json` trên `main` phải bằng sha blob của `lessons.json` trên `gh-pages`. Lệch thì chạy đồng bộ nguồn ngay, không để qua ngày, vì `main` là nơi duy nhất lưu mã nguồn và dữ liệu ngoài máy VM.
4. Mỗi yêu cầu bằng một commit, như quy tắc đã có từ 15/11, áp dụng cho cả hai nhánh. Tên commit ghi rõ thay đổi và ghi rõ nhánh đích khi cần, ví dụ commit deploy web và commit đồng bộ nguồn không gộp chung.
5. Đông nhắn hoàn tác thì chạy `undo_deploy.py` như trước, nhưng nay nó lùi `gh-pages`, không lùi `main`. Đọc `DEPLOY_LOG.md` trước khi chạy, xác nhận dòng cuối là commit web, không phải commit nguồn.
6. `CAP-NHAT-SITE.md` là tài liệu vận hành duy nhất cho luồng này. Mọi lần sửa luồng deploy hay đồng bộ đều cập nhật tài liệu này trong cùng lần sửa.

## 8. Rủi ro lớn nhất và cách tránh

### Rủi ro 1, lớn nhất: deploy đẩy cây site đầy đủ lên `main` sau khi `main` đã thành mã nguồn

Cơ chế deploy là đẩy cây đầy đủ, thay toàn bộ cây của nhánh đích, không phải gộp. Nếu một cron đăng bài, một lần deploy API hay một lần deploy giao diện chạy script cũ nhắm `main` sau bước 7 thì toàn bộ mã nguồn trên `main` sẽ bị cây site ghi đè và biến mất khỏi repo. Đây là đúng bài học sập web ngày 16/10, chỉ khác là lần này thứ mất là mã nguồn thay vì trang web.

Cách tránh, theo thứ tự:

1. Đóng băng và dừng cron đăng bài ở bước 1, trước mọi thao tác nhánh.
2. Sửa script deploy sang nhắm `gh-pages` ở bước 4, trước khi thay nội dung `main` ở bước 7.
3. Chứng minh bằng deploy thử ở bước 5: head `gh-pages` tiến, head `main` đứng yên.
4. Giữ bản sao script cũ trong `web/_archive/` và giữ toàn bộ mã nguồn trong `web/` local, nên dù `main` có bị ghi đè thì vẫn khôi phục được bằng cách chạy lại đồng bộ nguồn.

### Rủi ro 2: chuyển nguồn Pages làm web sập tạm thời

Khi chuyển nguồn Pages sang `gh-pages`, GitHub dựng lại web từ nhánh mới. Trong lúc dựng, bản web cũ vẫn được phục vụ cho tới khi bản mới xong, nhưng nếu bản mới dựng lỗi thì web có thể lỗi theo.

Cách tránh: tạo `gh-pages` từ đúng head `main` nên cây giống hệt, không có gì để dựng sai. Kiểm chứng bằng curl ở bước 3 trước khi làm tiếp. Nếu sau 5 phút mà trang chủ vẫn lỗi thì chuyển nguồn Pages về `main` ngay, vì lúc đó `main` vẫn còn nguyên cây site. Chỉ thay nội dung `main` ở bước 7, sau khi `gh-pages` đã chứng minh phục vụ được web.

### Rủi ro 3: script deploy vô tình bật lại Pages nguồn `main`

Khối cuối `deploy_github_pages.py` hiện có đoạn bật Pages khi chưa bật, với nguồn là nhánh mặc định. Sau tách, nếu đoạn này chạy sai thì Pages có thể bị chỉ lại về `main`.

Cách tránh: sửa khối này ở bước 4 để nguồn bật là `gh-pages`. Đọc lại file bằng mắt sau khi sửa. Ngoài ra sau bước 3 thì Pages đã bật rồi nên đoạn này không chạy nữa trong các lần deploy thường, chỉ còn là đường lui.

### Rủi ro 4: hoàn tác nhắm sai nhánh

`undo_deploy.py` hiện ghi cứng đích là `refs/heads/main` với `force=True`. Nếu quên sửa mà Đông nhắn hoàn tác sau tách thì lệnh sẽ lùi nhánh `main`, tức là lùi mã nguồn, trong khi web trên `gh-pages` không đổi gì.

Cách tránh: sửa cùng đợt với script deploy ở bước 4, kiểm chứng bằng mắt trước bước 5. Không dùng lệnh hoàn tác cho tới khi bước 5 xong.

### Rủi ro 5: `main` và web live lệch nhau

Mã nguồn và dữ liệu chỉ được đồng bộ lên `main` bằng tay, trong khi web live đổi 10 ca mỗi ngày. Quên đồng bộ thì `main` cũ dần, tới lúc cần khôi phục từ `main` sẽ thiếu bài mới nhất.

Cách tránh: kiểm tra bất biến sha của `lessons.json` mỗi tối ở mục 7, mục 3. Đồng bộ nguồn ngay sau mỗi đợt sửa mã nguồn, ví dụ sau đợt dựng giao diện mới ở bước 9.

### Rủi ro 6: API deploy và lần tách giẫm nhau

API đang dựng và sắp deploy lên `main`. Nếu tách bắt đầu khi API chưa deploy xong thì `gh-pages` sẽ được tạo từ cây chưa có API, rồi API deploy lên `main` sau đó sẽ làm hai nhánh lệch nhau ngay từ đầu.

Cách tránh: bước 0 bắt buộc API deploy xong và kiểm chứng live trước. Không chạy 2 deploy song song ở bất kỳ bước nào. Agent dựng API và agent tách nhánh không chạy cùng lúc.

## 9. Kế hoạch quay lui

### Quay lui trước bước 7, khi `main` vẫn còn cây site

1. Chuyển nguồn Pages về `main` bằng API hoặc giao diện web, giống bước 3 nhưng đổi nhánh về `main`.
2. Kiểm chứng bằng curl trang chủ và `/loi-009/` trả 200.
3. Xóa ref `gh-pages` nếu muốn dọn sạch, không bắt buộc, vì nhánh thừa không ảnh hưởng web. Lệnh xóa ref bằng API: `DELETE /repos/Dongdarealest/sai-dau-sua-do/git/refs/heads/gh-pages`.
4. Mở lại cron đăng bài. Web không đổi gì trong suốt quá trình quay lui vì `main` chưa hề bị chạm.

### Quay lui sau bước 7, khi `main` đã thành mã nguồn

1. Lấy script cũ từ `web/_archive/` đã lưu ở bước 1, khôi phục `deploy_github_pages.py` bản nhắm `main`.
2. Chuyển nguồn Pages về `main`.
3. Chạy script cũ để đẩy lại cây site đầy đủ từ `web/` local lên `main`. Cây site trong `web/` local vẫn đầy đủ nên lần đẩy này khôi phục đúng trạng thái trước tách.
4. Kiểm chứng bằng curl trang chủ và `/loi-009/` trả 200, rồi mở lại cron.
5. Sau khi sửa xong nguyên nhân, muốn tách lại thì làm lại từ bước 2 với head `main` mới.

### Điểm an toàn cuối cùng

Mọi trạng thái đều tái tạo được từ thư mục `web/` local: web đã sinh nằm đó, mã nguồn nằm đó, dữ liệu nằm đó, nhật ký deploy nằm đó. Mất cả hai nhánh trên GitHub vẫn dựng lại được, chỉ cần chạy deploy và đồng bộ nguồn từ đầu.

## 10. Việc không làm trong lần tách này

1. Không đổi URL, không dời thư mục bài học, không đổi tên repo, không thêm tên miền riêng.
2. Không đưa ảnh gốc vào repo. Ảnh gốc của bài học nằm ở các thư mục ngày trong workspace, ví dụ `ngay-04/`, hiện chỉ có trên máy VM, không nằm trong repo. Đưa ảnh gốc vào repo là việc riêng sau này, cần quyết riêng vì dung lượng và vì ảnh gốc có thể chứa bản nháp chưa đăng. Lần tách này không động vào ảnh gốc.
3. Không thử lệnh hoàn tác thật trên production để kiểm chứng. Chỉ kiểm bằng đọc code và chuỗi log, vì chạy thật sẽ lùi web live.
4. Không gộp tài liệu làm việc chưa hoàn thành vào `docs/`. Chỉ tài liệu đã xong và đã kiểm chứng mới lên `main`.
