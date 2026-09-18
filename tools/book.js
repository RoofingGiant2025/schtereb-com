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
      if (p.ms) { leftHand(); pages.push({ t: "ms", n: p.n }); } else rightHand();
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
    var t = (a.title || {})[lang] || "", n = (a.note || {})[lang] || "";
    return '<figure class="ms art" data-art="' + key + '"><button type="button" class="ms-sheet" aria-label="' + esc(t) + '"><img src="' + BASE + a.src + '?v=' + VER + '" alt="' + esc(t) + '" width="' + a.w + '" height="' + a.h + '" decoding="async"></button>' +
      '<figcaption><span class="c">' + esc(t) + (n ? ' · ' + esc(n) : "") + "</span></figcaption></figure>";
  }
  function msHTML(p, lang) {
    var ui = state.data.ui[lang], m = p.ms, pg = m.pages[0];
    var cap = [ui.autograph, m.date, (m.medium || {})[lang]].filter(Boolean).join(" · "), note = (m.note || {})[lang];
    return '<figure class="ms" data-n="' + p.n + '"><button type="button" class="ms-sheet" aria-label="' + esc(ui.zoom) + '"><img src="' + BASE + pg.src + '?v=' + VER + '" alt="' + esc(ui.manuscript) + ' — ' + esc(p.texts[lang].title) + '" width="' + pg.w + '" height="' + pg.h + '" decoding="async">' +
      (m.pages.length > 1 ? '<span class="ms-more">1 ' + esc(ui.of_pages) + " " + m.pages.length + "</span>" : "") + "</button>" +
      '<figcaption><span class="r">' + p.roman + '</span><span class="c">' + esc(cap) + (note ? '<br>' + esc(note) : "") + "</span></figcaption></figure>";
  }
  var byN = null;
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
      case "blank": return { body: '<div style="height:100%"></div>' };
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
        return { body: '<div class="center">' + ORN.staff + '<h2 class="sec-title">' + esc(name) + "</h2>" + (sub !== name ? '<p class="sec-sub">' + esc(sub) + "</p>" : "") + "</div>" };
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
