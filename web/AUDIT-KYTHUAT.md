# Audit kỹ thuật — Website Kho bài học "Sai Đâu Sửa Đó"

- **Phạm vi audit:** `~/workspace/sai-dau-sua-do/web/` — `generate_site.py` (1.296 dòng),
  `lessons.json` (11 bản ghi: 9 bài học + 2 reel ẩn), `deploy_github_pages.py`,
  `update_site.py`, `undo_deploy.py`, `CAP-NHAT-SITE.md`, file HTML đã sinh
  (`index.html` 52.758 byte, `loi-001/index.html` 38.297 byte, `quiz-001/index.html`,
  `lo-trinh/hoc-lai-tu-dau/index.html`).
- **Ngày audit:** 15/11/2026. **Loại:** chỉ audit + thiết kế. **KHÔNG sửa file nào, KHÔNG deploy.**
- **Trạng thái site tại thời điểm audit:** 9 bài học, 3 lộ trình, 27 câu chấm ngay,
  wizard 6 bước (Lỗi/Mẫu câu) / 4 bước (Quiz), chế độ tối, chuỗi ngày học, ảnh JPEG q85
  (9 ảnh, tổng 692 KB, đều 1080×1080).
- **Kết quả đếm:** **Nghiêm trọng: 5 · Cao: 10 · Trung bình: 18 · Thấp: 13 — tổng 46 phát hiện.**

> Quy ước: số dòng là dòng trong `generate_site.py`, trừ khi ghi rõ file khác.
> "Đã kiểm chứng" = đọc trực tiếp từ file đã sinh / chạy lệnh kiểm tra.
> "Chưa kiểm chứng live" = suy luận từ semantics của API, cần kiểm chứng trên repo thử
> trước khi kết luận cuối.

---

## 1. Phát hiện theo mức độ

### 1.1. Nghiêm trọng (5)

#### S-01 — Một ngoại lệ `localStorage` làm chết toàn bộ JS dùng chung (toggle theme, nút Nghe, chấm quiz)
- **Vị trí:** `generate_site.py:274–352` (`SHARED_JS`); dòng 286 (IIFE theme),
  dòng 278 (`saveJSON`), dòng 282 (`updateStreak`).
- **Bằng chứng:**
  - Dòng 286: `(function(){const t=localStorage.getItem("sdsc-theme"); ...})();` —
    `getItem` **không** nằm trong `try/catch`. Trong chế độ ẩn danh chặn storage,
    Safari ITP, hoặc khi cookie/storage bị tắt, `localStorage.getItem` ném
    `SecurityError`. Ngoại lệ này thoát khỏi IIFE và **hủy toàn bộ phần còn lại của
    cùng một khối `<script>`**: listener toggle theme (dòng 287), listener nút Nghe
    (dòng ~300), khởi tạo grading `document.querySelectorAll(".grade").forEach(...)`
    (dòng ~330), `updatePracticeScore()` (dòng ~348) đều không chạy. Hậu quả:
    toàn bộ quiz/luyện trên trang **không bấm được**, nút Nghe chết, nút đổi theme chết.
    (Khai báo `function` được hoisted nên `loadJSON`/`speak` vẫn tồn tại, nhưng
    không có handler nào gắn vào chúng.)
  - Dòng 278: `function saveJSON(k,v){localStorage.setItem(k,JSON.stringify(v))}` —
    không `try/catch`. `setItem` ném `QuotaExceededError` khi đầy quota (Safari
    mobile ~5 MB, nhưng `localStorage` dùng chung cả origin).
  - Dòng 282: `updateStreak()` gọi `localStorage.setItem` không bảo vệ.
  - Chỉ `loadJSON` (dòng 277) và `loadStreak` (dòng 281) có `try/catch` — và
    `loadJSON` chỉ cứu được `getItem`/`JSON.parse`, không cứu được `setItem`.
- **Kịch bản tái hiện:** bật "Block all cookies" / private mode chặn storage trên
  Safari iOS → mở bất kỳ trang bài nào → bấm đáp án quiz: không có phản hồi gì.
- **Mức độ:** nghiêm trọng vì là **single point of failure** cho toàn bộ tương tác.

#### S-02 — `gradeWidget` ghi storage TRƯỚC khi hiện kết quả: đầy quota → đáp án bị khóa mà không có phản hồi
- **Vị trí:** `generate_site.py:313–328` (hàm `gradeWidget` trong `SHARED_JS`).
- **Bằng chứng:** thứ tự trong hàm là: disable tất cả `.opt` → tô đúng/sai →
  `saveJSON(PRAC_KEY, s)` → mới `r.style.display="block"` hiện kết quả. Nếu
  `saveJSON` ném (xem S-01), ngoại lệ xảy ra **sau khi nút đã bị disable** nhưng
  **trước khi hiện `.grade-result`** → người học thấy đáp án bị khóa, không biết
  mình đúng hay sai, nút "Làm lại" vẫn bấm được nhưng trạng thái đã hỏng một nửa
  (đáp án đúng đã bị tô xanh nhưng không có giải thích — mâu thuẫn hiển thị).
- **Sửa đúng:** đổi thứ tự — hiện kết quả trước, ghi storage sau, và bọc ghi storage
  trong `try/catch` (lưu thất bại thì vẫn hiện kết quả + cảnh báo nhẹ).

#### S-03 — `renderToday()` không kiểm tra slug: 1 slug lạ trong lộ trình làm chết cả khối "Ôn hôm nay" + chuỗi học
- **Vị trí:** `generate_site.py:597–668` (`HOMEPAGE_JS`), dòng 631.
- **Bằng chứng:**
  - Dòng 622–633: `let next=order.find(s=>!done[s]); ... const l=window.SDSC_LESSONS[next];`
    rồi dùng `l.code`, `l.title`, `l.why` **không kiểm tra `l` tồn tại**.
    `renderProgress` (dòng ~603) và `renderReview` (dòng ~650) đều có guard
    `.filter(s=>window.SDSC_LESSONS[s])` — riêng `renderToday` không có.
  - `HOMEPAGE_JS` gọi tuần tự cuối file: `renderProgress();renderToday();renderReview();renderStreak();`
    Nếu `renderToday` ném `TypeError`, `renderReview` và `renderStreak` **không bao giờ chạy**
    → mất khung "Ôn hôm nay" và dòng chuỗi học, dù 2 hàm đó hoàn toàn khỏe mạnh.
  - Cách slug lạ lọt vào: `update_site.py` thêm bài vào `path["order"]` rồi bài đó
    bị xóa khỏi `lessons.json` (gỡ bài) mà `order` không được dọn; hoặc lộ trình
    trỏ tới slug reel (`show_in_ui: false`, không có trong `SDSC_LESSONS`).
    Hiện tại 3 lộ trình đều sạch (đã đối chiếu: 7 + 5 + 4 slug đều tồn tại) nên lỗi
    đang **tiềm ẩn, chưa phát nổ**.
- **Sửa đúng:** `next` phải lọc qua `window.SDSC_LESSONS` trước (`order.find(s=>!done[s] && window.SDSC_LESSONS[s])`),
  và bọc mỗi `render*()` trong `try/catch` riêng để một khối hỏng không kéo sập các khối khác.

#### S-04 — `undo_deploy.py` gần như chắc chắn KHÔNG hoàn tác được (PATCH ref `force=False` để lùi commit)
- **Vị trí:** `undo_deploy.py:26–32`; docstring dòng 5–6 tự nhận sai.
- **Bằng chứng:** script `PATCH /repos/{owner}/{repo}/git/refs/heads/main` với
  `{"sha": prev, "force": False}`. Theo GitHub API, cập nhật ref về commit cũ hơn
  trong cùng lịch sử là **non-fast-forward** và bắt buộc `force: true`; với
  `force: false` GitHub trả **422**. Docstring (dòng 5) ghi "chỉ được khi là
  fast-forward ngược, GitHub cho phép di chuyển ref về commit cũ hơn" — điều này
  **sai với semantics của API**. `DEPLOY_LOG.md` hiện có 3 dòng (commit
  `6280870` → `2fcd5b1` → `b5e86c4`), nghĩa là lần "hoàn tác" đầu tiên theo đúng
  quy trình Đông đã chốt ("Đông nhắn 'hoàn tác' thì chạy `undo_deploy.py`") sẽ
  rơi vào nhánh `except GitHubError` và in "KHÔNG hoàn tác được".
- **Chưa kiểm chứng live:** chưa chạy lệnh thật (chạy thật sẽ đổi ref của repo
  production). Cần kiểm chứng trên repo thử trước khi kết luận 100%.
- **Rủi ro kèm theo:** sau khi hoàn tác (nếu sửa thành `force=True`), log không được
  cập nhật (không thêm dòng, không xóa dòng cũ) → chạy "hoàn tác" lần 2 sẽ đọc
  lại đúng dòng cuối cũ và lùi về cùng một `prev` (không lùi thêm được nữa);
  `parts[2]` (dòng 26) không kiểm tra độ dài → log sai định dạng gây `IndexError`
  không được bắt (traceback thay vì thông báo lỗi đẹp); `log.read_text` không có
  `try` (file mất → traceback).

#### S-05 — `deploy_github_pages.py` ghi đè README đã sinh bằng hằng README cũ, sai sự thật
- **Vị trí:** `deploy_github_pages.py:21–27` (hằng `README`) và dòng 113
  (`if rel == "README.md": raw = README.encode(...)`).
- **Bằng chứng:** `generate_site.py` sinh `README.md` đúng từ dữ liệu
  (`render_readme`, dòng 1205–1238: "9 bài học • 3 lộ trình • 2 Reel", link từng bài).
  Nhưng khi deploy, file `README.md` trong cây push **không phải file đã sinh** mà là
  hằng string trong deploy script, ghi: "file duy nhất là `index.html`
  (dữ liệu 12 bài đầu nhúng sẵn trong file)" — **sai cả 3 ý**: không phải 12 bài
  (đang là 9 bài học + 2 reel), không phải file duy nhất, dữ liệu không còn nhúng
  trong `index.html` mà nằm ở `lessons.json`. Nghĩa là **mọi lần deploy đều đẩy
  README sai lên repo**, và README đúng do generator sinh ra không bao giờ lên được.
