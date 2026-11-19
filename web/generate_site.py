#!/usr/bin/env python3
"""Generate the Sai Dau Sua Do lesson library from lessons.json (single source).

Generated pages:
  index.html               trang chủ: Học hôm nay, tiến độ, 3 lộ trình,
                           Ôn hôm nay, nút vào Group / gửi câu, tab Học / Tra cứu
  lo-trinh/<slug>/         trang 1 lộ trình (danh sách bài theo thứ tự)
  <slug>/index.html        trang bài theo khuôn cố định (mở đầu, Sai→Đúng,
                           Vì sao ≤2 câu, nghe, luyện chấm ngay, Nhớ điều này,
                           Đã nhớ, Bài tiếp theo) + thẻ OG để chia sẻ Facebook
  lessons.json             tệp dữ liệu duy nhất (được đẩy lên cùng site)
  images/<slug>.jpg        ảnh bài học, JPEG tối ưu (dùng làm og:image)
  README.md                sinh từ cùng 1 dữ liệu (số bài luôn đồng bộ)

Run after every new post: python3 update_site.py --lesson new-lesson.json
(or just `python3 generate_site.py` to rebuild from lessons.json).
"""
import datetime
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parent
BASE_PATH = "/sai-dau-sua-do"
SITE_URL = "https://dongdarealest.github.io/sai-dau-sua-do"



def _svg(inner):
    return ('<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">' + inner + '</svg>')


