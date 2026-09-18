# Ноти життя: до і після — Oleg Shtereb, first collection

Four-language book (uk · ru · en · es) as a PDF and a static website for schtereb.com.

## Layout
- `content/originals.md` — the exact originals (43 Ukrainian, 37 Russian). **Never edit the text**; only fix extraction damage.
- `content/en.md` — English translation, 80 poems, same order (`## Title` per poem, `# Section` headers).
- `content/tr/uk.md`, `tr/ru.md`, `tr/es.md` — translations *only for poems not originally in that language*; headers are `## <n>. <Title>` where `<n>` is the poem's number (1–80) in `originals.md`.
- `content/uk.md`, `ru.md`, `es.md` — **generated** full files (originals merged in verbatim). Don't edit; edit the sources above.
- `docs/` — generated static site. `docs/data/poems.json` is the single data file.
- `tools/build_content.py` — merges sources → `content/{uk,ru,es}.md` + `docs/data/poems.json`
- `tools/build_site.py` (+ `book.css`, `book.js`) — builds all pages into `docs/`
- `tools/make_pdf.py` — builds `Oleg-Shtereb-Noty-Zhyttia-4-languages.pdf` (needs `pip install reportlab pypdf`)

## Rebuild everything
```bash
cd ~/Shtereb-Poems && python3 tools/build_content.py && python3 tools/build_site.py && python3 tools/make_pdf.py
```

## Fix or add a poem
1. Edit the source file for that language (`content/en.md`, or `content/tr/<lang>.md` with the numbered header).
2. Run the rebuild line above. The build asserts 80 poems × 4 languages and refuses to build if any is missing.
3. Deploy `docs/` (see below).

## Deploy to schtereb.com (GoDaddy)
The site is plain files — upload the *contents* of `docs/` to the web root (`public_html/` on cPanel hosting).
With cPanel/FTP credentials in hand: `rsync -av --delete docs/ user@host:public_html/` or use the cPanel File Manager.
If the domain is domain-only at GoDaddy, host `docs/` on GitHub Pages / Cloudflare Pages and point the A/CNAME records there.

## Site URLs
`/` epigraph + language choice · `/<lang>/` title + contents · `/<lang>/<n>-<slug>.html` one poem.
Keys ← → (and swipe) move between poems; the language pills keep the poem; "Beside the original" shows the original next to a translation.