- **Sửa đúng:** bỏ hằng `README` trong deploy script, đọc file `README.md` đã sinh
  trên đĩa như mọi file khác (chỉ giữ seed README cho repo mới hoàn toàn chưa có commit).

---

### 1.2. Cao (10)

#### H-01 — Điểm luyện tập hiển thị là điểm TOÀN SITE (27 câu) nhưng đặt trong từng trang bài như điểm của bài đó
- **Vị trí:** `generate_site.py:340–347` (`updatePracticeScore`), dòng 899–907
  (`total_graded`, `totals_script`); `lesson_steps` dòng 516–555.
- **Bằng chứng:** `PRAC_KEY` (`sdsc-practice-v2`) là một object toàn cục, khóa theo
  `slug:index`. `updatePracticeScore()` đếm **mọi** khóa đã lưu và chia cho
  `window.SDSC_TOTAL_GRADED` = 27 (tổng quiz + practice của cả 9 bài). Dòng chữ
  "Kết quả luyện tập: X / 27 câu đúng (Y đã làm)" xuất hiện trong **mỗi trang bài**,
  ngay dưới phần "Luyện ngay" của bài đó. Người học làm xong 3 câu ở Lỗi #001 sẽ
  thấy "3 / 27 câu đúng" — gây hiểu nhầm là bài này có 27 câu, hoặc mình mới làm
  được 3/27 của bài. Đã kiểm chứng số 27 trong `loi-001/index.html` đã sinh
  (`window.SDSC_TOTAL_GRADED=27`).
- **Sửa đúng:** hiển thị điểm theo bài (`đúng/tổng của bài này`) + điểm toàn site
  riêng ở trang chủ (`renderProgress` đã có vị trí "Luyện tập:" — dùng chung một nguồn).

#### H-02 — Kết quả luyện chỉ lưu boolean: tải lại trang mất lựa chọn đã chọn, không khôi phục được "đã chọn sai đáp án nào"
- **Vị trí:** `generate_site.py:322` (`s[key]=(choice===answer)`) và khối khôi phục
  dòng ~333–341.
- **Bằng chứng:** giá trị lưu là `true/false`. Khi tải lại, khối khôi phục chỉ tô
  xanh đáp án đúng và ghi "Bạn đã làm, đáp án là X" — **không tô đỏ lựa chọn sai
  của người học** (vì không còn biết họ đã chọn gì). Người học quay lại không biết
  mình từng sai ở đâu. Nút "Làm lại" xóa khóa (`delete s[key]`) nên không có cách nào
  xem lại lịch sử chọn. Đây là mất dữ liệu do thiết kế schema, không phải bug nhất thời.
- **Sửa đúng:** lưu `{choice, correct, at}` thay vì boolean (xem §2.1).

#### H-03 — Bộ lọc chủ đề/loại HARDCODE: chủ đề mới không bao giờ lọc được
- **Vị trí:** `generate_site.py:696` — `const TOPICS=["Tất cả","công sở","giao tiếp","phát âm"]`,
  `const TYPES=["Tất cả","Lỗi","Mẫu câu","Quiz"]`.
- **Bằng chứng:** `CAP-NHAT-SITE.md` cho phép topic `ngữ pháp`, `từ vựng`,
  `quiz tổng hợp`, `nhắc lại` — bài đầu tiên thuộc các topic này sẽ **xuất hiện
  trong lưới nhưng không có chip nào để lọc tới nó** (chip chỉ render 4 topic cũ).
  Lỗi cùng họ: dữ liệu tìm kiếm `data-search` (dòng 924–927, 951–954) được sinh
  từ Python nên đúng, nhưng chip lọc thì hardcode trong JS. `TYPES` thiếu `Reels`
  (hiện reel đang ẩn khỏi UI nên chưa phát nổ; nếu sau này reel hiện riêng sẽ lặp lại lỗi).
- **Sửa đúng:** sinh `TOPICS`/`TYPES` từ `lessons.json` lúc generate (giống cách
  `SDSC_LESSONS`/`SDSC_PATHS` đã làm ở `data_script`, dòng 972–981), kèm đếm số bài
  mỗi chip.

#### H-04 — `generate_site.py` không validate `lessons.json`: một trường thiếu là sập cả lần dựng
- **Vị trí:** `generate_site.py:1244–1296` (`main`), `quiz_block` dòng ~470,
  `card_html` dòng 910, `og_description` dòng ~571, `lessons_js` dòng ~963.
- **Bằng chứng (truy cập trực tiếp, không `.get`):**
  - `lessons_js`: `l["code"], l["title"], l["why"], l["topic"], l["date"]` — thiếu
    một trường → `KeyError`, traceback, không báo tên bài lỗi.
  - `quiz_block`: `q = lesson["quiz"]` rồi `q.get(...)` — bài type `Quiz` mà
    `quiz: null` → `AttributeError: 'NoneType' object has no attribute 'get'`.
  - `og_description`: `lesson["quiz"]["question"]` với quiz `null` → `TypeError`.
  - `card_html`: `q['question']`, `q['prompt']` tương tự.
  - `main()` đọc `lessons.json` bằng `json.loads` không `try` — file hỏng JSON
    (lỗi tay khi sửa) → traceback thay vì thông báo "dòng N lỗi".
  - `update_site.py` cũng chỉ validate `quiz.answer` (dòng 50–56), **không validate
    `practice[].answer`**: một câu practice có `answer: 5` với 2 lựa chọn sẽ sinh
    trang mà `gradeWidget` tính `String.fromCharCode(65+5)` = "F" và không bao giờ
    tô đúng → câu luyện **không thể làm đúng**.
- **Sửa đúng:** thêm `validate_lessons(data)` chạy đầu `main()` + đầu `update_site.py`,
  kiểm tra: đủ trường, `type` hợp lệ, `answer` trong khoảng, `practice ≥ 2`,
  `slug` khớp regex `^[a-z0-9-]+$`, `date` đúng `YYYY-MM-DD`, `fb` là URL http(s),
  `image_src` tồn tại và không thoát khỏi workspace.

#### H-05 — `main()` xóa toàn bộ `images/` TRƯỚC khi kiểm tra ảnh: chạy lỗi giữa chừng để lại site dở dang
- **Vị trí:** `generate_site.py:1252–1262`.
- **Bằng chứng:** thứ tự là `shutil.rmtree(img_dir)` → `mkdir` → lặp từng bài,
  `if not src.exists(): sys.exit(1)`. Nếu bài thứ 5 thiếu ảnh, tiến trình thoát
  **sau khi đã xóa sạch 9 ảnh cũ và chỉ ghi lại được 4 ảnh mới**; các `index.html`
  cũ vẫn trỏ tới ảnh đã mất. Lỗi này đúng vào "điểm không quay lại được" của quy trình.
- **Sửa đúng:** kiểm tra đủ ảnh của mọi bài TRƯỚC khi `rmtree`; hoặc build vào
  thư mục tạm rồi đổi tên nguyên tử (`os.replace`) khi xong.

#### H-06 — Font "Be Vietnam Pro" + "Inter" được khai nhưng KHÔNG BAO GIỜ được tải
- **Vị trí:** CSS dòng 65 (`font-family:"Be Vietnam Pro","Inter",system-ui,...`),
  `page_shell` dòng ~573 (không có thẻ `<link>` nào); canvas `drawShare` dòng ~800.
- **Bằng chứng đã kiểm chứng:** `grep -o '<link[^>]*>' index.html loi-001/index.html`
  → **không có thẻ `<link>` nào** trong file đã sinh: không favicon, không Google
  Fonts, không preload. Không có `@font-face` trong CSS. Toàn site đang render bằng
  `system-ui` — tức là **thiết kế typography (nhận diện dùng Be Vietnam Pro) chưa
  từng hiển thị đúng** trên máy người học không cài sẵn 2 font này. Canvas chia sẻ
  (`x.font="900 200px 'Be Vietnam Pro',...'`) cũng fallback font hệ thống, ảnh
  chia sẻ khác hẳn thiết kế.
- **Sửa đúng:** thêm `<link rel="preconnect" href="https://fonts.googleapis.com">` +
  Google Fonts CSS cho Be Vietnam Pro (400/600/700/900) + Inter (400/600/700),
  `display=swap`; hoặc tự host woff2 trong `fonts/` (khuyến nghị cho GitHub Pages
  để không phụ thuộc mạng ngoài + canvas dùng được font sau `document.fonts.ready`).

#### H-07 — Lưới thẻ tràn ngang ở viewport hẹp (~320 px)
- **Vị trí:** CSS dòng 126 (`.grid{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}`),
  dòng 98 (`.paths` dùng `minmax(280px,1fr)`).
- **Bằng chứng:** `.wrap` có `padding:0 16px` → ở viewport 320 px, chiều rộng nội dung
  còn 288 px, **nhỏ hơn track tối thiểu 300 px** của `.grid` → thẻ tra cứu rộng hơn
  màn hình, xuất hiện cuộn ngang. iPhone SE 375 px (nội dung 343 px) thì vừa, nhưng
  máy 320 px, chế độ chia đôi màn hình, hoặc trình duyệt thu hẹp đều vỡ. `.paths`
  (280 px) vừa khít 288 px nhưng không còn biên an toàn. Chỉ có **một breakpoint**
  `@media(max-width:560px)` (dòng 244–251) cho toàn site.
- **Sửa đúng:** `.grid{minmax(min(100%,300px),1fr)}` hoặc `minmax(260px,1fr)` +
  breakpoint 360 px; thêm `@media(max-width:380px)` giảm padding `.wrap` còn 12 px.