ICON = {
    "speaker": _svg('<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/>'),
    "book": _svg('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'),
    "map": _svg('<circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/>'),
    "cap": _svg('<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/>'),
    "case": _svg('<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>'),
    "users": _svg('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
    "mail": _svg('<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>'),
    "star": _svg('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'),
    "share": _svg('<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98"/>'),
    "moon": _svg('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
    "sun": _svg('<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>'),
    "flame": _svg('<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>'),
    "search": _svg('<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'),
    "bookmark": _svg('<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'),
}


PATH_ICONS = {"hoc-lai-tu-dau": "cap", "tieng-anh-di-lam": "case", "sua-phat-am": "speaker"}

def esc(s):
    return html.escape(str(s), quote=True)


def fmt_date(s):
    """YYYY-MM-DD -> DD/MM/YYYY. Ngay hien thi khong dung gach ngang."""
    try:
        y, m, d = str(s).split("-")
        return f"{d}/{m}/{y}"
    except Exception:
        return str(s or "")


CSS = """
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:400;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-400-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:400;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-400-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:400;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-400-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:600;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-600-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:600;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-600-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:600;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-600-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:700;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-700-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:700;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-700-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:700;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-700-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:900;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-900-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:900;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-900-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Be Vietnam Pro';font-style:normal;font-weight:900;font-display:swap;src:url(/sai-dau-sua-do/fonts/be-vietnam-pro-900-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Inter';font-style:normal;font-weight:400;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-400-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Inter';font-style:normal;font-weight:400;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-400-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Inter';font-style:normal;font-weight:400;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-400-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Inter';font-style:normal;font-weight:600;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-600-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Inter';font-style:normal;font-weight:600;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-600-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Inter';font-style:normal;font-weight:600;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-600-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Inter';font-style:normal;font-weight:700;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-700-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Inter';font-style:normal;font-weight:700;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-700-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}
@font-face{font-family:'Inter';font-style:normal;font-weight:700;font-display:swap;src:url(/sai-dau-sua-do/fonts/inter-700-vietnamese.woff2) format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
:root{--navy:#173F5F;--navy-bg:#173F5F;--navy-btn:#173F5F;--mint:#DCEFEA;--orange:#F26B38;--ink:#1A202C;--sub:#2D3748;--bg:#F6F8F7;--card:#fff;--bar:#EDF2F7;--red-bg:#FDECEA;--red:#C0392B;--line:#E2E8F0;--green:#276749;--green-btn:#276749;--green-bg:#C6F6D5;--amber-bg:#FEFCBF;--amber:#744210}
[data-theme="dark"]{--navy:#8FC3E8;--navy-btn:#4A90C2;--navy-bg:#0F2A42;--mint:#17382F;--ink:#E8EEF4;--sub:#A9BCD0;--bg:#0E1B2A;--card:#16283F;--bar:#1C2F45;--red-bg:#3D1F1C;--red:#FF9D8A;--line:#2C4258;--green:#7FD8A8;--green-bg:#14332A;--amber-bg:#3A2E12;--amber:#F6C453}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Be Vietnam Pro","Inter",system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink);line-height:1.65;font-size:16px}
a{color:var(--navy)}
header{background:var(--navy-bg);color:#fff;padding:28px 20px 22px}
.wrap{max-width:1020px;margin:0 auto;padding:0 16px}
.brand{display:flex;gap:14px;align-items:center}
.logo{width:56px;height:56px;border-radius:14px;background:#fff;color:var(--navy-btn);font-weight:900;font-size:34px;display:flex;align-items:center;justify-content:center;position:relative;flex:none}
.logo::after{content:"✓";position:absolute;right:-7px;bottom:-9px;color:var(--orange);font-size:28px}
header h1{font-size:25px;line-height:1.25}
header h1 a{color:#fff;text-decoration:none}
header p.slogan{color:#DCEFEA;font-weight:600;margin-top:4px;font-size:16px}
header p.intro{color:#CBDCE8;margin-top:10px;max-width:640px;font-size:16px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.stat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:6px 14px;font-size:16px}
.stat.score{background:var(--orange);border-color:var(--orange);color:#fff;font-weight:700}
main{padding:0 0 8px}
section{margin:20px 0}
h2{font-size:22px;margin-bottom:12px}
h2 small{font-size:16px;color:var(--sub);font-weight:400}
.btn{display:inline-block;border-radius:14px;padding:16px 24px;min-height:48px;font-size:17px;font-weight:700;text-decoration:none;text-align:center;cursor:pointer;border:2px solid transparent}
.btn-primary{background:var(--orange);color:#fff}
.btn-navy{background:var(--navy-btn);color:#fff}
.btn-ghost{background:var(--card);color:var(--navy);border-color:var(--navy)}
.btn-block{display:block;width:100%}
.btn:active{transform:scale(.98)}
.today{background:var(--card);border:2px solid var(--navy);border-radius:16px;padding:20px}
.today h2{margin-bottom:6px}
.today p{font-size:16px;margin-bottom:12px}
.progress{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px}
.progress .bar{height:16px;background:var(--bar);border-radius:999px;overflow:hidden;margin:10px 0 6px}
.progress .bar i{display:block;height:100%;background:var(--orange);width:0%;border-radius:999px;transition:width .4s}
.progress p{font-size:16px}
.progress p b{color:var(--navy)}
.paths{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))}
.path-card{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:20px;display:flex;flex-direction:column;gap:10px;text-decoration:none;color:var(--ink)}
.path-card:hover{border-color:var(--navy)}
.path-card .num{font-size:40px;line-height:1}
.path-card h3{font-size:20px}
.path-card p{font-size:16px;color:var(--sub)}
.path-card .meta{font-size:16px;font-weight:700;color:var(--navy);margin-top:auto}
.review-grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(180px,1fr))}
.review-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;text-decoration:none;color:var(--ink);display:block}
.review-card:hover{border-color:var(--navy)}
.review-card b{display:block;font-size:16px;margin-bottom:2px}
.review-card span{font-size:16px;color:var(--sub)}
.empty{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:22px;text-align:center;color:var(--sub);font-size:16px}
.cta-row{display:grid;gap:12px;grid-template-columns:1fr 1fr}
.tabs{display:flex;gap:8px;margin:20px 0 0}
.tab{flex:1;border:2px solid var(--line);background:var(--card);border-radius:14px 14px 0 0;border-bottom:0;padding:14px;font-size:17px;font-weight:700;cursor:pointer;color:var(--sub)}
.tab.on{background:var(--navy-btn);color:#fff;border-color:var(--navy-btn)}
.tabpanel{background:var(--card);border:2px solid var(--line);border-radius:0 0 16px 16px;padding:18px}
.toolbar{display:flex;flex-direction:column;gap:10px;margin-bottom:14px}
#search{width:100%;padding:13px 15px;font-size:16px;border:2px solid var(--line);border-radius:12px;outline:none;background:var(--card);color:var(--ink)}
#search:focus{border-color:var(--navy)}
input::placeholder{color:var(--sub);opacity:1}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.filter-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.filter-row select{padding:12px;border:2px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);font-size:16px;min-height:48px}
.filter-row label{font-size:16px;font-weight:700}
.wo-chip{border:2px solid var(--line);background:var(--card);border-radius:999px;padding:10px 16px;min-height:48px;font-size:16px;cursor:pointer;margin:4px}
.wo-chip:disabled{opacity:.45;cursor:default}
.wo-chip.picked{background:var(--mint);border-color:var(--navy)}
.wo-picked{min-height:56px;border:2px dashed var(--line);border-radius:12px;padding:8px;margin:10px 0}
.wo-empty{color:var(--sub);font-size:16px}
.wo-answer{font-size:16px;font-weight:700;color:var(--navy);margin-top:10px}
.selfgrade{border:2px solid var(--line);background:var(--card);border-radius:12px;padding:13px 16px;min-height:48px;font-size:16px;cursor:pointer;flex:1}
.selfgrade.on{background:var(--navy-btn);color:#fff;border-color:var(--navy-btn)}
.selfgrade-row{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.done-list ul,.recent-list ul,.stats-list ul{list-style:none;display:grid;gap:8px}
.done-list li,.recent-list li,.stats-list li{font-size:16px}
.import-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:12px}
.import-row label{font-size:16px}
#import-msg{font-size:16px;width:100%}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{border:1.5px solid var(--line);background:var(--card);border-radius:999px;padding:8px 14px;min-height:48px;font-size:16px;cursor:pointer;display:inline-flex;align-items:center}
.chip.on{background:var(--navy-btn);color:#fff;border-color:var(--navy-btn)}
.viewtoggle{margin-left:auto;display:flex;border:1.5px solid var(--line);border-radius:999px;overflow:hidden}
.viewtoggle button{border:0;background:var(--card);padding:8px 15px;min-height:48px;font-size:16px;cursor:pointer}
.viewtoggle button.on{background:var(--navy-btn);color:#fff}
#count{color:var(--sub);font-size:16px;margin:4px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px}
.card h3{font-size:18px}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{color:var(--navy);text-decoration:underline}
.tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{font-size:16px;font-weight:700;border-radius:999px;padding:3px 10px;background:var(--bar);color:var(--sub);white-space:nowrap}
.tag.topic{background:var(--mint);color:var(--navy)}
.box{border-radius:12px;padding:12px 14px;margin:10px 0}
.box small{display:block;font-size:16px;font-weight:700;letter-spacing:.04em;margin-bottom:2px}
.box.wrong{background:var(--red-bg);color:var(--red)}
.box.right{background:var(--mint);color:var(--navy)}
.box p{font-size:17px;font-weight:600}
.explain{font-size:16px}
.explain b{color:var(--navy)}
.example{font-size:16px;color:var(--sub);background:var(--bg);border-radius:12px;padding:11px 13px;white-space:pre-line}
.ipa{font-size:16px;color:var(--sub)}
.ipa b{color:var(--navy)}
.meta{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:auto;padding-top:4px}
.meta time{font-size:16px;color:var(--sub)}
.meta a{font-size:16px;font-weight:700;text-decoration:none;white-space:nowrap}
.meta a:hover{text-decoration:underline}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:16px}
th,td{border-bottom:1px solid var(--line);padding:11px 12px;text-align:left;vertical-align:top}
th{background:var(--navy-btn);color:#fff;font-size:16px;letter-spacing:.03em}
tr:last-child td{border-bottom:0}
td .wrong{color:var(--red);font-weight:600}
td .right{color:var(--navy);font-weight:600}
.tablewrap{overflow-x:auto;border-radius:14px;border:1px solid var(--line);margin-bottom:8px;background:var(--card)}
.listen{display:inline-flex;align-items:center;gap:6px;border:1.5px solid var(--navy);background:var(--card);color:var(--navy);border-radius:999px;padding:7px 13px;min-height:48px;min-width:48px;justify-content:center;font-size:16px;font-weight:700;cursor:pointer;margin-left:8px;vertical-align:middle}
.listen:hover{background:var(--navy-btn);color:#fff}
.listen.playing{background:var(--orange);border-color:var(--orange);color:#fff}
.dicts{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.dicts a{font-size:16px;font-weight:700;text-decoration:none;border:1.5px solid var(--line);border-radius:999px;padding:6px 13px;min-height:48px;display:inline-flex;align-items:center;background:var(--card)}
.dicts a:hover{border-color:var(--navy)}
.ask{font-size:19px;margin:16px 0 4px}
.origin{margin:24px 0 4px;border-top:2px solid var(--line);padding-top:16px}
.origin h3{font-size:18px;margin-bottom:6px}
.originimg{max-width:320px;width:100%;border-radius:12px;border:1px solid var(--line);display:block;margin:10px 0}
.step{margin:18px 0}
.step h3{font-size:18px;margin-bottom:8px}
.step h3 span{color:var(--orange)}
.remember{background:var(--amber-bg);border:2px solid var(--amber);border-radius:14px;padding:16px 18px;margin:18px 0}
.remember b{color:var(--amber);font-size:17px}
.grade{background:var(--card);border:2px solid var(--navy);border-radius:14px;padding:18px;margin:14px 0}
.grade h3{font-size:18px;margin-bottom:4px}
.grade .q{font-size:17px;font-weight:700;margin:8px 0 12px}
.grade .prompt{font-size:16px;background:var(--bg);border-radius:10px;padding:11px 13px;margin-bottom:12px}
.opts{display:grid;gap:10px}
.opt{display:flex;gap:10px;align-items:center;text-align:left;border:2px solid var(--line);background:var(--card);border-radius:12px;padding:13px 15px;min-height:48px;font-size:16px;cursor:pointer;width:100%}
.opt:hover{border-color:var(--navy)}
.opt .letter{font-weight:900;background:var(--bg);border-radius:8px;width:30px;height:30px;flex:none;display:flex;align-items:center;justify-content:center}
.opt.correct{border-color:var(--green);background:var(--green-bg)}
.opt.wrong-pick{border-color:var(--red);background:var(--red-bg)}
.opt:disabled{cursor:default;opacity:.92}
.grade-result{margin-top:14px;border-radius:10px;padding:12px 14px;font-size:16px;display:none}
.grade-result.good{background:var(--green-bg);color:var(--green)}
.grade-result.bad{background:var(--red-bg);color:var(--red)}
.grade-result b{display:block;font-size:17px;margin-bottom:2px}
.grade-retry{margin-top:10px;border:1.5px solid var(--line);background:var(--card);border-radius:999px;padding:8px 16px;min-height:48px;font-size:16px;cursor:pointer}
.practice-score{font-size:16px;font-weight:700;color:var(--navy);margin-top:6px}
.pagenav{display:flex;justify-content:space-between;gap:12px;margin:16px 0 8px}
.pagenav a{background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:12px 15px;text-decoration:none;font-size:16px;flex:1}
.pagenav a:hover{border-color:var(--navy)}
.pagenav .next{text-align:right}
.pagenav small{display:block;color:var(--sub);font-size:16px}
.back{font-size:16px;font-weight:700;text-decoration:none}
.path-list{display:grid;gap:12px}
.path-item{background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:16px 18px;display:flex;gap:14px;align-items:center;text-decoration:none;color:var(--ink)}
.path-item:hover{border-color:var(--navy)}
.path-item .n{font-size:24px;font-weight:900;color:var(--navy);flex:none;width:36px;height:36px;border-radius:50%;background:var(--mint);display:flex;align-items:center;justify-content:center}
.path-item.done .n{background:var(--green-bg);color:var(--green)}
.path-item h3{font-size:18px}
.path-item p{font-size:16px;color:var(--sub)}
.path-item .go{margin-left:auto;font-weight:700;white-space:nowrap;font-size:16px}
footer{background:var(--navy-bg);color:#CBDCE8;margin-top:28px;padding:24px 20px;font-size:16px}
footer a{color:#fff;font-weight:700}

.ic{width:1.15em;height:1.15em;flex:none;vertical-align:-0.18em}
.brand{justify-content:space-between}
.theme-toggle{flex:none;width:48px;height:48px;border-radius:50%;border:1.5px solid rgba(255,255,255,.4);background:rgba(255,255,255,.12);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center}
.theme-toggle .ic{width:22px;height:22px}
.wiz-progress{display:flex;align-items:center;gap:12px;margin:18px 0 4px}
.wiz-bar{flex:1;height:10px;background:var(--bar);border-radius:999px;overflow:hidden}
.wiz-bar i{display:block;height:100%;background:var(--orange);width:0%;border-radius:999px;transition:width .35s ease}
.wiz-progress span{font-size:16px;font-weight:700;color:var(--navy);white-space:nowrap}
.wstep{animation:fadein .25s ease}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.wiz-bottom{position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--card);border-top:1.5px solid var(--line);padding:10px 0 calc(10px + env(safe-area-inset-bottom,0px))}
.wiz-bottom-inner{display:flex;gap:10px;align-items:center}
.wiz-bottom .btn{min-height:52px}
#wizPrev{flex:0 0 auto}
#wizNext{flex:1}
.has-wiz main{padding-bottom:120px}
.grade-result{animation:pop .25s ease}
.grade-result.bad{animation:shake .3s ease}
@keyframes pop{from{transform:scale(.97);opacity:.5}to{transform:scale(1);opacity:1}}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)}}
.opt.correct::after{content:" ✓";color:var(--green);font-weight:900;margin-left:auto}
.opt.wrong-pick::after{content:" ✗";color:var(--red);font-weight:900;margin-left:auto}
.grade-result.good b::before{content:"✓ "}
.grade-result.bad b::before{content:"✗ "}
.complete{background:var(--card);border:2px solid var(--navy);border-radius:16px;padding:28px 20px;text-align:center;margin:18px 0}
.complete .complete-icon{width:72px;height:72px;border-radius:50%;background:var(--mint);color:var(--navy);display:flex;align-items:center;justify-content:center;margin:0 auto 14px}
.complete .complete-icon .ic{width:36px;height:36px}
.complete h3{font-size:24px;margin-bottom:8px}
.complete p{font-size:16px;color:var(--sub)}
.complete .pair{font-size:18px;font-weight:700;color:var(--ink);margin:10px 0}
.complete-actions{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 10px}
.complete-actions .btn{flex:1;min-width:200px}
.complete-note{font-size:16px}
.streak{font-size:16px}
@media(max-width:560px){.complete-actions .btn{min-width:0}}

@media(max-width:380px){.wrap{padding:0 12px}.paths{grid-template-columns:1fr}.grid{grid-template-columns:minmax(0,1fr)}}
@media(max-width:560px){
  header h1{font-size:22px}
  .viewtoggle{margin-left:0}
  .cta-row{grid-template-columns:1fr}
  .pagenav{flex-direction:column}
  .opening p{font-size:18px}
}
.sitenav{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
.sitenav a{color:#fff;background:rgba(255,255,255,.12);border:1.5px solid rgba(255,255,255,.25);border-radius:999px;padding:9px 16px;min-height:48px;display:inline-flex;align-items:center;font-size:16px;font-weight:700;text-decoration:none}
.sitenav a:hover{background:rgba(255,255,255,.24)}
.stat-tiles{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr))}
.tile{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px}
.tile .num{font-size:32px;font-weight:900;color:var(--navy);line-height:1.2}
.tile .lbl{font-size:16px;color:var(--sub);margin-top:4px}
.tile .sub2{font-size:16px;margin-top:8px}
.note{background:var(--mint);border:2px solid var(--navy);border-radius:14px;padding:14px 16px;font-size:16px;margin:14px 0}
.note.warn{background:var(--amber-bg);border-color:var(--amber)}
.chunk-box{background:var(--card);border:2px solid var(--navy);border-radius:16px;padding:20px;margin:14px 0}
.chunk-progress{font-size:16px;font-weight:700;color:var(--navy)}
.chunk-en{font-size:22px;font-weight:700;line-height:1.4;margin:10px 0 6px}
.chunk-vi{font-size:16px;color:var(--sub)}
.chunk-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;align-items:center}
.chunk-actions .btn{flex:1;min-width:140px}
.dict-search{display:flex;gap:10px;flex-wrap:wrap}
.dict-search input{flex:1;min-width:200px;padding:13px 15px;font-size:16px;border:2px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink)}
.dict-search input:focus{border-color:var(--navy);outline:none}
.dict-pos{font-size:18px;font-weight:700;color:var(--navy);margin:14px 0 6px}
.dict-def{font-size:16px;margin:6px 0}
.dict-ex{font-size:16px;color:var(--sub);background:var(--bg);border-radius:10px;padding:9px 12px;margin:4px 0 10px}
.dict-sec{font-size:18px;font-weight:700;color:var(--navy);margin:18px 0 4px;border-top:1px solid var(--line);padding-top:14px}
.dict-word{font-size:28px}
.dict-phon{margin:6px 0;overflow-wrap:anywhere}
.dict-vi{font-size:22px;font-weight:700;color:var(--navy);margin:2px 0 10px}
.dict-def-en{font-size:16px;color:var(--sub);margin:6px 0}
.dict-mt{font-size:16px;color:var(--sub);margin:2px 0 8px}
.dict-ex-vi{font-size:16px;margin:4px 0 10px;color:var(--ink);font-weight:600}
.dict-tag{font-size:16px;color:var(--sub);margin:8px 0}
.dict-src{font-size:16px;margin-top:16px}
.dict-src-small{font-size:16px;color:var(--sub);margin-top:6px}
.audio-btn{display:inline-flex;align-items:center;gap:6px;border:1.5px solid var(--navy);background:var(--card);color:var(--navy);border-radius:999px;padding:7px 13px;min-height:48px;font-size:16px;font-weight:700;cursor:pointer;margin:4px 6px 4px 0}
.audio-btn:hover{background:var(--navy-btn);color:#fff}
.speak-score{font-size:40px;font-weight:900;line-height:1.1}
.speak-score.good{color:var(--green)}
.speak-score.mid{color:var(--amber)}
.speak-score.low{color:var(--red)}
.speak-heard{font-size:16px;background:var(--bg);border-radius:12px;padding:12px 14px;margin:12px 0}
.speak-target{font-size:22px;font-weight:700;line-height:1.4}
.rec-dot{display:inline-block;width:14px;height:14px;border-radius:50%;background:var(--red);margin-right:8px;vertical-align:middle}
.lib-group{margin:22px 0}
.lib-group h3{font-size:20px;margin-bottom:10px}
pre{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;overflow:auto;font-size:16px;line-height:1.55}
pre code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:16px}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:16px}
blockquote{border-left:4px solid var(--orange);margin:16px 0;padding:8px 16px;background:var(--card);border-radius:0 12px 12px 0;font-size:16px}
"""


def listen_btn(text):
    return ('<button type="button" class="listen" data-say="' + esc(text)
            + '" aria-label="Nghe phát âm">' + ICON["speaker"] + ' Nghe</button>')


def ipa_words(lesson):
    words = []
    for entry in lesson.get("ipa", []):
        for part in entry["text"].split("—"):
            m = re.match(r"\s*([A-Za-z]+)\s*/", part)
            if m and m.group(1) not in words:
                words.append(m.group(1))
    if lesson["slug"] == "loi-004" and "comfortable" not in words:
        words.insert(0, "comfortable")
    return words


SHARED_JS = r"""
<script>
/* Sai Đâu Sửa Đó: shared JS (progress v1 + SRS + safe storage).
   Mọi lần chạm localStorage/sessionStorage đều có try/catch + bộ nhớ tạm
   trong phiên, nên storage bị chặn cũng không giết trang (S-01). */
const DONE_KEY="sdsc-done-v2", PRAC_KEY="sdsc-practice-v2", STREAK_KEY="sdsc-streak-v1";
const PROGRESS_KEY="sdsc-progress-v1", PROGRESS_BAK=PROGRESS_KEY+".bak";
const CURRENT_VERSION=1;
let __mem={};
function storageGet(k){try{const v=localStorage.getItem(k);if(v!==null)return v;}catch(e){}return (k in __mem)?__mem[k]:null;}
function storageSet(k,v){try{localStorage.setItem(k,v);}catch(e){}try{__mem[k]=v;}catch(e2){}}
function storageRemove(k){try{localStorage.removeItem(k);}catch(e){}try{delete __mem[k];}catch(e2){}}
function sessionGet(k){try{const v=sessionStorage.getItem(k);if(v!==null)return v;}catch(e){}return (("s:"+k) in __mem)?__mem["s:"+k]:null;}
function sessionSet(k,v){try{sessionStorage.setItem(k,v);}catch(e){}try{__mem["s:"+k]=v;}catch(e2){}}
function todayISO(){const d=new Date();return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function isValidDateStr(s){if(typeof s!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const d=new Date(s+"T00:00:00");return !isNaN(d.getTime())&&d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0")===s;}
function fmtDate(s){if(!isValidDateStr(s))return s;const p=s.split("-");return p[2]+"/"+p[1]+"/"+p[0];}
function dispDate(s){if(isValidDateStr(s))return fmtDate(s);return String(s||"").replace(/-/g,"/");}
function addDays(dateStr,n){const d=new Date(dateStr+"T00:00:00");d.setDate(d.getDate()+n);return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function yesterdayISO(){return addDays(todayISO(),-1);}
function emptyProgress(){return {version:1,updatedAt:new Date().toISOString(),lessons:{},practice:{},streak:{count:0,lastDate:"",dates:[]},review:{},history:[],settings:{dailyGoal:1,remindReview:true}};}
function normalizeProgress(o){
  const p=emptyProgress();
  if(o&&typeof o==="object"){
    if(o.lessons&&typeof o.lessons==="object")p.lessons=o.lessons;
    if(o.practice&&typeof o.practice==="object")p.practice=o.practice;
    if(o.review&&typeof o.review==="object")p.review=o.review;
    if(Array.isArray(o.history))p.history=o.history.slice(-500);
    if(o.streak&&typeof o.streak==="object"){p.streak.count=(typeof o.streak.count==="number"&&o.streak.count>=0)?o.streak.count:0;p.streak.lastDate=isValidDateStr(o.streak.lastDate)?o.streak.lastDate:"";p.streak.dates=Array.isArray(o.streak.dates)?o.streak.dates.filter(isValidDateStr).slice(-30):[];}
    if(o.settings&&typeof o.settings==="object"){p.settings.dailyGoal=(typeof o.settings.dailyGoal==="number"&&o.settings.dailyGoal>=1)?o.settings.dailyGoal:1;p.settings.remindReview=o.settings.remindReview!==false;}
  }
  const keys=Object.keys(p.practice).sort((a,b)=>String((p.practice[b]||{}).lastAt||"").localeCompare(String((p.practice[a]||{}).lastAt||""))).slice(0,1000);
  const pr={};keys.forEach(k=>{pr[k]=p.practice[k];});p.practice=pr;
  return p;
}
function migrateLegacy(p){
  let migrated=false;
  try{
    const rawDone=storageGet(DONE_KEY);
    if(rawDone){const done=JSON.parse(rawDone);if(done&&typeof done==="object"){
      Object.entries(done).forEach(([slug,date])=>{
        if(!isValidDateStr(date))return;
        const orphan=!(window.SDSC_LESSONS&&window.SDSC_LESSONS[slug]);
        p.lessons[slug]={done:true,doneAt:date,lastStudiedAt:date,selfGrade:null,reviews:0};
        if(orphan)p.lessons[slug].orphan=true;
        p.review[slug]={interval:1,nextDue:addDays(date,1),ease:2.5,reps:0};
        migrated=true;
      });
    }}
  }catch(e){}
  try{
    const rawPr=storageGet(PRAC_KEY);
    if(rawPr){const pr=JSON.parse(rawPr);if(pr&&typeof pr==="object"){
      Object.entries(pr).forEach(([key,v])=>{
        if(typeof v==="boolean"){p.practice[key]={choice:null,correct:v,attempts:1,lastAt:null};migrated=true;}
        else if(v&&typeof v==="object"&&typeof v.correct==="boolean"){p.practice[key]={choice:(v.choice===undefined?null:v.choice),correct:v.correct,attempts:(typeof v.attempts==="number"&&v.attempts>=1)?v.attempts:1,lastAt:v.lastAt||null};migrated=true;}
      });
    }}
  }catch(e){}
  try{
    const rawSt=storageGet(STREAK_KEY);
    if(rawSt){const st=JSON.parse(rawSt);if(st&&typeof st==="object"){
      const last=(typeof st.last==="string"&&isValidDateStr(st.last))?st.last:"";
      if(last){p.streak={count:(typeof st.streak==="number"&&st.streak>=1)?st.streak:1,lastDate:last,dates:[last]};migrated=true;}
    }}
  }catch(e){}
  if(migrated){
    p.history.push({date:todayISO(),at:new Date().toISOString(),slug:"",action:"import",note:"migrated from sdsc-done-v2/sdsc-practice-v2/sdsc-streak-v1"});
  }
  return migrated;
}
let __progressCache=null;
function loadProgress(){
  if(__progressCache)return __progressCache;
  let raw=null;try{raw=storageGet(PROGRESS_KEY);}catch(e){}
  if(raw){
    try{const o=JSON.parse(raw);if(!o||typeof o!=="object"||o.version!==CURRENT_VERSION)throw new Error("bad version");__progressCache=normalizeProgress(o);return __progressCache;}
    catch(e){
      try{const bak=storageGet(PROGRESS_BAK);if(bak){const o2=JSON.parse(bak);if(o2&&typeof o2==="object"&&o2.version===CURRENT_VERSION){try{storageSet(PROGRESS_KEY+".corrupt."+Date.now(),raw);}catch(e2){}__progressCache=normalizeProgress(o2);return __progressCache;}}}catch(e2){}
      try{storageSet(PROGRESS_KEY+".corrupt."+Date.now(),raw);}catch(e2){}
      __progressCache=emptyProgress();return __progressCache;
    }
  }
  const p=emptyProgress();
  if(migrateLegacy(p))saveProgress(p);
  __progressCache=p;return p;
}
function getProgress(){return loadProgress();}
function saveProgress(p){
  try{p.updatedAt=new Date().toISOString();}catch(e){}
  try{if(Array.isArray(p.history))p.history=p.history.slice(-500);}catch(e){}
  try{
    const raw=JSON.stringify(p);
    storageSet(PROGRESS_BAK,raw);
    storageSet(PROGRESS_KEY,raw);
  }catch(e){}
  __progressCache=p;
}
function updateProgress(fn){const p=getProgress();try{fn(p);}catch(e){}saveProgress(p);return p;}
function srsNew(todayStr){return {interval:1,nextDue:addDays(todayStr,1),ease:2.5,reps:0};}
function srsUpdate(r,grade,todayStr){
  r=r||{interval:1,ease:2.5,reps:0};
  if(grade==="kho"){r.interval=1;r.ease=Math.max(1.3,Math.round((r.ease-0.2)*100)/100);r.reps=0;}
  else if(grade==="vua"){r.interval=Math.max(1,Math.round(r.interval*r.ease));r.reps=(r.reps||0)+1;}
  else{r.interval=Math.max(1,Math.round(r.interval*r.ease*1.3));r.ease=Math.min(2.5,Math.round((r.ease+0.1)*100)/100);r.reps=(r.reps||0)+1;}
  r.interval=Math.min(60,Math.max(1,r.interval));
  r.nextDue=addDays(todayStr,r.interval);
  return r;
}
function pushHistory(p,entry){try{p.history.push(entry);if(p.history.length>500)p.history=p.history.slice(-500);}catch(e){}}
function updateStreakIn(p,todayStr){
  const st=p.streak||{count:0,lastDate:"",dates:[]};
  if(st.lastDate===todayStr)return st;
  if(st.lastDate===addDays(todayStr,-1)){st.count=(st.count||0)+1;}else{st.count=1;}
  st.lastDate=todayStr;
  st.dates=st.dates||[];if(!st.dates.includes(todayStr))st.dates.push(todayStr);
  st.dates=st.dates.filter(isValidDateStr).sort().slice(-30);
  p.streak=st;return st;
}
function loadJSON(k){try{const v=storageGet(k);return v?JSON.parse(v)||{}:{};}catch(e){return{};}}
function saveJSON(k,v){try{storageSet(k,JSON.stringify(v));}catch(e){}}
function loadStreak(){const p=getProgress();return {streak:p.streak.count||0,last:p.streak.lastDate||""};}
function updateStreak(){const p=getProgress();const t=todayISO();updateStreakIn(p,t);saveProgress(p);return loadStreak();}
const ICON_MOON='<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
const ICON_SUN='<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
function syncThemeBtn(){try{const b=document.getElementById("theme-toggle");if(b)b.innerHTML=document.documentElement.dataset.theme==="dark"?ICON_SUN:ICON_MOON;}catch(e){}}
(function(){try{const t=storageGet("sdsc-theme");if(t){document.documentElement.dataset.theme=t;}else if(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches){document.documentElement.dataset.theme="dark";}}catch(e){}syncThemeBtn();})();
document.addEventListener("click",e=>{try{const b=e.target.closest("#theme-toggle");if(!b)return;const cur=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=cur;storageSet("sdsc-theme",cur);syncThemeBtn();}catch(err){}});
let __voices=[];
function loadVoices(){try{__voices=speechSynthesis.getVoices()||[];}catch(e){__voices=[];}}
try{if("speechSynthesis" in window){loadVoices();speechSynthesis.addEventListener("voiceschanged",loadVoices);}}catch(e){}
function speak(text,btn){
  if(!("speechSynthesis" in window)){if(btn){const old=btn.textContent;btn.textContent="Không có giọng đọc";setTimeout(()=>{btn.textContent=old;},2000);}return;}
  try{speechSynthesis.cancel();}catch(e){}
  const u=new SpeechSynthesisUtterance(text);u.lang="en-US";u.rate=0.9;
  if(!__voices.length)loadVoices();
  const v=__voices.find(v=>v.lang&&v.lang.toLowerCase().startsWith("en-us"));
  if(v)u.voice=v;
  if(btn){btn.classList.add("playing");const clear=()=>btn.classList.remove("playing");u.onend=clear;u.onerror=clear;setTimeout(clear,15000);}
  try{speechSynthesis.speak(u);}catch(e){if(btn)btn.classList.remove("playing");}
}
document.addEventListener("click",e=>{
  const b=e.target.closest(".listen");if(!b)return;
  speak(b.dataset.say,b);
});
function escapeHtml(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");}
function savePracticeResult(key,choice,correct){
  updateProgress(p=>{
    const old=p.practice[key]||{};
    p.practice[key]={choice:choice,correct:!!correct,attempts:(typeof old.attempts==="number"?old.attempts:0)+1,lastAt:new Date().toISOString()};
    pushHistory(p,{date:todayISO(),at:new Date().toISOString(),slug:key.split(":")[0],action:"practice",key:key,correct:!!correct});
  });
}
function gradeWidget(box,choice){
  const answer=parseInt(box.dataset.answer,10);
  const explain=box.dataset.explain||"";
  const key=box.dataset.key;
  const r=box.querySelector(".grade-result");
  if(isNaN(answer)){
    if(r){r.style.display="block";r.className="grade-result bad";r.innerHTML="<b>Không chấm được câu này</b> (thiếu đáp án, báo cho trang nhé).";}
    return;
  }
  box.querySelectorAll(".opt").forEach((o,i)=>{
    o.disabled=true;
    if(i===answer)o.classList.add("correct");
    if(i===choice&&choice!==answer)o.classList.add("wrong-pick");
  });
  /* S-02: hiện kết quả TRƯỚC, ghi storage sau. Ghi lỗi vẫn hiện kết quả. */
  if(r){
    r.style.display="block";
    r.className="grade-result "+(choice===answer?"good":"bad");
    r.innerHTML=(choice===answer?"<b>Đúng rồi</b> ":"<b>Chưa đúng: đáp án là "+String.fromCharCode(65+answer)+"</b> ")+escapeHtml(explain);
  }
  try{savePracticeResult(key,choice,choice===answer);}catch(e){}
  if(key.endsWith(":q")){const reveal=document.getElementById("answer-box");if(reveal)reveal.style.display="block";}
  updatePracticeScore();
}
function restoreGrade(box){
  const key=box.dataset.key;
  const saved=getProgress().practice[key];
  if(!saved||typeof saved.correct!=="boolean")return;
  const answer=parseInt(box.dataset.answer,10);
  if(isNaN(answer))return;
  box.querySelectorAll(".opt").forEach((o,i)=>{o.disabled=true;if(i===answer)o.classList.add("correct");if(saved.choice!==null&&saved.choice!==undefined&&i===saved.choice&&saved.choice!==answer)o.classList.add("wrong-pick");});
  const r=box.querySelector(".grade-result");
  if(r){
    r.style.display="block";
    r.className="grade-result "+(saved.correct?"good":"bad");
    if(saved.choice===null||saved.choice===undefined){r.innerHTML=(saved.correct?"<b>Bạn đã làm đúng (trước đây)</b> ":"<b>Bạn đã làm trước đây, đáp án là "+String.fromCharCode(65+answer)+"</b> ")+escapeHtml(box.dataset.explain||"");}
    else{r.innerHTML=(saved.correct?"<b>Bạn đã làm đúng</b> ":"<b>Bạn đã làm, đáp án là "+String.fromCharCode(65+answer)+"</b> ")+escapeHtml(box.dataset.explain||"");}
  }
  if(key.endsWith(":q")){const reveal=document.getElementById("answer-box");if(reveal)reveal.style.display="block";}
}
document.querySelectorAll(".grade").forEach(box=>{
  const key=box.dataset.key;
  box.querySelectorAll(".opt").forEach(o=>o.addEventListener("click",()=>gradeWidget(box,parseInt(o.dataset.i,10))));
  try{restoreGrade(box);}catch(e){}
  const retry=box.querySelector(".grade-retry");
  if(retry)retry.addEventListener("click",()=>{
    try{updateProgress(p=>{delete p.practice[key];});}catch(e){}
    const rr=box.querySelector(".grade-result");if(rr)rr.style.display="none";
    box.querySelectorAll(".opt").forEach(o=>{o.disabled=false;o.classList.remove("correct","wrong-pick");});
    if(key.endsWith(":q")){const reveal=document.getElementById("answer-box");if(reveal)reveal.style.display="none";}
    updatePracticeScore();
  });
});
/* ---- word_order: xếp từ thành câu ---- */
function initWordOrder(box){
  const key=box.dataset.key;
  let answer=[];try{answer=JSON.parse(box.dataset.answer||"[]");}catch(e){answer=[];}
  let options=[];try{options=JSON.parse(box.dataset.options||"[]");}catch(e){options=[];}
  const pickedEl=box.querySelector(".wo-picked"), chipsEl=box.querySelector(".wo-chips"),
        resultEl=box.querySelector(".grade-result"), ansEl=box.querySelector(".wo-answer"),
        checkBtn=box.querySelector(".wo-check"), retryBtn=box.querySelector(".wo-retry");
  let picked=[];
  function renderPicked(){
    pickedEl.innerHTML=picked.map(i=>'<button type="button" class="wo-chip picked" data-i="'+i+'">'+escapeHtml(options[i]!==undefined?options[i]:"")+'</button>').join("")||'<span class="wo-empty">Bấm các từ bên dưới theo đúng thứ tự…</span>';
    pickedEl.querySelectorAll(".wo-chip").forEach(b=>b.addEventListener("click",()=>{
      const idx=parseInt(b.dataset.i,10);picked=picked.filter(x=>x!==idx);
      const chip=chipsEl.querySelector('[data-i="'+idx+'"]');if(chip)chip.disabled=false;
      renderPicked();
    }));
  }
  function correctSentence(){return answer.map(i=>options[i]).join(" ").replace(/ ([?.!,])/g,"$1");}
  function showResult(correct){
    if(resultEl){resultEl.style.display="block";resultEl.className="grade-result "+(correct?"good":"bad");
      resultEl.innerHTML=(correct?"<b>Đúng rồi</b> ":"<b>Chưa đúng: câu đúng là:</b> ")+escapeHtml(box.dataset.explain||"");}
    if(ansEl){ansEl.style.display="block";ansEl.textContent="Câu đúng: "+correctSentence();}
  }
  chipsEl.querySelectorAll(".wo-chip").forEach(ch=>{
    ch.addEventListener("click",()=>{
      if(ch.disabled)return;
      const idx=parseInt(ch.dataset.i,10);
      picked.push(idx);ch.disabled=true;renderPicked();
    });
  });
  if(checkBtn)checkBtn.addEventListener("click",()=>{
    if(!picked.length)return;
    const correct=picked.length===answer.length&&picked.every((v,i)=>v===answer[i]);
    chipsEl.querySelectorAll(".wo-chip").forEach(c=>{c.disabled=true;});
    showResult(correct);
    try{savePracticeResult(key,picked.slice(),correct);}catch(e){}
    updatePracticeScore();
  });
  if(retryBtn)retryBtn.addEventListener("click",()=>{
    picked=[];renderPicked();
    chipsEl.querySelectorAll(".wo-chip").forEach(c=>{c.disabled=false;});
    if(resultEl)resultEl.style.display="none";
    if(ansEl)ansEl.style.display="none";
    try{updateProgress(p=>{delete p.practice[key];});}catch(e){}
    updatePracticeScore();
  });
  try{
    const saved=getProgress().practice[key];
    if(saved&&typeof saved.correct==="boolean"&&Array.isArray(saved.choice)){
      picked=saved.choice.slice();renderPicked();
      chipsEl.querySelectorAll(".wo-chip").forEach(c=>{c.disabled=true;});
      showResult(saved.correct);
    }else{renderPicked();}
  }catch(e){renderPicked();}
}
document.querySelectorAll(".grade-wo").forEach(initWordOrder);
function practiceTotalsFor(slug){
  const p=getProgress();
  let total=0,done=0,right=0;
  const totals=(window.SDSC_TOTALS||{});
  total=totals[slug]||0;
  Object.entries(p.practice||{}).forEach(([k,v])=>{
    if(k===slug+":q"||k.indexOf(slug+":")===0){done++;if(v&&v.correct)right++;}
  });
  return {right: right,total: total,done: done};
}
function updatePracticeScore(){
  let siteRight=0,siteDone=0;
  try{const p=getProgress();Object.values(p.practice||{}).forEach(v=>{siteDone++;if(v&&v.correct)siteRight++;});}catch(e){}
  const siteTotal=window.SDSC_TOTAL_GRADED||0;
  document.querySelectorAll(".practice-score-num").forEach(el=>{
    const slug=el.dataset.slug;
    if(slug){const t=practiceTotalsFor(slug);el.textContent=t.right+" / "+t.total+" câu đúng ("+t.done+" đã làm), bài này";}
    else{el.textContent=siteRight+" / "+siteTotal+" câu đúng ("+siteDone+" đã làm), toàn trang";}
  });
  document.querySelectorAll(".practice-site-num").forEach(el=>{el.textContent=siteRight+" / "+siteTotal+" câu đúng ("+siteDone+" đã làm)";});
}
updatePracticeScore();
window.addEventListener("storage",e=>{
  if(e&&e.key===PROGRESS_KEY){try{__progressCache=null;loadProgress();}catch(err){}try{if(window.__sdscRenderProgress)window.__sdscRenderProgress();}catch(err){}try{updatePracticeScore();}catch(err){}}
});
/* ---- xuất / nhập tiến độ (§2.3) ---- */
function validImportDate(s){if(!isValidDateStr(s))return false;const d=new Date(s+"T00:00:00");const max=new Date();max.setDate(max.getDate()+1);max.setHours(23,59,59,999);return d.getTime()<=max.getTime();}
function validImportNextDue(s){if(!isValidDateStr(s))return false;const d=new Date(s+"T00:00:00");const max=new Date();max.setDate(max.getDate()+60);max.setHours(23,59,59,999);return d.getTime()<=max.getTime();}
function validateImportFile(text){
  let obj;
  try{obj=JSON.parse(text);}catch(e){return {ok:false,error:"File không phải JSON hợp lệ (lỗi ở ký tự "+(e&&e.message?e.message:"không rõ")+"). Kiểm tra lại file đã tải về."};}
  if(!obj||typeof obj!=="object"||obj.app!=="sai-dau-sua-do"||obj.kind!=="progress-export"){return {ok:false,error:"Đây không phải file tiến độ của Sai Đâu Sửa Đó (thiếu app/kind đúng)."};}
  const data=obj.data;
  if(!data||typeof data!=="object")return {ok:false,error:"Trường 'data' phải là object, nhận được "+(Array.isArray(data)?"array":typeof data)+"."};
  if(typeof data.version!=="number"||!Number.isInteger(data.version))return {ok:false,error:"File được xuất từ phiên bản không hỗ trợ (version không hợp lệ)."};
  if(data.version>CURRENT_VERSION)return {ok:false,error:"File được xuất từ phiên bản mới hơn (v"+data.version+"), trang này mới hỗ trợ tới v"+CURRENT_VERSION+". Cập nhật trang rồi nhập lại."};
  if(data.version<1)return {ok:false,error:"Không chuyển đổi được dữ liệu cũ (v"+data.version+"): phiên bản quá cũ."};
  const lessons=(window.SDSC_LESSONS||{});
  const badSlug=[];
  function checkSlug(s){if(!s||typeof s!=="string")return false;if(lessons[s])return true;return /^[a-z0-9-]+$/.test(s);}
  ["lessons","practice","review"].forEach(f=>{if(data[f]!==undefined&&(!data[f]||typeof data[f]!=="object"||Array.isArray(data[f])))return;});
  if(data.lessons!==undefined&&(!data.lessons||typeof data.lessons!=="object"||Array.isArray(data.lessons)))return {ok:false,error:"Trường 'lessons' phải là object, nhận được "+(Array.isArray(data.lessons)?"array":typeof data.lessons)+"."};
  if(data.practice!==undefined&&(!data.practice||typeof data.practice!=="object"||Array.isArray(data.practice)))return {ok:false,error:"Trường 'practice' phải là object, nhận được "+(Array.isArray(data.practice)?"array":typeof data.practice)+"."};
  if(data.review!==undefined&&(!data.review||typeof data.review!=="object"||Array.isArray(data.review)))return {ok:false,error:"Trường 'review' phải là object, nhận được "+(Array.isArray(data.review)?"array":typeof data.review)+"."};
  if(data.history!==undefined&&!Array.isArray(data.history))return {ok:false,error:"Trường 'history' phải là array, nhận được "+typeof data.history+"."};
  if(data.streak!==undefined&&(!data.streak||typeof data.streak!=="object"||Array.isArray(data.streak)))return {ok:false,error:"Trường 'streak' phải là object, nhận được "+(Array.isArray(data.streak)?"array":typeof data.streak)+"."};
  const slugs=new Set([...Object.keys(data.lessons||{}),...Object.keys(data.review||{})]);
  slugs.forEach(s=>{if(!checkSlug(s))badSlug.push(s);});
  if(badSlug.length)return {ok:false,error:"Bài '"+badSlug.slice(0,5).join("', '")+"' trong file không có trên trang. Có thể file thuộc bản web khác."};
  const dateFields=[];
  Object.entries(data.lessons||{}).forEach(([slug,v])=>{if(v&&typeof v==="object"){["doneAt","lastStudiedAt"].forEach(f=>{if(v[f]!==undefined&&v[f]!==null)dateFields.push([slug,v[f]]);});}});
  Object.entries(data.review||{}).forEach(([slug,v])=>{if(v&&typeof v==="object"&&v.nextDue)dateFields.push([slug,v.nextDue,true]);});
  if(data.streak&&data.streak.lastDate)dateFields.push(["",data.streak.lastDate,false]);
  for(const [slug,val,isDue] of dateFields){const okD=isDue?validImportNextDue(val):validImportDate(val);if(!okD)return {ok:false,error:isDue?("Ngày ôn lại '"+dispDate(val)+"' ở bài "+slug+" quá xa trong tương lai (tối đa 60 ngày tới)."):("Ngày '"+dispDate(val)+"' ở bài "+(slug||"chuỗi học")+" không phải ngày hợp lệ.")};}
  for(const [slug,v] of Object.entries(data.lessons||{})){
    if(!v||typeof v!=="object")continue;
    if(v.selfGrade!==undefined&&v.selfGrade!==null&&["kho","vua","de"].indexOf(v.selfGrade)<0)return {ok:false,error:"Bài "+slug+": selfGrade phải là kho/vua/de hoặc null, nhận được "+JSON.stringify(v.selfGrade)+"."};
    if(v.reviews!==undefined&&(typeof v.reviews!=="number"||!Number.isInteger(v.reviews)||v.reviews<0))return {ok:false,error:"Bài "+slug+": reviews phải là số nguyên ≥ 0."};
  }
  for(const [slug,v] of Object.entries(data.review||{})){
    if(!v||typeof v!=="object")continue;
    if(typeof v.interval!=="number"||!Number.isInteger(v.interval)||v.interval<1||v.interval>60)return {ok:false,error:"Bài "+slug+": interval phải từ 1 tới 60, nhận được "+v.interval+"."};
    if(typeof v.ease!=="number"||v.ease<1.3||v.ease>2.5)return {ok:false,error:"Bài "+slug+": ease phải từ 1.3 tới 2.5, nhận được "+v.ease+"."};
    if(typeof v.reps!=="number"||!Number.isInteger(v.reps)||v.reps<0)return {ok:false,error:"Bài "+slug+": reps phải là số nguyên ≥ 0."};
    if(!validImportNextDue(v.nextDue))return {ok:false,error:"Ngày ôn lại '"+dispDate(v.nextDue)+"' ở bài "+slug+" quá xa trong tương lai (tối đa 60 ngày tới)."};
  }
  for(const [k,v] of Object.entries(data.practice||{})){
    if(!v||typeof v!=="object"||typeof v.correct!=="boolean")return {ok:false,error:"Câu luyện '"+k+"': phải có trường correct (true/false)."};
    if(typeof v.attempts!=="number"||!Number.isInteger(v.attempts)||v.attempts<1)return {ok:false,error:"Câu luyện '"+k+"': attempts phải là số nguyên ≥ 1."};
  }
  if(data.streak&&typeof data.streak.count!=="undefined"&&(typeof data.streak.count!=="number"||!Number.isInteger(data.streak.count)||data.streak.count<0))return {ok:false,error:"Trường 'streak.count' phải là số nguyên ≥ 0."};
  if(Array.isArray(data.history)){for(const h of data.history){if(!h||typeof h!=="object"||["done","undone","practice","review","self-grade","import","reset","migrate"].indexOf(h.action)<0)return {ok:false,error:"Trường 'history[].action' không hợp lệ: "+JSON.stringify(h&&h.action)+"."};}}
  for(const [slug,v] of Object.entries(data.review||{})){
    const L=(data.lessons||{})[slug];
    if(!L||L.done!==true)return {ok:false,error:"Bài "+slug+" có lịch ôn nhưng chưa được đánh dấu đã nhớ."};
    if(L.doneAt&&v.nextDue&&v.nextDue<L.doneAt)return {ok:false,error:"Bài "+slug+": nextDue ("+dispDate(v.nextDue)+") phải từ ngày đánh dấu đã nhớ ("+dispDate(L.doneAt)+") trở đi."};
  }
  if(data.streak&&Array.isArray(data.streak.dates)&&data.streak.dates.length&&data.streak.lastDate){
    const last=[...data.streak.dates].sort().pop();
    if(last!==data.streak.lastDate)return {ok:false,error:"Chuỗi học không nhất quán: lastDate phải là ngày cuối trong danh sách ngày học."};
  }
  if(text.length>1024*1024)return {ok:false,error:"File quá lớn (hơn 1 MB). Có thể đây không phải file tiến độ."};
  if(Array.isArray(data.history)&&data.history.length>5000)return {ok:false,error:"File quá lớn (hơn 1 MB). Có thể đây không phải file tiến độ."};
  return {ok:true,data:normalizeProgress(data)};
}
function mergeProgress(current,incoming){
  const out=JSON.parse(JSON.stringify(current));
  Object.entries(incoming.lessons||{}).forEach(([slug,v])=>{
    const cur=out.lessons[slug];
    const newDate=v.lastStudiedAt||v.doneAt||"", curDate=cur?(cur.lastStudiedAt||cur.doneAt||""):"";
    if(!cur||newDate>=curDate){out.lessons[slug]=v;if(incoming.review&&incoming.review[slug])out.review[slug]=incoming.review[slug];}
  });
  Object.entries(incoming.practice||{}).forEach(([k,v])=>{
    const cur=out.practice[k];
    if(!cur||String(v.lastAt||"")>=String(cur.lastAt||""))out.practice[k]=v;
  });
  const allDates=new Set([...(out.streak.dates||[]),...((incoming.streak||{}).dates||[])]);
  out.streak.dates=[...allDates].filter(isValidDateStr).sort().slice(-30);
  const curLast=out.streak.lastDate||"", incLast=(incoming.streak||{}).lastDate||"";
  if(incLast>curLast){out.streak.count=incoming.streak.count||out.streak.count;out.streak.lastDate=incLast;}
  else if(out.streak.dates.length){out.streak.lastDate=[...out.streak.dates].sort().pop();}
  out.history=[...(out.history||[]),...((incoming.history||[]))].sort((a,b)=>String(a.at||"").localeCompare(String(b.at||""))).slice(-500);
  return out;
}
function exportProgress(){
  const p=getProgress();
  const env={app:"sai-dau-sua-do",kind:"progress-export",version:1,exportedAt:new Date().toISOString(),data:p};
  try{
    const blob=new Blob([JSON.stringify(env,null,2)],{type:"application/json"});
    const a=document.createElement("a");a.href=URL.createObjectURL(blob);
    a.download="sai-dau-sua-do-tien-do-"+todayISO()+".json";a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),5000);
    return true;
  }catch(e){return false;}
}
function importProgressText(text,mode){
  const v=validateImportFile(text);
  if(!v.ok)return v;
  const incoming=v.data;
  let result;
  if(mode==="overwrite"){result=incoming;}
  else{result=mergeProgress(getProgress(),incoming);}
  updateProgress(p=>{Object.keys(p).forEach(k=>{delete p[k];});Object.assign(p,JSON.parse(JSON.stringify(result)));pushHistory(p,{date:todayISO(),at:new Date().toISOString(),slug:"",action:"import",note:"mode="+(mode==="overwrite"?"overwrite":"merge")});});
  const doneCount=Object.values(result.lessons||{}).filter(l=>l&&l.done).length;
  const pracCount=Object.keys(result.practice||{}).length;
  const streakCount=(result.streak&&result.streak.count)||0;
  return {ok:true,message:"Đã nhập: "+doneCount+" bài đã nhớ, "+pracCount+" câu luyện, chuỗi "+streakCount+" ngày (chế độ "+(mode==="overwrite"?"Ghi đè":"Gộp")+")."};
}
function loadSpeaking(){
  try{const v=storageGet("sdsc-speaking-v1");const d=v?JSON.parse(v):null;if(d&&typeof d==="object")return {sessions:d.sessions||0,minutes:d.minutes||0,words:d.words||0,best:d.best||0,lastDay:d.lastDay||""};}catch(e){}
  return {sessions:0,minutes:0,words:0,best:0,lastDay:""};
}
function speakingHoursText(mins){
  mins=Math.round(mins||0);
  if(mins<60)return mins+" phút";
  const h=Math.floor(mins/60);const m=mins%60;
  return h+" giờ"+(m?" "+m+" phút":"");
}
function recordSpeaking(minutes,words,score){
  if(!isFinite(minutes)||minutes<=0)return;
  const d=loadSpeaking();
  d.sessions=(d.sessions||0)+1;
  d.minutes=Math.round(((d.minutes||0)+minutes)*10)/10;
  d.words=(d.words||0)+(words||0);
  if(typeof score==="number"&&score>0)d.best=Math.max(d.best||0,Math.round(score));
  d.lastDay=todayISO();
  try{storageSet("sdsc-speaking-v1",JSON.stringify(d));}catch(e){}
  try{noteSpeakingSession(d.minutes);}catch(e){}
}
/* Điền tổng số bài vào header (tối ưu B 19/11): tổng số lấy từ data.js
   lúc chạy, không ghi cứng vào HTML, để thêm bài mới không đổi mọi trang.
   Trang chủ và trang lộ trình cũng tự cập nhật lại đúng số này sau đó. */
(function(){
  try{
    var total=window.SDSC_TOTAL_LESSONS||0;
    document.querySelectorAll(".total-lessons-num").forEach(function(el){el.textContent=total;});
    var p=getProgress();
    var n=Object.entries(p.lessons||{}).filter(function(le){var l=le[1];return l&&l.done&&window.SDSC_LESSONS[le[0]];}).length;
    document.querySelectorAll(".progress-num").forEach(function(el){el.textContent=n+" / "+total+" bài";});
  }catch(e){}
})();
</script>
"""


CHUNK_JS = r"""
<script>
(function(){
  const box=document.getElementById("chunk-box");
  if(!box)return;
  let chunks=[];
  try{chunks=JSON.parse(document.getElementById("chunk-data").textContent)||[];}catch(e){chunks=[];}
  if(!chunks.length){box.style.display="none";return;}
  const enEl=document.getElementById("chunk-en");
  const viEl=document.getElementById("chunk-vi");
  const progEl=document.getElementById("chunk-progress");
  const barEl=document.getElementById("chunk-bar");
  const listenBtn=document.getElementById("chunk-listen");
  const prevBtn=document.getElementById("chunk-prev");
  const nextBtn=document.getElementById("chunk-next");
  let i=0;
  function show(){
    const c=chunks[i];
    if(enEl)enEl.textContent=c.en;
    if(viEl)viEl.textContent=c.vi||"";
    if(progEl)progEl.textContent="Cụm "+(i+1)+"/"+chunks.length;
    if(barEl)barEl.style.width=Math.round(100*(i+1)/chunks.length)+"%";
    if(listenBtn)listenBtn.dataset.say=c.en;
    if(prevBtn)prevBtn.disabled=i===0;
    if(nextBtn)nextBtn.textContent=i===chunks.length-1?"Học xong, luyện nói →":"Cụm tiếp theo";
  }
  if(listenBtn)listenBtn.addEventListener("click",()=>{
    if(listenBtn.dataset.say)speak(listenBtn.dataset.say,listenBtn);
  });
  if(prevBtn)prevBtn.addEventListener("click",()=>{if(i>0){i--;show();}});
  if(nextBtn)nextBtn.addEventListener("click",()=>{
    if(i<chunks.length-1){i++;show();}
    else{location.href=BASE_PATH_PLACEHOLDER+"/luyen-noi/?s="+encodeURIComponent(chunks[i].en);}
  });
  show();
})();
</script>
"""

DICT_JS = r"""
<script>
(function(){
  const input=document.getElementById("dict-input");
  const btn=document.getElementById("dict-go");
  const box=document.getElementById("dict-result");
  const recentBox=document.getElementById("dict-recent");
  const RECENT_KEY="sdsc-dict-recent";
  const VI_POS={"noun":"danh từ","verb":"động từ","adjective":"tính từ","adverb":"trạng từ","preposition":"giới từ","pronoun":"đại từ","conjunction":"liên từ","interjection":"thán từ","exclamation":"thán từ","article":"mạo từ","determiner":"từ hạn định","numeral":"số từ","transitive verb":"ngoại động từ","intransitive verb":"nội động từ"};
  const WIKI_POS={"Tính từ":"tính từ","Danh từ":"danh từ","Động từ":"động từ","Phó từ":"trạng từ","Thán từ":"thán từ","Giới từ":"giới từ","Đại từ":"đại từ","Liên từ":"liên từ","Mạo từ":"mạo từ","Nội động từ":"nội động từ","Ngoại động từ":"ngoại động từ","Cụm từ":"cụm từ","Thành ngữ":"thành ngữ"};
  const VI_GLOSSARY={
"a":[["mạo từ","một"]],
"about":[["giới từ","về"]],
"above":[["giới từ","ở trên"]],
"absolutely":[["trạng từ","hoàn toàn"]],
"across":[["giới từ","băng qua"]],
"actually":[["trạng từ","thật ra","Actually, I do not like coffee.","Thật ra tôi không thích cà phê."]],
"afraid":[["tính từ","sợ"]],
"after":[["giới từ","sau"]],
"again":[["trạng từ","nữa, lại"]],
"against":[["giới từ","chống lại"]],
"agree":[["động từ","đồng ý","I agree with you.","Tôi đồng ý với bạn."]],
"all":[["tính từ","tất cả"]],
"almost":[["trạng từ","gần như"]],
"alone":[["tính từ","một mình"]],
"already":[["trạng từ","rồi"]],
"also":[["trạng từ","cũng"]],
"although":[["liên từ","mặc dù"]],
"always":[["trạng từ","luôn luôn"]],
"am":[["động từ","là, ở"]],
"among":[["giới từ","giữa, trong số"]],
"an":[["mạo từ","một"]],
"and":[["liên từ","và"]],
"angry":[["tính từ","tức giận"]],
"another":[["đại từ","một cái khác"]],
"answer":[["động từ","trả lời","Answer my question.","Trả lời câu hỏi của tôi đi."],["danh từ","câu trả lời"]],
"any":[["tính từ","bất cứ"]],
"anything":[["danh từ","bất cứ thứ gì"]],
"apple":[["danh từ","quả táo"]],
"april":[["danh từ","tháng 4"]],
"are":[["động từ","là, ở"]],
"arm":[["danh từ","cánh tay"]],
"around":[["giới từ","xung quanh"]],
"arrive":[["động từ","đến nơi","We arrive at 9.","Chúng tôi đến nơi lúc 9 giờ."]],
"arrived":[["động từ","đã đến nơi"]],
"ask":[["động từ","hỏi","Can I ask a question?","Tôi hỏi một câu được không?"]],
"asked":[["động từ","đã hỏi"]],
"at":[["giới từ","tại"]],
"august":[["danh từ","tháng 8"]],
"autumn":[["danh từ","mùa thu"]],
"awake":[["tính từ","thức"]],
"baby":[["danh từ","em bé"]],
"back":[["danh từ","lưng"],["trạng từ","trở lại"]],
"bad":[["tính từ","xấu"]],
"bag":[["danh từ","cái túi"]],
"ball":[["danh từ","quả bóng"]],
"banana":[["danh từ","chuối"]],
"bank":[["danh từ","ngân hàng"]],
"be":[["động từ","là, ở","I am a student.","Tôi là học sinh."]],
"beach":[["danh từ","bãi biển"]],
"beautiful":[["tính từ","đẹp"]],
"became":[["động từ","đã trở thành"]],
"because":[["liên từ","vì"]],
"become":[["động từ","trở thành","She becomes a teacher.","Cô ấy trở thành giáo viên."]],
"bed":[["danh từ","giường"]],
"been":[["động từ","đã là, đã ở"]],
"before":[["giới từ","trước"]],
"began":[["động từ","đã bắt đầu"]],
"behind":[["giới từ","phía sau"]],
"believe":[["động từ","tin"]],
"below":[["giới từ","ở dưới"]],
"best":[["tính từ","tốt nhất"]],
"better":[["tính từ","tốt hơn"]],
"between":[["giới từ","giữa"]],
"big":[["tính từ","lớn"]],
"bigger":[["tính từ","lớn hơn"]],
"biggest":[["tính từ","lớn nhất"]],
"bike":[["danh từ","xe đạp"]],
"bird":[["danh từ","chim"]],
"birthday":[["danh từ","sinh nhật","Happy birthday!","Chúc mừng sinh nhật!"]],
"black":[["tính từ","đen"]],
"blue":[["tính từ","xanh dương"]],
"body":[["danh từ","cơ thể"]],
"book":[["danh từ","sách","I read a book.","Tôi đọc một cuốn sách."]],
"bored":[["tính từ","chán, buồn chán","I am bored.","Tôi chán quá."]],
"boring":[["tính từ","gây chán","This film is boring.","Bộ phim này chán quá."]],
"born":[["động từ","đã sinh ra"]],
"borrow":[["động từ","mượn (của ai cái gì)","Can I borrow your pen?","Tôi mượn cây bút của bạn được không?"]],
"both":[["đại từ","cả hai"]],
"bought":[["động từ","đã mua"]],
"boy":[["danh từ","con trai"]],
"boyfriend":[["danh từ","bạn trai"]],
"brave":[["tính từ","dũng cảm"]],
"bread":[["danh từ","bánh mì"]],
"break":[["động từ","làm vỡ","Do not break the glass.","Đừng làm vỡ cái ly."],["động từ","chia tay","She broke up with him.","Cô ấy chia tay anh ta."]],
"breakfast":[["danh từ","bữa sáng"]],
"bright":[["tính từ","sáng"]],
"bring":[["động từ","mang đến","Bring your book.","Mang sách theo nhé."]],
"broke":[["động từ","đã làm vỡ"]],
"brother":[["danh từ","anh, em trai"]],
"brought":[["động từ","đã mang đến"]],
"brown":[["tính từ","nâu"]],
"build":[["động từ","xây dựng","They build a house.","Họ xây một ngôi nhà."]],
"built":[["động từ","đã xây"]],
"bus":[["danh từ","xe buýt"]],
"busy":[["tính từ","bận"]],
"but":[["liên từ","nhưng"]],
"buy":[["động từ","mua","I buy a new bag.","Tôi mua một cái túi mới."]],
"by":[["giới từ","bằng, bởi"]],
"cafe":[["danh từ","quán cà phê"]],
"cake":[["danh từ","bánh ngọt"]],
"call":[["động từ","gọi điện","Call me tomorrow.","Ngày mai gọi cho tôi nhé."]],
"came":[["động từ","đã đến"]],
"can":[["động từ","có thể"]],
"cannot":[["động từ","không thể"]],
"car":[["danh từ","xe hơi"]],
"card":[["danh từ","thẻ, thiệp"]],
"careful":[["tính từ","cẩn thận"]],
"carry":[["động từ","mang, vác"]],
"castle":[["danh từ","lâu đài"]],
"cat":[["danh từ","mèo"]],
"catch":[["động từ","bắt"]],
"caught":[["động từ","đã bắt"]],
"celebrate":[["động từ","ăn mừng, kỷ niệm"]],
"chair":[["danh từ","cái ghế"]],
"change":[["động từ","thay đổi","Things change.","Mọi thứ thay đổi."]],
"cheap":[["tính từ","rẻ"]],
"child":[["danh từ","đứa trẻ"]],
"childish":[["tính từ","trẻ con, chưa chín chắn"]],
"children":[["danh từ","trẻ em"]],
"choose":[["động từ","chọn"]],
"chose":[["động từ","đã chọn"]],
"city":[["danh từ","thành phố"]],
"class":[["danh từ","lớp học"]],
"clean":[["tính từ","sạch"]],
"clear":[["tính từ","rõ ràng"]],
"close":[["động từ","đóng","Close the window.","Đóng cửa sổ lại."]],
"clothes":[["danh từ","quần áo"]],
"cloud":[["danh từ","mây"]],
"coffee":[["danh từ","cà phê"]],
"cold":[["tính từ","lạnh"]],
"colder":[["tính từ","lạnh hơn"]],
"come":[["động từ","đến","Come here, please.","Lại đây nào."]],
"comfortable":[["tính từ","thoải mái","This chair is comfortable.","Cái ghế này ngồi thoải mái."]],
"completely":[["trạng từ","hoàn toàn"]],
"computer":[["danh từ","máy tính"]],
"cook":[["động từ","nấu ăn","I cook dinner.","Tôi nấu bữa tối."]],
"correct":[["tính từ","đúng"]],
"could":[["động từ","có thể"]],
"country":[["danh từ","đất nước"]],
"cry":[["động từ","khóc"]],
"currently":[["trạng từ","hiện tại","I am currently working in Da Lat.","Hiện tại tôi làm việc ở Đà Lạt."]],
"cut":[["động từ","cắt"]],
"dangerous":[["tính từ","nguy hiểm"]],
"dark":[["tính từ","tối"]],
"daughter":[["danh từ","con gái"]],
"day":[["danh từ","ngày","Have a nice day.","Chúc một ngày vui vẻ."]],
"dead":[["tính từ","đã chết"]],
"dear":[["tính từ","thân mến"]],
"debt":[["danh từ","khoản nợ"]],
"december":[["danh từ","tháng 12"]],
"decide":[["động từ","quyết định"]],
"deep":[["tính từ","sâu"]],
"dentist":[["danh từ","nha sĩ"]],
"desk":[["danh từ","bàn học"]],
"detail":[["danh từ","chi tiết"]],
"did":[["động từ","đã làm"]],
"didn't":[["trạng từ","không (viết tắt của did not)"]],
"die":[["động từ","chết"]],
"different":[["tính từ","khác nhau"]],
"difficult":[["tính từ","khó"]],
"dinner":[["danh từ","bữa tối"]],
"dirty":[["tính từ","bẩn"]],
"dish":[["danh từ","món ăn, cái đĩa"]],
"do":[["động từ","làm","What do you do?","Bạn làm nghề gì?"]],
"doctor":[["danh từ","bác sĩ"]],
"does":[["động từ","làm"]],
"doesn't":[["trạng từ","không (viết tắt của does not)"]],
"dog":[["danh từ","chó"]],
"don't":[["trạng từ","không (viết tắt của do not)"]],
"done":[["động từ","đã làm xong"]],
"door":[["danh từ","cửa"]],
"down":[["trạng từ","xuống"]],
"draw":[["động từ","vẽ"]],
"dream":[["danh từ","giấc mơ"],["động từ","mơ"]],
"dress":[["danh từ","váy"]],
"drew":[["động từ","đã vẽ"]],
"drink":[["động từ","uống","I drink water.","Tôi uống nước."]],
"drive":[["động từ","lái xe"]],
"drop":[["động từ","làm rơi, thả xuống"]],
"drove":[["động từ","đã lái"]],
"dry":[["tính từ","khô"]],
"durian":[["danh từ","sầu riêng"]],
"during":[["giới từ","trong lúc"]],
"each":[["đại từ","mỗi"]],
"ear":[["danh từ","tai"]],
"early":[["tính từ","sớm","I get up early.","Tôi dậy sớm."],["trạng từ","sớm"]],
"earth":[["danh từ","trái đất"]],
"easy":[["tính từ","dễ"]],
"eat":[["động từ","ăn","We eat rice every day.","Ngày nào chúng tôi cũng ăn cơm."]],
"egg":[["danh từ","trứng"]],
"eight":[["số từ","tám"]],
"either":[["đại từ","một trong hai"]],
"eleven":[["số từ","mười một"]],
"else":[["trạng từ","khác nữa"]],
"empty":[["tính từ","trống"]],
"end":[["danh từ","cuối"],["động từ","kết thúc"]],
"english":[["danh từ","tiếng Anh"],["tính từ","thuộc Anh"]],
"enough":[["trạng từ","đủ"]],
"enter":[["động từ","đi vào"]],
"even":[["trạng từ","thậm chí"]],
"evening":[["danh từ","buổi tối"]],
"ever":[["trạng từ","đã từng, bao giờ"]],
"every":[["tính từ","mọi"]],
"everybody":[["đại từ","mọi người"]],
"everyone":[["đại từ","mọi người"]],
"everything":[["danh từ","mọi thứ"]],
"exam":[["danh từ","bài kiểm tra"]],
"example":[["danh từ","ví dụ"]],
"excited":[["tính từ","hào hứng"]],
"expensive":[["tính từ","đắt"]],
"eye":[["danh từ","mắt"]],
"face":[["danh từ","khuôn mặt"]],
"fact":[["danh từ","sự thật"]],
"fall":[["động từ","ngã"]],
"family":[["danh từ","gia đình"]],
"famous":[["tính từ","nổi tiếng"]],
"far":[["trạng từ","xa"]],
"farm":[["danh từ","nông trại"]],
"farther":[["trạng từ","xa hơn (khoảng cách)"]],
"fast":[["tính từ","nhanh"]],
"father":[["danh từ","bố"]],
"favorite":[["tính từ","yêu thích"]],
"february":[["danh từ","tháng 2"]],
"feel":[["động từ","cảm thấy","I feel tired.","Tôi thấy mệt."]],
"fell":[["động từ","đã ngã"]],
"felt":[["động từ","đã cảm thấy"]],
"few":[["tính từ","ít"]],
"fewer":[["tính từ","ít hơn (đếm được)"]],
"field":[["danh từ","cánh đồng"]],
"film":[["danh từ","phim"]],
"find":[["động từ","tìm","I cannot find my keys.","Tôi không tìm thấy chìa khóa."]],
"fine":[["tính từ","tốt, khỏe"]],
"finish":[["động từ","hoàn thành","Finish your homework.","Làm xong bài tập đi."]],
"finished":[["động từ","đã hoàn thành"]],
"first":[["số từ","đầu tiên"]],
"fish":[["danh từ","cá"]],
"five":[["số từ","năm"]],
"flew":[["động từ","đã bay"]],
"flower":[["danh từ","hoa"]],
"fly":[["động từ","bay"],["danh từ","con ruồi"]],
"follow":[["động từ","đi theo"]],
"food":[["danh từ","thức ăn"]],
"foot":[["danh từ","bàn chân"]],
"football":[["danh từ","bóng đá"]],
"for":[["giới từ","trong (khoảng thời gian)","I have lived here for 3 years.","Tôi sống ở đây 3 năm rồi."],["giới từ","cho","This gift is for you.","Món quà này cho bạn."]],
"forget":[["động từ","quên","Do not forget your bag.","Đừng quên cái túi."]],
"forgot":[["động từ","đã quên"]],
"four":[["số từ","bốn"]],
"free":[["tính từ","miễn phí, rảnh"]],
"friday":[["danh từ","thứ sáu"]],
"friend":[["danh từ","bạn","She is my best friend.","Cô ấy là bạn thân nhất của tôi."]],
"from":[["giới từ","từ"]],
"fruit":[["danh từ","trái cây"]],
"full":[["tính từ","đầy"]],
"fun":[["tính từ","vui"]],
"funny":[["tính từ","buồn cười"]],
"further":[["trạng từ","thêm nữa"]],
"future":[["danh từ","tương lai"]],
"garden":[["danh từ","vườn"]],
"get":[["động từ","lấy, nhận","I got a new book.","Tôi nhận được một cuốn sách mới."]],
"gift":[["danh từ","món quà"]],
"girl":[["danh từ","con gái"]],
"give":[["động từ","cho","Give me your hand.","Đưa tay cho tôi."]],
"glass":[["danh từ","cái ly"]],
"go":[["động từ","đi","I go to school every day.","Ngày nào tôi cũng đi học."]],
"goal":[["danh từ","mục tiêu"]],
"god":[["danh từ","thượng đế"]],
"gold":[["danh từ","vàng"]],
"gone":[["động từ","đã đi"]],
"good":[["tính từ","tốt"]],
"got":[["động từ","đã lấy, đã nhận"]],
"grandmother":[["danh từ","bà"]],
"gray":[["tính từ","xám"]],
"great":[["tính từ","tuyệt vời"]],
"green":[["tính từ","xanh lá"]],
"grew":[["động từ","đã lớn lên"]],
"grey":[["tính từ","xám"]],
"ground":[["danh từ","mặt đất"]],
"group":[["danh từ","nhóm"]],
"grow":[["động từ","lớn lên, trồng","Plants grow fast.","Cây lớn nhanh."]],
"guess":[["động từ","đoán"]],
"had":[["động từ","đã có"]],
"hair":[["danh từ","tóc"]],
"half":[["danh từ","một nửa"]],
"hand":[["danh từ","bàn tay"]],
"handsome":[["tính từ","đẹp trai"]],
"happen":[["động từ","xảy ra","What happened?","Có chuyện gì vậy?"]],
"happiness":[["danh từ","hạnh phúc"]],
"happy":[["tính từ","vui vẻ"]],
"hard":[["tính từ","khó"]],
"has":[["động từ","có"]],
"hat":[["danh từ","cái mũ"]],
"hate":[["động từ","ghét"]],
"have":[["động từ","có","I have two sisters.","Tôi có hai chị em gái."]],
"he":[["đại từ","anh ấy"]],
"head":[["danh từ","đầu"]],
"health":[["danh từ","sức khỏe"]],
"healthy":[["tính từ","khỏe mạnh"]],
"hear":[["động từ","nghe thấy"]],
"heard":[["động từ","đã nghe"]],
"heart":[["danh từ","trái tim"]],
"heat":[["danh từ","hơi nóng"]],
"heavy":[["tính từ","nặng"]],
"held":[["động từ","đã cầm, đã giữ"]],
"hello":[["thán từ","xin chào","Hello, how are you?","Xin chào, bạn khỏe không?"]],
"help":[["động từ","giúp","Can you help me?","Bạn giúp tôi được không?"]],
"helped":[["động từ","đã giúp"]],
"her":[["tính từ","của cô ấy"],["đại từ","cô ấy"]],
"here":[["trạng từ","ở đây"]],
"herself":[["đại từ","chính cô ấy"]],
"hi":[["thán từ","chào"]],
"high":[["tính từ","cao"]],
"him":[["đại từ","anh ấy, ông ấy"]],
"himself":[["đại từ","chính anh ấy"]],
"his":[["tính từ","của anh ấy, của cô ấy"]],
"history":[["danh từ","lịch sử"]],
"holiday":[["danh từ","kỳ nghỉ, ngày lễ"]],
"home":[["danh từ","nhà","I am going home.","Tôi đang về nhà."]],
"hometown":[["danh từ","quê hương"]],
"homework":[["danh từ","bài tập về nhà"]],
"hope":[["động từ","hi vọng"]],
"horse":[["danh từ","con ngựa"]],
"hospital":[["danh từ","bệnh viện"]],
"hot":[["tính từ","nóng"]],
"hotel":[["danh từ","khách sạn"]],
"hour":[["danh từ","giờ","Wait one hour.","Chờ một giờ nhé."]],
"house":[["danh từ","ngôi nhà"]],
"how":[["trạng từ","như thế nào"]],
"however":[["trạng từ","tuy nhiên"]],
"huge":[["tính từ","to lớn"]],
"human":[["danh từ","con người"]],
"hundred":[["số từ","một trăm"]],
"hungry":[["tính từ","đói"]],
"hurry":[["động từ","vội"]],
"i":[["đại từ","tôi"]],
"i'd":[["đại từ","tôi sẽ, tôi đã"]],
"ice":[["danh từ","đá, nước đá"]],
"idea":[["danh từ","ý tưởng"]],
"if":[["liên từ","nếu"]],
"ill":[["tính từ","ốm"]],
"immature":[["tính từ","chưa chín chắn, non nớt"]],
"important":[["tính từ","quan trọng"]],
"impossible":[["tính từ","không thể"]],
"in":[["giới từ","trong"]],
"interested":[["tính từ","quan tâm, thích thú"]],
"interesting":[["tính từ","thú vị"]],
"into":[["giới từ","vào trong"]],
"invite":[["động từ","mời"]],
"is":[["động từ","là, ở"]],
"it":[["đại từ","nó, cái đó"]],
"its":[["tính từ","của nó"]],
"january":[["danh từ","tháng 1"]],
"job":[["danh từ","công việc","I have a new job.","Tôi có công việc mới."]],
"juice":[["danh từ","nước ép"]],
"july":[["danh từ","tháng 7"]],
"june":[["danh từ","tháng 6"]],
"just":[["trạng từ","chỉ, vừa mới"]],
"keep":[["động từ","giữ","Keep it safe.","Giữ cẩn thận nhé."]],
"kept":[["động từ","đã giữ"]],
"key":[["danh từ","chìa khóa"]],
"kid":[["danh từ","đứa trẻ"]],
"kill":[["động từ","giết"]],
"kind":[["tính từ","tốt bụng"]],
"king":[["danh từ","vua"]],
"knew":[["động từ","đã biết"]],
"knight":[["danh từ","hiệp sĩ"]],
"know":[["động từ","biết","I know her.","Tôi biết cô ấy."]],
"known":[["động từ","đã biết"]],
"lady":[["danh từ","quý bà"]],
"lake":[["danh từ","hồ"]],
"land":[["danh từ","đất"]],
"language":[["danh từ","ngôn ngữ"]],
"laptop":[["danh từ","máy tính xách tay"]],
"large":[["tính từ","lớn"]],
"last":[["tính từ","cuối cùng"]],
"late":[["tính từ","muộn","Do not be late.","Đừng đến muộn."],["trạng từ","muộn"]],
"later":[["trạng từ","sau này","See you later.","Hẹn gặp lại sau nhé."]],
"laugh":[["động từ","cười"]],
"learn":[["động từ","học","I learn English every day.","Ngày nào tôi cũng học tiếng Anh."]],
"learned":[["động từ","đã học"]],
"least":[["tính từ","ít nhất"]],
"leave":[["động từ","rời đi","I leave at 8.","Tôi đi lúc 8 giờ."]],
"left":[["động từ","đã rời đi"]],
"leg":[["danh từ","chân"]],
"lend":[["động từ","cho mượn","Can you lend me your book?","Bạn cho tôi mượn sách được không?"]],
"lent":[["động từ","đã cho mượn"]],
"less":[["tính từ","ít hơn","Less sugar, please.","Ít đường thôi ạ."]],
"lesson":[["danh từ","bài học"]],
"let":[["động từ","để cho"]],
"letter":[["danh từ","lá thư"]],
"level":[["danh từ","mức độ"]],
"lie":[["động từ","nằm, nói dối"]],
"life":[["danh từ","cuộc sống"]],
"light":[["tính từ","nhẹ"],["danh từ","ánh sáng"]],
"like":[["động từ","thích","I like coffee.","Tôi thích cà phê."],["giới từ","giống như"]],
"liked":[["động từ","đã thích"]],
"line":[["danh từ","đường kẻ"]],
"listen":[["động từ","nghe","Listen to me.","Nghe tôi nói này."]],
"little":[["tính từ","nhỏ, ít"]],
"live":[["động từ","sống","I live in Da Lat.","Tôi sống ở Đà Lạt."]],
"lived":[["động từ","đã sống"]],
"long":[["tính từ","dài"]],
"look":[["động từ","nhìn","Look at the board.","Nhìn lên bảng đi."]],
"looked":[["động từ","đã nhìn"]],
"lose":[["động từ","làm mất, thua"]],
"lost":[["động từ","đã mất, đã thua"]],
"lot":[["danh từ","nhiều"]],
"love":[["động từ","yêu","I love my family.","Tôi yêu gia đình mình."],["danh từ","tình yêu"]],
"loved":[["động từ","đã yêu"]],
"low":[["tính từ","thấp"]],
"lunch":[["danh từ","bữa trưa"]],
"machine":[["danh từ","cái máy"]],
"made":[["động từ","đã làm"]],
"make":[["động từ","làm, tạo ra","I make coffee every morning.","Sáng nào tôi cũng pha cà phê."]],
"man":[["danh từ","đàn ông"]],
"many":[["tính từ","nhiều"]],
"march":[["danh từ","tháng 3"]],
"market":[["danh từ","chợ"]],
"married":[["tính từ","đã kết hôn"]],
"matter":[["danh từ","vấn đề"],["động từ","quan trọng"]],
"may":[["động từ","có thể"]],
"maybe":[["trạng từ","có thể"]],
"me":[["đại từ","tôi"]],
"meal":[["danh từ","bữa ăn"]],
"mean":[["động từ","có nghĩa là"]],
"meant":[["động từ","đã có nghĩa là"]],
"meat":[["danh từ","thịt"]],
"meet":[["động từ","gặp","Nice to meet you.","Rất vui được gặp bạn."]],
"meeting":[["danh từ","cuộc họp"]],
"melt":[["động từ","tan chảy"]],
"men":[["danh từ","đàn ông"]],
"message":[["danh từ","tin nhắn"]],
"met":[["động từ","đã gặp"]],
"might":[["động từ","có thể"]],
"milk":[["danh từ","sữa"]],
"mind":[["danh từ","tâm trí"]],
"minute":[["danh từ","phút"]],
"miss":[["động từ","nhớ, bỏ lỡ"]],
"moment":[["danh từ","lúc, khoảnh khắc"]],
"monday":[["danh từ","thứ hai"]],
"money":[["danh từ","tiền"]],
"month":[["danh từ","tháng"]],
"moon":[["danh từ","mặt trăng"]],
"more":[["trạng từ","nhiều hơn, hơn nữa"]],
"morning":[["danh từ","buổi sáng","I drink coffee in the morning.","Buổi sáng tôi uống cà phê."]],
"most":[["tính từ","nhất, nhiều nhất"]],
"mother":[["danh từ","mẹ"]],
"mountain":[["danh từ","núi"]],
"mouth":[["danh từ","miệng"]],
"move":[["động từ","di chuyển","Move to the left.","Dịch sang trái đi."]],
"moved":[["động từ","đã di chuyển"]],
"movie":[["danh từ","phim"]],
"much":[["tính từ","nhiều"]],
"music":[["danh từ","nhạc"]],
"must":[["động từ","phải"]],
"my":[["tính từ","của tôi"]],
"name":[["danh từ","tên"]],
"near":[["giới từ","gần"]],
"necessary":[["tính từ","cần thiết"]],
"neck":[["danh từ","cổ"]],
"need":[["động từ","cần","I need your help.","Tôi cần bạn giúp."]],
"needed":[["động từ","đã cần"]],
"neither":[["đại từ","không cái nào trong hai"]],
"never":[["trạng từ","không bao giờ"]],
"new":[["tính từ","mới"]],
"news":[["danh từ","tin tức"]],
"next":[["tính từ","tiếp theo"]],
"nice":[["tính từ","dễ chịu, tốt"]],
"night":[["danh từ","ban đêm","Good night.","Chúc ngủ ngon."]],
"nine":[["số từ","chín"]],
"no":[["trạng từ","không"]],
"nobody":[["đại từ","không ai"]],
"noisy":[["tính từ","ồn ào"]],
"north":[["danh từ","phía bắc"]],
"nose":[["danh từ","mũi"]],
"not":[["trạng từ","không"]],
"note":[["danh từ","ghi chú"]],
"nothing":[["danh từ","không có gì"]],
"notice":[["động từ","để ý"]],
"november":[["danh từ","tháng 11"]],
"now":[["trạng từ","bây giờ","I am busy now.","Bây giờ tôi đang bận."]],
"number":[["danh từ","con số"]],
"nurse":[["danh từ","y tá"]],
"occasion":[["danh từ","dịp"]],
"october":[["danh từ","tháng 10"]],
"of":[["giới từ","của"]],
"off":[["trạng từ","tắt, rời"]],
"often":[["trạng từ","thường xuyên"]],
"old":[["tính từ","cũ, già"]],
"on":[["giới từ","trên"]],
"once":[["trạng từ","một lần"]],
"one":[["số từ","một"]],
"only":[["trạng từ","chỉ"]],
"open":[["động từ","mở","Open the door.","Mở cửa ra."]],
"or":[["liên từ","hoặc"]],
"orange":[["danh từ","quả cam"],["tính từ","cam"]],
"order":[["danh từ","đơn hàng"],["động từ","gọi món"]],
"other":[["tính từ","khác"]],
"our":[["tính từ","của chúng tôi"]],
"out":[["trạng từ","ra ngoài"]],
"over":[["giới từ","trên"]],
"own":[["tính từ","của riêng"]],
"page":[["danh từ","trang"]],
"paid":[["động từ","đã trả"]],
"paper":[["danh từ","giấy"]],
"parents":[["danh từ","bố mẹ"]],
"park":[["danh từ","công viên"]],
"part":[["danh từ","phần"]],
"party":[["danh từ","bữa tiệc"]],
"pass":[["động từ","vượt qua"]],
"past":[["danh từ","quá khứ"]],
"pay":[["động từ","trả tiền","I pay by card.","Tôi trả bằng thẻ."]],
"pen":[["danh từ","cây bút"]],
"people":[["danh từ","mọi người"]],
"perfect":[["tính từ","hoàn hảo"]],
"phone":[["danh từ","điện thoại"]],
"photo":[["danh từ","ảnh"]],
"piano":[["danh từ","đàn piano"]],
"pick":[["động từ","hái, chọn"]],
"picture":[["danh từ","bức tranh"]],
"pink":[["tính từ","hồng"]],
"place":[["danh từ","nơi"]],
"plan":[["danh từ","kế hoạch"],["động từ","lên kế hoạch"]],
"plant":[["danh từ","cây cối"]],
"play":[["động từ","chơi","They play football.","Họ chơi bóng đá."]],
"played":[["động từ","đã chơi"]],
"please":[["trạng từ","làm ơn"]],
"point":[["danh từ","điểm"]],
"police":[["danh từ","cảnh sát"]],
"poor":[["tính từ","nghèo"]],
"popular":[["tính từ","phổ biến"]],
"possible":[["tính từ","có thể"]],
"prefer":[["động từ","thích hơn"]],
"present":[["danh từ","món quà"]],
"pretty":[["tính từ","xinh"]],
"price":[["danh từ","giá"]],
"problem":[["danh từ","vấn đề"]],
"pull":[["động từ","kéo"]],
"purple":[["tính từ","tím"]],
"push":[["động từ","đẩy"]],
"put":[["động từ","đã đặt"]],
"question":[["danh từ","câu hỏi"]],
"quick":[["tính từ","nhanh"]],
"quiet":[["tính từ","yên tĩnh"]],
"quite":[["trạng từ","khá, hoàn toàn"]],
"rain":[["danh từ","mưa"]],
"rainy":[["tính từ","có mưa"]],
"ran":[["động từ","đã chạy"]],
"rang":[["động từ","đã reo, đã gọi"]],
"rather":[["trạng từ","khá, thà rằng"]],
"read":[["động từ","đọc","I read books every night.","Tối nào tôi cũng đọc sách."]],
"ready":[["tính từ","sẵn sàng"]],
"real":[["tính từ","thật"]],
"really":[["trạng từ","thật sự"]],
"reason":[["danh từ","lý do"]],
"remember":[["động từ","nhớ","I remember you.","Tôi nhớ bạn."]],
"remembered":[["động từ","đã nhớ"]],
"rent":[["động từ","thuê"]],
"rest":[["danh từ","phần còn lại"]],
"rich":[["tính từ","giàu"]],
"ride":[["động từ","cưỡi, đi xe"]],
"right":[["tính từ","đúng"],["danh từ","quyền, phía phải"]],
"ring":[["danh từ","chiếc nhẫn"]],
"river":[["danh từ","sông"]],
"road":[["danh từ","đường"]],
"rob":[["động từ","cướp","They robbed the bank.","Họ cướp ngân hàng."]],
"robbed":[["động từ","đã cướp"]],
"rock":[["danh từ","tảng đá"]],
"rode":[["động từ","đã cưỡi, đã đi xe"]],
"room":[["danh từ","phòng"]],
"rose":[["động từ","đã mọc, đã tăng"]],
"round":[["tính từ","tròn"]],
"run":[["động từ","chạy","He runs fast.","Anh ấy chạy nhanh."]],
"sad":[["tính từ","buồn"]],
"safe":[["tính từ","an toàn"]],
"said":[["động từ","đã nói"]],
"salary":[["danh từ","lương tháng","Her salary is high.","Lương tháng của cô ấy cao."]],
"salt":[["danh từ","muối"]],
"same":[["tính từ","giống nhau"]],
"sang":[["động từ","đã hát"]],
"sank":[["động từ","đã chìm"]],
"sat":[["động từ","đã ngồi"]],
"saturday":[["danh từ","thứ bảy"]],
"save":[["động từ","tiết kiệm, lưu lại"]],
"saw":[["động từ","đã thấy"]],
"say":[["động từ","nói","Say hello to your mother.","Gửi lời chào tới mẹ bạn nhé."]],
"school":[["danh từ","trường học"]],
"sea":[["danh từ","biển"]],
"season":[["danh từ","mùa"]],
"second":[["số từ","thứ hai"],["danh từ","giây"]],
"see":[["động từ","nhìn thấy","I see a bird.","Tôi thấy một con chim."]],
"seem":[["động từ","có vẻ"]],
"seen":[["động từ","đã thấy"]],
"sell":[["động từ","bán"]],
"send":[["động từ","gửi","Send me a message.","Gửi tin nhắn cho tôi nhé."]],
"sent":[["động từ","đã gửi"]],
"september":[["danh từ","tháng 9"]],
"serious":[["tính từ","nghiêm túc"]],
"serve":[["động từ","phục vụ"]],
"set":[["động từ","đã đặt"]],
"seven":[["số từ","bảy"]],
"shall":[["động từ","sẽ"]],
"she":[["đại từ","cô ấy"]],
"sheep":[["danh từ","cừu","The sheep is white.","Con cừu màu trắng."]],
"ship":[["danh từ","tàu thủy","The ship is big.","Con tàu rất lớn."]],
"shirt":[["danh từ","áo sơ mi"]],
"shoe":[["danh từ","giày"]],
"shoes":[["danh từ","giày"]],
"shook":[["động từ","đã lắc"]],
"shop":[["danh từ","cửa hàng"]],
"short":[["tính từ","thấp, ngắn"]],
"should":[["động từ","nên"]],
"show":[["động từ","cho xem","Show me the photo.","Cho tôi xem ảnh đi."]],
"shut":[["động từ","đã đóng"]],
"sick":[["tính từ","ốm"]],
"side":[["danh từ","phía"]],
"sign":[["danh từ","biển báo"]],
"simple":[["tính từ","đơn giản"]],
"since":[["giới từ","từ khi","I have lived here since 2020.","Tôi sống ở đây từ năm 2020."]],
"sing":[["động từ","hát","She sings well.","Cô ấy hát hay."]],
"sink":[["động từ","chìm"],["danh từ","bồn rửa"]],
"sister":[["danh từ","chị, em gái"]],
"sit":[["động từ","ngồi"]],
"six":[["số từ","sáu"]],
"size":[["danh từ","cỡ"]],
"sky":[["danh từ","bầu trời"]],
"sleep":[["động từ","ngủ","I sleep 8 hours.","Tôi ngủ 8 tiếng."]],
"sleepy":[["tính từ","buồn ngủ"]],
"slept":[["động từ","đã ngủ"]],
"slow":[["tính từ","chậm"]],
"small":[["tính từ","nhỏ"]],
"smaller":[["tính từ","nhỏ hơn"]],
"smallest":[["tính từ","nhỏ nhất"]],
"smile":[["động từ","mỉm cười"]],
"snow":[["danh từ","tuyết"]],
"so":[["trạng từ","vì vậy, rất"]],
"sold":[["động từ","đã bán"]],
"some":[["tính từ","một vài"]],
"somebody":[["đại từ","ai đó"]],
"someone":[["đại từ","ai đó"]],
"something":[["danh từ","thứ gì đó"]],
"sometimes":[["trạng từ","thỉnh thoảng"]],
"son":[["danh từ","con trai"]],
"song":[["danh từ","bài hát"]],
"soon":[["trạng từ","sớm"]],
"sorry":[["tính từ","xin lỗi"]],
"south":[["danh từ","phía nam"]],
"speak":[["động từ","nói","I speak Vietnamese.","Tôi nói tiếng Việt."]],
"special":[["tính từ","đặc biệt"]],
"spent":[["động từ","đã tiêu, đã dành"]],
"spoke":[["động từ","đã nói"]],
"spoken":[["động từ","đã nói"]],
"spring":[["danh từ","mùa xuân"]],
"stand":[["động từ","đứng"]],
"star":[["danh từ","ngôi sao"]],
"start":[["động từ","bắt đầu","Class starts at 7.","Lớp bắt đầu lúc 7 giờ."]],
"started":[["động từ","đã bắt đầu"]],
"station":[["danh từ","nhà ga, bến xe"]],
"stay":[["động từ","ở lại","Stay here.","Ở lại đây đi."]],
"stayed":[["động từ","đã ở lại"]],
"steal":[["động từ","ăn cắp (thứ gì)","He stole my bike.","Anh ta ăn cắp xe đạp của tôi."]],
"still":[["trạng từ","vẫn"]],
"stole":[["động từ","đã ăn cắp"]],
"stood":[["động từ","đã đứng"]],
"stop":[["động từ","dừng lại"]],
"store":[["danh từ","cửa hàng"]],
"storm":[["danh từ","cơn bão"]],
"story":[["danh từ","câu chuyện"]],
"street":[["danh từ","đường phố"]],
"strong":[["tính từ","khỏe, mạnh"]],
"student":[["danh từ","học sinh, sinh viên"]],
"studied":[["động từ","đã học"]],
"study":[["động từ","học","She studies hard.","Cô ấy học chăm."]],
"stupid":[["tính từ","ngốc"]],
"such":[["tính từ","như vậy"]],
"sugar":[["danh từ","đường"]],
"suggest":[["động từ","gợi ý, đề nghị"]],
"summer":[["danh từ","mùa hè"]],
"sun":[["danh từ","mặt trời"]],
"sunday":[["danh từ","chủ nhật"]],
"sunset":[["danh từ","hoàng hôn"]],
"super":[["tính từ","tuyệt vời"]],
"sure":[["tính từ","chắc chắn"]],
"surprise":[["danh từ","bất ngờ"]],
"swam":[["động từ","đã bơi"]],
"swim":[["động từ","bơi"]],
"table":[["danh từ","cái bàn"]],
"take":[["động từ","lấy, mang đi","Take this book.","Cầm cuốn sách này đi."]],
"tall":[["tính từ","cao"]],
"taller":[["tính từ","cao hơn"]],
"tallest":[["tính từ","cao nhất"]],
"tea":[["danh từ","trà"]],
"teach":[["động từ","dạy","She teaches English.","Cô ấy dạy tiếng Anh."]],
"teacher":[["danh từ","giáo viên"]],
"team":[["danh từ","đội"]],
"teeth":[["danh từ","răng"]],
"tell":[["động từ","kể, bảo","Tell me the truth.","Kể tôi nghe sự thật đi."]],
"temperature":[["danh từ","nhiệt độ"]],
"ten":[["số từ","mười"]],
"tennis":[["danh từ","quần vợt"]],
"terrible":[["tính từ","tệ"]],
"than":[["liên từ","hơn, so với"]],
"thank":[["động từ","cảm ơn","Thank you very much.","Cảm ơn bạn rất nhiều."]],
"thanks":[["thán từ","cảm ơn"]],
"that":[["đại từ","kia"]],
"the":[["mạo từ","mạo từ xác định (thường không dịch riêng)"]],
"their":[["tính từ","của họ"]],
"them":[["đại từ","họ, chúng"]],
"then":[["trạng từ","sau đó"]],
"there":[["trạng từ","ở đó"]],
"these":[["đại từ","những cái này"]],
"they":[["đại từ","họ"]],
"thing":[["danh từ","thứ, vật"]],
"think":[["động từ","nghĩ","I think it is good.","Tôi nghĩ nó tốt."]],
"third":[["số từ","thứ ba"]],
"thirsty":[["tính từ","khát"]],
"thirteen":[["số từ","mười ba"]],
"thirty":[["số từ","ba mươi"]],
"this":[["đại từ","này"]],
"those":[["đại từ","những cái kia"]],
"though":[["liên từ","mặc dù"]],
"thought":[["động từ","đã nghĩ"]],
"thousand":[["số từ","một nghìn"]],
"three":[["số từ","ba"]],
"threw":[["động từ","đã ném"]],
"through":[["giới từ","qua"]],
"throw":[["động từ","ném"]],
"thursday":[["danh từ","thứ năm"]],
"ticket":[["danh từ","vé"]],
"tie":[["động từ","buộc"],["danh từ","cà vạt"]],
"time":[["danh từ","thời gian","What time is it?","Mấy giờ rồi?"]],
"tired":[["tính từ","mệt"]],
"to":[["giới từ","đến"]],
"today":[["trạng từ","hôm nay","I am busy today.","Hôm nay tôi bận."],["danh từ","hôm nay"]],
"together":[["trạng từ","cùng nhau"]],
"told":[["động từ","đã kể, đã bảo"]],
"tomorrow":[["trạng từ","ngày mai","See you tomorrow.","Hẹn gặp lại ngày mai."],["danh từ","ngày mai"]],
"tonight":[["trạng từ","tối nay","What are you doing tonight?","Tối nay bạn làm gì?"]],
"too":[["trạng từ","quá, cũng"]],
"tooth":[["danh từ","cái răng"]],
"top":[["danh từ","đỉnh"]],
"tore":[["động từ","đã xé"]],
"toward":[["giới từ","về phía"]],
"towards":[["giới từ","về phía"]],
"town":[["danh từ","thị trấn"]],
"train":[["danh từ","tàu hỏa"]],
"travel":[["động từ","du lịch","I travel to Sa Pa every year.","Năm nào tôi cũng du lịch Sa Pa."]],
"tree":[["danh từ","cây"]],
"tried":[["động từ","đã cố gắng"]],
"trip":[["danh từ","chuyến đi"]],
"true":[["tính từ","đúng sự thật"]],
"truth":[["danh từ","sự thật"]],
"try":[["động từ","cố gắng","Try again.","Thử lại đi."]],
"tuesday":[["danh từ","thứ ba"]],
"turn":[["động từ","rẽ, xoay"]],
"twice":[["trạng từ","hai lần"]],
"two":[["số từ","hai"]],
"umbrella":[["danh từ","cái ô"]],
"under":[["giới từ","dưới"]],
"understand":[["động từ","hiểu","I understand.","Tôi hiểu rồi."]],
"understood":[["động từ","đã hiểu"]],
"university":[["danh từ","trường đại học","She studies at a university.","Cô ấy học đại học."]],
"until":[["liên từ","cho đến khi"]],
"up":[["trạng từ","lên"]],
"us":[["đại từ","chúng tôi"]],
"use":[["động từ","dùng","I use a pen.","Tôi dùng một cây bút."]],
"used":[["động từ","đã từng"]],
"usually":[["trạng từ","thường"]],
"vegetable":[["danh từ","rau"]],
"very":[["trạng từ","rất"]],
"video":[["danh từ","video"]],
"vietnam":[["danh từ","Việt Nam"]],
"vietnamese":[["tính từ","thuộc Việt Nam"],["danh từ","tiếng Việt, người Việt"]],
"view":[["danh từ","khung cảnh"],["động từ","xem, ngắm"]],
"visit":[["động từ","thăm","I visit my grandmother.","Tôi thăm bà ngoại."]],
"visited":[["động từ","đã thăm"]],
"voice":[["danh từ","giọng nói"]],
"volleyball":[["danh từ","bóng chuyền"]],
"wage":[["danh từ","tiền công (theo giờ hoặc ngày)"]],
"wait":[["động từ","chờ","Wait for me.","Chờ tôi nhé."]],
"waited":[["động từ","đã chờ"]],
"walk":[["động từ","đi bộ","We walk to school.","Chúng tôi đi bộ đến trường."]],
"walked":[["động từ","đã đi bộ"]],
"wall":[["danh từ","bức tường"]],
"want":[["động từ","muốn","I want a cup of tea.","Tôi muốn một tách trà."]],
"wanted":[["động từ","đã muốn"]],
"war":[["danh từ","chiến tranh"]],
"warm":[["tính từ","ấm"]],
"was":[["động từ","đã là, đã ở"]],
"watch":[["động từ","xem","I watch TV every night.","Tối nào tôi cũng xem ti vi."]],
"water":[["danh từ","nước"]],
"way":[["danh từ","cách, đường"]],
"we":[["đại từ","chúng tôi"]],
"weak":[["tính từ","yếu"]],
"wear":[["động từ","mặc"]],
"weather":[["danh từ","thời tiết"]],
"wednesday":[["danh từ","thứ tư"]],
"week":[["danh từ","tuần","See you next week.","Hẹn gặp tuần sau."]],
"weekend":[["danh từ","cuối tuần"]],
"welcome":[["tính từ","được chào đón"]],
"well":[["trạng từ","tốt, khỏe"]],
"went":[["động từ","đã đi"]],
"were":[["động từ","đã là, đã ở"]],
"west":[["danh từ","phía tây"]],
"what":[["đại từ","cái gì"]],
"when":[["trạng từ","khi nào"]],
"where":[["trạng từ","ở đâu"]],
"which":[["đại từ","cái nào"]],
"while":[["liên từ","trong khi"]],
"white":[["tính từ","trắng"]],
"who":[["đại từ","ai","Who is that?","Kia là ai?"]],
"whole":[["tính từ","toàn bộ"]],
"whom":[["đại từ","người mà","The man whom I met is my teacher.","Người đàn ông tôi gặp là thầy tôi."]],
"whose":[["đại từ","của ai"]],
"why":[["trạng từ","tại sao"]],
"wide":[["tính từ","rộng"]],
"wife":[["danh từ","vợ"]],
"wild":[["tính từ","hoang dã"]],
"will":[["động từ","sẽ"]],
"win":[["động từ","thắng"]],
"wind":[["danh từ","gió"]],
"window":[["danh từ","cửa sổ"]],
"wine":[["danh từ","rượu vang"]],
"wing":[["danh từ","cánh"]],
"winter":[["danh từ","mùa đông"]],
"wish":[["động từ","ước, mong"],["danh từ","lời chúc"]],
"with":[["giới từ","với"]],
"without":[["giới từ","không có"]],
"woman":[["danh từ","phụ nữ"]],
"women":[["danh từ","phụ nữ"]],
"wonderful":[["tính từ","tuyệt vời"]],
"wood":[["danh từ","gỗ"]],
"word":[["danh từ","từ"]],
"work":[["động từ","làm việc","I work in Da Lat.","Tôi làm việc ở Đà Lạt."],["danh từ","công việc"]],
"worked":[["động từ","đã làm việc"]],
"world":[["danh từ","thế giới"]],
"worse":[["tính từ","tệ hơn"]],
"worst":[["tính từ","tệ nhất"]],
"worth":[["tính từ","đáng"]],
"would":[["động từ","sẽ"]],
"write":[["động từ","viết","I write a letter.","Tôi viết một lá thư."]],
"writer":[["danh từ","nhà văn"]],
"wrong":[["tính từ","sai"]],
"year":[["danh từ","năm"]],
"yellow":[["tính từ","vàng"]],
"yes":[["trạng từ","vâng, có"]],
"yesterday":[["trạng từ","hôm qua","I saw her yesterday.","Hôm qua tôi gặp cô ấy."],["danh từ","hôm qua"]],
"yet":[["trạng từ","chưa"]],
"you":[["đại từ","bạn"]],
"young":[["tính từ","trẻ"]],
"your":[["tính từ","của bạn"]],
"zero":[["số từ","không"]]
};
  function posVi(p){return VI_POS[String(p||"").toLowerCase()]||String(p||"");}
  function clean(s){return String(s||"").replace(/-/g," ").replace(/\s+/g," ").trim();}
  function stemForms(w){
    const out=[w];
    const push=function(s){if(s&&s.length>=2&&out.indexOf(s)<0)out.push(s);};
    if(w.endsWith("'s"))push(w.slice(0,-2));
    if(w.endsWith("ies")&&w.length>4){push(w.slice(0,-3)+"y");push(w.slice(0,-3)+"ie");}
    else if(w.endsWith("es")&&w.length>3){push(w.slice(0,-2));push(w.slice(0,-1));}
    else if(w.endsWith("s")&&w.length>3)push(w.slice(0,-1));
    const destem=function(base){
      push(base);
      if(base.length>=3&&base[base.length-1]===base[base.length-2])push(base.slice(0,-1));
      push(base+"e");
    };
    if(w.endsWith("ing")&&w.length>4)destem(w.slice(0,-3));
    if(w.endsWith("ed")&&w.length>4)destem(w.slice(0,-2));
    return out;
  }
  function glossaryHit(w){
    const forms=stemForms(w);
    for(let i=0;i<forms.length;i++){
      if(VI_GLOSSARY[forms[i]])return {word:forms[i],senses:VI_GLOSSARY[forms[i]]};
    }
    return null;
  }
  function loadRecent(){
    try{return JSON.parse(localStorage.getItem(RECENT_KEY)||"[]");}catch(e){return [];}
  }
  function saveRecent(w){
    try{
      let r=loadRecent().filter(x=>x!==w);
      r.unshift(w);
      localStorage.setItem(RECENT_KEY,JSON.stringify(r.slice(0,8)));
    }catch(e){}
  }
  function renderRecent(){
    if(!recentBox)return;
    const r=loadRecent();
    if(!r.length){recentBox.innerHTML="<p>Từ đã tra gần đây: Chưa tra từ nào. Gõ 1 từ tiếng Anh ở trên nhé.</p>";return;}
    recentBox.innerHTML="<p>Từ đã tra gần đây: "+r.map(w=>"<button type=\"button\" class=\"dict-chip\" data-word=\""+escapeHtml(w)+"\">"+escapeHtml(w)+"</button>").join(" ")+"</p>";
    bindChips(recentBox);
  }
  function audioLabel(ph){
    const a=String(ph.audio||"");
    if(/-uk\./i.test(a))return "giọng Anh";
    if(/-us\./i.test(a))return "giọng Mỹ";
    if(/-au\./i.test(a))return "giọng Úc";
    return "phát âm";
  }
  function pickPhonetics(phs){
    const uk=phs.find(p=>/-uk\./i.test(p.audio||""));
    const us=phs.find(p=>/-us\./i.test(p.audio||""));
    const out=[];
    if(uk)out.push({label:"giọng Anh",text:uk.text||"",audio:uk.audio||""});
    if(us)out.push({label:"giọng Mỹ",text:us.text||"",audio:us.audio||""});
    if(out.length<2){
      phs.forEach(p=>{
        if(out.length>=2)return;
        if(p.text&&!out.some(o=>o.text===p.text))out.push({label:p.audio?audioLabel(p):"phiên âm",text:p.text,audio:p.audio||""});
      });
    }
    return out.slice(0,2);
  }
  function parseWiki(extract,word){
    const text=String(extract||"");
    const start=text.search(/==\s*Tiếng Anh\s*==/);
    const body=start>=0?text.slice(start):text;
    const lines=body.split("\n");
    const senses=[];
    let cur=null;
    const dash="\u2014";
    lines.forEach(raw=>{
      const line=raw.trim();
      const h=line.match(/^===\s*([^=].*?)\s*===$/);
      if(h){
        const label=WIKI_POS[h[1].trim()];
        cur=null;
        if(label){
          const count=senses.filter(s=>s.pos===label).length;
          if(count<3)cur={pos:label,vi:"",ex:[]};
          if(cur)senses.push(cur);
        }
        return;
      }
      if(/^=/.test(line)){cur=null;return;}
      if(!cur)return;
      if(!line)return;
      if(line.indexOf(word)===0)return;
      if(/\//.test(line)&&line.length<80)return;
      if(/^(Vần|Tách âm|IPA|enPR|Đồng nghĩa|Trái nghĩa|Chia động từ|Tham khảo|Từ nguyên)/.test(line))return;
      const parts=line.split(" "+dash+" ");
      if(parts.length>=2){
        if(cur.ex.length<2)cur.ex.push({en:clean(parts[0]),vi:clean(parts.slice(1).join(" "))});
        return;
      }
      if(!cur.vi&&line.length>1&&line.length<120)cur.vi=clean(line);
      else if(cur.vi&&line.length>1&&line.length<120&&senses.filter(s=>s.pos===cur.pos).length<3&&cur.ex.length===0){
        const prev=senses[senses.length-1];
        if(prev===cur){
          const extra={pos:cur.pos,vi:clean(line),ex:[]};
          senses.push(extra);
        }
      }
    });
    return senses.filter(s=>s.vi||s.ex.length).slice(0,4);
  }
  function fetchWiki(word){
    return fetch("https://vi.wiktionary.org/w/api.php?action=query&prop=extracts&explaintext=1&titles="+encodeURIComponent(word)+"&format=json&origin=*")
      .then(r=>r.json())
      .then(d=>{
        const pages=d&&d.query&&d.query.pages?Object.values(d.query.pages):[];
        const page=pages[0];
        if(!page||page.missing!==undefined||!page.extract)return null;
        return parseWiki(page.extract,word);
      })
      .catch(()=>null);
  }
  function translateMT(text){
    return fetch("https://api.mymemory.translated.net/get?q="+encodeURIComponent(text)+"&langpair=en|vi")
      .then(r=>r.json())
      .then(d=>{
        const t=d&&d.responseData?d.responseData.translatedText:"";
        if(!t||/MYMEMORY WARNING/i.test(t)||d.responseStatus===429)return null;
        return clean(t);
      })
      .catch(()=>null);
  }
  function normText(s){return String(s||"").toLowerCase().replace(/[^a-z0-9 ]/g,"").replace(/\s+/g," ").trim();}
  function exampleVi(exEn,senses){
    if(!senses)return null;
    const want=normText(exEn);
    for(let i=0;i<senses.length;i++){
      const ex=senses[i].ex||[];
      for(let j=0;j<ex.length;j++){
        if(ex[j].en&&normText(ex[j].en)===want)return ex[j].vi;
      }
    }
    return null;
  }
  function viSensesFromGlossary(g){
    return g.senses.map(s=>({pos:s[0],vi:s[1],ex:(s[2]&&s[3])?[{en:s[2],vi:s[3]}]:[]}));
  }
  function bindAudio(){
    if(!box)return;
    box.querySelectorAll(".audio-btn").forEach(b=>b.addEventListener("click",()=>{
      try{const a=new Audio(b.dataset.audio);a.play().catch(()=>{});}catch(e){}
    }));
  }
  function renderViSenses(html,senses,source){
    html+="<p class=\"dict-sec\">Nghĩa tiếng Việt</p>";
    let lastPos="";
    senses.slice(0,4).forEach(s=>{
      if(s.pos!==lastPos){html+="<p class=\"dict-pos\">"+escapeHtml(s.pos)+"</p>";lastPos=s.pos;}
      html+="<p class=\"dict-vi\">"+escapeHtml(s.vi)+"</p>";
      (s.ex||[]).slice(0,2).forEach(e=>{
        html+="<p class=\"dict-ex\">Ví dụ: "+escapeHtml(clean(e.en))+"</p>";
        html+="<p class=\"dict-ex-vi\">Dịch: "+escapeHtml(clean(e.vi))+"</p>";
      });
    });
    html+="<p class=\"dict-tag\">Nghĩa tiếng Việt: "+escapeHtml(source)+".</p>";
    return html;
  }
  function renderViOnly(word,senses,source){
    saveRecent(word);renderRecent();
    let html="<h2 class=\"dict-word\">"+escapeHtml(word)+"</h2>";
    html=renderViSenses(html,senses,source);
    html+="<p class=\"dict-src\">Đọc thêm: <a href=\"https://dictionary.cambridge.org/dictionary/english/"+encodeURIComponent(word)+"\" target=\"_blank\" rel=\"noopener\">Cambridge</a> • <a href=\"https://www.oxfordlearnersdictionaries.com/definition/english/"+encodeURIComponent(word)+"\" target=\"_blank\" rel=\"noopener\">Oxford</a></p>";
    if(box)box.innerHTML=html;
  }
  function renderEntry(entry,word,viSenses,viSource){
    saveRecent(entry.word||word);renderRecent();
    let html="<h2 class=\"dict-word\">"+escapeHtml(entry.word||word)+"</h2>";
    const phs=pickPhonetics((entry.phonetics||[]).filter(p=>p&&(p.text||p.audio)));
    phs.forEach(p=>{
      html+="<p class=\"dict-phon\">"+escapeHtml(p.label)+": <b>"+escapeHtml(p.text||"")+"</b>";
      if(p.audio)html+=" <button type=\"button\" class=\"audio-btn\" data-audio=\""+escapeHtml(p.audio)+"\">Nghe "+escapeHtml(p.label)+"</button>";
      html+="</p>";
    });
    if(viSenses&&viSenses.length){
      html=renderViSenses(html,viSenses,viSource);
    }else{
      html+="<p class=\"note warn\">Chưa có nghĩa tiếng Việt cho từ này. Xem nghĩa tiếng Anh bên dưới, hoặc đọc thêm ở Cambridge và Oxford.</p>";
    }
    html+="<p class=\"dict-sec\">Nghĩa tiếng Anh</p>";
    const mtJobs=[];
    (entry.meanings||[]).slice(0,4).forEach((m,mi)=>{
      html+="<p class=\"dict-pos\">"+escapeHtml(posVi(m.partOfSpeech))+"</p>";
      (m.definitions||[]).slice(0,3).forEach((d,di)=>{
        const def=clean(d.definition||"");
        html+="<p class=\"dict-def-en\">"+escapeHtml(def)+"</p>";
        if(!viSenses&&def){
          const id="mt-"+mi+"-"+di;
          html+="<p class=\"dict-mt\" id=\""+id+"\">Đang dịch nghĩa này…</p>";
          mtJobs.push({id:id,text:def,isEx:false});
        }
        if(d.example){
          html+="<p class=\"dict-ex\">Ví dụ: "+escapeHtml(clean(d.example))+"</p>";
          const exVi=exampleVi(d.example,viSenses);
          if(exVi)html+="<p class=\"dict-ex-vi\">Dịch: "+escapeHtml(clean(exVi))+"</p>";
          else{
            const eid="mtex-"+mi+"-"+di;
            html+="<p class=\"dict-mt\" id=\""+eid+"\">Đang dịch ví dụ…</p>";
            mtJobs.push({id:eid,text:d.example,isEx:true});
          }
        }
      });
      const syn=(m.synonyms||[]).slice(0,5);
      if(syn.length){
        html+="<p class=\"dict-def\">Từ gần nghĩa: "+syn.map(s=>{
          const gh=glossaryHit(String(s).toLowerCase());
          const gloss=gh?(" ("+escapeHtml(gh.senses[0][1])+")"):"";
          return escapeHtml(clean(s))+gloss;
        }).join(", ")+"</p>";
      }
    });
    html+="<p class=\"dict-src\">Đọc thêm: <a href=\"https://dictionary.cambridge.org/dictionary/english/"+encodeURIComponent(entry.word||word)+"\" target=\"_blank\" rel=\"noopener\">Cambridge</a> • <a href=\"https://www.oxfordlearnersdictionaries.com/definition/english/"+encodeURIComponent(word)+"\" target=\"_blank\" rel=\"noopener\">Oxford</a></p>";
    html+="<p class=\"dict-src-small\">Phát âm và nghĩa tiếng Anh: từ điển mở dictionaryapi.dev.</p>";
    if(box)box.innerHTML=html;
    bindAudio();
    mtJobs.slice(0,4).reduce((chain,job)=>{
      return chain.then(()=>translateMT(job.text)).then(t=>{
        const el=document.getElementById(job.id);
        if(!el)return;
        if(t)el.textContent=(job.isEx?"Dịch ví dụ: ":"")+t+" (dịch máy, chưa kiểm chứng)";
        else el.textContent=job.isEx?"Chưa dịch được ví dụ này.":"Chưa dịch được nghĩa này, xem nghĩa tiếng Anh ở trên.";
      });
    },Promise.resolve());
  }
  function lookup(word){
    word=String(word||"").trim().toLowerCase();
    if(!word)return;
    if(!/^[a-z][a-z' ]{0,40}$/.test(word)){
      if(box)box.innerHTML="<p class=\"note warn\">Từ tra chỉ gồm chữ cái tiếng Anh, ví dụ: comfortable, borrow.</p>";
      return;
    }
    if(box)box.innerHTML="<p>Đang tra từ <b>"+escapeHtml(word)+"</b>…</p>";
    const g=glossaryHit(word);
    fetch("https://api.dictionaryapi.dev/api/v2/entries/en/"+encodeURIComponent(word))
      .then(r=>{if(!r.ok)throw new Error("notfound");return r.json();})
      .then(async data=>{
        const entry=Array.isArray(data)?data[0]:null;
        if(!entry||!entry.meanings||!entry.meanings.length)throw new Error("notfound");
        let viSenses=null,viSource="";
        if(g){viSenses=viSensesFromGlossary(g);viSource="Trang soạn";}
        else{
          const wk=await fetchWiki(word);
          if(wk&&wk.length){viSenses=wk;viSource="Wiktionary tiếng Việt";}
        }
        renderEntry(entry,word,viSenses,viSource);
      })
      .catch(async err=>{
        if(err&&err.message==="notfound"){
          const gg=glossaryHit(word);
          if(gg){renderViOnly(word,viSensesFromGlossary(gg),"Trang soạn");return;}
          const wk=await fetchWiki(word);
          if(wk&&wk.length){renderViOnly(word,wk,"Wiktionary tiếng Việt");return;}
          if(box)box.innerHTML="<p class=\"note warn\">Không tìm thấy từ <b>"+escapeHtml(word)+"</b> trong từ điển. Kiểm tra chính tả rồi thử lại, hoặc thử từ khác.</p>";
        }else{
          if(box)box.innerHTML="<p class=\"note warn\">Không tải được từ điển lúc này. Kiểm tra mạng rồi thử lại nhé.</p>";
        }
      });
  }
  function bindChips(scope){
    (scope||document).querySelectorAll(".dict-chip").forEach(c=>c.addEventListener("click",()=>{
      if(input)input.value=c.dataset.word||c.textContent;
      lookup(c.dataset.word||c.textContent);
    }));
  }
  if(btn)btn.addEventListener("click",()=>lookup(input?input.value:""));
  if(input)input.addEventListener("keydown",e=>{if(e.key==="Enter")lookup(input.value);});
  bindChips(document);
  renderRecent();
})();
</script>
"""

DASH_JS = r"""
<script>
function renderDashboard(){
  const p=getProgress();
  const sp=loadSpeaking();
  const total=window.SDSC_TOTAL_LESSONS||0;
  const done=Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).length;
  const prac=Object.values(p.practice||{});
  const acc=prac.length?Math.round(100*prac.filter(v=>v&&v.correct).length/prac.length):0;
  const set=(id,t)=>{const el=document.getElementById(id);if(el)el.textContent=t;};
  set("dash-done",done+" / "+total+" bài");
  set("dash-acc",acc+"%");
  set("dash-speak",(sp.sessions||0)+" buổi");
  set("dash-hours",speakingHoursText(sp.minutes||0));
  set("dash-streak",(p.streak.count||0)+" ngày");
  set("dash-best",(sp.best||0)+" điểm");
  const paths=window.SDSC_PATHS||{};
  const pathNames=PATH_NAMES_PLACEHOLDER;
  const wrap=document.getElementById("dash-paths");
  if(wrap){
    wrap.innerHTML=Object.keys(paths).map(slug=>{
      const order=(paths[slug]||[]).filter(s=>window.SDSC_LESSONS[s]);
      const d=order.filter(s=>{const L=p.lessons[s];return L&&L.done;}).length;
      const pct=order.length?Math.round(100*d/order.length):0;
      const next=order.find(s=>{const L=p.lessons[s];return !(L&&L.done);});
      const nextHtml=next?("<p>Bài tiếp theo: <a href=\""+BASE_PATH_PLACEHOLDER+"/"+next+"/\">"+escapeHtml((window.SDSC_LESSONS[next]||{}).code||"")+" "+escapeHtml((window.SDSC_LESSONS[next]||{}).title||"")+"</a></p>"):("<p>Đã xong lộ trình này rồi. Giỏi quá!</p>");
      return "<div class=\"progress\"><h3>"+escapeHtml(pathNames[slug]||slug)+"</h3><div class=\"bar\"><i style=\"width:"+pct+"%\"></i></div><p>"+d+" / "+order.length+" bài đã nhớ ("+pct+"%)</p>"+nextHtml+"</div>";
    }).join("");
  }
  const orderAll=(paths["hoc-lai-tu-dau"]||[]).filter(s=>window.SDSC_LESSONS[s]);
  let next=orderAll.find(s=>{const L=p.lessons[s];return !(L&&L.done);});
  if(!next){next=Object.keys(window.SDSC_LESSONS).find(s=>{const L=p.lessons[s];return !(L&&L.done);});}
  const nx=document.getElementById("dash-next");
  if(nx){
    if(next){const l=window.SDSC_LESSONS[next];nx.innerHTML="<p><b>"+escapeHtml(l.code)+": "+escapeHtml(l.title)+"</b><br>"+escapeHtml(l.why)+"</p><a class=\"btn btn-primary btn-block\" href=\""+BASE_PATH_PLACEHOLDER+"/"+next+"/\">Học bài này</a>";}
    else{nx.innerHTML="<p>Bạn đã học hết "+total+" bài rồi. Giỏi quá! Hôm nay ôn lại nhé.</p><a class=\"btn btn-navy\" href=\""+BASE_PATH_PLACEHOLDER+"/thu-vien-chu-de/\">Ôn trong Thư viện chủ đề</a>";}
  }
  const today=todayISO();
  const due=[];
  Object.entries(p.review||{}).forEach(([slug,r])=>{
    if(!r||!window.SDSC_LESSONS[slug])return;
    const L=p.lessons[slug];
    if(!L||!L.done)return;
    if(isValidDateStr(r.nextDue)&&r.nextDue<=today)due.push({slug:slug,nextDue:r.nextDue});
  });
  due.sort((a,b)=>a.nextDue.localeCompare(b.nextDue));
  const dg=document.getElementById("dash-due");
  if(dg){
    if(!due.length){dg.innerHTML="<p>Hôm nay chưa có bài đến hạn. Học xong 1 bài rồi bấm “Tôi đã nhớ bài này” nhé.</p>";}
    else{dg.innerHTML="<div class=\"review-grid\">"+due.slice(0,5).map(x=>{const l=window.SDSC_LESSONS[x.slug];return "<a class=\"review-card\" href=\""+BASE_PATH_PLACEHOLDER+"/"+x.slug+"/\"><b>"+escapeHtml(l.code)+"</b><span>"+escapeHtml(l.title)+"<br>Đến hạn ôn ngày "+escapeHtml(fmtDate(x.nextDue))+"</span></a>";}).join("")+"</div>";}
  }
}
try{renderDashboard();}catch(e){}
window.addEventListener("storage",e=>{if(e&&e.key==="sdsc-progress-v1"){try{renderDashboard();}catch(err){}}});
</script>
"""

LIB_JS = r"""
<script>
(function(){
  function libNorm(s){return String(s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/đ/g,"d").replace(/[^a-z0-9\s]/g," ").replace(/\s+/g," ").trim();}
  const q=document.getElementById("lib-search");
  const chips=document.querySelectorAll("#lib-chips .chip");
  const groups=[...document.querySelectorAll(".lib-group")];
  const cards=[...document.querySelectorAll(".lib-group .card")];
  const count=document.getElementById("lib-count");
  let topic="Tất cả";
  function apply(){
    const needle=libNorm(q?q.value:"");
    let shown=0;
    cards.forEach(c=>{
      const okT=topic==="Tất cả"||c.dataset.topic===topic;
      const hay=libNorm(c.dataset.search||"");
      const okQ=!needle||needle.split(" ").every(t=>hay.indexOf(t)>=0);
      const show=okT&&okQ;
      c.style.display=show?"":"none";
      if(show)shown++;
    });
    groups.forEach(g=>{
      const any=[...g.querySelectorAll(".card")].some(c=>c.style.display!=="none");
      g.style.display=any?"":"none";
    });
    if(count)count.textContent=shown+" bài khớp.";
  }
  chips.forEach(ch=>ch.addEventListener("click",()=>{
    topic=ch.dataset.topic||"Tất cả";
    chips.forEach(c=>c.classList.toggle("on",c===ch));
    apply();
  }));
  let t=null;
  if(q)q.addEventListener("input",()=>{clearTimeout(t);t=setTimeout(apply,150);});
  apply();
})();
</script>
"""

SPEAK_JS = r"""
<script>
(function(){
  const sentences=window.SDSC_SPEAK||[];
  const sel=document.getElementById("speak-pick");
  const targetEl=document.getElementById("speak-target");
  const viEl=document.getElementById("speak-vi");
  const listenBtn=document.getElementById("speak-listen");
  const startBtn=document.getElementById("speak-start");
  const stopBtn=document.getElementById("speak-stop");
  const statusEl=document.getElementById("speak-status");
  const heardBox=document.getElementById("speak-heard");
  const scoreBox=document.getElementById("speak-score");
  const statsEl=document.getElementById("speak-stats");
  const noSupport=document.getElementById("speak-nosupport");
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  const ERR_TEXT={"no-speech":"Máy không nghe thấy gì. Thử lại nhé.","audio-capture":"Không mở được micro. Thử lại nhé.","not-allowed":"Trình duyệt chưa cho phép dùng micro. Bấm cho phép micro rồi thử lại nhé.","network":"Mất mạng lúc nhận diện giọng nói. Kiểm tra mạng rồi thử lại nhé.","aborted":"Đã dừng nghe.","language-not-supported":"Trình duyệt này chưa hỗ trợ nhận diện tiếng Anh."};
  let rec=null, startedAt=null, finalText="", cur=null;
  function showStats(){
    const sp=loadSpeaking();
    if(statsEl)statsEl.textContent="Bạn đã luyện nói "+(sp.sessions||0)+" buổi, tổng "+speakingHoursText(sp.minutes||0)+", điểm tốt nhất "+(sp.best||0)+" điểm.";
  }
  function normWords(s){
    return String(s||"").toLowerCase().replace(/[^a-z0-9'\s]/g," ").replace(/\s+/g," ").trim().split(" ").filter(Boolean);
  }
  function scoreIt(target,heard){
    const t=normWords(target), h=normWords(heard);
    if(!t.length||!h.length)return {pct:0,missed:t};
    const hset={};h.forEach(w=>{hset[w]=(hset[w]||0)+1;});
    let hit=0;const missed=[];
    t.forEach(w=>{if(hset[w]>0){hset[w]--;hit++;}else missed.push(w);});
    return {pct:Math.round(100*hit/t.length),missed:missed};
  }
  function pick(i){
    cur=sentences[i]||sentences[0];
    if(!cur)return;
    if(targetEl)targetEl.textContent=cur.en;
    if(viEl)viEl.textContent=cur.vi||"";
    if(listenBtn)listenBtn.dataset.say=cur.en;
    if(heardBox)heardBox.innerHTML="";
    if(scoreBox)scoreBox.innerHTML="";
  }
  function paramSentence(){
    try{
      const q=new URLSearchParams(location.search);
      const s=q.get("s");
      if(!s)return -1;
      return sentences.findIndex(x=>x.en===s);
    }catch(e){return -1;}
  }
  if(sel){
    sel.innerHTML=sentences.map((s,i)=>"<option value=\""+i+"\">"+escapeHtml(s.code+": "+s.en)+"</option>").join("");
    sel.addEventListener("change",()=>pick(parseInt(sel.value,10)||0));
  }
  if(listenBtn)listenBtn.addEventListener("click",()=>{if(cur)speak(cur.en,listenBtn);});
  if(!SR){
    if(noSupport)noSupport.style.display="block";
    if(startBtn)startBtn.disabled=true;
    if(statusEl)statusEl.textContent="Trình duyệt này chưa hỗ trợ nhận diện giọng nói.";
  }else if(startBtn){
    startBtn.addEventListener("click",()=>{
      if(!cur)return;
      try{rec=new SR();}catch(e){if(statusEl)statusEl.textContent="Không mở được micro, thử lại nhé.";return;}
      rec.lang="en-US";rec.interimResults=true;rec.continuous=false;rec.maxAlternatives=1;
      finalText="";startedAt=Date.now();
      if(statusEl)statusEl.innerHTML="<span class=\"rec-dot\"></span>Đang nghe… nói câu trên nhé.";
      if(startBtn)startBtn.disabled=true;
      if(stopBtn)stopBtn.disabled=false;
      rec.onresult=e=>{
        let interim="",fin="";
        for(let i=e.resultIndex;i<e.results.length;i++){
          if(e.results[i].isFinal)fin+=e.results[i][0].transcript;
          else interim+=e.results[i][0].transcript;
        }
        if(fin)finalText+=fin;
        if(heardBox)heardBox.textContent="Máy đang nghe: "+(finalText+interim);
      };
      rec.onerror=e=>{
        if(statusEl)statusEl.textContent=ERR_TEXT[(e&&e.error)||""]||"Máy chưa nghe được. Thử lại nhé, nói rõ và gần micro hơn.";
        if(startBtn)startBtn.disabled=false;
        if(stopBtn)stopBtn.disabled=true;
      };
      rec.onend=()=>{
        if(startBtn)startBtn.disabled=false;
        if(stopBtn)stopBtn.disabled=true;
        const heard=(finalText||"").trim();
        if(!heard){if(statusEl)statusEl.textContent="Máy không nghe thấy gì. Thử lại nhé.";return;}
        const mins=startedAt?(Date.now()-startedAt)/60000:0;
        const r=scoreIt(cur.en,heard);
        const words=normWords(heard).length;
        recordSpeaking(mins,words,r.pct);
        showStats();
        if(heardBox)heardBox.innerHTML="Máy nghe được: <b>"+escapeHtml(heard)+"</b>"+(r.missed.length?"<br>Từ máy chưa nghe rõ: "+escapeHtml(r.missed.join(", ")):"");
        let band="", cls="mid";
        if(r.pct>=90){band="Gần như chuẩn rồi. Giỏi quá!";cls="good";}
        else if(r.pct>=70){band="Khá lắm, còn vài từ chưa rõ. Nghe lại câu mẫu rồi nói lại nhé.";cls="mid";}
        else if(r.pct>=50){band="Máy nghe được một nửa. Đọc chậm lại, nhấn rõ từng từ nhé.";cls="mid";}
        else{band="Máy chưa nghe rõ. Thử lại nhé, nói chậm và gần micro hơn.";cls="low";}
        if(scoreBox)scoreBox.innerHTML="<p class=\"speak-score "+cls+"\">"+r.pct+" điểm</p><p>"+band+"</p>";
        if(statusEl)statusEl.textContent="Xong 1 lượt luyện nói.";
      };
      try{rec.start();}catch(e){if(statusEl)statusEl.textContent="Không mở được micro, thử lại nhé.";if(startBtn)startBtn.disabled=false;if(stopBtn)stopBtn.disabled=true;}
    });
  }
  if(stopBtn)stopBtn.addEventListener("click",()=>{try{if(rec)rec.stop();}catch(e){}});
  const pi=paramSentence();
  if(sel&&pi>=0){sel.value=String(pi);}
  pick(pi>=0?pi:0);
  showStats();
})();
</script>
"""


def grade_block(key, title, question, prompt, options, answer, explanation, retry=True):
    letters = ["A", "B", "C", "D"]
    opts = "".join(
        f'<button type="button" class="opt" data-i="{i}">'
        f'<span class="letter">{letters[i]}</span><span>{esc(opt)}</span></button>'
        for i, opt in enumerate(options)
    )
    prompt_html = f'<p class="prompt">{esc(prompt)}</p>' if prompt else ""
    retry_html = (
        '<button type="button" class="grade-retry">Làm lại</button>' if retry else ""
    )
    return f"""
<div class="grade" data-key="{esc(key)}" data-answer="{answer}" data-explain="{esc(explanation)}">
  <h3>{esc(title)}</h3>
  <p class="q">{esc(question)}</p>
  {prompt_html}
  <div class="opts">{opts}</div>
  <div class="grade-result"></div>
  {retry_html}
</div>
"""


def word_order_block(key, title, prompt, options, answer, explanation, display_order):
    chips = "".join(
        f'<button type="button" class="wo-chip" data-i="{i}">{esc(options[i])}</button>'
        for i in display_order
    )
    return f"""
<div class="grade-wo" data-key="{esc(key)}" data-answer="{esc(json.dumps(answer))}" data-options="{esc(json.dumps(options, ensure_ascii=False))}" data-explain="{esc(explanation)}">
  <h3>{esc(title)}</h3>
  <p class="q">{esc(prompt)}</p>
  <div class="wo-picked"></div>
  <div class="wo-chips">{chips}</div>
  <p><button type="button" class="btn btn-navy wo-check">Kiểm tra</button>
  <button type="button" class="grade-retry wo-retry">Làm lại</button></p>
  <div class="grade-result"></div>
  <p class="wo-answer" style="display:none"></p>
</div>
"""


def quiz_block(lesson):
    q = lesson["quiz"]
    prompt = q.get("prompt", "").strip()
    question_norm = q["question"].strip().lower().lstrip("từ ").strip()
    show_prompt = prompt and prompt.lower() not in question_norm
    return grade_block(
        f"{lesson['slug']}:q",
        "Quiz: làm thử ngay",
        q["question"],
        prompt if show_prompt else "",
        q["options"],
        q["answer"],
        q["explanation"],
    )


def practice_blocks(lesson):
    import random
    out = []
    for i, p in enumerate(lesson.get("practice", [])):
        if p.get("kind") == "word_order":
            order = list(range(len(p["options"])))
            random.Random(f"{lesson['slug']}:{i}").shuffle(order)
            out.append(
                word_order_block(
                    f"{lesson['slug']}:{i}",
                    f"Luyện {i + 1}: xếp từ thành câu",
                    p["prompt"],
                    p["options"],
                    p["answer"],
                    p["explanation"],
                    order,
                )
            )
        else:
            out.append(
                grade_block(
                    f"{lesson['slug']}:{i}",
                    f"Luyện {i + 1}",
                    p["prompt"],
                    "",
                    p["options"],
                    p["answer"],
                    p["explanation"],
                )
            )
    return "\n".join(out)


def right_box(lesson):
    note = lesson.get("right_note", "")
    note_html = f'<br><span style="font-size:16px;font-weight:400">{esc(note)}</span>' if note else ""
    return (
        f'<div class="box right"><small>✓ CÂU ĐÚNG</small>'
        f'<p>{esc(lesson["right"])}{listen_btn(lesson["right"])}{note_html}</p></div>'
    )


def wrong_box(lesson):
    note = lesson.get("wrong_note", "")
    # Dịch nghĩa chỉ hiện 1 lần: nếu trùng với câu đúng thì bỏ ở ô Sai.
    if note and note == lesson.get("right_note", ""):
        note = ""
    note_html = f'<br><span style="font-size:16px;font-weight:400">{esc(note)}</span>' if note else ""
    return (
        f'<div class="box wrong"><small>✗ CÂU SAI</small>'
        f'<p>{esc(lesson["wrong"])}{note_html}</p></div>'
    )


def why_html(lesson):
    return f'<p class="explain"><b>Vì sao:</b> {esc(lesson["why"])}</p>'


def remember_html(lesson):
    return '<div class="remember"><b>' + ICON['bookmark'] + ' Nhớ điều này:</b> ' + esc(lesson['remember']) + '</div>'


def ipa_html(lesson):
    parts = []
    if lesson.get("ipa"):
        for entry in lesson["ipa"]:
            parts.append(
                f'<p class="ipa">IPA ({esc(entry["source"])}): <b>{esc(entry["text"])}</b>'
                f': {esc(entry["note"])}</p>'
            )
        words = ipa_words(lesson)
        if words:
            parts.append(
                '<p style="font-size:16px">Nghe từng từ: '
                + " ".join(listen_btn(w) + f" <span>{esc(w)}</span>" for w in words)
                + "</p>"
            )
    return chr(10).join(parts)


def examples_step(lesson):
    if lesson["type"] == "Mẫu câu":
        # Mẫu câu: các câu trong bài chính là nội dung học — hiện đủ các câu
        # khác câu đúng (không lặp câu đúng). Lỗi/Quiz: đúng 2 ví dụ.
        exs = [e for e in lesson.get("examples", []) if e["en"] != lesson["right"]]
    else:
        exs = lesson.get("examples", [])[:2]
    if not exs:
        return ""
    items = "".join(
        f'<p class="example"><b style="color:var(--navy)">{esc(e["en"])}</b>'
        f'{listen_btn(e["en"])}<br>{esc(e["vi"])}</p>'
        for e in exs
    )
    return f'<div class="step"><h3><span>Ví dụ:</span> nghe và đọc theo</h3>{items}</div>'



def dicts_reel_html(lesson):
    parts = []
    if lesson.get("dict_links"):
        parts.append(
            '<div class="dicts">' + "".join(
                '<a href="' + esc(d["url"]) + '" target="_blank" rel="noopener">' + ICON["book"] + ' ' + esc(d["label"]) + '</a>'
                for d in lesson["dict_links"]
            ) + "</div>"
        )
    if lesson.get("reel"):
        parts.append(
            '<p style="margin-top:14px"><a class="btn btn-navy" href="' + esc(lesson["reel"]["url"]) + '" '
            'target="_blank" rel="noopener">▶ ' + esc(lesson["reel"]["label"]) + '</a></p>'
        )
    return chr(10).join(parts)


def completion_step(lesson):
    code = lesson["code"]
    if lesson["type"] == "Lỗi":
        heading = "Bạn đã sửa " + code + "!"
    elif lesson["type"] == "Quiz":
        heading = "Bạn đã làm xong " + code + "!"
    else:
        heading = "Bạn đã học xong " + code + "!"
    pair = esc(lesson["title"])
    return (
        '<div class="complete">'
        '<div class="complete-icon">' + ICON["star"] + '</div>'
        '<h3>' + esc(heading) + '</h3>'
        '<p class="pair">' + pair + '</p>'
        '<p>Mỗi ngày sửa một lỗi nhỏ. Mai quay lại học tiếp nhé.</p>'
        '<div id="complete-summary"></div>'
        '<p class="streak" id="complete-streak"></p>'
        '<div class="complete-actions">'
        '<a class="btn btn-primary" id="btn-next" href="' + BASE_PATH + '/">Bài tiếp theo →</a>'
        '<button type="button" class="btn btn-navy" id="btn-share">' + ICON["share"] + ' Chia sẻ kết quả</button>'
        '</div>'
        '<p class="complete-note">Bấm “Chia sẻ kết quả” để tải ảnh rồi đăng ảnh lên Facebook khoe bạn vừa sửa được lỗi này nhé.</p>'
        '</div>'
    )


def problem_html(lesson):
    if not lesson.get("problem"):
        return ""
    return f'<p class="explain"><b>Vấn đề hay gặp:</b> {esc(lesson["problem"])}</p>'


def core_html(lesson):
    if not lesson.get("core"):
        return ""
    return f'<p class="explain"><b>Quy tắc cốt lõi:</b> {esc(lesson["core"])}</p>'


def compare_html(lesson):
    pairs = lesson.get("compare", [])
    if not pairs:
        return ""
    items = "".join(
        f'<p class="example"><b style="color:var(--navy)">{esc(c["a"])}</b><br>'
        f'<b style="color:var(--navy)">{esc(c["b"])}</b><br>{esc(c.get("note", ""))}</p>'
        for c in pairs
    )
    return f'<div class="step"><h3><span>So sánh:</span> dễ nhầm ở đâu</h3>{items}</div>'


def mistakes_html(lesson):
    ms = lesson.get("mistakes", [])
    if not ms:
        return ""
    items = "".join(
        f'<p class="example"><span style="color:var(--red);font-weight:700">Sai: {esc(m["wrong"])}</span><br>'
        f'<span style="color:var(--navy);font-weight:700">Đúng: {esc(m["right"])}</span></p>'
        for m in ms
    )
    return f'<div class="step"><h3><span>Lỗi phổ biến:</span> đừng mắc lại</h3>{items}</div>'


def articulation_html(lesson):
    if not lesson.get("articulation"):
        return ""
    return f'<p class="explain"><b>Cách đặt miệng / lưỡi:</b> {esc(lesson["articulation"])}</p>'


def tip_html(lesson):
    if not lesson.get("tip"):
        return ""
    return f'<p class="explain"><b>Mẹo:</b> {esc(lesson["tip"])}</p>'


def selfgrade_html():
    return (
        '<div class="step"><h3><span>Tự đánh giá:</span> bạn nhớ bài này tới đâu?</h3>'
        '<div class="selfgrade-row">'
        '<button type="button" class="selfgrade" data-grade="kho" aria-pressed="false">Khó: chưa nhớ</button>'
        '<button type="button" class="selfgrade" data-grade="vua" aria-pressed="false">Vừa: nhớ chưa chắc</button>'
        '<button type="button" class="selfgrade" data-grade="de" aria-pressed="false">Dễ: nhớ ngay</button>'
        '</div></div>'
    )


def lesson_steps(lesson):
    steps = []
    done_btn = ('<p style="margin-top:16px">'
                '<button type="button" class="btn btn-navy btn-block" id="btn-done">'
                'Tôi đã nhớ bài này</button></p>')
    if lesson["type"] == "Quiz":
        answer_extra = core_html(lesson) + mistakes_html(lesson)
        steps.append((('<h3 class="ask">Bạn có hay nói câu này?</h3>' + quiz_block(lesson)
                       + '<div id="answer-box" style="display:none">'
                       + right_box(lesson) + why_html(lesson) + answer_extra + examples_step(lesson)
                       + '</div>'), False))
        prac = ""
        if lesson.get("practice"):
            prac += ('<div class="step"><h3><span>Luyện thêm:</span> chấm ngay</h3>'
                     + practice_blocks(lesson)
                     + '<p class="practice-score">Kết quả luyện tập: '
                     + f'<span class="practice-score-num" data-slug="{lesson["slug"]}"></span></p></div>')
        else:
            prac += '<div class="step"><p>Bài này không có câu luyện thêm.</p></div>'
        steps.append((prac, False))
        steps.append((remember_html(lesson) + tip_html(lesson) + selfgrade_html() + done_btn + dicts_reel_html(lesson), True))
        steps.append((completion_step(lesson), False))
    else:
        steps.append((problem_html(lesson)
                      + '<h3 class="ask">Bạn có hay nói câu này?</h3>'
                      + wrong_box(lesson) + right_box(lesson), False))
        steps.append((why_html(lesson) + core_html(lesson), False))
        step3 = compare_html(lesson) + mistakes_html(lesson)
        ipa = ipa_html(lesson)
        if ipa:
            step3 += '<div class="step"><h3><span>Phát âm:</span> nghe và đọc theo</h3>' + ipa + articulation_html(lesson) + '</div>'
        elif lesson.get("articulation"):
            step3 += '<div class="step"><h3><span>Phát âm:</span> cách đặt miệng / lưỡi</h3>' + articulation_html(lesson) + '</div>'
        steps.append((step3, False))
        ex = examples_step(lesson)
        steps.append((ex if ex else '<div class="step"><p>Bài này không có ví dụ riêng.</p></div>', False))
        prac = ""
        if lesson.get("quiz"):
            prac += ('<div class="step">' + quiz_block(lesson) + '</div>')
        if lesson.get("practice"):
            prac += ('<div class="step"><h3><span>Luyện ngay:</span> chấm ngay</h3>'
                     + practice_blocks(lesson)
                     + '<p class="practice-score">Kết quả luyện tập: '
                     + f'<span class="practice-score-num" data-slug="{lesson["slug"]}"></span></p></div>')
        if prac:
            steps.append((prac, False))
        steps.append((remember_html(lesson) + tip_html(lesson) + selfgrade_html() + done_btn + dicts_reel_html(lesson), True))
        steps.append((completion_step(lesson), False))
    return steps


def lesson_body(lesson):
    out = []
    for i, (html, is_done) in enumerate(lesson_steps(lesson)):
        attr = ' data-action="done"' if is_done else ""
        hidden = "" if i == 0 else " hidden"
        out.append('<div class="wstep"' + attr + hidden + '>' + html + '</div>')
    return chr(10).join(out)


def og_description(lesson):
    if lesson["type"] == "Quiz":
        q = lesson.get("quiz") or {}
        text = f'{q.get("question", "")} {q.get("prompt", "")}. Làm quiz để xem đáp án.'
    else:
        text = f'{lesson.get("wrong", "")} → {lesson.get("right", "")}. {lesson.get("why", "")}'
    if len(text) <= 220:
        return text
    cut = text[:220].rsplit(" ", 1)[0]
    return cut if cut else text[:220]


HEAD_THEME_SCRIPT = '<script>try{var __t=localStorage.getItem("sdsc-theme");if(__t){document.documentElement.dataset.theme=__t;}else if(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches){document.documentElement.dataset.theme="dark";}}catch(e){}</script>'
NOSCRIPT_CSS = '<noscript><style>.wstep{display:block!important}.wiz-bottom{display:none}#view-tracuu{display:block!important}.wiz-progress{display:none}</style></noscript>'


# Tối ưu A (19/11): CSS + JS + dữ liệu dùng chung tách ra file riêng
# (styles.css, app.js, data.js) để mỗi lần đăng bài chỉ đổi vài file.
# page_shell tự chèn link/script tới 3 file chung; các hàm render chỉ còn
# truyền JS riêng của từng loại trang qua extra_js.
SHARED_SCRIPTS = (
    f'<script src="{BASE_PATH}/data.js"></script>'
    f'<script src="{BASE_PATH}/app.js"></script>'
)


def js_body(block):
    """Lấy phần JS thuần trong khối <script>...</script> để ghi ra file .js."""
    text = block.strip()
    if text.startswith("<script>"):
        text = text[len("<script>"):]
    if text.endswith("</script>"):
        text = text[: -len("</script>")]
    return text.strip() + "\n"


def page_shell(title, description, og_url, og_image, body_html, extra_js="", body_class=""):
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{HEAD_THEME_SCRIPT}
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" type="image/svg+xml" href="{BASE_PATH}/favicon.svg">
<link rel="canonical" href="{esc(og_url)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(og_url)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1080">
<meta property="og:site_name" content="Kho bài học Sai Đâu Sửa Đó">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image)}">
<link rel="stylesheet" href="{BASE_PATH}/styles.css">
{NOSCRIPT_CSS}
</head>
<body class="{body_class}">
{body_html}
{SHARED_SCRIPTS}{extra_js}
</body>
</html>
"""



HOMEPAGE_JS = r"""
<script>
window.SDSC_TOTAL_LESSONS = __TOTAL_LESSONS__;
/* SDSC_LESSONS và SDSC_PATHS lấy từ data.js (nạp trước khối này). */
function safeRender(fn){try{fn();}catch(e){}}
function progressDoneCount(){
  const p=getProgress();
  return Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).length;
}
function renderProgress(){
  const p=getProgress();
  const n=progressDoneCount();
  const total=window.SDSC_TOTAL_LESSONS;
  document.querySelectorAll(".progress-num").forEach(el=>{el.textContent=n+" / "+total+" bài";});
  const bar=document.getElementById("progress-bar");
  if(bar)bar.style.width=(total?Math.round(100*n/total):0)+"%";
  const t=document.getElementById("progress-text");
  if(t)t.innerHTML="Bạn đã nhớ <b>"+n+" / "+total+" bài</b>"+(n===total?". Xong hết rồi, giỏi quá!":"");
  const done=Object.fromEntries(Object.entries(p.lessons||{}).filter(([,l])=>l&&l.done).map(([s])=>[s,true]));
  document.querySelectorAll(".path-card").forEach(card=>{
    const order=(window.SDSC_PATHS[card.dataset.path]||[]).filter(s=>window.SDSC_LESSONS[s]);
    const d=order.filter(s=>done[s]).length;
    const el=card.querySelector(".path-done");
    if(el)el.textContent=d+" / "+order.length+" bài đã nhớ";
  });
  updatePracticeScore();
}
function renderToday(){
  const p=getProgress();
  const done=new Set(Object.entries(p.lessons||{}).filter(([,l])=>l&&l.done).map(([s])=>s));
  const order=(window.SDSC_PATHS["hoc-lai-tu-dau"]||[]).filter(s=>window.SDSC_LESSONS[s]);
  let next=order.find(s=>!done.has(s));
  if(!next){
    const all=Object.keys(window.SDSC_LESSONS);
    next=all.find(s=>!done.has(s));
  }
  const box=document.getElementById("today-box");
  if(!box)return;
  if(!next){
    box.innerHTML="<h2>Học hôm nay</h2><p>Bạn đã học hết "+window.SDSC_TOTAL_LESSONS+" bài rồi. Giỏi quá! Hôm nay ôn lại nhé.</p><a class=\"btn btn-navy\" href=\"#on-homnay\">Ôn hôm nay</a>";
    return;
  }
  const l=window.SDSC_LESSONS[next];
  if(!l){box.innerHTML="<h2>Học hôm nay</h2><p>Chưa tải được bài tiếp theo. Thử tải lại trang nhé.</p>";return;}
  box.innerHTML="<h2>Học hôm nay</h2><p><b>"+escapeHtml(l.code)+": "+escapeHtml(l.title)+"</b><br>"+escapeHtml(l.why)+"</p><a class=\"btn btn-primary btn-block\" href=\""+BASE_PATH_PLACEHOLDER+"/"+next+"/\" onclick=\"sessionSet('sdsc-path','hoc-lai-tu-dau')\">Học bài này</a>";
}
function renderStreak(){
  const p=getProgress();
  const el=document.getElementById("streak-text");
  if(!el)return;
  const today=todayISO();
  const doneToday=Object.values(p.lessons||{}).some(l=>l&&l.done&&(l.lastStudiedAt===today||l.doneAt===today));
  el.innerHTML="Mục tiêu: 1 bài/ngày • Chuỗi học: <b>"+(p.streak.count||0)+" ngày</b> • Hôm nay: "+(doneToday?"đã học. Giữ chuỗi nhé":"chưa học. Học 1 bài để giữ chuỗi nhé");
}
function renderReview(){
  const p=getProgress();
  const today=todayISO();
  const grid=document.getElementById("review-grid");
  const empty=document.getElementById("review-empty");
  if(!grid||!empty)return;
  const due=[];
  Object.entries(p.review||{}).forEach(([slug,r])=>{
    if(!r||!window.SDSC_LESSONS[slug])return;
    if(!isValidDateStr(r.nextDue))return;
    const L=p.lessons[slug];
    if(!L||!L.done)return;
    if(r.nextDue<=today){
      const overdue=Math.round((new Date(today+"T00:00:00")-new Date(r.nextDue+"T00:00:00"))/86400000);
      due.push({slug:slug,nextDue:r.nextDue,ease:r.ease||2.5,overdue:overdue});
    }
  });
  due.sort((a,b)=>b.overdue-a.overdue||a.ease-b.ease);
  const items=due.slice(0,5);
  if(!items.length){
    grid.style.display="none";empty.style.display="block";
    const future=Object.entries(p.review||{}).filter(([s,r])=>r&&window.SDSC_LESSONS[s]&&isValidDateStr(r.nextDue)&&r.nextDue>today&&(p.lessons[s]||{}).done).sort((a,b)=>a[1].nextDue.localeCompare(b[1].nextDue));
    if(future.length){
      const l=window.SDSC_LESSONS[future[0][0]];
      empty.textContent="Hôm nay chưa có bài đến hạn. Bài ôn gần nhất là "+l.code+": "+l.title+", vào ngày "+fmtDate(future[0][1].nextDue)+".";
    }else{
      empty.textContent="Chưa có bài nào để ôn. Học xong 1 bài rồi bấm “Tôi đã nhớ bài này” nhé.";
    }
    return;
  }
  empty.style.display="none";grid.style.display="grid";
  grid.innerHTML=items.map(x=>{
    const l=window.SDSC_LESSONS[x.slug];
    return "<a class=\"review-card\" href=\""+BASE_PATH_PLACEHOLDER+"/"+x.slug+"/\"><b>"+escapeHtml(l.code)+"</b><span>"+escapeHtml(l.title)+"<br>Đến hạn ôn"+(x.overdue>0?" (quá "+x.overdue+" ngày)":" hôm nay")+"</span></a>";
  }).join("");
}
function renderDoneList(){
  const p=getProgress();
  const box=document.getElementById("done-list");
  if(!box)return;
  const items=Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).sort((a,b)=>String(b[1].lastStudiedAt||b[1].doneAt||"").localeCompare(String(a[1].lastStudiedAt||a[1].doneAt||""))).slice(0,10);
  if(!items.length){box.innerHTML="<p>Chưa có bài nào đã nhớ. Học bài đầu tiên ở khung “Học hôm nay” nhé.</p>";return;}
  box.innerHTML="<ul>"+items.map(([s,l])=>{const m=window.SDSC_LESSONS[s];return "<li><a href=\""+BASE_PATH_PLACEHOLDER+"/"+s+"/\">"+escapeHtml(m.code)+": "+escapeHtml(m.title)+"</a>, đã nhớ ngày "+escapeHtml(fmtDate(l.doneAt||l.lastStudiedAt||""))+"</li>";}).join("")+"</ul>";
}
function renderRecent(){
  const p=getProgress();
  const box=document.getElementById("recent-list");
  if(!box)return;
  const evs=(p.history||[]).filter(h=>h&&h.slug&&window.SDSC_LESSONS[h.slug]).slice(-5).reverse();
  if(!evs.length){box.innerHTML="<p>Chưa có hoạt động nào. Làm thử 1 câu luyện ở bất kỳ bài nào nhé.</p>";return;}
  const label={done:"Đã nhớ bài",undone:"Bỏ đánh dấu bài",practice:"Luyện câu ở bài",review:"Ôn lại bài","self-grade":"Tự đánh giá bài",import:"Nhập tiến độ",reset:"Đặt lại tiến độ"};
  box.innerHTML="<ul>"+evs.map(h=>{const m=window.SDSC_LESSONS[h.slug];const extra=h.action==="practice"?(h.correct?", đúng":", chưa đúng"):(h.grade?", mức "+({kho:"Khó",vua:"Vừa",de:"Dễ"}[h.grade]||h.grade):"");return "<li>"+escapeHtml(label[h.action]||h.action)+" <a href=\""+BASE_PATH_PLACEHOLDER+"/"+h.slug+"/\">"+escapeHtml(m.code)+"</a>"+extra+" ("+escapeHtml(fmtDate(h.date||""))+ ")"+"</li>";}).join("")+"</ul>";
}
function longestStreak(dates){
  if(!dates||!dates.length)return 0;
  const set=new Set(dates.filter(isValidDateStr));
  let best=0;
  set.forEach(d=>{
    if(!set.has(addDays(d,-1))){
      let n=1,cur=d;
      while(set.has(addDays(cur,1))){cur=addDays(cur,1);n++;}
      if(n>best)best=n;
    }
  });
  return best;
}
function renderStats(){
  const p=getProgress();
  const box=document.getElementById("stats-list");
  if(!box)return;
  const done=progressDoneCount();
  const prac=Object.values(p.practice||{});
  const acc=prac.length?Math.round(100*prac.filter(v=>v&&v.correct).length/prac.length):0;
  const reviews=Object.values(p.lessons||{}).reduce((a,l)=>a+(l&&l.reviews||0),0);
  const lastDates=Object.values(p.lessons||{}).map(l=>l&&(l.lastStudiedAt||l.doneAt||"")).filter(isValidDateStr).sort();
  const last=lastDates.length?fmtDate(lastDates[lastDates.length-1]):"chưa có";
  box.innerHTML="<ul><li>Bài đã nhớ: <b>"+done+" / "+window.SDSC_TOTAL_LESSONS+"</b></li><li>Tỉ lệ luyện đúng: <b>"+acc+"%</b> ("+prac.filter(v=>v&&v.correct).length+" / "+prac.length+" câu)</li><li>Số lần ôn lại: <b>"+reviews+"</b></li><li>Chuỗi ngày học dài nhất: <b>"+longestStreak(p.streak.dates||[])+" ngày</b> (chuỗi hiện tại: "+(p.streak.count||0)+" ngày)</li><li>Ngày học gần nhất: <b>"+escapeHtml(last)+"</b></li></ul>";
}
function renderExportUI(){
  const msg=document.getElementById("import-msg");
  const showMsg=(t,ok)=>{if(msg){msg.textContent=t;msg.style.color=ok?"var(--green)":"var(--red)";}};
  const exp=document.getElementById("btn-export");
  if(exp&&!exp.dataset.wired){exp.dataset.wired="1";exp.addEventListener("click",()=>{if(exportProgress())showMsg("Đã tải file tiến độ. Cất file này cẩn thận, đổi máy thì nhập lại nhé.",true);else showMsg("Không tạo được file tiến độ, thử lại nhé.",false);});}
  const file=document.getElementById("import-file");
  const imp=document.getElementById("btn-import");
  if(imp&&!imp.dataset.wired){imp.dataset.wired="1";imp.addEventListener("click",()=>{if(file)file.click();});}
  if(file&&!file.dataset.wired){file.dataset.wired="1";file.addEventListener("change",()=>{
    const f=file.files&&file.files[0];if(!f)return;
    if(f.size>1024*1024){showMsg("File quá lớn (hơn 1 MB). Có thể đây không phải file tiến độ.",false);file.value="";return;}
    const modeEl=document.querySelector('input[name="import-mode"]:checked');
    const mode=modeEl?modeEl.value:"merge";
    if(mode==="overwrite"){
      const p=getProgress();
      const dc=Object.values(p.lessons||{}).filter(l=>l&&l.done).length;
      const pc=Object.keys(p.practice||{}).length;
      if(!confirm("Ghi đè sẽ xóa "+dc+" bài đã nhớ, "+pc+" câu luyện và chuỗi "+(p.streak.count||0)+" ngày hiện tại. Tiếp tục?")){file.value="";return;}
    }
    const reader=new FileReader();
    reader.onload=()=>{const res=importProgressText(String(reader.result||""),mode);if(res.ok){showMsg(res.message,true);renderAll();}else{showMsg(res.error,false);}file.value="";};
    reader.onerror=()=>{showMsg("Không đọc được file, thử lại nhé.",false);file.value="";};
    reader.readAsText(f);
  });}
}
function renderAll(){
  safeRender(renderProgress);safeRender(renderToday);safeRender(renderReview);safeRender(renderStreak);
  safeRender(renderDoneList);safeRender(renderRecent);safeRender(renderStats);safeRender(renderExportUI);
}
window.__sdscRenderProgress=renderAll;
function showTab(name,push){
  const th=document.getElementById("tab-hoc"), tt=document.getElementById("tab-tracuu");
  if(th){th.classList.toggle("on",name==="hoc");th.setAttribute("aria-selected",name==="hoc"?"true":"false");}
  if(tt){tt.classList.toggle("on",name==="tracuu");tt.setAttribute("aria-selected",name==="tracuu"?"true":"false");}
  const vh=document.getElementById("view-hoc"), vt=document.getElementById("view-tracuu");
  if(vh)vh.style.display=name==="hoc"?"block":"none";
  if(vt)vt.style.display=name==="tracuu"?"block":"none";
  try{
    if(push&&history.pushState)history.pushState(null,"",name==="tracuu"?"#tra-cuu":"#");
    else if(history.replaceState)history.replaceState(null,"",name==="tracuu"?"#tra-cuu":"#");
  }catch(e){}
}
document.getElementById("tab-hoc").addEventListener("click",()=>showTab("hoc",true));
document.getElementById("tab-tracuu").addEventListener("click",()=>showTab("tracuu",true));
window.addEventListener("popstate",()=>{showTab(location.hash==="#tra-cuu"?"tracuu":"hoc",false);});
if(location.hash==="#tra-cuu")showTab("tracuu",false);else showTab("hoc",false);
renderAll();
</script>
"""

INDEX_FILTER_JS = r"""
<script>
/* Tìm kiếm + bộ lọc (§2.4): chuẩn hóa không dấu cả hai phía, xếp hạng theo trọng số.
   Chỉ mục tìm kiếm đầy đủ nằm ở search-index.json, CHỈ nạp khi người dùng
   tìm kiếm (19/11). Trước lúc đó dùng chỉ mục gọn dựng từ data.js
   (mã, tiêu đề, lý do, chủ đề, loại, ngày, lộ trình) — đủ cho chip đếm,
   lọc theo chủ đề/loại/lộ trình/trạng thái và sắp xếp. */
