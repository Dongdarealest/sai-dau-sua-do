# Đặc tả API mở Kho bài học Sai Đâu Sửa Đó

Phiên bản 1.0.0. API đang hoạt động tại đường dẫn gốc bên dưới.

## API này là gì

API mở là bộ dữ liệu học tiếng Anh của Trang Sai Đâu Sửa Đó, công khai dưới dạng file JSON tĩnh trên GitHub Pages. Không cần đăng ký, không cần khóa, không mất phí, không cần máy chủ riêng. App flashcard, chatbot luyện nói, Zalo mini app hay app ôn tập theo lịch SRS đều có thể lấy nội dung từ đây.

Đường dẫn gốc: `https://dongdarealest.github.io/sai-dau-sua-do/api/v1/`

## Nội dung của bộ dữ liệu

1. Nghĩa tiếng Việt viết cho người Việt, không phải dịch máy từ nghĩa tiếng Anh. 852 từ trong bảng từ điển do Trang soạn và kiểm tra bằng tay, từng nghĩa một.
2. 64 bài học: 32 bài Lỗi, 17 bài Quiz, 9 bài Mẫu câu, 6 bài Reels. Mỗi bài có cặp câu sai và câu đúng, lý do bằng tiếng Việt và bài tập có giải thích. Tổng cộng 214 câu luyện tập.
3. Mọi ví dụ tiếng Anh đều có dịch tiếng Việt ngay bên dưới.
4. Từ điển hiểu dạng chia của từ. Tra `loves` ra `love`, tra `went` ra nghĩa quá khứ của `go`, tra `don't` ra nghĩa viết tắt.
5. Dữ liệu nhẹ: danh sách bài học khoảng 38 KB, từ điển đầy đủ khoảng 150 KB. Tải một lần rồi dùng ngoại tuyến được. Không có máy chủ, không cần khóa.
6. Mọi file trả về đều có khối `meta.source` ghi tên Trang, link web, link Facebook, giấy phép và câu ghi công.

## Nguyên tắc thiết kế

1. Tĩnh hoàn toàn. Mọi đầu dữ liệu là file JSON tĩnh do `generate_site.py` sinh ra lúc build, phục vụ qua GitHub Pages. Không có code chạy phía máy chủ, không có cơ sở dữ liệu, không có trạng thái người dùng.
2. Có phiên bản trong đường dẫn. Mọi đường dẫn đều bắt đầu bằng `/api/v1/`. Phiên bản 1 giữ nguyên sau khi công bố. Thay đổi phá vỡ tương thích chỉ xuất hiện ở phiên bản mới; phiên bản cũ vẫn hoạt động.
3. Ghi công nằm trong dữ liệu. Mọi file trả về đều có khối `meta.source` ghi tên Trang, link web, link Facebook, giấy phép và câu ghi công.
4. Tiếng Việt là chính. Từ loại, nghĩa, giải thích, ghi chú đều bằng tiếng Việt. Câu tiếng Anh chỉ xuất hiện trong ví dụ và câu luyện tập, luôn kèm dịch tiếng Việt.
5. Không đổi URL cũ. API chỉ thêm đường dẫn mới dưới `/api/`. Mọi bài học cũ giữ nguyên đường dẫn.
6. Nguồn gốc ghi rõ. Trường nào do Trang tự soạn thì ghi Trang soạn. Trường nào lấy từ nguồn ngoài thì ghi rõ nguồn đó.

## Tổng quan đầu dữ liệu

| Phương thức | Đường dẫn | Nội dung | Kích thước khoảng |
|---|---|---|---|
| GET | `/api/v1/meta.json` | Phiên bản, số lượng, nguồn, giấy phép | 1 KB |
| GET | `/api/v1/lessons.json` | Danh sách gọn 64 bài, lọc phía trình duyệt | 38 KB |
| GET | `/api/v1/lessons/{slug}.json` | Chi tiết đầy đủ 1 bài | 2 đến 6 KB mỗi bài |
| GET | `/api/v1/dictionary.json` | Toàn bộ 852 từ, nghĩa tiếng Việt đã kiểm tra tay | 150 KB |
| GET | `/api/v1/search-index.json` | Chỉ mục tìm kiếm 58 bài đang hiển thị | 66 KB |
| GET | `/api/v1/paths.json` | 3 lộ trình học | 2 KB |
| GET | `/api/` | Trang tài liệu cho lập trình viên | Trang HTML |

Mọi đầu dữ liệu trả về JSON, mã hóa UTF-8, không cần tiêu đề xác thực. GitHub Pages cho phép đọc từ mọi nguồn, nên gọi API từ trình duyệt hay từ app đều được.