#### H-08 — Không có favicon: mọi lượt truy cập sinh 1 request 404, tab trình duyệt mất nhận diện
- **Vị trí:** `page_shell` — không có `<link rel="icon">`; trong `web/` không có
  `favicon.ico` / `favicon.svg` / `apple-touch-icon.png` (đã `ls` kiểm tra).
- **Bằng chứng:** trình duyệt tự request `/sai-dau-sua-do/favicon.ico` → GitHub Pages
  trả 404. Nhỏ nhưng là lỗi "mặt tiền": tab không có icon S+tick, người học lưu
  bookmark không nhận ra trang; log 404 nhiễu.
- **Sửa đúng:** thêm `favicon.svg` (chữ S trắng + tick cam trên nền navy, đúng logo)
  + `<link rel="icon" type="image/svg+xml" href="/sai-dau-sua-do/favicon.svg">`
  và đưa vào danh sách `site_files()` của deploy script.

#### H-09 — Ghi đè không cảnh báo ở `update_site.py`: trùng slug thay cả bài, gắn reel xóa reel cũ
- **Vị trí:** `update_site.py:100–107` (replace khi trùng slug), dòng 90–95 (`attach_to`).
- **Bằng chứng:** thêm bài có slug đã tồn tại → `lessons[i] = new` **lặng lẽ thay
  toàn bộ bản ghi cũ** (kể cả `practice`, `remember`, `paths` đã gắn) mà không hỏi,
  không sao lưu bản cũ, không in cảnh báo. Tương tự `target["reel"] = {...}` ghi đè
  reel đã gắn trước đó. Với quy trình cron tự chạy sau mỗi bài đăng, một file
  `/tmp/bai-moi.json` ghi nhầm slug (vd. `loi-004` thay vì `loi-005`) sẽ **xóa bài
  đã đăng khỏi web** mà nhật ký chỉ ghi "Thay Lỗi #004".
- **Sửa đúng:** thêm cờ `--force-replace` (mặc định từ chối khi slug đã tồn tại,
  hoặc bắt buộc `--replace` tường minh); trước khi thay, ghi bản cũ ra
  `backup/lessons-<slug>-<timestamp>.json`.

#### H-10 — Deploy push full-tree: mọi file ngoài danh sách `FILES` bị xóa khỏi repo
- **Vị trí:** `deploy_github_pages.py:44–57` (`site_files`), dòng 128–135
  (tạo tree mới từ đúng `FILES` rồi commit).
- **Bằng chứng:** tree mới chỉ chứa `index.html`, `lessons.json`, `README.md`,
  `*/index.html`, `images/*`. File nào trên repo không nằm trong danh sách —
  vd. `CNAME` (nếu sau này gắn domain riêng), `.nojekyll`, file do Đông thêm tay
  trên GitHub — sẽ **biến mất sau lần deploy sau**. Đây là hệ quả có chủ đích của
  bài học sập web 16/10 (never push lẻ), nhưng phía ngược lại chưa được khóa:
  không có "danh sách file được phép tồn tại ngoài FILES" và không có cảnh báo.
- **Sửa đúng:** `site_files()` thêm `CNAME`, `.nojekyll`, `favicon.svg` nếu tồn tại;
  trước khi tạo tree, liệt kê file trên repo hiện tại và cảnh báo/bail nếu có file
  ngoài danh sách sẽ bị xóa.

---

### 1.3. Trung bình (18)

