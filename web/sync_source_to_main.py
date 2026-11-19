#!/usr/bin/env python3
"""Đồng bộ mã nguồn Sai Đâu Sửa Đó lên nhánh main.

Sau lần tách nhánh 19/11/2026, repo có 2 nhánh: main chỉ giữ mã nguồn và
tài liệu, gh-pages chỉ giữ web đã sinh. Script này đẩy cây nguồn sạch lên
main, thay toàn bộ cây cũ của main bằng cây nguồn. Không bao giờ chạm
gh-pages, không bao giờ deploy web.

Quy tắc chạy: chỉ chạy bằng dòng lệnh, không import:
    python3 sync_source_to_main.py --message "..."
    python3 sync_source_to_main.py --list

Mẫu an toàn (giống deploy_github_pages.py): đọc head main làm commit cha,
kiểm tra mọi file tồn tại trước khi tạo blob, tái dùng blob trùng SHA với
cây remote, đẩy cây đầy đủ, không force push, ghi log riêng vào
web/SOURCE_SYNC_LOG.md để không lẫn với DEPLOY_LOG.md của web.

Script từ chối chạy nếu phát hiện một tiến trình deploy_github_pages.py
hoặc update_site.py đang chạy, để hai lần đẩy không giẫm nhau.
"""
import argparse
import base64
import datetime
import hashlib
import os
import subprocess
import sys
from pathlib import Path

WS = os.path.expanduser("~/workspace/sai-dau-sua-do")
SRC = os.path.join(WS, "web")
OWNER = "Dongdarealest"
REPO = "sai-dau-sua-do"
TARGET_BRANCH = "main"

sys.path.insert(0, os.path.expanduser("~/workspace/custom-connectors/custom.github/bin"))
from gh_api import api, GitHubError


