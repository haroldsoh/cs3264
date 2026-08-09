# CS3264 course website

Static site — plain HTML and CSS, no build step, no dependencies. Edit `index.html`
and push; GitHub Pages serves it as-is.

```
website/
├── index.html      the whole site (one page, anchored sections)
├── style.css       palette and type, matched to the lecture deck
├── .nojekyll       stops GitHub Pages running Jekyll over the files
├── notes/          past years' collaborative notes (PDF)
├── slides/         lecture decks (see "Publishing slides" below)
└── README.md
```

---

## Before it goes public — things only you can confirm

The schedule, term dates and venues come from the AY26/27 calendar, NUSMods and
`../CS3264-Materials/Syllabus.xlsx`, so they are as good as the sources. These are not:

| Item | Where | Status |
|---|---|---|
| **Piazza URL** | hero button, announcement, footer | Set to `piazza.com/nus.edu.sg/fall2025/cs3264` as supplied. Piazza serves an identical landing page for any term slug, so this could not be verified from outside — click it once and confirm it lands on the right class. |
| **Assignments — everything** | `#assessment`, deck slides 47/48/55 | Number, format and dates are all open; the page and both decks say "still being planned". Minghao is leading the design. |
| **Final exam 25 Nov, 5–7pm** | `#assessment`, schedule, key dates | Looks right, but marked **Provisional** on the page in all three places. Drop the badges once the official NUS exam timetable confirms it. |
| **Tutorial slot count** (five) | `#policies` | T03 closed; Shashank T06/T01/T02, Oscar T04/T05. Further merging depends on post-add/drop numbers. |
| **Week 13 topic + cover** | `#schedule` reads "optional topic — TBA" | Guest lecturer vs pre-record — decide by early October, then fill the title in here, on slides 44 and 53, and in `Syllabus.xlsx`. |

Anything marked TBC on the page uses the `.tbc` badge, so it is easy to grep for:

```bash
grep -n 'class="tbc"' website/index.html
```

---

## Publishing it

Live at **`https://cs3264.github.io`** — a GitHub **organisation** site, so the course
owns its own URL and nothing touches `haroldsoh.com`.

### One-time setup

1. Create an organisation named `cs3264` (github.com → **+** → New organization → Free).
2. Inside it, create a **public** repo named exactly `cs3264.github.io`, with no README,
   .gitignore or licence — it must be empty.
3. Push (see below).
4. Repo **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**.

Live within a minute or two. Add the TAs as org members if they should be able to edit;
that gives them this repo and nothing else.

### Deploying — `git subtree`, not a nested repo

This folder is **not** its own repository; the git dir is at `AY26-27S1/`. Do not run
`git init` in here — that nests a second repo inside the first. Push the subfolder
instead:

```bash
cd "AY26-27S1" && git subtree push --prefix=website cs3264 main
```

The `cs3264` remote is already configured (`git@github.com:cs3264/cs3264.github.io.git`).
That one command is also the update path — commit to `website/` as normal, then re-run it.

**Why subtree and not a plain push.** The parent repo also tracks `CS3264-Materials/`,
which holds `meetings.md` (TA contracted hours), `TA-Details.xlsx` and `Syllabus.xlsx`.
Pushing the whole repo would publish all of it. `--prefix=website` sends only the site,
with its contents at the repo root, which is what Pages needs.

### The alternative, if you ever want it

A project repo under your own account lands at **`haroldsoh.com/cs3264`** — because
`haroldsoh.github.io` CNAMEs to `haroldsoh.com`, and GitHub serves project sites from the
user site's custom domain. It cannot break the existing Jekyll site (separate repo,
separate Pages deployment), but the org site keeps the course self-contained.

Every path in the site is relative, so it works at a root or a subpath either way.

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

**Opened by double-clicking, the embed will not play.** From disk the page is `file://`,
and YouTube refuses the opaque origin with *Error 153 — video player configuration error*.
No embed parameter changes that. The build detects it and the play button opens
youtube.com in a new tab instead, with the badge reading "Video → YouTube". To see it
inline locally, serve the folder:

```bash
cd "AY26-27S1/CS3264-Materials/Lectures" && python3 -m http.server 8000
```

then open `http://localhost:8000`. For lecturing, use the master deck — it has the real
video file and needs no network at all.

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