| # | Vấn đề | Vị trí / bằng chứng |
|---|--------|---------------------|
| M-01 | **Chế độ tối: FOUC + 3 chỗ màu chưa nhất quán.** Theme chỉ áp sau khi `SHARED_JS` cuối `<body>` chạy (dòng 286) → lần tải đầu ở dark mode sẽ **chớp nền sáng rồi mới tối**. `--navy-btn` **không** được override trong `[data-theme="dark"]` (dòng 64) nên `.btn-navy`, `.tab.on`, `.chip.on`, `th` vẫn là navy đậm `#173F5F` trên nền tối `#0E1B2A` — đọc được nhưng chìm, khác hẳn các thành phần dùng `--navy` (đã đổi sang `#8FC3E8`). `.remember` dùng `border:2px solid #F6AD55` cố định (dòng ~182), không theo biến. `input::placeholder` không được style → placeholder xám mặc định trên nền tối `#16283F` tương phản thấp. | CSS dòng 63–64; `SHARED_JS` dòng 286 |
| M-02 | **Nhiều tap target < 48 px** (chuẩn tự đặt: nút ≥ 48 px). `.dicts a` padding 6px 13px → cao ~40 px; `.chip` 8px 14px → ~45 px; `.viewtoggle button` 8px 15px → ~45 px; `.grade-retry` 8px 16px → ~45 px; link text `.meta a`, `.back`, link footer không có padding (vùng bấm ~26 px). `.btn`/`.opt`/`.listen` đã đạt 48 px. | CSS dòng 120, 123, 159, 188 |
| M-03 | **Ảnh không resize + không lazy + không kích thước → tốn băng thông và CLS.** Ảnh nguồn 1080×1080 được giữ nguyên kích thước, chỉ nén JPEG q85 (dòng 1252–1262: `im.save(..., quality=85)` — **không có `thumbnail`/`resize`**). Ảnh cuối trang bài (`.originimg`, `max-width:320px`) vẫn tải đủ ~60–97 KB/bức; không có `loading="lazy"`, không có `width`/`height` hay `aspect-ratio` → trình duyệt không giữ chỗ, nội dung nhảy khi ảnh về (CLS). | `generate_site.py:1252–1262`; CSS `.originimg` |
| M-04 | **CSS ~13 KB inline lặp lại trong cả 13 trang**, không cache được giữa các trang. Không có file CSS ngoài, không có `preload`. Mỗi lần chuyển bài tải lại toàn bộ CSS. | `CSS` dòng 62–252; `page_shell` dòng ~583 `<style>{CSS}</style>` |
| M-05 | **OG image sai cho trang lộ trình + trang chủ** (đều dùng `images/loi-001.jpg`, `render_index`/`render_path`); thiếu `og:image:width/height`, thiếu `<link rel="canonical">`. Chia sẻ lộ trình "Tiếng Anh đi làm" lên Facebook hiện ảnh bài borrow/lend — sai ngữ cảnh. | `render_index`, `render_path` dòng 991–1141 |
| M-06 | **Nav trang bài chỉ có "Bài trước", không có "Bài tiếp theo".** `render_lesson` tính `next_lesson` (dòng 1282) nhưng **không dùng** — `<nav class="pagenav">{prev_link}<span></span></nav>`; bài đầu tiên nav rỗng hoàn toàn (chỉ còn `<span></span>` trống). "Bài tiếp theo" chỉ tồn tại trong wizard (nút đáy + màn hình hoàn thành), không có ở dạng link tĩnh → tắt JS là mất đường đi tiếp. | `generate_site.py:1143`, `1270–1275`, `1282–1286` |
| M-07 | **`speak()` có thể đọc sai giọng + kẹt trạng thái.** `speechSynthesis.getVoices()` (dòng ~293) hay trả `[]` ở lần gọi đầu (voices load bất đồng bộ, cần `voiceschanged`) → `find(en-US)` ra `undefined`, đọc bằng giọng mặc định của máy (có thể là giọng khác / tiếng Việt). `speechSynthesis.cancel()` rồi `speak` ngay có thể làm `onend` không bắn → nút `.playing` kẹt cam. Không có TTS thì `alert()` chặn cả trang. | `SHARED_JS` dòng ~290–300 |
| M-08 | **`escapeHtml` chỉ escape `&` và `<`.** Đủ cho text node hiện tại, nhưng là hàm "tưởng an toàn": nếu sau này `explain` được đưa vào attribute thì `"` không được escape → lỗi chèn HTML. Nên escape đủ `& < > " '`. | `SHARED_JS` dòng ~328 |
| M-09 | **Kiểm tra "Vì sao ≤ 2 câu" sai với câu có viết tắt.** `update_site.py:69`: `why.rstrip(".").split(". ")` — "vd. ..." hoặc "U.S." tạo thêm phần tử → bài hợp lệ bị từ chối; ngược lại câu không có ". " mà dài 3 câu vẫn qua. | `update_site.py:69–70` |
| M-10 | **Rác trong `web/`:** `_tmp_v2_*.js` (5 file), `patch_wizard_1.py`, `patch_wizard_2.py`, `__pycache__/`, `shots/` (ảnh chụp kiểm chứng). Không được deploy nhưng nằm chung thư mục deploy, dễ nhầm là thành phần của site; `site_files()` không có allowlist thư mục nên một ngày nào đó có thể lọt vào cây push. | `ls web/` |
| M-11 | **Streak không nhất quán với "Đã nhớ".** Bỏ đánh dấu "Đã nhớ" (bấm lại `btn-done`, `LESSON_PAGE_JS` dòng ~730) chỉ xóa `sdsc-done-v2`, **không trừ streak**; streak chỉ tăng trong `markDone()` ở trang bài, không có đường nào giảm. Người học có thể có streak 5 ngày trong khi `sdsc-done-v2` trống. | `LESSON_PAGE_JS`; `SHARED_JS` dòng 282 |
| M-12 | **Quiz gộp trong bài Lỗi không có hộp đáp án hiện sau khi chọn.** `#answer-box` chỉ tồn tại ở bước 1 của bài type `Quiz` (`lesson_steps` dòng 516–535). Bài Lỗi #004 gộp quiz (`quiz` trong bản ghi Lỗi) nhúng `quiz_block` ở bước Luyện nhưng không có `answer-box` → `gradeWidget` gọi `getElementById("answer-box")` trả `null` (đã guard `if(reveal)` nên không crash, nhưng quiz gộp mất hẳn phần "hộp đáp án" mà quiz độc lập có). Ngoài ra: Quiz không có `practice` sẽ chỉ còn **3 bước** thay vì 4 bước theo khuôn CAP-NHAT-SITE (bước "Luyện thêm" là có điều kiện). | `lesson_steps` dòng 516–555 |
| M-13 | **Tab không đi được bằng nút Back.** `showTab` dùng `history.replaceState` (dòng ~663) đổi hash `#tra-cuu` nhưng **thay** entry thay vì `pushState` → bấm Back không quay về tab Học. | `HOMEPAGE_JS` dòng ~660–665 |
| M-14 | **Tìm kiếm không bao gồm ví dụ / "Nhớ điều này" / IPA.** `data-search` chỉ gồm `code + title + wrong + right + why + topic` (dòng 924–927, 951–954). Tìm từ chỉ xuất hiện trong ví dụ (vd. "laptop" ở Lỗi #001) hoặc trong câu "Nhớ điều này" thì **không ra kết quả** dù bài đó chứa từ đó. | `card_html`, `table_row_html` |
| M-15 | **Tìm kiếm không chuẩn hóa dấu tiếng Việt.** `norm()` chỉ `.toLowerCase()` (dòng 678). Gõ "muon" không tìm ra "mượn"; gõ "phat am" không ra "phát âm". Người học gõ không dấu (phổ biến trên mobile) sẽ tưởng là không có bài. | `INDEX_FILTER_JS` dòng 676–680 |
| M-16 | **Không có fallback khi tắt JS.** Wizard ẩn các bước sau bằng thuộc tính `hidden` (`lesson_body` dòng ~560); tab Tra cứu mặc định `display:none` (`render_index`); toàn bộ grading/theme/streak đều là JS. Tắt JS → trang bài chỉ đọc được bước 1, không đổi tab, không tìm kiếm. Cần `<noscript>` + CSS fallback hiện tất cả bước. | `lesson_body`, `render_index` |
| M-17 | **`render_path` đếm cả slug chết.** Tiêu đề "N bài" dùng `len(path['order'])` nhưng vòng lặp bỏ qua slug không có trong `by_slug` (`if not l: continue`) → có thể hiện "7 bài" mà chỉ liệt kê 6. Cùng họ với S-03. | `render_path` dòng 1095–1125 |
| M-18 | **`renderReview` nuốt lặng giá trị ngày hỏng.** `new Date(date+"T00:00:00")` với `date` không phải `YYYY-MM-DD` (vd. dữ liệu cũ từng lưu `true`) → `Invalid Date` → `diff=NaN` → bị loại khỏi "Ôn hôm nay" mà không báo gì. | `HOMEPAGE_JS` dòng ~645–655 |

### 1.4. Thấp (13)

| # | Vấn đề | Vị trí / bằng chứng |
|---|--------|---------------------|
| L-01 | **CSS chết:** `.heroimg`, `.opening`, `.actions` được định nghĩa nhưng **không class nào được sinh ra** (grep 0 lần dùng). `.actions` chỉ xuất hiện qua `complete-actions`. | CSS dòng ~165, ~200, ~215 |
| L-02 | **Biến chết:** `n_reels` trong `render_index` (dòng 995) tính rồi không dùng; `i` trong `for i, p in enumerate(paths)` không dùng; tham số `next_lesson` của `render_lesson` (xem M-06). | Dòng 995, 1005, 1143 |
| L-03 | **Link tuyệt đối theo `BASE_PATH=/sai-dau-sua-do`** (dòng 27): mở `index.html` bằng `file://` hoặc preview local thì mọi link nội bộ + ảnh đều hỏng. Không có chế độ preview local. | Dòng 27 |
| L-04 | **Không có sitemap.xml / robots.txt.** Site 13 trang, Google chỉ khám phá qua link nội bộ. | `ls web/` |
| L-05 | **Canvas chia sẻ vẽ font chưa load** (xem H-06); `wrapText` không xử lý từ dài hơn `maxW` (từ đơn dài sẽ tràn khung trắng 900 px); `toBlob` không kiểm tra `b === null`. | `LESSON_PAGE_JS` `drawShare` |
| L-06 | **`gradeWidget` với `data-answer` thiếu:** `parseInt → NaN` → không đáp án nào được tô đúng, `String.fromCharCode(65+NaN)` ra ký tự `\0`. | `SHARED_JS` dòng ~313 |
| L-07 | **`updateStreak` tính "hôm qua" bằng `Date.now()-86400000`.** Đúng ở VN (không DST) nhưng là cách tính giòn; nên trừ ngày trên đối tượng Date local. | Dòng 282 |
| L-08 | **Không có `aria-selected`/`role="tab"` trên 2 tab; ô tìm kiếm không có `<label>`.** Trợ năng: screen reader không biết tab nào đang mở. | `render_index` |
| L-09 | **`og_description` cắt đúng 220 ký tự giữa chừng từ.** Hiển thị mô tả chia sẻ cụt câu. | Dòng ~571 |
| L-10 | **Deploy không kiểm tra file tồn tại trước khi upload blob** → `FileNotFoundError` traceback giữa chừng (blob đã tạo trước đó thành rác trên repo). | `deploy_github_pages.py:115–125` |
| L-11 | **`showTab` ghi đè hash `#on-homnay`.** Link "Ôn hôm nay ↓" (khi đã học hết) trỏ `#on-homnay`, nhưng `showTab("hoc")` lúc tải trang chạy `replaceState(null,"","#")` → anchor có thể bị xóa trước khi trình duyệt cuộn tới. | `HOMEPAGE_JS` |
| L-12 | **Trong `update_site.py`, `new.pop("paths", [])` và `pop("attach_to")` đột biến dict đầu vào** trước khi `json.dumps` ghi log — không ảnh hưởng file đã ghi (vì pop xong mới `setdefault` + ghi), nhưng gây khó đọc/khó test. | `update_site.py:80–95` |
| L-13 | **`loadJSON` nuốt lỗi JSON hỏng và trả `{}`** (dòng 277): một lần ghi dở (tắt tab giữa chừng) làm **mất toàn bộ tiến độ đã lưu mà không báo** — xem thêm §1.5(f). | Dòng 277 |

---

### 1.5. Điểm yếu của cơ chế lưu tiến độ hiện tại (mục f)

Hiện có 4 key riêng lẻ, không có versioning thật, không backup, không đồng bộ:

| Key | Nội dung | Vấn đề |
|-----|----------|--------|
| `sdsc-done-v2` | `{slug: "YYYY-MM-DD"}` | (1) Không có trường version trong dữ liệu — hậu tố `-v2` chỉ nằm ở **tên key**, nghĩa là muốn đổi schema phải đổi tên key → **dữ liệu cũ bị bỏ rơi lặng lẽ**, không migrate. (2) Giá trị chỉ là ngày: không biết người học tự đánh giá hiểu mức nào, đã ôn mấy lần, lần ôn tới khi nào → **không làm được SRS** với dữ liệu hiện tại. (3) `Object.values(done).includes(todayISO())` dùng làm "đã học hôm nay" — một slug lạ với date hôm nay cũng tính là đã học. |
| `sdsc-practice-v2` | `{key: boolean}` | Chỉ lưu đúng/sai (xem H-02); không lưu lựa chọn, không lưu thời gian, không phân biệt lần làm đầu và làm lại; `delete` khi "Làm lại" xóa luôn lịch sử. Key dạng `slug:index` — đổi thứ tự câu practice trong `lessons.json` là **đảo lộn toàn bộ lịch sử** (câu 0 cũ thành câu 0 mới). |
| `sdsc-streak-v1` | `{streak, last}` | Không có lịch sử ngày học → không kiểm chứng được chuỗi, không sửa được ngày bị sót (ốm/nghỉ); bỏ đánh dấu không trừ (M-11); tính "hôm qua" bằng trừ mili-giây (L-07). |
| `sdsc-theme` | `"light"/"dark"` | Không có vấn đề lớn; nhưng đọc không có `try/catch` (S-01) và là key duy nhất **không** có hậu tố version — nếu sau này đổi giá trị (vd. thêm `"auto"`) sẽ không có đường migrate. |

**Các điểm yếu hệ thống:**
1. **Không có backup:** một `JSON.parse` hỏng (L-13) hoặc `QuotaExceededError` → mất toàn bộ, không có bản sao nào để khôi phục. Không có export (người học không tự cứu được dữ liệu).
2. **Không migrate được:** không có code đọc key cũ khi key mới ra đời; không có trường `version` trong payload; không có hàm `migrate()`.
3. **Đổi máy / xóa dữ liệu trình duyệt = mất hết**, đã ghi rõ trên trang chủ ("Tiến độ lưu trên trình duyệt này, đổi máy sẽ mất") — chấp nhận được với người học, nhưng không có đường xuất/nhập để khắc phục.
4. **Không có đồng bộ chéo tab:** hai tab cùng mở → tab nào ghi sau thắng, tab kia không biết (không dùng sự kiện `storage`).
5. **Không validate khi đọc:** mọi hàm đọc đều tin tưởng tuyệt đối dữ liệu trong storage (vd. `done[SLUG]` có thể là số, object, chuỗi rác — `renderDone` chỉ kiểm tra truthy).
6. **Không có giới hạn kích thước / dọn dẹp:** `history` không tồn tại nên chưa phình, nhưng khi thêm SRS + history (xem §2) mà không cắt ngắn sẽ chạm quota.
7. **Dữ liệu và code cùng version bằng "niềm tin":** `sdsc-done-v2` được sinh bởi generator bản wizard, nhưng không có gì ngăn một bản site cũ (cache) ghi đè dữ liệu của bản mới.

---

### 1.6. Ba vấn đề kỹ thuật nghiêm trọng nhất (tóm tắt)

1. **S-01 + S-02 — `localStorage` không được bảo vệ làm sập toàn bộ tương tác.**
   Một `SecurityError`/`QuotaExceededError` (private mode, storage bị chặn, đầy quota)
   giết chết `SHARED_JS` — quiz, nút Nghe, đổi theme đều chết; riêng `gradeWidget`
   còn khóa đáp án mà không hiện kết quả. Đây là single point of failure chạm tới
   **mọi trang, mọi người học**. Sửa: bọc **mọi** lần chạm `localStorage`/`sessionStorage`
   trong `try/catch` + đổi thứ tự "hiện kết quả trước, ghi sau".
2. **S-04 — "Hoàn tác" gần như chắc chắn không chạy** (`force=False` khi lùi ref là
   non-fast-forward → GitHub trả 422). Đây là đường cứu hộ duy nhất Đông đã chốt
   ("Đông nhắn 'hoàn tác' thì chạy `undo_deploy.py`"); khi cần dùng thật mới phát hiện
   hỏng thì đã muộn. Cần kiểm chứng trên repo thử và sửa thành `force=True` (kèm xác
   nhận) + cập nhật log sau khi lùi.
3. **S-05 + S-03 — Deploy đẩy README sai sự thật; một slug lạ trong lộ trình làm sập khối động lực trang chủ.**
   S-05: mọi lần deploy ghi đè README đúng bằng bản cũ sai ("12 bài", "file duy nhất").
   S-03: `renderToday` thiếu guard mà `renderProgress`/`renderReview` đã có, nên một
   slug chết sẽ kéo sập cả "Ôn hôm nay" + chuỗi học. Cả hai đều là lỗi "đúng một dòng",
   sửa rẻ, nhưng hậu quả âm thầm và kéo dài.

---

## 2. Thiết kế (không code — chỉ đặc tả để triển khai sau)

### 2.1. Schema tiến độ có version — key mới `sdsc-progress-v1`

**Nguyên tắc:**
- **Một key duy nhất** cho toàn bộ tiến độ: `sdsc-progress-v1`. Các key cũ
  (`sdsc-done-v2`, `sdsc-practice-v2`, `sdsc-streak-v1`) chỉ còn là **nguồn migrate**,
  không ghi mới nữa. `sdsc-theme` giữ nguyên key riêng (không thuộc tiến độ học).
- Mọi lần ghi đều qua **một hàm duy nhất** `saveProgress()` có `try/catch` +
  ghi **bản sao dự phòng** `sdsc-progress-v1.bak` (ghi luân phiên: ghi `.bak` trước,
  ghi chính sau; khi đọc chính hỏng thì đọc `.bak`).
- Payload luôn có `version: 1` và `updatedAt` (ISO datetime). Đọc: parse trong
  `try/catch` → sai version → chạy `migrate()` → vẫn sai → trả về progress rỗng
  **và giữ lại bản hỏng** ở key `sdsc-progress-v1.corrupt.<timestamp>` để cứu hộ,
  không xóa lặng lẽ.
- Giới hạn kích thước: `history` cắt tối đa **500 sự kiện** (giữ mới nhất);
  `practice` cắt tối đa **1.000 khóa** (giữ mới nhất theo `lastAt`).

```jsonc
{
  "version": 1,
  "updatedAt": "2026-11-15T08:30:00+07:00",   // lần ghi cuối (ISO 8601, có múi giờ)
  "lessons": {
    "loi-001": {
      "done": true,                            // đã bấm "Tôi đã nhớ bài này"
      "doneAt": "2026-11-14",                  // YYYY-MM-DD, ngày đánh dấu đầu tiên
      "lastStudiedAt": "2026-11-15",           // YYYY-MM-DD, lần học/ôn gần nhất
      "selfGrade": "de",                       // "kho" | "vua" | "de" | null — tự đánh giá lần gần nhất
      "reviews": 2                             // số lần ôn lại sau khi done
    }
  },
  "practice": {
    "loi-001:0": { "choice": 1, "correct": true, "attempts": 2, "lastAt": "2026-11-15T08:31:00+07:00" },
    "loi-001:q": { "choice": 0, "correct": false, "attempts": 1, "lastAt": "2026-11-14T20:02:00+07:00" }
  },
  "streak": { "count": 5, "lastDate": "2026-11-15", "dates": ["2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15"] },
  "review": {
    "loi-001": { "interval": 3, "nextDue": "2026-11-18", "ease": 2.5, "reps": 1 }
  },
  "history": [
    { "date": "2026-11-15", "at": "2026-11-15T08:30:00+07:00", "slug": "loi-001", "action": "done", "grade": "de" },
    { "date": "2026-11-15", "at": "2026-11-15T08:31:00+07:00", "slug": "loi-001", "action": "practice", "key": "loi-001:0", "correct": true }
  ],
  "settings": { "dailyGoal": 1, "remindReview": true }
}
```

**Chú thích trường:**
- `lessons[slug].selfGrade`: mức hiểu do người học tự chọn ở màn hình hoàn thành
  (3 mức, xem §2.2). `null` = chưa đánh giá (tương thích bài done trước khi có tính năng).
- `practice` key giữ dạng `slug:index` / `slug:q` như cũ để migrate 1–1,
  nhưng giá trị cũ là boolean → xem quy tắc migrate.
- `streak.dates`: tối đa **30 ngày gần nhất** (đủ để vẽ và để kiểm chứng chuỗi;
  ngày cũ hơn được cắt nhưng `count` vẫn giữ).
- `history[].action`: một trong `done` | `undone` | `practice` | `review` |
  `self-grade` | `import` | `reset`. `grade` chỉ có với `done`/`review`/`self-grade`.
- `settings.dailyGoal`: mặc định 1 (mục tiêu hiện tại); `remindReview`: có hiện
  khung "Ôn hôm nay" không.

**Quy tắc migrate từ key cũ (chạy 1 lần khi đọc thấy `version` vắng mặt / key mới chưa có):**
1. Đọc `sdsc-done-v2` (try/catch; hỏng → bỏ qua, ghi log vào `history` action `import` với `note: "done corrupt"`).
   Mỗi `slug: date` (date hợp lệ `YYYY-MM-DD`) → `lessons[slug] = {done: true,
   doneAt: date, lastStudiedAt: date, selfGrade: null, reviews: 0}`.
   Slug **không tồn tại** trong `lessons.json` hiện tại → vẫn giữ lại trong
   `lessons` kèm cờ `orphan: true` (đừng xóa: bài có thể quay lại; UI ẩn orphan).
   Giá trị không phải date hợp lệ → bỏ qua entry đó.
2. Đọc `sdsc-practice-v2`. Mỗi `key: boolean` → `practice[key] = {choice: null,
   correct: boolean, attempts: 1, lastAt: null}` (`choice: null` = "không biết đã
   chọn gì" — trung thực với dữ liệu cũ, xem H-02; UI hiển thị "đã làm trước đây"
   thay vì tô sai lựa chọn).
3. Đọc `sdsc-streak-v1` → `streak = {count, lastDate: last, dates: [last]}` nếu
   `last` hợp lệ; `count` không hợp lệ → tính lại `count = dates.length`.
   Sau đó **đối chiếu với `lessons`**: nếu `lastDate` không có trong bất kỳ
   `doneAt`/`lastStudiedAt` nào thì giữ nguyên (tin streak cũ), nhưng ghi
   `history` action `import` với `note: "streak unverified"`.
4. Tính `review` lần đầu cho mỗi bài `done`: `interval = 1`, `nextDue = doneAt + 1 ngày`,
   `ease = 2.5`, `reps = 0` (xem §2.2 — bài cũ bắt đầu lại từ nấc 1, an toàn hơn là
   đoán mức nhớ).
5. Ghi `sdsc-progress-v1` mới + `history` 1 entry `{action: "import",
   note: "migrated from sdsc-done-v2/sdsc-practice-v2/sdsc-streak-v1"}`.
6. **Không xóa key cũ ngay.** Giữ nguyên 30 ngày làm bằng chứng; sau 30 ngày
   (hoặc khi người học bấm "Xóa dữ liệu cũ"), xóa bằng hàm dọn dẹp riêng.
7. Nếu key mới **đã tồn tại** nhưng `version < 1` (tương lai có v2): migrate theo
   bảng `MIGRATIONS[version]` từng bước (v1→v2, v2→v3…), không nhảy cóc; mỗi bước
   ghi `history` action `migrate`.

**Quy tắc ghi:**
- Mọi thay đổi đi qua `updateProgress(mutator)` — đọc → mutate trên bản sao →
  validate nhanh (slug tồn tại hoặc `orphan`) → ghi `.bak` → ghi chính →
  cập nhật `updatedAt`. Lỗi ở bất kỳ bước nào → giữ bản cũ, báo lỗi cho người học
  (không lặng lẽ mất).
- Nghe sự kiện `storage` để đồng bộ chéo tab: tab nhận được `sdsc-progress-v1`
  thay đổi thì render lại tiến độ (không ghi đè).

### 2.2. Thuật toán ôn tập lặp lại ngắt quãng (SRS) — chạy hoàn toàn phía client

**Mục tiêu:** thay khung "Ôn hôm nay" cố định 2–7 ngày bằng lịch ôn cá nhân hóa theo
mức nhớ thật. Không máy chủ, không tài khoản; mọi tính toán bằng Date local.

**Thời điểm hỏi tự đánh giá:** ở màn hình hoàn thành của mỗi bài (sau khi bấm
"Tôi đã nhớ bài này") và ở cuối mỗi lần ôn lại: hiện 3 nút —
**😟 Khó** (không nhớ / sai nhiều), **🙂 Vừa** (nhớ sau khi ngập ngừng),
**😄 Dễ** (nhớ ngay). Nếu người học bỏ qua (không chọn) → mặc định là **Vừa**,
nhưng ghi `selfGrade: null` để phân biệt "không đánh giá" với "đánh giá Vừa".

**Trạng thái mỗi bài** (lưu ở `review[slug]`): `interval` (số ngày tới lần ôn sau),
`nextDue` (`YYYY-MM-DD`), `ease` (hệ số dễ, 1.3–2.5, khởi đầu 2.5), `reps`
(số lần ôn đúng liên tiếp).

**Công thức cập nhật** (áp dụng khi người học ôn xong 1 bài và chọn mức):

| Kết quả | Cập nhật |
|---|---|
| **Khó** (quên / sai) | `interval = 1`; `ease = max(1.3, ease − 0.2)`; `reps = 0`; `nextDue = hôm nay + 1 ngày` |
| **Vừa** (nhớ sau khi ngập ngừng) | `interval = max(1, round(interval × ease))`; `ease` giữ nguyên; `reps += 1`; `nextDue = hôm nay + interval` |
| **Dễ** (nhớ ngay) | `interval = max(1, round(interval × ease × 1.3))`; `ease = min(2.5, ease + 0.1)`; `reps += 1`; `nextDue = hôm nay + interval` |

- **Giới hạn:** `interval` tối đa **60 ngày** (trần). `interval` tối thiểu 1 ngày.
- **Bài mới done lần đầu:** `interval = 1`, `nextDue = ngày mai`, `ease = 2.5`, `reps = 0`
  (chưa tính là đã ôn).
- **Bài done trước khi có SRS (migrate):** như trên, `interval = 1`, `nextDue = doneAt + 1 ngày`
  (nếu ngày đó đã qua → đến hạn ngay, xếp đầu danh sách ôn).
- **Làm lại từ đầu:** nếu người học bỏ đánh dấu "Đã nhớ" (`undone`) → xóa `review[slug]`,
  giữ `lessons[slug]` với `done: false` (để lần done sau bắt đầu lại từ nấc 1).

**Ví dụ chạy tay (bài Lỗi #001, done 15/11, ease 2.5):**

| Ngày | Hành động | interval trước → sau | nextDue |
|---|---|---|---|
| 15/11 | Done lần đầu | — → 1 | 16/11 |
| 16/11 | Ôn, chọn **Dễ** | 1 → round(1×2.5×1.3)=3 | 19/11 |
| 19/11 | Ôn, chọn **Vừa** | 3 → round(3×2.5)=8 (ease đã 2.5) | 27/11 |
| 27/11 | Ôn, chọn **Khó** | 8 → 1, ease 2.5→2.3, reps 0 | 28/11 |
| 28/11 | Ôn, chọn **Vừa** | 1 → round(1×2.3)=2 | 30/11 |

**Hàng đợi "Ôn hôm nay":**
- Lấy mọi bài có `review.nextDue <= hôm nay`, sắp xếp: quá hạn nhiều ngày nhất trước,
  rồi `ease` thấp trước. Tối đa **5 bài** (giữ như hiện tại).
- Bài chưa đến hạn không hiện; thay dòng "Chưa có bài nào để ôn" bằng 2 trạng thái:
  "Hôm nay chưa có bài đến hạn — bài ôn gần nhất là X vào ngày Y" (tính từ `nextDue`
  nhỏ nhất trong tương lai).
- Khi người học ôn xong 1 bài trong danh sách: cập nhật SRS ngay (§ trên) → bài biến
  khỏi danh sách hôm nay; cập nhật `lessons[slug].reviews += 1`,
  `lastStudiedAt = hôm nay`, thêm `history` action `review`.
- **Bài quá hạn lâu** (> 30 ngày quá hạn): vẫn xếp đầu, nhưng khi ôn xong mà chọn
  Khó thì `interval = 1` như thường (không phạt thêm).

**Những gì KHÔNG làm (giữ đơn giản):** không dùng SM-2 đầy đủ (không có `quality 0–5`,
không có `lapses` riêng); không có "ôn trước hạn" (chỉ ôn bài đến hạn, tránh lạm dụng
nút ôn để đẩy interval); không thay đổi `ease` khi chỉ làm practice mà không ôn
(practice không phải là ôn — chỉ `review` qua màn hình hoàn thành mới cập nhật SRS).

### 2.3. Format xuất / nhập dữ liệu tiến độ

**Xuất (export):**
- Nút "Tải dữ liệu tiến độ của tôi (.json)" đặt ở cuối khối Tiến độ trang chủ
  (cạnh dòng "Tiến độ lưu trên trình duyệt này…").
- File: `sai-dau-sua-do-tien-do-YYYY-MM-DD.json` (ngày xuất, giờ VN).
- Tạo bằng `Blob` + `URL.createObjectURL` (giống `drawShare` đã có) — không cần server.
- Nội dung file = **nguyên văn object `sdsc-progress-v1`** (đã gồm `version`,
  `updatedAt`, `lessons`, `practice`, `streak`, `review`, `history`, `settings`),
  bọc thêm envelope để file tự mô tả:
  ```jsonc
  { "app": "sai-dau-sua-do", "kind": "progress-export", "version": 1,
    "exportedAt": "2026-11-15T08:30:00+07:00", "data": { /* sdsc-progress-v1 */ } }
  ```
- Trước khi xuất: validate nhanh (đúng schema §2.1) — nếu dữ liệu trong máy đang hỏng
  thì báo lỗi, không xuất file hỏng.

**Nhập (import):**
- Nút "Nhập dữ liệu đã lưu" + `<input type="file" accept=".json,application/json">`.
- Hai chế độ do người học chọn trước khi nhập: **(A) Gộp** (mặc định): giữ cả hai,
  xung đột thì bản nào `updatedAt`/`lastAt` mới hơn thì thắng (theo từng bài, từng
  khóa practice riêng lẻ). **(B) Ghi đè**: thay toàn bộ tiến độ hiện tại bằng file.
  Chế độ (B) bắt buộc hiện hộp xác nhận ghi rõ "sẽ xóa X bài đã nhớ, Y câu luyện,
  chuỗi Z ngày hiện tại".
- Đọc file bằng `FileReader` → `JSON.parse` trong `try/catch`.

**Các bước validate (theo đúng thứ tự này; bước nào sai thì DỪNG, báo lỗi cụ thể, KHÔNG ghi gì):**
1. **Đọc được JSON:** parse lỗi → `"File không phải JSON hợp lệ (lỗi ở ký tự N: …). Kiểm tra lại file đã tải về."` Không ghi.
2. **Đúng app/kind:** `app === "sai-dau-sua-do"` và `kind === "progress-export"` →
   sai thì `"Đây không phải file tiến độ của Sai Đâu Sửa Đó (thiếu app/kind đúng)."`.
3. **Version hỗ trợ:** `data.version` là số nguyên 1..`CURRENT_VERSION` (hiện là 1) →
   lớn hơn → `"File được xuất từ phiên bản mới hơn (vX), trang này mới hỗ trợ tới v1. Cập nhật trang rồi nhập lại."`;
   nhỏ hơn → chạy `migrate()` từng bước (xem §2.1 bước 7); migrate thất bại →
   `"Không chuyển đổi được dữ liệu cũ (vX): …"`.
4. **Kiểu gốc:** `data` là object; `lessons`/`practice`/`review` (nếu có) là object;
   `history` (nếu có) là array; `streak` (nếu có) là object → sai kiểu →
   `"Trường 'lessons' phải là object, nhận được array."` (nêu đúng tên trường + kiểu nhận được).
5. **Slug phải tồn tại:** mọi slug trong `lessons`/`review` phải có trong `lessons.json`
   hiện tại, **trừ** slug được chấp nhận là `orphan` (giữ lại kèm cờ, không báo lỗi).
   Slug lạ hoàn toàn (không trong lessons.json, không phải dạng slug hợp lệ) →
   `"Bài 'loi-999' trong file không có trên trang — có thể file thuộc bản web khác."`
   (báo tối đa 5 slug đầu).
6. **Ngày hợp lệ:** mọi `doneAt`/`lastStudiedAt`/`nextDue`/`lastDate` phải khớp
   `YYYY-MM-DD` **và là ngày có thật trên lịch** (vd. `2026-02-30` là sai) và không
   ở tương lai quá 1 ngày (cho phép lệch múi giờ 1 ngày) → sai thì
   `"Ngày '2026-02-30' ở bài loi-001 không phải ngày hợp lệ."`.
7. **Miền giá trị:** `selfGrade ∈ {kho, vua, de, null}`; `interval` nguyên 1–60;
   `ease` số 1.3–2.5; `reps` nguyên ≥ 0; `practice[].attempts` nguyên ≥ 1;
   `streak.count` nguyên ≥ 0; `history[].action` thuộc enum → sai thì
   `"Bài loi-001: interval phải từ 1 tới 60, nhận được 90."`.
8. **Nhất quán nội bộ:** `review[slug]` chỉ tồn tại khi `lessons[slug].done === true`
   (trừ orphan); `nextDue` phải ≥ `doneAt`; `streak.lastDate` phải là ngày cuối
   trong `streak.dates` (nếu `dates` không rỗng) → sai thì
   `"Bài loi-001 có lịch ôn nhưng chưa được đánh dấu đã nhớ."`.
9. **Giới hạn kích thước:** file > 1 MB hoặc `history` > 5.000 entry → từ chối:
   `"File quá lớn (> 1 MB) — có thể không phải file tiến độ."` (chống file rác).
- **Sau khi validate xong:** áp dụng theo chế độ (A)/(B) → ghi `sdsc-progress-v1`
  (qua `updateProgress`) → thêm `history` action `import` (ghi rõ chế độ + số bài
  gộp/ghi đè) → render lại toàn bộ tiến độ → báo thành công:
  `"Đã nhập: 9 bài đã nhớ, 27 câu luyện, chuỗi 5 ngày (chế độ Gộp)."`.
- **Không bao giờ:** ghi đè dữ liệu cũ khi validate chưa xong; nhập một phần
  (hoặc nhập hết, hoặc không nhập gì — atomic).

### 2.4. Thiết kế tìm kiếm + bộ lọc

**Hiện trạng:** tìm theo chuỗi con trên `data-search` đã lower-case (gồm code, title,
wrong, right, why, topic), lọc chip topic/type hardcode, không chuẩn hóa dấu,
không lọc theo lộ trình/trạng thái, điểm tìm kiếm không xếp hạng.

**Thiết kế mới:**

**a) Index — những trường nào của `lessons.json` cần index (sinh lúc generate, nhúng 1 lần):**
| Nhóm | Trường | Trọng số |
|---|---|---|
| Nhận dạng | `code` ("Lỗi #001"), `slug` | cao nhất — gõ "loi 001" / "001" phải ra ngay |
| Tiêu đề | `title` | cao |
| Nội dung chính | `wrong`, `right`, `remember`, `why` | cao |
| Ví dụ | `examples[].en`, `examples[].vi` | trung bình |
| Phát âm | `ipa[].text`, từ rút ra từ IPA (vd. "comfortable") | trung bình |
| Quiz/luyện | `quiz.question`, `quiz.prompt`, `quiz.options`, `practice[].prompt`, `practice[].options` | trung bình |
| Phân loại | `topic`, `type`, `date`, `paths` (lộ trình chứa bài) | dùng lọc, không dùng tìm tự do |
| Từ điển | `dict_links[].label` | thấp |

- Mỗi bài sinh **một chuỗi tìm kiếm đã chuẩn hóa** (xem (b)) từ các trường trên,
  lưu ở `data-search` như hiện tại nhưng đầy đủ hơn; đồng thời lưu **mảng token**
  trong JS (`SDSC_SEARCH_INDEX`) để xếp hạng.
- `lessons.json` vẫn được đẩy lên cùng site — có thể tìm ngay trên dữ liệu gốc
  nếu cần, không cần API.

**b) Chuẩn hóa truy vấn:**
1. Lowercase; 2. Bỏ dấu tiếng Việt (NFD + loại bỏ combining marks: "mượn"→"muon",
   "phát âm"→"phat am"); 3. Bỏ ký tự đặc biệt, giữ chữ/số/khoảng trắng; 4. Tách token
   theo khoảng trắng; 5. Bỏ stopword tiếng Việt ngắn ("của", "là", "và", "cái") trừ
   khi truy vấn chỉ có 1 token.
