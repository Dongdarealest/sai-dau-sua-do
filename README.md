# Sai Đâu Sửa Đó

An open English lesson library for Vietnamese learners. Fix one small mistake every day.

Live site: https://dongdarealest.github.io/sai-dau-sua-do/

Each lesson covers one mistake Vietnamese speakers commonly make: the wrong sentence, the correct sentence, a short explanation in Vietnamese, and practice questions with answers. The library holds 64 lessons, 852 dictionary entries, and 3 learning paths.

The site is a learning app, not just a list of pages. Four skills (speaking, listening, writing, reading) practise one mistake at a time, with daily tasks, XP and levels, three learning paths, and review after 1, 3, 7, and 30 days.

Community: [Facebook page](https://www.facebook.com/saidausuado) and [study group](https://www.facebook.com/groups/4387154551501983).

## Open API

All lesson and dictionary data is available as static JSON. No key, no sign-up, no fee. Documentation: https://dongdarealest.github.io/sai-dau-sua-do/api/

```js
const BASE = "https://dongdarealest.github.io/sai-dau-sua-do/api/v1/";
const data = await (await fetch(BASE + "lessons.json")).json();
console.log(data.lessons.length, "lessons");
```

## Run locally

The site is generated from `web/lessons.json` by `web/generate_site.py`:

```sh
cd web
python3 generate_site.py
```

Then serve the `web/` directory with any static file server. Internal links use the `/sai-dau-sua-do` base path.

## License

Code: MIT, see LICENSE. Lesson content and dictionary: CC BY 4.0, see LICENSE-CONTENT.md. Reuse requires attribution with a link to the site. The name, logo, and slogan are not covered by the open licenses.

## Contributing

See CONTRIBUTING.md.
