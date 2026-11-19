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
    "user": _svg('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
    "mail": _svg('<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>'),
    "star": _svg('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'),
    "share": _svg('<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98"/>'),
    "moon": _svg('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
    "sun": _svg('<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>'),
    "flame": _svg('<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>'),
    "search": _svg('<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'),
    "bookmark": _svg('<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'),
    "headphones": _svg('<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>'),
    "pen": _svg('<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>'),
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
.wrap{max-width:1020px;margin:0 auto;padding:0 16px}
main{padding:0 0 8px}
section{margin:16px 0}
h2{font-size:22px;margin-bottom:12px}
h2 small{font-size:16px;color:var(--sub);font-weight:400}
.btn{display:inline-block;border-radius:14px;padding:16px 24px;min-height:48px;font-size:17px;font-weight:700;text-decoration:none;text-align:center;cursor:pointer;border:2px solid transparent}
.btn-primary{background:var(--orange);color:#fff}
.btn-navy{background:var(--navy-btn);color:#fff}
.btn-ghost{background:var(--card);color:var(--navy);border-color:var(--navy)}
.btn-block{display:block;width:100%}
.btn-compact{padding:12px 20px;min-height:48px}
.btn:active{transform:scale(.98)}
.review-grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(180px,1fr))}
.review-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;text-decoration:none;color:var(--ink);display:block}
.review-card:hover{border-color:var(--navy)}
.review-card b{display:block;font-size:16px;margin-bottom:2px}
.review-card span{font-size:16px;color:var(--sub)}
.empty{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:22px;text-align:center;color:var(--sub);font-size:16px}
.cta-row{display:grid;gap:12px;grid-template-columns:1fr 1fr}
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
footer{background:var(--navy-bg);color:#CBDCE8;margin-top:20px;padding:16px 20px;font-size:16px}
footer a{color:#fff;font-weight:700}

.ic{width:1.15em;height:1.15em;flex:none;vertical-align:-0.18em}
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

@media(max-width:380px){.wrap{padding:0 12px}.grid{grid-template-columns:minmax(0,1fr)}}
@media(max-width:560px){
  .viewtoggle{margin-left:0}
  .cta-row{grid-template-columns:1fr}
  .pagenav{flex-direction:column}
  .opening p{font-size:18px}
}
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
/* ---- Vỏ mới hướng A, 19/11: đầu trang gọn, nút chân trang, nhiệm vụ và XP ---- */
.appwrap{max-width:480px;margin:0 auto;padding:0 16px}
@media(min-width:768px){.appwrap{max-width:720px}}
body.has-nav{padding-bottom:96px}
.appbar{position:sticky;top:0;z-index:60;background:var(--card);border-bottom:1.5px solid var(--line)}
.appbar .appwrap{display:flex;align-items:center;gap:10px;height:56px}
.logo{width:36px;height:36px;border-radius:10px;background:var(--navy-btn);color:#fff;font-weight:900;font-size:22px;display:flex;align-items:center;justify-content:center;position:relative;flex:none}
.logo::after{content:"✓";position:absolute;right:-4px;bottom:-7px;color:var(--orange);font-size:16px}
.appname{flex:1;min-width:0;font-weight:900;font-size:18px;color:var(--navy);line-height:1.2;overflow:hidden}
.appname a{display:block;color:var(--navy);text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.appname small{display:block;font-size:16px;font-weight:400;color:var(--sub);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:480px){.appname small{display:none}}
.pills{margin-left:auto;display:flex;gap:8px;flex:none}
.pill{display:inline-flex;align-items:center;gap:5px;background:var(--bg);border:1.5px solid var(--line);border-radius:999px;padding:5px 11px;font-size:16px;font-weight:700;color:var(--navy);white-space:nowrap}
.pill .ic{width:16px;height:16px}
@media(max-width:419px){.pill-word{display:none}}
.appbar .theme-toggle{width:44px;height:44px;border:1.5px solid var(--line);background:var(--card);color:var(--navy)}
.appbar .theme-toggle .ic{width:22px;height:22px}
.hero{background:var(--navy-bg);border-radius:24px;padding:14px 16px;margin-top:14px;color:#fff}
.hero .eyebrow{color:var(--orange);font-weight:900;font-size:16px;letter-spacing:.06em}
.hero h1{font-size:22px;line-height:1.25;font-weight:900;margin:6px 0 8px;color:#fff}
.hero .wrong{color:#FFB4A8;font-size:16px}
.hero .wrong s{text-decoration-color:var(--orange);text-decoration-thickness:2px}
.hero .right{color:#DCEFEA;font-size:16px;font-weight:700;margin-top:2px}
.btn-hero{padding:12px 20px;min-height:52px}
.hero .btn{margin-top:10px}
.msub{text-align:center;color:#CBDCE8;font-size:16px;margin-top:8px}
.msub2{font-size:16px;color:var(--sub);line-height:1.5;margin:6px 0}
.tiles{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px}
.tiles .tile{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px 8px;text-align:center}
.tiles .tile .num{font-size:24px;font-weight:900;color:var(--navy);line-height:1.1}
.tiles .tile .lbl{font-size:16px;color:var(--sub);margin-top:4px}
.strip{display:block;background:var(--mint);border-radius:14px;padding:10px 14px;font-size:16px;color:var(--navy);margin-top:12px;text-decoration:none}
.strip b{font-weight:900}
.strip .go{color:var(--orange);font-weight:900;white-space:nowrap}
.strip-row{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.stripbar{display:block;height:6px;background:var(--bg);border-radius:999px;overflow:hidden;margin-top:8px}
.stripbar i{display:block;height:100%;width:0%;background:var(--orange);border-radius:999px}
.missions{background:var(--card);border:1.5px solid var(--orange);border-radius:20px;padding:14px 16px;margin-top:0}
.missions .mhead{display:flex;align-items:center;gap:8px}
.missions h2{margin:0;font-size:20px}
.xppill{margin-left:auto;display:inline-flex;align-items:center;gap:5px;background:var(--amber-bg);border:1.5px solid #F6C453;border-radius:999px;padding:5px 11px;font-size:16px;font-weight:900;color:var(--amber);white-space:nowrap}
.xpbar{height:8px;background:var(--bar);border-radius:999px;overflow:hidden;margin-top:12px}
.xpbar i{display:block;height:100%;width:0%;background:var(--orange);border-radius:999px}
.xpmeta{font-size:16px;color:var(--sub);margin-top:6px}
.mrow{display:flex;gap:12px;align-items:center;padding:10px 0;border-top:1px solid var(--bar)}
.mrow.first{margin-top:8px}
.mcheck{width:32px;height:32px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:16px}
.mcheck.done{background:var(--mint);color:var(--navy)}
.mcheck.half{background:var(--amber-bg);color:var(--amber)}
.mcheck.todo{background:var(--card);border:2px solid var(--line);color:var(--sub)}
.mrow h3{font-size:16px}
.mrow p{font-size:16px;color:var(--sub)}
.mrow .xp{margin-left:auto;font-size:16px;font-weight:900;color:var(--orange);white-space:nowrap}
.mreward{font-size:16px;color:var(--sub);margin-top:8px;background:var(--bg);border-radius:12px;padding:8px 12px}
.mreward b{color:var(--navy)}
.rows{display:grid;gap:10px}
.row{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;display:flex;gap:12px;align-items:center;text-decoration:none;color:var(--ink)}
.row .dot{width:36px;height:36px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:16px}
.dot.done{background:var(--mint);color:var(--navy)}
.dot.now{background:var(--orange);color:#fff}
.dot.next{background:var(--bar);color:var(--sub)}
.row h3{font-size:16px}
.row p{font-size:16px;color:var(--sub)}
.row .state{margin-left:auto;font-size:16px;font-weight:700;color:var(--navy);white-space:nowrap}
.row .state.done{color:var(--green)}
.bar{height:8px;background:var(--bar);border-radius:999px;overflow:hidden;margin-top:8px}
.bar i{display:block;height:100%;background:var(--orange);border-radius:999px}
.tools{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.tool{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 14px;display:flex;gap:12px;align-items:center;text-decoration:none;color:var(--ink)}
.tool .ic{width:26px;height:26px;color:var(--navy);flex:none}
.tool b{font-size:16px;display:block}
.tool span{font-size:16px;color:var(--sub)}
@media(max-width:560px){.tool span{display:none}.tool{padding:12px}}
.path{position:relative;margin-top:4px;padding-left:6px}
.path::before{content:"";position:absolute;left:27px;top:24px;bottom:24px;border-left:2px dashed var(--line)}
.pnode{display:flex;gap:14px;align-items:flex-start;padding:12px 0;position:relative}
.pdot{width:44px;height:44px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:17px;background:var(--card);border:2px solid var(--line);z-index:1}
.pdot.done{background:var(--mint);border-color:var(--mint);color:var(--navy)}
.pdot.now{background:var(--orange);border-color:var(--orange);color:#fff}
.pnode h3{font-size:16px}
.pnode p{font-size:16px;color:var(--sub)}
.pnode .go{margin-left:auto;font-size:16px;font-weight:700;color:var(--navy);white-space:nowrap}
.pathlink{display:block;text-align:center;font-size:16px;font-weight:700;color:var(--orange);margin-top:6px}
.bottomnav{position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--card);border-top:1.5px solid var(--line)}
.bottomnav .appwrap{display:flex}
.navitem{flex:1 1 0;min-width:0;min-height:56px;text-align:center;padding:8px 2px calc(8px + env(safe-area-inset-bottom,0px));font-size:16px;font-weight:700;color:var(--sub);text-decoration:none;line-height:1.2}
.navitem .ic{width:22px;height:22px;display:block;margin:0 auto 2px}
.navitem.on{color:var(--orange)}
.topbar{position:sticky;top:0;z-index:60;background:var(--card);border-bottom:1.5px solid var(--line)}
.topbar .appwrap{display:flex;align-items:center;gap:10px;height:56px}
.topbar .back{min-width:44px;min-height:44px;display:inline-flex;align-items:center;justify-content:center;font-size:20px}
.topbar .title{flex:1;min-width:0;font-weight:900;font-size:17px;color:var(--navy);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.xphint{text-align:center;font-size:16px;color:var(--amber);background:var(--amber-bg);border:1.5px solid #F6C453;border-radius:12px;padding:10px 12px;margin-top:14px}
.xphint b{color:var(--amber)}
.feat{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;margin-top:12px}
.feat img{display:block;width:100%;aspect-ratio:1/1;object-fit:cover}
.feat .body{padding:16px}
.feat .tag{margin-bottom:8px}
.feat h3{font-size:20px;margin-bottom:6px}
.feat h3 a{color:var(--ink);text-decoration:none}
.feat .msub{text-align:left;color:var(--sub);margin-top:0}
.feat .go{display:inline-block;margin-top:10px;font-size:16px;font-weight:700;color:var(--orange);text-decoration:none}
/* ---- Luyện nói v2, 19/11: 3 hàng thẻ chọn câu, chấm theo từng từ, 3 lượt mỗi buổi ---- */
.speak-intro{font-size:16px;margin:10px 0 14px}
.speak-card{background:var(--card);border:2px solid var(--navy);border-radius:16px;padding:18px 16px;margin-top:14px}
.speak-round{font-size:16px;font-weight:700;color:var(--navy)}
.speak-source{font-size:16px;color:var(--sub);margin-top:12px}
.speak-source a{font-weight:700}
.speak-target{font-size:22px;font-weight:700;line-height:1.4;margin:10px 0 6px}
.speak-vi{font-size:16px;color:var(--sub)}
.speak-colored{font-size:22px;font-weight:700;line-height:1.6;margin:10px 0 6px}
.speak-colored .w-ok{color:var(--green)}
.speak-colored .w-miss{color:var(--red);text-decoration:underline}
.speak-hidden{font-size:22px;font-weight:700;color:var(--sub);margin:10px 0 6px}
.speak-heard{font-size:16px;background:var(--bg);border-radius:12px;padding:12px 14px;margin:12px 0}
.speak-missed{margin:10px 0}
.speak-missed h3{font-size:18px;margin-bottom:8px}
.miss-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;background:var(--bg);border-radius:12px;padding:10px 12px;margin-bottom:8px}
.miss-row b{font-size:16px}
.miss-row span{font-size:16px;color:var(--sub)}
.speak-next{margin-top:12px}
.speak-topic{margin:18px 0 0}
.speak-topic h2{margin-bottom:4px}
.speak-topic .sub{font-size:16px;color:var(--sub);margin-bottom:12px}
.speak-cards{display:grid;gap:8px}
.topic-card{background:var(--card);border:1.5px solid var(--line);border-radius:16px;padding:14px;display:flex;gap:12px;align-items:center;text-align:left;cursor:pointer;width:100%;color:var(--ink);font-size:16px}
.topic-card:hover{border-color:var(--navy)}
.topic-card .ic{width:26px;height:26px;color:var(--navy);flex:none}
.topic-card h3{font-size:18px}
.topic-card p{font-size:16px;color:var(--sub)}
.topic-card .best{margin-left:auto;font-size:16px;font-weight:700;color:var(--navy);white-space:nowrap}
.speak-sentence{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;text-align:left;cursor:pointer;width:100%;color:var(--ink);font-size:16px}
.speak-sentence:hover{border-color:var(--navy)}
.speak-sentence .en{font-size:18px;font-weight:700;line-height:1.4}
.speak-sentence .vi{font-size:16px;color:var(--sub);margin-top:4px}
.speak-sentence .meta2{font-size:16px;color:var(--sub);margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.speak-sentence .lvl{background:var(--mint);color:var(--navy);border-radius:999px;padding:2px 10px;font-weight:700}
.speak-sentence .done-mark{color:var(--green);font-weight:700}
.speak-sentence .last-score{color:var(--navy);font-weight:700}
.speak-limit{font-size:16px;color:var(--sub);margin-top:18px}
/* Trang kỹ năng Nghe, Viết, Đọc (đợt hướng A, 19/11) */
.skill-intro{font-size:17px;line-height:1.5;color:var(--navy)}
.skill-modes{display:grid;gap:12px;margin:14px 0}
.skill-mode{text-align:left;background:var(--card);border:2px solid var(--line);border-radius:16px;padding:16px;cursor:pointer}
.skill-mode b{font-size:18px;display:block;margin-bottom:4px}
.skill-mode span{font-size:16px;color:var(--sub);line-height:1.4}
.skill-mode.on{border-color:var(--orange)}
.skill-card{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:18px;margin:14px 0}
.skill-card h3{font-size:19px;margin:0 0 8px}
.skill-round{font-size:16px;font-weight:800;color:var(--orange);margin:0 0 10px}
.skill-sentence{font-size:20px;font-weight:700;line-height:1.5;margin:8px 0}
.skill-vi{font-size:17px;color:var(--sub);margin:6px 0}
.skill-source{font-size:16px;color:var(--sub);margin:6px 0}
.skill-pair{display:grid;gap:10px;margin:12px 0}
.skill-pair .pair{border:2px solid var(--line);border-radius:12px;padding:12px}
.skill-pair .pair b{display:block;font-size:16px;margin-bottom:6px}
.skill-pair .pair p{font-size:18px;line-height:1.5;margin:0}
.w-diff{background:#FDE68A;border-radius:6px;padding:0 4px;font-weight:800}
.skill-choices{display:grid;gap:10px;margin:14px 0}
.skill-choices .opt{width:100%;text-align:left}
.skill-answer{width:100%;font-size:18px;padding:14px;border:2px solid var(--line);border-radius:12px;background:#fff}
.skill-feedback{margin:12px 0}
.skill-feedback .good{color:var(--green);font-weight:800}
.skill-feedback .bad{color:var(--red);font-weight:800}
.skill-progress{font-size:16px;color:var(--sub);margin:8px 0}
.skill-done{background:var(--mint);border-radius:16px;padding:18px;margin:14px 0}
.skill-done h3{font-size:20px;margin:0 0 8px}
.read-passage{font-size:18px;line-height:1.8;margin:12px 0}
.read-passage .word{cursor:pointer;border-radius:6px;padding:0 2px}
.read-passage .word:hover{background:var(--mint)}
.read-passage .word.err{color:var(--red);font-weight:800;text-decoration:underline wavy var(--red)}
.read-passage .word.fixed{color:var(--green);font-weight:800}
.read-word-pop{background:var(--card);border:2px solid var(--line);border-radius:12px;padding:12px;margin:10px 0;font-size:17px}
.read-level{font-size:16px;color:var(--sub)}
.write-wrong-list{margin:12px 0}
.write-wrong-list .miss-row{margin-bottom:8px}
/* Mục Cộng đồng (đợt hướng A, 19/11) */
.comm-card{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:14px 16px;margin:0}
.comm-card h3{font-size:19px;margin:0 0 8px}
.comm-row{display:flex;justify-content:space-between;gap:8px;padding:8px 4px;border-bottom:1px solid var(--line);font-size:17px;align-items:center}
.comm-row:last-child{border-bottom:0}
.comm-row.me{background:var(--mint);border-radius:10px;padding:10px}
.comm-row .rank{font-weight:900;min-width:24px}
.comm-row .name{flex:1;min-width:0;overflow:hidden}
.comm-who{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.comm-row .pts{font-weight:800;white-space:nowrap}
.comm-badge{display:inline-block;background:var(--orange);color:#fff;border-radius:999px;padding:2px 10px;font-size:16px;font-weight:800;margin-left:6px;white-space:nowrap}
.comm-progress{height:14px;background:var(--mint);border-radius:999px;overflow:hidden;margin:8px 0}
.comm-progress i{display:block;height:100%;background:var(--orange)}
.comm-note{font-size:16px;color:var(--sub)}
.comm-form label{display:block;font-size:16px;font-weight:700;margin:12px 0 4px}
.comm-form input{width:100%;font-size:18px;padding:12px;border:2px solid var(--line);border-radius:12px}
.comm-heart{border:2px solid var(--line);background:#fff;border-radius:999px;padding:6px 10px;font-size:16px;cursor:pointer;flex:none;white-space:nowrap}
.comm-heart.on{border-color:var(--red);color:var(--red)}
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
function emptyProgress(){return {version:1,updatedAt:new Date().toISOString(),lessons:{},practice:{},streak:{count:0,lastDate:"",dates:[]},review:{},history:[],settings:{dailyGoal:1,remindReview:true},xpTotal:0,daily:{date:todayISO(),newDone:0,reviewCount:0,bonusDone:false,skills:{}}};}
function normalizeProgress(o){
  const p=emptyProgress();
  if(o&&typeof o==="object"){
    if(o.lessons&&typeof o.lessons==="object")p.lessons=o.lessons;
    if(o.practice&&typeof o.practice==="object")p.practice=o.practice;
    if(o.review&&typeof o.review==="object")p.review=o.review;
    if(Array.isArray(o.history))p.history=o.history.slice(-500);
    if(o.streak&&typeof o.streak==="object"){p.streak.count=(typeof o.streak.count==="number"&&o.streak.count>=0)?o.streak.count:0;p.streak.lastDate=isValidDateStr(o.streak.lastDate)?o.streak.lastDate:"";p.streak.dates=Array.isArray(o.streak.dates)?o.streak.dates.filter(isValidDateStr).slice(-30):[];}
    if(o.settings&&typeof o.settings==="object"){p.settings.dailyGoal=(typeof o.settings.dailyGoal==="number"&&o.settings.dailyGoal>=1)?o.settings.dailyGoal:1;p.settings.remindReview=o.settings.remindReview!==false;}
    if(typeof o.xpTotal==="number"&&o.xpTotal>=0)p.xpTotal=o.xpTotal;
    if(o.daily&&typeof o.daily==="object"){
      const d={date:isValidDateStr(o.daily.date)?o.daily.date:"",newDone:(typeof o.daily.newDone==="number"&&o.daily.newDone>=0)?Math.floor(o.daily.newDone):0,reviewCount:(typeof o.daily.reviewCount==="number"&&o.daily.reviewCount>=0)?Math.floor(o.daily.reviewCount):0,bonusDone:!!o.daily.bonusDone,skills:{}};
      if(o.daily.skills&&typeof o.daily.skills==="object"){Object.entries(o.daily.skills).forEach(([k,v])=>{if(v===true)d.skills[k]=true;});}
      p.daily=d;
    }
  }
  if(!(o&&typeof o.xpTotal==="number"&&o.xpTotal>=0)){
    const doneCount=Object.values(p.lessons||{}).filter(L=>L&&L.done).length;
    p.xpTotal=doneCount*20;
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
/* XP, Nhiệm vụ hôm nay, phiên kỹ năng, vòng một lỗi bốn kỹ năng.
   XP: 200 XP một cấp, không khóa bài. Người học cũ gieo 20 XP mỗi bài đã nhớ
   (trong normalizeProgress). Nhiệm vụ hôm nay: học 1 bài mới 20 XP, ôn 2 bài
   đến hạn 10 XP, luyện nói 1 câu 20 XP, xong cả 3 thưởng thêm 50 XP.
   Vòng một lỗi bốn kỹ năng: mỗi bài đã nhớ có dạng kỹ năng cho lần ôn tới,
   xoay theo thứ tự nghe, viết, đọc, nói, lịch ôn 1, 3, 7, 30 ngày. */
const XP_PER_LEVEL=200;
const SKILL_ORDER=["listen","write","read","speak"];
const SKILL_LABEL={listen:"Nghe",write:"Viết",read:"Đọc",speak:"Nói"};
const SKILL_PATH={listen:"luyen-nghe/",write:"luyen-viet/",read:"luyen-doc/",speak:"luyen-noi/"};
const SKILL_DUE=[1,3,7,30];
const MISSIONS=[
  {id:"new",label:"Học 1 bài mới",xp:20,done:d=>(d.newDone||0)>=1,prog:d=>Math.min(1,(d.newDone||0))},
  {id:"review",label:"Ôn 2 bài đến hạn",xp:10,done:d=>(d.reviewCount||0)>=2,prog:d=>Math.min(1,(d.reviewCount||0)/2)},
  {id:"speak",label:"Luyện nói 1 câu",xp:20,done:d=>!!(d.skills&&d.skills.speak),prog:d=>(d.skills&&d.skills.speak)?1:0}
];
function emptyDaily(){return {date:todayISO(),newDone:0,reviewCount:0,bonusDone:false,skills:{}};}
function ensureDaily(p){if(!p.daily||p.daily.date!==todayISO())p.daily=emptyDaily();return p.daily;}
function dailyToday(p){if(p.daily&&p.daily.date===todayISO())return p.daily;return emptyDaily();}
function awardXp(p,n){p.xpTotal=Math.max(0,(typeof p.xpTotal==="number"?p.xpTotal:0)+n);return p.xpTotal;}
function xpLevel(xp){return Math.floor(Math.max(0,xp||0)/XP_PER_LEVEL)+1;}
function xpInLevel(xp){return Math.max(0,xp||0)%XP_PER_LEVEL;}
function checkDailyBonus(p){
  const d=ensureDaily(p);
  if(d.newDone>=1&&d.reviewCount>=2&&d.skills&&d.skills.speak&&!d.bonusDone){d.bonusDone=true;awardXp(p,50);return true;}
  return false;
}
function missionStatus(p){
  const d=dailyToday(p);
  return MISSIONS.map(m=>({id:m.id,label:m.label,xp:m.xp,done:!!m.done(d),prog:m.prog(d)}));
}
function countReview(p,slug,wasStudiedToday){
  const d=ensureDaily(p);
  const L=p.lessons[slug];
  if(!L||!L.done)return false;
  if(wasStudiedToday)return false;
  L.lastStudiedAt=todayISO();
  d.reviewCount=(d.reviewCount||0)+1;
  if(d.reviewCount===2)awardXp(p,10);
  checkDailyBonus(p);
  return true;
}
function markSkillDone(p,skill,xp){
  const d=ensureDaily(p);
  if(d.skills[skill])return false;
  d.skills[skill]=true;
  awardXp(p,xp);
  checkDailyBonus(p);
  return true;
}
function renderStreakPills(){
  try{const p=getProgress();const n=p.streak.count||0;document.querySelectorAll(".streak-pill").forEach(el=>{el.textContent=n+" ngày";});}catch(e){}
}
function loadSkillSession(key){
  const rec=loadJSON("sdsc-"+key+"-v1");
  const out={sessions:0,seconds:0,words:0,best:0,lastDay:"",streak:0,lastStreakDay:"",bestByTopic:{},lastBySlug:{}};
  if(rec&&typeof rec==="object"){
    if(typeof rec.sessions==="number")out.sessions=rec.sessions;
    if(typeof rec.seconds==="number")out.seconds=rec.seconds;
    else if(typeof rec.minutes==="number")out.seconds=Math.round(rec.minutes*60);
    if(typeof rec.words==="number")out.words=rec.words;
    if(typeof rec.best==="number")out.best=rec.best;
    if(typeof rec.lastDay==="string")out.lastDay=rec.lastDay;
    if(typeof rec.streak==="number")out.streak=rec.streak;
    if(typeof rec.lastStreakDay==="string")out.lastStreakDay=rec.lastStreakDay;
    if(rec.bestByTopic&&typeof rec.bestByTopic==="object")out.bestByTopic=rec.bestByTopic;
    if(rec.lastBySlug&&typeof rec.lastBySlug==="object")out.lastBySlug=rec.lastBySlug;
  }
  out.minutes=out.sessions>0?Math.max(1,Math.round(out.seconds/60)):0;
  return out;
}
function recordSkillSession(key,seconds,words,score,extra){
  const rec=loadSkillSession(key);
  const today=todayISO();
  rec.sessions=(rec.sessions||0)+1;
  rec.seconds=(rec.seconds||0)+Math.max(0,Math.round(seconds||0));
  rec.words=(rec.words||0)+Math.max(0,Math.round(words||0));
  if(typeof score==="number")rec.best=Math.max(rec.best||0,score);
  rec.lastDay=today;
  if(rec.lastStreakDay===today){}
  else if(rec.lastStreakDay===addDays(today,-1)){rec.streak=(rec.streak||0)+1;}
  else{rec.streak=1;}
  rec.lastStreakDay=today;
  if(extra&&extra.topic&&typeof score==="number"){rec.bestByTopic[extra.topic]=Math.max(rec.bestByTopic[extra.topic]||0,score);}
  if(extra&&extra.slug&&typeof score==="number"){rec.lastBySlug[extra.slug]=score;}
  rec.minutes=rec.sessions>0?Math.max(1,Math.round(rec.seconds/60)):0;
  saveJSON("sdsc-"+key+"-v1",rec);
  return rec;
}
function loadSpeaking(){return loadSkillSession("speaking");}
function recordSpeaking(seconds,words,score,topic,slug){
  const rec=recordSkillSession("speaking",seconds,words,score,{topic:topic,slug:slug});
  try{if(typeof noteSpeakingSession==="function")noteSpeakingSession(rec);}catch(e){}
  let xpAwarded=false;
  updateProgress(p=>{xpAwarded=markSkillDone(p,"speak",20);});
  return {session:rec,xpAwarded:xpAwarded};
}
function skillFor(slug){
  const p=getProgress();const r=p.review[slug];
  return (r&&r.skill&&SKILL_ORDER.indexOf(r.skill)>=0)?r.skill:"listen";
}
function skillPath(skill){return SKILL_PATH[skill]||SKILL_PATH.speak;}
function completeSkillReview(slug,skill){
  const p=getProgress();const today=todayISO();
  const r=p.review[slug]||srsNew(today);
  const cur=(r.skill&&SKILL_ORDER.indexOf(r.skill)>=0)?r.skill:"listen";
  if(cur!==skill)return {advanced:false,skill:cur,nextDue:r.nextDue||null};
  const step=(typeof r.skillStep==="number"?r.skillStep:0);
  const nextStep=step+1;
  r.skillStep=nextStep;
  r.skill=SKILL_ORDER[nextStep%SKILL_ORDER.length];
  r.nextDue=addDays(today,SKILL_DUE[Math.min(nextStep%SKILL_ORDER.length,3)]);
  r.reps=(r.reps||0)+1;
  p.review[slug]=r;
  const L=p.lessons[slug];
  const wasStudiedToday=!!(L&&L.lastStudiedAt===today);
  if(L){L.reviews=(L.reviews||0)+1;}
  const counted=countReview(p,slug,wasStudiedToday);
  pushHistory(p,{date:today,at:new Date().toISOString(),slug:slug,action:"review",skill:skill});
  saveProgress(p);
  return {advanced:true,skill:r.skill,nextDue:r.nextDue,counted:counted};
}
try{renderStreakPills();}catch(e){}
/* Căn chỉnh từng từ: so bản nghe được hoặc bản gõ với câu mẫu, theo thứ tự,
   nhìn trước tối đa 2 từ để nhận từ thừa. Trả về marks (ok/miss theo từng từ
   của câu mẫu), pct, missed (từ thiếu hoặc sai), extra (từ thừa). */
function sdscTokenize(s){return String(s||"").toLowerCase().replace(/[^a-z0-9'\s]/g," ").split(/\s+/).filter(Boolean);}
function sdscAlignWords(target,heard){
  const t=sdscTokenize(target), h=sdscTokenize(heard);
  const marks=[];let j=0;const missed=[];const extra=[];let correct=0;
  for(let i=0;i<t.length;i++){
    if(j<h.length&&h[j]===t[i]){marks.push("ok");j++;correct++;}
    else if(j+1<h.length&&h[j+1]===t[i]){extra.push(h[j]);marks.push("ok");j+=2;correct++;}
    else if(j+2<h.length&&h[j+2]===t[i]){extra.push(h[j]);extra.push(h[j+1]);marks.push("ok");j+=3;correct++;}
    else{marks.push("miss");missed.push(t[i]);}
  }
  for(let k=j;k<h.length;k++)extra.push(h[k]);
  const pct=t.length?Math.round(100*correct/t.length):0;
  return {marks:marks,pct:pct,missed:missed,extra:extra,target:t,heard:h};
}
function sdscColoredSentence(target,marks){
  const parts=String(target||"").split(/(\s+)/);
  let wi=0;let html="";
  parts.forEach(part=>{
    if(!/[A-Za-z]/.test(part)){html+=escapeHtml(part);return;}
    const cls=marks[wi]==="ok"?"w-ok":(marks[wi]==="miss"?"w-miss":"");
    html+="<span class=\""+cls+"\">"+escapeHtml(part)+"</span>";
    wi++;
  });
  return html;
}
/* So sánh 2 câu theo từng từ (LCS), trả HTML 2 câu với từ khác nhau
   được bọc span.w-diff. Dùng cho trang Nghe (hiện 2 câu cạnh nhau). */
function sdscWordTokens(s){
  return String(s||"").split(/\s+/).filter(Boolean).map(function(w){
    return {text:w,norm:w.toLowerCase().replace(/[^a-z0-9']/g,"")};
  }).filter(function(t){return t.norm;});
}
function sdscDiffHtml(a,b){
  const ta=sdscWordTokens(a), tb=sdscWordTokens(b);
  const n=ta.length, m=tb.length;
  const dp=[];
  for(let i=0;i<=n;i++){dp.push(new Array(m+1).fill(0));}
  for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--){dp[i][j]=ta[i].norm===tb[j].norm?dp[i+1][j+1]+1:Math.max(dp[i+1][j],dp[i][j+1]);}
  const aOut=[], bOut=[];
  let i=0,j=0;
  while(i<n&&j<m){
    if(ta[i].norm===tb[j].norm){aOut.push({t:ta[i].text,same:true});bOut.push({t:tb[j].text,same:true});i++;j++;}
    else if(dp[i+1][j]>=dp[i][j+1]){aOut.push({t:ta[i].text,same:false});i++;}
    else{bOut.push({t:tb[j].text,same:false});j++;}
  }
  while(i<n){aOut.push({t:ta[i].text,same:false});i++;}
  while(j<m){bOut.push({t:tb[j].text,same:false});j++;}
  const wrap=function(parts){return parts.map(function(p){return p.same?escapeHtml(p.t):"<span class=\"w-diff\">"+escapeHtml(p.t)+"</span>";}).join(" ");};
  return {aHtml:wrap(aOut),bHtml:wrap(bOut)};
}
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
  if(data.xpTotal!==undefined&&(typeof data.xpTotal!=="number"||data.xpTotal<0))return {ok:false,error:"Trường 'xpTotal' phải là số ≥ 0."};
  if(data.daily!==undefined&&(!data.daily||typeof data.daily!=="object"||Array.isArray(data.daily)))return {ok:false,error:"Trường 'daily' phải là object."};
  if(data.daily&&data.daily.date!==undefined&&data.daily.date!==""&&!isValidDateStr(data.daily.date))return {ok:false,error:"Trường 'daily.date' không phải ngày hợp lệ."};
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
  out.xpTotal=Math.max(out.xpTotal||0,incoming.xpTotal||0);
  const dOut=out.daily||{}, dInc=incoming.daily||{};
  if(dInc.date&&dInc.date===todayISO()){
    if(dOut.date===todayISO()){
      out.daily={date:todayISO(),newDone:Math.max(dOut.newDone||0,dInc.newDone||0),reviewCount:Math.max(dOut.reviewCount||0,dInc.reviewCount||0),bonusDone:!!(dOut.bonusDone||dInc.bonusDone),skills:Object.assign({},dOut.skills||{},dInc.skills||{})};
    }else{out.daily=JSON.parse(JSON.stringify(dInc));}
  }
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
function speakingHoursText(mins){
  mins=Math.round(mins||0);
  if(mins<60)return mins+" phút";
  const h=Math.floor(mins/60);const m=mins%60;
  return h+" giờ"+(m?" "+m+" phút":"");
}
/* Danh sách và thống kê tiến độ (dùng chung trang chủ và trang Tôi).
   Trước đây nằm ở khối JS riêng của trang chủ, chuyển về đây để trang
   Tôi cũng vẽ được mà không nhân đôi code. */
const SDSC_SITE_ROOT="/sai-dau-sua-do";
function progressDoneCount(){
  const p=getProgress();
  return Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).length;
}
function renderDoneList(){
  const p=getProgress();
  const box=document.getElementById("done-list");
  if(!box)return;
  const items=Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).sort((a,b)=>String(b[1].lastStudiedAt||b[1].doneAt||"").localeCompare(String(a[1].lastStudiedAt||a[1].doneAt||""))).slice(0,10);
  if(!items.length){box.innerHTML="<p>Chưa có bài nào đã nhớ. Học bài đầu tiên ở khung “Bài hôm nay” nhé.</p>";return;}
  box.innerHTML="<ul>"+items.map(([s,l])=>{const m=window.SDSC_LESSONS[s];return "<li><a href=\""+SDSC_SITE_ROOT+"/"+s+"/\">"+escapeHtml(m.code)+": "+escapeHtml(m.title)+"</a>, đã nhớ ngày "+escapeHtml(fmtDate(l.doneAt||l.lastStudiedAt||""))+"</li>";}).join("")+"</ul>";
}
function renderRecent(){
  const p=getProgress();
  const box=document.getElementById("recent-list");
  if(!box)return;
  const evs=(p.history||[]).filter(h=>h&&h.slug&&window.SDSC_LESSONS[h.slug]).slice(-5).reverse();
  if(!evs.length){box.innerHTML="<p>Chưa có hoạt động nào. Làm thử 1 câu luyện ở bất kỳ bài nào nhé.</p>";return;}
  const label={done:"Đã nhớ bài",undone:"Bỏ đánh dấu bài",practice:"Luyện câu ở bài",review:"Ôn lại bài","self-grade":"Tự đánh giá bài",import:"Nhập tiến độ",reset:"Đặt lại tiến độ"};
  box.innerHTML="<ul>"+evs.map(h=>{const m=window.SDSC_LESSONS[h.slug];const extra=h.action==="practice"?(h.correct?", đúng":", chưa đúng"):(h.grade?", mức "+({kho:"Khó",vua:"Vừa",de:"Dễ"}[h.grade]||h.grade):(h.skill?", bằng "+(SKILL_LABEL[h.skill]||h.skill):""));return "<li>"+escapeHtml(label[h.action]||h.action)+" <a href=\""+SDSC_SITE_ROOT+"/"+h.slug+"/\">"+escapeHtml(m.code)+"</a>"+extra+" ("+escapeHtml(fmtDate(h.date||""))+ ")"+"</li>";}).join("")+"</ul>";
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
  const xp=typeof p.xpTotal==="number"?p.xpTotal:0;
  box.innerHTML="<ul><li>Điểm kinh nghiệm: <b>"+xp+" XP (Cấp "+xpLevel(xp)+")</b></li><li>Bài đã nhớ: <b>"+done+" / "+window.SDSC_TOTAL_LESSONS+"</b></li><li>Tỉ lệ luyện đúng: <b>"+acc+"%</b> ("+prac.filter(v=>v&&v.correct).length+" / "+prac.length+" câu)</li><li>Số lần ôn lại: <b>"+reviews+"</b></li><li>Chuỗi ngày học dài nhất: <b>"+longestStreak(p.streak.dates||[])+" ngày</b> (chuỗi hiện tại: "+(p.streak.count||0)+" ngày)</li><li>Ngày học gần nhất: <b>"+escapeHtml(last)+"</b></li></ul>";
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
    reader.onload=()=>{const res=importProgressText(String(reader.result||""),mode);if(res.ok){showMsg(res.message,true);if(typeof window.__sdscRenderProgress==="function"){try{window.__sdscRenderProgress();}catch(e){}} if(typeof renderDashboard==="function"){try{renderDashboard();}catch(e){}}}else{showMsg(res.error,false);}file.value="";};
    reader.onerror=()=>{showMsg("Không đọc được file, thử lại nhé.",false);file.value="";};
    reader.readAsText(f);
  });}
}
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
  async function fallbackViOnly(word){
    const gg=glossaryHit(word);
    if(gg){renderViOnly(word,viSensesFromGlossary(gg),"Trang soạn");return true;}
    const wk=await fetchWiki(word);
    if(wk&&wk.length){renderViOnly(word,wk,"Wiktionary tiếng Việt");return true;}
    return false;
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
    const ctrl=new AbortController();
    const timer=setTimeout(function(){ctrl.abort();},8000);
    fetch("https://api.dictionaryapi.dev/api/v2/entries/en/"+encodeURIComponent(word),{signal:ctrl.signal})
      .then(r=>{
        if(r.status===429||r.status>=500)throw new Error("transient");
        if(!r.ok)throw new Error("notfound");
        return r.json();
      })
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
          if(await fallbackViOnly(word))return;
          if(box)box.innerHTML="<p class=\"note warn\">Không tìm thấy từ <b>"+escapeHtml(word)+"</b> trong từ điển. Kiểm tra chính tả rồi thử lại, hoặc thử từ khác.</p>";
        }else{
          if(await fallbackViOnly(word))return;
          if(box)box.innerHTML="<p class=\"note warn\">Không tải được từ điển lúc này. Kiểm tra mạng rồi thử lại nhé.</p>";
        }
      })
      .finally(function(){clearTimeout(timer);});
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
  try{renderDoneList();}catch(e){}
  try{renderRecent();}catch(e){}
  try{renderStats();}catch(e){}
  try{renderExportUI();}catch(e){}
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
  const speakable=window.SDSC_SPEAKABLE||[];
  const weak=window.SDSC_WEAK||[];
  const viMap=window.SDSC_SPEAK_VI||{};
  const TOPIC_LABEL={"giao tiếp":"Giao tiếp","ngữ pháp":"Ngữ pháp","từ vựng":"Từ vựng","công sở":"Công sở","quiz tổng hợp":"Quiz tổng hợp","phát âm":"Phát âm"};
  const TOPIC_ORDER=["giao tiếp","ngữ pháp","từ vựng","công sở","quiz tổng hợp"];
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  const ERR_TEXT={"no-speech":"Máy không nghe thấy gì. Thử lại nhé.","audio-capture":"Không mở được micro. Thử lại nhé.","not-allowed":"Trình duyệt chưa cho phép dùng micro. Bấm cho phép micro rồi thử lại nhé.","network":"Mất mạng lúc nhận diện giọng nói. Kiểm tra mạng rồi thử lại nhé.","aborted":"Đã dừng nghe.","language-not-supported":"Trình duyệt này chưa hỗ trợ nhận diện tiếng Anh."};
  const todayBox=document.getElementById("speak-today");
  const topicsBox=document.getElementById("speak-topics");
  const topicListBox=document.getElementById("speak-topic-list");
  const weakBox=document.getElementById("speak-weak");
  const card=document.getElementById("speak-card");
  const roundEl=document.getElementById("speak-round");
  const targetEl=document.getElementById("speak-target");
  const viEl=document.getElementById("speak-vi");
  const sourceEl=document.getElementById("speak-source");
  const listenBtn=document.getElementById("speak-listen");
  const startBtn=document.getElementById("speak-start");
  const stopBtn=document.getElementById("speak-stop");
  const replayBtn=document.getElementById("speak-replay");
  const statusEl=document.getElementById("speak-status");
  const heardBox=document.getElementById("speak-heard");
  const coloredBox=document.getElementById("speak-colored");
  const scoreBox=document.getElementById("speak-score");
  const missedBox=document.getElementById("speak-missed");
  const nextBtn=document.getElementById("speak-next");
  const doneBox=document.getElementById("speak-done");
  const newBtn=document.getElementById("speak-new");
  const statsEl=document.getElementById("speak-stats");
  const noSupport=document.getElementById("speak-nosupport");
  const randomBtn=document.getElementById("speak-random");
  let cur=null, round=1, scores=[], sessionStart=null, sessionWords=0, rec=null, finalText="", mediaRecorder=null, audioChunks=[], audioUrl=null, recordingStream=null;
  function withPeriod(s){
    s=String(s||"").trim();
    if(!s)return s;
    if(/[.!?]$/.test(s))return s;
    return s+".";
  }
  function speakableBySlug(slug){return speakable.find(function(s){return s.slug===slug;});}
  function lessonOrder(){
    const order=[];
    const path=(window.SDSC_PATHS&&window.SDSC_PATHS["hoc-lai-tu-dau"])||[];
    path.forEach(function(s){if(order.indexOf(s)<0)order.push(s);});
    (window.SDSC_ORDER||[]).forEach(function(s){if(order.indexOf(s)<0)order.push(s);});
    Object.keys(window.SDSC_LESSONS||{}).forEach(function(s){if(order.indexOf(s)<0)order.push(s);});
    return order;
  }
  function sentenceCard(s){
    const p=getProgress();
    const done=p.lessons[s.slug]&&p.lessons[s.slug].done;
    const sp=loadSpeaking();
    const last=sp.lastBySlug[s.slug];
    const lvl=s.level==="Ngắn"?"Ngắn":"Vừa";
    return "<button type=\"button\" class=\"speak-sentence\" data-slug=\""+escapeHtml(s.slug)+"\">"
      +"<span class=\"en\">"+escapeHtml(withPeriod(s.en))+"</span>"
      +"<span class=\"vi\">"+escapeHtml(s.vi||"")+"</span>"
      +"<span class=\"meta2\"><span class=\"lvl\">"+lvl+"</span><span>"+escapeHtml(s.code+" "+s.title)+"</span>"
      +(done?"<span class=\"done-mark\">✓ Đã nhớ</span>":"")
      +"<span>"+(typeof last==="number"?"Điểm lần trước: "+last:"Chưa luyện")+"</span></span></button>";
  }
  function bindSentenceCards(box){
    if(!box)return;
    box.querySelectorAll(".speak-sentence").forEach(function(btn){
      btn.addEventListener("click",function(){
        const s=speakableBySlug(btn.dataset.slug);
        if(s)startSession(s);
      });
    });
  }
  function renderToday(){
    if(!todayBox)return;
    const p=getProgress();
    const order=lessonOrder();
    const picked=[];
    order.forEach(function(slug){
      if(picked.length>=3)return;
      if(p.lessons[slug]&&p.lessons[slug].done)return;
      const s=speakableBySlug(slug);
      if(s)picked.push(s);
    });
    if(picked.length<3){
      const newest=Object.keys(window.SDSC_LESSONS||{}).sort(function(a,b){return String((window.SDSC_LESSONS[b]||{}).date||"").localeCompare(String((window.SDSC_LESSONS[a]||{}).date||""));});
      newest.forEach(function(slug){
        if(picked.length>=3)return;
        if(picked.some(function(s){return s.slug===slug;}))return;
        const s=speakableBySlug(slug);
        if(s)picked.push(s);
      });
    }
    if(!picked.length){todayBox.innerHTML="<p>Chưa có câu nào để luyện.</p>";return;}
    todayBox.innerHTML=picked.map(sentenceCard).join("");
    bindSentenceCards(todayBox);
  }
  function renderTopics(){
    if(!topicsBox)return;
    const sp=loadSpeaking();
    topicsBox.innerHTML=TOPIC_ORDER.map(function(t){
      const n=speakable.filter(function(s){return s.topic===t;}).length;
      const best=sp.bestByTopic[t];
      return "<button type=\"button\" class=\"topic-card\" data-topic=\""+escapeHtml(t)+"\">"
        +"<b>"+escapeHtml(TOPIC_LABEL[t]||t)+"</b>"
        +"<span class=\"sub\">"+n+" câu</span>"
        +"<span class=\"sub\">"+(typeof best==="number"?"Điểm tốt nhất: "+best:"Chưa luyện")+"</span></button>";
    }).join("");
    topicsBox.querySelectorAll(".topic-card").forEach(function(btn){
      btn.addEventListener("click",function(){renderTopicList(btn.dataset.topic);});
    });
  }
  function renderTopicList(topic){
    if(!topicListBox)return;
    const list=speakable.filter(function(s){return s.topic===topic;});
    topicListBox.style.display="block";
    topicListBox.innerHTML="<h3>"+escapeHtml(TOPIC_LABEL[topic]||topic)+" ("+list.length+" câu)</h3>"+(list.length?list.map(sentenceCard).join(""):"<p>Chưa có câu nào ở chủ đề này.</p>");
    bindSentenceCards(topicListBox);
    topicListBox.scrollIntoView({block:"nearest"});
  }
  function renderWeak(){
    if(!weakBox)return;
    if(!weak.length){weakBox.innerHTML="<p>Chưa có từ yếu nào. Luyện vài buổi rồi quay lại nhé.</p>";return;}
    weakBox.innerHTML=weak.map(function(w){
      const s=w.sentence;
      return "<button type=\"button\" class=\"speak-sentence\" data-slug=\""+escapeHtml(s.slug)+"\">"
        +"<span class=\"en\">"+escapeHtml(w.word)+(w.vi?" <span class=\"vi\">"+escapeHtml(w.vi)+"</span>":"")+"</span>"
        +"<span class=\"vi\">"+escapeHtml(withPeriod(s.en))+"</span>"
        +"<span class=\"meta2\"><span>"+escapeHtml(s.code+" "+s.title)+"</span></span></button>";
    }).join("");
    bindSentenceCards(weakBox);
  }
  function showStats(){
    if(!statsEl)return;
    const sp=loadSpeaking();
    statsEl.textContent="Bạn đã luyện nói "+(sp.sessions||0)+" buổi, tổng "+speakingHoursText(sp.minutes||0)+", điểm tốt nhất "+(sp.best||0)+" điểm, chuỗi luyện nói "+(sp.streak||0)+" ngày.";
  }
  function renderRound(){
    if(!cur)return;
    if(roundEl)roundEl.textContent="Lượt "+round+" trên 3: "+(round===1?"nghe rồi nói lại chậm":round===2?"nói lại tốc độ tự nhiên":"ẩn câu mẫu, nói lại theo trí nhớ");
    if(targetEl){
      targetEl.textContent=withPeriod(cur.en);
      if(round===3){targetEl.classList.add("speak-hidden");targetEl.textContent="Nói lại theo trí nhớ nhé, dịch ở dưới là gợi ý.";}
      else targetEl.classList.remove("speak-hidden");
    }
    if(viEl)viEl.textContent=cur.vi||"";
    if(sourceEl)sourceEl.innerHTML="Từ bài <a href=\""+BASE_PATH_PLACEHOLDER+"/bai/"+encodeURIComponent(cur.slug)+"/\">"+escapeHtml(cur.code+" "+cur.title)+"</a>";
    if(listenBtn)listenBtn.dataset.say=cur.en;
    if(heardBox)heardBox.innerHTML="";
    if(coloredBox)coloredBox.innerHTML="";
    if(scoreBox)scoreBox.innerHTML="";
    if(missedBox)missedBox.innerHTML="";
    if(nextBtn)nextBtn.style.display="none";
    if(doneBox)doneBox.style.display="none";
    if(statusEl)statusEl.textContent=round===1?"Nghe câu mẫu rồi bấm Bắt đầu nói nhé.":round===2?"Nói lại lần nữa, tốc độ tự nhiên nhé.":"Lần này không nhìn câu mẫu nữa, nói theo trí nhớ nhé.";
    if(replayBtn)replayBtn.style.display="none";
  }
  function startSession(s){
    cur=s;round=1;scores=[];sessionWords=0;sessionStart=Date.now();
    try{if(audioUrl){URL.revokeObjectURL(audioUrl);audioUrl=null;}}catch(e){}
    if(card)card.style.display="block";
    renderRound();
    if(card)card.scrollIntoView({block:"nearest"});
    if(startBtn)startBtn.disabled=!SR;
  }
  function startRecording(){
    if(!window.MediaRecorder||!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia)return;
    navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){
      recordingStream=stream;audioChunks=[];
      try{mediaRecorder=new MediaRecorder(stream);}catch(e){return;}
      mediaRecorder.ondataavailable=function(e){if(e.data&&e.data.size)audioChunks.push(e.data);};
      mediaRecorder.onstop=function(){
        try{if(audioUrl)URL.revokeObjectURL(audioUrl);}catch(e){}
        try{audioUrl=URL.createObjectURL(new Blob(audioChunks,{type:(mediaRecorder&&mediaRecorder.mimeType)||"audio/webm"}));}catch(e){audioUrl=null;}
        if(audioUrl&&replayBtn)replayBtn.style.display="";
      };
      try{mediaRecorder.start();}catch(e){}
    }).catch(function(){});
  }
  function stopRecording(){
    try{if(mediaRecorder&&mediaRecorder.state!=="inactive")mediaRecorder.stop();}catch(e){}
    try{if(recordingStream)recordingStream.getTracks().forEach(function(t){t.stop();});}catch(e){}
    mediaRecorder=null;recordingStream=null;
  }
  function finishRound(heard){
    const r=sdscAlignWords(cur.en,heard);
    scores.push(r.pct);
    sessionWords+=sdscTokenize(heard).length;
    if(coloredBox)coloredBox.innerHTML=sdscColoredSentence(cur.en,r.marks);
    if(heardBox)heardBox.innerHTML="Máy nghe được: <b>"+escapeHtml(heard)+"</b>";
    let band="", cls="mid";
    if(r.pct>=90){band="Gần như chuẩn rồi. Giỏi quá!";cls="good";}
    else if(r.pct>=70){band="Khá lắm, còn vài từ chưa rõ. Nghe lại câu mẫu rồi nói lại nhé.";cls="mid";}
    else if(r.pct>=50){band="Máy nghe được một nửa. Đọc chậm lại, nhấn rõ từng từ nhé.";cls="mid";}
    else{band="Máy chưa nghe rõ. Thử lại nhé, nói chậm và gần micro hơn.";cls="low";}
    if(scoreBox)scoreBox.innerHTML="<p class=\"speak-score "+cls+"\">"+r.pct+" điểm</p><p>"+band+"</p>";
    if(missedBox){
      if(r.missed.length){
        missedBox.innerHTML="<p>Từ chưa đúng:</p>"+r.missed.map(function(w){
          const v=viMap[String(w).toLowerCase()]||"";
          return "<div class=\"miss-row\"><span><b>"+escapeHtml(w)+"</b>"+(v?" <span class=\"vi\">"+escapeHtml(v)+"</span>":"")+"</span><button type=\"button\" class=\"btn btn-ghost btn-listen-word\" data-say=\""+escapeHtml(w)+"\">Nghe</button></div>";
        }).join("");
        missedBox.querySelectorAll(".btn-listen-word").forEach(function(b){
          b.addEventListener("click",function(){speak(b.dataset.say,b);});
        });
      }else{
        missedBox.innerHTML="<p>Nói đúng hết mọi từ. Tuyệt vời!</p>";
      }
    }
    if(statusEl)statusEl.textContent=round<3?"Xong lượt "+round+". Bấm Lượt tiếp theo để nói tiếp nhé.":"Xong lượt 3, buổi luyện nói đã xong.";
    if(round<3){if(nextBtn)nextBtn.style.display="";}
    else finishSession();
  }
  function finishSession(){
    const avg=scores.length?Math.round(scores.reduce(function(a,b){return a+b;},0)/scores.length):0;
    const seconds=sessionStart?Math.max(60,Math.round((Date.now()-sessionStart)/1000)):60;
    const res=recordSpeaking(seconds,sessionWords,avg,cur.topic,cur.slug);
    let adv=false;
    try{adv=completeSkillReview(cur.slug,"speak");}catch(e){}
    showStats();
    if(doneBox){
      doneBox.style.display="block";
      doneBox.innerHTML="<h3>Xong buổi luyện nói</h3><p>Điểm trung bình 3 lượt: <b>"+avg+" điểm</b>.</p>"
        +(res.xpAwarded?"<p>Nhận <b>+20 XP</b>, đã cộng vào Nhiệm vụ hôm nay.</p>":"<p>Hôm nay đã nhận 20 XP luyện nói rồi.</p>")
        +(adv?"<p>Bài này đã ôn xong bằng Nói, lần ôn tới đổi sang kỹ năng khác.</p>":"")
        +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"speak-again\">Luyện câu khác</button></p>";
      const again=document.getElementById("speak-again");
      if(again)again.addEventListener("click",function(){
        if(card)card.style.display="none";
        const t=document.getElementById("speak-today");
        if(t)t.scrollIntoView({block:"nearest"});
      });
    }
  }
  if(listenBtn)listenBtn.addEventListener("click",function(){if(cur)speak(cur.en,listenBtn);});
  if(replayBtn)replayBtn.addEventListener("click",function(){
    if(!audioUrl)return;
    try{new Audio(audioUrl).play();}catch(e){}
  });
  if(nextBtn)nextBtn.addEventListener("click",function(){
    if(round<3){round++;renderRound();}
  });
  if(newBtn)newBtn.addEventListener("click",function(){
    if(card)card.style.display="none";
    const t=document.getElementById("speak-today");
    if(t)t.scrollIntoView({block:"nearest"});
  });
  if(randomBtn)randomBtn.addEventListener("click",function(){
    if(!speakable.length)return;
    const s=speakable[Math.floor(Math.random()*speakable.length)];
    startSession(s);
  });
  if(!SR){
    if(noSupport)noSupport.style.display="block";
    if(startBtn)startBtn.disabled=true;
    if(statusEl)statusEl.textContent="Trình duyệt này chưa hỗ trợ nhận diện giọng nói. Dùng Chrome hoặc Edge để luyện nói nhé.";
  }else if(startBtn){
    startBtn.addEventListener("click",function(){
      if(!cur)return;
      try{rec=new SR();}catch(e){if(statusEl)statusEl.textContent="Không mở được micro, thử lại nhé.";return;}
      rec.lang="en-US";rec.interimResults=true;rec.continuous=false;rec.maxAlternatives=1;
      finalText="";
      startRecording();
      if(statusEl)statusEl.innerHTML="<span class=\"rec-dot\"></span>Đang nghe… nói câu trên nhé.";
      if(startBtn)startBtn.disabled=true;
      if(stopBtn)stopBtn.disabled=false;
      rec.onresult=function(e){
        let interim="",fin="";
        for(let i=e.resultIndex;i<e.results.length;i++){
          if(e.results[i].isFinal)fin+=e.results[i][0].transcript;
          else interim+=e.results[i][0].transcript;
        }
        if(fin)finalText+=fin;
        if(heardBox)heardBox.textContent="Máy đang nghe: "+(finalText+interim);
      };
      rec.onerror=function(e){
        stopRecording();
        if(statusEl)statusEl.textContent=ERR_TEXT[(e&&e.error)||""]||"Máy chưa nghe được. Thử lại nhé, nói rõ và gần micro hơn.";
        if(startBtn)startBtn.disabled=false;
        if(stopBtn)stopBtn.disabled=true;
      };
      rec.onend=function(){
        stopRecording();
        if(startBtn)startBtn.disabled=false;
        if(stopBtn)stopBtn.disabled=true;
        const heard=(finalText||"").trim();
        if(!heard){if(statusEl)statusEl.textContent="Máy không nghe thấy gì. Thử lại nhé.";return;}
        finishRound(heard);
      };
      try{rec.start();}catch(e){stopRecording();if(statusEl)statusEl.textContent="Không mở được micro, thử lại nhé.";if(startBtn)startBtn.disabled=false;if(stopBtn)stopBtn.disabled=true;}
    });
  }
  if(stopBtn)stopBtn.addEventListener("click",function(){try{if(rec)rec.stop();}catch(e){}});
  renderToday();renderTopics();renderWeak();showStats();
  try{
    const q=new URLSearchParams(location.search);
    const lesson=q.get("lesson");
    const sParam=q.get("s");
    if(lesson){
      const s=speakableBySlug(lesson);
      if(s)startSession(s);
      else if(window.SDSC_LESSONS&&window.SDSC_LESSONS[lesson]){
        const l=window.SDSC_LESSONS[lesson];
        startSession({en:l.right||"",vi:l.right_note||"",code:l.code||"",slug:lesson,topic:l.topic||"",title:l.title||"",words:sdscTokenize(l.right||"").length,level:"Vừa"});
      }
    }else if(sParam){
      const old=(window.SDSC_SPEAK||[]).find(function(x){return x.en===sParam;});
      const s=old?{en:old.en,vi:old.vi||"",code:old.code||"",slug:old.slug||"",topic:old.topic||"",title:old.title||"",words:sdscTokenize(old.en).length,level:"Vừa"}:null;
      if(s)startSession(s);
    }
  }catch(e){}
  window.__speakTest={
    startSession:startSession,
    completeRound:function(transcript){if(!cur)return null;finishRound(String(transcript||""));return {round:round,scores:scores.slice()};},
    state:function(){return {round:round,scores:scores.slice(),sentence:cur?cur.en:null};},
    speakable:speakable
  };
})();
</script>
"""



LISTEN_JS = r"""
<script>
(function(){
  const skills=window.SDSC_SKILLS||{};
  const pairs=[];
  Object.keys(skills).forEach(function(slug){
    const l=skills[slug];
    const ms=(l.mistakes||[]).filter(function(m){return m.wrong&&m.right;});
    if(ms.length){
      ms.forEach(function(m){pairs.push({wrong:m.wrong,right:m.right,code:l.code,title:l.title,slug:slug,topic:l.topic||"",why:l.why||"",right_note:l.right_note||""});});
    }else if(l.wrong&&l.right){
      pairs.push({wrong:l.wrong,right:l.right,code:l.code,title:l.title,slug:slug,topic:l.topic||"",why:l.why||"",right_note:l.right_note||""});
    }
  });
  const modes=["pick","choose","type"];
  const MODE_LABEL={pick:"Nghe 1 câu, chọn Sai hay Đúng",choose:"Nghe 2 câu, chọn câu nào đúng",type:"Nghe câu sai, gõ lại thành câu đúng"};
  const card=document.getElementById("listen-card");
  const roundEl=document.getElementById("listen-round");
  const promptEl=document.getElementById("listen-prompt");
  const playBox=document.getElementById("listen-play");
  const choiceBox=document.getElementById("listen-choices");
  const typeBox=document.getElementById("listen-type");
  const typeInput=document.getElementById("listen-input");
  const typeBtn=document.getElementById("listen-check");
  const feedbackEl=document.getElementById("listen-feedback");
  const nextBtn=document.getElementById("listen-next");
  const doneBox=document.getElementById("listen-done");
  const statsEl=document.getElementById("listen-stats");
  const startBox=document.getElementById("listen-start");
  const progressEl=document.getElementById("listen-progress");
  let session=[], idx=0, scores=[], sessionStart=null, sessionWords=0, lessonSlug=null, played=null;
  function shuffle(a){
    for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));const t=a[i];a[i]=a[j];a[j]=t;}
    return a;
  }
  function showStats(){
    if(!statsEl)return;
    const sp=loadSkillSession("listening");
    statsEl.textContent="Bạn đã luyện nghe "+(sp.sessions||0)+" buổi, tổng "+speakingHoursText(sp.minutes||0)+", điểm tốt nhất "+(sp.best||0)+" điểm, chuỗi luyện nghe "+(sp.streak||0)+" ngày.";
  }
  function pairHtml(p){
    const d=sdscDiffHtml(p.wrong,p.right);
    return "<div class=\"skill-pair\"><div class=\"pair\"><b>Câu sai</b><p>"+d.aHtml+"</p></div>"
      +"<div class=\"pair\"><b>Câu đúng</b><p>"+d.bHtml+"</p></div></div>"
      +(p.why?"<p>"+escapeHtml(p.why)+"</p>":"");
  }
  function startSession(){
    let pool=pairs.slice();
    if(lessonSlug)pool=pool.filter(function(p){return p.slug===lessonSlug;});
    if(!pool.length)pool=pairs.slice();
    shuffle(pool);
    session=[];
    for(let r=0;r<6;r++){
      session.push({pair:pool[r%pool.length],mode:modes[r%3]});
    }
    idx=0;scores=[];sessionWords=0;sessionStart=Date.now();
    if(startBox)startBox.style.display="none";
    if(card)card.style.display="block";
    if(doneBox)doneBox.style.display="none";
    renderRound();
  }
  function renderRound(){
    const cur=session[idx];
    if(!cur)return;
    played=null;
    if(roundEl)roundEl.textContent="Câu "+(idx+1)+" trên "+session.length+": "+MODE_LABEL[cur.mode];
    if(progressEl)progressEl.textContent="Buổi luyện nghe: "+(idx+1)+" trên "+session.length+" câu.";
    if(promptEl)promptEl.innerHTML="Từ bài <a href=\""+BASE_PATH_PLACEHOLDER+"/bai/"+encodeURIComponent(cur.pair.slug)+"/\">"+escapeHtml(cur.pair.code+" "+cur.pair.title)+"</a>";
    if(feedbackEl)feedbackEl.innerHTML="";
    if(nextBtn)nextBtn.style.display="none";
    if(typeBox)typeBox.style.display="none";
    if(choiceBox)choiceBox.innerHTML="";
    if(playBox)playBox.innerHTML="";
    sessionWords+=sdscTokenize(cur.pair.right).length;
    if(cur.mode==="pick"){
      const isRight=Math.random()<0.5;
      const spoken=isRight?cur.pair.right:cur.pair.wrong;
      if(playBox)playBox.innerHTML="<button type=\"button\" class=\"btn btn-navy\" id=\"listen-play-one\">Nghe câu này</button>";
      const pb=document.getElementById("listen-play-one");
      if(pb)pb.addEventListener("click",function(){played=spoken;speak(spoken,pb);});
      if(choiceBox)choiceBox.innerHTML="<button type=\"button\" class=\"opt\" data-v=\"wrong\"><span class=\"letter\">A</span><span>Câu sai</span></button><button type=\"button\" class=\"opt\" data-v=\"right\"><span class=\"letter\">B</span><span>Câu đúng</span></button>";
      choiceBox.querySelectorAll(".opt").forEach(function(b){
        b.addEventListener("click",function(){
          const ok=(b.dataset.v==="right")===isRight;
          scores.push(ok?100:0);
          if(feedbackEl)feedbackEl.innerHTML=(ok?"<p class=\"good\">Đúng rồi!</p>":"<p class=\"bad\">Chưa đúng. Câu vừa nghe là câu "+(isRight?"đúng":"sai")+".</p>")+pairHtml(cur.pair);
          if(nextBtn)nextBtn.style.display="";
        });
      });
    }else if(cur.mode==="choose"){
      const order=Math.random()<0.5?[cur.pair.wrong,cur.pair.right]:[cur.pair.right,cur.pair.wrong];
      const rightIdx=order[0]===cur.pair.right?0:1;
      if(playBox)playBox.innerHTML="<button type=\"button\" class=\"btn btn-navy\" id=\"listen-play-1\">Nghe câu 1</button> <button type=\"button\" class=\"btn btn-navy\" id=\"listen-play-2\">Nghe câu 2</button>";
      const p1=document.getElementById("listen-play-1"), p2=document.getElementById("listen-play-2");
      if(p1)p1.addEventListener("click",function(){speak(order[0],p1);});
      if(p2)p2.addEventListener("click",function(){speak(order[1],p2);});
      if(choiceBox)choiceBox.innerHTML="<button type=\"button\" class=\"opt\" data-v=\"0\"><span class=\"letter\">A</span><span>Câu 1 đúng</span></button><button type=\"button\" class=\"opt\" data-v=\"1\"><span class=\"letter\">B</span><span>Câu 2 đúng</span></button>";
      choiceBox.querySelectorAll(".opt").forEach(function(b){
        b.addEventListener("click",function(){
          const ok=parseInt(b.dataset.v,10)===rightIdx;
          scores.push(ok?100:0);
          if(feedbackEl)feedbackEl.innerHTML=(ok?"<p class=\"good\">Đúng rồi! Câu "+(rightIdx+1)+" là câu đúng.</p>":"<p class=\"bad\">Chưa đúng. Câu "+(rightIdx+1)+" mới là câu đúng.</p>")+pairHtml(cur.pair);
          if(nextBtn)nextBtn.style.display="";
        });
      });
    }else{
      if(playBox)playBox.innerHTML="<button type=\"button\" class=\"btn btn-navy\" id=\"listen-play-wrong\">Nghe câu sai</button>";
      const pb=document.getElementById("listen-play-wrong");
      if(pb)pb.addEventListener("click",function(){speak(cur.pair.wrong,pb);});
      if(typeBox)typeBox.style.display="block";
      if(typeInput)typeInput.value="";
      if(typeInput)typeInput.focus();
      const check=function(){
        const typed=typeInput?String(typeInput.value||"").trim():"";
        if(!typed)return;
        const r=sdscAlignWords(cur.pair.right,typed);
        scores.push(r.pct);
        const d=sdscDiffHtml(typed,cur.pair.right);
        if(feedbackEl)feedbackEl.innerHTML="<p>Bạn gõ: "+d.aHtml+"</p><p>Câu đúng: "+d.bHtml+"</p>"
          +"<p>Điểm lượt này: <b>"+r.pct+" điểm</b></p>"
          +"<div class=\"skill-colored\">"+sdscColoredSentence(cur.pair.right,r.marks)+"</div>"
          +(r.missed.length?"<p>Từ còn thiếu hoặc chưa đúng: "+escapeHtml(r.missed.join(", "))+"</p>":"<p>Gõ đúng hết mọi từ. Tuyệt vời!</p>")
          +(cur.pair.why?"<p>"+escapeHtml(cur.pair.why)+"</p>":"");
        if(nextBtn)nextBtn.style.display="";
      };
      if(typeBtn)typeBtn.onclick=check;
      if(typeInput)typeInput.onkeydown=function(e){if(e.key==="Enter"){e.preventDefault();check();}};
    }
  }
  function finishSession(){
    const avg=scores.length?Math.round(scores.reduce(function(a,b){return a+b;},0)/scores.length):0;
    const seconds=sessionStart?Math.max(60,Math.round((Date.now()-sessionStart)/1000)):60;
    recordSkillSession("listening",seconds,sessionWords,avg);
    let xpAwarded=false;
    updateProgress(function(p){xpAwarded=markSkillDone(p,"listen",20);});
    let adv=false;
    if(lessonSlug){try{adv=completeSkillReview(lessonSlug,"listen");}catch(e){}}
    showStats();
    if(card)card.style.display="none";
    if(doneBox){
      doneBox.style.display="block";
      doneBox.innerHTML="<h3>Xong buổi luyện nghe</h3><p>Điểm trung bình "+session.length+" câu: <b>"+avg+" điểm</b>.</p>"
        +(xpAwarded?"<p>Nhận <b>+20 XP</b>, đã cộng vào Nhiệm vụ hôm nay.</p>":"<p>Hôm nay đã nhận 20 XP luyện nghe rồi.</p>")
        +(adv?"<p>Bài này đã ôn xong bằng Nghe, lần ôn tới đổi sang kỹ năng khác.</p>":"")
        +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"listen-again\">Luyện buổi mới</button></p>";
      const again=document.getElementById("listen-again");
      if(again)again.addEventListener("click",function(){startSession();});
    }
  }
  if(nextBtn)nextBtn.addEventListener("click",function(){
    idx++;
    if(idx<session.length)renderRound();
    else finishSession();
  });
  const startBtn=document.getElementById("listen-begin");
  if(startBtn)startBtn.addEventListener("click",startSession);
  try{
    const q=new URLSearchParams(location.search);
    const l=q.get("lesson");
    if(l&&skills[l])lessonSlug=l;
  }catch(e){}
  showStats();
  if(lessonSlug)startSession();
  window.__listenTest={
    startSession:startSession,
    state:function(){return {idx:idx,total:session.length,scores:scores.slice(),mode:session[idx]?session[idx].mode:null,pair:session[idx]?session[idx].pair:null};},
    answerPick:function(v){const b=choiceBox&&choiceBox.querySelector(".opt[data-v=\""+v+"\"]");if(b)b.click();},
    answerChoose:function(v){const b=choiceBox&&choiceBox.querySelector(".opt[data-v=\""+v+"\"]");if(b)b.click();},
    answerType:function(t){if(typeInput)typeInput.value=t;if(typeBtn)typeBtn.click();},
    next:function(){if(nextBtn)nextBtn.click();}
  };
})();
</script>
"""

WRITE_JS = r"""
<script>
(function(){
  const skills=window.SDSC_SKILLS||{};
  const pairs=[];
  Object.keys(skills).forEach(function(slug){
    const l=skills[slug];
    const ms=(l.mistakes||[]).filter(function(m){return m.wrong&&m.right;});
    if(ms.length){
      ms.forEach(function(m){pairs.push({wrong:m.wrong,right:m.right,code:l.code,title:l.title,slug:slug,topic:l.topic||"",why:l.why||"",right_note:l.right_note||""});});
    }else if(l.wrong&&l.right){
      pairs.push({wrong:l.wrong,right:l.right,code:l.code,title:l.title,slug:slug,topic:l.topic||"",why:l.why||"",right_note:l.right_note||""});
    }
  });
  const WRONG_KEY="sdsc-write-wrong-v1";
  function loadWrong(){try{const v=loadJSON(WRONG_KEY);return Array.isArray(v)?v:[];}catch(e){return [];}}
  function saveWrong(list){try{saveJSON(WRONG_KEY,list);}catch(e){}}
  function noteWrong(pair,ok){
    const list=loadWrong();
    const key=pair.slug+"|"+pair.wrong;
    const i=list.findIndex(function(x){return x.key===key;});
    if(ok){if(i>=0){list.splice(i,1);saveWrong(list);}}
    else{
      if(i>=0)list[i].count=(list[i].count||1)+1;
      else list.push({key:key,wrong:pair.wrong,right:pair.right,code:pair.code,title:pair.title,slug:pair.slug,count:1});
      saveWrong(list);
    }
  }
  const modes=["fix","translate","fill"];
  const MODE_LABEL={fix:"Viết lại câu sai thành câu đúng",translate:"Dịch từ tiếng Việt sang câu đúng",fill:"Điền từ còn thiếu"};
  const card=document.getElementById("write-card");
  const roundEl=document.getElementById("write-round");
  const promptEl=document.getElementById("write-prompt");
  const sourceEl=document.getElementById("write-source");
  const inputEl=document.getElementById("write-input");
  const checkBtn=document.getElementById("write-check");
  const feedbackEl=document.getElementById("write-feedback");
  const nextBtn=document.getElementById("write-next");
  const doneBox=document.getElementById("write-done");
  const statsEl=document.getElementById("write-stats");
  const wrongBox=document.getElementById("write-wrong");
  const startBox=document.getElementById("write-start");
  const progressEl=document.getElementById("write-progress");
  let session=[], idx=0, scores=[], sessionStart=null, sessionWords=0, lessonSlug=null, curPair=null;
  function shuffle(a){
    for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));const t=a[i];a[i]=a[j];a[j]=t;}
    return a;
  }
  function showStats(){
    if(!statsEl)return;
    const sp=loadSkillSession("writing");
    statsEl.textContent="Bạn đã luyện viết "+(sp.sessions||0)+" buổi, tổng "+speakingHoursText(sp.minutes||0)+", điểm tốt nhất "+(sp.best||0)+" điểm, chuỗi luyện viết "+(sp.streak||0)+" ngày.";
  }
  function renderWrongList(){
    if(!wrongBox)return;
    const list=loadWrong();
    if(!list.length){wrongBox.innerHTML="<p>Chưa có câu nào bạn hay viết sai. Luyện vài buổi rồi quay lại nhé.</p>";return;}
    wrongBox.innerHTML=list.map(function(x){
      return "<div class=\"miss-row\"><span><b>"+escapeHtml(x.wrong)+"</b> <span class=\"vi\">sai "+x.count+" lần</span></span><button type=\"button\" class=\"btn btn-ghost\" data-slug=\""+escapeHtml(x.slug)+"\" data-wrong=\""+escapeHtml(x.wrong)+"\">Luyện lại</button></div>";
    }).join("");
    wrongBox.querySelectorAll("button").forEach(function(b){
      b.addEventListener("click",function(){
        const p=pairs.find(function(pp){return pp.slug===b.dataset.slug&&pp.wrong===b.dataset.wrong;});
        if(p)startSession([p]);
      });
    });
  }
  function blankWords(sentence){
    const toks=sdscWordTokens(sentence);
    const content=toks.filter(function(t){return t.norm.length>2;});
    if(!content.length)return {display:sentence,answer:""};
    const pick=content[Math.floor(Math.random()*content.length)];
    const display=toks.map(function(t){return t.norm===pick.norm?"___":t.text;}).join(" ");
    return {display:display,answer:pick.text};
  }
  function startSession(fixedPairs){
    let pool=pairs.slice();
    if(lessonSlug)pool=pool.filter(function(p){return p.slug===lessonSlug;});
    if(fixedPairs&&fixedPairs.length)pool=fixedPairs.slice();
    if(!pool.length)pool=pairs.slice();
    shuffle(pool);
    session=[];
    for(let r=0;r<3;r++){
      const item={pair:pool[r%pool.length],mode:modes[r%3]};
      if(item.mode==="translate"&&!item.pair.right_note)item.mode="fix";
      session.push(item);
    }
    idx=0;scores=[];sessionWords=0;sessionStart=Date.now();
    if(startBox)startBox.style.display="none";
    if(card)card.style.display="block";
    if(doneBox)doneBox.style.display="none";
    renderRound();
  }
  function renderRound(){
    const cur=session[idx];
    if(!cur)return;
    curPair=cur.pair;
    if(roundEl)roundEl.textContent="Câu "+(idx+1)+" trên "+session.length+": "+MODE_LABEL[cur.mode];
    if(progressEl)progressEl.textContent="Buổi luyện viết: "+(idx+1)+" trên "+session.length+" câu.";
    if(sourceEl)sourceEl.innerHTML="Từ bài <a href=\""+BASE_PATH_PLACEHOLDER+"/bai/"+encodeURIComponent(cur.pair.slug)+"/\">"+escapeHtml(cur.pair.code+" "+cur.pair.title)+"</a>";
    if(feedbackEl)feedbackEl.innerHTML="";
    if(nextBtn)nextBtn.style.display="none";
    if(inputEl){inputEl.value="";inputEl.focus();}
    if(cur.mode==="fix"){
      if(promptEl)promptEl.innerHTML="<p class=\"skill-sentence\">"+escapeHtml(cur.pair.wrong)+"</p><p class=\"skill-vi\">Viết lại câu này thành câu đúng nhé.</p>";
    }else if(cur.mode==="translate"){
      const vi=cur.pair.right_note||"";
      if(promptEl)promptEl.innerHTML="<p class=\"skill-sentence\">"+escapeHtml(vi)+"</p><p class=\"skill-vi\">Dịch câu trên sang tiếng Anh, viết đúng câu đã học nhé.</p>";
    }else{
      const b=blankWords(cur.pair.right);
      cur.blank=b;
      if(promptEl)promptEl.innerHTML="<p class=\"skill-sentence\">"+escapeHtml(b.display)+"</p><p class=\"skill-vi\">Điền từ còn thiếu vào chỗ trống nhé.</p>";
    }
  }
  function check(){
    const cur=session[idx];
    if(!cur)return;
    const typed=inputEl?String(inputEl.value||"").trim():"";
    if(!typed)return;
    sessionWords+=sdscTokenize(typed).length;
    let target=cur.pair.right, pct=0, marks=[], missed=[];
    if(cur.mode==="fill"){
      const filled=cur.blank.display.replace("___",typed);
      const r=sdscAlignWords(target,filled);
      pct=r.pct;marks=r.marks;missed=r.missed;
    }else{
      const r=sdscAlignWords(target,typed);
      pct=r.pct;marks=r.marks;missed=r.missed;
    }
    scores.push(pct);
    const ok=pct>=90;
    noteWrong(cur.pair,ok);
    const d=sdscDiffHtml(typed,target);
    if(feedbackEl)feedbackEl.innerHTML="<p>Bạn viết: "+d.aHtml+"</p><p>Câu đúng: "+d.bHtml+"</p>"
      +"<p>Điểm lượt này: <b>"+pct+" điểm</b></p>"
      +"<div class=\"skill-colored\">"+sdscColoredSentence(target,marks)+"</div>"
      +(missed.length?"<p>Từ còn thiếu hoặc chưa đúng: "+escapeHtml(missed.join(", "))+"</p>":"<p>Viết đúng hết mọi từ. Tuyệt vời!</p>")
      +(cur.pair.why?"<p>"+escapeHtml(cur.pair.why)+"</p>":"");
    if(nextBtn)nextBtn.style.display="";
    renderWrongList();
  }
  function finishSession(){
    const avg=scores.length?Math.round(scores.reduce(function(a,b){return a+b;},0)/scores.length):0;
    const seconds=sessionStart?Math.max(60,Math.round((Date.now()-sessionStart)/1000)):60;
    recordSkillSession("writing",seconds,sessionWords,avg);
    let xpAwarded=false;
    updateProgress(function(p){xpAwarded=markSkillDone(p,"write",20);});
    let adv=false;
    if(lessonSlug){try{adv=completeSkillReview(lessonSlug,"write");}catch(e){}}
    showStats();
    if(card)card.style.display="none";
    if(doneBox){
      doneBox.style.display="block";
      doneBox.innerHTML="<h3>Xong buổi luyện viết</h3><p>Điểm trung bình "+session.length+" câu: <b>"+avg+" điểm</b>.</p>"
        +(xpAwarded?"<p>Nhận <b>+20 XP</b>, đã cộng vào Nhiệm vụ hôm nay.</p>":"<p>Hôm nay đã nhận 20 XP luyện viết rồi.</p>")
        +(adv?"<p>Bài này đã ôn xong bằng Viết, lần ôn tới đổi sang kỹ năng khác.</p>":"")
        +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"write-again\">Luyện buổi mới</button></p>";
      const again=document.getElementById("write-again");
      if(again)again.addEventListener("click",function(){startSession();});
    }
  }
  if(checkBtn)checkBtn.addEventListener("click",check);
  if(inputEl)inputEl.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();check();}});
  if(nextBtn)nextBtn.addEventListener("click",function(){
    idx++;
    if(idx<session.length)renderRound();
    else finishSession();
  });
  const startBtn=document.getElementById("write-begin");
  if(startBtn)startBtn.addEventListener("click",function(){startSession();});
  try{
    const q=new URLSearchParams(location.search);
    const l=q.get("lesson");
    if(l&&skills[l])lessonSlug=l;
  }catch(e){}
  showStats();renderWrongList();
  if(lessonSlug)startSession();
  window.__writeTest={
    startSession:startSession,
    state:function(){return {idx:idx,total:session.length,scores:scores.slice(),mode:session[idx]?session[idx].mode:null,pair:session[idx]?session[idx].pair:null};},
    answer:function(t){if(inputEl)inputEl.value=t;check();},
    next:function(){if(nextBtn)nextBtn.click();},
    wrongList:loadWrong
  };
})();
</script>
"""

READ_JS = r"""
<script>
(function(){
  const passages=(window.SDSC_READING&&window.SDSC_READING.passages)||window.SDSC_READING||[];
  const viMap=window.SDSC_READ_VI||{};
  const card=document.getElementById("read-card");
  const levelEl=document.getElementById("read-level");
  const passageEl=document.getElementById("read-passage");
  const situationEl=document.getElementById("read-situation");
  const sourceEl=document.getElementById("read-source");
  const fixBox=document.getElementById("read-fix");
  const qBox=document.getElementById("read-question");
  const feedbackEl=document.getElementById("read-feedback");
  const nextBtn=document.getElementById("read-next");
  const doneBox=document.getElementById("read-done");
  const statsEl=document.getElementById("read-stats");
  const wordPop=document.getElementById("read-wordpop");
  const startBox=document.getElementById("read-start");
  const progressEl=document.getElementById("read-progress");
  let session=[], idx=0, scores=[], sessionStart=null, sessionWords=0, lessonSlug=null, cur=null, findAttempts=0, fixAttempts=0, found=false, fixed=false, qDone=false;
  function getLevel(){
    try{const p=getProgress();const lv=p.settings&&p.settings.readLevel;return (lv===1||lv===2||lv===3)?lv:1;}catch(e){return 1;}
  }
  function setLevel(lv){
    updateProgress(function(p){if(!p.settings)p.settings={};p.settings.readLevel=Math.max(1,Math.min(3,lv));});
  }
  function showStats(){
    if(!statsEl)return;
    const sp=loadSkillSession("reading");
    statsEl.textContent="Bạn đã luyện đọc "+(sp.sessions||0)+" buổi, tổng "+speakingHoursText(sp.minutes||0)+", điểm tốt nhất "+(sp.best||0)+" điểm, chuỗi luyện đọc "+(sp.streak||0)+" ngày.";
  }
  function passagesAtLevel(lv){
    const list=passages.filter(function(p){return p.level===lv;});
    if(list.length)return list;
    return passages.slice();
  }
  function shuffle(a){
    for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));const t=a[i];a[i]=a[j];a[j]=t;}
    return a;
  }
  function startSession(){
    const lv=getLevel();
    let pool=passagesAtLevel(lv).slice();
    if(lessonSlug)pool=pool.filter(function(p){return p.slug===lessonSlug;});
    if(!pool.length)pool=passages.slice();
    shuffle(pool);
    session=pool.slice(0,3);
    idx=0;scores=[];sessionWords=0;sessionStart=Date.now();
    if(startBox)startBox.style.display="none";
    if(card)card.style.display="block";
    if(doneBox)doneBox.style.display="none";
    renderRound();
  }
  function renderRound(){
    cur=session[idx];
    if(!cur)return;
    findAttempts=0;fixAttempts=0;found=false;fixed=false;qDone=false;
    if(levelEl)levelEl.textContent="Cấp độ đọc: "+getLevel()+" trên 3. Đạt 90 điểm trở lên thì lần sau khó hơn, dưới 70 điểm thì dễ hơn.";
    if(progressEl)progressEl.textContent="Buổi luyện đọc: đoạn "+(idx+1)+" trên "+session.length+".";
    if(situationEl)situationEl.textContent="Tình huống: "+(cur.situation||cur.title||"");
    if(sourceEl)sourceEl.innerHTML="Từ bài <a href=\""+BASE_PATH_PLACEHOLDER+"/bai/"+encodeURIComponent(cur.slug)+"/\">"+escapeHtml(cur.code+" "+cur.title)+"</a>";
    if(feedbackEl)feedbackEl.innerHTML="";
    if(fixBox)fixBox.innerHTML="";
    if(qBox)qBox.innerHTML="";
    if(wordPop)wordPop.innerHTML="";
    if(nextBtn)nextBtn.style.display="none";
    sessionWords+=cur.sentences.reduce(function(n,s){return n+sdscTokenize(s.text).length;},0);
    if(passageEl){
      passageEl.innerHTML=cur.sentences.map(function(s,i){
        const words=sdscWordTokens(s.text).map(function(t){
          return "<span class=\"word\" data-w=\""+escapeHtml(t.norm)+"\">"+escapeHtml(t.text)+"</span>";
        }).join(" ");
        return "<p class=\"read-sentence\" data-i=\""+i+"\">"+words+" <button type=\"button\" class=\"btn btn-ghost btn-pick-sentence\" data-i=\""+i+"\">Câu này sai</button></p>";
      }).join("");
      passageEl.querySelectorAll(".word").forEach(function(w){
        w.addEventListener("click",function(e){
          e.stopPropagation();
          const word=w.dataset.w;
          const v=viMap[word]||"";
          if(wordPop){
            if(v)wordPop.innerHTML="<b>"+escapeHtml(word)+"</b>: "+escapeHtml(v);
            else wordPop.innerHTML="<b>"+escapeHtml(word)+"</b>: chưa có trong từ điển của Trang. <a href=\"https://dictionary.cambridge.org/dictionary/english/"+encodeURIComponent(word)+"\" target=\"_blank\" rel=\"noopener\">Tra trên Cambridge →</a>";
          }
        });
      });
      passageEl.querySelectorAll(".btn-pick-sentence").forEach(function(b){
        b.addEventListener("click",function(){pickSentence(parseInt(b.dataset.i,10));});
      });
    }
  }
  function pickSentence(i){
    const s=cur.sentences[i];
    if(!s)return false;
    if(found)return false;
    if(!s.error){
      findAttempts++;
      if(feedbackEl)feedbackEl.innerHTML="<p class=\"bad\">Câu này không có lỗi. Đọc kĩ lại nhé, lỗi nằm ở 1 câu khác.</p>";
      return false;
    }
    found=true;
    if(feedbackEl)feedbackEl.innerHTML="<p class=\"good\">Đúng rồi, lỗi nằm ở câu này.</p>";
    if(fixBox){
      fixBox.innerHTML="<h3>Chọn cách sửa đúng:</h3><div class=\"skill-choices\">"
        +s.options.map(function(o,j){
          return "<button type=\"button\" class=\"opt\" data-i=\""+j+"\"><span class=\"letter\">"+["A","B","C"][j]+"</span><span>"+escapeHtml(o)+"</span></button>";
        }).join("")+"</div>";
      fixBox.querySelectorAll(".opt").forEach(function(b){
        b.addEventListener("click",function(){pickFix(parseInt(b.dataset.i,10));});
      });
    }
    return true;
  }
  function pickFix(j){
    const s=cur.sentences.find(function(x){return x.error;});
    if(!s||fixed)return false;
    if(j!==s.answer){
      fixAttempts++;
      if(feedbackEl)feedbackEl.innerHTML="<p class=\"bad\">Chưa đúng. Đọc lại lời giải thích nhé.</p><p>"+escapeHtml(s.why||"")+"</p>";
      return false;
    }
    fixed=true;
    if(feedbackEl)feedbackEl.innerHTML="<p class=\"good\">Sửa đúng rồi!</p><p>Câu đúng: <b>"+escapeHtml(s.fix)+"</b></p><p>"+escapeHtml(s.why||"")+"</p>";
    const sentEl=passageEl&&passageEl.querySelector(".read-sentence[data-i=\""+cur.sentences.indexOf(s)+"\"]");
    if(sentEl){
      sentEl.querySelectorAll(".word").forEach(function(w){w.classList.add("fixed");});
    }
    if(qBox&&cur.question){
      qBox.innerHTML="<h3>Câu hỏi hiểu bài:</h3><p>"+escapeHtml(cur.question.q)+"</p><div class=\"skill-choices\">"
        +cur.question.options.map(function(o,k){
          return "<button type=\"button\" class=\"opt\" data-i=\""+k+"\"><span class=\"letter\">"+["A","B","C"][k]+"</span><span>"+escapeHtml(o)+"</span></button>";
        }).join("")+"</div>";
      qBox.querySelectorAll(".opt").forEach(function(b){
        b.addEventListener("click",function(){pickQ(parseInt(b.dataset.i,10));});
      });
    }else{
      finishRound();
    }
    return true;
  }
  function pickQ(k){
    if(qDone)return false;
    qDone=true;
    const q=cur.question;
    const ok=k===q.answer;
    if(feedbackEl)feedbackEl.innerHTML+=(ok?"<p class=\"good\">Trả lời đúng rồi!</p>":"<p class=\"bad\">Chưa đúng. Đáp án đúng là: "+escapeHtml(q.options[q.answer])+"</p>");
    finishRound(ok);
    return ok;
  }
  function finishRound(qOk){
    const findScore=findAttempts===0?50:(findAttempts===1?25:0);
    const fixScore=fixAttempts===0?30:(fixAttempts===1?15:0);
    const qScore=qOk===undefined?20:(qOk?20:0);
    const score=findScore+fixScore+qScore;
    scores.push(score);
    let xpAwarded=false;
    updateProgress(function(p){xpAwarded=markSkillDone(p,"read",20);});
    if(feedbackEl)feedbackEl.innerHTML+="<p>Điểm đoạn này: <b>"+score+" điểm</b>"+(xpAwarded?" (nhận +20 XP)":"")+".</p>";
    if(nextBtn)nextBtn.style.display="";
  }
  function finishSession(){
    const avg=scores.length?Math.round(scores.reduce(function(a,b){return a+b;},0)/scores.length):0;
    const seconds=sessionStart?Math.max(60,Math.round((Date.now()-sessionStart)/1000)):60;
    recordSkillSession("reading",seconds,sessionWords,avg);
    const lv=getLevel();
    if(avg>=90&&lv<3)setLevel(lv+1);
    else if(avg<70&&lv>1)setLevel(lv-1);
    let adv=false;
    if(lessonSlug){try{adv=completeSkillReview(lessonSlug,"read");}catch(e){}}
    showStats();
    if(card)card.style.display="none";
    if(doneBox){
      doneBox.style.display="block";
      doneBox.innerHTML="<h3>Xong buổi luyện đọc</h3><p>Điểm trung bình "+session.length+" đoạn: <b>"+avg+" điểm</b>.</p>"
        +"<p>Cấp độ đọc lần sau: <b>"+getLevel()+" trên 3</b>.</p>"
        +(adv?"<p>Bài này đã ôn xong bằng Đọc, lần ôn tới đổi sang kỹ năng khác.</p>":"")
        +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"read-again\">Luyện buổi mới</button></p>";
      const again=document.getElementById("read-again");
      if(again)again.addEventListener("click",function(){startSession();});
    }
  }
  if(nextBtn)nextBtn.addEventListener("click",function(){
    idx++;
    if(idx<session.length)renderRound();
    else finishSession();
  });
  const startBtn=document.getElementById("read-begin");
  if(startBtn)startBtn.addEventListener("click",startSession);
  try{
    const q=new URLSearchParams(location.search);
    const l=q.get("lesson");
    if(l&&passages.some(function(p){return p.slug===l;}))lessonSlug=l;
  }catch(e){}
  showStats();
  if(lessonSlug)startSession();
  window.__readTest={
    startSession:startSession,
    state:function(){return {idx:idx,total:session.length,scores:scores.slice(),passage:cur?cur.slug:null,found:found,fixed:fixed};},
    pickSentence:pickSentence,
    pickFix:pickFix,
    pickQ:pickQ,
    next:function(){if(nextBtn)nextBtn.click();},
    level:getLevel
  };
})();
</script>
"""

COMM_JS = r"""
<script>
(function(){
  var API_BASE="https://sdsc-community-api.vercel.app";
  var AUTH_KEY="sdsc-comm-auth-v1";
  var BOARDS_KEY="sdsc-comm-boards-v1";
  var HEART_KEY="sdsc-comm-hearts-v1";
  var BADGE_KEY="sdsc-comm-badges-v1";
  var SYNC_KEY="sdsc-comm-sync-v1";
  var XPDAY_KEY="sdsc-comm-xpday-v1";
  var CHALLENGE={title:"Sửa 5 lỗi về thì trong tuần",target:5,unit:"lỗi",rewardXp:100,badge:"Hoàn thành thử thách tuần"};
  var FALLBACK_WEEK="2026-11-23";
  var boards={weekly:null,streak:null,speaking:null};
  var stats=null;
  var weekMonday=FALLBACK_WEEK;
  var boardsLoaded=false;
  var boardsFailed=false;
  var boardsFromCache=false;
  var cheerMsg={board:null,text:""};
  var pendingReg=null;
  var syncTimer=null;
  var syncing=false;
  var readyResolve=null;
  var ready=new Promise(function(res){readyResolve=res;});
  function hasFetch(){return typeof fetch==="function";}
  function commLoad(key,fallback){try{var v=JSON.parse(localStorage.getItem(key)||"null");return (v===null||v===undefined)?fallback:v;}catch(e){return fallback;}}
  function commSave(key,val){try{localStorage.setItem(key,JSON.stringify(val));}catch(e){}}
  function loadAuth(){var v=commLoad(AUTH_KEY,null);if(v&&v.token&&v.email&&v.expires&&new Date(v.expires).getTime()>Date.now())return v;return null;}
  function saveAuth(a){commSave(AUTH_KEY,a);}
  function clearAuth(){try{localStorage.removeItem(AUTH_KEY);}catch(e){}}
  function loadHearts(){var v=commLoad(HEART_KEY,[]);return Array.isArray(v)?v:[];}
  function saveHearts(list){commSave(HEART_KEY,list);}
  function loadBadges(){var v=commLoad(BADGE_KEY,[]);return Array.isArray(v)?v:[];}
  function saveBadges(list){commSave(BADGE_KEY,list);}
  function apiCall(path,opts){
    opts=opts||{};
    return new Promise(function(resolve,reject){
      if(!hasFetch()){var e0=new Error("Không có kết nối mạng, kiểm tra mạng rồi thử lại nhé.");e0.code="network";reject(e0);return;}
      var headers={};
      if(opts.headers){Object.keys(opts.headers).forEach(function(k){headers[k]=opts.headers[k];});}
      if(opts.body!==undefined&&opts.body!==null)headers["Content-Type"]="application/json";
      var ctrl=null,timer=null;
      try{
        if(typeof AbortController!=="undefined"){ctrl=new AbortController();timer=setTimeout(function(){try{ctrl.abort();}catch(e2){}},8000);}
      }catch(e){}
      var init={method:opts.method||"GET",headers:headers};
      if(opts.body!==undefined&&opts.body!==null)init.body=JSON.stringify(opts.body);
      if(ctrl)init.signal=ctrl.signal;
      fetch(API_BASE+path,init).then(function(resp){
        if(timer)clearTimeout(timer);
        return resp.text().then(function(text){
          var data=null;
          try{data=text?JSON.parse(text):null;}catch(e){}
          if(resp.ok){resolve(data);return;}
          var err=new Error((data&&data.error)||"Máy chủ chưa trả lời được, thử lại sau nhé.");
          err.code=(data&&data.code)||"server_error";
          err.status=resp.status;
          if(resp.status===401)clearAuth();
          reject(err);
        });
      }).catch(function(){
        if(timer)clearTimeout(timer);
        var e2=new Error("Không nối được máy chủ, kiểm tra mạng rồi thử lại nhé.");
        e2.code="network";
        reject(e2);
      });
    });
  }
  function weekNumber(mondayStr){
    try{
      var d=new Date(mondayStr+"T00:00:00");
      var day=(d.getDay()+6)%7;
      d.setDate(d.getDate()-day+3);
      var first=new Date(d.getFullYear(),0,4);
      var fday=(first.getDay()+6)%7;
      first.setDate(first.getDate()-fday+3);
      return 1+Math.round((d.getTime()-first.getTime())/86400000/7);
    }catch(e){return 48;}
  }
  function myLevel(){
    try{var p=getProgress();return xpLevel(p.xpTotal||0);}catch(e){return 1;}
  }
  function weeklyXpLocal(){
    try{
      var p=getProgress();
      var weekStart=new Date(weekMonday+"T00:00:00");
      var xp=0;
      (p.history||[]).forEach(function(h){
        var d=new Date(h.at||h.date+"T00:00:00");
        if(d>=weekStart){
          if(h.action==="done")xp+=20;
          else if(h.action==="review")xp+=10;
        }
      });
      return xp;
    }catch(e){return 0;}
  }
  function challengeProgress(){
    try{
      var p=getProgress();
      var weekStart=new Date(weekMonday+"T00:00:00");
      var doneSlugs={};
      (p.history||[]).forEach(function(h){
        var d=new Date(h.at||h.date+"T00:00:00");
        if(d>=weekStart&&h.action==="done"&&h.slug)doneSlugs[h.slug]=true;
      });
      var n=0;
      Object.keys(doneSlugs).forEach(function(slug){
        var l=(window.SDSC_LESSONS||{})[slug];
        if(l&&l.type==="Lỗi")n++;
      });
      return Math.min(n,CHALLENGE.target);
    }catch(e){return 0;}
  }
  function dailyEarnedToday(){
    var today=todayISO();
    var rec=commLoad(XPDAY_KEY,null);
    var xp=0;
    try{xp=getProgress().xpTotal||0;}catch(e){}
    if(!rec||typeof rec!=="object")rec={date:today,lastXpTotal:xp,earned:0};
    if(rec.date!==today)rec={date:today,lastXpTotal:rec.lastXpTotal||0,earned:0};
    var delta=Math.max(0,xp-(rec.lastXpTotal||0));
    rec.earned=(rec.earned||0)+delta;
    rec.lastXpTotal=xp;
    commSave(XPDAY_KEY,rec);
    return rec.earned;
  }
  function toServerProgress(p){
    var sp=null;
    try{sp=loadSpeaking();}catch(e){sp={sessions:0,minutes:0,words:0,best:0,lastDay:""};}
    var review={};
    Object.keys(p.review||{}).forEach(function(slug){
      var r=p.review[slug]||{};
      review[slug]={interval:r.interval||1,nextDue:r.nextDue||"",ease:r.ease||2.5,reps:r.reps||0};
    });
    return {
      version:1,
      updatedAt:p.updatedAt||new Date().toISOString(),
      lessons:p.lessons||{},
      practice:p.practice||{},
      streak:p.streak||{count:0,lastDate:"",dates:[]},
      review:review,
      history:(p.history||[]).slice(-500),
      settings:p.settings||{dailyGoal:1,remindReview:true},
      speaking:{sessions:sp.sessions||0,minutes:sp.minutes||0,words:sp.words||0,best:sp.best||0,lastDay:sp.lastDay||""},
      xp:{total:p.xpTotal||0,weekly:weeklyXpLocal(),weekKey:weekMonday,dailyEarned:dailyEarnedToday(),dailyDate:todayISO()},
      completions:[]
    };
  }
  function fromServerProgress(sp){
    if(!sp||typeof sp!=="object")return;
    var local=null;
    try{local=getProgress();}catch(e){local=null;}
    var oldSkills={};
    try{
      Object.keys((local&&local.review)||{}).forEach(function(slug){
        var r=local.review[slug]||{};
        if(r.skill||typeof r.skillStep==="number")oldSkills[slug]={skill:r.skill,skillStep:r.skillStep};
      });
    }catch(e){}
    updateProgress(function(p){
      if(sp.lessons)p.lessons=sp.lessons;
      if(sp.practice)p.practice=sp.practice;
      if(sp.streak)p.streak=sp.streak;
      if(sp.review){
        var merged={};
        Object.keys(sp.review).forEach(function(slug){
          var r=sp.review[slug]||{};
          merged[slug]={interval:r.interval||1,nextDue:r.nextDue||"",ease:r.ease||2.5,reps:r.reps||0};
          if(oldSkills[slug]){
            if(oldSkills[slug].skill)merged[slug].skill=oldSkills[slug].skill;
            if(typeof oldSkills[slug].skillStep==="number")merged[slug].skillStep=oldSkills[slug].skillStep;
          }
        });
        p.review=merged;
      }
      if(Array.isArray(sp.history))p.history=sp.history.slice(-500);
      if(sp.settings)p.settings=sp.settings;
      if(sp.xp&&typeof sp.xp.total==="number")p.xpTotal=Math.max(p.xpTotal||0,sp.xp.total);
    });
    try{
      var spk=loadSpeaking();
      var s=sp.speaking||{};
      var rec=null;
      try{rec=JSON.parse(localStorage.getItem("sdsc-speaking-v1")||"null")||{};}catch(e){rec={};}
      rec.sessions=Math.max(spk.sessions||0,s.sessions||0);
      rec.seconds=Math.max(spk.seconds||0,(s.minutes||0)*60);
      rec.words=Math.max(spk.words||0,s.words||0);
      rec.best=Math.max(spk.best||0,s.best||0);
      rec.lastDay=((spk.lastDay||"")>=(s.lastDay||""))?spk.lastDay:(s.lastDay||"");
      try{localStorage.setItem("sdsc-speaking-v1",JSON.stringify(rec));}catch(e){}
    }catch(e){}
  }
  function payloadString(){
    try{return JSON.stringify(toServerProgress(getProgress()));}catch(e){return "";}
  }
  function syncNow(){
    var auth=loadAuth();
    if(!auth||syncing)return Promise.resolve(false);
    syncing=true;
    var payload=null;
    try{payload=toServerProgress(getProgress());}catch(e){syncing=false;return Promise.resolve(false);}
    return apiCall("/api/progress/sync",{method:"POST",body:{token:auth.token,progress:payload,updated_at:new Date().toISOString()}}).then(function(res){
      syncing=false;
      if(res&&res.progress)fromServerProgress(res.progress);
      try{commSave(SYNC_KEY,{payload:payloadString(),at:Date.now()});}catch(e){}
      return true;
    }).catch(function(e){
      syncing=false;
      if(e&&e.status===401){clearAuth();renderAll();}
      return false;
    });
  }
  function scheduleSync(ms){
    if(syncTimer)clearTimeout(syncTimer);
    syncTimer=setTimeout(function(){syncTimer=null;syncNow();},ms||3000);
  }
  function maybeSync(){
    var auth=loadAuth();
    if(!auth)return;
    var last=commLoad(SYNC_KEY,null);
    if(last&&last.at&&Date.now()-last.at<60000)return;
    var h=payloadString();
    if(!h)return;
    if(last&&last.payload===h)return;
    scheduleSync(2000);
  }
  function pullMeAndSync(){
    var auth=loadAuth();
    if(!auth)return Promise.resolve(false);
    return apiCall("/api/me",{headers:{Authorization:"Bearer "+auth.token}}).then(function(res){
      if(res&&res.progress)fromServerProgress(res.progress);
      if(res&&res.account&&res.account.display_name){
        var a=loadAuth();
        if(a){a.name=res.account.display_name;saveAuth(a);}
      }
      return syncNow();
    }).catch(function(e){
      if(e&&e.status===401){clearAuth();renderAll();}
      throw e;
    });
  }
  function saveBoardsCache(){
    var prev=commLoad(BOARDS_KEY,null)||{};
    var next={fetchedAt:new Date().toISOString(),week:weekMonday};
    ["weekly","streak","speaking"].forEach(function(k){next[k]=boards[k]||prev[k]||null;});
    next.stats=stats||prev.stats||null;
    commSave(BOARDS_KEY,next);
  }
  function loadBoards(){
    var auth=loadAuth();
    var headers={};
    if(auth&&auth.token)headers={Authorization:"Bearer "+auth.token};
    var cached=commLoad(BOARDS_KEY,null);
    function get(path){return apiCall(path,{headers:headers});}
    var settled=[
      get("/api/leaderboard?board=weekly"),
      get("/api/leaderboard?board=streak"),
      get("/api/leaderboard?board=speaking"),
      get("/api/stats")
    ].map(function(p){return p.then(function(v){return {ok:true,v:v};},function(e){return {ok:false,e:e};});});
    return Promise.all(settled).then(function(res){
      var anyBoardFail=false,fromCache=false;
      var keys=["weekly","streak","speaking"];
      for(var i=0;i<3;i++){
        if(res[i].ok){boards[keys[i]]=res[i].v;}
        else{
          anyBoardFail=true;
          if(cached&&cached[keys[i]]){boards[keys[i]]=cached[keys[i]];fromCache=true;}
        }
      }
      if(res[3].ok){stats=res[3].v;}
      else if(cached&&cached.stats){stats=cached.stats;fromCache=true;}
      if(boards.weekly&&boards.weekly.week)weekMonday=boards.weekly.week;
      else if(cached&&cached.week)weekMonday=cached.week;
      boardsFailed=anyBoardFail;
      boardsFromCache=fromCache;
      boardsLoaded=true;
      saveBoardsCache();
      renderAll();
      if(readyResolve){readyResolve();readyResolve=null;}
      maybeSync();
    });
  }
  function heartBtn(board,r){
    var hearts=loadHearts();
    var key=weekMonday+":"+board+":"+r.account_id;
    var on=hearts.indexOf(key)>=0;
    var n=r.cheers||0;
    return "<button type=\"button\" class=\"comm-heart"+(on?" on":"")+"\" data-board=\""+escapeHtml(board)+"\" data-id=\""+escapeHtml(r.account_id)+"\">"+(on?"♥ ":"♡ ")+n+"</button>";
  }
  function onCheer(btn){
    var auth=loadAuth();
    var board=btn.dataset.board,id=btn.dataset.id;
    if(!auth){cheerMsg={board:board,text:"Đăng nhập để tặng tim nhé."};renderAll();return;}
    var hearts=loadHearts();
    var key=weekMonday+":"+board+":"+id;
    if(hearts.indexOf(key)>=0){cheerMsg={board:board,text:"Bạn đã tặng tim cho người này trong tuần rồi."};renderAll();return;}
    btn.disabled=true;
    apiCall("/api/cheer",{method:"POST",body:{token:auth.token,account_id:id,board:board}}).then(function(res){
      hearts.push(key);saveHearts(hearts);
      var b=boards[board];
      if(b&&b.entries)b.entries.forEach(function(r){if(r.account_id===id)r.cheers=res.cheers;});
      saveBoardsCache();
      cheerMsg={board:null,text:""};
      renderAll();
    }).catch(function(e){
      cheerMsg={board:board,text:e.message||"Không tặng tim được, thử lại sau nhé."};
      renderAll();
    });
  }
  function renderBoard(boardId,apiBoard,title,valueLabel){
    var box=document.getElementById(boardId);
    if(!box)return;
    var data=boards[apiBoard];
    var auth=loadAuth();
    var html="<h3>"+escapeHtml(title)+"</h3>";
    if(!data){
      html+=boardsLoaded?"<p class=\"comm-note\">Không tải được bảng này. Kiểm tra mạng rồi tải lại trang nhé.</p>":"<p>Đang tải bảng…</p>";
      box.innerHTML=html;
      return;
    }
    var rows=data.entries||[];
    if(!rows.length)html+="<p class=\"comm-note\">Chưa có ai trên bảng này.</p>";
    rows.slice(0,10).forEach(function(r,i){
      var medal=i===0?"🥇":i===1?"🥈":i===2?"🥉":"";
      html+="<div class=\"comm-row\"><span class=\"rank\">"+(r.rank||i+1)+"</span><span class=\"name\"><span class=\"comm-who\">"+medal+" "+escapeHtml(r.display_name)+" (Cấp "+(r.level||1)+")</span></span><span class=\"pts\">"+escapeHtml(String(r.value))+" "+escapeHtml(valueLabel)+"</span>"+heartBtn(apiBoard,r)+"</div>";
    });
    if(auth){
      var me=data.me;
      if(me){
        var rankTxt=me.rank?("Hạng "+me.rank):"Chưa xếp hạng";
        html+="<div class=\"comm-row me\"><span class=\"rank\">•</span><span class=\"name\">"+escapeHtml(auth.name)+" (Cấp "+myLevel()+") (bạn)</span><span class=\"pts\">"+me.value+" "+escapeHtml(valueLabel)+"</span><span>"+escapeHtml(rankTxt)+"</span></div>";
      }
    }else{
      html+="<p class=\"comm-note\">Đăng nhập để thấy hạng của bạn trên bảng này.</p>";
    }
    if(cheerMsg.board===apiBoard&&cheerMsg.text)html+="<p class=\"comm-note\">"+escapeHtml(cheerMsg.text)+"</p>";
    box.innerHTML=html;
    box.querySelectorAll(".comm-heart").forEach(function(b){
      b.addEventListener("click",function(){onCheer(b);});
    });
  }
  function renderChallenge(){
    var box=document.getElementById("comm-challenge");
    if(!box)return;
    var done=challengeProgress();
    var target=CHALLENGE.target;
    var pct=Math.round(100*done/target);
    var badges=loadBadges();
    var cid="tuan-"+weekNumber(weekMonday);
    var claimed=badges.indexOf(cid)>=0;
    box.innerHTML="<h3>Thử thách tuần "+weekNumber(weekMonday)+"</h3><p><b>"+escapeHtml(CHALLENGE.title)+"</b></p>"
      +"<div class=\"comm-progress\"><i style=\"width:"+pct+"%\"></i></div>"
      +"<p>"+done+" trên "+target+" "+escapeHtml(CHALLENGE.unit)+" ("+pct+"%)</p>"
      +(done>=target
        ?(claimed?"<p>Đã nhận huy hiệu <b>"+escapeHtml(CHALLENGE.badge)+"</b> và +"+CHALLENGE.rewardXp+" XP.</p>"
          :"<p><button type=\"button\" class=\"btn btn-primary\" id=\"comm-claim\">Nhận huy hiệu + "+CHALLENGE.rewardXp+" XP</button></p>")
        :"<p>Hoàn thành thử thách để nhận huy hiệu <b>"+escapeHtml(CHALLENGE.badge)+"</b> và +"+CHALLENGE.rewardXp+" XP.</p>");
    var claim=document.getElementById("comm-claim");
    if(claim)claim.addEventListener("click",function(){
      var b=loadBadges();
      if(b.indexOf(cid)<0)b.push(cid);
      saveBadges(b);
      updateProgress(function(p){awardXp(p,CHALLENGE.rewardXp);});
      scheduleSync(1000);
      renderAll();
    });
  }
  function renderStats(){
    var el=document.getElementById("comm-stats");
    if(!el)return;
    if(!stats){el.textContent=boardsLoaded?"Chưa tải được thống kê.":"Đang tải thống kê…";return;}
    el.textContent="Đã có "+stats.accounts+" người đăng kí, "+stats.active_week+" người học trong tuần này.";
  }
  function renderAuth(){
    var box=document.getElementById("comm-auth");
    if(!box)return;
    var auth=loadAuth();
    if(auth){
      var badges=loadBadges();
      box.innerHTML="<h3>Tài khoản của bạn</h3><p>Xin chào <b>"+escapeHtml(auth.name)+"</b> ("+escapeHtml(auth.email)+"). Cấp "+myLevel()+".</p>"
        +(badges.length?"<p>Huy hiệu: "+badges.map(function(b){return escapeHtml(b);}).join(", ")+"</p>":"<p>Chưa có huy hiệu nào.</p>")
        +"<p><button type=\"button\" class=\"btn btn-ghost\" id=\"comm-logout\">Đăng xuất</button></p>";
      var out=document.getElementById("comm-logout");
      if(out)out.addEventListener("click",function(){clearAuth();renderAll();loadBoards();});
      return;
    }
    box.innerHTML="<h3>Đăng nhập để đua top</h3>"
      +"<div class=\"comm-form\"><label for=\"comm-email\">Email</label><input id=\"comm-email\" type=\"email\" placeholder=\"email của bạn\" autocomplete=\"email\">"
      +"<label for=\"comm-pass\">Mật khẩu</label><input id=\"comm-pass\" type=\"password\" placeholder=\"mật khẩu\" autocomplete=\"current-password\">"
      +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"comm-login\">Đăng nhập</button> <button type=\"button\" class=\"btn btn-ghost\" id=\"comm-show-register\">Đăng kí tài khoản mới</button></p>"
      +"<p><a href=\"#\" id=\"comm-forgot-link\">Quên mật khẩu</a></p>"
      +"<p id=\"comm-auth-msg\"></p></div>"
      +"<div id=\"comm-register\" style=\"display:none\"><h3>Đăng kí</h3><div class=\"comm-form\">"
      +"<label for=\"comm-reg-email\">Email</label><input id=\"comm-reg-email\" type=\"email\" placeholder=\"email của bạn\">"
      +"<label for=\"comm-reg-name\">Tên hiển thị (2 đến 20 ký tự)</label><input id=\"comm-reg-name\" type=\"text\" placeholder=\"tên hiển thị, không cần tên thật\" maxlength=\"20\">"
      +"<label for=\"comm-reg-pass\">Mật khẩu (ít nhất 8 ký tự)</label><input id=\"comm-reg-pass\" type=\"password\" placeholder=\"mật khẩu\" autocomplete=\"new-password\">"
      +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"comm-register-btn\">Đăng kí</button></p>"
      +"<p id=\"comm-reg-msg\"></p></div></div>"
      +"<div id=\"comm-activate\" style=\"display:none\"><h3>Kích hoạt tài khoản</h3><p>Nhập mã 6 số đã gửi qua email.</p><div class=\"comm-form\">"
      +"<label for=\"comm-code\">Mã 6 số</label><input id=\"comm-code\" type=\"text\" inputmode=\"numeric\" maxlength=\"6\" placeholder=\"••••••\">"
      +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"comm-activate-btn\">Kích hoạt</button> <button type=\"button\" class=\"btn btn-ghost\" id=\"comm-resend-code\">Gửi lại mã</button></p>"
      +"<p id=\"comm-activate-msg\"></p><p class=\"comm-note\">Mã có hiệu lực trong 10 phút. Không nhận được mã? Kiểm tra mục thư rác rồi bấm gửi lại.</p></div></div>"
      +"<div id=\"comm-reset\" style=\"display:none\"><h3>Đặt lại mật khẩu</h3><div class=\"comm-form\">"
      +"<label for=\"comm-reset-email\">Email</label><input id=\"comm-reset-email\" type=\"email\" placeholder=\"email đã đăng kí\">"
      +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"comm-reset-send\">Gửi mã</button></p>"
      +"<label for=\"comm-reset-code\">Mã 6 số</label><input id=\"comm-reset-code\" type=\"text\" inputmode=\"numeric\" maxlength=\"6\" placeholder=\"••••••\">"
      +"<label for=\"comm-reset-pass\">Mật khẩu mới (ít nhất 8 ký tự)</label><input id=\"comm-reset-pass\" type=\"password\" placeholder=\"mật khẩu mới\">"
      +"<p><button type=\"button\" class=\"btn btn-primary\" id=\"comm-reset-btn\">Đặt mật khẩu mới</button></p>"
      +"<p id=\"comm-reset-msg\"></p><p class=\"comm-note\">Mã có hiệu lực trong 10 phút.</p></div></div>";
    function setMsg(id,text){var m=document.getElementById(id);if(m)m.textContent=text;}
    var loginBtn=document.getElementById("comm-login");
    if(loginBtn)loginBtn.addEventListener("click",function(){
      var email=(document.getElementById("comm-email").value||"").trim().toLowerCase();
      var pass=document.getElementById("comm-pass").value||"";
      if(!email||!pass){setMsg("comm-auth-msg","Nhập đủ email và mật khẩu nhé.");return;}
      loginBtn.disabled=true;
      setMsg("comm-auth-msg","Đang đăng nhập…");
      apiCall("/api/auth/login",{method:"POST",body:{email:email,password:pass}}).then(function(res){
        saveAuth({token:res.token,email:email,name:res.account.display_name,accountId:res.account.id,expires:new Date(Date.now()+30*86400000).toISOString()});
        loginBtn.disabled=false;
        renderAll();
        pullMeAndSync().then(function(){loadBoards();renderAll();},function(){loadBoards();renderAll();});
      }).catch(function(e){
        loginBtn.disabled=false;
        setMsg("comm-auth-msg",e.message||"Đăng nhập chưa được, thử lại nhé.");
      });
    });
    var showReg=document.getElementById("comm-show-register");
    if(showReg)showReg.addEventListener("click",function(){
      var r=document.getElementById("comm-register");
      if(r)r.style.display="block";
    });
    var regBtn=document.getElementById("comm-register-btn");
    if(regBtn)regBtn.addEventListener("click",function(){
      var email=(document.getElementById("comm-reg-email").value||"").trim().toLowerCase();
      var name=(document.getElementById("comm-reg-name").value||"").trim();
      var pass=document.getElementById("comm-reg-pass").value||"";
      if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){setMsg("comm-reg-msg","Email chưa đúng định dạng.");return;}
      if(name.length<2||name.length>20){setMsg("comm-reg-msg","Tên hiển thị từ 2 đến 20 ký tự.");return;}
      if(pass.length<8){setMsg("comm-reg-msg","Mật khẩu ít nhất 8 ký tự.");return;}
      regBtn.disabled=true;
      setMsg("comm-reg-msg","Đang gửi mã qua email…");
      apiCall("/api/auth/send-code",{method:"POST",body:{email:email,display_name:name,password:pass,purpose:"register"}}).then(function(){
        pendingReg={email:email,name:name,pass:pass};
        regBtn.disabled=false;
        var act=document.getElementById("comm-activate");
        if(act)act.style.display="block";
        setMsg("comm-reg-msg","Đã gửi mã 6 số qua email. Nhập mã bên dưới nhé.");
      }).catch(function(e){
        regBtn.disabled=false;
        setMsg("comm-reg-msg",e.message||"Chưa gửi được mã, thử lại nhé.");
      });
    });
    var actBtn=document.getElementById("comm-activate-btn");
    if(actBtn)actBtn.addEventListener("click",function(){
      var code=(document.getElementById("comm-code").value||"").trim();
      if(!/^\d{6}$/.test(code)){setMsg("comm-activate-msg","Mã có 6 số nhé.");return;}
      if(!pendingReg){setMsg("comm-activate-msg","Không tìm thấy tài khoản chờ kích hoạt. Đăng kí lại nhé.");return;}
      actBtn.disabled=true;
      setMsg("comm-activate-msg","Đang kích hoạt…");
      apiCall("/api/auth/verify",{method:"POST",body:{email:pendingReg.email,code:code,purpose:"register"}}).then(function(res){
        saveAuth({token:res.token,email:pendingReg.email,name:res.account.display_name,accountId:res.account.id,expires:new Date(Date.now()+30*86400000).toISOString()});
        pendingReg=null;
        actBtn.disabled=false;
        renderAll();
        pullMeAndSync().then(function(){loadBoards();renderAll();},function(){loadBoards();renderAll();});
      }).catch(function(e){
        actBtn.disabled=false;
        setMsg("comm-activate-msg",e.message||"Kích hoạt chưa được, thử lại nhé.");
      });
    });
    var resendBtn=document.getElementById("comm-resend-code");
    if(resendBtn)resendBtn.addEventListener("click",function(){
      if(!pendingReg){setMsg("comm-activate-msg","Không tìm thấy tài khoản chờ kích hoạt. Đăng kí lại nhé.");return;}
      resendBtn.disabled=true;
      apiCall("/api/auth/send-code",{method:"POST",body:{email:pendingReg.email,display_name:pendingReg.name,password:pendingReg.pass,purpose:"register"}}).then(function(){
        setMsg("comm-activate-msg","Đã gửi lại mã qua email.");
        setTimeout(function(){try{resendBtn.disabled=false;}catch(e){}},60000);
      }).catch(function(e){
        resendBtn.disabled=false;
        setMsg("comm-activate-msg",e.message||"Chưa gửi lại được mã, thử lại sau nhé.");
      });
    });
    var forgot=document.getElementById("comm-forgot-link");
    if(forgot)forgot.addEventListener("click",function(e){
      e.preventDefault();
      var r=document.getElementById("comm-reset");
      if(r)r.style.display="block";
    });
    var resetSend=document.getElementById("comm-reset-send");
    if(resetSend)resetSend.addEventListener("click",function(){
      var email=(document.getElementById("comm-reset-email").value||"").trim().toLowerCase();
      if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){setMsg("comm-reset-msg","Email chưa đúng định dạng.");return;}
      resetSend.disabled=true;
      setMsg("comm-reset-msg","Đang gửi mã…");
      apiCall("/api/auth/send-code",{method:"POST",body:{email:email,purpose:"reset"}}).then(function(){
        resetSend.disabled=false;
        setMsg("comm-reset-msg","Đã gửi mã qua email. Nhập mã và mật khẩu mới bên dưới nhé.");
      }).catch(function(e){
        resetSend.disabled=false;
        setMsg("comm-reset-msg",e.message||"Chưa gửi được mã, thử lại nhé.");
      });
    });
    var resetBtn=document.getElementById("comm-reset-btn");
    if(resetBtn)resetBtn.addEventListener("click",function(){
      var email=(document.getElementById("comm-reset-email").value||"").trim().toLowerCase();
      var code=(document.getElementById("comm-reset-code").value||"").trim();
      var pass=document.getElementById("comm-reset-pass").value||"";
      if(!/^\d{6}$/.test(code)){setMsg("comm-reset-msg","Mã có 6 số nhé.");return;}
      if(pass.length<8){setMsg("comm-reset-msg","Mật khẩu mới ít nhất 8 ký tự.");return;}
      resetBtn.disabled=true;
      setMsg("comm-reset-msg","Đang đặt mật khẩu mới…");
      apiCall("/api/auth/verify",{method:"POST",body:{email:email,code:code,purpose:"reset"}}).then(function(res){
        return apiCall("/api/auth/reset-password",{method:"POST",body:{email:email,reset_token:res.reset_token,new_password:pass}});
      }).then(function(){
        resetBtn.disabled=false;
        setMsg("comm-reset-msg","Đã đặt mật khẩu mới. Đăng nhập lại nhé.");
      }).catch(function(e){
        resetBtn.disabled=false;
        setMsg("comm-reset-msg",e.message||"Đặt mật khẩu chưa được, thử lại nhé.");
      });
    });
  }
  function renderTeaser(){
    var box=document.getElementById("comm-teaser");
    if(!box)return;
    var auth=loadAuth();
    var w=boards.weekly;
    var html="<h3>Đua top tuần này</h3>";
    if(!w){
      html+=boardsLoaded?"<p>Chưa tải được bảng tuần này. Vào trang Cộng đồng để xem nhé.</p>":"<p>Đang tải bảng tuần này…</p>";
    }else if(!(w.entries||[]).length){
      html+="<p>Chưa có ai đua top tuần này. Đăng nhập và học xong 1 bài để lên bảng nhé.</p>";
    }else{
      var top=w.entries.slice(0,3);
      html+="<p>"+top.map(function(r,i){return (i+1)+". "+escapeHtml(r.display_name)+" ("+r.value+" XP)";}).join(" • ")+"</p>";
      if(auth&&w.me)html+="<p>Hạng của bạn tuần này: <b>"+w.me.value+" XP</b>"+(w.me.rank?" (hạng "+w.me.rank+")":"")+".</p>";
      else if(!auth)html+="<p>Đăng nhập để đua top và thấy hạng của bạn.</p>";
    }
    html+="<p><a class=\"btn btn-primary\" href=\""+BASE_PATH_PLACEHOLDER+"/cong-dong/\">Xem bảng đầy đủ →</a></p>";
    box.innerHTML=html;
  }
  function renderAll(){
    renderBoard("board-xp","weekly","Top XP tuần (reset 0 giờ Thứ 2)","XP");
    renderBoard("board-streak","streak","Chuỗi ngày dài nhất","ngày");
    renderBoard("board-speak","speaking","Điểm nói tốt nhất tuần","điểm");
    renderChallenge();
    renderAuth();
    renderTeaser();
    renderStats();
    var note=document.getElementById("comm-offline");
    if(note){
      if(boardsFailed){
        note.style.display="block";
        note.textContent=boardsFromCache?"Đang hiện bảng đã lưu từ lần trước. Kiểm tra mạng rồi tải lại trang để cập nhật.":"Không tải được bảng xếp hạng. Kiểm tra mạng rồi tải lại trang nhé.";
      }else{
        note.style.display="none";
      }
    }
  }
  window.addEventListener("storage",function(e){
    if(e&&e.key==="sdsc-progress-v1")scheduleSync(5000);
  });
  renderAll();
  loadBoards();
  window.__commTest={
    state:function(){return {auth:loadAuth(),hearts:loadHearts(),badges:loadBadges(),challengeDone:challengeProgress(),weeklyXp:weeklyXpLocal(),boardsLoaded:boardsLoaded,boardsFailed:boardsFailed,weekMonday:weekMonday,stats:stats};},
    renderAll:renderAll,
    ready:ready,
    loadBoards:loadBoards,
    syncNow:syncNow,
    toServerProgress:toServerProgress,
    fromServerProgress:fromServerProgress
  };
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


def page_shell(title, description, og_url, og_image, body_html, extra_js="", body_class="", active=None):
    """active: khóa nút chân trang đang xem (home/path/dict/speak/me).
    active=None thì không có thanh dưới (trang bài). active="" thì có thanh
    dưới nhưng không tô nút nào (trang không có tab riêng)."""
    nav = bottomnav_html(active) if active is not None else ""
    cls = ((body_class + " has-nav") if active is not None else body_class).strip()
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
<body class="{cls}">
{body_html}
{nav}
{SHARED_SCRIPTS}{extra_js}
</body>
</html>
"""



HOMEPAGE_JS = r"""
<script>
window.SDSC_TOTAL_LESSONS = __TOTAL_LESSONS__;
const SDSC_HOME_BASE=BASE_PATH_PLACEHOLDER;
/* SDSC_LESSONS và SDSC_PATHS lấy từ data.js (nạp trước khối này). */
function safeRender(fn){try{fn();}catch(e){}}
function dueCount(){
  const p=getProgress();const today=todayISO();let n=0;
  Object.entries(p.review||{}).forEach(([slug,r])=>{
    if(!r||!window.SDSC_LESSONS[slug])return;
    if(!isValidDateStr(r.nextDue))return;
    const L=p.lessons[slug];
    if(!L||!L.done)return;
    if(r.nextDue<=today)n++;
  });
  return n;
}
function renderProgress(){
  const p=getProgress();
  const n=progressDoneCount();
  const total=window.SDSC_TOTAL_LESSONS;
  const due=dueCount();
  const streak=p.streak.count||0;
  const setNum=(id,v)=>{const el=document.getElementById(id);if(el)el.textContent=v;};
  setNum("tile-streak-num",streak+" ngày");
  setNum("tile-done-num",n+" / "+total);
  setNum("tile-due-num",due+" bài");
  const strip=document.getElementById("strip-text");
  if(strip)strip.innerHTML="Học lại từ đầu • <b>"+n+" trên "+total+" bài</b>";
  const sbar=document.getElementById("strip-bar");
  if(sbar)sbar.style.width=(total?Math.round(100*n/total):0)+"%";
  updatePracticeScore();
  renderStreakPills();
}
function heroLesson(){
  const p=getProgress();
  const done=new Set(Object.entries(p.lessons||{}).filter(([,l])=>l&&l.done).map(([s])=>s));
  const order=(window.SDSC_PATHS["hoc-lai-tu-dau"]||[]).filter(s=>window.SDSC_LESSONS[s]);
  let next=order.find(s=>!done.has(s));
  if(!next){
    const all=Object.keys(window.SDSC_LESSONS);
    next=all.find(s=>!done.has(s));
  }
  return next||null;
}
function renderToday(){
  const box=document.getElementById("hero-box");
  if(!box)return;
  const next=heroLesson();
  if(!next){
    box.innerHTML="<p class=\"eyebrow\">BÀI HÔM NAY</p><h1>Bạn đã học hết "+window.SDSC_TOTAL_LESSONS+" bài rồi</h1><p class=\"msub\">Giỏi quá! Hôm nay ôn lại nhé.</p><a class=\"btn btn-primary btn-hero\" href=\"#on-homnay\">Ôn hôm nay</a>";
    return;
  }
  const l=window.SDSC_LESSONS[next];
  if(!l){box.innerHTML="<p class=\"eyebrow\">BÀI HÔM NAY</p><h1>Chưa tải được bài tiếp theo</h1><p class=\"msub\">Thử tải lại trang nhé.</p>";return;}
  const isQuiz=l.type==="Quiz";
  const wrongHtml=isQuiz
    ? "<p class=\"wrong\">"+escapeHtml(l.quiz_q||l.why)+"</p>"
    : "<p class=\"wrong\"><s>"+escapeHtml(l.wrong)+"</s></p>";
  const rightHtml=isQuiz
    ? "<p class=\"right\">Làm quiz để xem đáp án</p>"
    : "<p class=\"right\">✓ "+escapeHtml(l.right)+"</p>";
  const meta="3 phút • "+(l.steps||7)+" bước"+(l.has_ipa?" • Có nghe phát âm":"");
  box.innerHTML="<p class=\"eyebrow\">BÀI HÔM NAY • "+escapeHtml(l.topic)+"</p>"
    +"<h1>"+escapeHtml(l.code)+": "+escapeHtml(l.title)+"</h1>"
    +wrongHtml+rightHtml
    +"<a class=\"btn btn-primary btn-hero\" href=\""+SDSC_HOME_BASE+"/"+next+"/\" onclick=\"sessionSet('sdsc-path','hoc-lai-tu-dau')\">Học ngay</a>"
    +"<p class=\"msub\">"+escapeHtml(meta)+"</p>";
}
function renderMissions(){
  const box=document.getElementById("missions-box");
  if(!box)return;
  const p=getProgress();
  const d=dailyToday(p);
  const xp=typeof p.xpTotal==="number"?p.xpTotal:0;
  const level=xpLevel(xp);
  const inLevel=xpInLevel(xp);
  const ms=missionStatus(p);
  const allDone=ms.every(m=>m.done);
  const descs={
    new:ms[0]&&ms[0].done?"Đã học 1 bài mới hôm nay":"Học 1 bài mới trong lộ trình",
    review:(d.reviewCount||0)>0?"Đã ôn "+(d.reviewCount||0)+" trên 2 bài":"Ôn bài đã đến hạn ôn",
    speak:ms[2]&&ms[2].done?"Đã luyện nói 1 câu hôm nay":"Nói 1 câu ở trang Luyện nói"
  };
  const rows=ms.map((m,i)=>{
    const state=m.done?"done":(m.prog>0?"half":"todo");
    const mark=m.done?"✓":"";
    return "<div class=\"mrow"+(i===0?" first":"")+"\"><span class=\"mcheck "+state+"\">"+mark+"</span><div><h3>"+escapeHtml(m.label)+"</h3><p>"+escapeHtml(descs[m.id]||"")+"</p></div><span class=\"xp\">+"+m.xp+" XP</span></div>";
  }).join("");
  const bonus=allDone?"<p class=\"mreward\"><b>Đã xong cả 3 nhiệm vụ, thưởng thêm 50 XP.</b></p>":"<p class=\"mreward\">Xong cả 3 nhiệm vụ được thưởng thêm 50 XP.</p>";
  box.innerHTML="<div class=\"mhead\"><h2>Nhiệm vụ hôm nay</h2><span class=\"xppill\">★ "+xp+" XP</span></div>"
    +"<div class=\"xpbar\"><i style=\"width:"+Math.round(100*inLevel/200)+"%\"></i></div>"
    +"<p class=\"xpmeta\">Cấp "+level+" • "+inLevel+" trên 200 XP đến Cấp "+(level+1)+"</p>"
    +rows+bonus;
}
function renderContinue(){
  const box=document.getElementById("continue-box");
  if(!box)return;
  const p=getProgress();
  const order=(window.SDSC_PATHS["hoc-lai-tu-dau"]||[]).filter(s=>window.SDSC_LESSONS[s]);
  const done=new Set(Object.entries(p.lessons||{}).filter(([,l])=>l&&l.done).map(([s])=>s));
  const idx=order.findIndex(s=>!done.has(s));
  const rows=[];
  if(idx>=0){
    const slug=order[idx];const l=window.SDSC_LESSONS[slug];
    const prac=Object.keys(p.practice||{}).filter(k=>k.indexOf(slug+":")===0).length;
    const total=(window.SDSC_TOTALS||{})[slug]||0;
    const pct=total?Math.round(100*prac/total):0;
    const state=prac>0?("Đang học • "+prac+" trên "+total+" câu luyện"):"Đang học • Chưa làm câu luyện nào";
    rows.push("<a class=\"row\" href=\""+SDSC_HOME_BASE+"/"+slug+"/\"><span class=\"dot now\">→</span><div style=\"flex:1;min-width:0\"><h3>"+escapeHtml(l.code)+": "+escapeHtml(l.title)+"</h3><p>"+escapeHtml(state)+"</p><div class=\"bar\"><i style=\"width:"+pct+"%\"></i></div></div><span class=\"state\">Học</span></a>");
    if(order[idx+1]){
      const l2=window.SDSC_LESSONS[order[idx+1]];
      rows.push("<a class=\"row\" href=\""+SDSC_HOME_BASE+"/"+order[idx+1]+"/\"><span class=\"dot next\">•</span><div style=\"flex:1;min-width:0\"><h3>"+escapeHtml(l2.code)+": "+escapeHtml(l2.title)+"</h3><p>Tiếp theo trong lộ trình</p></div><span class=\"state\">Xem</span></a>");
    }
  }
  const lastDone=Object.entries(p.lessons||{}).filter(([s,l])=>l&&l.done&&window.SDSC_LESSONS[s]).sort((a,b)=>String(b[1].lastStudiedAt||b[1].doneAt||"").localeCompare(String(a[1].lastStudiedAt||a[1].doneAt||"")))[0];
  if(lastDone){
    const m=window.SDSC_LESSONS[lastDone[0]];
    rows.push("<a class=\"row\" href=\""+SDSC_HOME_BASE+"/"+lastDone[0]+"/\"><span class=\"dot done\">✓</span><div style=\"flex:1;min-width:0\"><h3>"+escapeHtml(m.code)+": "+escapeHtml(m.title)+"</h3><p>Đã nhớ • Ôn lại</p></div><span class=\"state done\">Đã nhớ</span></a>");
  }
  if(!rows.length){box.innerHTML="<p>Chưa có bài nào. Học bài đầu tiên ở khung “Bài hôm nay” nhé.</p>";return;}
  box.innerHTML=rows.join("");
}
function renderLatest(scored,q){
  const box=document.getElementById("latest-box");
  if(!box)return;
  const link=document.getElementById("latest-link");
  const total=window.SDSC_TOTAL_LESSONS;
  const rows=(slugs)=>slugs.map(slug=>{
    const l=window.SDSC_LESSONS[slug];if(!l)return "";
    return "<a class=\"row\" href=\""+SDSC_HOME_BASE+"/"+slug+"/\"><span class=\"dot now\">→</span><div style=\"flex:1;min-width:0\"><h3>"+escapeHtml(l.code)+": "+escapeHtml(l.title)+"</h3><p>"+escapeHtml(l.topic)+" • "+escapeHtml(l.type)+"</p></div><span class=\"state\">Học</span></a>";
  }).join("");
  const setLink=(text,href)=>{if(link){link.textContent=text;link.href=href;}};
  if(q&&scored&&scored.length){
    box.innerHTML=rows(scored.slice(0,3).map(x=>x.lesson.slug));
    setLink("Xem tất cả "+scored.length+" bài cho '"+q+"' →",SDSC_HOME_BASE+"/thu-vien-bai-hoc/?q="+encodeURIComponent(q));
  }else if(q){
    box.innerHTML="<p>Không thấy bài nào khớp. Thử từ khác nhé.</p>";
    setLink("Xem tất cả "+total+" bài →",SDSC_HOME_BASE+"/thu-vien-bai-hoc/");
  }else{
    const newest=Object.keys(window.SDSC_LESSONS).sort((a,b)=>String(window.SDSC_LESSONS[b].date||"").localeCompare(String(window.SDSC_LESSONS[a].date||""))).slice(0,3);
    box.innerHTML=rows(newest);
    setLink("Xem tất cả "+total+" bài →",SDSC_HOME_BASE+"/thu-vien-bai-hoc/");
  }
}
function renderReview(){
  const p=getProgress();
  const today=todayISO();
  const grid=document.getElementById("review-grid");
  const empty=document.getElementById("review-empty");
  if(!grid||!empty)return;
  const sec=document.getElementById("review-section");
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
  const future=Object.entries(p.review||{}).filter(([s,r])=>r&&window.SDSC_LESSONS[s]&&isValidDateStr(r.nextDue)&&r.nextDue>today&&(p.lessons[s]||{}).done).sort((a,b)=>a[1].nextDue.localeCompare(b[1].nextDue));
  if(!items.length){
    if(!future.length){if(sec)sec.style.display="none";return;}
    if(sec)sec.style.display="";
    grid.style.display="none";empty.style.display="block";
    const l=window.SDSC_LESSONS[future[0][0]];
    empty.textContent="Hôm nay chưa có bài đến hạn. Bài ôn gần nhất là "+l.code+": "+l.title+", vào ngày "+fmtDate(future[0][1].nextDue)+".";
    return;
  }
  if(sec)sec.style.display="";
  empty.style.display="none";grid.style.display="grid";
  grid.innerHTML=items.map(x=>{
    const l=window.SDSC_LESSONS[x.slug];
    const sk=skillFor(x.slug);
    const url=SDSC_HOME_BASE+"/"+skillPath(sk)+"?lesson="+encodeURIComponent(x.slug);
    return "<a class=\"review-card\" href=\""+url+"\"><b>"+escapeHtml(l.code)+"</b><span>"+escapeHtml(l.title)+"<br>Đến hạn ôn"+(x.overdue>0?" (quá "+x.overdue+" ngày)":" hôm nay")+" • Ôn bằng "+escapeHtml(SKILL_LABEL[sk])+"</span></a>";
  }).join("");
}
function renderAll(){
  safeRender(renderProgress);safeRender(renderToday);safeRender(renderMissions);safeRender(renderContinue);safeRender(renderReview);
}
window.__sdscRenderProgress=renderAll;
renderAll();
</script>
"""

INDEX_FILTER_JS = r"""
<script>
/* Tìm kiếm + bộ lọc (§2.4): chuẩn hóa không dấu cả hai phía, xếp hạng theo trọng số.
   Chỉ mục tìm kiếm đầy đủ nằm ở search-index.json, CHỈ nạp khi người dùng
   tìm kiếm (19/11). Trước lúc đó dùng chỉ mục gọn dựng từ data.js
   (mã, tiêu đề, lý do, chủ đề, loại, ngày, lộ trình), đủ cho chip đếm,
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
  if(typeof renderLatest==="function"){try{renderLatest(scored,fQ);}catch(e){}}
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
  const c=document.getElementById("cards");if(c)c.style.display=view==="cards"?"grid":"none";
  const t=document.getElementById("tableWrap");if(t)t.style.display=view==="table"?"block":"none";
  const bc=document.getElementById("btnCards");if(bc)bc.classList.toggle("on",view==="cards");
  const bt=document.getElementById("btnTable");if(bt)bt.classList.toggle("on",view==="table");
}
const searchEl=document.getElementById("search");
if(searchEl)searchEl.addEventListener("input",e=>{
  clearTimeout(debounceTimer);
  debounceTimer=setTimeout(()=>{fQ=e.target.value.trim();applyFilters();},150);
});
const bc0=document.getElementById("btnCards");if(bc0)bc0.addEventListener("click",()=>{view="cards";syncView();});
const bt0=document.getElementById("btnTable");if(bt0)bt0.addEventListener("click",()=>{view="table";syncView();});
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
      const today=todayISO();
      const oldReview=pp.review[SLUG];
      const wasDue=oldReview&&isValidDateStr(oldReview.nextDue)&&oldReview.nextDue<=today;
      const wasStudiedToday=LL.lastStudiedAt===today;
      LL.selfGrade=grade;LL.lastStudiedAt=today;LL.reviews=(LL.reviews||0)+1;
      pp.review[SLUG]=srsUpdate(pp.review[SLUG]||srsNew(today),grade,today);
      if(wasDue)countReview(pp,SLUG,wasStudiedToday);
      pushHistory(pp,{date:today,at:new Date().toISOString(),slug:SLUG,action:"review",grade:grade});
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
  if(r&&r.skill){html+="<p>Lần ôn tới luyện bằng <b>"+escapeHtml(SKILL_LABEL[r.skill]||r.skill)+"</b>: <a href=\""+BASE_PATH_PLACEHOLDER+"/"+skillPath(r.skill)+"?lesson="+encodeURIComponent(SLUG)+"\">Mở trang "+escapeHtml(SKILL_LABEL[r.skill]||r.skill)+" →</a></p>";}
  const xp=typeof p.xpTotal==="number"?p.xpTotal:0;
  html+="<p>Điểm kinh nghiệm của bạn: <b>"+xp+" XP (Cấp "+xpLevel(xp)+")</b>.</p>";
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
    const wasStudiedToday=L.lastStudiedAt===today;
    const firstDoneToday=!L.doneAt||L.doneAt!==today;
    const oldReview=p.review[SLUG];
    const wasDue=oldReview&&isValidDateStr(oldReview.nextDue)&&oldReview.nextDue<=today;
    L.done=true;
    if(!L.doneAt)L.doneAt=today;
    L.lastStudiedAt=today;
    if(grade)L.selfGrade=grade;
    p.lessons[SLUG]=L;
    if(!wasDone){
      p.review[SLUG]=srsNew(today);
      p.review[SLUG].skill="listen";p.review[SLUG].skillStep=0;
      if(firstDoneToday){const d=ensureDaily(p);d.newDone=(d.newDone||0)+1;awardXp(p,20);checkDailyBonus(p);}
    }
    else if(grade){p.review[SLUG]=srsUpdate(p.review[SLUG]||srsNew(today),grade,today);L.reviews=(L.reviews||0)+1;if(wasDue)countReview(p,SLUG,wasStudiedToday);}
    updateStreakIn(p,today);
    if(!wasDone||grade){pushHistory(p,{date:today,at:new Date().toISOString(),slug:SLUG,action:wasDone?"self-grade":"done",grade:grade||undefined});}
  });
  __pendingGrade=null;
  renderDone();renderSelfGrade();renderCompleteStreak();renderCompleteSummary();updatePracticeScore();
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

def header_html(site):
    """Đầu trang gọn hướng A: thanh trên 56px, chỉ logo, tên, slogan 1 dòng,
    pill chuỗi ngày. Không còn khối giới thiệu, thống kê hay menu trên."""
    return f"""
<header class="appbar">
  <div class="appwrap">
    <a href="{BASE_PATH}/" aria-label="Trang chủ"><span class="logo">S</span></a>
    <div class="appname"><a href="{BASE_PATH}/">Sai Đâu Sửa Đó</a><small>{esc(site['slogan'])}</small></div>
    <span class="pills"><span class="pill"><span class="pill-word">Chuỗi</span> <span class="streak-pill">0 ngày</span></span></span>
    <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Chế độ tối"></button>
  </div>
</header>"""


# Thanh dưới hướng A: 5 nút cố định, tối thiểu 56px, mục đang xem tô cam.
# Không thêm nút thứ 6 (mục Cộng đồng vào bằng thẻ trên trang chủ và từ tab Tôi).
BOTTOM_NAV = [
    ("home", "Học", "/", "book"),
    ("path", "Lộ trình", "/lo-trinh/hoc-lai-tu-dau/", "map"),
    ("dict", "Từ điển", "/tu-dien/", "search"),
    ("speak", "Luyện nói", "/luyen-noi/", "speaker"),
    ("me", "Tôi", "/bang-lo-trinh/", "user"),
]


def bottomnav_html(active):
    items = ""
    for key, label, href, icon in BOTTOM_NAV:
        on = " on" if key == active else ""
        items += f'<a class="navitem{on}" href="{BASE_PATH}{href}">{ICON[icon]}<span>{esc(label)}</span></a>'
    return f'<nav class="bottomnav" aria-label="Mục chính"><div class="appwrap">{items}</div></nav>'


def topbar_html(title, back_href):
    """Thanh trên trang bài: nút về, mã bài, pill chuỗi ngày. Không bottomnav."""
    return f"""
<header class="topbar">
  <div class="appwrap">
    <a class="back" href="{esc(back_href)}" aria-label="Về trang chủ">←</a>
    <span class="title">{esc(title)}</span>
    <span class="pills"><span class="pill"><span class="pill-word">Chuỗi</span> <span class="streak-pill">0 ngày</span></span></span>
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
    """Dữ liệu bài học cho data.js. Thêm wrong/right/steps/has_ipa/quiz_q để
    trang chủ vẽ được thẻ Bài hôm nay mà không cần nạp thêm file."""
    out = {}
    for l in visible:
        q = l.get("quiz") or {}
        out[l["slug"]] = {
            "code": l["code"],
            "title": l["title"],
            "why": l["why"],
            "topic": l["topic"],
            "type": l["type"],
            "date": l["date"],
            "wrong": l.get("wrong", ""),
            "right": l.get("right", ""),
            "steps": len(lesson_steps(l)),
            "has_ipa": bool(l.get("ipa")),
            "quiz_q": q.get("question", "") if l["type"] == "Quiz" else "",
        }
    return out


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


def render_index(data):
    site = data["site"]
    visible = visible_lessons(data)
    ask_url = site.get("ask_url") or site["facebook_page"]
    body = f"""
{header_html(site)}
<main class="appwrap">
  <section class="hero" id="hero-box">
    <p class="eyebrow">BÀI HÔM NAY</p>
    <h1>Đang tải…</h1>
    <p class="msub">Mở trang bằng trình duyệt có JavaScript để học nhé.</p>
  </section>
  <div class="tiles">
    <div class="tile"><div class="num" id="tile-streak-num">…</div><div class="lbl">Chuỗi ngày</div></div>
    <div class="tile"><div class="num" id="tile-done-num">…</div><div class="lbl">Bài đã nhớ</div></div>
    <div class="tile"><div class="num" id="tile-due-num">…</div><div class="lbl">Đến hạn ôn</div></div>
  </div>
  <a class="strip" href="{BASE_PATH}/lo-trinh/hoc-lai-tu-dau/"><span class="strip-row"><span id="strip-text">Đang tải tiến độ…</span> <span class="go">→</span></span><span class="stripbar"><i id="strip-bar"></i></span></a>
  <section class="missions" id="missions-box">
    <div class="mhead"><h2>Nhiệm vụ hôm nay</h2></div>
    <p>Đang tải…</p>
  </section>
  <section class="comm-card" id="comm-teaser">
    <h3>Đua top tuần này</h3>
    <p>Đang tải…</p>
  </section>
  <section>
    <h2>Học tiếp</h2>
    <div class="rows" id="continue-box"><p>Đang tải…</p></div>
  </section>
  <section>
    <h2>Công cụ học</h2>
    <div class="tools">
      <a class="tool" href="{BASE_PATH}/tu-dien/">{ICON["search"]}<div><b>Từ điển</b><span>Nghĩa tiếng Việt lên đầu</span></div></a>
      <a class="tool" href="{BASE_PATH}/luyen-noi/">{ICON["speaker"]}<div><b>Luyện nói</b><span>Nói câu mẫu, chấm từng từ</span></div></a>
      <a class="tool" href="{BASE_PATH}/luyen-nghe/">{ICON["headphones"]}<div><b>Luyện nghe</b><span>Nghe và bắt lỗi</span></div></a>
      <a class="tool" href="{BASE_PATH}/luyen-viet/">{ICON["pen"]}<div><b>Luyện viết</b><span>Viết lại câu sai thành đúng</span></div></a>
      <a class="tool" href="{BASE_PATH}/luyen-doc/">{ICON["book"]}<div><b>Luyện đọc</b><span>Đọc và săn lỗi</span></div></a>
      <a class="tool" href="{BASE_PATH}/thu-vien-chu-de/">{ICON["cap"]}<div><b>Thư viện chủ đề</b><span>Mọi bài gom theo chủ đề</span></div></a>
    </div>
  </section>
  <section id="review-section">
    <h2 id="on-homnay">Ôn hôm nay <small>Những bài đã đến hạn ôn theo lịch riêng của bạn</small></h2>
    <div class="review-grid" id="review-grid"></div>
    <div class="empty" id="review-empty" style="display:none">Chưa có bài nào để ôn. Học xong 1 bài rồi bấm “Tôi đã nhớ bài này” nhé.</div>
  </section>
  <section>
    <div class="cta-row">
      <a class="btn btn-navy btn-compact" href="{esc(site['facebook_group'])}" target="_blank" rel="noopener">{ICON["users"]} Vào Group</a>
      <a class="btn btn-primary btn-compact" href="{esc(ask_url)}" target="_blank" rel="noopener">{ICON["mail"]} Gửi câu để được sửa</a>
    </div>
  </section>
  <section id="tra-cuu">
    <h2>Tra cứu mọi bài học</h2>
    <form class="toolbar" action="{BASE_PATH}/thu-vien-bai-hoc/" method="get">
      <label class="sr-only" for="search">Tìm bài học</label>
      <input id="search" name="q" type="search" placeholder="Tìm lỗi mình hay mắc… ví dụ: borrow, bored, comfortable" autocomplete="off">
    </form>
    <div class="rows" id="latest-box"><p>Đang tải…</p></div>
    <a class="pathlink" id="latest-link" href="{BASE_PATH}/thu-vien-bai-hoc/">Xem tất cả bài →</a>
  </section>
</main>
{footer_html(site)}
"""
    homepage_js = (
        HOMEPAGE_JS.replace("__TOTAL_LESSONS__", str(len(visible)))
        .replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    )
    index_filter_js = INDEX_FILTER_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    comm_js = COMM_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    return page_shell(
        f"{site['name']}: {site['slogan']}",
        "Học tiếng Anh từ lỗi người Việt hay mắc. 3 lộ trình có thứ tự, mỗi bài 3 đến 5 phút, quiz chấm ngay, nhắc ôn lại. Tra cứu mọi lỗi đã sửa.",
        SITE_URL + "/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=homepage_js + index_filter_js + comm_js,
        active="home",
    )


def render_dict(data):
    site = data["site"]
    visible = visible_lessons(data)
    chips = "".join(
        f'<button type="button" class="chip" data-w="{esc(w)}">{esc(w)}</button>'
        for w in dict_chip_words(visible)
    )
    body = f"""
{header_html(site)}
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
        active="dict",
    )


def render_dashboard(data):
    site = data["site"]
    visible = visible_lessons(data)
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
{header_html(site)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả bài học</a></p>
  <section>
    <h2>Bảng lộ trình</h2>
    {tiles}
    <p class="note">Tiến độ lưu trên trình duyệt này, đổi máy sẽ mất. Muốn giữ lại thì bấm Tải dữ liệu tiến độ (.json) ở cuối trang này để lưu ra máy.</p>
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
  <section>
    <h2>Cộng đồng</h2>
    <p>Đua top tuần này cùng mọi người học: bảng XP tuần, chuỗi ngày, điểm nói tốt nhất tuần, thử thách tuần.</p>
    <p><a class="btn btn-primary" href="{BASE_PATH}/cong-dong/">Xem bảng Cộng đồng →</a></p>
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
    <p>Luyện tập toàn trang: <span class="practice-site-num"></span></p>
    <div class="import-row">
      <button type="button" class="btn btn-ghost" id="btn-export">Tải dữ liệu tiến độ (.json)</button>
      <button type="button" class="btn btn-ghost" id="btn-import">Nhập dữ liệu đã lưu</button>
      <input type="file" id="import-file" accept=".json,application/json" hidden>
      <label><input type="radio" name="import-mode" value="merge" checked> Gộp (mới hơn thắng)</label>
      <label><input type="radio" name="import-mode" value="overwrite"> Ghi đè</label>
      <p id="import-msg"></p>
    </div>
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
        active="me",
    )


def render_library(data):
    site = data["site"]
    visible = visible_lessons(data)
    paths_map = paths_for_lessons(data)
    topics = {}
    for l in visible:
        topics.setdefault(l["topic"], []).append(l)
    order = sorted(topics, key=lambda t: (-len(topics[t]), t))
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
{header_html(site)}
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
        active="",
    )


def render_browse(data):
    site = data["site"]
    visible = visible_lessons(data)
    paths = site["paths"]
    paths_map = paths_for_lessons(data)
    ask_url = site.get("ask_url") or site["facebook_page"]
    path_options = "".join(
        f'<option value="{esc(p["slug"])}">{esc(p["name"])}</option>' for p in paths
    )
    body = f"""
{header_html(site)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Trang chủ</a></p>
  <section id="tra-cuu">
    <h2>Tra cứu mọi bài học</h2>
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
  </section>
</main>
{footer_html(site)}
"""
    index_filter_js = INDEX_FILTER_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"')
    return page_shell(
        "Tra cứu mọi bài học | Kho bài học Sai Đâu Sửa Đó",
        "Tra cứu mọi bài học: tìm theo lỗi mình hay mắc, lọc theo chủ đề, loại bài, lộ trình và trạng thái đã nhớ.",
        SITE_URL + "/thu-vien-bai-hoc/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=index_filter_js,
        active="",
    )


def render_speak(data):
    site = data["site"]
    visible = visible_lessons(data)
    speakable = speakable_sentences(visible)
    weak = weak_words_data(data, limit=5)
    speak_vi = speak_vi_map(speakable)
    speak_data = (
        '<script>window.SDSC_SPEAKABLE='
        + json.dumps(speakable, ensure_ascii=False)
        + ";window.SDSC_WEAK="
        + json.dumps(weak, ensure_ascii=False)
        + ";window.SDSC_SPEAK_VI="
        + json.dumps(speak_vi, ensure_ascii=False)
        + ";window.SDSC_SPEAK="
        + json.dumps(speak_sentences(visible), ensure_ascii=False)
        + ";</script>"
    )
    body = f"""
{header_html(site)}
<main class="appwrap">
  <section>
    <h2>Luyện nói</h2>
    <p class="speak-intro">Nghe câu mẫu, nói lại, máy tô xanh từ nói đúng, đỏ từ chưa đúng. 3 lượt mỗi buổi, xong được 20 XP.</p>
    <p class="note warn" id="speak-nosupport" style="display:none">Trình duyệt này chưa hỗ trợ nhận diện giọng nói. Mở trang bằng Chrome hoặc Edge trên máy tính hoặc điện thoại Android để luyện nói nhé. Safari và iPhone chưa dùng được tính năng này.</p>
  </section>
  <section>
    <h2>Câu của hôm nay</h2>
    <p class="msub2">Câu từ bài hôm nay và 2 bài gần nhất chưa nhớ. Bấm vào 1 câu là vào thẳng lượt 1.</p>
    <div class="speak-cards" id="speak-today"><p>Đang tải…</p></div>
  </section>
  <section>
    <h2>Luyện theo chủ đề</h2>
    <p class="msub2">Chọn 1 chủ đề rồi chọn câu trong đó để luyện.</p>
    <div class="speak-topic" id="speak-topics"><p>Đang tải…</p></div>
    <div id="speak-topic-list" style="display:none"></div>
  </section>
  <section>
    <h2>Từ yếu của bạn</h2>
    <p class="msub2">Những từ hay sai nhất, mỗi từ kèm 1 câu chứa từ đó. Bấm vào từ là luyện câu đó.</p>
    <div class="speak-cards" id="speak-weak"><p>Đang tải…</p></div>
  </section>
  <section class="speak-card" id="speak-card" style="display:none">
    <p class="speak-round" id="speak-round">Lượt 1 trên 3</p>
    <p class="speak-target" id="speak-target">Đang tải câu mẫu…</p>
    <p class="speak-vi" id="speak-vi"></p>
    <p class="speak-source" id="speak-source"></p>
    <div class="chunk-actions">
      <button type="button" class="btn btn-navy" id="speak-listen">Nghe câu mẫu</button>
      <button type="button" class="btn btn-primary" id="speak-start">Bắt đầu nói</button>
      <button type="button" class="btn btn-ghost" id="speak-stop" disabled>Dừng</button>
      <button type="button" class="btn btn-ghost" id="speak-replay" style="display:none">Nghe lại giọng mình</button>
    </div>
    <p id="speak-status">Bấm “Nghe câu mẫu” rồi bấm “Bắt đầu nói” nhé.</p>
    <div class="speak-heard" id="speak-heard"></div>
    <div class="speak-colored" id="speak-colored"></div>
    <div id="speak-score"></div>
    <div class="speak-missed" id="speak-missed"></div>
    <div class="speak-next">
      <button type="button" class="btn btn-primary" id="speak-next" style="display:none">Lượt tiếp theo</button>
      <button type="button" class="btn btn-ghost" id="speak-new">Chọn câu khác</button>
    </div>
    <div id="speak-done" style="display:none"></div>
  </section>
  <section>
    <p id="speak-stats"></p>
    <p><button type="button" class="btn btn-ghost" id="speak-random">Ngẫu nhiên 1 câu</button></p>
    <p class="msub2">Máy chấm theo từ, không chấm từng âm.</p>
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        "Luyện nói | Kho bài học Sai Đâu Sửa Đó",
        "Luyện nói tiếng Anh: nghe câu mẫu, nói lại, máy tô xanh từ nói đúng, đỏ từ chưa đúng. 3 lượt mỗi buổi, xong được 20 XP.",
        SITE_URL + "/luyen-noi/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=speak_data + SPEAK_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"'),
        active="speak",
    )

def render_listen(data):
    site = data["site"]
    visible = visible_lessons(data)
    body = f"""
{header_html(site)}
<main class="appwrap">
  <section>
    <h2>Luyện nghe</h2>
    <p class="skill-intro">Nghe và bắt lỗi. Nghe 1 câu rồi chọn Sai hay Đúng, nghe 2 câu rồi chọn câu nào đúng, nghe câu sai rồi gõ lại thành câu đúng. Nghe xong hiện cả 2 câu cạnh nhau, từ khác nhau được tô vàng.</p>
  </section>
  <section id="listen-start">
    <div class="skill-modes">
      <div class="skill-mode"><b>Nghe 1 câu, chọn Sai hay Đúng</b><span>Nghe 1 câu rồi chọn xem câu đó sai hay đúng.</span></div>
      <div class="skill-mode"><b>Nghe 2 câu, chọn câu nào đúng</b><span>Nghe 2 câu liên tiếp rồi chọn câu đúng trong 2 câu.</span></div>
      <div class="skill-mode"><b>Nghe câu sai, gõ lại thành câu đúng</b><span>Nghe câu sai rồi gõ lại thành câu đúng, máy chấm theo từng từ.</span></div>
    </div>
    <p><button type="button" class="btn btn-primary" id="listen-begin">Bắt đầu luyện nghe</button></p>
    <p class="msub2">Mỗi buổi 6 câu, xong được 20 XP.</p>
  </section>
  <section class="skill-card" id="listen-card" style="display:none">
    <p class="skill-round" id="listen-round">Câu 1 trên 6</p>
    <p id="listen-prompt"></p>
    <div id="listen-play"></div>
    <div class="skill-choices" id="listen-choices"></div>
    <div id="listen-type" style="display:none">
      <label class="sr-only" for="listen-input">Gõ lại thành câu đúng</label>
      <input class="skill-answer" id="listen-input" type="text" placeholder="Gõ lại thành câu đúng…" autocomplete="off">
      <p><button type="button" class="btn btn-primary" id="listen-check">Kiểm tra</button></p>
    </div>
    <div class="skill-feedback" id="listen-feedback"></div>
    <p><button type="button" class="btn btn-primary" id="listen-next" style="display:none">Câu tiếp theo</button></p>
    <p class="skill-progress" id="listen-progress"></p>
  </section>
  <section class="skill-done" id="listen-done" style="display:none"></section>
  <section>
    <p id="listen-stats"></p>
  </section>
</main>
{footer_html(site)}
"""
    skills_js = '<script src="' + BASE_PATH + '/skills.js"></script>'
    return page_shell(
        "Luyện nghe | Kho bài học Sai Đâu Sửa Đó",
        "Luyện nghe tiếng Anh: nghe và bắt lỗi, nghe 1 câu chọn Sai hay Đúng, nghe 2 câu chọn câu nào đúng, nghe câu sai rồi gõ lại thành câu đúng.",
        SITE_URL + "/luyen-nghe/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=skills_js + LISTEN_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"'),
        active="",
    )


def render_write(data):
    site = data["site"]
    visible = visible_lessons(data)
    body = f"""
{header_html(site)}
<main class="appwrap">
  <section>
    <h2>Luyện viết</h2>
    <p class="skill-intro">Viết lại câu sai thành câu đúng. Máy so từng từ, tô màu từ đúng, từ thừa, từ thiếu, từ sai chính tả, rồi hiện lời giải thích vì sao đã có trong bài.</p>
  </section>
  <section id="write-start">
    <div class="skill-modes">
      <div class="skill-mode"><b>Viết lại câu sai thành câu đúng</b><span>Hiện câu sai, gõ lại thành câu đúng.</span></div>
      <div class="skill-mode"><b>Dịch từ tiếng Việt sang câu đúng</b><span>Hiện nghĩa tiếng Việt, dịch sang câu tiếng Anh đã học.</span></div>
      <div class="skill-mode"><b>Điền từ còn thiếu</b><span>Câu đúng bị khuyết 1 từ, điền từ còn thiếu vào chỗ trống.</span></div>
    </div>
    <p><button type="button" class="btn btn-primary" id="write-begin">Bắt đầu luyện viết</button></p>
    <p class="msub2">Mỗi buổi 3 câu, xong được 20 XP.</p>
  </section>
  <section class="skill-card" id="write-card" style="display:none">
    <p class="skill-round" id="write-round">Câu 1 trên 3</p>
    <div id="write-prompt"></div>
    <p class="skill-source" id="write-source"></p>
    <label class="sr-only" for="write-input">Viết câu trả lời</label>
    <input class="skill-answer" id="write-input" type="text" placeholder="Viết câu trả lời…" autocomplete="off">
    <p><button type="button" class="btn btn-primary" id="write-check">Kiểm tra</button></p>
    <div class="skill-feedback" id="write-feedback"></div>
    <p><button type="button" class="btn btn-primary" id="write-next" style="display:none">Câu tiếp theo</button></p>
    <p class="skill-progress" id="write-progress"></p>
  </section>
  <section class="skill-done" id="write-done" style="display:none"></section>
  <section>
    <h2>Lỗi tôi hay viết sai</h2>
    <p class="msub2">Câu nào bạn gõ sai nhiều lần sẽ tự vào đây, lần sau ôn lại đúng câu đó.</p>
    <div class="write-wrong-list" id="write-wrong"><p>Đang tải…</p></div>
  </section>
  <section>
    <p id="write-stats"></p>
  </section>
</main>
{footer_html(site)}
"""
    skills_js = '<script src="' + BASE_PATH + '/skills.js"></script>'
    return page_shell(
        "Luyện viết | Kho bài học Sai Đâu Sửa Đó",
        "Luyện viết tiếng Anh: viết lại câu sai thành câu đúng, dịch từ tiếng Việt sang câu đúng, điền từ còn thiếu. Máy chấm theo từng từ.",
        SITE_URL + "/luyen-viet/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=skills_js + WRITE_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"'),
        active="",
    )


def render_read(data):
    site = data["site"]
    visible = visible_lessons(data)
    passages = load_reading()
    read_data = (
        '<script>window.SDSC_READ_VI='
        + json.dumps(read_vi_map(passages), ensure_ascii=False)
        + ";</script>"
    )
    body = f"""
{header_html(site)}
<main class="appwrap">
  <section>
    <h2>Luyện đọc</h2>
    <p class="skill-intro">Đọc và săn lỗi. Đoạn văn ngắn 3 đến 5 câu về tình huống đời thường, giấu 1 lỗi đúng kiểu bài vừa học. Bấm vào câu nghi là sai rồi chọn cách sửa. Bấm vào 1 từ để xem nghĩa tiếng Việt ngay.</p>
  </section>
  <section id="read-start">
    <p><button type="button" class="btn btn-primary" id="read-begin">Bắt đầu luyện đọc</button></p>
    <p class="msub2">Mỗi buổi 3 đoạn, xong 1 đoạn được 20 XP. Cấp độ đọc tự điều chỉnh theo điểm của bạn.</p>
    <p class="read-level" id="read-level"></p>
  </section>
  <section class="skill-card" id="read-card" style="display:none">
    <p class="skill-round" id="read-progress"></p>
    <p class="skill-source" id="read-situation"></p>
    <p class="skill-source" id="read-source"></p>
    <div class="read-passage" id="read-passage"></div>
    <div class="read-word-pop" id="read-wordpop"></div>
    <div id="read-fix"></div>
    <div id="read-question"></div>
    <div class="skill-feedback" id="read-feedback"></div>
    <p><button type="button" class="btn btn-primary" id="read-next" style="display:none">Đoạn tiếp theo</button></p>
  </section>
  <section class="skill-done" id="read-done" style="display:none"></section>
  <section>
    <p id="read-stats"></p>
  </section>
</main>
{footer_html(site)}
"""
    reading_js = '<script src="' + BASE_PATH + '/reading.js"></script>'
    return page_shell(
        "Luyện đọc | Kho bài học Sai Đâu Sửa Đó",
        "Luyện đọc tiếng Anh: đọc đoạn văn ngắn và săn lỗi, bấm từ hiện nghĩa, cấp độ đọc tự điều chỉnh theo điểm.",
        SITE_URL + "/luyen-doc/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=reading_js + read_data + READ_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"'),
        active="",
    )

def render_community(data):
    site = data["site"]
    visible = visible_lessons(data)
    body = f"""
{header_html(site)}
<main class="appwrap">
  <section>
    <h2>Cộng đồng</h2>
    <p class="skill-intro">Đua top tuần này cùng mọi người học. Bảng xếp hạng reset 0 giờ Thứ 2 hàng tuần. Tham gia tự động khi đã đăng nhập, không cần bấm tham gia.</p>
    <p class="comm-note" id="comm-stats">Đang tải thống kê…</p>
    <p class="comm-note" id="comm-offline" style="display:none">Đang tải bảng xếp hạng…</p>
  </section>
  <section class="comm-card" id="comm-challenge"><p>Đang tải thử thách tuần…</p></section>
  <section class="comm-card" id="board-xp"><p>Đang tải bảng Top XP tuần…</p></section>
  <section class="comm-card" id="board-streak"><p>Đang tải bảng chuỗi ngày…</p></section>
  <section class="comm-card" id="board-speak"><p>Đang tải bảng điểm nói…</p></section>
  <section class="comm-card" id="comm-auth"><p>Đang tải tài khoản…</p></section>
  <section>
    <p><a class="btn btn-navy" href="{esc(site['facebook_group'])}" target="_blank" rel="noopener">{ICON["users"]} Vào Group Cộng đồng Sai Đâu Sửa Đó</a></p>
    <p class="comm-note">Thứ 2 tuần sau, Trang đăng kết quả lên Group: top 3 bảng XP tuần, tên thử thách tuần mới, lời mời vào web. Chỉ đăng tên hiển thị của top 3 trên bảng.</p>
  </section>
</main>
{footer_html(site)}
"""
    return page_shell(
        "Cộng đồng | Kho bài học Sai Đâu Sửa Đó",
        "Cộng đồng Sai Đâu Sửa Đó: đua top tuần, thử thách tuần, bảng xếp hạng XP, chuỗi ngày và điểm nói.",
        SITE_URL + "/cong-dong/",
        SITE_URL + "/images/loi-001.jpg",
        body,
        extra_js=COMM_JS.replace("BASE_PATH_PLACEHOLDER", f'"{BASE_PATH}"'),
        active="",
    )

def render_path(data, path):
    site = data["site"]
    visible = visible_lessons(data)
    by_slug = {l["slug"]: l for l in visible}
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
{header_html(site)}
<main class="wrap">
  <p style="margin:16px 0 0"><a class="back" href="{BASE_PATH}/">← Tất cả lộ trình</a></p>
  <section>
    <h2>{esc(path['name'])} <small>{len(listed)} bài, mỗi bài 3 đến 5 phút</small></h2>
    <p>{esc(path['desc'])}</p>
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
        active="path",
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


SPEAK_STOPWORDS = {
    "a", "an", "the", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "can", "could",
    "shall", "should", "may", "might", "must",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "and", "or", "but", "if", "then", "than", "so", "very", "not", "no", "yes",
    "this", "that", "these", "those", "there", "here",
    "what", "when", "where", "who", "whom", "which", "why", "how",
    "all", "any", "some", "each", "every", "both", "either", "neither",
    "one", "two",
}


def speakable_sentences(visible):
    """Câu luyện nói đạt chuẩn: câu right từ 4 từ trở lên, chỉ chứa chữ cái
    tiếng Anh. Không loại trùng (2 bài có thể chung 1 câu, mỗi bài 1 thẻ)."""
    out = []
    for l in visible:
        right = l.get("right", "")
        words = re.findall(r"[A-Za-z']+", right)
        if len(words) < 4:
            continue
        alpha = "".join(c for c in right if c.isalpha())
        if not alpha.isascii():
            continue
        out.append({
            "en": right,
            "vi": l.get("right_note", ""),
            "code": l["code"],
            "slug": l["slug"],
            "topic": l.get("topic", ""),
            "title": l.get("title", ""),
            "words": len(words),
            "level": "Ngắn" if len(words) <= 6 else "Vừa",
        })
    return out


def speak_vi_map(sentences):
    """Nghĩa tiếng Việt cho từng từ trong câu luyện nói, lấy từ bảng nghĩa.
    Chỉ lấy nghĩa đầu tiên của mỗi từ, để nhúng gọn vào trang Luyện nói."""
    glossary = parse_vi_glossary()
    words = set()
    for s in sentences:
        for w in re.findall(r"[A-Za-z']+", s["en"]):
            words.add(w.lower())
    out = {}
    for w in sorted(words):
        senses = glossary.get(w)
        if senses and senses[0] and len(senses[0]) >= 2 and senses[0][1]:
            out[w] = senses[0][1]
    return out


def weak_words_data(data, limit=5):
    """Từ yếu: từ nội dung có gắn nhiều bài học nhất qua trường mistakes.
    Mỗi từ kèm 1 câu đạt chuẩn chứa từ đó, ưu tiên câu của 1 bài gắn với từ."""
    visible = visible_lessons(data)
    speakable = speakable_sentences(visible)
    by_slug = {s["slug"]: s for s in speakable}
    mistakes = word_mistake_slugs(data)
    glossary = parse_vi_glossary()
    ranked = []
    for w, slugs in mistakes.items():
        if not slugs or w.lower() in SPEAK_STOPWORDS:
            continue
        ranked.append((w, slugs))
    ranked.sort(key=lambda kv: (-len(kv[1]), kv[0]))
    out = []
    for w, slugs in ranked:
        if len(out) >= limit:
            break
        pat = re.compile(r"\b" + re.escape(w) + r"\b", re.I)
        sentence = None
        for slug in slugs:
            s = by_slug.get(slug)
            if s and pat.search(s["en"]):
                sentence = s
                break
        if sentence is None:
            for s in speakable:
                if pat.search(s["en"]):
                    sentence = s
                    break
        if sentence is None:
            continue
        senses = glossary.get(w.lower())
        meaning = senses[0][1] if senses and senses[0] and len(senses[0]) >= 2 else ""
        out.append({"word": w, "meaning": meaning, "slugs": slugs, "sentence": sentence})
    return out


def skills_js_content(visible):
    """Dữ liệu cho 4 trang kỹ năng: câu sai, câu đúng, cặp lỗi, ví dụ,
    giải thích của từng bài. Chỉ nạp ở trang kỹ năng, không nạp ở trang chủ."""
    out = {}
    for l in visible:
        out[l["slug"]] = {
            "code": l["code"],
            "title": l["title"],
            "topic": l.get("topic", ""),
            "type": l["type"],
            "wrong": l.get("wrong", ""),
            "right": l.get("right", ""),
            "why": l.get("why", ""),
            "right_note": l.get("right_note", ""),
            "mistakes": [{"wrong": m.get("wrong", ""), "right": m.get("right", "")}
                         for m in l.get("mistakes", [])],
            "examples": [{"en": e.get("en", ""), "vi": e.get("vi", "")}
                         for e in l.get("examples", [])],
        }
    return "window.SDSC_SKILLS=" + json.dumps(out, ensure_ascii=False) + ";\n"


def load_reading():
    """Đoạn văn đọc (63 đoạn, soạn tay từ dữ liệu bài học). Trả về [] nếu
    chưa có file, trang Luyện đọc hiện dòng chưa có đoạn văn."""
    p = ROOT / "reading.json"
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        passages = raw.get("passages", []) if isinstance(raw, dict) else []
        return [x for x in passages if isinstance(x, dict) and x.get("slug")]
    except Exception as e:
        print("không đọc được reading.json:", e)
        return []


def reading_js_content(passages):
    return "window.SDSC_READING=" + json.dumps(passages, ensure_ascii=False) + ";\n"


def read_vi_map(passages):
    """Nghĩa tiếng Việt cho từ trong đoạn văn đọc, lấy từ bảng 852 từ.
    Tái dùng speak_vi_map bằng cách đưa câu trong đoạn văn vào dạng câu."""
    sentences = []
    for p in passages:
        for s in p.get("sentences", []):
            if s.get("text"):
                sentences.append({"en": s["text"]})
    return speak_vi_map(sentences)


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
    n_steps = len(lesson_steps(lesson))
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
{topbar_html(f"{lesson['code']}: {lesson['title']}", f"{BASE_PATH}/")}
<main class="wrap">
  <div class="wiz-progress"><div class="wiz-bar"><i id="wizFill"></i></div><span id="wizLabel">Bước 1</span></div>
  <section class="lesson">
    <div class="tags" style="margin:6px 0 10px">
      <span class="tag topic">{esc(lesson['topic'])}</span>
      <span class="tag">{esc(fmt_date(lesson['date']))}</span>
    </div>
    <h2 style="font-size:23px;line-height:1.3">{esc(lesson['code'])}: {esc(lesson['title'])}</h2>
    {lesson_body(lesson)}
    <p class="xphint">★ Xong {n_steps} bước được <b>20 XP</b>, cộng vào Nhiệm vụ hôm nay.</p>
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
        "# Kho bài học Sai Đâu Sửa Đó: Content engine học tiếng Anh mở",
        "",
        "Học tiếng Anh từ lỗi người Việt hay mắc. Mỗi ngày sửa một lỗi nhỏ.",
        "",
        f"- **{len(visible)} bài học** hiển thị trên web • **{len(data['lessons'])} bài** trong API • **{n_words} từ** trong từ điển • **{len(site['paths'])} lộ trình** • **{n_reels} Reel** đính kèm trong bài",
        "- Trang mới: **Từ điển** (/tu-dien/), **Bảng lộ trình** (/bang-lo-trinh/), "
        "**Thư viện chủ đề** (/thu-vien-chu-de/), **Luyện nói** (/luyen-noi/), "
        "**Luyện nghe** (/luyen-nghe/), **Luyện viết** (/luyen-viet/), **Luyện đọc** (/luyen-doc/), "
        "**Cộng đồng** (/cong-dong/). "
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
        "Trang này chạy bằng GitHub Pages, sinh từ `lessons.json`.",
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
    body = body.replace("__HEADER__", header_html(site))
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
        active="",
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
             SITE_URL + "/thu-vien-chu-de/", SITE_URL + "/thu-vien-bai-hoc/", SITE_URL + "/luyen-noi/"]
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
    keep_dirs = vis_slugs | {"tu-dien", "bang-lo-trinh", "thu-vien-chu-de", "thu-vien-bai-hoc", "luyen-noi",
                             "luyen-nghe", "luyen-viet", "luyen-doc", "cong-dong", "api"}
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
    # Dữ liệu cho 4 trang kỹ năng (đợt hướng A): câu sai/câu đúng từng bài
    # và đoạn văn đọc. Chỉ nạp ở trang kỹ năng, không nạp ở trang chủ.
    changed += write_if_changed(ROOT / "skills.js", skills_js_content(visible))
    changed += write_if_changed(ROOT / "reading.js", reading_js_content(load_reading()))
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
                       ("thu-vien-bai-hoc", render_browse(data)),
                       ("luyen-noi", render_speak(data)),
                       ("luyen-nghe", render_listen(data)),
                       ("luyen-viet", render_write(data)),
                       ("luyen-doc", render_read(data)),
                       ("cong-dong", render_community(data))):
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
          f" + 3 trang kỹ năng (luyện nghe, luyện viết, luyện đọc)"
          f" + API mở ({len(data['lessons'])} file chi tiết bài, từ điển {len(parse_vi_glossary())} từ)"
          f" — đổi {changed} file")


if __name__ == "__main__":
    main()