- Tìm **không dấu** và **có dấu** đều ra (chuẩn hóa cả hai phía). Gõ "borrow",
  "muon", "mượn" đều tìm ra Lỗi #001.

**c) Xếp hạng kết quả:** tính điểm mỗi bài = tổng điểm token khớp:
- token khớp ở `code`/`title`: +10; `wrong`/`right`: +6; `remember`/`why`: +4;
  `examples`/`quiz`/`practice`: +2; `topic`: +3.
- Khớp **từ đầu chuỗi** (prefix) được ×2 ("bor" khớp "borrow").
- Sắp xếp theo điểm giảm dần, hòa thì bài mới hơn trước. Hiển thị tối đa 50 bài,
  kèm dòng "Tìm thấy N bài cho '…'".
- Không có truy vấn → giữ thứ tự mặc định (ngày đăng).

**d) Bộ lọc (kết hợp được với nhau, AND):**
- **Chủ đề:** chip sinh **từ dữ liệu** (mọi `topic` phân biệt trong `lessons.json`,
  kèm đếm số bài) — sửa H-03; thêm "Tất cả".
- **Loại:** Lỗi / Mẫu câu / Quiz (sinh từ dữ liệu; `Reels` chỉ hiện khi reel được
  bật riêng).
- **Lộ trình:** dropdown/chip "Thuộc lộ trình: Tất cả / Học lại từ đầu / Tiếng Anh
  đi làm / Sửa phát âm" — dùng trường `paths` của bài (cần `lessons.json` ghi
  `paths` cho mọi bài; hiện tại `paths` chỉ nằm ở `site.paths[].order` → lúc
  generate đảo ngược thành `paths` mỗi bài).