## meta.json

Mô tả phiên bản và nguồn gốc toàn bộ API. App nên đọc file này trước để biết API đang ở phiên bản nào và còn bao nhiêu bài.

```json
{
  "api_version": "1.0.0",
  "api_base": "https://dongdarealest.github.io/sai-dau-sua-do/api/v1/",
  "total_lessons": 64,
  "visible_lessons": 58,
  "total_words": 852,
  "words_with_example": 112,
  "learning_paths": 3,
  "updated": "2026-11-19",
  "source": {
    "name": "Sai Đâu Sửa Đó",
    "site": "https://dongdarealest.github.io/sai-dau-sua-do",
    "facebook_page": "https://www.facebook.com/profile.php?id=61596506009854",
    "facebook_group": "https://www.facebook.com/groups/4387154551501983",
    "license": "CC BY 4.0",
    "attribution": "Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang."
  }
}
```

Trường `visible_lessons` là số bài đang hiển thị trên web, 58 bài. 6 bài Reels còn lại vẫn có trong API nhưng không hiện trong danh sách chính của web, phân biệt bằng trường `show_in_ui` ở mỗi bài.

## lessons.json: danh sách bài học

Trả về danh sách gọn của toàn bộ 64 bài. Mỗi bài chỉ gồm các trường đủ để hiển thị danh sách và thẻ xem trước, không gồm bài tập đầy đủ. Muốn xem bài tập thì gọi đầu dữ liệu chi tiết theo `slug`.

Vì API chạy tĩnh nên không có tham số lọc phía máy chủ. App tải một lần file 38 KB rồi lọc ngay trên máy người dùng theo `type`, `topic` hoặc tìm trong `title`, `wrong`, `right`.

```json
{
  "meta": {
    "api_version": "1.0.0",
    "total_lessons": 64,
    "visible_lessons": 58,
    "source": {
      "name": "Sai Đâu Sửa Đó",
      "site": "https://dongdarealest.github.io/sai-dau-sua-do",
      "facebook_page": "https://www.facebook.com/profile.php?id=61596506009854",
      "facebook_group": "https://www.facebook.com/groups/4387154551501983",
      "license": "CC BY 4.0",
      "attribution": "Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang."
    }
  },
  "lessons": [
    {
      "slug": "loi-001",
      "code": "Lỗi #001",
      "type": "Lỗi",
      "topic": "giao tiếp",
      "title": "borrow và lend",
      "date": "2026-11-12",
      "wrong": "Can you borrow me your pen?",
      "right": "Can you lend me your pen?",
      "remember": "Mượn VỀ mình → borrow. Cho người KHÁC mượn → lend.",
      "url": "https://dongdarealest.github.io/sai-dau-sua-do/loi-001/",
      "fb": "https://www.facebook.com/61596506009854/posts/122097926157550200",
      "image": "ngay-01/Loi-001-borrow-lend.png",
      "show_in_ui": true
    }
  ]
}
```

Ý nghĩa từng trường:

| Trường | Kiểu | Nguồn | Ghi chú |
|---|---|---|---|
| `slug` | chuỗi | Trang soạn | Mã bài, trùng với đường dẫn trang bài |
| `code` | chuỗi | Trang soạn | Tên hiển thị, ví dụ Lỗi #001 |
| `type` | chuỗi | Trang soạn | 1 trong 4 giá trị: Lỗi, Mẫu câu, Quiz, Reels |
| `topic` | chuỗi | Trang soạn | 1 trong 6 giá trị: giao tiếp, ngữ pháp, từ vựng, phát âm, công sở, quiz tổng hợp |
| `title` | chuỗi | Trang soạn | Chủ đề bài, ví dụ borrow và lend |
| `date` | chuỗi ngày | Trang soạn | Ngày đăng bài, dạng năm tháng ngày |
| `wrong` | chuỗi | Trang soạn | Câu sai người Việt hay nói |
| `right` | chuỗi | Trang soạn | Câu đúng thay cho câu sai |
| `remember` | chuỗi | Trang soạn | Câu nhớ nhanh, ngắn gọn |
| `url` | chuỗi | Sinh từ `slug` | Link trang bài trên web |
| `fb` | chuỗi | Trang đăng | Link bài gốc trên Facebook |
| `image` | chuỗi | Trang vẽ | Đường dẫn ảnh bài, tương đối theo gốc web |
| `show_in_ui` | đúng sai | Trang soạn | False ở 6 bài Reels, các bài còn lại là true |

## lessons/{slug}.json: chi tiết 1 bài học

