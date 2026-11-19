#!/usr/bin/env python3
"""Revert the latest GitHub Pages deploy: move the gh-pages branch back to
the previous commit.

Reads DEPLOY_LOG.md for the previous commit (prev), PATCHes the ref with
force=True (moving a ref to an older commit is a non-fast-forward update,
so force=False returns 422 from GitHub), then appends a line to
DEPLOY_LOG.md so the next revert can go one step further.

Not yet verified live on a test repo or on production; code only.
"""
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/workspace/custom-connectors/custom.github/bin"))
from gh_api import api, GitHubError

SRC = os.path.expanduser("~/workspace/sai-dau-sua-do/web")
OWNER = "Dongdarealest"
REPO = "sai-dau-sua-do"


def fail(msg):
    print("LỖI:", msg, file=sys.stderr)
    sys.exit(1)


def parse_log_line(line):
    """Trả về (sha, prev, message) hoặc None nếu dòng sai định dạng."""
    parts = [x.strip() for x in line.split("|")]
    if len(parts) < 4 or not parts[2].startswith("prev "):
        return None
    sha, prev = parts[1], parts[2].replace("prev ", "").strip()
    if len(sha) < 7 or len(prev) < 7:
        return None
    return (sha, prev, parts[3])


def find_prev_for(lines, target_sha):
    """Commit đứng trước target_sha trong log (để hoàn tác lần sau lùi tiếp)."""
    for older in reversed(lines[:-1]):
        parsed = parse_log_line(older)
        if parsed and parsed[0] == target_sha:
            return parsed[1]
    return ""


def main():
    log = Path(SRC) / "DEPLOY_LOG.md"
    try:
        text = log.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"không thấy {log} — không có gì để hoàn tác")
    except OSError as e:
        fail(f"không đọc được {log}: {e}")
    lines = [l.strip() for l in text.splitlines() if l.startswith("- ")]
    if not lines:
        fail("DEPLOY_LOG.md trống — không có gì để hoàn tác")
    last = lines[-1]
    # line format: - <date> <time> +07 | <sha> | prev <sha> | <message>
    parsed = parse_log_line(last)
    if not parsed:
        fail(f"dòng log cuối sai định dạng, không đọc được commit trước: {last}")
    cur, prev, _msg = parsed
    try:
        ref = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/gh-pages",
                  {"sha": prev, "force": True})
    except GitHubError as e:
        print("KHÔNG hoàn tác được:", e)
        sys.exit(1)
    print("đã hoàn tác — gh-pages đang ở:", ref["object"]["sha"])
    print("live url:", f"https://{OWNER.lower()}.github.io/{REPO}/")
    # Append a log line so the next revert can go one step further:
    # the new line records the commit now live (prev) and the commit before
    # it (taken from the deploy line that created prev), not prev=cur,
    # which would move forward instead of back.
    new_prev = find_prev_for(lines, prev)
    stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M")
    line = (f"- {stamp} +07 | {prev} | prev {new_prev} | HOÀN TÁC về {prev[:7]} "
            f"(lùi từ {cur[:7]})\n")
    if not new_prev:
        print("CẢNH BÁO: không tìm được commit trước nữa trong log — lần hoàn tác sau sẽ dừng lại và báo lỗi thay vì lùi sai.")
    try:
        log.write_text(text + line, encoding="utf-8")
        print("đã ghi log hoàn tác:", line.strip())
    except OSError as e:
        print("CẢNH BÁO: đã lùi ref nhưng không ghi được DEPLOY_LOG.md:", e)


if __name__ == "__main__":
    main()
