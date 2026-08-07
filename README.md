# CS3264 course website

Static site — plain HTML and CSS, no build step, no dependencies. Edit `index.html`
and push; GitHub Pages serves it as-is.

```
website/
├── index.html      the whole site (one page, anchored sections)
├── style.css       palette and type, matched to the lecture deck
├── .nojekyll       stops GitHub Pages running Jekyll over the files
├── slides/         lecture decks (see "Publishing slides" below)
└── README.md
```

---

## Before it goes public — things only you can confirm

The schedule, term dates and venues come from the AY26/27 calendar, NUSMods and
`../CS3264-Materials/Syllabus.xlsx`, so they are as good as the sources. These are not:

| Item | Where | Status |
|---|---|---|
| **Piazza URL** | hero button, announcement, footer | Guessed as `piazza.com/nus.edu.sg/fall2026/cs3264`. Dead until you create the class — replace with the real one. |
| **Assessment weights** 30/10/20/40 | `#assessment` | Carried over from AY25/26. Confirm before students read it. |
| **Assignment dates** | `#assessment` | Marked **TBC** on the page. Fill in when decided. |
| **Final exam 25 Nov, 5–7pm** | `#assessment`, schedule | From NUSMods; the page says it is provisional. Confirm against the official exam timetable. |
| **Tutorial slot count** (five) | `#policies` | T03 closed; Shashank T06/T01/T02, Oscar T04/T05. Further merging depends on post-add/drop numbers. |
| **Week 13 topic + cover** | `#schedule` reads "optional topic — TBA" | Guest lecturer vs pre-record — decide by early October, then fill the title in here, on slides 44 and 53, and in `Syllabus.xlsx`. |

Anything marked TBC on the page uses the `.tbc` badge, so it is easy to grep for:

```bash
grep -n 'class="tbc"' website/index.html
```

---

## Publishing it

`cs3264` is currently **available** as a GitHub organisation name, so the URL you wanted
is achievable. Two options:

### Option A — `https://cs3264.github.io` (recommended)

A GitHub **organisation** site. Slightly more setup, but it is the clean URL, it survives
you changing accounts, and you can add TAs as members without giving them access to
anything else.

1. Create an organisation named `cs3264` (github.com → **+** → New organization → Free).
2. Inside it, create a **public** repo named exactly `cs3264.github.io`.
3. Push the contents of this folder to the repo root:

```bash
cd website && git init -b main && git add -A && git commit -m "CS3264 course site" && git remote add origin git@github.com:cs3264/cs3264.github.io.git && git push -u origin main
```

4. Settings → Pages → Source: **Deploy from a branch**, branch `main`, folder `/ (root)`.

Live within a minute or two at `https://cs3264.github.io`.

### Option B — `https://haroldsoh.com/cs3264` (recommended if the slides stay on Canvas)

A **project repo** under your own account. No organisation needed: create a public repo
named `cs3264`, push this folder, enable Pages the same way.

```bash
cd website && git init -b main && git add -A && git commit -m "CS3264 course site" && git remote add origin git@github.com:haroldsoh/cs3264.git && git push -u origin main
```

Note the URL. `haroldsoh.github.io` 301-redirects to `haroldsoh.com`, i.e. the user site
repo has a CNAME. GitHub serves project sites from the user site's custom domain, so this
repo lands at **`haroldsoh.com/cs3264`**, not `haroldsoh.github.io/cs3264`.

**It cannot break the existing site.** A project repo is a separate repo with its own
Pages deployment; nothing in `haroldsoh/haroldsoh.github.io` is touched. The only shared
thing is the URL namespace — if the Jekyll site ever gains its own `/cs3264/` page, this
repo wins. It has no such page today.

Both options work with the site as written — every path is relative, so nothing breaks at
a subpath.

---

## Adding a lecture's slides

The decks are self-contained HTML. To publish one:

```bash
mkdir -p website/slides && cp "../CS3264-Materials/Lectures/Lecture 01 - Intro to CS3264 (web).html" website/slides/lecture-01.html && cp -R "../CS3264-Materials/Lectures/media" website/slides/media && rm -f website/slides/media/atlas.mp4
```

The schedule already links to `slides/lecture-01.html`.

There are two builds of Lecture 1:

| File | Boston Dynamics clip | Use |
|---|---|---|
| `Lecture 01 - Intro to CS3264.html` | re-hosted `media/atlas.mp4` | lecturing — fully offline |
| `Lecture 01 - Intro to CS3264 (web).html` | click-to-load YouTube embed | publishing |

The web build is **generated**, not hand-maintained: edit the master, then re-run

```bash
python3 "AY26-27S1/CS3264-Materials/Lectures/make-web-variant.py"
```

It needs a network connection for that one video and nothing else; the KaTeX fonts,
figures and demos are all still local. Publish the web build and you can leave
`media/atlas.mp4` out of the copy entirely (2.4 MB saved).

**Check this before you push.** The web build settles the largest item, not all of them.
The deck embeds third-party material. Teaching use is not
one blanket permission — what matters is who can reach it. Showing these in LT15, or
posting the deck on Canvas, sits inside the education exceptions, which are written around
material supplied to *enrolled students*. A public URL is communication to the public and
is judged on the general fair-use factors instead, where "it's for a class" is one factor
among four rather than an answer.

The practical risk is a DMCA notice to GitHub (US-hosted, so US process applies wherever
you are), which disables the repo. Ranked by exposure:

| Asset | Risk | Fix |
|---|---|---|
| ~~Boston Dynamics clip~~ | **resolved** in the web build | Now the rights-holder's own YouTube player — not a copy, so the question does not arise. |
| `llm.mp4` (the GPT-5 clip) | Same problem, still re-hosted | Same fix if you want it: give me the source URL and I will add it to the generator. |
| Statista chart | High — their licence forbids redistribution and they enforce it | Redraw from the underlying source data. Facts are not copyrightable, only that particular rendering. |
| Figures from papers | Low in an academic context, with citation | Cite properly; check the publisher's reuse terms if it matters. |
| Netflix mark | Low — trademark, and this is nominative use | Leave it. |

So: publish the web build and, if you want the remaining rows dealt with too, either swap
them out or keep the deck on **Canvas** and point the schedule links there instead.

NUS Libraries has a copyright team and institutional licences that may cover more than the
bare statutory exceptions — they are the authority for your situation, not this file.

The `media/` folder is ~8 MB, which is fine for Pages (1 GB soft limit).

---

## Editing

Everything is in `index.html`, in the order it appears on the page. The parts that change
most often:

| What | Where |
|---|---|
| Announcements | `<section id="announcements">` — newest first, copy an `.ann` block |
| Weekly topics, slide links | the `<table class="sched">` rows |
| Dates, assessment weights | `<section id="assessment">` |
| Staff | `<section id="staff">` |

The site follows the reader's system light/dark setting; the **◑** button in the nav
overrides it and remembers the choice.

## Keeping it in sync with the deck

`style.css` deliberately uses the same palette and typefaces as the lecture deck
(`--accent: #9B2C2C` on `--bg: #FBF7EF`, Iowan Old Style / Palatino). If you restyle one,
restyle the other so the course reads as one thing.