Trả về toàn bộ nội dung 1 bài, gồm câu sai và câu đúng, lý do, ví dụ, bài tập đầy đủ và link liên quan. Đây là đầu dữ liệu app dùng nhiều nhất để hiển thị bài học và chạy bài tập. Nội dung bài nằm trong trường `lesson` của file trả về.

Ví dụ đầy đủ với bài Lỗi #001, dữ liệu thật, không rút gọn:

```json
{
  "meta": {
    "api_version": "1.0.0",
    "source": {
      "name": "Sai Đâu Sửa Đó",
      "site": "https://dongdarealest.github.io/sai-dau-sua-do",
      "facebook_page": "https://www.facebook.com/profile.php?id=61596506009854",
      "facebook_group": "https://www.facebook.com/groups/4387154551501983",
      "license": "CC BY 4.0",
      "attribution": "Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang."
    }
  },
  "lesson": {
    "slug": "loi-001",
    "code": "Lỗi #001",
    "type": "Lỗi",
    "topic": "giao tiếp",
    "title": "borrow và lend",
    "date": "2026-11-12",
    "wrong": "Can you borrow me your pen?",
    "wrong_note": "Bạn cho tôi mượn cây bút được không?",
    "right": "Can you lend me your pen?",
    "right_note": "Bạn cho tôi mượn cây bút được không?",
    "why": "borrow là mượn về mình, lend là cho người khác mượn.",
    "problem": "Người Việt hay dịch thẳng 'cho tôi mượn' thành borrow me, vì nghĩ borrow là 'cho mượn'. Thực ra borrow chỉ dùng khi chính mình là người mượn về.",
    "core": "borrow + vật + from + người: mình mượn về. lend + người + vật, hoặc lend + vật + to + người: mình cho người khác mượn. Nhớ hướng chuyển động: borrow là về phía mình, lend là ra khỏi mình.",
    "compare": [
      {
        "a": "I borrowed some money from my friend.",
        "b": "My friend lent some money to me.",
        "note": "Hai câu cùng một sự việc, chỉ đổi góc nhìn: người mượn dùng borrow from, người cho mượn dùng lend to."
      },
      {
        "a": "Could you lend me your dictionary?",
        "b": "Could I borrow your dictionary?",
        "note": "Muốn mượn đồ của ai, hỏi bằng lend me hoặc borrow your, đừng nói borrow me."
      },
      {
        "a": "She borrowed my camera and kept it for a week.",
        "b": "I lent her my camera for a week.",
        "note": "Borrow kể từ phía người mượn, lend kể từ phía người cho mượn."
      }
    ],
    "mistakes": [
      {"wrong": "Can you borrow me your car?", "right": "Can you lend me your car?"},
      {"wrong": "He borrowed me his notes before the exam.", "right": "He lent me his notes before the exam."},
      {"wrong": "I want to lend a book from the library.", "right": "I want to borrow a book from the library."}
    ],
    "remember": "Mượn VỀ mình → borrow. Cho người KHÁC mượn → lend.",
    "examples": [
      {"en": "Can I borrow your pen?", "vi": "Tôi mượn cây bút của bạn được không?"},
      {"en": "She lent me her laptop yesterday.", "vi": "Hôm qua cô ấy cho tôi mượn laptop."}
    ],
    "practice": [
      {
        "kind": "choice",
        "prompt": "Can you ___ me your pen?",
        "options": ["borrow", "lend", "take"],
        "answer": 1,
        "explanation": "Bạn mượn bút của người khác về mình → người kia lend cho bạn."
      },
      {
        "kind": "choice",
        "prompt": "I need to ___ a book from the library.",
        "options": ["borrow", "lend", "take"],
        "answer": 0,
        "explanation": "Bạn mượn sách về mình → borrow. I need to borrow a book from the library."
      },
      {
        "kind": "choice",
        "prompt": "Chọn câu đúng:",
        "options": ["She borrowed me her bike.", "She lent me her bike."],
        "answer": 1,
        "explanation": "She lent me her bike, cô ấy cho tôi mượn xe."
      },
      {
        "kind": "fill_blank",
        "prompt": "Could I ___ your jacket for the evening?",
        "options": ["borrow", "lend"],
        "answer": 0,
        "explanation": "Mình là người mượn về nên dùng borrow. Nếu hỏi ngược lại: Could you lend me your jacket?"
      },
      {
        "kind": "find_error",
        "prompt": "Tìm lỗi trong câu: 'Please borrow me your umbrella, it is raining.'",
        "options": [
          "Please lend me your umbrella, it is raining.",
          "Please borrow your umbrella to me, it is raining.",
          "Please borrowing me your umbrella, it is raining."
        ],
        "answer": 0,
        "explanation": "Người nói muốn mượn ô về mình nên người kia phải lend. 'Borrow me' sai vì borrow không nhận tân ngữ chỉ người được cho mượn."
      },
      {
        "kind": "distinguish",
        "prompt": "Chọn câu đúng:",
        "options": ["I lent some money from my brother.", "I borrowed some money from my brother."],
        "answer": 1,
        "explanation": "Mượn tiền về mình thì borrow from. Lend không đi với from, người cho mượn dùng lend to."
      },
      {
        "kind": "translate",
        "prompt": "Dịch câu: 'Bạn cho mình mượn sạc dự phòng được không?'",
        "options": ["Can you borrow me your power bank?", "Can you lend me your power bank?", "Can I lend your power bank?"],
        "answer": 1,
        "explanation": "Bạn là người cho mượn nên dùng lend me. 'Can you borrow me' sai hướng, còn 'Can I lend your power bank' thiếu tân ngữ chỉ người nhận."
      }
    ],
    "quiz": null,
    "reel": {
      "label": "Xem Reel bài này",
      "url": "https://www.facebook.com/reel/1521348529887565"
    },
    "tip": null,
    "ipa": [],
    "dict_links": [],
    "image": "ngay-01/Loi-001-borrow-lend.png",
    "fb": "https://www.facebook.com/61596506009854/posts/122097926157550200",
    "url": "https://dongdarealest.github.io/sai-dau-sua-do/loi-001/",
    "show_in_ui": true
  }
}
```

