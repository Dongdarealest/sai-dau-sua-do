"""Deploy the Sai Dau Sua Do lesson library to GitHub Pages.

CẢNH BÁO (15/11/2026): file này KHÔNG có `if __name__ == "__main__"` — toàn bộ
code deploy chạy ở top-level, nên `import deploy_github_pages` (kể cả chỉ để lấy
site_files()) sẽ ĐẨY NGAY một commit lên GitHub. Đã xảy ra 1 lần do import nhầm
trong lúc kiểm tra song song (commit 5003a53 thiếu ảnh, phải hoàn tác). KHÔNG BAO
GIỜ import file này — chỉ chạy bằng dòng lệnh:
    python3 deploy_github_pages.py --message "..."

Safe pattern (from push_tubeeq.py + AGENTS.md lesson 16/10/2026):
- full tree push (index.html + README.md), never a single stray file
- commit ALWAYS has the real parent (seed commit on a fresh repo,
  current head on an existing repo) — never parents=[] + force-push
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

# Tách nhánh 19/11/2026: web đã sinh đẩy lên nhánh gh-pages, main chỉ giữ
# mã nguồn và tài liệu. Không bao giờ dùng nhánh mặc định làm đích đẩy nữa.
TARGET_BRANCH = "gh-pages"

# Seed README — CHỈ dùng cho repo mới hoàn toàn chưa có commit nào (S-05).
# Mọi lần deploy bình thường đều đọc README.md đã sinh trên đĩa, không dùng hằng này.
SEED_README = """# Sai Đâu Sửa Đó — Kho bài học

Kho tra cứu lỗi tiếng Anh người Việt hay mắc. Mỗi bài ghi một lỗi, cách nói đúng và ví dụ. Mỗi ngày sửa một lỗi nhỏ.

- Trang Facebook: https://www.facebook.com/profile.php?id=61596506009854
- Group: https://www.facebook.com/groups/4387154551501983
- Trang này chạy bằng GitHub Pages, sinh từ `lessons.json` bằng `generate_site.py`.
"""

def site_files():
    """Every file the site serves: homepage, data file, one page per
    lesson and all artwork. The push ALWAYS carries the full tree
    (AGENTS.md lesson 16/10/2026: never push a single stray file)."""
    src = Path(SRC)
    out = ["index.html", "lessons.json", "README.md"]
    for extra in ["favicon.svg", "sitemap.xml", "robots.txt", "CNAME", ".nojekyll",
                  "LICENSE", "LICENSE-CONTENT.md"]:
        if (src / extra).exists():
            out.append(extra)
    # File dùng chung (tối ưu A, 19/11): CSS + JS + dữ liệu + chỉ mục tìm kiếm.
    for extra in ["styles.css", "app.js", "data.js", "search-index.json"]:
        if (src / extra).exists():
            out.append(extra)
    # API mở (19/11): toàn bộ file JSON tĩnh dưới api/v1/ + định nghĩa OpenAPI.
    # Trang tài liệu api/index.html đã nằm trong danh sách qua vòng lặp thư mục
    # có index.html ở dưới. Không đổi đường dẫn bài học cũ.
    for f in sorted((src / "api" / "v1").glob("*.json")):
        out.append(f"api/v1/{f.name}")
    for f in sorted((src / "api" / "v1" / "lessons").glob("*.json")):
        out.append(f"api/v1/lessons/{f.name}")
    if (src / "api" / "openapi.yaml").exists():
        out.append("api/openapi.yaml")
    # Giáo trình tặng (16/11/2026): giữ file này trong mọi lần deploy,
    # nếu không lần deploy cây đầy đủ sẽ xóa nó khỏi repo.
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
