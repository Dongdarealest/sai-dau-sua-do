# Contributing to Sai Đâu Sửa Đó

## Reporting a data error

Open an issue with the lesson code (for example, Lỗi #009), the incorrect sentence, the proposed correction, and the source (Cambridge or Oxford Learner's Dictionaries). Only corrections verified against a dictionary are accepted.

## Proposing a new lesson

Open an issue with a mistake Vietnamese speakers commonly make, the wrong sentence, the correct sentence, an explanation in Vietnamese, and two example sentences with Vietnamese translations. The mistake must occur in real life or at work.

## Content rules

1. Every English sentence has a Vietnamese translation directly below it.
2. Pronunciation (IPA) comes from Cambridge or Oxford only, with the accent (American or British) stated. If unsure, leave it out.
3. No hyphens in display text. Use commas, periods, colons, or split the sentence. Write number ranges in words. Use a colon in titles.
4. No political, religious, or medical content. No promises about learning outcomes.
5. No personal information about other people.

## Contributing code

Changes go through pull requests. Describe the change and how it was verified. Run the full test suite before submitting. One pull request per change, with a descriptive commit message.

```sh
cd web
python3 -m unittest discover -s tests -v
bash tests/check_js.sh
cd tests
npm install jsdom --no-save   # first run only
node test_browser_be.js
node test_new_pages_be.js
```
