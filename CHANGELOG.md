# Changelog

## 2026-11-19

- Split the repository into two branches: `main` holds source code and documentation, `gh-pages` serves the generated site. All URLs unchanged.
- Published public API v1: lessons, an 852-word dictionary with linked common mistakes, learning paths, documentation, and open licenses.
- Removed internal working documents from `main`; `docs/` now holds the API specification only.
- Rewrote public documentation (README, CONTRIBUTING, CHANGELOG) in English, in a neutral technical tone.
- Learning app: compact header, five bottom tabs, daily tasks with XP and levels, and a leaderboard card on the home page.
- Four skills: speaking v2, listening, writing, and reading, built around one mistake at a time, with review after 1, 3, 7, and 30 days.
- Dictionary rebuilt: Vietnamese meaning first and largest, with Vietnamese part-of-speech labels.
- Community backend live: password accounts, email codes, weekly XP, streak, and speaking leaderboards, cheers, and stats at https://sdsc-community-api.vercel.app.
- Performance: split shared CSS, JavaScript, and data into separate files; incremental builds and deploys; lazy-loaded search index. Adding one lesson now changes about 9 files instead of 67.
