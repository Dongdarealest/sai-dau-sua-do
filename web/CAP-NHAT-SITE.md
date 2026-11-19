# Cập nhật web Kho bài học sau mỗi bài đăng (giai đoạn 2: wizard từng bước, commit 6280870)

## Nguyên tắc
- **Tệp dữ liệu duy nhất:** `~/workspace/sai-dau-sua-do/web/lessons.json`, mọi bài học đều ở đây, không sửa nội dung
  trực tiếp trong file HTML đã sinh.
- **Sau mỗi bài đăng lên Facebook:** chạy `update_site.py`, nó thêm bài vào `lessons.json`, chạy lại
  `generate_site.py` (dựng lại trang chủ + trang riêng từng bài + ảnh OG), rồi đẩy **toàn bộ cây file**
  lên GitHub Pages. Không bao giờ đẩy lẻ 1 file (bài học sập web 16/10/2026).
- **Tách nhánh 19/11/2026:** web đã sinh đẩy lên nhánh `gh-pages`, mã nguồn và tài liệu giữ trên
  nhánh `main`. Cron đăng bài chỉ deploy web lên `gh-pages`, không bao giờ chạm `main`.
  Mã nguồn đổi thì đồng bộ lên `main` bằng `sync_source_to_main.py`, chạy tay sau khi sửa xong.
