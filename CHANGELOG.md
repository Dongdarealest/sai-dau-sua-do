# Changelog

## 2026-11-19

- Split the repository into two branches: `main` holds source code and documentation, `gh-pages` serves the generated site. All URLs unchanged.
- Published public API v1: lessons, an 852-word dictionary with linked common mistakes, learning paths, documentation, and open licenses.
- Removed internal working documents from `main`; `docs/` now holds the API specification only.
- Rewrote public documentation (README, CONTRIBUTING, CHANGELOG) in English, in a neutral technical tone.

## 2026-11-15

- Performance: split shared CSS, JavaScript, and data into separate files; incremental builds and deploys; lazy-loaded search index. Adding one lesson now changes about 9 files instead of 67.