### Trường nào có thể vắng mặt

Không phải bài nào cũng có đủ mọi trường. App phải chịu được trường vắng, không được lỗi khi gặp giá trị rỗng.

| Trường | Có mặt ở | Khi vắng thì hiểu là |
|---|---|---|
| `quiz` | 21 trong 64 bài | Bài không có câu đố nhanh, giá trị là null |
| `reel` | 6 trong 64 bài | Bài không gắn Reel, giá trị là null |
| `tip` | 47 trong 64 bài | Bài không có mẹo riêng, giá trị là null |
| `ipa` | Bài phát âm | Mảng rỗng khi bài không dạy phát âm |
| `dict_links` | Hầu hết là mảng rỗng | Link từ điển ngoài, hiện chưa dùng |
| `problem`, `core`, `compare`, `mistakes` | 58 trong 64 bài | 6 bài Reels không có các trường này |
| `practice` | 58 trong 64 bài | 6 bài Reels có mảng rỗng |

### 6 dạng câu luyện tập

Trường `practice` chứa các câu luyện tập của bài. Mỗi câu đều có `prompt`, `options`, `answer` là vị trí đáp án đúng trong mảng `options` tính từ 0, và `explanation` giải thích bằng tiếng Việt. 6 dạng câu:

| Dạng `kind` | Cách chơi | Ví dụ prompt |
|---|---|---|
| `choice` | Chọn 1 đáp án đúng trong 2 đến 3 lựa chọn | Can you ___ me your pen? |
| `fill_blank` | Điền từ đúng vào chỗ trống | Could I ___ your jacket for the evening? |
| `find_error` | Tìm câu đúng trong các câu gần giống nhau, có câu sai | Tìm lỗi trong câu: 'Please borrow me...' |
| `distinguish` | Phân biệt 2 câu chỉ khác nhau 1 điểm | Chọn câu đúng: I lent... / I borrowed... |
| `translate` | Dịch câu tiếng Việt sang câu tiếng Anh đúng | Dịch câu: 'Bạn cho mình mượn sạc dự phòng được không?' |
| `word_order` | Sắp xếp các từ thành câu đúng, `answer` là mảng vị trí | Sắp xếp thành câu đúng: 'me / your / Can / lend / camera / you / ?' |

Riêng dạng `word_order`, trường `answer` là mảng số thứ tự, ví dụ `[0, 1, 2, 3, 4, 5, 6]`, còn `options` là các từ cần sắp xếp. Các dạng còn lại, `answer` là 1 số duy nhất.

## dictionary.json: từ điển tiếng Việt

Trả về toàn bộ 852 từ trong bảng nghĩa của Trang, mỗi từ có 1 hoặc nhiều nghĩa, mỗi nghĩa có từ loại tiếng Việt, nghĩa tiếng Việt, và có thể có ví dụ kèm dịch. File đầy đủ khoảng 150 KB, app tải một lần rồi tra ngay trên máy người dùng, không cần gọi lại.

Vì API chạy tĩnh nên không có đường dẫn tra theo từ phía máy chủ. Cách tra 1 từ là tải `dictionary.json` một lần rồi tìm trong đó. Trang tài liệu `/api/` hướng dẫn cách này kèm code mẫu.