const SDSC_BASE=BASE_PATH_PLACEHOLDER;
function sdscMetaIndex(){
  const pathsBySlug={};
  Object.entries(window.SDSC_PATHS||{}).forEach(function(pe){var p=pe[0],order=pe[1]||[];order.forEach(function(s){(pathsBySlug[s]=pathsBySlug[s]||[]).push(p);});});
  return Object.entries(window.SDSC_LESSONS||{}).map(function(le){var slug=le[0],l=le[1]||{};return {slug:slug,code:l.code||"",title:l.title||"",wrong:"",right:"",remember:"",why:l.why||"",examples:[],quiz:[],practice:[],topic:l.topic||"",type:l.type||"",date:l.date||"",paths:pathsBySlug[slug]||[]};});
}
let SDSC_INDEX=sdscMetaIndex();
let sdscFullLoaded=false;
let sdscIndexPromise=null;
function ensureSearchIndex(){
  if(sdscIndexPromise)return sdscIndexPromise;
  if(typeof fetch!=="function"){sdscFullLoaded=true;return Promise.resolve(SDSC_INDEX);}
  sdscIndexPromise=fetch(SDSC_BASE+"/search-index.json").then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();}).then(function(j){SDSC_INDEX=j;window.SDSC_SEARCH=j;sdscFullLoaded=true;return j;}).catch(function(){sdscFullLoaded=true;return SDSC_INDEX;});
  return sdscIndexPromise;
}
function sdscNorm(s){
  return String(s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/đ/g,"d").replace(/[^a-z0-9\s]/g," ").replace(/\s+/g," ").trim();
}
function sdscTokens(s){return sdscNorm(s).split(" ").filter(Boolean);}
const STOPWORDS=new Set(["cua","la","va","cai","mot","cung","thi","de","cho","voi","ve","o","trong","khi","ma"]);
function queryTokens(q){
  let toks=sdscTokens(q);
  if(toks.length>1)toks=toks.filter(t=>!STOPWORDS.has(t));
  return toks;
}
function fieldScore(fieldText,qtok,weight){
  const ftoks=sdscTokens(fieldText);
  let s=0;
  qtok.forEach(t=>{
    ftoks.forEach(ft=>{
      if(ft===t)s+=weight;
      else if(ft.indexOf(t)===0&&t.length>=2)s+=weight*2;
    });
  });
  return s;
}
function sdscScore(lesson,qtok){
  if(!qtok.length)return 0;
  let s=0;
  s+=fieldScore((lesson.code||"")+" "+(lesson.title||""),qtok,10);
  s+=fieldScore((lesson.wrong||"")+" "+(lesson.right||""),qtok,6);
  s+=fieldScore((lesson.remember||"")+" "+(lesson.why||""),qtok,4);
  s+=fieldScore((lesson.examples||[]).join(" "),qtok,2);
  s+=fieldScore((lesson.quiz||[]).join(" "),qtok,2);
  s+=fieldScore((lesson.practice||[]).join(" "),qtok,2);
  s+=fieldScore(lesson.topic||"",qtok,3);
  return s;
}
const cards=[...document.querySelectorAll(".card")];
const rows=[...document.querySelectorAll("#tbody tr")];
let fTopic="Tất cả",fType="Tất cả",fPath="Tất cả",fStatus="all",fSort="newest",fQ="";
let debounceTimer=null;
function getProgressForFilter(){try{return getProgress();}catch(e){return {lessons:{},review:{}};}}
function statusOf(slug){
  const p=getProgressForFilter();
  const L=(p.lessons||{})[slug];
  if(L&&L.done){
    const r=(p.review||{})[slug];
    if(r&&isValidDateStr(r.nextDue)&&r.nextDue<=todayISO())return "due";
    return "done";
  }
  return "todo";
}
function applyFilters(){
  const qtok=queryTokens(fQ);
  if(qtok.length&&!sdscFullLoaded){
    const countEl0=document.getElementById("count");
    if(countEl0)countEl0.textContent="Đang tìm…";
    ensureSearchIndex().then(function(){applyFilters();});
    return;
  }
  const scored=[];
  SDSC_INDEX.forEach(lesson=>{
    let s=qtok.length?sdscScore(lesson,qtok):0;
    if(qtok.length&&s<=0)return;
    const okT=fTopic==="Tất cả"||lesson.topic===fTopic;
    const okY=fType==="Tất cả"||lesson.type===fType;
    const okP=fPath==="Tất cả"||(lesson.paths||[]).indexOf(fPath)>=0;
    const st=statusOf(lesson.slug);
    const okS=fStatus==="all"||(fStatus==="done"&&st==="done")||(fStatus==="todo"&&st==="todo")||(fStatus==="due"&&st==="due");
    if(!okT||!okY||!okP||!okS)return;
    scored.push({lesson:lesson,score:s});
  });
  if(qtok.length){scored.sort((a,b)=>b.score-a.score||String(b.lesson.date).localeCompare(String(a.lesson.date)));}
  else if(fSort==="oldest"){scored.sort((a,b)=>String(a.lesson.date).localeCompare(String(b.lesson.date)));}
  else if(fSort==="az"){scored.sort((a,b)=>String(a.lesson.title).localeCompare(String(b.lesson.title)));}
  else{scored.sort((a,b)=>String(b.lesson.date).localeCompare(String(a.lesson.date)));}
  const visible=new Set(scored.map(x=>x.lesson.slug));
  let n=0;
  cards.forEach(c=>{const ok=visible.has(c.dataset.slug);c.style.display=ok?"":"none";if(ok)n++;});
  rows.forEach(r=>{r.style.display=visible.has(r.dataset.slug)?"":"none";});
  const countEl=document.getElementById("count");
  if(countEl)countEl.textContent=n?(fQ?("Tìm thấy "+n+" bài cho '"+fQ+"'"):("Đang xem "+n+" bài")):"Không thấy bài nào khớp. Thử từ khác nhé.";
  const emptyEl=document.getElementById("empty");
  if(emptyEl)emptyEl.style.display=n?"none":"block";
  syncURL();
}
function syncURL(){
  try{
    const params=new URLSearchParams();
    if(fQ)params.set("q",fQ);
    if(fTopic!=="Tất cả")params.set("topic",fTopic);
    if(fType!=="Tất cả")params.set("type",fType);
    if(fPath!=="Tất cả")params.set("path",fPath);
    if(fStatus!=="all")params.set("status",fStatus);
    if(fSort!=="newest")params.set("sort",fSort);
    const qs=params.toString();
    history.replaceState(null,"",location.pathname+(qs?"?"+qs:"")+location.hash);
  }catch(e){}
}
function chipRow(id,items,cur,fn){
  const el=document.getElementById(id);
  if(!el)return;
  el.innerHTML=items.map(v=>'<button type="button" class="chip'+(v.value===cur?" on":"")+'" data-v="'+escapeHtml(v.value)+'">'+escapeHtml(v.label)+"</button>").join("");
  el.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{fn(b.dataset.v);renderChips();applyFilters();}));
}
function renderChips(){
  const topicCounts={};SDSC_INDEX.forEach(l=>{topicCounts[l.topic]=(topicCounts[l.topic]||0)+1;});
  const topics=[{value:"Tất cả",label:"Tất cả ("+SDSC_INDEX.length+")"}].concat(Object.keys(topicCounts).sort().map(t=>({value:t,label:t+" ("+topicCounts[t]+")"})));
  const typeCounts={};SDSC_INDEX.forEach(l=>{typeCounts[l.type]=(typeCounts[l.type]||0)+1;});
  const types=[{value:"Tất cả",label:"Tất cả"}].concat(Object.keys(typeCounts).sort().map(t=>({value:t,label:t+" ("+typeCounts[t]+")"})));
  chipRow("topicChips",topics,fTopic,v=>{fTopic=v;});
  chipRow("typeChips",types,fType,v=>{fType=v;});
}
let view="cards";
function syncView(){
  document.getElementById("cards").style.display=view==="cards"?"grid":"none";
  document.getElementById("tableWrap").style.display=view==="table"?"block":"none";
  document.getElementById("btnCards").classList.toggle("on",view==="cards");
  document.getElementById("btnTable").classList.toggle("on",view==="table");
}
document.getElementById("search").addEventListener("input",e=>{
  clearTimeout(debounceTimer);
  debounceTimer=setTimeout(()=>{fQ=e.target.value.trim();applyFilters();},150);
});
document.getElementById("btnCards").addEventListener("click",()=>{view="cards";syncView();});
document.getElementById("btnTable").addEventListener("click",()=>{view="table";syncView();});
const pathSel=document.getElementById("pathFilter");
if(pathSel)pathSel.addEventListener("change",()=>{fPath=pathSel.value;applyFilters();});
const statusSel=document.getElementById("statusFilter");
if(statusSel)statusSel.addEventListener("change",()=>{fStatus=statusSel.value;applyFilters();});
const sortSel=document.getElementById("sortFilter");
if(sortSel)sortSel.addEventListener("change",()=>{fSort=sortSel.value;applyFilters();});
(function restoreFromURL(){
  try{
    const params=new URLSearchParams(location.search);
    if(params.get("q")){fQ=params.get("q");document.getElementById("search").value=fQ;}
    if(params.get("topic"))fTopic=params.get("topic");
    if(params.get("type"))fType=params.get("type");
    if(params.get("path")){fPath=params.get("path");if(pathSel)pathSel.value=fPath;}
    if(params.get("status")){fStatus=params.get("status");if(statusSel)statusSel.value=fStatus;}
    if(params.get("sort")){fSort=params.get("sort");if(sortSel)sortSel.value=fSort;}
  }catch(e){}
})();
renderChips();syncView();applyFilters();
</script>
"""

LESSON_PAGE_JS = r"""
<script>
const SLUG="__SLUG__";
const LESSON_DATA=__LESSON_JSON__;
let __pendingGrade=null;
function renderDone(){
  const p=getProgress();
  const btn=document.getElementById("btn-done");
  if(!btn)return;
  const L=p.lessons[SLUG];
  if(L&&L.done){btn.textContent="Đã nhớ: bấm để bỏ đánh dấu";btn.classList.add("done");}
  else{btn.textContent="Tôi đã nhớ bài này";btn.classList.remove("done");}
}
function renderSelfGrade(){
  const p=getProgress();
  const L=p.lessons[SLUG];
  const cur=(L&&L.selfGrade)||__pendingGrade;
  document.querySelectorAll(".selfgrade").forEach(b=>{
    b.classList.toggle("on",b.dataset.grade===cur);
    b.setAttribute("aria-pressed",b.dataset.grade===cur?"true":"false");
  });
}
function recordSelfGrade(grade){
  __pendingGrade=grade;
  const p=getProgress();
  const L=p.lessons[SLUG];
  if(L&&L.done){
    updateProgress(pp=>{
      const LL=pp.lessons[SLUG];if(!LL)return;
      LL.selfGrade=grade;LL.lastStudiedAt=todayISO();LL.reviews=(LL.reviews||0)+1;
      pp.review[SLUG]=srsUpdate(pp.review[SLUG]||srsNew(todayISO()),grade,todayISO());
      pushHistory(pp,{date:todayISO(),at:new Date().toISOString(),slug:SLUG,action:"review",grade:grade});
    });
  }else{
    renderSelfGrade();
  }
  renderSelfGrade();
}
document.querySelectorAll(".selfgrade").forEach(b=>b.addEventListener("click",()=>recordSelfGrade(b.dataset.grade)));
function renderCompleteStreak(){
  const el=document.getElementById("complete-streak");
  if(!el)return;
  const p=getProgress();
  el.innerHTML="Chuỗi học của bạn: <b>"+(p.streak.count||0)+" ngày</b>. Mục tiêu: 1 bài/ngày.";
}
function renderCompleteSummary(){
  const box=document.getElementById("complete-summary");
  if(!box)return;
  const t=practiceTotalsFor(SLUG);
  const p=getProgress();
  const wrong=[];
  Object.entries(p.practice||{}).forEach(([k,v])=>{
    if((k===SLUG+":q"||k.indexOf(SLUG+":")===0)&&v&&v.correct===false){
      const pr=(LESSON_DATA.practice||[]).find(x=>x.key===k);
      if(pr)wrong.push(pr.prompt);
    }
  });
  let html="<p>Kết quả luyện của bài này: <b>"+t.right+" / "+t.total+" câu đúng</b> ("+t.done+" đã làm).</p>";
  if(wrong.length){html+="<p>Câu còn sai, ôn lại nhé:</p><ul>"+wrong.map(w=>"<li>"+escapeHtml(w)+"</li>").join("")+"</ul>";}
  else if(t.done>0){html+="<p>Không còn câu sai trong bài này. Giỏi quá!</p>";}
  const r=p.review[SLUG];
  if(r&&isValidDateStr(r.nextDue)){html+="<p>Bài này sẽ đến hạn ôn vào ngày <b>"+escapeHtml(fmtDate(r.nextDue))+"</b>. Trang chủ sẽ nhắc bạn.</p>";}
  const L=p.lessons[SLUG];
  if(L&&L.selfGrade){html+="<p>Bạn tự đánh giá mức hiểu: <b>"+({kho:"Khó: chưa nhớ",vua:"Vừa: nhớ chưa chắc",de:"Dễ: nhớ ngay"}[L.selfGrade]||L.selfGrade)+"</b>.</p>";}
  box.innerHTML=html;
}
function markDone(){
  const grade=__pendingGrade;
  updateProgress(p=>{
    const today=todayISO();
    const L=p.lessons[SLUG]||{done:false,doneAt:"",lastStudiedAt:"",selfGrade:null,reviews:0};
    const wasDone=!!L.done;
    L.done=true;
    if(!L.doneAt)L.doneAt=today;
    L.lastStudiedAt=today;
    if(grade)L.selfGrade=grade;
    p.lessons[SLUG]=L;
    if(!wasDone){p.review[SLUG]=srsNew(today);}
    else if(grade){p.review[SLUG]=srsUpdate(p.review[SLUG]||srsNew(today),grade,today);L.reviews=(L.reviews||0)+1;}
    updateStreakIn(p,today);
    if(!wasDone||grade){pushHistory(p,{date:today,at:new Date().toISOString(),slug:SLUG,action:wasDone?"self-grade":"done",grade:grade||undefined});}
  });
  __pendingGrade=null;
  renderDone();renderSelfGrade();renderCompleteStreak();updatePracticeScore();
}
function unmarkDone(){
  updateProgress(p=>{
    const L=p.lessons[SLUG];
    if(L){L.done=false;}
    delete p.review[SLUG];
    pushHistory(p,{date:todayISO(),at:new Date().toISOString(),slug:SLUG,action:"undone"});
  });
  __pendingGrade=null;
  renderDone();renderSelfGrade();updatePracticeScore();
}
document.getElementById("btn-done").addEventListener("click",()=>{
  const p=getProgress();
  const L=p.lessons[SLUG];
  if(L&&L.done){unmarkDone();}
  else{markDone();showStep(cur+1);}
});
const steps=[...document.querySelectorAll(".wstep")];
let cur=0;
const fill=document.getElementById("wizFill"), wlabel=document.getElementById("wizLabel"),
  prevBtn=document.getElementById("wizPrev"), nextBtn=document.getElementById("wizNext");
