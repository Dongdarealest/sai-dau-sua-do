#!/bin/bash
# node --check cho mọi khối <script> trong HTML đã sinh.
# Chạy từ thư mục web/:  bash tests/check_js.sh
# Trích từng khối script ra file tạm rồi chạy node --check; lỗi nào cũng fail.
set -u
cd "$(dirname "$0")/.." || exit 1
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
python3 - "$TMP" <<'PYEOF'
import re, glob, sys
from pathlib import Path
out = Path(sys.argv[1])
n = 0
for f in sorted(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('lo-trinh/*/index.html')):
    html = open(f, encoding='utf-8').read()
    blocks = re.findall(r'<script>(.*?)</script>', html, re.S)
    name = Path(f).parent.name
    if name == '.':
        name = 'index'
    elif 'lo-trinh' in f:
        name = 'lo-trinh-' + name
    for i, b in enumerate(blocks):
        (out / f'{name}-{i}.js').write_text(b, encoding='utf-8')
        n += 1
print(f"extracted {n} script blocks")
PYEOF
fail=0
ok=0
for f in "$TMP"/*.js; do
  if node --check "$f" >"$TMP/err.txt" 2>&1; then
    ok=$((ok+1))
  else
    fail=$((fail+1))
    echo "FAIL: $f"
    head -8 "$TMP/err.txt"
  fi
done
echo "node --check: OK=$ok FAIL=$fail"
# File JS dùng chung (tối ưu A): kiểm tra trực tiếp, vì <script src> không
# nằm trong các khối <script> trích ở trên.
for f in app.js data.js; do
  if node --check "$f" >"$TMP/err.txt" 2>&1; then
    ok=$((ok+1))
  else
    fail=$((fail+1))
    echo "FAIL: $f"
    head -8 "$TMP/err.txt"
  fi
done
# Chỉ mục tìm kiếm phải là JSON hợp lệ.
if python3 -c "import json; json.load(open('search-index.json', encoding='utf-8'))" 2>"$TMP/err.txt"; then
  ok=$((ok+1))
else
  fail=$((fail+1))
  echo "FAIL: search-index.json không phải JSON hợp lệ"
  head -8 "$TMP/err.txt"
fi
echo "node --check + JSON: OK=$ok FAIL=$fail"
[ "$fail" -eq 0 ]
