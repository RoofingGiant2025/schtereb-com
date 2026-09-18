# Ноти життя: до і після — Oleg Schtereb, first collection

Four-language book (uk · ru · en · es) as a PDF and a static website for schtereb.com.

## Layout
- `content/originals.md` — the exact originals (43 Ukrainian, 37 Russian). **Never edit the text**; only fix extraction damage.
- `content/en.md` — English translation, 80 poems, same order (`## Title` per poem, `# Section` headers).
- `content/tr/uk.md`, `tr/ru.md`, `tr/es.md` — translations *only for poems not originally in that language*; headers are `## <n>. <Title>` where `<n>` is the poem's number (1–80) in `originals.md`.
- `content/notes/{uk,ru,en,es}.md` — one short **headnote** (introduction/analysis) per poem in each language, `## <n>. <Title>` headers, one paragraph each. The build refuses to run if any of the 82 × 4 is missing. Shown on the title plate before every poem, behind the "About" button beside "Listen", and as the page's meta description.
- `content/uk.md`, `ru.md`, `es.md` — **generated** full files (originals merged in verbatim). Don't edit; edit the sources above.
- `docs/` — generated static site. `docs/data/poems.json` is the single data file.
- `tools/build_content.py` — merges sources → `content/{uk,ru,es}.md` + `docs/data/poems.json`
- `tools/build_site.py` (+ `book.css`, `book.js`) — builds all pages into `docs/`
- `tools/make_pdf.py` — builds `Oleg-Schtereb-Noty-Zhyttia-4-languages.pdf` (needs `pip install reportlab pypdf`)
- `tools/img/author.jpg` — the author's portrait (960×1440, 2:3). When the file exists, the book gets an **About the author** spread before the colophon (portrait plate + caption on the left, short bio on the right; strings `about*` in the `UI` dict of `build_site.py`, link in the contents sheet). Without the file the spread is simply absent.

## Rebuild everything
```bash
cd ~/Shtereb-Poems && python3 tools/build_content.py && python3 tools/build_site.py && python3 tools/make_pdf.py
```

## Fix or add a poem
1. Edit the source file for that language (`content/en.md`, or `content/tr/<lang>.md` with the numbered header).
2. Run the rebuild line above. The build asserts 80 poems × 4 languages and refuses to build if any is missing.
3. Deploy `docs/` (see below).

## Deploy to schtereb.com (Hostinger)
Run `./deploy.sh` — rebuilds and rsyncs `docs/` to `roofinggiant:~/domains/schtereb.com/public_html/`
(Hostinger Business plan; the website was added on 2026-09-18 through the Hostinger API).

The domain is registered at GoDaddy. DNS records to set there (Domain → DNS → Manage):
- `A`     `@`    → `82.197.83.129`   (Hostinger server for this account)
- `CNAME` `www`  → `schtereb.com`
Delete the two existing parked `A` records (3.33.130.190, 15.197.148.33) and any domain forwarding.
Once DNS resolves, Hostinger issues the Let's Encrypt certificate automatically (hPanel → Websites → schtereb.com → SSL);
then turn on **Force HTTPS** in hPanel, or add the redirect to the `.htaccess` block in `tools/build_site.py`.

## Site URLs
`/` epigraph + language choice · `/<lang>/` title + contents · `/<lang>/<n>-<slug>.html` one poem.
Keys ← → (and swipe) move between poems; the language pills keep the poem; "Beside the original" shows the original next to a translation.

## Printed edition — hardcover (Lulu print-on-demand, ships worldwide)
- `python3 tools/make_print.py` → `print/interior-6x9.pdf` (US Trade 6×9, mirrored margins with the 1 in gutter Lulu wants at 400+ pages,
  edition page with a line for the copy number + signature, dedication, rectos where a book expects them, even page count, fonts embedded)
  and `print/spec.json` (page count, paperback spine formula, hardcover spine from Lulu's table, jacket geometry).
- `python3 tools/make_jacket.py` → `print/jacket-6x9-hardcover.pdf` — the dust jacket for Lulu's **Linen Wrap** hardcover, on Lulu's own template
  geometry (21 × 9.75 in, 0.25 in bleed, 3.25 in flaps, 1.25 in spine for 417–444 pp), same design as the site's cover (bordeaux cloth, gilt frame,
  arched plate) — and `tools/img/jacket.jpg` for the edition page. The cloth grain raster is cached in `print/.cloth-*.jpg`.
- Rebuild the interior first whenever the text changes; the jacket reads the page count from `spec.json` (spine width changes at 445 pages).
- `print/edition.json` — `price_usd` (printed on the front flap and shown on the site) and `order_url` (the Lulu bookstore link; empty = "coming soon").
- Lulu product: US Trade 6×9 · Hardcover **Linen Wrap** (comes with the dust jacket) · Standard B&W · 60# cream · matte jacket ·
  linen **black**, foil **gold** · print cost $25.54 (2026-09) · Lulu Bookstore only (retail distribution would need a $51+ list price and pays ~$3/copy).
- Site: `/<lang>/order.html` = the edition page (3-D book, price, specs, the jacket laid flat). `make_cover.py` is the old paperback cover, kept for reference.

## Manuscripts and drawings (facsimile plates)
The author's archive (286 iPhone photos of the original sheets and drawings) lives outside git; the 38 selected originals are copied to `archive/IMG_*.HEIC` (gitignored, 68 MB).
- `content/manuscripts.json` — which photo belongs to which poem (27 poems have an autograph; 10, 26 and 67 have two pages) and to which book plate (`frontispiece`, `endpaper`, `part-before`, `sec-1..3`, `part-after`, `colophon`), with the sheet's corners (`quad`, normalised, TL→clockwise), `rotate`, `colour` (keep some of the paper's own tone), `gamma` (pencil sheets), and the caption fields `date` (what the author wrote) and `medium` per language.
- `python3 tools/manuscripts.py [--debug] [keys…]` → `docs/assets/ms/<n>[-<page>].jpg` (1000 px, on the leaf) + `-x.jpg` (2000 px, lightbox), `docs/assets/art/<key>.jpg`, and `docs/assets/ms/manifest.json`. Needs `pip3 install numpy opencv-python-headless`; HEIC decoding via macOS `sips`. `--debug` writes the detected corners to `archive/debug/`.
- `build_site.py` reads the manifest and adds `poems[n].ms` / `art` to `poems.json`; the reader (book.js) then lays out: autograph on the verso facing the typeset original (or facing the title plate, before original|translation); drawings facing the part/section plates, the self-portrait as frontispiece, the folder as endpapers, ✎ in the contents; tap a sheet for the lightbox (tap again to zoom into that spot, ←/→ between pages).
- To add a manuscript: drop the photo in `archive/`, add the poem to `manuscripts.json` (run once with `--debug`, check the corner overlay, set `quad` by hand if the auto-detection grabbed a neighbouring sheet), run `manuscripts.py <n>`, then `./deploy.sh`.

## Audio (listen button)
- `python3 tools/make_audio.py [lang ...]` records every poem with macOS voices (Lesya uk, Milena ru, Samantha en, Mónica es) into `docs/audio/<lang>/<n>.m4a` and writes `docs/audio/manifest.json`. Files whose text is unchanged are skipped (`.sha` sidecars). Re-run after editing poems.
- The page plays the file when the manifest lists it; otherwise it falls back to the browser's own speech synthesis in the poem's language.