let NEXT_URL=BASE_PATH_PLACEHOLDER+"/";
function showStep(i){
  cur=Math.max(0,Math.min(i,steps.length-1));
  steps.forEach((s,j)=>{s.hidden=j!==cur;});
  if(fill)fill.style.width=Math.round(100*(cur+1)/steps.length)+"%";
  if(wlabel)wlabel.textContent="Bước "+(cur+1)+"/"+steps.length;
  if(prevBtn)prevBtn.style.visibility=cur>0?"visible":"hidden";
  const isDoneStep=steps[cur].dataset.action==="done";
  const isLast=cur===steps.length-1;
  if(nextBtn)nextBtn.textContent=isLast?"Bài tiếp theo →":(isDoneStep?"✓ Tôi đã nhớ bài này":"Tiếp tục →");
  if(isLast){renderCompleteStreak();renderCompleteSummary();}
  try{window.scrollTo({top:0,behavior:"smooth"});}catch(e){}
}
if(prevBtn)prevBtn.addEventListener("click",()=>{if(cur>0)showStep(cur-1);});
if(nextBtn)nextBtn.addEventListener("click",()=>{
  if(cur===steps.length-1){location.href=NEXT_URL;return;}
  if(steps[cur].dataset.action==="done"){markDone();}
  showStep(cur+1);
});
(function(){
  const paths=window.SDSC_PATHS||{};
  const ctx=sessionGet("sdsc-path");
  let order=null, label=null;
  if(ctx&&paths[ctx]){order=paths[ctx];label=ctx;}
  else{order=window.SDSC_ORDER||[];}
  const i=order.indexOf(SLUG);
  const next=document.getElementById("btn-next");
  if(i>=0&&i+1<order.length){
    const nl=window.SDSC_LESSONS[order[i+1]];
    NEXT_URL=BASE_PATH_PLACEHOLDER+"/"+order[i+1]+"/";
    if(next){next.href=NEXT_URL;next.textContent="Bài tiếp theo là "+nl.code+": "+nl.title+" →";
      next.addEventListener("click",()=>{if(label)sessionSet("sdsc-path",label);});}
  }else if(label){
    NEXT_URL=BASE_PATH_PLACEHOLDER+"/lo-trinh/"+label+"/";
    if(next){next.href=NEXT_URL;next.textContent="Đã hết lộ trình: xem lại lộ trình";}
  }else{
    NEXT_URL=BASE_PATH_PLACEHOLDER+"/";
    if(next){next.href=NEXT_URL;next.textContent="Về trang chủ";}
  }
})();
renderDone();renderSelfGrade();showStep(0);
document.getElementById("btn-share").addEventListener("click",()=>{
  try{document.fonts&&document.fonts.ready?document.fonts.ready.then(()=>{try{drawShare();}catch(e){alert("Không tạo được ảnh, thử lại nhé.");}}):drawShare();}catch(e){alert("Không tạo được ảnh, thử lại nhé.");}
});
function drawShare(){
  const c=document.createElement("canvas");c.width=1080;c.height=1080;
  const x=c.getContext("2d");
  x.fillStyle="#173F5F";x.fillRect(0,0,1080,1080);
  x.textAlign="center";
  x.fillStyle="#FFFFFF";x.font="900 200px 'Be Vietnam Pro','Inter',sans-serif";
  x.fillText("S",540,270);
  x.fillStyle="#F26B38";x.font="900 110px 'Be Vietnam Pro','Inter',sans-serif";
  x.fillText("✓",665,295);
  x.fillStyle="#FFFFFF";x.font="700 62px 'Be Vietnam Pro','Inter',sans-serif";
  x.fillText("Tôi đã sửa "+LESSON_DATA.code,540,420);
  x.fillStyle="#DCEFEA";x.font="600 44px 'Be Vietnam Pro','Inter',sans-serif";
  x.fillText(LESSON_DATA.title,540,485);
  x.fillStyle="#FFFFFF";
  roundRect(x,90,540,900,300,28);x.fill();
  let y=640;
  x.fillStyle="#C0392B";x.font="600 46px 'Inter',sans-serif";
  y=wrapText(x,LESSON_DATA.wrong,540,y,820,58);
  x.fillStyle="#173F5F";x.font="700 46px 'Inter',sans-serif";
  x.fillText("↓",540,y+30);y+=80;
  x.fillStyle="#173F5F";x.font="700 46px 'Inter',sans-serif";
  y=wrapText(x,LESSON_DATA.right,540,y,820,58);
  x.fillStyle="#DCEFEA";x.font="600 36px 'Be Vietnam Pro','Inter',sans-serif";
  x.fillText("Kho bài học Sai Đâu Sửa Đó",540,930);
  x.fillStyle="#CBDCE8";x.font="400 30px 'Inter',sans-serif";
  x.fillText("dongdarealest.github.io/sai-dau-sua-do",540,985);
  c.toBlob(b=>{
    if(!b){alert("Không tạo được ảnh, thử lại nhé.");return;}
    const a=document.createElement("a");
    a.href=URL.createObjectURL(b);
    a.download="sai-dau-sua-do-"+SLUG+".png";
    a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),5000);
  },"image/png");
}
function roundRect(x,px,py,w,h,r){x.beginPath();x.moveTo(px+r,py);x.arcTo(px+w,py,px+w,py+h,r);x.arcTo(px+w,py+h,px,py+h,r);x.arcTo(px,py+h,px,py,r);x.arcTo(px,py,px+w,py,r);x.closePath();}
function wrapText(x,text,cx,y,maxW,lh){
  const words=String(text).split(" ");
  let line="";
  for(const w of words){
    let word=w;
    while(x.measureText(word).width>maxW){
      let cut=word;
      while(cut.length>1&&x.measureText(cut).width>maxW)cut=cut.slice(0,-1);
      x.fillText(cut,cx,y);y+=lh;word=word.slice(cut.length);
    }
    const test=line?line+" "+word:word;
    if(x.measureText(test).width>maxW&&line){x.fillText(line,cx,y);line=word;y+=lh;}
    else line=test;
  }
  if(line){x.fillText(line,cx,y);y+=lh;}
  return y;
}
</script>
"""

PATH_PAGE_JS = r"""
<script>
(function(){
  const p=getProgress();
  const n=Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).length;
  document.querySelectorAll(".progress-num").forEach(el=>{el.textContent=n+" / "+window.SDSC_TOTAL_LESSONS+" bài";});
  document.querySelectorAll(".path-item").forEach(el=>{
    const L=p.lessons[el.dataset.slug];
    if(L&&L.done){
      el.classList.add("done");
      const go=el.querySelector(".go");if(go)go.textContent="Đã nhớ";
    }
  });
})();
</script>
"""

def header_html(site, subtitle, stats_extra):
    return f"""