- **Gộp trùng:** nếu 2 bài cùng nội dung (ví dụ Quiz #003 và Lỗi #004 đều hỏi comfortable mấy âm), chỉ thêm 1 bài
  vào web, gắn quiz của bài còn lại vào trong bài đó và ghi chú `merged_from`.
- **Không lặp câu trong một trang bài:** mỗi câu đầy đủ (≥4 từ) chỉ xuất hiện tối đa 1 lần trong văn bản hiển thị
  của trang đó, kể cả ở ô Đúng, Ví dụ, Luyện tập, "Nhớ điều này" và màn hình hoàn thành. Trước khi đẩy,
  đếm chuỗi trực tiếp trên văn bản hiển thị (không đếm chuỗi trong thẻ HTML) của cả 9 trang bài.
  Từ đơn/mảnh ngắn (borrow, lend, bored...) xuất hiện nhiều lần là bình thường, không tính là lặp.

## Khuôn trang bài: wizard từng bước (từ Phần 2, tháng 11/2026, thay khuôn 6 bước cũ)
- Mỗi bài chạy theo từng bước, mỗi bước một màn hình gọn; thanh tiến độ ở đầu trang ("Bước X/Y");
  nút "Tiếp tục" lớn cố định ở đáy màn hình; nút "Quay lại" bên trái.
- Lỗi / Mẫu câu = 7 bước: (1) Vấn đề hay gặp + câu mở + ô Sai/Đúng (chữ thật, nút Nghe ở câu đúng),
  (2) Vì sao (≤2 câu) + Quy tắc cốt lõi (core), (3) So sánh dễ nhầm (compare) + Lỗi phổ biến (mistakes)
  + Phát âm (IPA + cách đặt miệng/lưỡi + nút Nghe, chỉ bài có IPA/articulation),
  (4) Ví dụ (Mẫu câu hiện đủ câu, Lỗi/Quiz đúng 2 ví dụ, khác câu đúng),
  (5) Quiz gộp (nếu có) + Luyện ngay chấm ngay (gồm cả dạng xếp từ word_order),
  (6) "Nhớ điều này" + Mẹo (nếu có) + tự đánh giá mức hiểu (3 nút: Khó, chưa nhớ / Vừa, nhớ chưa chắc /
  Dễ, nhớ ngay, không dùng emoji) + nút "Tôi đã nhớ bài này",
  (7) màn hình hoàn thành: tổng kết luyện của bài (đúng/tổng, liệt kê câu còn sai để ôn) + ngày ôn tới theo SRS
  + nút Bài tiếp theo + Chia sẻ kết quả.
- Quiz = 4 bước: (1) câu mở + quiz chính + hộp đáp án (ô Đúng + Vì sao + Quy tắc cốt lõi + Lỗi phổ biến
  tóm tắt + ví dụ) chỉ hiện SAU khi chọn, (2) Luyện thêm, (3) Nhớ + tự đánh giá + Đã nhớ,
  (4) hoàn thành.
- Điểm luyện hiển thị THEO BÀI ("đúng/tổng của bài này"); điểm toàn trang chỉ hiện ở trang chủ.
  Kết quả luyện lưu dạng {choice, correct, attempts, lastAt}, tải lại trang vẫn tô đỏ lựa chọn sai đã chọn.
  Dữ liệu cũ boolean true/false vẫn đọc được (choice=null, "đã làm trước đây").
- Bài Mẫu câu: bước Ví dụ hiện **đủ các câu của bài** (3–4 câu), vì đó chính là nội dung bài học. Đông chưa chốt siết lại đúng 2 câu.
- Màn hình hoàn thành: "Bạn đã sửa/học xong/làm xong <mã bài>!", cặp tóm tắt = **tên bài** (không lặp câu),
  dòng chuỗi học, nút "Bài tiếp theo" và nút "Chia sẻ kết quả", bấm để tải ảnh 1080×1080 vẽ bằng canvas
  (nền navy, chữ S + tick cam, cặp Sai→Đúng, slogan + URL trang) để đăng Facebook.
- Chế độ tối: nút chuyển sáng/tối ở đầu trang, nhớ lựa chọn trong localStorage (`sdsc-theme`),
  mặc định theo hệ thống. Icon toàn site là SVG đồng bộ (không emoji). Nút bấm ≥48px, chữ ≥16px, dòng 1,6.
- Động lực: chuỗi ngày học (localStorage `sdsc-streak-v1`: hôm nay đã học → giữ, hôm qua → +1, khác → 1),
  mục tiêu 1 bài/ngày, hiển thị trên trang chủ ("Chuỗi học: X ngày • Hôm nay: đã học/chưa học").
  Tiến độ "Đã nhớ" lưu trong trình duyệt (`sdsc-done-v2`), đổi máy sẽ mất.
- Ảnh web: ảnh bài được chuyển sang **JPEG chất lượng 85** khi dựng (nhẹ hơn PNG nhiều; 9 ảnh tổng ~692KB);
  ảnh OG và ảnh gốc cuối trang đều dùng `.jpg`. Ảnh bài Facebook nằm cuối trang, thu nhỏ (tối đa 320px)
  kèm link "Xem bài gốc trên Facebook".

## Schema bài mới: trường bổ sung (Phần 2)
- Ngoài các trường cũ: `problem` (vấn đề hay gặp, 1–2 câu), `core` (quy tắc cốt lõi),
  `compare` (mảng {a, b, note}, 2 câu đối chiếu), `mistakes` (mảng {right, wrong}, lỗi phổ biến),
  `tip` (mẹo ngắn, tùy chọn), `articulation` (cách đặt miệng/lưỡi, chỉ bài phát âm).
- `practice` có thêm `kind`: `fill_blank`, `find_error`, `distinguish`, `translate` (chấm như trắc nghiệm
  thường) và `word_order`, `answer` là MẢNG thứ tự đúng (hoán vị của 0..n-1), `options` là các từ rời rạc;
  khi dựng trang, thứ tự chip hiển thị được xáo trộn cố định theo slug (người học bấm lần lượt để xếp câu,
  bấm "Kiểm tra" để chấm). Câu `word_order` vẫn tính vào tổng câu luyện.
- `practice` không có `kind` = câu trắc nghiệm thường (tương thích dữ liệu cũ).
- `quiz` của bài Lỗi gộp vào bước Luyện (bước 5); hộp đáp án của bài Quiz có thêm core + mistakes tóm tắt.

## Tiến độ + SRS (Phần 2: key mới `sdsc-progress-v1`)
- Một key duy nhất `{version:1, updatedAt, lessons{done,doneAt,lastStudiedAt,selfGrade,reviews,orphan?},
  practice{choice,correct,attempts,lastAt}, streak{count,lastDate,dates≤30},
  review{interval,nextDue,ease,reps}, history≤500, settings{dailyGoal:1,remindReview:true}}`
  + bản sao `.bak` (ghi .bak trước, ghi chính sau; đọc chính hỏng thì đọc .bak, bản hỏng giữ ở
  `.corrupt.<timestamp>`).
- Migrate 1 lần từ `sdsc-done-v2` / `sdsc-practice-v2` / `sdsc-streak-v1` khi key mới chưa có:
  bài done cũ bắt đầu SRS từ nấc 1 (interval=1, nextDue=doneAt+1 ngày); slug lạ giữ lại kèm `orphan:true`;
  key cũ KHÔNG bị xóa. `sdsc-theme` giữ nguyên key riêng.
- SRS: Khó → interval=1, ease=max(1.3,ease−0.2), reps=0; Vừa → interval=max(1,round(interval×ease)), reps+1;
  Dễ → interval=max(1,round(interval×ease×1.3)), ease=min(2.5,ease+0.1), reps+1; trần interval 60 ngày.
  Tự đánh giá ở bước 6 lưu `selfGrade`; đánh dấu Đã nhớ lần đầu tạo lịch ôn (interval=1, ôn ngày mai);
  ôn lại (tự đánh giá khi bài đã nhớ) cập nhật SRS ngay + reviews+1.
  Bỏ đánh dấu Đã nhớ thì xóa `review[slug]` (đánh dấu lại bắt đầu từ nấc 1) và KHÔNG trừ streak đã tăng.
- "Ôn hôm nay" ở trang chủ là hàng đợi SRS thật: bài có `nextDue <= hôm nay`, quá hạn nhất trước, tối đa 5.
  Khi chưa có bài đến hạn: hiện "Bài ôn gần nhất là X vào ngày Y".
- Mọi lần chạm localStorage/sessionStorage đều có try/catch + bộ nhớ tạm trong phiên:
  storage bị chặn (private mode) thì quiz vẫn chấm được, theme vẫn đổi được. Đồng bộ chéo tab qua sự kiện `storage`.
- Trang chủ có thêm: danh sách "Bài đã hoàn thành" (tối đa 10, kèm ngày), "Hoạt động gần đây" (5 sự kiện mới nhất),
  "Thống kê quá trình học" (số bài đã nhớ, tỉ lệ luyện đúng, số lần ôn, chuỗi dài nhất, ngày học gần nhất).

## Xuất / nhập tiến độ (Phần 2: cuối khối Tiến độ, trang chủ)
- Nút "Tải dữ liệu tiến độ (.json)" xuất file `sai-dau-sua-do-tien-do-YYYY-MM-DD.json`,
  envelope `{app:"sai-dau-sua-do", kind:"progress-export", version:1, exportedAt, data}`.
- Nút "Nhập dữ liệu đã lưu" đọc file `.json`, validate đủ 9 bước theo đúng thứ tự trong AUDIT-KYTHUAT §2.3
  (JSON hợp lệ → app/kind → version → kiểu gốc → slug tồn tại → ngày hợp lệ → miền giá trị →
  nhất quán nội bộ → kích thước ≤1MB); lỗi nào cũng DỪNG, báo đúng câu lỗi tiếng Việt, KHÔNG ghi gì.
- Hai chế độ: Gộp (mặc định, mới hơn thắng từng bài/khóa) và Ghi đè (hộp xác nhận ghi rõ số bài/câu/chuỗi sẽ mất).
  Nhập xong ghi history action `import` + render lại toàn bộ + báo thành công có số liệu.

## Tìm kiếm + bộ lọc (Phần 2)
- Chuẩn hóa không dấu cả hai phía (NFD bỏ dấu): gõ "muon" hay "mượn" đều ra. Index gồm code/title/wrong/right/
  remember/why/ví dụ/IPA/quiz/practice. Xếp hạng: code/title +10, wrong/right +6, remember/why +4,
  ví dụ/quiz/practice +2, topic +3, khớp đầu từ ×2.
- Chip chủ đề + loại SINH TỪ DỮ LIỆU (kèm đếm số bài); thêm lọc theo lộ trình + trạng thái
  (Tất cả/Chưa học/Đã nhớ/Đến hạn ôn) + sắp xếp (Mới nhất/Cũ nhất/A–Z). Trạng thái lọc đồng bộ lên URL
  (`?q=&topic=&type=&path=&status=&sort=`) bằng replaceState, khôi phục khi tải trang; debounce 150ms.

## Quy tắc merge / migrate (Phần 2)
- `update_site.py`: trùng slug mặc định TỪ CHỐI (in rõ lỗi); chỉ thay khi có `--force-replace`, và trước khi thay
  sao lưu bản cũ ra `backup/lessons-<slug>-<timestamp>.json`. Validate toàn bộ dữ liệu (dùng chung
  `validate_lessons()` trong `generate_site.py`) trước khi ghi, lỗi thì chưa ghi gì.
- `generate_site.py` chạy `validate_lessons()` đầu `main()` (báo rõ tên bài lỗi) và kiểm tra đủ ảnh
  TRƯỚC khi xóa `images/` (H-05).
- `deploy_github_pages.py`: README lấy từ file đã sinh trên đĩa (chỉ giữ seed README cho repo mới hoàn toàn);
  `site_files()` gồm thêm `favicon.svg`, `sitemap.xml`, `robots.txt`, `CNAME`, `.nojekyll` (nếu có) và `fonts/*.woff2`;
  kiểm tra mọi file tồn tại trước khi tạo blob; cảnh báo file trên repo ngoài danh sách sẽ bị xóa.
- `undo_deploy.py`: PATCH ref với `force=True`, validate định dạng dòng log (lỗi đẹp thay vì traceback),
  sau khi lùi ghi thêm dòng vào DEPLOY_LOG.md để lần hoàn tác sau lùi tiếp được nữa.
  CHƯA kiểm chứng live trên repo thử hay repo production, chỉ sửa code, cần parent kiểm chứng.
- Font: tự host woff2 trong `fonts/` (Be Vietnam Pro 400/600/700/900 + Inter 400/600/700), chỉ subset
  latin/latin-ext/vietnamese; `@font-face` trong CSS; canvas chia sẻ đợi `document.fonts.ready` trước khi vẽ.
- Site sinh thêm `favicon.svg` (S trắng + tick cam trên nền navy), `sitemap.xml`, `robots.txt`.

## Kiểm thử (Phần 2)
- `python3 -m unittest discover -s tests -v` (từ thư mục web/), 17 test nhóm A (§2.5, A3 điều chỉnh theo
  khuôn 7/4 bước, A12 điều chỉnh theo deploy đã sửa): trang đủ, gỡ bài xóa trang cũ, số bước wizard,
  không lặp câu, ảnh JPEG, validate schema, OG tags, link nội bộ, font-size ≥16px, không link rỗng,
  README đúng số liệu, deploy đọc README đĩa, font subset, chuỗi hoàn tác.
- `bash tests/check_js.sh`, trích mọi khối `<script>` trong HTML đã sinh rồi chạy `node --check` từng khối.
- Sau mỗi lần sửa `generate_site.py`: chạy lại `python3 generate_site.py`, kiểm tra 9 trang bài + 3 trang lộ
  trình + trang chủ sinh đủ, đếm câu lặp hiển thị = 0, mọi ảnh .jpg tồn tại, không có font-size <16px,
  không có href="#" hay href="".
- Tài liệu rác cũ (`_tmp_v2_*.js`, `patch_wizard_*.py`, `__pycache__`) đã dời vào `web/_archive/`
  (không nằm lẫn với file deploy).

## Cách làm việc từ nay (Đông chốt 15/11 00:21)
- Mọi thay đổi nội dung/giao diện do Đông chỉ thị bằng tin nhắn hoặc ô chỉ thị trên dashboard, tự sửa và đẩy lên repo, Đông không tải file.
- **Mỗi yêu cầu = MỘT commit**, tên commit mô tả rõ thay đổi. `deploy_github_pages.py --message "..."`;
  `update_site.py` tự truyền message theo mã bài. Sau khi đẩy: báo lại link trang vừa đổi + tóm tắt đã sửa gì.
- **Đông nhắn "hoàn tác"** thì đưa trang về lần trước: chạy `python3 undo_deploy.py`, nó đọc dòng cuối
  `DEPLOY_LOG.md` (ngày giờ +07 | commit sha | prev sha | message) và đưa nhánh `gh-pages` về commit `prev`.
- **Trước khi sửa nội dung kiến thức** (IPA, ví dụ, cách đọc): kiểm tra lại nguồn Cambridge hoặc Oxford.

## Quy trình cho cron đăng bài (sáng/trưa/tối/Reels)
Sau bước "thêm bản ghi Notion công khai" và "đăng bình luận đầu tiên", làm thêm:
1. Viết file JSON của bài vừa đăng, ví dụ `/tmp/bai-moi.json`, đúng schema bên dưới.
   Ảnh bài học (`image_src`) là đường dẫn tương đối từ `~/workspace/sai-dau-sua-do/`, ví dụ
   `ngay-04/Loi-005-a-university.png` (ảnh đã dựng sẵn trước giờ đăng).
2. Chạy: `python3 ~/workspace/sai-dau-sua-do/web/update_site.py --lesson /tmp/bai-moi.json`
3. Kiểm tra dòng cuối in ra link live. Nếu script báo LỖI: ghi vào nhật ký + dashboard,
   KHÔNG tự sửa tay file HTML đã sinh, KHÔNG đẩy lại bằng tay.

## Schema bài mới (JSON)
```json
{
  "slug": "loi-005", "code": "Lỗi #005", "type": "Lỗi", "topic": "ngữ pháp",
  "date": "2026-11-15", "title": "a university",
  "wrong": "an university.", "wrong_note": "",
  "right": "a university.", "right_note": "",
  "why": "a hay an dựa vào âm đầu, không dựa vào chữ cái.",
  "examples": [{"en": "a university in Da Lat.", "vi": "Một trường đại học ở Đà Lạt."}],
  "ipa": [{"text": "/juːnɪˈvɜːrsəti/", "source": "Cambridge, Anh-Mỹ", "note": ""}],
  "dict_links": [{"label": "Cambridge, university", "url": "https://dictionary.cambridge.org/dictionary/english/university"}],
  "quiz": null,
  "fb": "https://www.facebook.com/61596506009854/posts/<ID_BAI_MOI>",
  "image_src": "ngay-04/Loi-005-a-university.png"
}
```
- `slug`: viết thường, không dấu, dạng `loi-005` / `mau-cau-004` / `quiz-004` / `reel-003` (theo đúng số bài đã đăng).
- `type`: chỉ 1 trong 4: `Lỗi`, `Mẫu câu`, `Quiz`, `Reels`.
- `topic`: `công sở`, `giao tiếp`, `phát âm`, `ngữ pháp`, `từ vựng`, `quiz tổng hợp`, `nhắc lại`.
- `quiz` (chỉ bài Quiz, hoặc bài Lỗi gộp quiz): `{"question": "...", "prompt": "...",
  "options": ["...", "...", "..."], "answer": 0, "explanation": "..."}`, `answer` là vị trí đáp án đúng
  (0 = A, 1 = B, 2 = C). Đáp án đúng KHÔNG xuất hiện trong caption/bài Facebook, nhưng trên web thì hiện
  sau khi người học chọn, đó là chủ đích của quiz tương tác.
- `practice` (BẮT BUỘC với bài hiện cho người học, ít nhất 2 câu): mảng các câu luyện chấm ngay,
  mỗi câu `{"prompt": "...", "options": ["...", "..."], "answer": 0, "explanation": "..."}`, tự soạn từ nội dung bài (điền chỗ trống hoặc chọn câu đúng), đáp án đúng và giải thích ngắn.
  Bài Quiz thì quiz chính là câu luyện đầu tiên, cộng thêm 2 câu practice.
- `remember` (BẮT BUỘC với bài hiện cho người học): 1 dòng "Nhớ điều này", ngắn gọn, nêu đúng quy tắc
  (ví dụ: "borrow = mượn về mình, lend = cho người khác mượn.").
- `why` (Vì sao): tối đa 2 câu, ngắn gọn.
- `paths` (tùy chọn): danh sách lộ trình bài này thuộc về, ví dụ `["hoc-lai-tu-dau", "tieng-anh-di-lam"]`.
  Lộ trình: `hoc-lai-tu-dau` (học lại từ đầu), `tieng-anh-di-lam` (tiếng Anh đi làm),
  `sua-phat-am` (sửa phát âm). Không ghi thì bài chỉ nằm trong kho Tra cứu.
- `ipa`: chỉ ghi IPA đã kiểm chứng với Cambridge hoặc Oxford, luôn kèm nguồn + giọng (Anh-Mỹ/Anh-Anh).
  Không chắc thì bỏ trống trường này, đừng bịa.
- Ảnh: dùng đúng file ảnh đã dựng cho bài đăng Facebook (slide 1 với Mẫu câu, frame đầu với Reels).
- Reel: bài Reel (type `Reels`) KHÔNG hiện riêng trên giao diện học, nó được gắn vào bài tương ứng
  bằng trường `attach_to` (slug của bài, ví dụ `"attach_to": "loi-005"`), nút "Xem Reel" sẽ hiện
  trong trang bài đó.

## Kiểm tra nhanh sau khi cập nhật
- Mở `https://dongdarealest.github.io/sai-dau-sua-do/`, số bài tăng 1; trang chủ có khung "Học hôm nay",
  thanh tiến độ, dòng chuỗi học, 3 thẻ lộ trình.
- Mở `https://dongdarealest.github.io/sai-dau-sua-do/<slug>/`, thấy wizard từng bước (thanh tiến độ + nút
  "Tiếp tục" cố định đáy), nút Nghe, quiz chấm được, màn hình hoàn thành sau khi bấm "Tôi đã nhớ bài này".
- Bấm nút chuyển sáng/tối ở đầu trang, nền tối phải đổi toàn trang (cả thẻ bài).
- Nếu trang chưa đổi: GitHub Pages cần ~1 phút để dựng lại, chờ rồi tải lại, đừng đẩy lại.

## Sửa / gỡ bài (chỉ khi cần)
- Sửa nội dung 1 bài: sửa đúng bản ghi đó trong `lessons.json`, chạy `python3 generate_site.py`,
  rồi `python3 deploy_github_pages.py`.
- Gỡ 1 bài: xóa bản ghi khỏi `lessons.json` rồi làm 2 lệnh trên. Trang cũ của bài đó biến mất sau lần đẩy.

## Nâng cấp toàn diện 15/11/2026: ghi chú vận hành mới
- Trang bài Lỗi/Mẫu câu chạy **7 bước** (Vấn đề → Vì sao/Quy tắc → So sánh/Lỗi phổ biến/Phát âm
  → Ví dụ → Luyện tập → Nhớ + tự đánh giá Khó/Vừa/Dễ → Hoàn thành), Quiz giữ **4 bước**.
  Tự đánh giá tạo/cập nhật lịch ôn SRS ngay; bỏ "Đã nhớ" xóa lịch ôn, không trừ chuỗi học.
- Tiến độ lưu ở **1 key `sdsc-progress-v1`** (+ `.bak` tự động), migrate 1 lần từ 3 key cũ
  (`sdsc-done-v2`, `sdsc-practice-v2`, `sdsc-streak-v1`, key cũ vẫn giữ nguyên 30 ngày).
- SRS: Khó → ôn lại 1 ngày sau; Vừa → interval × ease; Dễ → interval × ease × 1,3;
  ease 1,3–2,5, interval trần 60 ngày. "Ôn tập hôm nay" = bài có nextDue ≤ hôm nay, tối đa 5.
- Xuất/nhập tiến độ: nút cuối khối Tiến độ trên trang chủ, file
  `sai-dau-sua-do-tien-do-YYYY-MM-DD.json`, envelope `{app, kind, version, exportedAt, data}`.
  Validate 9 bước, lỗi thì không ghi gì. **Lưu ý:** ngày ôn lại (nextDue) được chấp nhận tới
  hôm nay + 60 ngày (trần interval SRS); các ngày còn lại (doneAt, lastStudiedAt, lastDate)
  chỉ tới ngày mai, file export luôn nhập lại được (đã kiểm thử vòng tròn).
- Tìm kiếm: gõ không dấu vẫn trúng ("muon" → "mượn"); lọc theo chủ đề/loại/lộ trình/trạng thái
  (Chưa học/Đã nhớ/Đến hạn ôn); đồng bộ URL `?q=&topic=&type=&path=&status=&sort=`.
- Quy tắc gạch ngang (Đông, 00:49 15/11): mọi nội dung hiển thị trên web KHÔNG dùng dấu
  gạch ngang (-, –, —). Trong câu dùng dấu phẩy, dấu chấm, dấu hai chấm, hoặc tách câu.
  Tiêu đề dùng dấu hai chấm. Tên trang: Kho bài học Sai Đâu Sửa Đó. Khoảng số viết bằng
  chữ (3 đến 5 phút). Ngày hiển thị dạng DD/MM/YYYY (helper Python `fmt_date`, JS
  `fmtDate`/`dispDate`, kể cả ngày trong thông báo lỗi nhập). Tên file, đường dẫn, slug,
  URL và cờ CLI (`--lesson`) giữ nguyên (đó là cấu trúc, không phải nội dung hiển thị).
  `validate_lessons` chặn bài mới có gạch ngang ở trường hiển thị (title/why/wrong/
  right/remember/problem/core/tip/articulation/examples/compare/mistakes/practice/quiz/
  ipa); bài vi phạm thì `generate_site.py`/`update_site.py` báo lỗi và dừng TRƯỚC khi ghi.
  **Lưu ý cho cron đăng bài:** nội dung ngày mới có gạch ngang sẽ làm bước cập nhật web
  lỗi (ghi log, web không đẩy); xem log rồi sửa nội dung ngày đó, không bỏ qua lỗi.

## Kiểm thử (chạy sau mỗi lần sửa generator)
- `python3 generate_site.py`, phải in dòng OK với số bài đúng bằng số bài visible trong
  lessons.json (19/11: 56 bài học, 3 lộ trình, 6 reel, 228 câu luyện, + 4 trang mới).
- `python3 -m unittest discover -s tests`, nhóm A (sinh trang, deploy, undo-log) + lớp
  TestNewPages + lớp TestOptimization: 28 test. Lỗi duy nhất còn lại là A4 đã có từ trước (câu lặp ở quiz-nhanh-003,
  lỗi dữ liệu bài cũ, ngoài phạm vi).
- `bash tests/check_js.sh`, `node --check` trên toàn bộ block script: mọi block đều phải qua
  (19/11: 186 block nội tuyến + app.js, data.js và search-index.json).
- `cd tests && node test_browser_be.js`, nhóm B–E bằng jsdom (cần `npm install jsdom --no-save`
  lần đầu): chấm điểm/wizard, SRS, xuất/nhập, tìm kiếm, 68 test. `tests/node_modules/`
  chỉ dùng để test, KHÔNG nằm trong danh sách deploy.
- `cd tests && node test_new_pages_be.js`, 44 test cho 4 trang mới + chunk (từ điển với fetch
  giả lập, gồm N35 đến N44 kiểm tra nghĩa tiếng Việt hiện trước, nhãn từ loại tiếng Việt,
  phiên âm tối đa 2 dòng, ví dụ có dịch, từ gần nghĩa có nghĩa tiếng Việt, tách gốc số nhiều,
  Wiktionary và dịch máy có nhãn; bảng lộ trình với tiến độ mẫu, thư viện lọc/tìm, luyện nói
  khi trình duyệt không hỗ trợ).
- Đếm câu lặp: không có câu đầy đủ nào xuất hiện quá 1 lần trong cùng 1 trang bài (kiểm bằng
  script đếm trên văn bản hiển thị; lần kiểm cuối = 0, trừ A4 đã biết ở trên).
- Quét gạch ngang (chạy sau mỗi lần sửa nội dung/generator, từ thư mục `web/`):
  `python3 tests/scan_dash.py` (văn bản hiển thị toàn bộ trang, gồm title/meta/alt),
  `python3 tests/scan_js_strings.py` (chuỗi JS hiển thị), `python3 tests/scan_displ.py`
  (trường hiển thị trong `lessons.json`); cả 3 phải = 0 hit. Văn bản hiển thị trên 4 trang mới
  cũng đã quét = 0 hit (kiểm bằng parser bỏ qua script/style, 19/11).

## Tối ưu A+B (19/11/2026, Đông chốt "tối ưu nhất có thể")
- File dùng chung: `styles.css` (từ hằng CSS), `app.js` (từ SHARED_JS), `data.js`
  (tổng + SDSC_LESSONS/SDSC_PATHS/SDSC_ORDER/SDSC_TOTALS). Mọi trang chỉ link
  tới 3 file này; JS riêng từng loại trang vẫn nhúng trong trang đó.
- Chỉ mục tìm kiếm: `search-index.json`, chỉ nạp khi người dùng tìm kiếm
  (fetch lúc gõ hoặc mở trang với ?q=). Trước lúc đó trang chủ dùng chỉ mục
  gọn dựng từ data.js (mã, tiêu đề, lý do, chủ đề, loại, ngày, lộ trình).
- Tổng số bài ở header KHÔNG ghi cứng vào HTML nữa: header ghi span rỗng
  (`.total-lessons-num`, `.progress-num`), app.js điền số lúc chạy từ data.js.
  Nhờ đó thêm 1 bài chỉ đổi khoảng 9 đến 10 file (trang bài mới, ảnh mới,
  trang chủ, data.js, search-index.json, sitemap.xml, README.md, lessons.json,
  thư viện chủ đề, luyện nói nếu có câu mới, trang bài kề trước do đổi link
  Bài tiếp theo) thay vì 67 file như trước.
- Build tăng dần: `generate_site.py` chỉ ghi file nào đổi (write_if_changed),
  chỉ nén lại ảnh nào đổi (so mtime ảnh nguồn và ảnh đích), in số file đổi
  cuối dòng OK. Build lần 2 ngay sau lần 1 phải đổi 0 file.
- Deploy thông minh: `deploy_github_pages.py` so SHA blob với cây remote,
  file nào trùng thì tái dùng, không POST blob mới. Cây commit vẫn đẩy đủ,
  không force push, hoàn tác bằng undo_deploy.py như cũ.
- Kiểm thử mới: lớp TestOptimization trong tests/test_site.py (5 test).
  Harness jsdom nội tuyến app.js/data.js vào HTML trước khi dựng DOM và
  stub fetch cho search-index.json; test E6 chờ nạp xong rồi mới assert.

## Nâng cấp kiểu app PeakFour (19/11/2026, Đông chốt "làm luôn trên web Kho bài học")
- 4 trang mới do `generate_site.py` sinh (nằm trong sitemap, deploy tự gồm): `/tu-dien/`
  (tra từ điển qua API miễn phí dictionaryapi.dev, không key: nghĩa tiếng Việt hiện ĐẦU
  TIÊN, to và rõ nhất, nhãn từ loại bằng tiếng Việt (danh từ, động từ, tính từ, trạng từ...),
  phiên âm tối đa 2 dòng (giọng Anh, giọng Mỹ) kèm nút Nghe, mỗi ví dụ có dịch tiếng Việt
  ngay bên dưới, từ gần nghĩa có nghĩa tiếng Việt kèm theo nếu có; nguồn nghĩa tiếng Việt
  theo thứ tự: bảng nghĩa Trang soạn sẵn trong `DICT_JS` (852 từ thường gặp + từ
  trong bài học, kể cả dạng quá khứ bất quy tắc và số nhiều qua tách gốc), Wiktionary tiếng
  Việt qua MediaWiki API, rồi dịch máy MyMemory chỉ khi cả hai đều không có và luôn ghi rõ
  "(dịch máy, chưa kiểm chứng)"; nghĩa tiếng Anh vẫn hiện bên dưới kèm nhãn từ loại tiếng
  Việt; link Cambridge/Oxford ở cuối dạng đọc thêm; dòng nguồn dictionaryapi.dev đẩy xuống
  chân trang nhỏ; từ đã tra gần đây lưu localStorage key `sdsc-dict-recent`, báo rõ khi
  không tìm thấy từ hoặc mất mạng), `/bang-lo-trinh/` (6 ô số: bài đã nhớ, tỉ lệ luyện đúng,
  buổi luyện nói, tổng giờ luyện nói, chuỗi ngày học, điểm luyện nói tốt nhất; tiến độ từng
  lộ trình + bài tiếp theo + ôn hôm nay), `/thu-vien-chu-de/` (mọi bài gom theo chủ đề, lọc
  chip + tìm kiếm không dấu), `/luyen-noi/` (chọn câu mẫu trong 178 câu từ các bài, nghe câu
  mẫu, nói lại, máy nghe qua Web Speech API và chấm khớp theo từ, hiện câu máy nghe được +
  từ chưa rõ; chỉ Chrome/Edge mới có nhận diện giọng nói, Safari/iPhone thì hiện câu báo rõ
  và khóa nút Bắt đầu nói).
- Học từng cụm (Chunking) trong từng trang bài: sau wizard, hộp "Học từng cụm" đi từng câu
  (câu đúng + ví dụ, chuỗi nhiều câu tách thành từng câu đơn), nút Nghe câu mẫu / Cụm trước /
  Cụm tiếp theo, thanh tiến độ Cụm x/y; cụm cuối bấm thì qua trang Luyện nói với đúng câu đó
  (`?s=`). Câu chunk chỉ nằm trong khối `<script type="application/json">`, JS điền lúc chạy,
  KHÔNG render tĩnh để không vi phạm test A4 (câu lặp).
- Luyện nói lưu key riêng `sdsc-speaking-v1` {sessions, minutes, words, best, lastDay}, không
  đụng schema `sdsc-progress-v1`; mỗi lượt luyện nói ghi số phút + số từ + điểm tốt nhất.
- Giới hạn nói rõ trên trang Luyện nói: web chỉ kiểm tra câu nói có khớp câu mẫu không, chưa
  chấm được từng âm như app chuyên luyện phát âm (cần app chạy ngay trên máy, web tĩnh chưa
  làm được). Không hứa quá.
- Thanh điều hướng chung trong header mọi trang: Trang chủ, Bảng lộ trình, Thư viện chủ đề,
  Từ điển, Luyện nói. Trang chủ thêm mục "Kỹ năng mới" nối tới 4 trang.
- Kỳ vọng test cũ đã lỗi thời sửa thành tính theo dữ liệu (A11/A12/word_order/E6) thay vì số
  cứng, để thêm bài mới không làm vỡ test.

## CẢNH BÁO: deploy_github_pages.py deploy ngay khi import
- File `deploy_github_pages.py` **không có `if __name__ == "__main__"`**, toàn bộ code deploy
  chạy ở top-level. `import deploy_github_pages` (kể cả chỉ để lấy `site_files()`) sẽ ĐẨY
  NGAY một commit lên GitHub. **15/11 00:45 đã xảy ra 1 lần như vậy do import nhầm trong lúc
  kiểm tra song song** (commit 5003a53 thiếu 9 ảnh .jpg, đã hoàn tác về b5e86c4 bằng
  `undo_deploy.py` rồi đẩy lại đúng 1 commit).
- Quy tắc: KHÔNG bao giờ `import deploy_github_pages`; muốn liệt kê file thì tự viết đoạn
  liệt kê riêng, hoặc đọc source. Chỉ chạy bằng dòng lệnh:
  `python3 deploy_github_pages.py --message "..."`.
- `undo_deploy.py` đã kiểm chứng live lần đầu ngày 15/11/2026 (lùi main 5003a53 → b5e86c4,
  force=True). Dùng khi Đông nhắn "hoàn tác"; mỗi lần chạy chỉ lùi 1 commit theo DEPLOY_LOG.md.

## Tách nhánh 19/11/2026: main giữ mã nguồn, gh-pages phục vụ web
- Repo tách thành 2 nhánh: `main` chỉ chứa mã nguồn và tài liệu, `gh-pages` chỉ chứa web đã sinh.
  GitHub Pages phục vụ `gh-pages` ở cùng tên miền, mọi URL giữ nguyên, không đổi link nào.
- `deploy_github_pages.py` đẩy web lên `gh-pages` qua hằng `TARGET_BRANCH`, không dùng nhánh
  mặc định nữa. `undo_deploy.py` lùi `gh-pages`, không lùi `main`.
- Mã nguồn, dữ liệu, test và tài liệu vận hành đồng bộ lên `main` bằng
  `sync_source_to_main.py`, chạy tay sau mỗi đợt sửa mã nguồn. Không gắn đồng bộ nguồn vào
  cuối script deploy web, vì cron đăng bài chạy deploy web 10 ca mỗi ngày, gắn thêm sẽ làm
  cron chạm `main` và phá đúng ranh giới vừa dựng.
- Mỗi tối kiểm tra một bất biến: sha blob của `web/lessons.json` trên `main` phải bằng sha blob
  của `lessons.json` trên `gh-pages`. Lệch thì chạy đồng bộ nguồn ngay, không để qua ngày.
- `deploy_github_pages.py` vẫn cấm import như trước, chỉ chạy bằng dòng lệnh.
