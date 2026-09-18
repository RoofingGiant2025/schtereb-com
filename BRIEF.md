# Brief — "My Poetry": the first collection of Oleg Shtereb, as a book on schtereb.com

*This is the prompt for Claude. It is self-contained; everything needed is in `content/` and this file.*

## What you are building

A four-language digital edition of Oleg Shtereb's first poetry collection (≈80 poems, originally published on schtereb.com, page "POET", c. 2005–2019), presented as a **book to be read**, not a web page to be scanned. Deployed live at **https://schtereb.com** (domain and hosting at GoDaddy).

Languages: **English, Ukrainian, Russian, Spanish.** Every poem exists in all four.

## Source material

- `content/originals.md` — the exact original texts as written by the author. Roughly 45 poems are in Ukrainian, 35 in Russian. Some contain English lines (`way`, `If you want to be okey / Drink a vodka every day`, `Fuck !`, `O.Rich`, `Romantic ballad`). These are part of the work.
- `content/en.md` — the English translation (complete).
- Section structure from the original page, in this order:
  1. *(untitled opening)* — "Белое произведение / Я странник"
  2. **Любов як захоплення** — Love as Infatuation
  3. **Любов як драма** — Love as Drama
  4. **Любов як істина** — Love as Truth

## Non-negotiable rules

1. **The originals are never edited.** Not a word, not a comma, not a line break, not the author's capitalisation or punctuation quirks (`Ха-Ха`, `!!!`, `..!`, `Fuck !`). The only permitted cleanup is removing HTML-extraction damage (runs of blank lines, stray tab indentation that was clearly layout rather than intent). When in doubt, keep it.
2. **Translate only into the languages that are missing.** A Ukrainian poem gets Russian, English, Spanish. A Russian poem gets Ukrainian, English, Spanish. The original is always marked as the original.
3. **Translation standard:** literary, line-for-line where the target language allows, stanza structure identical to the original, meaning and imagery before rhyme; rhyme where it arrives naturally, never forced at the cost of sense. Register follows the author — slang stays slang, prayer stays prayer, obscenity stays obscenity. Words already in English in the original stay in English in every version.
4. **Order and grouping** follow the original page exactly. No re-sorting, no "best of", no omissions.
5. **Author's name, one way:** Oleg Shtereb / Олег Штереб / Oleg Shtereb (es).

## The reading experience ("looks like reading a book")

- One poem per spread. Generous margins, book typography (a serif with real Cyrillic support — e.g. *Literata*, *PT Serif*, *EB Garamond* + Cyrillic fallback), measure ≈ 60–70 characters, line-height ≈ 1.6, poem lines never re-wrapped on desktop; on phones the poem stays left-aligned and hanging-indents wrapped lines.
- Front matter: half-title, title page, a short **author's note** (to be written by the author or left as a one-line placeholder — do not invent biography), contents.
- Contents page lists all poems by section with page numbers; every poem is a stable, shareable URL (`/en/12-my-dream`, `/uk/12-moya-mriya`, …).
- Navigation: ← / → keys and swipe move between poems; a **language switch** stays on the same poem; an "original" badge marks the language the poem was written in; optional **side-by-side** view (original | chosen language).
- Colophon at the back: original publication note, translation note, © Oleg Shtereb, year.
- Light and dark paper. No ads, no analytics beyond a privacy-respecting counter if the owner asks, no cookie banner.
- Static HTML/CSS/JS, no framework, no build server required to view. Works offline once loaded. Total weight small.
- Works in Safari/Chrome/Firefox, iPhone and desktop. Lighthouse ≥ 95 on all four.

## Deliverables

1. `content/uk.md`, `content/ru.md`, `content/es.md` — complete, same 80-poem order as `en.md`.
2. `site/` — the finished static site.
3. `tools/build.py` — parses the four content files, verifies 80 × 4, emits `site/data/poems.json` and the static pages.
4. Deployment to schtereb.com at GoDaddy. **Prompt the owner to log in to GoDaddy when the login is needed; never type the owner's credentials.** Confirm hosting type first (cPanel/Linux hosting, Website Builder, or domain-only), then choose: upload via cPanel File Manager / FTP, or — if domain-only — point DNS at GitHub Pages / Cloudflare Pages and deploy there.
5. A `README.md` describing how to add or fix a poem and redeploy.

## Acceptance

- Every original text byte-identical (ignoring whitespace normalisation) to `content/originals.md`.
- 80 poems × 4 languages present; language switch never lands on a missing text.
- Reads like a book on a phone in portrait.
- https://schtereb.com resolves with HTTPS and shows the title page.