def source_files():
    """Danh sách file nguồn lên main, đường đích là đường trên repo.
    Trả về danh sách cặp (đường nguồn trên đĩa, đường đích trên repo)."""
    out = []
    # File gốc mới, viết tay ở gốc workspace (mục 2 trong kế hoạch tách).
    for name in ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", ".gitignore"]:
        out.append((os.path.join(WS, name), name))
    # Hai file giấy phép, file gốc duy nhất nằm trong web/, copy ra gốc main.
    for name in ["LICENSE", "LICENSE-CONTENT.md"]:
        out.append((os.path.join(SRC, name), name))
    # Mã nguồn sinh trang, dữ liệu, tài liệu vận hành (mục 2.1).
    for name in ["generate_site.py", "update_site.py", "deploy_github_pages.py",
                 "undo_deploy.py", "sync_source_to_main.py",
                 "lessons.json", "enrichment.json",
                 "CAP-NHAT-SITE.md", "AUDIT-KYTHUAT.md", "AUDIT-NOIDUNG.md",
                 "DEPLOY_LOG.md", "SOURCE_SYNC_LOG.md", "favicon.svg"]:
        out.append((os.path.join(SRC, name), f"web/{name}"))
    for f in sorted(Path(os.path.join(SRC, "fonts")).glob("*.woff2")):
        out.append((str(f), f"web/fonts/{f.name}"))
    for f in sorted(Path(os.path.join(SRC, "giao-trinh")).glob("*.pdf")):
        out.append((str(f), f"web/giao-trinh/{f.name}"))
    # Thư mục tests, trừ node_modules và __pycache__ (mục 2.1).
    tests_dir = Path(os.path.join(SRC, "tests"))
    for f in sorted(tests_dir.iterdir()):
        if f.is_file() and f.name not in ("__pycache__",):
            out.append((str(f), f"web/tests/{f.name}"))
    # Tài liệu công khai cho lập trình viên ngoài: chỉ đặc tả API.
    # Mọi tài liệu nội bộ (nghiên cứu, kế hoạch, quyết định thiết kế,
    # kế hoạch tách nhánh) chỉ ở trên máy VM, không bao giờ lên main.
    for name in ["api-spec.md"]:
        out.append((os.path.join(WS, "docs", name), f"docs/{name}"))
    return out


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def deploy_in_flight():
    """True nếu có tiến trình deploy web đang chạy (không tính chính mình)."""
    try:
        r = subprocess.run(["pgrep", "-f", "deploy_github_pages.py|update_site.py"],
                           capture_output=True, text=True)
    except OSError:
        return False
    pids = [p for p in r.stdout.split() if p.isdigit() and int(p) != os.getpid()]
    return len(pids) > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", default="Đồng bộ mã nguồn lên main")
    ap.add_argument("--list", action="store_true",
                    help="chỉ liệt kê file sẽ đẩy rồi dừng, không đẩy gì")
    args = ap.parse_args()

    pairs = source_files()
    if args.list:
        print(f"đồng bộ nguồn: {len(pairs)} file")
        for _src, dest in pairs:
            print(" ", dest)
        return 0

    if deploy_in_flight():
        print("LỖI: phát hiện tiến trình deploy web đang chạy, dừng đồng bộ "
              "nguồn để hai lần đẩy không giẫm nhau.", file=sys.stderr)
        return 1

    me = api("GET", "/user")
    assert me["login"] == OWNER, me["login"]
    print("owner:", OWNER)

    head = api("GET", f"/repos/{OWNER}/{REPO}/commits/{TARGET_BRANCH}")
    parents = [head["sha"]]
    print("head main hiện tại:", parents[0])

    missing = [src for src, _dest in pairs if not os.path.exists(src)]
    # SOURCE_SYNC_LOG.md chưa có ở lần chạy đầu, cho phép thiếu và tạo sau.
    missing = [m for m in missing if not m.endswith("SOURCE_SYNC_LOG.md")]
    if missing:
        print("THIẾU FILE, chưa đẩy gì:", missing, file=sys.stderr)
        return 1

    remote_tree = {}
    try:
        tree = api("GET", f"/repos/{OWNER}/{REPO}/git/trees/{parents[0]}?recursive=1")
        remote_tree = {t["path"]: t["sha"] for t in tree.get("tree", [])
                       if t.get("type") == "blob"}
    except GitHubError as e:
        print("không đọc được cây remote, sẽ đẩy toàn bộ blob:", e)

    if remote_tree:
        extra = [p for p in remote_tree if p not in [d for _s, d in pairs]]
        if extra:
            print(f"CẢNH BÁO: {len(extra)} file có trên main nhưng KHÔNG nằm trong "
                  "danh sách nguồn, sẽ bị xóa sau lần đẩy này (đúng mục đích: "
                  "cây site cũ được thay bằng cây nguồn sạch).")

    entries = []
    n_reused = 0
    n_uploaded = 0
    for src, dest in pairs:
        if not os.path.exists(src):
            continue
        with open(src, "rb") as f:
            raw = f.read()
        sha = git_blob_sha(raw)
        if remote_tree.get(dest) == sha:
            entries.append({"path": dest, "mode": "100644", "type": "blob", "sha": sha})
            n_reused += 1
            print("reuse:", dest)
            continue
        blob = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs",
                   {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"})
        entries.append({"path": dest, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        n_uploaded += 1
        print("blob:", dest)
    print(f"blob: {n_uploaded} mới, {n_reused} tái dùng")

    tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"tree": entries})
    commit = api("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
        "message": args.message,
        "tree": tree["sha"],
        "parents": parents,
    })

    try:
        ref = api("POST", f"/repos/{OWNER}/{REPO}/git/refs",
                  {"ref": f"refs/heads/{TARGET_BRANCH}", "sha": commit["sha"]})
    except GitHubError as e:
        if e.status != 422:
            raise
        ref = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{TARGET_BRANCH}",
                  {"sha": commit["sha"], "force": False})

    print("pushed:", ref["object"]["sha"])
    print("repo:", f"https://github.com/{OWNER}/{REPO}")

    log_path = Path(SRC) / "SOURCE_SYNC_LOG.md"
    prev_sha = parents[0]
    line = (f"- {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%Y-%m-%d %H:%M')} "
            f"+07 | {commit['sha']} | prev {prev_sha} | {args.message}\n")
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + line, encoding="utf-8")
    else:
        log_path.write_text("# Nhật ký đồng bộ nguồn lên main (mới nhất cuối file)\n\n" + line, encoding="utf-8")
    print("logged to SOURCE_SYNC_LOG.md:", line.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
