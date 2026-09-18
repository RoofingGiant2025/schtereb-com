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

## Printed edition (print-on-demand)
- `python3 tools/make_print.py` → `print/interior-6x9.pdf` (US Trade 6×9, mirrored margins, even page count, all fonts embedded) + `print/spec.json` (page count, Lulu spine width = pages/444 + 0.06 in).
- `python3 tools/make_cover.py` → `print/cover-6x9-paperback.pdf` (bleed + back + spine + front + bleed; barcode area bottom-right of the back left clear for Lulu's ISBN barcode).
- Rebuild the interior first whenever the text changes; the cover reads the page count from `spec.json`.
- Site: `ORDER_URL` in `tools/build_site.py` = the Lulu bookstore link; while empty, `/<lang>/order.html` shows "coming soon".
