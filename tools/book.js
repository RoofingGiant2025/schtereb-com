/* Ноти життя: до і після — book reader. Progressive: every page is server-rendered; this turns it into a book. */
(function () {
  "use strict";
  var LANGS = ["uk", "ru", "en", "es"];
  var root = document.getElementById("book-root");
  if (!root) return;
  var BASE = root.dataset.base || "/", VER = root.dataset.v || "0";
  var state = { lang: root.dataset.lang || "uk", open: root.dataset.open === "1", page: 0, data: null, pages: null, turning: "none" };
  var spreadMode = window.matchMedia("(min-width: 768px)");
  var el = {
    stage: document.getElementById("stage"), book: document.getElementById("book"), cover: document.getElementById("cover"),
    left: document.getElementById("leaf-left"), right: document.getElementById("leaf-right"),
    prevL: document.getElementById("turn-prev-l"), prevR: document.getElementById("turn-prev-r"), nextR: document.getElementById("turn-next-r"),
    langs: document.getElementById("langs"), toc: document.getElementById("toc-btn"), folio: document.getElementById("folio-ind"),
    overlay: document.getElementById("overlay"), sheet: document.getElementById("sheet"), bottom: document.getElementById("chrome-bottom"),
    coverBtn: document.getElementById("cover-open"), cta: document.getElementById("cover-cta"),
    lb: document.getElementById("lightbox"), lbImg: document.getElementById("lb-img"), lbCap: document.getElementById("lb-cap"), lbStage: document.getElementById("lb-stage")
  };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var em = function (s) { return esc(s).replace(/\*([^*]+)\*/g, "<em>$1</em>"); };   /* headnotes: *word* = italics (foreign words, titles) */
  var ORN = {
    rule: '<svg class="orn rule" viewBox="0 0 180 12" fill="none" aria-hidden="true"><path d="M2 6h68" stroke="currentColor" stroke-width=".7" stroke-linecap="round"/><circle cx="90" cy="6" r="1.6" fill="currentColor"/><path d="M78 6h24" stroke="currentColor" stroke-width=".7" opacity=".5"/><path d="M110 6h68" stroke="currentColor" stroke-width=".7" stroke-linecap="round"/></svg>',
    staff: '<svg class="orn staff" viewBox="0 0 96 36" fill="none" aria-hidden="true"><path d="M4 8h88M4 14h88M4 20h88M4 26h88M4 32h88" stroke="currentColor" stroke-width=".7" opacity=".55"/><path d="M22 26c0-7 5-12 8-18 1 8-2 14-2 20 0 3 2 5 4 5 3 0 5-3 5-6 0-5-4-8-7-8-4 0-8 4-8 9 0 6 5 10 11 10 8 0 13-7 13-15" stroke="currentColor" stroke-width="1.15" stroke-linecap="round"/><ellipse cx="58" cy="24" rx="4.2" ry="3" fill="currentColor"/><path d="M62 24V10" stroke="currentColor" stroke-width="1.1"/><ellipse cx="74" cy="18" rx="4.2" ry="3" fill="currentColor"/><path d="M78 18V6" stroke="currentColor" stroke-width="1.1"/></svg>',
    light: '<svg class="orn light" viewBox="0 0 48 72" fill="none" aria-hidden="true"><path d="M24 6c0 18-10 28-10 46 0 8 4.4 14 10 14s10-6 10-14c0-18-10-28-10-46Z" stroke="currentColor" stroke-width="1.2" opacity=".85"/><path d="M24 10v46" stroke="currentColor" stroke-width=".8" opacity=".5"/></svg>',
    bfly: '<svg class="orn bfly" viewBox="0 0 64 48" fill="none" aria-hidden="true"><path d="M32 10c-8-10-22-6-24 6-1.5 9 8 14 24 22 16-8 25.5-13 24-22-2-12-16-16-24-6Z" stroke="currentColor" stroke-width="1.1"/><path d="M32 10v30" stroke="currentColor" stroke-width=".9"/><path d="M32 10c-2-6 2-8 0-10" stroke="currentColor" stroke-width=".9"/></svg>'
  };

  /* ---------- codex: Leonardo-notebook studies in the margins (sanguine line drawings, mirror script) ---------- */
  var STUDY = {"icosa": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><path d=\"M87.0 105.1L71.0 136.7 M87.0 105.1L54.6 89.9 M87.0 105.1L125.5 91.4 M87.0 105.1L91.8 64.9 M87.0 105.1L116.0 133.2 M71.0 136.7L54.6 89.9 M71.0 136.7L116.0 133.2 M54.6 89.9L91.8 64.9 M125.5 91.4L91.8 64.9 M125.5 91.4L116.0 133.2 M125.5 91.4L131.7 59.8 M125.5 91.4L150.1 111.1 M91.8 64.9L131.7 59.8 M116.0 133.2L150.1 111.1\" stroke=\"currentColor\" stroke-width=\".6\" opacity=\".35\"/><path d=\"M71.0 136.7L111.4 148.8 M71.0 136.7L59.3 113.8 M54.6 89.9L78.0 54.5 M54.6 89.9L59.3 113.8 M111.4 148.8L116.0 133.2 M111.4 148.8L59.3 113.8 M111.4 148.8L123.6 90.8 M111.4 148.8L150.1 111.1 M78.0 54.5L91.8 64.9 M78.0 54.5L59.3 113.8 M78.0 54.5L123.6 90.8 M78.0 54.5L131.7 59.8 M59.3 113.8L123.6 90.8 M123.6 90.8L131.7 59.8 M123.6 90.8L150.1 111.1 M131.7 59.8L150.1 111.1\" stroke=\"currentColor\" stroke-width=\"1.05\" stroke-linecap=\"round\"/><circle cx=\"100\" cy=\"100\" r=\"82\" stroke=\"currentColor\" stroke-width=\".5\" opacity=\".4\" stroke-dasharray=\"1 4\"/></svg>", "dodeca": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><path d=\"M57.6 110.5L77.0 94.6 M57.6 110.5L73.7 139.2 M68.2 58.8L83.8 67.3 M100.6 108.8L77.0 94.6 M100.6 108.8L123.2 93.1 M100.6 108.8L101.3 134.9 M128.9 137.5L101.3 134.9 M128.9 137.5L143.3 107.9 M114.5 66.2L123.2 93.1 M114.5 66.2L83.8 67.3 M114.5 66.2L129.1 56.7 M77.0 94.6L83.8 67.3 M73.7 139.2L101.3 134.9 M123.2 93.1L143.3 107.9\" stroke=\"currentColor\" stroke-width=\".6\" opacity=\".35\"/><path d=\"M57.6 110.5L48.0 90.6 M79.8 147.0L73.7 139.2 M79.8 147.0L122.7 145.8 M79.8 147.0L61.3 111.5 M68.2 58.8L48.0 90.6 M68.2 58.8L98.2 49.9 M98.9 83.4L98.2 49.9 M98.9 83.4L61.3 111.5 M98.9 83.4L138.7 109.1 M128.9 137.5L122.7 145.8 M151.3 87.3L138.7 109.1 M151.3 87.3L129.1 56.7 M151.3 87.3L143.3 107.9 M48.0 90.6L61.3 111.5 M122.7 145.8L138.7 109.1 M98.2 49.9L129.1 56.7\" stroke=\"currentColor\" stroke-width=\"1.05\" stroke-linecap=\"round\"/><circle cx=\"100\" cy=\"100\" r=\"84\" stroke=\"currentColor\" stroke-width=\".5\" opacity=\".4\" stroke-dasharray=\"1 4\"/></svg>", "spiral": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><g stroke=\"currentColor\" stroke-width=\".55\" opacity=\".45\"><rect x=\"15.0\" y=\"47.5\" width=\"105.1\" height=\"105.1\"/><rect x=\"120.1\" y=\"47.5\" width=\"64.9\" height=\"64.9\"/><rect x=\"144.8\" y=\"112.4\" width=\"40.2\" height=\"40.2\"/><rect x=\"120.1\" y=\"127.8\" width=\"24.7\" height=\"24.7\"/><rect x=\"120.1\" y=\"112.4\" width=\"15.5\" height=\"15.5\"/><rect x=\"135.5\" y=\"112.4\" width=\"9.3\" height=\"9.3\"/><rect x=\"138.6\" y=\"121.6\" width=\"6.2\" height=\"6.2\"/><rect x=\"135.5\" y=\"124.7\" width=\"3.1\" height=\"3.1\"/><rect x=\"135.5\" y=\"121.6\" width=\"3.1\" height=\"3.1\"/></g><path d=\"M15.0 152.5A105.1 105.1 0 0 1 120.1 47.5 M120.1 47.5A64.9 64.9 0 0 1 185.0 112.4 M185.0 112.4A40.2 40.2 0 0 1 144.8 152.5 M144.8 152.5A24.7 24.7 0 0 1 120.1 127.8 M120.1 127.8A15.5 15.5 0 0 1 135.5 112.4 M135.5 112.4A9.3 9.3 0 0 1 144.8 121.6 M144.8 121.6A6.2 6.2 0 0 1 138.6 127.8 M138.6 127.8A3.1 3.1 0 0 1 135.5 124.7 M135.5 124.7A3.1 3.1 0 0 1 138.6 121.6\" stroke=\"currentColor\" stroke-width=\"1.1\" stroke-linecap=\"round\"/></svg>", "vortex": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><path d=\"M103.2 104.7 L103.1 105.6 L102.7 106.4 L102.0 107.2 L101.1 107.8 L100.1 108.1 L98.9 108.2 L97.7 107.9 L96.6 107.3 L95.7 106.4 L95.0 105.2 L94.6 103.8 L94.6 102.2 L95.1 100.7 L95.9 99.3 L97.2 98.1 L98.8 97.3 L100.7 97.0 L102.7 97.1 L104.6 97.8 L106.4 99.1 L107.8 100.8 L108.8 103.0 L109.1 105.5 L108.8 108.0 L107.7 110.5 L106.0 112.7 L103.6 114.5 L100.7 115.6 L97.4 115.8 L94.1 115.2 L90.9 113.6 L88.1 111.1 L86.0 107.9 L84.8 104.0\" stroke=\"currentColor\" stroke-width=\"0.9\" opacity=\"0.9\" stroke-linecap=\"round\"/><path d=\"M100.4 107.3 L99.5 107.4 L98.5 107.3 L97.6 106.9 L96.7 106.2 L96.1 105.3 L95.7 104.2 L95.6 103.0 L95.8 101.8 L96.4 100.6 L97.3 99.6 L98.6 98.8 L100.0 98.3 L101.6 98.3 L103.2 98.7 L104.7 99.6 L106.0 100.8 L106.9 102.5 L107.4 104.4 L107.3 106.5 L106.7 108.6 L105.4 110.5 L103.7 112.1 L101.4 113.1 L98.9 113.6 L96.2 113.4 L93.5 112.4 L91.1 110.6 L89.2 108.2 L87.9 105.2 L87.5 101.8 L88.0 98.3 L89.5 94.9 L92.0 91.9 L95.3 89.6\" stroke=\"currentColor\" stroke-width=\"0.6\" opacity=\"0.55\" stroke-linecap=\"round\"/><path d=\"M97.0 105.4 L96.6 104.5 L96.4 103.6 L96.5 102.6 L96.9 101.6 L97.5 100.7 L98.4 100.0 L99.5 99.5 L100.8 99.3 L102.1 99.5 L103.4 100.1 L104.5 101.0 L105.4 102.3 L105.9 103.7 L106.0 105.4 L105.7 107.1 L104.9 108.7 L103.6 110.1 L101.9 111.2 L99.9 111.7 L97.7 111.8 L95.5 111.2 L93.5 110.0 L91.7 108.2 L90.5 105.9 L89.9 103.3 L90.0 100.4 L91.0 97.6 L92.7 95.0 L95.1 92.9 L98.2 91.5 L101.7 90.9 L105.4 91.2 L109.0 92.7 L112.3 95.1\" stroke=\"currentColor\" stroke-width=\"0.9\" opacity=\"0.9\" stroke-linecap=\"round\"/><path d=\"M97.8 101.6 L98.4 100.9 L99.3 100.5 L100.3 100.2 L101.3 100.3 L102.4 100.6 L103.4 101.3 L104.1 102.2 L104.7 103.3 L104.9 104.6 L104.8 106.0 L104.2 107.4 L103.3 108.6 L102.1 109.5 L100.5 110.2 L98.8 110.4 L97.0 110.1 L95.3 109.3 L93.8 108.0 L92.6 106.3 L91.9 104.2 L91.8 102.0 L92.3 99.6 L93.5 97.4 L95.2 95.6 L97.6 94.2 L100.3 93.4 L103.3 93.4 L106.3 94.3 L109.0 95.9 L111.4 98.4 L113.0 101.6 L113.8 105.2 L113.6 109.1 L112.3 112.9\" stroke=\"currentColor\" stroke-width=\"0.6\" opacity=\"0.55\" stroke-linecap=\"round\"/><path d=\"M101.6 101.1 L102.4 101.6 L103.1 102.2 L103.7 103.1 L104.0 104.1 L104.0 105.2 L103.6 106.3 L103.0 107.4 L102.1 108.2 L100.9 108.9 L99.6 109.2 L98.1 109.1 L96.7 108.6 L95.4 107.7 L94.3 106.4 L93.6 104.8 L93.3 103.0 L93.5 101.1 L94.3 99.3 L95.5 97.7 L97.3 96.4 L99.4 95.6 L101.8 95.3 L104.2 95.8 L106.6 96.9 L108.6 98.7 L110.2 101.0 L111.1 103.8 L111.2 107.0 L110.5 110.1 L108.8 113.1 L106.3 115.6 L103.1 117.5 L99.4 118.5 L95.3 118.4\" stroke=\"currentColor\" stroke-width=\"0.9\" opacity=\"0.9\" stroke-linecap=\"round\"/><path d=\"M10 150q22 -6 44 0t44 0t44 0t44 0 M16 159q22 -6 44 0t44 0t44 0t44 0 M22 168q22 -6 44 0t44 0t44 0t44 0 M28 177q22 -6 44 0t44 0t44 0t44 0\" stroke=\"currentColor\" stroke-width=\".55\" opacity=\".5\"/></svg>", "proportion": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><circle cx=\"100\" cy=\"96\" r=\"76\" stroke=\"currentColor\" stroke-width=\"1.05\"/><rect x=\"34\" y=\"42\" width=\"132\" height=\"132\" stroke=\"currentColor\" stroke-width=\"1.05\"/><path d=\"M34 42L166 174M166 42L34 174M100 20v154M24 108h152\" stroke=\"currentColor\" stroke-width=\".5\" opacity=\".5\"/><path d=\"M34 92.6h132M115.4 42v132M84.6 42v132\" stroke=\"currentColor\" stroke-width=\".55\" opacity=\".7\" stroke-dasharray=\"3 3\"/><circle cx=\"100\" cy=\"96\" r=\"2\" fill=\"currentColor\"/><path d=\"M40 178h120\" stroke=\"currentColor\" stroke-width=\".6\"/><path d=\"M40 175v6M100 175v6M160 175v6M77 176v4M123 176v4\" stroke=\"currentColor\" stroke-width=\".6\"/><text x=\"168\" y=\"98\" font-size=\"11\" font-style=\"italic\" fill=\"currentColor\" font-family=\"Cormorant Garamond,serif\">φ</text></svg>", "wing": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><path d=\"M22 150C50 82 96 48 178 44\" stroke=\"currentColor\" stroke-width=\"1.15\" stroke-linecap=\"round\"/><path d=\"M22 150L60 70M22 150L88 58M22 150L118 50M22 150L150 46M22 150L178 44\" stroke=\"currentColor\" stroke-width=\".7\" opacity=\".85\"/><path d=\"M42 108C62 96 84 90 110 88M56 124C80 110 110 104 146 104M74 146C100 132 138 128 178 130\" stroke=\"currentColor\" stroke-width=\".6\" opacity=\".6\"/><path d=\"M22 150c-8 6-12 14-10 24M60 70l4-10M88 58l3-10M118 50l2-10\" stroke=\"currentColor\" stroke-width=\".6\" opacity=\".7\"/><circle cx=\"22\" cy=\"150\" r=\"3.2\" stroke=\"currentColor\" stroke-width=\".9\"/><path d=\"M178 44c10 14 8 40-2 70\" stroke=\"currentColor\" stroke-width=\".6\" opacity=\".5\" stroke-dasharray=\"2 3\"/></svg>", "lily": "<svg class=\"study\" viewBox=\"0 0 200 200\" fill=\"none\" aria-hidden=\"true\"><g stroke=\"currentColor\" stroke-linecap=\"round\"><path d=\"M100 176C96 140 70 120 44 118c22-6 46 6 58 30\" stroke-width=\"1\"/><path d=\"M100 176c4-38 30-58 58-56-22 4-46 20-56 42\" stroke-width=\"1\"/><path d=\"M100 176c-6-44-36-70-70-64 30 2 56 26 66 62\" stroke-width=\".8\" opacity=\".8\"/><path d=\"M100 176c8-44 40-68 72-60-30 0-58 22-68 58\" stroke-width=\".8\" opacity=\".8\"/><path d=\"M100 176c0-50-8-90-30-120 18 26 28 66 30 118\" stroke-width=\".9\"/><path d=\"M100 176c2-54 12-92 34-118-18 28-30 66-32 116\" stroke-width=\".9\"/><path d=\"M100 176c-2-46-18-78-40-92 20 18 34 50 40 92\" stroke-width=\".7\" opacity=\".7\"/><path d=\"M100 176c4-44 22-76 44-88-22 14-38 46-42 88\" stroke-width=\".7\" opacity=\".7\"/><path d=\"M100 176v18\" stroke-width=\"1.1\"/></g><g stroke=\"currentColor\" stroke-width=\".7\"><path d=\"M70 56l-4-8 5 3 1-9 3 8 6-6-2 8 8-1-7 5 6 6-8-2 1 8-5-6-4 8-1-9-7 4z\"/><path d=\"M134 62l-3-7 4 3 1-8 3 7 5-5-2 7 7-1-6 4 5 6-7-2 1 7-4-5-4 7-1-8-6 3z\"/><circle cx=\"72\" cy=\"58\" r=\"1.6\" fill=\"currentColor\"/><circle cx=\"136\" cy=\"64\" r=\"1.4\" fill=\"currentColor\"/></g></svg>"};
  var STUDY_KEYS = ["proportion", "spiral", "icosa", "vortex", "wing", "dodeca", "lily"];
  var PLATE_STUDY = { "part-before": "proportion", "sec-1": "spiral", "sec-2": "vortex", "sec-3": "dodeca", "part-after": "wing", "colophon": "lily", "frontispiece": "icosa" };
  function studyFor(n) { return STUDY[STUDY_KEYS[n % STUDY_KEYS.length]]; }
  /* a deterministic little tilt per page, so the fragments do not all lie square */
  function tiltOf(n, spread) { var x = Math.sin(n * 12.9898) * 43758.5453; x -= Math.floor(x); return ((x * 2 - 1) * spread).toFixed(2); }
  function mirrorHTML(text, cls) { return text ? '<p class="mirror' + (cls ? " " + cls : "") + '" aria-hidden="true">' + esc(text) + "</p>" : ""; }
  function firstLines(p, lang, k) { var out = [], ch = p.texts[lang].chunks[0] || []; for (var i = 0; i < ch.length && out.length < k; i++) { var l = ch[i].trim(); if (l && !/^\*.*\*$/.test(l)) out.push(l); } return out; }

  /* ---------- page model ---------- */
  function contentsEntries(D) {
    var out = [{ k: "part", id: "before" }], last = null;
    var lastPart = "before";
    D.poems.forEach(function (p) {
      if (p.part !== "before" && p.part !== lastPart) { out.push({ k: "part", id: p.part }); }
      else if (p.part === "before" && p.section && p.section !== last) { out.push({ k: "sec", id: p.section }); }
      last = p.part !== "before" ? p.part : p.section; lastPart = p.part;
      out.push({ k: "poem", n: p.n });
    });
    return out;
  }
  function contentsChunks(D, size) {
    size = size || 12; var chunks = [], cur = [], w = 0;
    contentsEntries(D).forEach(function (e) {
      var ew = e.k === "poem" ? 1 : 1.4;
      if (cur.length && w + ew > size) { chunks.push(cur); cur = []; w = 0; }
      cur.push(e); w += ew;
    });
    if (cur.length) chunks.push(cur);
    return chunks;
  }
  function buildPages(D, lang) {
    var pages = [{ t: "epigraph" }, { t: "half" }, { t: "frontis" }, { t: "title" }, { t: "copyright" }, { t: "dedication" }];
    contentsChunks(D).forEach(function (_, i) { pages.push({ t: "contents", c: i }); });
    if (pages.length % 2 === 1) pages.push({ t: "blank" });
    var rightHand = function () { if (pages.length % 2 === 0) pages.push({ t: "blank" }); };
    var leftHand = function () { if (pages.length % 2 === 1) pages.push({ t: "blank" }); };
    var art = D.art || {};
    /* a drawing from the author's archive on the verso, facing a part or section plate on the recto */
    var plateWithArt = function (page, key) { if (art[key]) { leftHand(); pages.push({ t: "art", key: key }); } else rightHand(); pages.push(page); };
    plateWithArt({ t: "part", id: "before" }, "part-before");
    var lastSec = null, lastPart = "before";
    D.poems.forEach(function (p) {
      if (p.part !== "before" && p.part !== lastPart) plateWithArt({ t: "part", id: p.part }, "part-" + p.part);
      else if (p.part === "before" && p.section && p.section !== lastSec) plateWithArt({ t: "section", id: p.section }, "sec-" + (sectionIndex(p.section) + 1));
      lastSec = p.section; lastPart = p.part;
      var chunks = p.texts[p.orig].chunks.length;
      /* every poem, in every language: [autograph or blank | title plate with the headnote], then the text —
         the original alone, or original | translation */
      if (p.ms) { leftHand(); pages.push({ t: "ms", n: p.n }); } else if (pages.length % 2 === 0) pages.push({ t: "blank", study: p.n });   /* the empty verso: a study in the margin */
      pages.push({ t: "plate", n: p.n });
      if (lang === p.orig || p.single) { for (var c = 0; c < chunks; c++) pages.push({ t: "poem", n: p.n, c: c }); }
      else { for (var c2 = 0; c2 < chunks; c2++) { pages.push({ t: "orig", n: p.n, c: c2 }); pages.push({ t: "poem", n: p.n, c: c2 }); } }
    });
    if (D.portrait) { if (pages.length % 2 === 1) pages.push({ t: "blank" }); pages.push({ t: "author-plate" }); pages.push({ t: "author" }); }
    plateWithArt({ t: "colophon" }, "colophon");
    if (pages.length % 2 === 1) pages.push({ t: "blank" });
    pages.push({ t: "endpaper" });
    return pages;
  }
  function sectionIndex(id) { for (var i = 0; i < state.data.sections.length; i++) if (state.data.sections[i].key === id) return i; return 0; }
  function artHTML(a, key, lang) {
    var t = (a.title || {})[lang] || "", n = (a.note || {})[lang] || "", c = a.codex;
    /* codex: the drawing lifted off the photographed sheet, laid on the leaf in its own ink; the photo stays in the lightbox */
    var img = c ? '<img class="cx-ink" src="' + BASE + c.src + '?v=' + VER + '" alt="' + esc(t) + '" width="' + c.w + '" height="' + c.h + '" decoding="async">'
                : '<img src="' + BASE + a.src + '?v=' + VER + '" alt="' + esc(t) + '" width="' + a.w + '" height="' + a.h + '" decoding="async">';
    var study = c && PLATE_STUDY[key] ? '<span class="cx-study art-study" aria-hidden="true">' + STUDY[PLATE_STUDY[key]] + "</span>" : "";
    return '<figure class="ms art' + (c ? " codex" : "") + '" data-art="' + key + '"' + (c ? ' style="--rot:' + tiltOf(key.length * 7 + key.charCodeAt(0), 1.2) + 'deg"' : "") + '>' + study + (c ? mirrorHTML(t, "art-mirror") : "") +
      '<button type="button" class="ms-sheet" aria-label="' + esc(t) + '">' + img + "</button>" +
      '<figcaption><span class="c">' + esc(t) + (n ? ' · ' + esc(n) : "") + "</span></figcaption></figure>";
  }
  function msHTML(p, lang) {
    var ui = state.data.ui[lang], m = p.ms, pg = m.pages[0], c = m.codex;
    var cap = [ui.autograph, m.date, (m.medium || {})[lang]].filter(Boolean).join(" · "), note = (m.note || {})[lang];
    var more = m.pages.length > 1 ? '<span class="ms-more">1 ' + esc(ui.of_pages) + " " + m.pages.length + "</span>" : "";
    var alt = esc(ui.manuscript) + " — " + esc(p.texts[lang].title);
    if (!c) return '<figure class="ms" data-n="' + p.n + '"><button type="button" class="ms-sheet" aria-label="' + esc(ui.zoom) + '"><img src="' + BASE + pg.src + '?v=' + VER + '" alt="' + alt + '" width="' + pg.w + '" height="' + pg.h + '" decoding="async">' + more + "</button>" +
      '<figcaption><span class="r">' + p.roman + '</span><span class="c">' + esc(cap) + (note ? '<br>' + esc(note) : "") + "</span></figcaption></figure>";
    /* codex: the hand lifted off the sheet — the opening of the poem as the main cut, the signature and date as a detail
       laid over its torn foot; the whole photographed sheet opens in the lightbox */
    var det = c.detail ? '<span class="cx-detail" style="--drot:' + tiltOf(p.n * 3 + 1, 4) + 'deg"><img class="cx-ink" src="' + BASE + c.detail.src + '?v=' + VER + '" alt="" width="' + c.detail.w + '" height="' + c.detail.h + '" decoding="async"></span>' : "";
    var ot = p.texts[p.orig].title; if (ot === "* * *") ot = firstLines(p, p.orig, 1)[0] || "";
    return '<figure class="ms codex" data-n="' + p.n + '" style="--rot:' + tiltOf(p.n, 0.9) + 'deg">' +
      '<span class="cx-mark" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="15" stroke="currentColor" stroke-width=".8"/><path d="M20 3v5M20 32v5M3 20h5M32 20h5" stroke="currentColor" stroke-width=".8"/><circle cx="20" cy="20" r="1.2" fill="currentColor"/></svg><b>' + p.roman + "</b></span>" + mirrorHTML(ot, "ms-mirror") +
      '<button type="button" class="ms-sheet" aria-label="' + esc(ui.zoom) + '"><img class="cx-ink cx-main" src="' + BASE + c.main.src + '?v=' + VER + '" alt="' + alt + '" width="' + c.main.w + '" height="' + c.main.h + '" decoding="async">' + det + more + "</button>" +
      '<figcaption><span class="r">' + p.roman + '</span><span class="c">' + esc(cap) + (note ? '<br>' + esc(note) : "") + "</span></figcaption></figure>";
  }
  var byN = null;   /* n → poem (songs and poems are not one contiguous run) */
  function poem(n) { if (!byN) { byN = {}; state.data.poems.forEach(function (q) { byN[q.n] = q; }); } return byN[n]; }
  function pageIndex(t, id, c) { for (var i = 0; i < state.pages.length; i++) { var q = state.pages[i]; if (q.t === t && (id === undefined || q.id === id) && (c === undefined || q.c === c)) return i; } return -1; }
  function firstPageOf(pages, n, c) {
    c = c || 0;
    for (var i = 0; i < pages.length; i++) {
      var p = pages[i];
      if (p.n === n && (p.t === "orig" || p.t === "poem") && p.c === c) return i;   // the text itself, never the plate
    }
    return 0;
  }

  /* ---------- rendering ---------- */
  function stanzasOf(lines) {
    var out = [[]];
    lines.forEach(function (l) { if (l === "") out.push([]); else out[out.length - 1].push(l); });
    return out.filter(function (s) { return s.length; });
  }
  function verse(lines, drop) {
    return '<div class="verse">' + stanzasOf(lines).map(function (st, i) {
      var f0 = st[0].trim().charAt(0); var isLetter = f0 && f0.toLowerCase() !== f0.toUpperCase();
      var cls = "stanza" + (drop && i === 0 && isLetter ? " drop" : "");
      return '<p class="' + cls + '">' + st.map(function (l) {
        var m = /^\*(.+)\*$/.exec(l.trim());
        return m ? '<span class="note">' + esc(m[1]) + '</span>' : '<span class="l">' + esc(l) + '</span>';
      }).join("") + "</p>";
    }).join("") + "</div>";
  }
  var LISTEN_SVG = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><path d="M3 7.5v5h3l4 3.5v-12l-4 3.5H3z" fill="currentColor"/><path d="M12.5 6.5a4.5 4.5 0 0 1 0 7M14.5 4a8 8 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>';
  var ABOUT_SVG = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><circle cx="10" cy="10" r="7.25" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M10 9v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="10" cy="6.4" r=".9" fill="currentColor"/></svg>';
  function listenBtn(n, lang) {   /* same recording as the leaf; class/label are kept in sync by setBtn for every copy of the button */
    var ui = state.data.ui[lang], on = player.key === lang + "/" + n;
    return '<button class="listen' + (on ? " playing" : "") + '" type="button" data-n="' + n + '" data-lang="' + lang + '" aria-label="' + esc(ui.listen) + '">' + LISTEN_SVG + "<span>" + esc(on ? ui.stop : ui.listen) + "</span></button>";
  }
  function poemBlock(title, lines, kicker, drop, cont, n, lang) {
    var ui = state.data.ui[lang || state.lang];
    var btn = (n && !cont) ? listenBtn(n, lang) : "";
    /* "About the poem": the headnote in the reading language, opened in the sheet — only on the leaf in that language */
    if (n && !cont && lang === state.lang && (poem(n).note || {})[lang]) {
      var uiR = state.data.ui[state.lang];
      btn += '<button class="about-btn" type="button" data-about="' + n + '" aria-label="' + esc(uiR.about_poem) + '">' + ABOUT_SVG + "<span>" + esc(uiR.about_btn) + "</span></button>";
    }
    return '<div class="poem"><div class="poem-head">' + (kicker ? '<p class="kick">' + esc(kicker) + '</p>' : "<p></p>") + '<span class="poem-tools">' + btn + "</span></div>" +
      '<h2 class="' + (cont ? "cont" : "") + '">' + esc(title) + "</h2>" + ORN.rule + verse(lines, drop) + "</div>";
  }
  function sectionName(id, lang) {
    var D = state.data;
    if (D.parts && D.parts[id]) return D.parts[id][lang];
    var s = D.sections.filter(function (x) { return x.key === id; })[0];
    return s ? s[lang] : id;
  }
  function tocTitle(p, lang) {
    var t = p.texts[lang].title;
    if (t === "* * *") { var first = p.texts[lang].chunks[0].filter(function (l) { return l.trim(); })[0] || ""; return "* * *  " + first.trim().replace(/[,;:.—–\-\s]+$/, ""); }
    return t;
  }
  function contentsList(D, lang, entries, hrefFn) {
    return "<ol>" + entries.map(function (e) {
      if (e.k !== "poem") return '<li class="sec"><p>' + esc(sectionName(e.id, lang)) + "</p></li>";
      var p = poem(e.n);
      return '<li class="p"><a href="' + hrefFn(p) + '" data-n="' + p.n + '"><span class="r">' + p.roman + '</span><span class="t">' + esc(tocTitle(p, lang)) + (p.ms ? '<span class="ms-mark" title="' + esc(state.data.ui[lang].manuscript) + '">✎</span>' : "") + "</span></a></li>";
    }).join("") + "</ol>";
  }
  function poemHref(p, lang) { return BASE + lang + "/" + p.slug[lang] + ".html"; }
  function render(page, lang) {
    var D = state.data, ui = D.ui[lang];
    switch (page.t) {
      case "endpaper": return D.art && D.art.endpaper ? { cls: "endpaper folder", body: '<img src="' + BASE + D.art.endpaper.src + '?v=' + VER + '" alt="">' } : { cls: "endpaper", body: '<img src="' + BASE + 'assets/img/endpaper.jpg" alt="">' };
      case "art": return { cls: "plate art", body: artHTML(D.art[page.key], page.key, lang) };
      case "ms": return { cls: "plate", body: msHTML(poem(page.n), lang) };
      case "blank": {
        if (!page.study) return { body: '<div style="height:100%"></div>' };
        var sp = poem(page.study), lines = firstLines(sp, lang, 2);
        return { cls: "study", body: '<div class="study-page" data-v="' + (page.study % 3) + '"><span class="cx-study" aria-hidden="true">' + studyFor(page.study) + "</span>" + mirrorHTML(lines.join("\n")) + '<p class="study-num" aria-hidden="true">' + sp.roman + "</p></div>" };
      }
      case "epigraph": return { body: '<div class="center">' + ORN.staff + '<p class="epi">Art Knows No Languages</p><p class="epi-by">Oleg Schtereb</p>' + (lang !== "en" ? '<p class="epi-tr">' + esc(ui.epigraph) + "</p>" : "") + "</div>" };
      case "half": return { body: '<div class="center"><p class="kick">' + esc(ui.first) + '</p><h2 class="ht-main">' + esc(ui.main) + '</h2><p class="ht-sub">' + esc(ui.sub) + "</p></div>" };
      case "frontis": return D.art && D.art.frontispiece ? { cls: "plate art", body: artHTML(D.art.frontispiece, "frontispiece", lang) } : { body: '<figure class="frontis" style="margin:0"><img src="' + BASE + 'assets/img/frontispiece.jpg" alt=""></figure>' };
      case "title": return { body: '<div class="center"><p class="kick">' + esc(ui.first) + '</p><div style="margin-top:2rem">' + ORN.rule + '</div><h1 class="tp-main">' + esc(ui.main) + '</h1><p class="tp-sub">' + esc(ui.sub) + '</p><p class="tp-count">' + esc(ui.count) + '</p><p class="tp-author">' + esc(D.author[lang]) + '</p><div style="margin-top:2rem">' + ORN.rule + '</div><p class="tp-house">' + esc(ui.house) + " · 2026</p></div>" };
      case "copyright": return { body: '<div class="copyright"><p class="kick">' + esc(ui.edition) + ' · 2026</p><p class="note">' + esc(ui.note) + '</p><p class="m">' + esc(ui.facing) + '</p><p class="c">© 2026 ' + esc(D.author[lang]) + "</p><p>" + esc(ui.rights) + '</p><p class="m">' + esc(ui.published) + "</p></div>" };
      case "dedication": return { body: '<div class="center"><p class="dedic">To Those Who Are Living the Dream</p>' + (lang !== "en" ? '<p class="dedic-tr">' + esc(ui.dedication) + "</p>" : "") + "</div>" };
      case "contents": {
        var chunks = contentsChunks(D);
        return { body: '<div class="toc"><h2>' + esc(ui.contents) + '</h2><p class="kick">' + esc(ui.count) + "</p>" + (chunks.length > 1 ? '<p class="kick">' + (page.c + 1) + " / " + chunks.length + "</p>" : "") + ORN.rule + contentsList(D, lang, chunks[page.c], function (p) { return poemHref(p, lang); }) + "</div>" };
      }
      case "part": case "section": {
        var name = sectionName(page.id, lang), other = lang === "uk" ? "en" : "uk", sub = sectionName(page.id, other);
        var skey = page.t === "part" ? "part-" + page.id : "sec-" + (sectionIndex(page.id) + 1), sst = PLATE_STUDY[skey] ? '<span class="cx-study sec-study" aria-hidden="true">' + STUDY[PLATE_STUDY[skey]] + "</span>" : "";
        return { cls: "codex-plate", body: '<div class="center">' + ORN.staff + '<h2 class="sec-title">' + esc(name) + "</h2>" + (sub !== name ? '<p class="sec-sub">' + esc(sub) + "</p>" : "") + "</div>" + sst };
      }
      case "plate": {
        var p = poem(page.n), mark = p.n === 81 ? ORN.light : p.n === 82 ? ORN.bfly : ORN.staff;
        var note = (p.note || {})[lang] || "", ot = p.texts[p.orig].title, pt = p.texts[lang].title;
        var sg = p.song ? '<p class="plate-song">' + esc(ui.single) + " · " + esc(p.song.released) + (p.song.explicit ? " · E" : "") + '</p><p class="plate-links"><a href="' + esc(p.song.apple_url) + '" target="_blank" rel="noopener">Apple Music ↗</a> · <a href="' + esc(p.song.spotify) + '" target="_blank" rel="noopener">Spotify ↗</a>' + (p.song.source_poem ? ' · <a href="#" data-n="' + p.song.source_poem + '" class="src-poem">' + esc(ui.from_poem) + " " + (poem(p.song.source_poem).part === "after" ? esc(state.data.parts.after[lang]) + " " : "") + poem(p.song.source_poem).roman + "</a>" : "") + "</p>" : "";
        return { body: '<div class="center plate-page">' + mark + '<p class="plate-num">' + (p.song ? esc(ui.song) + " " : "") + p.roman + '</p><h2 class="plate-title">' + esc(pt) + "</h2>" + sg +
          (lang !== p.orig && ot !== pt ? '<p class="plate-orig">' + esc(ot) + "</p>" : "") +
          (note ? ORN.rule + '<p class="kick plate-kick">' + esc(ui.about_poem) + '</p><p class="plate-note">' + em(note) + "</p>" : "") + "</div>" };
      }
      case "orig": {
        var po = poem(page.n), to = po.texts[po.orig];
        return { body: poemBlock(to.title, to.chunks[page.c], page.c === 0 ? ui.original : ui.continued, false, page.c > 0, po.n, po.orig) };
      }
      case "poem": {
        var pp = poem(page.n), tp = pp.texts[lang], isO = lang === pp.orig || !!pp.single;
        if (pp.song) { var st = pp.song.status === "author" ? ui.lyrics_author : pp.song.status === "transcribed" ? ui.lyrics_transcribed : ui.lyrics_pending;
          return { body: poemBlock(tp.title, tp.chunks[page.c], page.c === 0 ? st : ui.continued, page.c === 0, page.c > 0, pp.n, lang) }; }
        return { body: poemBlock(tp.title, tp.chunks[page.c], isO ? (page.c > 0 ? ui.continued : "") : (page.c === 0 ? ui.translation : ui.continued), page.c === 0, page.c > 0, pp.n, lang) };
      }
      case "author-plate": return { body: '<figure class="portrait"><img src="' + BASE + D.portrait + '?v=' + (root.dataset.v || "0") + '" alt="' + esc(D.author[lang]) + '" width="960" height="1440" loading="lazy"><figcaption>' + esc(ui.about_caption) + "</figcaption></figure>" };
      case "author": return { body: '<div class="about"><p class="kick">' + esc(ui.about) + '</p><h2 class="about-name">' + esc(D.author[lang]) + "</h2>" + ORN.rule + '<p class="about-text">' + esc(ui.about_text) + "</p></div>" };
      case "colophon": return { body: '<div class="center">' + ORN.rule + '<p class="colo">' + esc(ui.colophon) + '</p><p class="colo-house">' + esc(ui.house) + " · " + esc(ui.published) + "</p>" + ORN.rule + "</div>" };
    }
    return { body: "" };
  }
  function leafHTML(page, lang, side, folio) {
    if (!page) return '<div class="leaf"><div class="leaf-body"></div></div>';
    var r = render(page, lang), ui = state.data.ui[lang];
    if (r.cls && r.cls.indexOf("endpaper") === 0) return '<div class="leaf ' + r.cls + '">' + r.body + "</div>";
    var foot = side === "left" ? '<span class="n">' + folio + "</span><span>" + esc(state.data.author[lang]) + "</span>" : "<span>" + esc(ui.main) + '</span><span class="n">' + folio + "</span>";
    return '<div class="leaf' + (r.cls ? " " + r.cls : "") + '"><div class="leaf-body">' + r.body + '</div><footer class="leaf-foot">' + foot + "</footer></div>";
  }

  /* ---------- state & navigation ---------- */
  function step() { return spreadMode.matches ? 2 : 1; }
  function draw() {
    var pages = state.pages, spread = spreadMode.matches;
    if (spread && state.page % 2 === 1) state.page -= 1;
    var li = spread ? state.page : null, ri = spread ? state.page + 1 : state.page;
    el.left.innerHTML = spread ? leafHTML(pages[li], state.lang, "left", li + 1) : "";
    el.right.innerHTML = leafHTML(pages[ri], state.lang, "right", ri + 1);
    var last = pages.length - 1;
    el.prevL.hidden = !(state.open && state.page > 0); el.prevR.hidden = !(state.open && state.page > 0); el.nextR.hidden = !(state.open && ri < last);
    el.folio.textContent = spread ? (state.page + 1) + "–" + (state.page + 2) : String(state.page + 1);
    markOverflow();
    el.bottom.hidden = !state.open;
    el.stage.className = "stage " + (state.open ? "open" : "closed");
    el.cover.dataset.open = state.open ? "true" : "false";
    el.cover.setAttribute("aria-hidden", state.open ? "true" : "false");
    if (state.open) tilt.stop(true); else tilt.start();
    document.documentElement.lang = state.lang;
    syncURL();
    try { localStorage.setItem("book.lang", state.lang); localStorage.setItem("book.page." + state.lang, String(state.page)); } catch (e) { }
  }
  function markOverflow() {
    Array.prototype.forEach.call(document.querySelectorAll("#book .leaf"), function (leaf) {
      var b = leaf.querySelector(".leaf-body"); if (!b) return;
      leaf.classList.toggle("more", b.scrollHeight > b.clientHeight + 4 && b.scrollTop + b.clientHeight < b.scrollHeight - 4);
      b.onscroll = function () { leaf.classList.toggle("more", b.scrollTop + b.clientHeight < b.scrollHeight - 4); };
    });
  }
  function relabelChrome() {
    var ui = state.data.ui[state.lang];
    var t = el.toc.querySelector("span"); if (t) t.textContent = ui.contents;
    var o = document.querySelector(".order-link"); if (o) { o.textContent = ui.order; o.href = BASE + state.lang + "/order.html"; }
    el.sheet.setAttribute("aria-label", ui.contents);
    var cov = el.coverBtn; if (cov) { cov.setAttribute("aria-label", ui.open); var q = function (sel, v) { var n = cov.querySelector(sel); if (n) n.textContent = v; };
      q(".k", ui.first); q("h1", ui.main); q(".s", ui.sub); q(".a", state.data.author[state.lang]); q(".c", ui.count); }
    var sp = function (sel, v) { var n = el.cover.querySelector(sel); if (n) n.textContent = v; };
    sp(".sp-t", ui.main + ": " + ui.sub); sp(".sp-a", state.data.author[state.lang]);
    if (el.cta) { var cs = el.cta.querySelector("span"); if (cs) cs.textContent = ui.open; }
  }
  function currentPoem() {
    var spread = spreadMode.matches, idx = [state.page].concat(spread ? [state.page + 1] : []);
    for (var i = 0; i < idx.length; i++) { var p = state.pages[idx[i]]; if (p && p.n) return p; }
    return null;
  }
  function syncURL() {
    if (!history.replaceState) return;
    var cp = currentPoem(), url;
    if (!state.open) url = BASE;
    else if (cp) url = poemHref(poem(cp.n), state.lang) + (cp.c ? "#c" + cp.c : "");
    else url = BASE + state.lang + "/#p" + state.page;
    if (location.pathname + location.hash !== url) history.replaceState(null, "", url);
    var cpp = cp ? poem(cp.n) : null;
    document.title = (cpp ? cpp.texts[state.lang].title + " — " : "") + state.data.title[state.lang] + " — " + state.data.author[state.lang];
  }
  function turn(dir, n) {
    if (!state.open) return;
    stopAll();
    var target = dir > 0 ? Math.min(state.pages.length - 1, state.page + n) : Math.max(0, state.page - n);
    if (!spreadMode.matches) { while (target > 0 && target < state.pages.length - 1 && state.pages[target].t === "blank") target += dir > 0 ? 1 : -1; }   /* one page at a time: never stop on a blank verso */
    if (target === state.page) return;
    state.page = target;
    el.book.classList.add("turning"); el.book.dataset.dir = dir > 0 ? "next" : "prev";
    clearTimeout(turn.timer);
    turn.timer = setTimeout(function () { el.book.classList.remove("turning"); el.book.dataset.dir = "none"; draw(); }, 170);
  }
  function goToPoem(n, c) { stopAll(); state.page = firstPageOf(state.pages, n, c || 0); state.open = true; draw(); }
  function setLang(lang) {
    if (lang === state.lang) return;
    var cp = currentPoem(), oldPage = state.page, cur = state.pages[oldPage], same;
    state.lang = lang; state.pages = buildPages(state.data, lang);
    if (cp) state.page = firstPageOf(state.pages, cp.n, cp.c || 0);
    else if (cur && cur.t !== "blank" && (same = pageIndex(cur.t, cur.id, cur.c)) >= 0) state.page = same;   // front/back matter keeps its place across languages
    else state.page = Math.min(oldPage, state.pages.length - 1);
    Array.prototype.forEach.call(el.langs.querySelectorAll("a"), function (a) { a.classList.toggle("on", a.dataset.lang === lang); });
    relabelChrome(); buildSheet(); draw();
  }
  function openBook() { if (state.open) return; state.open = true; state.page = 0; draw(); }
  function buildSheet() {
    var D = state.data, ui = D.ui[state.lang];
    el.sheet.innerHTML = '<button class="close" type="button">' + esc(ui.close) + '</button><p class="kick">' + esc(ui.main) + '</p><h2>' + esc(ui.contents) + '</h2><p class="kick" style="margin-top:.5rem">' + esc(ui.count) + '</p>' +
      '<div class="fm"><a href="#p0" data-p="0">' + esc(ui.epigraph_short) + '</a><a href="#p3" data-p="3">' + esc(ui.titlepage) + "</a>" + (D.portrait ? '<a href="#p' + pageIndex("author-plate") + '" data-p="' + pageIndex("author-plate") + '">' + esc(ui.about) + "</a>" : "") + '<a href="#p' + (state.pages.length - 2) + '" data-p="' + (state.pages.length - 2) + '">' + esc(ui.colophon_short) + '</a></div>' +
      contentsList(D, state.lang, contentsEntries(D), function (p) { return poemHref(p, state.lang); });
    el.sheet.dataset.mode = "toc";
  }
  function showSheet(on) { if (on && el.sheet.dataset.mode === "note") buildSheet(); el.overlay.hidden = !on; if (on) { var c = el.sheet.querySelector(".close"); if (c) c.focus(); } }
  /* the headnote of poem n in the sheet (for readers who arrived by link or from the contents, past the title plate) */
  function showNote(n) {
    var D = state.data, ui = D.ui[state.lang], p = poem(n), ot = p.texts[p.orig].title, pt = p.texts[state.lang].title;
    el.sheet.innerHTML = '<button class="close" type="button">' + esc(ui.close) + '</button><p class="kick">' + esc(ui.about_poem) + " · " + p.roman + '</p><h2>' + esc(tocTitle(p, state.lang)) + "</h2>" +
      (state.lang !== p.orig && ot !== pt ? '<p class="sheet-orig">' + esc(ot) + "</p>" : "") +
      '<p class="sheet-tools">' + listenBtn(n, state.lang) + "</p>" +
      '<p class="sheet-note">' + em((p.note || {})[state.lang] || "") + "</p>" +
      '<div class="fm"><a href="#" data-toc="1">' + esc(ui.contents) + "</a></div>";
    el.overlay.hidden = false; var c = el.sheet.querySelector(".close"); if (c) c.focus();
    el.sheet.dataset.mode = "note";
  }

  /* ---------- closed book: 3-D pose. Follows a fine pointer (walk around the book); otherwise a slow sway ---------- */
  var tilt = (function () {
    var tome = el.cover, REST = { ry: -26, rx: 7 }, cur = { ry: REST.ry, rx: REST.rx }, tgt = { ry: REST.ry, rx: REST.rx };
    var mx = 50, my = 32, raf = 0, ptr = false, ptrT = 0, t0 = 0, last = 0;
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)"), fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    function set() {
      tome.style.setProperty("--ry", cur.ry.toFixed(2) + "deg"); tome.style.setProperty("--rx", cur.rx.toFixed(2) + "deg");
      tome.style.setProperty("--mx", mx.toFixed(1) + "%"); tome.style.setProperty("--my", my.toFixed(1) + "%");
    }
    function frame(now) {
      if (!t0) { t0 = now; last = now; }
      var dt = Math.min(100, now - last); last = now;
      var k = 1 - Math.pow(.93, dt / 16.7), ks = 1 - Math.pow(.96, dt / 16.7);   /* frame-rate independent easing */
      if (ptr && now - ptrT > 2500) ptr = false;
      if (!ptr) {
        var t = (now - t0) / 1000;
        tgt.ry = REST.ry + Math.sin(t * .42) * 7; tgt.rx = REST.rx + Math.sin(t * .29 + 1) * 2.5;
        mx += ((50 - (tgt.ry - REST.ry) * 3) - mx) * ks; my += (32 - my) * ks;
      }
      cur.ry += (tgt.ry - cur.ry) * k; cur.rx += (tgt.rx - cur.rx) * k;
      set(); raf = requestAnimationFrame(frame);
    }
    function move(e) {
      if (!raf || !fine.matches) return;
      var r = el.stage.getBoundingClientRect();
      var nx = (e.clientX - (r.left + r.width / 2)) / (r.width * .9), ny = (e.clientY - (r.top + r.height / 2)) / (r.height * .8);
      nx = Math.max(-1, Math.min(1, nx)); ny = Math.max(-1, Math.min(1, ny));
      tgt.ry = REST.ry + (nx < 0 ? -nx * 60 : -nx * 16);   /* pointer left: turn to show the spine; right: more of the fore-edge */
      tgt.rx = REST.rx - ny * 8;
      mx = 50 + nx * 40; my = 35 + ny * 30; ptr = true; ptrT = performance.now();
    }
    function start() { if (!tome || state.open || reduce.matches || raf) return; t0 = 0; last = 0; raf = requestAnimationFrame(frame); }
    function stop(open) {
      if (raf) cancelAnimationFrame(raf); raf = 0;
      if (open && tome) { tome.style.setProperty("--ry", "0deg"); tome.style.setProperty("--rx", "0deg"); }
    }
    document.addEventListener("pointermove", move, { passive: true });
    document.addEventListener("mouseleave", function () { ptr = false; });
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(false); else start(); });
    return { start: start, stop: stop };
  })();

  /* ---------- lightbox: the sheet at full size; tap to zoom in on that spot, ←/→ between pages ---------- */
  var lb = { items: [], i: 0, zoom: false };
  function zoomSrc(src) { return src.replace(/\.jpg$/, "-x.jpg"); }
  function lbShow(i) {
    var it = lb.items[i]; lb.i = i; lb.zoom = false;
    el.lb.classList.remove("zoomed"); el.lbImg.src = BASE + zoomSrc(it.src) + "?v=" + VER; el.lbImg.alt = it.cap;
    el.lbCap.textContent = it.cap + (lb.items.length > 1 ? "  ·  " + (i + 1) + " / " + lb.items.length : "");
    document.getElementById("lb-prev").hidden = document.getElementById("lb-next").hidden = lb.items.length < 2;
  }
  function openLightbox(fig) {
    var D = state.data, lang = state.lang, ui = D.ui[lang];
    if (fig.dataset.n) {
      var p = poem(+fig.dataset.n), m = p.ms, base = [p.roman, p.texts[lang].title, ui.autograph, m.date].filter(Boolean).join(" · ");
      lb.items = m.pages.map(function (pg, k) { return { src: pg.src, cap: base }; });
    } else {
      var a = D.art[fig.dataset.art]; lb.items = [{ src: a.src, cap: [(a.title || {})[lang], (a.note || {})[lang]].filter(Boolean).join(" · ") }];
    }
    el.lb.hidden = false; document.body.classList.add("lb-open"); lbShow(0);
    document.getElementById("lb-close").focus();
  }
  function closeLightbox() { el.lb.hidden = true; document.body.classList.remove("lb-open"); el.lbImg.removeAttribute("src"); }
  function lbStep(d) { if (lb.items.length > 1) lbShow((lb.i + d + lb.items.length) % lb.items.length); }
  el.lbImg.addEventListener("click", function (e) {
    lb.zoom = !lb.zoom; el.lb.classList.toggle("zoomed", lb.zoom);
    if (lb.zoom) {                                   /* keep the tapped point under the finger */
      var r = el.lbStage.getBoundingClientRect(), fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      el.lbStage.scrollLeft = fx * el.lbImg.offsetWidth - r.width / 2; el.lbStage.scrollTop = fy * el.lbImg.offsetHeight - r.height / 2;
    }
  });
  document.getElementById("lb-close").addEventListener("click", closeLightbox);
  document.getElementById("lb-prev").addEventListener("click", function () { lbStep(-1); });
  document.getElementById("lb-next").addEventListener("click", function () { lbStep(1); });
  el.lb.addEventListener("click", function (e) { if (e.target === el.lb || e.target === el.lbStage) closeLightbox(); });
  document.addEventListener("click", function (e) { var b = e.target.closest("button.ms-sheet"); if (b && state.data) { e.preventDefault(); openLightbox(b.closest("figure.ms")); } });

  /* ---------- listening: recorded file first, device speech as fallback ---------- */
  var player = { audio: null, key: null, manifest: null, utter: null };   /* key = "<lang>/<n>" of what is playing */
  var SPEECH_LANG = { uk: "uk-UA", ru: "ru-RU", en: "en-US", es: "es-ES" };
  function setBtn(key, playing) {   /* every Listen button for this poem+language: on the leaf and in the About sheet */
    if (!key) return;
    var lang = key.split("/")[0], n = key.split("/")[1], ui = state.data.ui[lang] || state.data.ui[state.lang];
    document.querySelectorAll('button.listen[data-n="' + n + '"][data-lang="' + lang + '"]').forEach(function (btn) {
      btn.classList.toggle("playing", playing);
      btn.querySelector("span").textContent = playing ? ui.stop : ui.listen;
    });
  }
  function stopAll() {
    if (player.audio) { player.audio.pause(); player.audio = null; }
    if (window.speechSynthesis) speechSynthesis.cancel();
    setBtn(player.key, false); player.key = null;
  }
  function speakable(p, lang) {
    var t = p.texts[lang], parts = [];
    if (t.title !== "* * *") parts.push(t.title);
    t.chunks.forEach(function (c) { c.forEach(function (l) { if (l.trim() && !/^\*.+\*$/.test(l.trim())) parts.push(l.trim()); else if (!l.trim()) parts.push(""); }); });
    return parts;
  }
  function speakFallback(p, lang, key) {
    if (!window.speechSynthesis) return;
    var voices = speechSynthesis.getVoices(), want = SPEECH_LANG[lang], pick = null;
    voices.forEach(function (v) { if (v.lang.replace("_", "-").toLowerCase().indexOf(want.slice(0, 2)) === 0 && (!pick || /premium|enhanced|natural/i.test(v.name))) pick = v; });
    var lines = speakable(p, lang), text = lines.map(function (l) { return l === "" ? "\n" : l; }).join(",\n");
    var u = new SpeechSynthesisUtterance(text); u.lang = want; u.rate = 0.88; if (pick) u.voice = pick;
    u.onend = u.onerror = function () { if (player.key === key) { setBtn(key, false); player.key = null; } };
    player.utter = u; speechSynthesis.speak(u);
  }
  function listen(btn) {
    var n = +btn.dataset.n, lang = btn.dataset.lang, p = poem(n), key = lang + "/" + n;
    if (player.key === key) { stopAll(); return; }
    stopAll(); player.key = key; setBtn(key, true);
    var has = player.manifest && player.manifest[lang] && player.manifest[lang][String(n)];
    if (p.song && p.song.preview) {
      var pa = new Audio(p.song.preview); player.audio = pa;
      pa.onended = function () { if (player.audio === pa) { setBtn(key, false); player.key = null; player.audio = null; } };
      pa.onerror = function () { if (player.audio === pa) { setBtn(key, false); player.key = null; player.audio = null; } };
      pa.play().catch(function () { setBtn(key, false); player.key = null; player.audio = null; });
    } else if (has) {
      var a = new Audio(BASE + "audio/" + lang + "/" + n + ".m4a?v=" + (has.v || VER)); player.audio = a;   /* versioned: m4a is cached 7 days */
      a.onended = function () { if (player.audio === a) { setBtn(key, false); player.key = null; player.audio = null; } };
      a.onerror = function () { if (player.audio === a) { player.audio = null; speakFallback(p, lang, key); } };
      a.play().catch(function () { player.audio = null; speakFallback(p, lang, key); });
    } else speakFallback(p, lang, key);
  }
  fetch(BASE + "audio/manifest.json?v=" + VER).then(function (r) { return r.ok ? r.json() : {}; }).then(function (m) { player.manifest = m; }).catch(function () { player.manifest = {}; });
  if (window.speechSynthesis) speechSynthesis.getVoices();
  document.addEventListener("click", function (e) { var b = e.target.closest("button.listen"); if (b && state.data) { e.preventDefault(); listen(b); } });
  document.addEventListener("click", function (e) { var a = e.target.closest("a.src-poem"); if (a && state.data) { e.preventDefault(); goToPoem(+a.dataset.n, 0); } });
  document.addEventListener("click", function (e) { var b = e.target.closest("button.about-btn"); if (b && state.data) { e.preventDefault(); showNote(+b.dataset.about); } });

  /* ---------- wiring ---------- */
  function init(D) {
    state.data = D;
    D.poems.forEach(function (p) { LANGS.forEach(function (l) { if (!p.slug || !p.slug[l]) throw new Error("slug"); }); });
    state.pages = buildPages(D, state.lang);
    var m = /#c(\d+)/.exec(location.hash), mp = /#p(\d+)/.exec(location.hash);
    if (root.dataset.n) state.page = firstPageOf(state.pages, +root.dataset.n, m ? +m[1] : 0);
    else if (mp) state.page = Math.min(+mp[1], state.pages.length - 1);
    else if (state.open) state.page = 0;
    buildSheet(); draw();

    el.coverBtn.addEventListener("click", openBook);
    if (el.cta) el.cta.addEventListener("click", openBook);
    el.prevL.addEventListener("click", function () { turn(-1, step()); });
    el.prevR.addEventListener("click", function () { turn(-1, step()); });
    el.nextR.addEventListener("click", function () { turn(1, step()); });
    el.toc.addEventListener("click", function () { showSheet(true); });
    el.overlay.addEventListener("click", function (e) {
      if (e.target === el.overlay || e.target.closest(".close")) { showSheet(false); return; }
      var a = e.target.closest("a"); if (!a) return;
      e.preventDefault();
      if (a.dataset.toc) { buildSheet(); return; }
      if (a.dataset.n) goToPoem(+a.dataset.n, 0); else if (a.dataset.p) { state.page = +a.dataset.p; state.open = true; draw(); }
      showSheet(false);
    });
    el.langs.addEventListener("click", function (e) { var a = e.target.closest("a"); if (!a) return; e.preventDefault(); setLang(a.dataset.lang); });
    el.right.addEventListener("click", onTocLink); el.left.addEventListener("click", onTocLink);
    function onTocLink(e) { var a = e.target.closest("a[data-n]"); if (!a) return; e.preventDefault(); goToPoem(+a.dataset.n, 0); }
    document.addEventListener("keydown", function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (!el.lb.hidden) { if (e.key === "Escape") closeLightbox(); else if (e.key === "ArrowRight") lbStep(1); else if (e.key === "ArrowLeft") lbStep(-1); return; }
      if (!el.overlay.hidden) { if (e.key === "Escape") showSheet(false); return; }
      if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); turn(1, step()); }
      else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); turn(-1, step()); }
      else if (e.key === "Enter" && !state.open) openBook();
      else if (e.key === "Escape" && state.open) showSheet(true);
    });
    var tx = null, ty = null;
    document.addEventListener("touchstart", function (e) { tx = e.changedTouches[0].clientX; ty = e.changedTouches[0].clientY; }, { passive: true });
    document.addEventListener("touchend", function (e) {
      if (tx === null || !el.lb.hidden) { tx = ty = null; return; } var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty; tx = ty = null;
      if (Math.abs(dx) < 48 || Math.abs(dy) > Math.abs(dx)) return;
      turn(dx < 0 ? 1 : -1, step());
    }, { passive: true });
    spreadMode.addEventListener("change", draw);
    window.addEventListener("resize", markOverflow);
    window.addEventListener("popstate", function () { location.reload(); });
  }
  fetch(BASE + "data/poems.json?v=" + (root.dataset.v || "0")).then(function (r) { return r.json(); }).then(init).catch(function (err) { console.error("book: " + err.message); });
})();
