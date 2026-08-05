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
| **Collaborative Notes page limits** (20 / 40) | `#assessment` | Carried over from AY25/26. |
| **Final exam 25 Nov, 5–7pm** | `#assessment`, schedule | From NUSMods; the page says it is provisional. Confirm against the official exam timetable. |
| **Tutorial slot count** (six) | `#policies` | Depends on TA contracted hours and post-add/drop numbers. |
| **Week 13 cover** | not on the page yet | Guest lecturer vs pre-record — decide by early October, then announce. |

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

### Option B — `https://haroldsoh.github.io/cs3264`

A project repo under your own account. No organisation needed: create a public repo named
`cs3264`, push this folder, enable Pages the same way.

Both work with the site as written — every path is relative, so nothing breaks at a
subpath.

---

## Adding a lecture's slides

The decks are self-contained HTML. To publish one:

```bash
mkdir -p website/slides && cp "../CS3264-Materials/Lectures/Lecture 01 - Intro to CS3264.html" website/slides/lecture-01.html && cp -R "../CS3264-Materials/Lectures/media" website/slides/media
```

The schedule already links to `slides/lecture-01.html`.

**Check this before you push.** The deck embeds third-party material — the Boston Dynamics
clip, the Netflix mark, a Statista chart, figures from published papers. That is
comfortably fair dealing for teaching behind a login; putting it on a public website is a
different question. Two safer routes:

- host the decks on **Canvas or Piazza** and point the schedule links there, or
- publish a version with the third-party media swapped out.

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