<header>
  <div class="wrap">
    <div class="brand">
      <div style="display:flex;gap:14px;align-items:center">
        <div class="logo">S</div>
        <div>
          <h1><a href="{BASE_PATH}/">{esc(site['name'])}</a></h1>
          <p class="slogan">{esc(site['slogan'])}</p>
        </div>
      </div>
      <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Chế độ tối"></button>
    </div>
    <p class="intro">{esc(subtitle)}</p>
    <div class="stats">{stats_extra}</div>
    <nav class="sitenav" aria-label="Mục chính">
      <a href="{BASE_PATH}/">Trang chủ</a>
      <a href="{BASE_PATH}/bang-lo-trinh/">Bảng lộ trình</a>
      <a href="{BASE_PATH}/thu-vien-chu-de/">Thư viện chủ đề</a>
      <a href="{BASE_PATH}/tu-dien/">Từ điển</a>
      <a href="{BASE_PATH}/luyen-noi/">Luyện nói</a>
    </nav>
  </div>
</header>"""


def footer_html(site):
    return f"""
<footer>
  <div class="wrap">
    Học trên Facebook: <a href="{esc(site['facebook_page'])}">Sai Đâu Sửa Đó</a>
    &nbsp;•&nbsp; Vào Group làm bài tập mỗi ngày: <a href="{esc(site['facebook_group'])}">Cộng đồng Sai Đâu Sửa Đó</a>
  </div>