- **Trạng thái học:** Tất cả / Chưa học / Đã nhớ / Đến hạn ôn (dựa vào
  `sdsc-progress-v1`: `done` và `review.nextDue <= hôm nay`).
- **Sắp xếp:** Mới nhất / Cũ nhất / A–Z theo tên bài.
- Trạng thái lọc + truy vấn được **đồng bộ lên URL** (`?q=borrow&topic=giao-tiep&path=sua-phat-am`)
  bằng `history.replaceState` để chia sẻ link kết quả tìm kiếm; lúc tải trang đọc
  URL để khôi phục.
- Hiệu năng: `input` debounce **150 ms**; lọc trên mảng ≤ vài trăm bài là tức thì;
  không cần Web Worker ở quy mô này (ghi chú: nếu > 1.000 bài thì chuyển index sang
  Worker).

### 2.5. Danh sách kiểm thử cần có (test script chạy bằng node/python)

**Khung:** 1 file `web/tests/test_site.py` (Python, dùng `unittest`, chạy
`python3 -m unittest tests.test_site`) cho phần sinh trang + schema; 1 file
`web/tests/test_browser.mjs` (Node, dùng `node:test` + `jsdom` tối thiểu, hoặc
chạy bằng `node --test`) cho JS phía client. **Không cần trình duyệt thật** cho
phần lớn test (logic thuần). Test trình duyệt thật (mobile 390 px, dark, TTS)
nằm ở checklist tay cuối mục.