```json
{
  "meta": {
    "api_version": "1.0.0",
    "total_words": 852,
    "words_with_example": 112,
    "source": {
      "name": "Sai Đâu Sửa Đó",
      "site": "https://dongdarealest.github.io/sai-dau-sua-do",
      "facebook_page": "https://www.facebook.com/profile.php?id=61596506009854",
      "facebook_group": "https://www.facebook.com/groups/4387154551501983",
      "license": "CC BY 4.0",
      "attribution": "Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang."
    },
    "meaning_source": "Bảng nghĩa do Trang soạn và kiểm tra bằng tay. Phiên âm và nghĩa tiếng Anh lấy trực tiếp từ dictionaryapi.dev lúc tra, không lưu trong dữ liệu này."
  },
  "words": {
    "tomorrow": {
      "senses": [
        {
          "pos": "trạng từ",
          "meaning": "ngày mai",
          "example_en": "See you tomorrow.",
          "example_vi": "Hẹn gặp lại ngày mai."
        },
        {
          "pos": "danh từ",
          "meaning": "ngày mai"
        }
      ]
    },
    "comfortable": {
      "senses": [
        {
          "pos": "tính từ",
          "meaning": "thoải mái",
          "example_en": "This chair is comfortable.",
          "example_vi": "Cái ghế này ngồi thoải mái."
        }
      ]
    },
    "went": {
      "senses": [
        {
          "pos": "động từ",
          "meaning": "đã đi"
        }
      ]
    },
    "don't": {
      "senses": [
        {
          "pos": "trạng từ",
          "meaning": "không (viết tắt của do not)"
        }
      ]
    }
  }
}
```

Ý nghĩa từng trường trong 1 nghĩa:

| Trường | Kiểu | Nguồn | Ghi chú |
|---|---|---|---|
| `pos` | chuỗi | Trang soạn | Từ loại bằng tiếng Việt. 10 giá trị: danh từ, động từ, tính từ, trạng từ, giới từ, đại từ, liên từ, mạo từ, số từ, thán từ |
| `meaning` | chuỗi | Trang soạn | Nghĩa tiếng Việt, viết cho người Việt hiểu ngay |
| `example_en` | chuỗi, có thể vắng | Trang soạn | Ví dụ tiếng Anh, chỉ có ở 112 từ |
| `example_vi` | chuỗi, có thể vắng | Trang soạn | Dịch tiếng Việt của ví dụ, đi kèm `example_en` |

### Trường mistakes: nối từ với bài học

Mỗi từ còn có trường `mistakes` là danh sách tối đa 5 slug bài học mà từ đó xuất hiện trong cặp câu sai và câu đúng của bài. Quét theo ranh giới từ, không phân biệt hoa thường, thứ tự slug theo thứ tự bài trong `lessons.json`. Từ nào không xuất hiện ở bài nào thì danh sách rỗng. Ví dụ từ `tomorrow` có `mistakes` là `["mau-cau-001"]`, từ `borrow` có `["loi-001", "reel-001"]`. App dùng trường này để gợi ý bài học ngay khi người dùng tra từ, thay vì chỉ hiện nghĩa.

### Tra dạng chia của từ

Bảng chỉ lưu 852 dạng gốc và dạng bất quy tắc, không lưu mọi dạng chia. App tra từ nên chuẩn hóa trước khi tìm, theo đúng cách web của Trang đang làm:

1. Viết thường toàn bộ từ, bỏ khoảng trắng thừa.
2. Tìm đúng từ trong bảng trước. Ví dụ `books` không có trong bảng, `book` thì có.
3. Nếu không thấy, thử bỏ đuôi chia: `s`, `es`, `ed`, `ing`, rồi thử đổi `ies` thành `y`. Ví dụ `loves` bỏ `s` thành `love`, `going` bỏ `ing` thành `go`.
4. Dạng bất quy tắc đã có sẵn trong bảng: `went` nghĩa là đã đi, `said` nghĩa là đã nói, `children` nghĩa là trẻ em.
5. Dạng rút gọn đã có sẵn trong bảng: `don't`, `doesn't`, `didn't`, `i'd`.

Quy tắc này ghi trong trang tài liệu kèm code mẫu, để app ngoài tra được giống hệt web của Trang.

## search-index.json: chỉ mục tìm kiếm

Dùng lại chỉ mục tìm kiếm sẵn có của web, 58 bài đang hiển thị. Mỗi mục gồm `slug`, `code`, `title`, `wrong`, `right`, `remember`, `why` và `examples` là các chuỗi đã gộp câu tiếng Anh với dịch tiếng Việt. App dùng file này để làm ô tìm kiếm gõ là ra, không cần tự tách dữ liệu.