</footer>"""


def total_graded(lessons):
    return sum((1 if l.get("quiz") else 0) + len(l.get("practice", [])) for l in lessons)


def data_js_content(visible, paths):
    """Nội dung file data.js (tổng + dữ liệu bài học). Trước đây data_script
    nhúng thẳng khối này vào từng trang; từ 19/11 nó là 1 file chung để mỗi
    lần đăng bài chỉ đổi data.js thay vì đổi mọi trang."""
    return (
        f"window.SDSC_TOTAL_GRADED={total_graded(visible)};"
        f"window.SDSC_TOTAL_LESSONS={len(visible)};"
        "window.SDSC_LESSONS="
        + json.dumps(lessons_js(visible), ensure_ascii=False)
        + ";window.SDSC_PATHS="
        + json.dumps({p["slug"]: p["order"] for p in paths}, ensure_ascii=False)
        + ";window.SDSC_ORDER="
        + json.dumps([l["slug"] for l in visible], ensure_ascii=False)
        + ";window.SDSC_TOTALS="
        + json.dumps(lesson_totals(visible), ensure_ascii=False)
        + ";\n"
    )


def card_html(lesson, paths_for=None):
    href = f"{BASE_PATH}/{lesson['slug']}/"
    title = f"{lesson['code']}: {lesson['title']}"
    if lesson["type"] == "Quiz":
        q = lesson["quiz"]
        inner = f"""
    <p class="q" style="font-size:17px;font-weight:700">{esc(q['question'])}</p>
    <p class="prompt" style="font-size:16px;background:var(--bg);border-radius:10px;padding:11px 13px">{esc(q['prompt'])}</p>
    <p style="font-size:16px;color:var(--sub)">3 lựa chọn A / B / C. Bấm vào bài để làm quiz, trang chấm ngay.</p>"""
    else:
        inner = f"""
    <div class="box wrong"><small>✗ CÂU SAI</small><p>{esc(lesson['wrong'])}</p></div>
    <div class="box right"><small>✓ CÂU ĐÚNG</small><p>{esc(lesson['right'])}</p></div>
    <p class="explain"><b>Vì sao:</b> {esc(lesson['why'])}</p>"""
    search_text = search_text_for(lesson)
    path_attr = ",".join(paths_for or [])
    return f"""
<article class="card" data-slug="{esc(lesson['slug'])}" data-path="{esc(path_attr)}" data-topic="{esc(lesson['topic'])}" data-type="{esc(lesson['type'])}" data-search="{search_text.lower()}">
  <div class="tags"><span class="tag topic">{esc(lesson['topic'])}</span><span class="tag">{esc(fmt_date(lesson['date']))}</span></div>
  <h3><a href="{href}">{esc(title)}</a></h3>
  {inner}
  <div class="meta"><time>{esc(fmt_date(lesson['date']))}</time><a href="{href}">Học bài này →</a></div>
</article>"""


def table_row_html(lesson, paths_for=None):
    href = f"{BASE_PATH}/{lesson['slug']}/"
    right = "Làm quiz để xem đáp án" if lesson["type"] == "Quiz" else lesson["right"]
    search_text = search_text_for(lesson)
    path_attr = ",".join(paths_for or [])
    return (
        f'<tr data-slug="{esc(lesson["slug"])}" data-path="{esc(path_attr)}" data-topic="{esc(lesson["topic"])}" data-type="{esc(lesson["type"])}" '
        f'data-search="{search_text.lower()}">'
        f'<td><a href="{href}"><b>{esc(lesson["code"])}</b>: {esc(lesson["title"])}</a></td>'
        f'<td><span class="wrong">{esc(lesson["wrong"])}</span></td>'
        f'<td><span class="right">{esc(right)}</span></td>'
        f'<td>{esc(lesson["why"])}</td>'
        f'<td><span class="tag topic">{esc(lesson["topic"])}</span></td></tr>'
    )


def visible_lessons(data):
    return [l for l in data["lessons"] if l.get("show_in_ui", True)]


def lessons_js(visible):
    return {
        l["slug"]: {
            "code": l["code"],
            "title": l["title"],
            "why": l["why"],
            "topic": l["topic"],
            "type": l["type"],
            "date": l["date"],
        }
        for l in visible
    }


def paths_for_lessons(data):
    out = {}
    for p in data["site"]["paths"]:
        for slug in p["order"]:
            out.setdefault(slug, []).append(p["slug"])
    return out


def search_text_for(lesson):
    parts = [
        lesson.get("code", ""), lesson.get("title", ""), lesson.get("wrong", ""),
        lesson.get("right", ""), lesson.get("why", ""), lesson.get("remember", ""),
        lesson.get("topic", ""), lesson.get("type", ""),
    ]
    for e in lesson.get("examples", []):
        parts += [e.get("en", ""), e.get("vi", "")]
    parts += ipa_words(lesson)
    q = lesson.get("quiz") or {}
    parts += [q.get("question", ""), q.get("prompt", "")] + list(q.get("options", []))
    for p in lesson.get("practice", []):
        parts += [p.get("prompt", ""), p.get("explanation", "")] + [str(o) for o in p.get("options", [])]
    return esc(" ".join(x for x in parts if x))


def build_search_index(visible, paths_map):
    idx = []
    for l in visible:
        q = l.get("quiz") or {}
        idx.append({
            "slug": l["slug"], "code": l["code"], "title": l["title"],
            "wrong": l.get("wrong", ""), "right": l.get("right", ""),
            "remember": l.get("remember", ""), "why": l.get("why", ""),
            "examples": [e.get("en", "") + " " + e.get("vi", "") for e in l.get("examples", [])],
            "quiz": [q.get("question", ""), q.get("prompt", "")] + list(q.get("options", [])),
            "practice": [p.get("prompt", "") + " " + " ".join(str(o) for o in p.get("options", [])) for p in l.get("practice", [])],
            "topic": l.get("topic", ""), "type": l.get("type", ""), "date": l.get("date", ""),
            "paths": paths_map.get(l["slug"], []),
        })
    return idx


def lesson_totals(visible):
    return {l["slug"]: (1 if l.get("quiz") else 0) + len(l.get("practice", [])) for l in visible}


def data_script(visible, paths):
    """Giữ lại để tương thích: trả nội dung JS thuần của data.js (không bọc
    <script>). Các trang không còn nhúng khối này, chúng nạp data.js."""
    return data_js_content(visible, paths)


def total_lessons_stat():
    """Tổng số bài học ở header: ghi span rỗng, app.js điền số lúc chạy
    từ data.js (tối ưu B 19/11) để thêm bài mới không đổi mọi trang."""
    return '<span class="stat">' + ICON["book"] + ' <span class="total-lessons-num">…</span> bài học</span>'


def progress_chip():
    """Chip Đã nhớ: ghi span rỗng, app.js điền "n / tổng bài" lúc chạy."""
    return (
        '<span class="stat score">' + ICON["star"]
        + ' Đã nhớ <span class="progress-num">…</span></span>'
    )


def render_index(data):
    site = data["site"]
    visible = visible_lessons(data)
    paths = site["paths"]
    paths_map = paths_for_lessons(data)
    stats = (
        total_lessons_stat()
        + '<span class="stat">' + ICON["map"] + f' {len(paths)} lộ trình</span>'
        + progress_chip()
    )
    ask_url = site.get("ask_url") or site["facebook_page"]
    vis_slugs = {l["slug"] for l in visible}
    path_cards = ""
    for p in paths:
        n_in_path = len([s for s in p["order"] if s in vis_slugs])
        path_cards += (
            f'<a class="path-card" data-path="{esc(p["slug"])}" href="{BASE_PATH}/lo-trinh/{esc(p["slug"])}/">'
            f'<span class="num">{ICON[PATH_ICONS.get(p["slug"], "book")]}</span>'
            f"<h3>{esc(p['name'])}</h3><p>{esc(p['desc'])}</p>"
            f'<span class="meta"><span class="path-done">0 / {n_in_path} bài đã nhớ</span>'
            f" • {n_in_path} bài →</span></a>"
        )
    path_options = "".join(
        f'<option value="{esc(p["slug"])}">{esc(p["name"])}</option>' for p in paths
    )
    body = f"""
{header_html(site, "Học trước, tra cứu sau: mỗi bài chỉ 3 đến 5 phút, học xong bấm Đã nhớ để trang nhắc ôn lại.", stats)}
<main class="wrap">
  <div class="tabs" role="tablist">
    <button class="tab on" id="tab-hoc" type="button" role="tab" aria-selected="true">{ICON["book"]} Học</button>
    <button class="tab" id="tab-tracuu" type="button" role="tab" aria-selected="false">{ICON["search"]} Tra cứu</button>
  </div>
  <div id="view-hoc">
    <section>
      <div class="today" id="today-box"><h2>Học hôm nay</h2><p>Đang tải…</p></div>
    </section>
    <section>
      <div class="progress">
        <h2>Tiến độ của bạn</h2>
        <div class="bar"><i id="progress-bar"></i></div>
        <p id="progress-text"></p>
        <p>Luyện tập toàn trang: <span class="practice-site-num"></span></p>
        <p id="streak-text"></p>
        <p>{ICON["bookmark"]} Tiến độ lưu trên trình duyệt này, đổi máy sẽ mất.</p>
        <div class="import-row">
          <button type="button" class="btn btn-ghost" id="btn-export">Tải dữ liệu tiến độ (.json)</button>
          <button type="button" class="btn btn-ghost" id="btn-import">Nhập dữ liệu đã lưu</button>
          <input type="file" id="import-file" accept=".json,application/json" hidden>
          <label><input type="radio" name="import-mode" value="merge" checked> Gộp (mới hơn thắng)</label>
          <label><input type="radio" name="import-mode" value="overwrite"> Ghi đè</label>
          <p id="import-msg"></p>
        </div>
      </div>
    </section>
    <section>
      <h2>Chọn lộ trình của bạn</h2>
      <p style="margin-bottom:12px">Tổng cộng <b>{len(visible)} bài học</b>. Mỗi bài có thể nằm trong nhiều lộ trình, bạn chỉ cần học 1 lần.</p>
      <div class="paths">{path_cards}</div>
    </section>
    <section>
      <h2>Kỹ năng mới</h2>
      <p style="margin-bottom:12px">Học như app: tra từ, luyện nói, xem lộ trình và thư viện chủ đề.</p>
      <div class="paths">
        <a class="path-card" href="{BASE_PATH}/tu-dien/"><span class="num">{ICON["book"]}</span><h3>Từ điển</h3><p>Tra nghĩa, phiên âm, nghe phát âm giọng Anh và giọng Mỹ.</p><span class="meta">Tra từ →</span></a>
        <a class="path-card" href="{BASE_PATH}/luyen-noi/"><span class="num">{ICON["speaker"]}</span><h3>Luyện nói</h3><p>Nói câu mẫu, máy nghe lại và cho biết khớp được bao nhiêu.</p><span class="meta">Luyện nói →</span></a>
        <a class="path-card" href="{BASE_PATH}/bang-lo-trinh/"><span class="num">{ICON["map"]}</span><h3>Bảng lộ trình</h3><p>Tiến độ từng lộ trình, buổi luyện nói, bài tiếp theo.</p><span class="meta">Xem bảng →</span></a>
        <a class="path-card" href="{BASE_PATH}/thu-vien-chu-de/"><span class="num">{ICON["cap"]}</span><h3>Thư viện chủ đề</h3><p>Mọi bài học gom theo chủ đề, tìm và lọc nhanh.</p><span class="meta">Mở thư viện →</span></a>
      </div>
    </section>
    <section>
      <h2 id="on-homnay">Ôn hôm nay <small>Những bài đã đến hạn ôn theo lịch riêng của bạn</small></h2>
      <div class="review-grid" id="review-grid"></div>
      <div class="empty" id="review-empty" style="display:none">Chưa có bài nào để ôn. Học xong 1 bài rồi bấm “Tôi đã nhớ bài này” nhé.</div>
    </section>
    <section class="done-list">
      <h2>Bài đã hoàn thành</h2>
      <div id="done-list"><p>Đang tải…</p></div>
    </section>
    <section class="recent-list">
      <h2>Hoạt động gần đây</h2>
      <div id="recent-list"><p>Đang tải…</p></div>
    </section>
    <section class="stats-list">
      <h2>Thống kê quá trình học</h2>
      <div id="stats-list"><p>Đang tải…</p></div>
    </section>
    <section>
      <div class="cta-row">
        <a class="btn btn-navy" href="{esc(site['facebook_group'])}" target="_blank" rel="noopener">{ICON["users"]} Vào Group làm bài tập</a>
        <a class="btn btn-primary" href="{esc(ask_url)}" target="_blank" rel="noopener">{ICON["mail"]} Gửi câu của bạn để được sửa</a>
      </div>
    </section>
  </div>
  <div id="view-tracuu" style="display:none">
    <div class="tabpanel">
      <div class="toolbar">
        <label class="sr-only" for="search">Tìm bài học</label>
        <input id="search" type="search" placeholder="Tìm lỗi mình hay mắc… ví dụ: borrow, bored, comfortable">
        <div class="chips" id="topicChips"></div>
        <div class="chips">
          <span id="typeChips" style="display:flex;gap:8px;flex-wrap:wrap"></span>
          <span class="viewtoggle">
            <button id="btnCards" class="on" type="button">Thẻ</button>
            <button id="btnTable" type="button">Bảng</button>
          </span>
        </div>
        <div class="filter-row">
          <label for="pathFilter">Lộ trình:</label>
          <select id="pathFilter"><option value="Tất cả">Tất cả</option>{path_options}</select>
          <label for="statusFilter">Trạng thái:</label>
          <select id="statusFilter"><option value="all">Tất cả</option><option value="todo">Chưa học</option><option value="done">Đã nhớ</option><option value="due">Đến hạn ôn</option></select>
          <label for="sortFilter">Sắp xếp:</label>
          <select id="sortFilter"><option value="newest">Mới nhất</option><option value="oldest">Cũ nhất</option><option value="az">A đến Z</option></select>
        </div>
      </div>
      <p id="count"></p>
      <div id="cards" class="grid">
        {''.join(card_html(l, paths_map.get(l["slug"], [])) for l in visible)}
      </div>
      <div id="empty" class="empty" style="display:none">Không thấy bài nào khớp. Thử từ khác nhé.</div>
      <div id="tableWrap" class="tablewrap" style="display:none">
        <table>
          <thead><tr><th>Bài</th><th>Câu sai</th><th>Câu đúng</th><th>Giải thích</th><th>Chủ đề</th></tr></thead>
          <tbody id="tbody">
            {''.join(table_row_html(l, paths_map.get(l["slug"], [])) for l in visible)}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</main>
{footer_html(site)}
"""
    homepage_js = (
        HOMEPAGE_JS.replace("__TOTAL_LESSONS__", str(len(visible)))
        .replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    )
    index_filter_js = INDEX_FILTER_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    return page_shell(
        f"{site['name']}: {site['slogan']}",
        "Học tiếng Anh từ lỗi người Việt hay mắc. 3 lộ trình có thứ tự, mỗi bài 3 đến 5 phút, quiz chấm ngay, nhắc ôn lại. Tra cứu mọi lỗi đã sửa.",
        SITE_URL + "/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=homepage_js + index_filter_js,
    )


def render_dict(data):
    site = data["site"]
    visible = visible_lessons(data)
    stats = (
        total_lessons_stat()
        + progress_chip()
    )
    chips = "".join(
        f'<button type="button" class="chip" data-w="{esc(w)}">{esc(w)}</button>'
        for w in dict_chip_words(visible)
    )
    body = f"""
{header_html(site, "Tra từ điển cho người Việt: nghĩa tiếng Việt hiện trước, kèm phiên âm và nghe phát âm giọng Anh và giọng Mỹ.", stats)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả bài học</a></p>
  <section>
    <h2>Tra từ điển</h2>
    <p>Gõ 1 từ tiếng Anh, trang hiện nghĩa tiếng Việt trước, kèm phiên âm và nút nghe phát âm.</p>
    <div class="dict-search">
      <label class="sr-only" for="dict-input">Từ cần tra</label>
      <input id="dict-input" type="search" placeholder="Ví dụ: comfortable, borrow" autocomplete="off">
      <button type="button" class="btn btn-primary" id="dict-go">Tra từ</button>
    </div>
    <div id="dict-result" style="margin-top:16px"><p>Gõ 1 từ rồi bấm Tra từ nhé.</p></div>
  </section>
  <section>
    <h2>Từ trong bài học</h2>
    <div class="chips" id="dict-chips">{chips}</div>
  </section>
  <section>
    <h2>Từ đã tra gần đây</h2>
    <div id="dict-recent"><p>Chưa tra từ nào.</p></div>
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        "Từ điển: tra nghĩa và phát âm | Kho bài học Sai Đâu Sửa Đó",
        "Tra từ điển tiếng Anh cho người Việt: nghĩa tiếng Việt hiện trước, phiên âm IPA, nghe phát âm giọng Anh và giọng Mỹ.",
        SITE_URL + "/tu-dien/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=DICT_JS,
    )