**Quy ước:** mỗi test ghi `input → expected`. Test nào FAIL thì in rõ input,
expected, actual.

**Nhóm A — Sinh trang (Python, đọc `lessons.json` + `generate_site.py`):**
| # | Test | Input → Expected |
|---|---|---|
| A1 | Mọi bài visible đều có trang | `lessons.json` (9 visible) → 9 thư mục `*/index.html` tồn tại |
| A2 | Không còn trang cũ sau khi gỡ bài | Xóa `loi-002` khỏi data → chạy `main()` → `loi-002/index.html` không tồn tại, `lo-trinh/*` không nhắc tới nó |
| A3 | Số bước wizard đúng khuôn | Lỗi/Mẫu câu → 6 `.wstep`; Quiz → 4 `.wstep`; `data-action="done"` đúng 1 |
| A4 | Không lặp câu trong trang bài | Text hiển thị mỗi trang bài → mọi câu ≥ 4 từ xuất hiện ≤ 1 lần |
| A5 | Mọi ảnh tồn tại + là JPEG | Mỗi `image_src` → file `images/<slug>.jpg` tồn tại, header JPEG, kích thước ≤ 200 KB |
| A6 | `lessons.json` hợp lệ | Schema §2.1 (đủ trường, `answer` trong khoảng, `practice ≥ 2`, `why ≤ 2 câu`) → không lỗi |
| A7 | OG tags đủ | Mỗi trang bài → có `og:title`, `og:description` (≤ 220 ký tự), `og:url`, `og:image` trỏ đúng `images/<slug>.jpg` |
| A8 | Không có link chết nội bộ | Mọi `href="/sai-dau-sua-do/..."` trong HTML đã sinh → file tương ứng tồn tại trên đĩa |
| A9 | CSS không có font-size < 16 px | Quét `CSS` → mọi `font-size` ≥ 16 px |
| A10 | Mọi nút <a>/<button> có href/handler | Quét HTML → không có `href="#"`, `href=""`, `onclick=""` |
| A11 | `README.md` sinh ra đúng số liệu | `render_readme` → chứa "9 bài học", "3 lộ trình", "2 Reel" |
| A12 | Deploy không ghi đè README đã sinh | Chạy `site_files()` + logic đọc file → nội dung README trong tree bằng file trên đĩa (bắt S-05) |

**Nhóm B — Chấm điểm + wizard (Node, jsdom, nạp `SHARED_JS` + `LESSON_PAGE_JS`):**
| # | Test | Input → Expected |
|---|---|---|
| B1 | Chọn đúng | `gradeWidget(box, answer)` → `.grade-result` hiện, class `good`, text chứa "Đúng rồi", nút đúng có class `correct` |
| B2 | Chọn sai | Chọn sai → class `bad`, text chứa "Chưa đúng — đáp án là B", nút đã chọn có `wrong-pick`, nút đúng vẫn `correct` |
| B3 | Đáp án quiz chỉ hiện sau khi chọn | Trước khi chọn → `#answer-box` `display:none`; sau khi chọn → `display:block` |
| B4 | Làm lại | Sau khi chọn → bấm `.grade-retry` → các `.opt` hết `disabled`, `.grade-result` ẩn, storage không còn key đó |
| B5 | Khôi phục sau tải lại | Storage có `{key: {choice:0, correct:false}}` → tải lại → nút đúng tô xanh, nút đã chọn tô đỏ, result hiện "Bạn đã làm, đáp án là …" |
| B6 | Điểm theo bài, không theo site | Làm đúng 3/3 câu ở loi-001, chưa làm bài khác → trang loi-001 hiện "3 / 3", trang chủ hiện "3 / 27" (bắt H-01) |
| B7 | localStorage bị chặn không giết trang | `localStorage.getItem/setItem` ném `SecurityError` → `SHARED_JS` vẫn gắn đủ handler, quiz vẫn chấm được (bộ nhớ tạm), theme toggle vẫn đổi class (bắt S-01) |
| B8 | Đầy quota khi chấm | `setItem` ném `QuotaExceededError` sau khi disable nút → `.grade-result` **vẫn hiện** (bắt S-02) |
| B9 | Wizard đi/quay lại | `showStep(0)` → "Bước 1/6", `#wizPrev` ẩn; `showStep(5)` → nút Next ghi "Bài tiếp theo →"; bấm Next ở bước cuối → `location.href` = bài tiếp theo theo lộ trình |
| B10 | Bước "Đã nhớ" | Ở bước `data-action="done"`, bấm Next → `done[slug]` được ghi + streak tăng + chuyển bước sau; bấm lại nút `btn-done` → xóa dấu, streak **không** tăng thêm |
| B11 | Slug lạ trong lộ trình không sập trang chủ | `SDSC_PATHS["hoc-lai-tu-dau"] = ["loi-999", "loi-001"]`, `SDSC_LESSONS` không có `loi-999` → `renderToday()` không ném, `renderReview()` + `renderStreak()` vẫn chạy (bắt S-03) |
| B12 | Theme toggle | Bấm `#theme-toggle` ở light → `documentElement.dataset.theme === "dark"`, `localStorage["sdsc-theme"] === "dark"`, icon đổi sang mặt trời; bấm lại → về light |
| B13 | Theme theo hệ thống | Không có `sdsc-theme`, `matchMedia("(prefers-color-scheme: dark)")` = true → theme ban đầu là `dark` (không chớp sáng — kiểm tra `data-theme` được set trước khi `body` render nếu chuyển script lên `<head>`) |

