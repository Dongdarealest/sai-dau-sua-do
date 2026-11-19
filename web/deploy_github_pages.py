"""Deploy the Sai Dau Sua Do lesson library to GitHub Pages.

Warning: this file has no `if __name__ == "__main__"` guard, so the deploy
code runs at import time. Importing deploy_github_pages, even only to read
site_files(), pushes a commit to GitHub immediately. An accidental import
on 15/11/2026 created commit 5003a53 missing 9 images; it was reverted.
Never import this file. Run it only from the command line:
    python3 deploy_github_pages.py --message "..."

Safe pattern:
- full tree push (index.html + README.md), never a single stray file
- every commit has the real parent (seed commit on a fresh repo,
  current head on an existing repo), never parents=[] + force-push
- ref update falls back to PATCH with force=False
"""
import base64
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/workspace/custom-connectors/custom.github/bin"))
from gh_api import api, GitHubError

SRC = os.path.expanduser("~/workspace/sai-dau-sua-do/web")
OWNER = "Dongdarealest"
REPO = "sai-dau-sua-do"

# The generated site deploys to the gh-pages branch; main holds source
# and documentation. The default branch is never a deploy target.
TARGET_BRANCH = "gh-pages"

# Seed README, used only for a completely new repo with no commits.
# Normal deploys read the generated README.md from disk instead.
SEED_README = """# Sai Đâu Sửa Đó — Kho bài học

Kho tra cứu lỗi tiếng Anh người Việt hay mắc. Mỗi bài ghi một lỗi, cách nói đúng và ví dụ. Mỗi ngày sửa một lỗi nhỏ.

- Trang Facebook: https://www.facebook.com/profile.php?id=61596506009854
- Group: https://www.facebook.com/groups/4387154551501983
- Trang này chạy bằng GitHub Pages, sinh từ `lessons.json` bằng `generate_site.py`.
"""