```json
{
  "slug": "loi-001",
  "code": "Lỗi #001",
  "title": "borrow và lend",
  "wrong": "Can you borrow me your pen?",
  "right": "Can you lend me your pen?",
  "remember": "Mượn VỀ mình → borrow. Cho người KHÁC mượn → lend.",
  "why": "borrow là mượn về mình, lend là cho người khác mượn.",
  "examples": [
    "Can I borrow your pen? Tôi mượn cây bút của bạn được không?",
    "She lent me her laptop yesterday. Hôm qua cô ấy cho tôi mượn laptop."
  ]
}
```

## paths.json: lộ trình học

Trả về 3 lộ trình học của Trang, mỗi lộ trình là thứ tự các bài nên học. App dùng file này để gợi ý người học đi theo lộ trình thay vì học không theo thứ tự.

```json
{
  "meta": {
    "api_version": "1.0.0",
    "source": {
      "name": "Sai Đâu Sửa Đó",
      "site": "https://dongdarealest.github.io/sai-dau-sua-do",
      "facebook_page": "https://www.facebook.com/profile.php?id=61596506009854",
      "facebook_group": "https://www.facebook.com/groups/4387154551501983",
      "license": "CC BY 4.0",
      "attribution": "Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang."
    }
  },
  "paths": [
    {
      "slug": "hoc-lai-tu-dau",
      "name": "Học lại từ đầu",
      "desc": "Từ những lỗi cơ bản nhất, học theo thứ tự, mỗi bài chỉ 3, 5 phút.",
      "icon": "🌱",
      "order": ["loi-001", "quiz-001", "loi-002", "quiz-002", "loi-003", "mau-cau-001", "mau-cau-002"]
    },
    {
      "slug": "tieng-anh-di-lam",
      "name": "Tiếng Anh đi làm",
      "desc": "Lỗi hay gặp ở văn phòng: xin nghỉ, giới thiệu bản thân, nói chuyện với đồng nghiệp.",
      "icon": "💼",
      "order": ["loi-001", "loi-003", "mau-cau-001", "mau-cau-002", "quiz-001"]
    },
    {
      "slug": "sua-phat-am",
      "name": "Sửa phát âm",
      "desc": "Những từ người Việt hay đọc sai, nghe, đọc theo, sửa ngay.",
      "icon": "🗣️",
      "order": ["loi-004", "mau-cau-003", "loi-002", "quiz-002", "quiz-nhanh-001", "quiz-nhanh-005"]
    }
  ]
}
```

Một bài có thể nằm trong nhiều lộ trình, thứ tự trong mỗi lộ trình mới là thứ tự nên học.

## Nguồn gốc từng trường

| Nhóm trường | Nguồn | Ghi chú |
|---|---|---|
| Mọi trường bài học: `wrong`, `right`, `why`, `problem`, `core`, `compare`, `mistakes`, `remember`, `examples`, `practice`, `quiz`, `tip` | Trang Sai Đâu Sửa Đó tự soạn | Nội dung gốc của Trang, kiểm chứng lại bằng từ điển Cambridge hoặc Oxford trước khi đăng |
| Nghĩa tiếng Việt trong từ điển: `pos`, `meaning`, `example_en`, `example_vi` | Trang Sai Đâu Sửa Đó tự soạn | 852 từ kiểm tra bằng tay, 112 từ có ví dụ kèm dịch |
| Phiên âm và nghĩa tiếng Anh khi tra từ trên web | dictionaryapi.dev, API miễn phí không cần khóa | Không lưu trong dữ liệu API, web gọi trực tiếp lúc tra, ghi rõ nguồn ở cuối trang Từ điển |
| Nghĩa dự phòng khi từ không có trong bảng của Trang | Wiktionary tiếng Việt qua MediaWiki API | Chỉ dùng khi bảng của Trang không có từ đó, ghi rõ nguồn khi hiển thị |
| Dịch máy khi không còn nguồn nào | MyMemory, dịch máy miễn phí | Chỉ dùng khi cả bảng Trang và Wiktionary đều không có, luôn ghi rõ dòng chữ dịch máy chưa kiểm chứng, không bao giờ trình bày như nghĩa đã kiểm chứng |
| Ảnh bài học | Trang vẽ | Ảnh minh họa bài, thuộc nội dung gốc của Trang |
| Link Facebook `fb` và `reel.url` | Bài đăng thật trên Trang | Mở ra đúng bài đăng gốc, không phải link rút gọn |

## Ghi công và giấy phép

Giấy phép áp dụng:

| Đối tượng | Giấy phép | Ghi chú |
|---|---|---|
| Code: `generate_site.py`, code trang web, code ví dụ trong tài liệu | MIT | Ai cũng được dùng, sửa, bán sản phẩm làm từ code, chỉ cần giữ lại dòng bản quyền và giấy phép. Không bắt buộc công khai code của app họ. |
| Nội dung: bài học, bảng nghĩa tiếng Việt, ảnh bài học, lộ trình | CC BY 4.0 | Ai cũng được chia sẻ và dùng lại, kể cả để kiếm tiền, với 1 điều kiện duy nhất là ghi công đúng cách. |
| Tên Trang, logo chữ S kèm dấu tick, slogan "Mỗi ngày sửa một lỗi nhỏ." | Không thuộc giấy phép mở | Đây là dấu hiệu nhận diện của Trang. Ghi công bằng tên và link thì được, tự ý dùng logo làm thương hiệu riêng thì không được, cần hỏi Trang trước. |

Câu ghi công bắt buộc, app phải hiển thị ở nơi người học thấy được, ví dụ cuối trang hoặc trong phần giới thiệu app:

> Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang.

Kèm theo 1 trong 2 link: link web `https://dongdarealest.github.io/sai-dau-sua-do` hoặc link Facebook `https://www.facebook.com/profile.php?id=61596506009854`.

### Lưu ý giấy phép của nguồn nghĩa bên ngoài

Dữ liệu API chỉ chứa phần do Trang tự soạn: bài học và bảng nghĩa tiếng Việt 852 từ đã kiểm tra bằng tay, nên CC BY 4.0 áp dụng trọn cho dữ liệu này. Phiên âm và nghĩa tiếng Anh mà trang Từ điển tra trực tiếp lúc người dùng gõ từ lấy từ dictionaryapi.dev, dữ liệu gốc của họ lấy từ Wiktionary theo giấy phép CC BY-SA 3.0, tức là giấy phép có điều kiện chia sẻ tương tự. Vì API không lưu phần đó vào file JSON nên không xung đột giấy phép. Nếu sau này lưu thêm nghĩa hay phiên âm lấy từ Wiktionary hay dictionaryapi.dev vào file API, phải ghi rõ nguồn và giữ giấy phép CC BY-SA cho đúng phần đó, không được gộp chung vào CC BY 4.0 của Trang. Nghĩa dịch máy MyMemory cũng vậy, phải ghi rõ là dịch máy chưa kiểm chứng và không nhận là công của Trang.

### Cái gì không công khai

1. Sản phẩm trả phí chưa bán hoặc đã dừng bán của Trang, ví dụ sổ tay luyện sửa lỗi và bộ 100 mẫu câu bản bán, không nằm trong API và không đưa vào repo công khai. Chỉ nội dung miễn phí đã đăng mới thuộc API.
2. Không có dữ liệu người dùng trong API. API không thu thập, không lưu, không trả về bất cứ thông tin nào của người học. App tự lo việc lưu tiến độ của người dùng bên phía app.
3. Logo và nhận diện thương hiệu của Trang không thuộc giấy phép mở.

## Trang tài liệu /api/

Trang tài liệu đặt ở `https://dongdarealest.github.io/sai-dau-sua-do/api/`. Nội dung trang gồm:

1. Giới thiệu ngắn: API là gì, dùng để làm gì, không cần khóa, không mất phí.
2. Bắt đầu trong 30 giây: 1 đoạn code lấy danh sách bài học và hiển thị 3 bài đầu tiên.
3. Danh sách đầu dữ liệu kèm ví dụ trả về cho từng đầu, lấy đúng ví dụ trong đặc tả này.
4. Cách tra từ: tải `dictionary.json` một lần, chuẩn hóa từ rồi tìm, kèm code mẫu xử lý dạng chia.
5. 4 app ví dụ có thể xây ngay, mỗi app có dàn ý và đoạn code bắt đầu.
6. Giấy phép và ghi công: MIT cho code, CC BY 4.0 cho nội dung, câu ghi công bắt buộc.
7. Đóng góp: link repo, cách báo lỗi dữ liệu, cách đề xuất thêm bài.
8. File OpenAPI `openapi.yaml` đặt ở `/api/openapi.yaml`, mô tả đủ 6 đầu dữ liệu cùng trang tài liệu, để đăng lên APIs.guru và Postman API Network, vì hai kênh này yêu cầu định nghĩa OpenAPI ở một URL ổn định.

### Ví dụ gọi API bằng fetch

Lấy danh sách bài học rồi lọc ra bài loại Lỗi thuộc chủ đề giao tiếp:

```js
const BASE = "https://dongdarealest.github.io/sai-dau-sua-do/api/v1/";
const data = await (await fetch(BASE + "lessons.json")).json();
const loiGiaoTiep = data.lessons.filter(
  (l) => l.type === "Lỗi" && l.topic === "giao tiếp"
);
console.log(loiGiaoTiep.length, "bài lỗi giao tiếp");
```

Lấy chi tiết 1 bài rồi chạy 1 câu luyện tập:

```js
const detail = await (await fetch(BASE + "lessons/loi-001.json")).json();
const lesson = detail.lesson;
const q = lesson.practice[0];
console.log(q.prompt, q.options, "Đáp án đúng là lựa chọn số", q.answer);
console.log("Giải thích:", q.explanation);
```

Tra 1 từ trong từ điển, có xử lý dạng chia:

```js
const dict = await (await fetch(BASE + "dictionary.json")).json();
function lookup(word) {
  word = word.toLowerCase().trim();
  if (dict.words[word]) return dict.words[word];
  for (const ending of ["ing", "es", "ed", "s"]) {
    if (word.endsWith(ending)) {
      const base = word.slice(0, word.length - ending.length);
      if (dict.words[base]) return dict.words[base];
    }
  }
  if (word.endsWith("ies")) {
    const base = word.slice(0, -3) + "y";
    if (dict.words[base]) return dict.words[base];
  }
  return null;
}
console.log(lookup("loves"));
console.log(lookup("tomorrow"));
```

### 4 app ví dụ có thể xây ngay

1. App flashcard. Lấy `lessons.json`, mỗi thẻ hiện câu sai ở mặt trước, lật thẻ hiện câu đúng kèm lý do và câu nhớ nhanh. Dùng trường `remember` làm mặt sau ngắn gọn. Thêm nút nghe phát âm bằng cách gọi dictionaryapi.dev lấy link âm thanh.
2. Chatbot luyện nói. Lấy chi tiết bài theo `slug`, chatbot hỏi từng câu trong `practice` theo thứ tự, chấm đúng sai bằng `answer`, giải thích bằng `explanation`. Hết bài thì gợi ý bài tiếp theo trong `paths.json`.
3. Zalo mini app. Màn hình chính hiện 3 lộ trình từ `paths.json`, bấm vào lộ trình thì tải chi tiết từng bài trong `order`. Mỗi bài hiện gọn câu sai và câu đúng, bấm vào mới xem lý do và bài tập, đúng thói quen đọc nhanh trên điện thoại.
4. App ôn tập theo lịch SRS. Lấy `practice` của mọi bài, trộn thành ngân hàng câu hỏi. Người học trả lời đúng thì đẩy câu đó ra xa theo lịch, trả lời sai thì cho gặp lại sớm. Dùng trường `date` để ưu tiên bài mới, dùng `topic` để ôn theo chủ đề yếu.

## Phiên bản và tương thích

1. Phiên bản 1 giữ nguyên sau khi công bố. Đã công bố thì không sửa schema làm hỏng app đang chạy. Chỉ thêm trường mới, không đổi tên hay xóa trường cũ.
2. Thêm bài mới không đổi phiên bản. Bài mới chỉ thêm vào danh sách, app cũ vẫn chạy, chỉ cần tải lại file là thấy bài mới.
3. Phiên bản 2 chỉ xuất hiện khi có thay đổi phá vỡ tương thích, ví dụ đổi tên trường hay đổi cấu trúc bài tập. Khi đó phiên bản 1 vẫn giữ nguyên đường dẫn và vẫn hoạt động, trang tài liệu ghi rõ khác biệt giữa 2 phiên bản.
4. Mỗi file đều có `meta.api_version` để app tự kiểm tra mình đang đọc phiên bản nào.

## Giới hạn

1. API chỉ đọc, không ghi. Không có đầu dữ liệu nào nhận bài mới hay lưu tiến độ người học. Muốn đóng góp thì gửi pull request lên repo.
2. Không có tìm kiếm phía máy chủ. Tìm kiếm chạy ngay trên máy người dùng bằng `search-index.json` hoặc lọc `lessons.json`.
3. Không có phiên âm trong dữ liệu tĩnh. Phiên âm và âm thanh lấy trực tiếp từ dictionaryapi.dev lúc tra, giống cách web của Trang đang làm.
4. Không có dịch máy trong dữ liệu tĩnh. Nghĩa dịch máy chỉ xuất hiện lúc tra trên web khi không còn nguồn nào, và luôn ghi rõ là dịch máy chưa kiểm chứng.
5. Nội dung tăng theo nhịp đăng của Trang. App nên tải lại file mỗi lần mở để thấy bài mới.
