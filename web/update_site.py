#!/usr/bin/env python3
"""Add one posted lesson to the site and republish it.

Usage (run by the posting crons after a lesson goes live on Facebook):
    python3 update_site.py --lesson /tmp/bai-moi.json [--no-push]

The lesson JSON must have: slug, code, type, topic, date, title,
wrong, right, why, fb, image_src. Optional: wrong_note, right_note,
examples [{en, vi}], ipa [{text, source, note}],
dict_links [{label, url}], quiz {question, prompt, options[], answer, explanation}.

Flow: validate -> append/replace in lessons.json (the single data file)
-> regenerate the whole site -> push the full tree to GitHub Pages.
Never push a single file (AGENTS.md lesson 16/10/2026).
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parent

sys.path.insert(0, str(ROOT))
from generate_site import validate_lessons, count_sentences_why

REQUIRED = ["slug", "code", "type", "topic", "date", "title",
            "wrong", "right", "why", "fb", "image_src"]
VALID_TYPES = ["Lỗi", "Mẫu câu", "Quiz", "Reels"]


def fail(msg):
    print("LỖI:", msg, file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", required=True, help="đường dẫn file JSON của bài mới")
    ap.add_argument("--no-push", action="store_true", help="chỉ cập nhật + dựng lại, không đẩy")
    ap.add_argument("--force-replace", action="store_true",
                    help="cho phép thay bài đã có cùng slug (mặc định: từ chối trùng slug; khi thay sẽ sao lưu bản cũ)")
    args = ap.parse_args()

    try:
        new = json.loads(Path(args.lesson).read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"không đọc được file bài mới: {e}")

    for field in REQUIRED:
        if not new.get(field):
            fail(f"thiếu trường bắt buộc: {field}")
    if new["type"] not in VALID_TYPES:
        fail(f"type phải là một trong {VALID_TYPES}, nhận được: {new['type']}")
    if new.get("quiz"):
        q = new["quiz"]
        if not (q.get("question") and q.get("options") and len(q["options"]) >= 2
                and isinstance(q.get("answer"), int) and 0 <= q["answer"] < len(q["options"])
                and q.get("explanation")):
            fail("quiz thiếu question/options/answer/explanation hợp lệ")
    img = WS / new["image_src"]
    if not img.exists():
        fail(f"không thấy file ảnh bài học: {img}")

    # Giai đoạn 2: bài học hiện cho người học phải có đủ khuôn cố định.
    show_in_ui = new.get("show_in_ui", new["type"] != "Reels")
    if show_in_ui:
        if len(new.get("practice", [])) < 2:
            fail("bài hiện cho người học phải có ít nhất 2 câu luyện (practice) — "
                 "xem schema trong CAP-NHAT-SITE.md")
        if not new.get("remember"):
            fail("bài hiện cho người học phải có dòng 'Nhớ điều này' (remember)")
        if count_sentences_why(new.get("why", "")) > 2:
            fail("Vì sao tối đa 2 câu")
    data_path = ROOT / "lessons.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    lessons = data["lessons"]
    new.setdefault("wrong_note", "")
    new.setdefault("right_note", "")
    new.setdefault("examples", [])
    new.setdefault("ipa", [])
    new.setdefault("dict_links", [])
    new.setdefault("quiz", None)
    new.setdefault("practice", [])
    new.setdefault("remember", "")
    new.setdefault("reel", None)
    new["show_in_ui"] = show_in_ui
    # Gắn bài vào lộ trình (nếu worker chỉ định)
    for path_slug in new.pop("paths", []):
        path = next((p for p in data["site"]["paths"] if p["slug"] == path_slug), None)
        if not path:
            fail(f"không có lộ trình: {path_slug}")
        if new["slug"] not in path["order"]:
            path["order"].append(new["slug"])
    # Gắn Reel vào bài tương ứng (Reel không hiện riêng trên giao diện học)
    attach_to = new.pop("attach_to", None)
    if attach_to:
        target = next((l for l in lessons if l["slug"] == attach_to), None)
        if not target:
            fail(f"không có bài để gắn Reel: {attach_to}")
        if target.get("reel"):
            print(f"CẢNH BÁO: bài {attach_to} đã có Reel gắn sẵn, sẽ bị thay bằng Reel mới.")
        target["reel"] = {"label": "Xem Reel bài này", "url": new["fb"]}

    replaced = False
    existing_idx = next((i for i, lesson in enumerate(lessons) if lesson["slug"] == new["slug"]), None)
    if existing_idx is not None and not args.force_replace:
        fail(f"slug '{new['slug']}' đã tồn tại ({lessons[existing_idx].get('code', '')} — "
             f"{lessons[existing_idx].get('title', '')}). Muốn thay bài cũ thì chạy lại với --force-replace "
             "(bản cũ sẽ được sao lưu vào backup/).")
    if existing_idx is not None:
        backup_dir = ROOT / "backup"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y%m%d-%H%M%S")
        backup_path = backup_dir / f"lessons-{new['slug']}-{stamp}.json"
        backup_path.write_text(json.dumps(lessons[existing_idx], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Đã sao lưu bản cũ ra {backup_path}")
        lessons[existing_idx] = new
        replaced = True
    else:
        lessons.append(new)
    # validate toàn bộ dữ liệu sau khi thêm/thay (H-04: answer trong khoảng, schema...)
    errs = validate_lessons(data, WS)
    if errs:
        for e in errs:
            print("LỖI validate:", e, file=sys.stderr)
        fail("dữ liệu không hợp lệ, chưa ghi gì")
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'Thay' if replaced else 'Thêm'} {new['code']} — {new['title']} "
          f"(tổng {len(lessons)} bài trong lessons.json)")

    gen = subprocess.run([sys.executable, str(ROOT / "generate_site.py")],
                         capture_output=True, text=True)
    print(gen.stdout.strip())
    if gen.returncode != 0:
        print(gen.stderr, file=sys.stderr)
        fail("generate_site.py chạy lỗi, chưa đẩy gì lên")

    if args.no_push:
        print("Chế độ --no-push: đã dừng trước bước đẩy.")
        return

    msg = f"{'Cập nhật' if replaced else 'Thêm'} bài {new['code']} — {new['title']}"
    push = subprocess.run([sys.executable, str(ROOT / "deploy_github_pages.py"),
                           "--message", msg],
                          capture_output=True, text=True)
    print(push.stdout.strip()[-1200:])
    if push.returncode != 0:
        print(push.stderr, file=sys.stderr)
        fail("deploy_github_pages.py chạy lỗi")
    print("Xong: bài mới đã lên https://dongdarealest.github.io/sai-dau-sua-do/")


if __name__ == "__main__":
    main()