def site_files():
    """Every file the site serves: homepage, data file, one page per
    lesson and all artwork. The push always carries the full tree;
    never push a single file."""
    src = Path(SRC)
    out = ["index.html", "lessons.json", "README.md"]
    for extra in ["favicon.svg", "sitemap.xml", "robots.txt", "CNAME", ".nojekyll",
                  "LICENSE", "LICENSE-CONTENT.md"]:
        if (src / extra).exists():
            out.append(extra)
    # Shared files: CSS, JS, data, and the search index.
    # Đợt hướng A: skills.js (dữ liệu 4 trang kỹ năng), reading.js
    # (đoạn văn đọc). Mục Cộng đồng nối API thật nên không còn file mock.
    for extra in ["styles.css", "app.js", "data.js", "search-index.json",
                  "skills.js", "reading.js"]:
        if (src / extra).exists():
            out.append(extra)
    # Public API: static JSON files under api/v1/ and the OpenAPI definition.
    # The api/index.html docs page is included by the directory loop below.
    for f in sorted((src / "api" / "v1").glob("*.json")):
        out.append(f"api/v1/{f.name}")
    for f in sorted((src / "api" / "v1" / "lessons").glob("*.json")):
        out.append(f"api/v1/lessons/{f.name}")
    if (src / "api" / "openapi.yaml").exists():
        out.append("api/openapi.yaml")
    # Free study guides: keep these in every deploy, or the full-tree
    # push removes them from the repo.
    for extra in ["giao-trinh/tieng-anh-doi-thuong.pdf",
                  "giao-trinh/200-tu-vung-doi-song-hang-ngay.pdf"]:
        if (src / extra).exists():
            out.append(extra)
    for f in sorted((src / "fonts").glob("*.woff2")):
        out.append(f"fonts/{f.name}")
    for d in sorted(src.iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            out.append(f"{d.name}/index.html")
        if d.name == "lo-trinh":
            for sub in sorted(d.iterdir()):
                if sub.is_dir() and (sub / "index.html").exists():
                    out.append(f"lo-trinh/{sub.name}/index.html")
    for img in sorted((src / "images").glob("*.jpg")) + sorted((src / "images").glob("*.png")):
        out.append(f"images/{img.name}")
    return out


COMMIT_MESSAGE = (
    "Kho bài học — wizard từng bước + chế độ tối + màn hình hoàn thành "
    "và chuỗi ngày học (9 bài, không lặp câu)"
)


def read_message():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", default=COMMIT_MESSAGE)
    return ap.parse_args().message


FILES = site_files()

me = api("GET", "/user")
assert me["login"] == OWNER, me["login"]
print("owner:", OWNER)

try:
    repo = api("GET", f"/repos/{OWNER}/{REPO}")
    print("repo already exists:", repo["html_url"])
except GitHubError as e:
    if e.status != 404:
        raise
    repo = api("POST", "/user/repos", {
        "name": REPO,
        "description": "Kho bài học Sai Đâu Sửa Đó — tra cứu lỗi tiếng Anh người Việt hay mắc.",
        "private": False,
        "auto_init": False,
    })
    print("created:", repo["html_url"])

branch = TARGET_BRANCH

try:
    api("PUT", f"/repos/{OWNER}/{REPO}/topics",
        {"names": ["english-learning", "vietnamese", "notion-alternative"]})
except GitHubError as e:
    print("topics skipped:", e)

def repo_has_commits():
    try:
        commits = api("GET", f"/repos/{OWNER}/{REPO}/commits?per_page=1")
        return len(commits) > 0
    except GitHubError as e:
        if e.status == 409:
            return False
        raise

parents = []
if not repo_has_commits():
    seed = api("PUT", f"/repos/{OWNER}/{REPO}/contents/README.md",
               {"message": "seed README", "content": base64.b64encode(SEED_README.encode("utf-8")).decode("ascii"), "branch": branch})
    parents = [seed["commit"]["sha"]]
    print("seeded initial commit:", parents[0])
else:
    head = api("GET", f"/repos/{OWNER}/{REPO}/commits/{branch}")
    parents = [head["sha"]]
    print("existing head:", parents[0])

# L-10: kiểm tra mọi file tồn tại TRƯỚC khi tạo blob nào.
missing = [rel for rel in FILES if not os.path.exists(os.path.join(SRC, rel))]
if missing:
    print("THIẾU FILE, chưa đẩy gì:", missing, file=sys.stderr)
    sys.exit(1)

# Tối ưu B (19/11): deploy thông minh — đọc cây remote 1 lần, file nào có
# SHA blob trùng với remote thì tái dùng luôn, không POST blob mới.
# Cây commit vẫn đẩy đủ (full tree, không force-push) nên hoàn tác bằng
# undo_deploy.py vẫn chạy như cũ; nếu không đọc được cây remote thì đẩy
# toàn bộ blob như trước (đường lui an toàn).
def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


remote_tree = {}
if repo_has_commits():
    try:
        head_sha = api("GET", f"/repos/{OWNER}/{REPO}/commits/{branch}")["sha"]
        tree = api("GET", f"/repos/{OWNER}/{REPO}/git/trees/{head_sha}?recursive=1")
        remote_tree = {t["path"]: t["sha"] for t in tree.get("tree", [])
                       if t.get("type") == "blob"}
    except GitHubError as e:
        print("không đọc được cây remote, sẽ đẩy toàn bộ blob:", e)

# H-10: cảnh báo file trên repo nằm ngoài danh sách sẽ bị xóa sau lần đẩy này.
if remote_tree:
    extra = [p for p in remote_tree if p not in FILES]
    if extra:
        print("CẢNH BÁO: các file sau có trên repo nhưng KHÔNG nằm trong danh sách deploy, sẽ bị xóa:", extra)

entries = []
n_reused = 0
n_uploaded = 0
for rel in FILES:
    path = os.path.join(SRC, rel)
    with open(path, "rb") as f:
        raw = f.read()
    sha = git_blob_sha(raw)
    if remote_tree.get(rel) == sha:
        entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": sha})
        n_reused += 1
        print("reuse:", rel)
        continue
    blob = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs",
               {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"})
    entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    n_uploaded += 1
    print("blob:", rel)
print(f"blob: {n_uploaded} mới, {n_reused} tái dùng")

tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"tree": entries})
message = read_message()
commit = api("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
    "message": message,
    "tree": tree["sha"],
    "parents": parents,
})

try:
    ref = api("POST", f"/repos/{OWNER}/{REPO}/git/refs",
              {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
except GitHubError as e:
    if e.status != 422:
        raise
    ref = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{branch}",
              {"sha": commit["sha"], "force": False})

print("pushed:", ref["object"]["sha"])
print("repo:", f"https://github.com/{OWNER}/{REPO}")

# Enable GitHub Pages (source: gh-pages branch, root)
try:
    pages = api("GET", f"/repos/{OWNER}/{REPO}/pages")
    print("pages already enabled:", pages.get("html_url"), "status:", pages.get("status"))
except GitHubError as e:
    if e.status != 404:
        raise
    pages = api("POST", f"/repos/{OWNER}/{REPO}/pages",
                {"source": {"branch": branch, "path": "/"}})
    print("pages enabled:", pages.get("html_url"), "status:", pages.get("status"))

print("live url:", f"https://{OWNER.lower()}.github.io/{REPO}/")

# Deploy log: one line per push (date, commit, message) so "hoàn tác"
# can move the branch back to the previous commit.
import datetime
log_path = Path(SRC) / "DEPLOY_LOG.md"
prev_sha = parents[0] if parents else ""
line = (f"- {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%Y-%m-%d %H:%M')} "
        f"+07 | {commit['sha']} | prev {prev_sha} | {message}\n")
if log_path.exists():
    log_path.write_text(log_path.read_text(encoding="utf-8") + line, encoding="utf-8")
else:
    log_path.write_text("# Nhật ký đẩy trang (mới nhất cuối file)\n\n" + line, encoding="utf-8")
print("logged to DEPLOY_LOG.md:", line.strip())