def render_dashboard(data):
    site = data["site"]
    visible = visible_lessons(data)
    stats = (
        total_lessons_stat()
        + '<span class="stat">' + ICON["map"] + f' {len(site["paths"])} lộ trình</span>'
        + progress_chip()
    )
    path_names = {p["slug"]: p["name"] for p in site["paths"]}
    dash_js = DASH_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"').replace(
        "PATH_NAMES_PLACEHOLDER", json.dumps(path_names, ensure_ascii=False)
    )
    tiles = """
    <div class="stat-tiles">
      <div class="tile"><div class="num" id="dash-done">…</div><div class="lbl">Bài đã nhớ</div></div>
      <div class="tile"><div class="num" id="dash-acc">…</div><div class="lbl">Luyện tập đúng</div><div class="sub2">Tính trên mọi câu luyện trong trang</div></div>
      <div class="tile"><div class="num" id="dash-speak">…</div><div class="lbl">Buổi luyện nói</div></div>
      <div class="tile"><div class="num" id="dash-hours">…</div><div class="lbl">Tổng giờ luyện nói</div></div>
      <div class="tile"><div class="num" id="dash-streak">…</div><div class="lbl">Chuỗi ngày học</div></div>
      <div class="tile"><div class="num" id="dash-best">…</div><div class="lbl">Điểm luyện nói tốt nhất</div></div>
    </div>
"""
    body = f"""
{header_html(site, "Tiến độ học của bạn: bài đã nhớ, buổi luyện nói, chuỗi ngày học và bài tiếp theo.", stats)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả bài học</a></p>
  <section>
    <h2>Bảng lộ trình</h2>
    {tiles}
    <p class="note">Tiến độ lưu trên trình duyệt này, đổi máy sẽ mất. Muốn giữ lại thì về <a href="{BASE_PATH}/">trang chủ</a>, bấm Tải dữ liệu tiến độ (.json) để lưu ra máy.</p>
  </section>
  <section>
    <h2>Tiến độ từng lộ trình</h2>
    <div id="dash-paths"><p>Đang tải…</p></div>
  </section>
  <section>
    <h2>Bài tiếp theo</h2>
    <div id="dash-next"><p>Đang tải…</p></div>
  </section>
  <section>
    <h2>Ôn hôm nay</h2>
    <div id="dash-due"><p>Đang tải…</p></div>
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        "Bảng lộ trình | Kho bài học Sai Đâu Sửa Đó",
        "Bảng lộ trình học: tiến độ từng lộ trình, số buổi luyện nói, số giờ, chuỗi ngày học, bài tiếp theo.",
        SITE_URL + "/bang-lo-trinh/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=dash_js,
    )


def render_library(data):
    site = data["site"]
    visible = visible_lessons(data)
    paths_map = paths_for_lessons(data)
    topics = {}
    for l in visible:
        topics.setdefault(l["topic"], []).append(l)
    order = sorted(topics, key=lambda t: (-len(topics[t]), t))
    stats = (
        total_lessons_stat()
        + '<span class="stat">' + ICON["map"] + f' {len(site["paths"])} lộ trình</span>'
        + progress_chip()
    )
    chips = '<button type="button" class="chip on" data-topic="Tất cả">Tất cả (' + str(len(visible)) + ')</button>' + "".join(
        f'<button type="button" class="chip" data-topic="{esc(t)}">{esc(t)} ({len(topics[t])})</button>'
        for t in order
    )
    groups = ""
    for t in order:
        cards = "".join(card_html(l, paths_map.get(l["slug"], [])) for l in topics[t])
        groups += f"""
  <div class="lib-group" data-topic="{esc(t)}">
    <h3>{esc(t)} ({len(topics[t])} bài)</h3>
    <div class="grid">{cards}</div>
  </div>
"""
    body = f"""
{header_html(site, "Mọi bài học gom theo chủ đề: thì, cấu trúc, từ hay nhầm, mẫu câu.", stats)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả bài học</a></p>
  <section>
    <h2>Thư viện chủ đề</h2>
    <p>Bấm 1 chủ đề để lọc, hoặc gõ từ cần tìm. Mỗi thẻ mở ra bài học đầy đủ.</p>
    <div class="dict-search">
      <label class="sr-only" for="lib-search">Tìm bài học</label>
      <input id="lib-search" type="search" placeholder="Tìm bài học… ví dụ: borrow, thì hiện tại" autocomplete="off">
    </div>
    <div class="chips" id="lib-chips" style="margin-top:14px">{chips}</div>
    <p id="lib-count"></p>
    {groups}
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        "Thư viện chủ đề | Kho bài học Sai Đâu Sửa Đó",
        "Mọi bài học gom theo chủ đề: thì, cấu trúc, từ hay nhầm, mẫu câu. Lọc theo chủ đề và tìm kiếm.",
        SITE_URL + "/thu-vien-chu-de/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=LIB_JS,
    )


def render_speak(data):
    site = data["site"]
    visible = visible_lessons(data)
    stats = (
        total_lessons_stat()
        + progress_chip()
    )
    speak_data = f'<script>window.SDSC_SPEAK={json.dumps(speak_sentences(visible), ensure_ascii=False)};</script>'
    body = f"""
{header_html(site, "Luyện nói: nói câu mẫu, máy nghe lại và cho biết khớp được bao nhiêu.", stats)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả bài học</a></p>
  <section>
    <h2>Luyện nói</h2>
    <p>Chọn 1 câu mẫu, nghe câu mẫu rồi nói lại. Máy nghe và cho biết khớp được bao nhiêu, từ nào chưa rõ.</p>
    <p class="note">Trang chỉ kiểm tra câu nói có khớp với câu mẫu không, chưa chấm được từng âm như app chuyên luyện phát âm. Muốn chấm từng âm thì cần app chạy ngay trên máy, web này chưa làm được.</p>
    <p class="note warn" id="speak-nosupport" style="display:none">Trình duyệt này chưa hỗ trợ nhận diện giọng nói. Mở trang bằng Chrome hoặc Edge trên máy tính hoặc điện thoại Android để luyện nói nhé. Safari và iPhone chưa dùng được tính năng này.</p>
    <div class="filter-row">
      <label for="speak-pick">Câu mẫu:</label>
      <select id="speak-pick"></select>
    </div>
    <p class="speak-target" id="speak-target">Đang tải câu mẫu…</p>
    <p id="speak-vi"></p>
    <div class="chunk-actions">
      <button type="button" class="btn btn-navy" id="speak-listen">Nghe câu mẫu</button>
      <button type="button" class="btn btn-primary" id="speak-start">Bắt đầu nói</button>
      <button type="button" class="btn btn-ghost" id="speak-stop" disabled>Dừng</button>
    </div>
    <p id="speak-status">Bấm “Nghe câu mẫu” rồi bấm “Bắt đầu nói” nhé.</p>
    <div class="speak-heard" id="speak-heard"></div>
    <div id="speak-score"></div>
    <p id="speak-stats"></p>
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        "Luyện nói | Kho bài học Sai Đâu Sửa Đó",
        "Luyện nói tiếng Anh: nói câu mẫu, máy nghe lại và cho biết khớp được bao nhiêu.",
        SITE_URL + "/luyen-noi/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=speak_data + SPEAK_JS,
    )


def render_path(data, path):
    site = data["site"]
    visible = visible_lessons(data)
    by_slug = {l["slug"]: l for l in visible}
    stats = (
        total_lessons_stat()
        + '<span class="stat">' + ICON["map"] + f' {len(site["paths"])} lộ trình</span>'
        + progress_chip()
    )
    listed = [by_slug[s] for s in path["order"] if s in by_slug]
    items = ""
    for i, l in enumerate(listed):
        slug = l["slug"]
        items += f"""
<a class="path-item" data-slug="{esc(slug)}" href="{BASE_PATH}/{esc(slug)}/" onclick="sessionSet('sdsc-path','{esc(path['slug'])}')">
  <span class="n">{i + 1}</span>
  <div><h3>{esc(l['code'])}: {esc(l['title'])}</h3><p>{esc(l['why'])}</p></div>
  <span class="go">Học →</span>
</a>"""
    og_img = f"{SITE_URL}/images/{listed[0]['slug']}.jpg" if listed else SITE_URL + "/images/loi-001.jpg"
    body = f"""
{header_html(site, f"Lộ trình {path['name']}: {path['desc']}", stats)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả lộ trình</a></p>
  <section>
    <h2>{esc(path['name'])} <small>{len(listed)} bài, mỗi bài 3 đến 5 phút</small></h2>
    <div class="path-list">{items}</div>
  </section>
  <section>
    <div class="cta-row">
      <a class="btn btn-navy" href="{esc(site['facebook_group'])}" target="_blank" rel="noopener">{ICON["users"]} Vào Group làm bài tập</a>
      <a class="btn btn-primary" href="{esc(site.get('ask_url') or site['facebook_page'])}" target="_blank" rel="noopener">{ICON["mail"]} Gửi câu của bạn để được sửa</a>
    </div>
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        f"{path['name']} | Kho bài học Sai Đâu Sửa Đó",
        f"Lộ trình {path['name']}: {path['desc']}",
        f"{SITE_URL}/lo-trinh/{path['slug']}/",
        og_img,
        body,
        extra_js=PATH_PAGE_JS,
    )


def _split_sentences(s):
    """Tách chuỗi thành từng câu đơn (dấu . ! ? rồi khoảng trắng)."""
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", (s or "").strip()) if p.strip()]


def chunk_data(lesson):
    """Câu cho chế độ học từng cụm: câu đúng + ví dụ, mỗi cụm đúng 1 câu.
    Chuỗi nhiều câu tách thành từng câu đơn để mỗi cụm chỉ 1 câu."""
    raw = []
    if lesson.get("right"):
        raw.append({"en": lesson["right"], "vi": lesson.get("right_note", "")})
    for e in lesson.get("examples", []):
        if e.get("en"):
            raw.append({"en": e["en"], "vi": e.get("vi", "")})
    out = []
    seen = set()
    for c in raw:
        en_parts = _split_sentences(c["en"])
        vi_parts = _split_sentences(c.get("vi", ""))
        pairs = [(en_parts[i], vi_parts[i] if i < len(vi_parts) else "") for i in range(len(en_parts))]
        for en, vi in pairs:
            k = en.lower()
            if en and k not in seen:
                seen.add(k)
                out.append({"en": en, "vi": vi})
    return out


def speak_sentences(visible):
    """Mọi câu luyện nói (câu đúng + ví dụ của mọi bài), không trùng."""
    out = []
    seen = set()
    for l in visible:
        for c in chunk_data(l):
            k = c["en"].lower()
            if k in seen:
                continue
            seen.add(k)
            out.append({"en": c["en"], "vi": c["vi"], "code": l["code"], "slug": l["slug"]})
    return out


def dict_chip_words(visible):
    """Từ phát âm trong các bài học, dùng làm gợi ý tra nhanh."""
    words = []
    for l in visible:
        for w in ipa_words(l):
            if w not in words:
                words.append(w)
    return words[:12]


def render_lesson(data, lesson, prev_lesson, next_lesson):
    site = data["site"]
    visible = visible_lessons(data)
    slug = lesson["slug"]
    url = f"{SITE_URL}/{slug}/"
    img = f"{SITE_URL}/images/{slug}.jpg"
    title = f"{lesson['code']}: {lesson['title']} | Kho bài học Sai Đâu Sửa Đó"
    stats = (
        total_lessons_stat()
        + progress_chip()
    )
    prev_link = ""
    if prev_lesson:
        prev_link = (
            f'<a href="{BASE_PATH}/{prev_lesson["slug"]}/"><small>← Bài trước</small>'
            f'{esc(prev_lesson["code"])}: {esc(prev_lesson["title"])}</a>'
        )
    next_link = ""
    if next_lesson:
        next_link = (
            f'<a class="next" href="{BASE_PATH}/{next_lesson["slug"]}/"><small>Bài tiếp theo →</small>'
            f'{esc(next_lesson["code"])}: {esc(next_lesson["title"])}</a>'
        )
    prac_for_share = [{"key": f"{slug}:{i}", "prompt": p.get("prompt", "")}
                      for i, p in enumerate(lesson.get("practice", []))]
    if lesson.get("quiz"):
        prac_for_share.append({"key": f"{slug}:q", "prompt": lesson["quiz"].get("question", "")})
    share_data = {
        "code": lesson["code"],
        "title": lesson["title"],
        "wrong": lesson["wrong"] if lesson["type"] != "Quiz" else lesson["quiz"]["question"],
        "right": lesson["right"],
        "practice": prac_for_share,
    }
    chunks = chunk_data(lesson)
    chunk_section = ""
    if chunks:
        chunk_section = f"""
  <section id="chunk-box" class="chunk-box">
    <h2 style="margin-top:0">Học từng cụm</h2>
    <p>Đi từng cụm một: nghe câu mẫu, đọc lại, rồi qua cụm tiếp theo. Hết các cụm thì bấm để qua trang Luyện nói.</p>
    <script type="application/json" id="chunk-data">{json.dumps(chunks, ensure_ascii=False)}</script>
    <p class="chunk-progress" id="chunk-progress">Cụm 1/{len(chunks)}</p>
    <div class="bar"><i id="chunk-bar" style="width:{max(1, round(100 / len(chunks)))}%"></i></div>
    <p class="chunk-en" id="chunk-en">Đang tải cụm đầu tiên…</p>
    <p class="chunk-vi" id="chunk-vi"></p>
    <div class="chunk-actions">
      <button type="button" class="btn btn-navy" id="chunk-listen">Nghe câu mẫu</button>
      <button type="button" class="btn btn-ghost" id="chunk-prev">← Cụm trước</button>
      <button type="button" class="btn btn-primary" id="chunk-next">Cụm tiếp theo</button>
    </div>
  </section>
"""
    body = f"""
{header_html(site, f"Bài {lesson['code']} • Chủ đề {lesson['topic']} • Đăng ngày {fmt_date(lesson['date'])}", stats)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả bài học</a></p>
  <div class="wiz-progress"><div class="wiz-bar"><i id="wizFill"></i></div><span id="wizLabel">Bước 1</span></div>
  <section class="lesson">
    <div class="tags" style="margin:6px 0 10px">
      <span class="tag topic">{esc(lesson['topic'])}</span>
      <span class="tag">{esc(fmt_date(lesson['date']))}</span>
    </div>
    <h2 style="font-size:23px;line-height:1.3">{esc(lesson['code'])}: {esc(lesson['title'])}</h2>
    {lesson_body(lesson)}
  </section>
  {chunk_section}
  <section class="origin">
    <h3>Ảnh bài đăng trên Facebook</h3>
    <img class="originimg" src="{BASE_PATH}/images/{slug}.jpg" alt="Ảnh bài {esc(lesson['code'])}">
    <p><a href="{esc(lesson['fb'])}" target="_blank" rel="noopener">Xem bài gốc trên Facebook →</a></p>
  </section>
  <nav class="pagenav">{prev_link}{next_link if next_link else "<span></span>"}</nav>
</main>
<div class="wiz-bottom">
  <div class="wrap wiz-bottom-inner">
    <button type="button" class="btn btn-ghost" id="wizPrev">← Quay lại</button>
    <button type="button" class="btn btn-primary" id="wizNext">Tiếp tục →</button>
  </div>
</div>
{footer_html(site)}
"""
    lesson_js = LESSON_PAGE_JS.replace("__SLUG__", slug).replace(
        "__LESSON_JSON__", json.dumps(share_data, ensure_ascii=False)
    ).replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    chunk_js = CHUNK_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    return page_shell(
        title, og_description(lesson), url, img, body,
        extra_js=lesson_js + chunk_js,
        body_class="has-wiz",
    )


def render_readme(data):
    site = data["site"]
    visible = visible_lessons(data)
    n_reels = len(data["lessons"]) - len(visible)
    n_words = len(parse_vi_glossary())
    lines = [
        "# Kho bài học Sai Đâu Sửa Đó — Content engine học tiếng Anh mở",
        "",
        "Học tiếng Anh từ lỗi người Việt hay mắc. Mỗi ngày sửa một lỗi nhỏ.",
        "",
        f"- **{len(visible)} bài học** hiển thị trên web • **{len(data['lessons'])} bài** trong API • **{n_words} từ** trong từ điển • **{len(site['paths'])} lộ trình** • **{n_reels} Reel** đính kèm trong bài",
        "- Trang mới: **Từ điển** (/tu-dien/), **Bảng lộ trình** (/bang-lo-trinh/), "
        "**Thư viện chủ đề** (/thu-vien-chu-de/), **Luyện nói** (/luyen-noi/). "
        "Mỗi bài học có thêm chế độ Học từng cụm.",
        f"- Trang Facebook: {site['facebook_page']}",
        f"- Group: {site['facebook_group']}",
        "",
        "## API mở",
        "",
        "Toàn bộ dữ liệu học tiếng Anh của Trang, công khai dưới dạng file JSON tĩnh, "
        "không cần đăng ký, không cần khóa, không mất phí. Tài liệu đầy đủ cho lập trình viên "
        "ở trang [/api/](/api/).",
        "",
        "Dùng ngay:",
        "",
        "```js",
        'const BASE = "https://dongdarealest.github.io/sai-dau-sua-do/api/v1/";',
        'const data = await (await fetch(BASE + "lessons.json")).json();',
        'const detail = await (await fetch(BASE + "lessons/loi-001.json")).json();',
        "```",
        "",
        "| Đầu dữ liệu | Nội dung |",
        "|---|---|",
        "| `/api/v1/meta.json` | Phiên bản, số lượng, nguồn, giấy phép |",
        "| `/api/v1/lessons.json` | Danh sách gọn toàn bộ bài học |",
        "| `/api/v1/lessons/{slug}.json` | Chi tiết đầy đủ 1 bài học |",
        "| `/api/v1/dictionary.json` | Toàn bộ từ điển tiếng Việt |",
        "| `/api/v1/search-index.json` | Chỉ mục tìm kiếm |",
        "| `/api/v1/paths.json` | Lộ trình học |",
        "| `/api/openapi.yaml` | Định nghĩa OpenAPI cho mọi đầu dữ liệu |",
        "| `/api/` | Trang tài liệu cho lập trình viên |",
        "",
        "## Giấy phép",
        "",
        "- Code tạo trang web: MIT, xem file `LICENSE`.",
        "- Nội dung bài học, bảng nghĩa tiếng Việt, ảnh bài học, lộ trình: CC BY 4.0, "
        "xem file `LICENSE-CONTENT.md`.",
        "- Ghi công khi dùng lại nội dung: “Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi "
        "công và giữ link về Trang.”",
        "- Tên Trang, logo chữ S kèm dấu tick và slogan không thuộc giấy phép mở.",
        "",
        "## Đóng góp",
        "",
        "Báo lỗi dữ liệu bằng issue, đề xuất bài mới bằng pull request. Nghĩa mới phải kiểm "
        "chứng bằng Cambridge hoặc Oxford trước khi gửi.",
        "",
        "## Lộ trình",
        "",
    ]
    for p in site["paths"]:
        lines.append(f"### {p['name']} ({len(p['order'])} bài)")
        lines.append("")
        for slug in p["order"]:
            l = next((x for x in visible if x["slug"] == slug), None)
            if l:
                lines.append(f"- [{l['code']}: {l['title']}]({slug}/)")
        lines.append("")
    lines += [
        "## Cập nhật sau mỗi bài đăng",
        "",
        "Dữ liệu bài học nằm trong 1 tệp duy nhất `lessons.json`. Sau mỗi bài đăng lên Facebook:",
        "",
        "1. Viết file JSON của bài mới (đúng schema trong `CAP-NHAT-SITE.md`).",
        "2. Chạy `python3 update_site.py --lesson /tmp/bai-moi.json`. Script thêm bài,",
        "   dựng lại toàn bộ trang rồi đẩy lên GitHub Pages.",
        "",
        "Trang này chạy bằng GitHub Pages, sinh từ `lessons.json` bằng `generate_site.py`.",
    ]
    return "\n".join(lines) + "\n"


def count_sentences_why(why):
    if not why:
        return 0
    text = why.replace("vd.", "vd").replace("U.S.", "US").replace("U.K.", "UK")
    parts = [p.strip() for p in re.split(r"\.\s+|\.$", text) if p.strip()]
    return len(parts)


def validate_lessons(data, ws_root=None):
    """H-04: kiểm tra lessons.json, trả về danh sách lỗi (rỗng = hợp lệ)."""
    errors = []
    if not isinstance(data, dict) or not isinstance(data.get("lessons"), list):
        return ["lessons.json không có mảng 'lessons'"]
    ws_root = Path(ws_root) if ws_root else WS
    valid_types = ["Lỗi", "Mẫu câu", "Quiz", "Reels"]
    kinds = {None, "fill_blank", "find_error", "distinguish", "translate", "word_order"}
    for lesson in data["lessons"]:
        tag = lesson.get("slug") or lesson.get("code") or "?"
        if not isinstance(lesson, dict):
            errors.append(f"Bài {tag}: bản ghi không phải object")
            continue
        for field in ["slug", "code", "type", "topic", "date", "title", "wrong", "right", "why", "fb", "image_src"]:
            if not lesson.get(field):
                errors.append(f"Bài {tag}: thiếu trường bắt buộc '{field}'")
        if lesson.get("slug") and not re.match(r"^[a-z0-9-]+$", lesson["slug"]):
            errors.append(f"Bài {tag}: slug không khớp ^[a-z0-9-]+$")
        if lesson.get("type") and lesson["type"] not in valid_types:
            errors.append(f"Bài {tag}: type không hợp lệ '{lesson['type']}'")
        date = lesson.get("date", "")
        if date:
            import datetime as _dt
            try:
                _dt.date(int(date[0:4]), int(date[5:7]), int(date[8:10]))
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                    raise ValueError
            except Exception:
                errors.append(f"Bài {tag}: date không đúng YYYY-MM-DD hợp lệ '{date}'")
        fb = lesson.get("fb", "")
        if fb and not (fb.startswith("http://") or fb.startswith("https://")):
            errors.append(f"Bài {tag}: fb không phải URL http(s)")
        img = lesson.get("image_src", "")
        if img:
            p = (ws_root / img).resolve()
            if not str(p).startswith(str(ws_root.resolve())):
                errors.append(f"Bài {tag}: image_src thoát khỏi workspace")
            elif not p.exists():
                errors.append(f"Bài {tag}: không thấy file ảnh {p}")
        if count_sentences_why(lesson.get("why", "")) > 2:
            errors.append(f"Bài {tag}: 'Vì sao' quá 2 câu")
        q = lesson.get("quiz")
        if lesson.get("type") == "Quiz" and not q:
            errors.append(f"Bài {tag}: bài Quiz phải có quiz")
        if q:
            if not (q.get("question") and q.get("options") and len(q["options"]) >= 2
                    and isinstance(q.get("answer"), int) and 0 <= q["answer"] < len(q["options"])
                    and q.get("explanation")):
                errors.append(f"Bài {tag}: quiz thiếu question/options/answer/explanation hợp lệ")
        show = lesson.get("show_in_ui", lesson.get("type") != "Reels")
        prac = lesson.get("practice", [])
        if show:
            if len(prac) < 2:
                errors.append(f"Bài {tag}: bài hiện cho người học phải có ít nhất 2 câu luyện (practice)")
            if not lesson.get("remember"):
                errors.append(f"Bài {tag}: thiếu dòng 'Nhớ điều này' (remember)")
        for i, p in enumerate(prac):
            if not isinstance(p, dict) or not p.get("prompt") or not p.get("options") or len(p.get("options", [])) < 2 or not p.get("explanation"):
                errors.append(f"Bài {tag}: practice[{i}] thiếu prompt/options(≥2)/explanation")
                continue
            if p.get("kind") not in kinds:
                errors.append(f"Bài {tag}: practice[{i}] kind không hợp lệ '{p.get('kind')}'")
                continue
            if p.get("kind") == "word_order":
                ans = p.get("answer")
                if not (isinstance(ans, list) and sorted(ans) == list(range(len(p["options"])))):
                    errors.append(f"Bài {tag}: practice[{i}] word_order answer phải là hoán vị của 0..{len(p['options']) - 1}")
            elif not (isinstance(p.get("answer"), int) and 0 <= p["answer"] < len(p["options"])):
                errors.append(f"Bài {tag}: practice[{i}] answer ngoài khoảng 0..{len(p['options']) - 1}")
        for entry in lesson.get("ipa", []):
            if not entry.get("text") or not entry.get("source"):
                errors.append(f"Bài {tag}: IPA thiếu text/source")
        # Quy tac cua Dong (00:49 15/11): truong hien thi khong duoc chua gach ngang
        # (-, en dash, em dash). Tru slug/date/image_src/fb URL vi do la cau truc.
        _hyph = ("-", "\u2013", "\u2014")

        def _has_hyph(txt):
            return isinstance(txt, str) and any(c in txt for c in _hyph)

        def _hyph_err(where):
            errors.append(f"Bài {tag}: {where} còn dấu gạch ngang, viết lại không dùng gạch ngang")

        for _f in ("title", "why", "wrong", "right", "remember", "problem",
                   "core", "tip", "articulation"):
            if _has_hyph(lesson.get(_f)):
                _hyph_err(_f)
        for _grp in ("examples", "compare", "mistakes"):
            for _it in lesson.get(_grp, []) or []:
                if isinstance(_it, dict):
                    for _k, _v in _it.items():
                        if _has_hyph(_v):
                            _hyph_err(f"{_grp}.{_k}")
        for _i, _p in enumerate(prac):
            for _k in ("prompt", "explanation"):
                if _has_hyph(_p.get(_k)):
                    _hyph_err(f"practice[{_i}].{_k}")
            for _o in _p.get("options", []) or []:
                if isinstance(_o, str) and _has_hyph(_o):
                    _hyph_err(f"practice[{_i}].options")
                    break
            for _o in _p.get("options", []) or []:
                if isinstance(_o, dict):
                    for _k, _v in _o.items():
                        if _has_hyph(_v):
                            _hyph_err(f"practice[{_i}].options.{_k}")
        if q:
            for _k in ("question", "prompt", "explanation"):
                if _has_hyph(q.get(_k)):
                    _hyph_err(f"quiz.{_k}")
            for _o in q.get("options", []) or []:
                if _has_hyph(_o):
                    _hyph_err("quiz.options")
                    break
        for _e in lesson.get("ipa", []) or []:
            for _k in ("text", "note", "source"):
                if _has_hyph(_e.get(_k)):
                    _hyph_err(f"ipa.{_k}")
    return errors


FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#173F5F"/><text x="32" y="44" font-family="sans-serif" font-size="38" font-weight="900" fill="#FFFFFF" text-anchor="middle">S</text><path d="M42 46 l6 6 l12 -13" fill="none" stroke="#F26B38" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>
"""


# ---------------------------------------------------------------------------
# API mở (19/11): dữ liệu học tiếng Anh của Trang, công khai dạng file JSON
# tĩnh dưới api/v1/ để lập trình viên ngoài dùng không cần khóa. Nguồn sự
# thật duy nhất vẫn là lessons.json và bảng VI_GLOSSARY trong DICT_JS;
# API chỉ chiếu dữ liệu sẵn có ra dạng khác, không tạo nguồn thứ 2.
# ---------------------------------------------------------------------------
API_VERSION = "1.0.0"
API_BASE = SITE_URL + "/api/v1/"

_GLOSSARY_CACHE = None


def parse_vi_glossary():
    """Đọc bảng VI_GLOSSARY trong DICT_JS thành dict Python.
    Mỗi từ ánh xạ tới danh sách nghĩa, mỗi nghĩa là mảng
    [từ loại, nghĩa tiếng Việt, ví dụ tiếng Anh, dịch ví dụ]."""
    global _GLOSSARY_CACHE
    if _GLOSSARY_CACHE is not None:
        return _GLOSSARY_CACHE
    m = re.search(r"const VI_GLOSSARY=\{(.*?)\n\};", DICT_JS, re.S)
    if not m:
        raise ValueError("không tìm thấy VI_GLOSSARY trong DICT_JS")
    text = "{" + m.group(1) + "\n}"
    try:
        _GLOSSARY_CACHE = json.loads(text)
    except json.JSONDecodeError:
        fixed = re.sub(r",\s*([}\]])", r"\1", text)
        _GLOSSARY_CACHE = json.loads(fixed)
    return _GLOSSARY_CACHE


def glossary_senses(raw_senses):
    out = []
    for s in raw_senses:
        sense = {"pos": s[0], "meaning": s[1]}
        if len(s) >= 4:
            sense["example_en"] = s[2]
            sense["example_vi"] = s[3]
        out.append(sense)
    return out


def words_with_example(glossary):
    return sum(1 for v in glossary.values() if any(len(s) >= 4 for s in v))


def word_mistake_slugs(data):
    """Mỗi từ trong bảng nghĩa ánh xạ tới tối đa 5 slug bài học mà từ đó
    xuất hiện trong cặp câu sai và câu đúng của bài, khớp theo ranh giới
    từ, không phân biệt hoa thường. Thứ tự slug theo thứ tự bài trong
    lessons.json. Từ nào không xuất hiện ở bài nào thì danh sách rỗng."""
    glossary = parse_vi_glossary()
    patterns = {w: re.compile(r"\b" + re.escape(w) + r"\b", re.I)
                for w in glossary}
    found = {w: [] for w in glossary}
    for lesson in data["lessons"]:
        text = (lesson.get("wrong", "") + " " + lesson.get("right", ""))
        if not text.strip():
            continue
        slug = lesson["slug"]
        for w, pat in patterns.items():
            if len(found[w]) >= 5:
                continue
            if pat.search(text):
                found[w].append(slug)
    return found


def api_source(site):
    # Tên trong khối ghi công là tên Trang, không phải tiêu đề trang web.
    return {
        "name": "Sai Đâu Sửa Đó",
        "site": SITE_URL,
        "facebook_page": site["facebook_page"],
        "facebook_group": site["facebook_group"],
        "license": "CC BY 4.0",
        "attribution": "Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang.",
    }


def api_meta_block(site):
    return {"api_version": API_VERSION, "source": api_source(site)}


def api_meta(data):
    glossary = parse_vi_glossary()
    return {
        "api_version": API_VERSION,
        "api_base": API_BASE,
        "total_lessons": len(data["lessons"]),
        "visible_lessons": len(visible_lessons(data)),
        "total_words": len(glossary),
        "words_with_example": words_with_example(glossary),
        "learning_paths": len(data["site"]["paths"]),
        "updated": datetime.date.today().isoformat(),
        "source": api_source(data["site"]),
    }


def api_lessons_list(data):
    return {
        "meta": {
            "api_version": API_VERSION,
            "total_lessons": len(data["lessons"]),
            "visible_lessons": len(visible_lessons(data)),
            "source": api_source(data["site"]),
        },
        "lessons": [
            {
                "slug": l["slug"],
                "code": l["code"],
                "type": l["type"],
                "topic": l["topic"],
                "title": l["title"],
                "date": l["date"],
                "wrong": l.get("wrong", ""),
                "right": l.get("right", ""),
                "remember": l.get("remember", ""),
                "url": SITE_URL + "/" + l["slug"] + "/",
                "fb": l.get("fb", ""),
                "image": l.get("image_src", ""),
                "show_in_ui": l.get("show_in_ui", True),
            }
            for l in data["lessons"]
        ],
    }


def api_lesson_detail(data, lesson):
    l = lesson
    return {
        "meta": api_meta_block(data["site"]),
        "lesson": {
            "slug": l["slug"],
            "code": l["code"],
            "type": l["type"],
            "topic": l["topic"],
            "title": l["title"],
            "date": l["date"],
            "wrong": l.get("wrong", ""),
            "wrong_note": l.get("wrong_note", ""),
            "right": l.get("right", ""),
            "right_note": l.get("right_note", ""),
            "why": l.get("why", ""),
            "problem": l.get("problem"),
            "core": l.get("core"),
            "compare": l.get("compare", []),
            "mistakes": l.get("mistakes", []),
            "remember": l.get("remember", ""),
            "examples": l.get("examples", []),
            "practice": l.get("practice", []),
            "quiz": l.get("quiz"),
            "reel": l.get("reel"),
            "tip": l.get("tip"),
            "articulation": l.get("articulation"),
            "ipa": l.get("ipa", []),
            "dict_links": l.get("dict_links", []),
            "image": l.get("image_src", ""),
            "fb": l.get("fb", ""),
            "url": SITE_URL + "/" + l["slug"] + "/",
            "show_in_ui": l.get("show_in_ui", True),
        },
    }


def api_dictionary(data):
    glossary = parse_vi_glossary()
    mistakes = word_mistake_slugs(data)
    return {
        "meta": {
            "api_version": API_VERSION,
            "total_words": len(glossary),
            "words_with_example": words_with_example(glossary),
            "source": api_source(data["site"]),
            "meaning_source": "Bảng nghĩa do Trang soạn và kiểm tra bằng tay. Phiên âm và nghĩa tiếng Anh lấy trực tiếp từ dictionaryapi.dev lúc tra, không lưu trong dữ liệu này.",
        },
        "words": {w: {"senses": glossary_senses(s), "mistakes": mistakes[w]}
                  for w, s in glossary.items()},
    }


def api_paths(data):
    return {
        "meta": api_meta_block(data["site"]),
        "paths": [
            {
                "slug": p["slug"],
                "name": p["name"],
                "desc": p["desc"],
                "icon": p.get("icon", ""),
                "order": list(p["order"]),
            }
            for p in data["site"]["paths"]
        ],
    }


def api_search_index(data):
    return build_search_index(visible_lessons(data), paths_for_lessons(data))


def api_openapi_yaml(data):
    glossary = parse_vi_glossary()
    n = len(data["lessons"])
    nw = len(glossary)
    np_ = len(data["site"]["paths"])
    return f"""openapi: 3.0.3
info:
  title: API mở Kho bài học Sai Đâu Sửa Đó
  version: {API_VERSION}
  description: Dữ liệu học tiếng Anh của Trang Sai Đâu Sửa Đó, công khai dưới dạng file JSON tĩnh trên GitHub Pages. Không cần đăng ký, không cần khóa, không mất phí. Hiện có {n} bài học, {nw} từ trong từ điển và {np_} lộ trình học.
  license:
    name: CC BY 4.0
    url: https://creativecommons.org/licenses/by/4.0/
  contact:
    url: {data["site"]["facebook_page"]}
servers:
  - url: {SITE_URL}
paths:
  /api/v1/meta.json:
    get:
      summary: Phiên bản, số lượng, nguồn, giấy phép
      responses:
        "200":
          description: Thông tin phiên bản và nguồn gốc toàn bộ API
          content:
            application/json:
              schema:
                type: object
  /api/v1/lessons.json:
    get:
      summary: Danh sách gọn toàn bộ bài học
      responses:
        "200":
          description: Danh sách gọn {n} bài học, lọc phía trình duyệt
          content:
            application/json:
              schema:
                type: object
  /api/v1/lessons/{{slug}}.json:
    get:
      summary: Chi tiết đầy đủ 1 bài học
      parameters:
        - name: slug
          in: path
          required: true
          schema:
            type: string
          example: loi-001
      responses:
        "200":
          description: Toàn bộ nội dung 1 bài học, gồm bài tập đầy đủ
          content:
            application/json:
              schema:
                type: object
  /api/v1/dictionary.json:
    get:
      summary: Toàn bộ từ điển tiếng Việt
      responses:
        "200":
          description: Toàn bộ {nw} từ, nghĩa tiếng Việt đã kiểm tra tay
          content:
            application/json:
              schema:
                type: object
  /api/v1/search-index.json:
    get:
      summary: Chỉ mục tìm kiếm
      responses:
        "200":
          description: Chỉ mục tìm kiếm cho các bài đang hiển thị
          content:
            application/json:
              schema:
                type: array
  /api/v1/paths.json:
    get:
      summary: Lộ trình học
      responses:
        "200":
          description: "{np_} lộ trình học của Trang"
          content:
            application/json:
              schema:
                type: object
  /api/:
    get:
      summary: Trang tài liệu cho lập trình viên
      responses:
        "200":
          description: Trang HTML tài liệu, kèm ví dụ gọi API và bản thử trực tiếp
          content:
            text/html:
              schema:
                type: string
"""


API_DOCS_JS = r"""
<script>
(function(){
  function showLessons(box, lessons){
    var html = "";
    lessons.slice(0, 3).forEach(function(l){
      html += "<p><b>" + escapeHtml(l.code) + ": " + escapeHtml(l.title) + "</b><br>Sai: "
        + escapeHtml(l.wrong) + "<br>Đúng: " + escapeHtml(l.right) + "</p>";
    });
    box.innerHTML = html;
  }
  var demoBtn = document.getElementById("api-demo-btn");
  var demoBox = document.getElementById("api-demo-lessons");
  if (demoBtn && demoBox) {
    demoBtn.addEventListener("click", function(){
      demoBox.textContent = "Đang tải...";
      fetch("v1/lessons.json").then(function(r){ return r.json(); }).then(function(d){
        showLessons(demoBox, d.lessons);
      }).catch(function(){
        demoBox.textContent = "Không tải được danh sách bài. Thử tải lại trang nhé.";
      });
    });
  }
  var dictCache = null;
  function dictLookup(word){
    word = word.toLowerCase().trim();
    if (dictCache.words[word]) return dictCache.words[word];
    var endings = ["ing", "es", "ed", "s"];
    for (var i = 0; i < endings.length; i++) {
      var e = endings[i];
      if (word.endsWith(e)) {
        var base = word.slice(0, word.length - e.length);
        if (dictCache.words[base]) return dictCache.words[base];
      }
    }
    if (word.endsWith("ies")) {
      var b2 = word.slice(0, word.length - 3) + "y";
      if (dictCache.words[b2]) return dictCache.words[b2];
    }
    return null;
  }
  var dictBtn = document.getElementById("api-demo-dict-btn");
  var dictInput = document.getElementById("api-demo-dict-input");
  var dictBox = document.getElementById("api-demo-dict");
  if (dictBtn && dictInput && dictBox) {
    dictBtn.addEventListener("click", function(){
      var w = dictInput.value.trim();
      if (!w) { dictBox.textContent = "Gõ 1 từ rồi bấm Tra từ nhé."; return; }
      dictBox.textContent = "Đang tải từ điển...";
      var p = dictCache ? Promise.resolve(dictCache)
        : fetch("v1/dictionary.json").then(function(r){ return r.json(); });
      p.then(function(d){
        dictCache = d;
        var hit = dictLookup(w);
        if (!hit) { dictBox.textContent = "Chưa có từ này trong bảng từ của Trang."; return; }
        var html = "<p><b>" + escapeHtml(w) + "</b></p>";
        hit.senses.forEach(function(s){
          html += "<p>" + escapeHtml(s.pos) + ": " + escapeHtml(s.meaning);
          if (s.example_en) {
            html += "<br>Ví dụ: " + escapeHtml(s.example_en)
              + "<br>Dịch: " + escapeHtml(s.example_vi);
          }
          html += "</p>";
        });
        dictBox.innerHTML = html;
      }).catch(function(){
        dictBox.textContent = "Không tải được từ điển. Thử tải lại trang nhé.";
      });
    });
  }
})();
</script>
"""


def _api_kb(n_bytes):
    return ("%.1f" % (n_bytes / 1024)).replace(".", ",") + " KB"


def render_api_docs(data):
    site = data["site"]
    glossary = parse_vi_glossary()
    n_total = len(data["lessons"])
    n_visible = len(visible_lessons(data))
    n_words = len(glossary)
    n_wex = words_with_example(glossary)
    meta_s = json.dumps(api_meta(data), ensure_ascii=False, indent=2)
    lessons_s = json.dumps(api_lessons_list(data), ensure_ascii=False, indent=2)
    dict_s = json.dumps(api_dictionary(data), ensure_ascii=False, indent=2)
    search_s = json.dumps(api_search_index(data), ensure_ascii=False, indent=2)
    paths_s = json.dumps(api_paths(data), ensure_ascii=False, indent=2)
    openapi_s = api_openapi_yaml(data)
    detail_sizes = [
        len(json.dumps(api_lesson_detail(data, l), ensure_ascii=False, indent=2).encode("utf-8"))
        for l in data["lessons"]
    ]
    rows = "".join([
        "<tr><td><code>/api/v1/meta.json</code></td><td>Phiên bản, số lượng, nguồn, giấy phép</td><td>" + _api_kb(len(meta_s.encode("utf-8"))) + "</td></tr>",
        "<tr><td><code>/api/v1/lessons.json</code></td><td>Danh sách gọn toàn bộ bài học</td><td>" + _api_kb(len(lessons_s.encode("utf-8"))) + "</td></tr>",
        "<tr><td><code>/api/v1/lessons/{slug}.json</code></td><td>Chi tiết đầy đủ 1 bài học</td><td>" + _api_kb(min(detail_sizes)) + " tới " + _api_kb(max(detail_sizes)) + " mỗi bài</td></tr>",
        "<tr><td><code>/api/v1/dictionary.json</code></td><td>Toàn bộ từ điển tiếng Việt</td><td>" + _api_kb(len(dict_s.encode("utf-8"))) + "</td></tr>",
        "<tr><td><code>/api/v1/search-index.json</code></td><td>Chỉ mục tìm kiếm</td><td>" + _api_kb(len(search_s.encode("utf-8"))) + "</td></tr>",
        "<tr><td><code>/api/v1/paths.json</code></td><td>Lộ trình học</td><td>" + _api_kb(len(paths_s.encode("utf-8"))) + "</td></tr>",
        "<tr><td><code>/api/openapi.yaml</code></td><td>Định nghĩa OpenAPI cho mọi đầu dữ liệu</td><td>" + _api_kb(len(openapi_s.encode("utf-8"))) + "</td></tr>",
        "<tr><td><code>/api/</code></td><td>Trang tài liệu này</td><td>Trang HTML</td></tr>",
    ])
    stats = total_lessons_stat() + progress_chip()
    body = """
__HEADER__
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="__BASE_PATH__/">← Tất cả bài học</a></p>
  <section>
    <h2>API mở là gì</h2>
    <p>API mở là toàn bộ dữ liệu học tiếng Anh của Trang Sai Đâu Sửa Đó, công khai dưới dạng file JSON tĩnh trên GitHub Pages. Bất cứ lập trình viên nào cũng dùng được, không cần đăng ký, không cần khóa, không mất phí, không cần máy chủ riêng. Một app flashcard, một chatbot luyện nói, một Zalo mini app hay một app ôn tập theo lịch SRS đều có thể lấy nội dung từ đây và chạy được ngay.</p>
    <ul>
      <li>__TOTAL_WORDS__ từ trong bảng từ điển do Trang soạn và kiểm tra bằng tay, từng nghĩa một, viết cho người Việt chứ không dịch máy từ nghĩa tiếng Anh.</li>
      <li>__TOTAL_LESSONS__ bài học, mỗi bài là một cặp câu sai và câu đúng thật, kèm lý do vì sao sai bằng tiếng Việt và bài tập có giải thích.</li>
      <li>Mọi ví dụ tiếng Anh đều có dịch tiếng Việt ngay bên dưới.</li>
      <li>Từ điển hiểu dạng chia của từ. Tra loves ra love, tra went ra nghĩa quá khứ của go, tra don't ra nghĩa viết tắt.</li>
      <li>Mỗi từ trong từ điển kèm tối đa 5 bài học mà từ đó xuất hiện trong cặp câu sai và câu đúng, để tra từ là thấy ngay lỗi người Việt hay mắc với từ đó.</li>
      <li>Dữ liệu nhẹ và chạy ngoại tuyến được. Tải một lần rồi dùng tiếp không cần mạng.</li>
      <li>Mọi đầu dữ liệu đều mang theo ghi công và link về Trang. API càng được dùng nhiều, Trang càng được biết tới.</li>
    </ul>
    <p>Đường dẫn gốc: <code>__SITE_URL__/api/v1/</code></p>
  </section>
  <section>
    <h2>Bắt đầu trong 30 giây</h2>
    <p>Lấy danh sách bài học rồi lọc ra bài loại Lỗi thuộc chủ đề giao tiếp:</p>
    <pre><code>const BASE = "__SITE_URL__/api/v1/";
const data = await (await fetch(BASE + "lessons.json")).json();
const loiGiaoTiep = data.lessons.filter(
  (l) =&gt; l.type === "Lỗi" &amp;&amp; l.topic === "giao tiếp"
);
console.log(loiGiaoTiep.length, "bài lỗi giao tiếp");</code></pre>
    <p><button type="button" class="btn btn-primary" id="api-demo-btn">Thử ngay: lấy 3 bài đầu tiên</button></p>
    <div id="api-demo-lessons"><p>Bấm nút trên để xem 3 bài đầu tiên tải từ API.</p></div>
    <p>Lấy chi tiết 1 bài rồi chạy 1 câu luyện tập:</p>
    <pre><code>const detail = await (await fetch(BASE + "lessons/loi-001.json")).json();
const lesson = detail.lesson;
const q = lesson.practice[0];
console.log(q.prompt, q.options, "Đáp án đúng là lựa chọn số", q.answer);
console.log("Giải thích:", q.explanation);</code></pre>
  </section>
  <section>
    <h2>Đầu dữ liệu</h2>
    <div class="tablewrap"><table>
      <thead><tr><th>Đường dẫn</th><th>Nội dung</th><th>Kích thước</th></tr></thead>
      <tbody>
__ROWS__
      </tbody>
    </table></div>
    <p>Định nghĩa OpenAPI đầy đủ nằm ở <a href="__BASE_PATH__/api/openapi.yaml">openapi.yaml</a>, dùng được cho Postman và APIs.guru.</p>
  </section>
  <section>
    <h2>Cách tra từ</h2>
    <p>Từ điển chỉ lưu dạng gốc và dạng bất quy tắc, không lưu mọi dạng chia. App tra từ nên chuẩn hóa trước khi tìm, theo đúng cách web của Trang đang làm:</p>
    <ol>
      <li>Viết thường toàn bộ từ, bỏ khoảng trắng thừa.</li>
      <li>Tìm đúng từ trong bảng trước. Ví dụ books không có trong bảng, book thì có.</li>
      <li>Nếu không thấy, thử bỏ đuôi chia: s, es, ed, ing, rồi thử đổi ies thành y. Ví dụ loves bỏ s thành love, going bỏ ing thành go.</li>
      <li>Dạng bất quy tắc đã có sẵn trong bảng: went nghĩa là đã đi, said nghĩa là đã nói, children nghĩa là trẻ em.</li>
      <li>Dạng rút gọn đã có sẵn trong bảng: don't, doesn't, didn't, i'd.</li>
    </ol>
    <pre><code>const dict = await (await fetch(BASE + "dictionary.json")).json();
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
console.log(lookup("tomorrow"));</code></pre>
    <p>Mỗi từ trả về còn có trường mistakes là danh sách tối đa 5 slug bài học mà từ đó xuất hiện trong cặp câu sai và câu đúng. App có thể dùng trường này để gợi ý bài học ngay khi người dùng tra từ.</p>
    <p>Thử tra từ ngay tại đây:</p>
    <div class="dict-search">
      <label class="sr-only" for="api-demo-dict-input">Từ cần tra</label>
      <input id="api-demo-dict-input" type="search" placeholder="Ví dụ: tomorrow, loves" autocomplete="off">
      <button type="button" class="btn btn-primary" id="api-demo-dict-btn">Tra từ</button>
    </div>
    <div id="api-demo-dict" style="margin-top:16px"><p>Gõ 1 từ rồi bấm Tra từ nhé.</p></div>
  </section>
  <section>
    <h2>4 app ví dụ</h2>
    <h3>App flashcard</h3>
    <p>Lấy lessons.json, mỗi thẻ hiện câu sai ở mặt trước, lật thẻ hiện câu đúng kèm lý do và câu nhớ nhanh. Dùng trường remember làm mặt sau ngắn gọn.</p>
    <h3>Chatbot luyện nói</h3>
    <p>Lấy chi tiết bài theo slug, chatbot hỏi từng câu trong practice theo thứ tự, chấm đúng sai bằng answer, giải thích bằng explanation. Hết bài thì gợi ý bài tiếp theo trong paths.json.</p>
    <h3>Zalo mini app</h3>
    <p>Màn hình chính hiện 3 lộ trình từ paths.json, bấm vào lộ trình thì tải chi tiết từng bài trong order. Mỗi bài hiện gọn câu sai và câu đúng, bấm vào mới xem lý do và bài tập.</p>
    <h3>App ôn tập theo lịch SRS</h3>
    <p>Lấy practice của mọi bài, trộn thành ngân hàng câu hỏi. Người học trả lời đúng thì đẩy câu đó ra xa theo lịch, trả lời sai thì cho gặp lại sớm. Dùng trường date để ưu tiên bài mới, dùng topic để ôn theo chủ đề yếu.</p>
  </section>
  <section>
    <h2>Giấy phép và ghi công</h2>
    <p>Code tạo trang web và code ví dụ trong tài liệu này dùng giấy phép MIT: ai cũng được dùng, sửa và bán sản phẩm làm từ code, chỉ cần giữ lại dòng bản quyền và giấy phép.</p>
    <p>Nội dung bài học, bảng nghĩa tiếng Việt, ảnh bài học và lộ trình dùng giấy phép CC BY 4.0: ai cũng được chia sẻ và dùng lại, kể cả để kiếm tiền, với 1 điều kiện duy nhất là ghi công đúng cách.</p>
    <blockquote>Nguồn: Sai Đâu Sửa Đó. Dùng lại nội dung xin ghi công và giữ link về Trang.<br><a href="__SITE_URL__/">Kho bài học</a> &nbsp;•&nbsp; <a href="__FB_PAGE__">Trang Facebook</a></blockquote>
    <p>Tên Trang, logo chữ S kèm dấu tick và slogan Mỗi ngày sửa một lỗi nhỏ là dấu hiệu nhận diện của Trang, không thuộc giấy phép mở. Ghi công bằng tên và link thì được, tự ý dùng logo làm thương hiệu riêng thì không được, cần hỏi Trang trước.</p>
    <p>Phiên âm và nghĩa tiếng Anh khi tra từ trên web lấy trực tiếp từ dictionaryapi.dev lúc tra, không lưu trong file API. Dữ liệu gốc của họ lấy từ Wiktionary theo giấy phép CC BY-SA 3.0. Nếu sau này có lưu phần đó vào file API, Trang sẽ ghi rõ nguồn và giữ giấy phép CC BY-SA cho đúng phần đó.</p>
    <p>Toàn văn giấy phép: <a href="__BASE_PATH__/LICENSE">MIT cho code</a> &nbsp;•&nbsp; <a href="__BASE_PATH__/LICENSE-CONTENT.md">CC BY 4.0 cho nội dung</a></p>
  </section>
  <section>
    <h2>Đóng góp</h2>
    <p>Báo lỗi dữ liệu bằng issue, đề xuất bài mới bằng pull request trên repo <a href="https://github.com/Dongdarealest/sai-dau-sua-do">Dongdarealest/sai-dau-sua-do</a>. Nghĩa mới phải kiểm chứng bằng Cambridge hoặc Oxford trước khi gửi.</p>
  </section>
  <section>
    <h2>Giới hạn</h2>
    <ul>
      <li>API chỉ đọc, không ghi. Không có đầu dữ liệu nào nhận bài mới hay lưu tiến độ người học. Muốn đóng góp thì gửi pull request lên repo.</li>
      <li>Không có tìm kiếm phía máy chủ. Tìm kiếm chạy ngay trên máy người dùng bằng search-index.json hoặc lọc lessons.json.</li>
      <li>Không có phiên âm trong dữ liệu tĩnh. Phiên âm và âm thanh lấy trực tiếp từ dictionaryapi.dev lúc tra, giống cách web của Trang đang làm.</li>
      <li>Không có dịch máy trong dữ liệu tĩnh. Nghĩa dịch máy chỉ xuất hiện lúc tra trên web khi không còn nguồn nào, và luôn ghi rõ là dịch máy chưa kiểm chứng.</li>
      <li>Nội dung tăng theo nhịp đăng của Trang. App nên tải lại file mỗi lần mở để thấy bài mới.</li>
    </ul>
    <p>Hiện có __TOTAL_LESSONS__ bài học, __VISIBLE_LESSONS__ bài đang hiển thị trên web, __TOTAL_WORDS__ từ trong từ điển, trong đó __WORDS_WITH_EXAMPLE__ từ có ví dụ kèm dịch.</p>
  </section>
</main>
__FOOTER__
"""
    body = body.replace("__HEADER__", header_html(
        site,
        "Dữ liệu học tiếng Anh của Trang, mở cho mọi lập trình viên dùng miễn phí, không cần khóa.",
        stats))
    body = body.replace("__FOOTER__", footer_html(site))
    body = body.replace("__BASE_PATH__", BASE_PATH)
    body = body.replace("__SITE_URL__", SITE_URL)
    body = body.replace("__FB_PAGE__", esc(site["facebook_page"]))
    body = body.replace("__TOTAL_LESSONS__", str(n_total))
    body = body.replace("__VISIBLE_LESSONS__", str(n_visible))
    body = body.replace("__TOTAL_WORDS__", str(n_words))
    body = body.replace("__WORDS_WITH_EXAMPLE__", str(n_wex))
    body = body.replace("__ROWS__", rows)
    return page_shell(
        "API mở | Kho bài học Sai Đâu Sửa Đó",
        "API mở Kho bài học Sai Đâu Sửa Đó: dữ liệu học tiếng Anh cho lập trình viên, không cần khóa, không mất phí.",
        SITE_URL + "/api/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=API_DOCS_JS,
    )


def write_if_changed(path, text):
    """Tối ưu B (19/11): chỉ ghi file khi nội dung đổi. Trả True nếu đã ghi
    (file mới hoặc nội dung đổi), False nếu giữ nguyên. Nhờ đó mỗi lần đăng
    1 bài chỉ đổi vài file thay vì viết lại toàn bộ cây."""
    path = Path(path)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def write_sitemap_robots(data):
    visible = visible_lessons(data)
    urls = [SITE_URL + "/"] + [f"{SITE_URL}/{l['slug']}/" for l in visible]
    urls += [f"{SITE_URL}/lo-trinh/{p['slug']}/" for p in data["site"]["paths"]]
    urls += [SITE_URL + "/tu-dien/", SITE_URL + "/bang-lo-trinh/",
             SITE_URL + "/thu-vien-chu-de/", SITE_URL + "/luyen-noi/"]
    # API mở (19/11): chỉ thêm đường dẫn mới, không đổi đường dẫn cũ.
    urls += [SITE_URL + "/api/", SITE_URL + "/api/v1/meta.json",
             SITE_URL + "/api/v1/lessons.json", SITE_URL + "/api/v1/dictionary.json"]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>{u}</loc></url>")
    lines.append("</urlset>")
    n = 0
    n += write_if_changed(ROOT / "sitemap.xml", "\n".join(lines) + "\n")
    n += write_if_changed(ROOT / "robots.txt",
                          "User-agent: *\nAllow: /\nSitemap: " + SITE_URL + "/sitemap.xml\n")
    return n


def main():
    try:
        data = json.loads((ROOT / "lessons.json").read_text(encoding="utf-8"))
    except Exception as e:
        print("LỖI lessons.json không đọc được:", e, file=sys.stderr)
        sys.exit(1)
    errs = validate_lessons(data, WS)
    if errs:
        for e in errs:
            print("LỖI validate:", e, file=sys.stderr)
        sys.exit(1)
    lessons = data["lessons"]
    site = data["site"]
    visible = visible_lessons(data)
    vis_slugs = {l["slug"] for l in visible}

    # images: only visible lessons — kiểm tra đủ ảnh TRƯỚC khi xóa (H-05)
    for lesson in visible:
        src = WS / lesson["image_src"]
        if not src.exists():
            print("THIẾU ẢNH:", src, file=sys.stderr)
            sys.exit(1)
    # Tối ưu B (19/11): chỉ nén lại ảnh nào đổi (ảnh nguồn mới hơn ảnh đích
    # hoặc chưa có ảnh đích); ảnh cũ giữ nguyên, không xóa cả thư mục nữa.
    img_dir = ROOT / "images"
    img_dir.mkdir(exist_ok=True)
    changed = 0
    for lesson in visible:
        src = WS / lesson["image_src"]
        dest = img_dir / f"{lesson['slug']}.jpg"
        if dest.exists() and src.stat().st_mtime <= dest.stat().st_mtime:
            continue
        from PIL import Image
        im = Image.open(src).convert("RGB")
        im.save(dest, "JPEG", quality=85, optimize=True)
        changed += 1
    keep_imgs = {f"{l['slug']}.jpg" for l in visible}
    for f in img_dir.glob("*.jpg"):
        if f.name not in keep_imgs:
            f.unlink()
            print("gỡ ảnh cũ:", f.name)

    # remove stale lesson dirs (e.g. reel-001/ from phase 1)
    keep_dirs = vis_slugs | {"tu-dien", "bang-lo-trinh", "thu-vien-chu-de", "luyen-noi", "api"}
    for d in list(ROOT.iterdir()):
        if d.is_dir() and (d / "index.html").exists() and d.name not in keep_dirs:
            shutil.rmtree(d)
            print("gỡ trang cũ:", d.name)
    # remove stale lo-trinh dirs (không xóa cả cây nữa, chỉ gỡ thư mục thừa)
    lt = ROOT / "lo-trinh"
    keep_lt = {p["slug"] for p in site["paths"]}
    if lt.exists():
        for d in list(lt.iterdir()):
            if d.is_dir() and d.name not in keep_lt:
                shutil.rmtree(d)
                print("gỡ lộ trình cũ:", d.name)

    # File dùng chung (tối ưu A): CSS + JS + dữ liệu + chỉ mục tìm kiếm.
    changed += write_if_changed(ROOT / "styles.css", CSS.strip() + "\n")
    changed += write_if_changed(ROOT / "app.js", js_body(SHARED_JS))
    changed += write_if_changed(ROOT / "data.js", data_js_content(visible, site["paths"]))
    changed += write_if_changed(
        ROOT / "search-index.json",
        json.dumps(build_search_index(visible, paths_for_lessons(data)), ensure_ascii=False))
    changed += write_if_changed(ROOT / "index.html", render_index(data))
    for p in site["paths"]:
        changed += write_if_changed(ROOT / "lo-trinh" / p["slug"] / "index.html",
                                    render_path(data, p))
    for i, lesson in enumerate(visible):
        prev_lesson = visible[i - 1] if i > 0 else None
        next_lesson = visible[i + 1] if i + 1 < len(visible) else None
        changed += write_if_changed(
            ROOT / lesson["slug"] / "index.html",
            render_lesson(data, lesson, prev_lesson, next_lesson))
    for slug, html in (("tu-dien", render_dict(data)),
                       ("bang-lo-trinh", render_dashboard(data)),
                       ("thu-vien-chu-de", render_library(data)),
                       ("luyen-noi", render_speak(data))):
        changed += write_if_changed(ROOT / slug / "index.html", html)
    changed += write_if_changed(ROOT / "README.md", render_readme(data))
    changed += write_if_changed(ROOT / "favicon.svg", FAVICON_SVG)
    # API mở (19/11): file JSON tĩnh dưới api/v1/ + trang tài liệu /api/.
    # Chỉ thêm file mới, không đổi đường dẫn bài học cũ.
    api_dir = ROOT / "api"
    api_v1 = api_dir / "v1"
    changed += write_if_changed(api_v1 / "meta.json",
                                json.dumps(api_meta(data), ensure_ascii=False, indent=2) + "\n")
    changed += write_if_changed(api_v1 / "lessons.json",
                                json.dumps(api_lessons_list(data), ensure_ascii=False, indent=2) + "\n")
    for l in data["lessons"]:
        changed += write_if_changed(api_v1 / "lessons" / (l["slug"] + ".json"),
                                    json.dumps(api_lesson_detail(data, l), ensure_ascii=False, indent=2) + "\n")
    # Gỡ file chi tiết của bài đã gỡ khỏi lessons.json (tránh file cũ nằm lại).
    keep_detail = {l["slug"] + ".json" for l in data["lessons"]}
    detail_dir = api_v1 / "lessons"
    if detail_dir.exists():
        for f in detail_dir.glob("*.json"):
            if f.name not in keep_detail:
                f.unlink()
                print("gỡ chi tiết API cũ:", f.name)
    changed += write_if_changed(api_v1 / "dictionary.json",
                                json.dumps(api_dictionary(data), ensure_ascii=False, indent=2) + "\n")
    changed += write_if_changed(api_v1 / "search-index.json",
                                json.dumps(api_search_index(data), ensure_ascii=False, indent=2) + "\n")
    changed += write_if_changed(api_v1 / "paths.json",
                                json.dumps(api_paths(data), ensure_ascii=False, indent=2) + "\n")
    changed += write_if_changed(api_dir / "openapi.yaml", api_openapi_yaml(data))
    changed += write_if_changed(api_dir / "index.html", render_api_docs(data))
    changed += write_sitemap_robots(data)
    print(f"OK: {len(visible)} bài học, {len(site['paths'])} lộ trình, "
          f"{len(data['lessons']) - len(visible)} reel, "
          f"{total_graded(visible)} câu luyện chấm ngay, "
          f"{len(visible)} trang bài + {len(site['paths'])} trang lộ trình + trang chủ"
          f" + 4 trang mới (từ điển, bảng lộ trình, thư viện chủ đề, luyện nói)"
          f" + API mở ({len(data['lessons'])} file chi tiết bài, từ điển {len(parse_vi_glossary())} từ)"
          f" — đổi {changed} file")


if __name__ == "__main__":
    main()