**Nhóm C — Tiến độ + SRS (Node, logic thuần, không cần DOM):**
| # | Test | Input → Expected |
|---|---|---|
| C1 | Migrate done cũ | `sdsc-done-v2 = {loi-001: "2026-11-14"}` → migrate → `lessons["loi-001"].done === true`, `doneAt === "2026-11-14"`, `review["loi-001"].interval === 1`, `nextDue === "2026-11-15"` |
| C2 | Migrate practice cũ | `sdsc-practice-v2 = {"loi-001:0": true}` → `practice["loi-001:0"] = {choice: null, correct: true, attempts: 1}` |
| C3 | Migrate streak cũ | `sdsc-streak-v1 = {streak: 5, last: "2026-11-15"}` → `streak.count === 5`, `lastDate === "2026-11-15"` |
| C4 | Migrate bỏ qua rác | `sdsc-done-v2 = {loi-001: "not-a-date", "loi-999": "2026-11-14"}` → `loi-001` bị bỏ qua, `loi-999` giữ lại với `orphan: true` |
| C5 | SRS — Dễ | `{interval:1, ease:2.5, reps:0}` + grade `de` → `{interval:3, ease:2.5, reps:1}`, `nextDue = hôm nay + 3` |
| C6 | SRS — Vừa | `{interval:3, ease:2.5, reps:1}` + `vua` → `{interval:8, ease:2.5, reps:2}` (round(3×2.5)=8) |
| C7 | SRS — Khó | `{interval:8, ease:2.5, reps:2}` + `kho` → `{interval:1, ease:2.3, reps:0}` |
| C8 | SRS — trần 60 ngày | `{interval:50, ease:2.5}` + `de` → `interval === 60` (không vượt trần) |
| C9 | SRS — ease sàn 1.3 | `{interval:5, ease:1.4}` + `kho` → `ease === 1.3` (không dưới sàn) |
| C10 | Hàng đợi ôn | 3 bài `nextDue` = hôm qua / hôm nay / ngày mai → "Ôn hôm nay" chứa đúng 2 bài, quá hạn nhất đứng đầu |
| C11 | Streak +1 / giữ / reset | `last = hôm qua` + học hôm nay → `count+1`; `last = hôm nay` → không đổi; `last = 3 hôm trước` → `count = 1` |
| C12 | Đọc JSON hỏng dùng bản sao | `sdsc-progress-v1` hỏng + `.bak` tốt → đọc được từ `.bak`, bản hỏng được giữ ở key `.corrupt.<timestamp>` |
| C13 | Đồng bộ chéo tab | Tab A ghi progress mới → sự kiện `storage` ở tab B → tab B render lại số "Đã nhớ" |

**Nhóm D — Xuất / nhập (Node, logic thuần):**
| # | Test | Input → Expected |
|---|---|---|
| D1 | Xuất đúng envelope | Progress hợp lệ → file JSON có `app`, `kind`, `version: 1`, `exportedAt`, `data.version === 1` |
| D2 | Nhập: JSON hỏng | Nội dung `"{"` → lỗi `"File không phải JSON hợp lệ"`, storage không đổi |
| D3 | Nhập: sai app | `app: "khac"` → lỗi `"không phải file tiến độ của Sai Đâu Sửa Đó"`, storage không đổi |
| D4 | Nhập: version mới hơn | `data.version: 99` → lỗi `"phiên bản mới hơn (v99)"`, storage không đổi |
| D5 | Nhập: slug lạ | `lessons: {"loi-999": {...}}` → lỗi nêu đúng `"loi-999"`, storage không đổi |
| D6 | Nhập: ngày không có thật | `doneAt: "2026-02-30"` → lỗi `"không phải ngày hợp lệ"`, storage không đổi |
| D7 | Nhập: interval ngoài miền | `review: {"loi-001": {interval: 90, ...}}` → lỗi `"interval phải từ 1 tới 60, nhận được 90"`, storage không đổi |
| D8 | Nhập: mâu thuẫn nội bộ | `review` có nhưng `lessons[slug].done === false` → lỗi `"có lịch ôn nhưng chưa được đánh dấu đã nhớ"`, storage không đổi |
| D9 | Nhập: chế độ Gộp, xung đột | Máy có `loi-001 doneAt 2026-11-14`, file có `loi-001 doneAt 2026-11-15` → sau gộp `doneAt === "2026-11-15"` (mới hơn thắng); bài chỉ có trong máy vẫn còn |
| D10 | Nhập: chế độ Ghi đè | Máy có 9 bài, file có 2 bài → sau nhập đúng 2 bài, `history` có action `import` ghi chế độ |
| D11 | Nhập: file quá lớn | File 2 MB → từ chối `"File quá lớn"`, storage không đổi |
| D12 | Xuất → nhập vòng tròn | Xuất progress hiện tại → xóa storage → nhập lại file → progress khôi phục giống hệt (so sánh deep-equal trừ `updatedAt`) |

**Nhóm E — Tìm kiếm + bộ lọc (Node, logic thuần):**
| # | Test | Input → Expected |
|---|---|---|
| E1 | Không dấu | Query `"muon"` → ra Lỗi #001 (trước cả "mượn") |
| E2 | Có dấu | Query `"mượn"` → ra Lỗi #001 |
| E3 | Tìm trong ví dụ | Query `"laptop"` → ra Lỗi #001 (ví dụ "She lent me her laptop") |
| E4 | Tìm trong "Nhớ điều này" | Query `"cứu đói"`-tương tự (từ trong `remember`) → ra đúng bài |
| E5 | Xếp hạng | Query `"borrow"` → Lỗi #001 và Quiz #001 đều ra, Lỗi #001 đứng trước (title khớp) |
| E6 | Lọc topic sinh từ dữ liệu | Thêm bài topic `ngữ pháp` → chip "ngữ pháp" xuất hiện, lọc ra đúng bài đó (bắt H-03) |
| E7 | Lọc kết hợp | `topic=giao tiếp` + `type=Lỗi` + `q=bored` → đúng 1 bài (Lỗi #002) |
| E8 | Lọc theo trạng thái | Đánh dấu loi-001 đã nhớ → lọc "Đã nhớ" chỉ còn loi-001; lọc "Đến hạn ôn" chỉ còn bài có `nextDue <= hôm nay` |
| E9 | Lọc theo lộ trình | `path=sua-phat-am` → đúng 4 bài (loi-004, mau-cau-003, loi-002, quiz-002) |
| E10 | URL đồng bộ | Set `q=borrow&topic=giao-tiep` → `location.search` chứa cả hai; tải lại với URL đó → lọc khôi phục |

**Checklist kiểm thử tay (không tự động hóa được — cần trình duyệt thật):**
1. iPhone thật (Safari): viewport 390 px và 320 px (máy cũ) — không cuộn ngang ở tab Tra cứu
   (bắt H-07); nút "Tiếp tục" cố định đáy không che nội dung bước cuối; `env(safe-area-inset-bottom)` trên máy có tai thỏ.
2. Bấm nút Nghe trên iPhone/Android thật: có tiếng en-US không (bắt M-07); thử khi máy đang
   chế độ im lặng (iOS: `speechSynthesis` vẫn đọc, nhưng kiểm chứng).
3. Chế độ tối trên máy thật: mở trang ở dark mode hệ thống → **không chớp sáng**;
   đọc hết 9 trang bài + trang chủ + 3 trang lộ trình, chụp lại chỗ chữ chìm (bắt M-01).
4. Tắt JavaScript: trang bài vẫn đọc được toàn bộ nội dung (bắt M-16).
5. Private mode Safari iOS: blocking storage → quiz vẫn chấm được (bắt S-01).
6. Chia sẻ ảnh canvas: tải ảnh từ màn hình hoàn thành, mở xem — chữ không tràn khung,
   font đúng (bắt L-05).
7. Chia sẻ link bài lên Facebook (debug bằng Sharing Debugger): ảnh OG đúng bài,
   mô tả không cụt (bắt M-05).
8. Undo thật trên **repo thử** (không phải repo production): chạy `undo_deploy.py` →
   xác nhận 422 hay thành công (bắt S-04).
9. Kiểm chứng bằng mắt: 3 trang lộ trình hiển thị đúng số bài đã nhớ theo từng lộ trình.

---

## 3. Ghi chú cho lần triển khai sau (không phải phát hiện)

- **Thứ tự sửa khuyến nghị:** S-01/S-02 (bọc storage + đổi thứ tự ghi) → S-03 (guard
  `renderToday`) → S-05 (README) → S-04 (kiểm chứng undo trên repo thử) → H-01/H-02
  (điểm theo bài + schema practice) → H-03 (chip từ dữ liệu) → H-06 (font) → H-07
  (grid 320 px) → rồi mới làm §2 (schema v1 + SRS + export/import + tìm kiếm mới).
- **Mỗi lần sửa = 1 commit** theo cách làm việc đã chốt (CAP-NHAT-SITE.md); lần sửa
  S-04 bắt buộc kiểm chứng trên repo thử trước, không thử trên repo production.
- **Không thay đổi trong đợt này:** nội dung bài học, luật caption, nhận diện
  (navy/mint/cam), khuôn wizard 6/4 bước, lịch đăng bài.
- **File này là tài liệu audit + thiết kế, không phải code.** Mọi đoạn JSON/JS trong
  §2 là đặc tả (ví dụ minh họa), chưa được chạy — cần viết test §2.5 trước rồi mới
  triển khai theo test.
