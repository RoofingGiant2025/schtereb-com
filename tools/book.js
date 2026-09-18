/* Ноти життя: до і після — book reader. Progressive: every page is server-rendered; this turns it into a book. */
(function () {
  "use strict";
  var LANGS = ["uk", "ru", "en", "es"];
  var root = document.getElementById("book-root");
  if (!root) return;
  var BASE = root.dataset.base || "/";
  var state = { lang: root.dataset.lang || "uk", open: root.dataset.open === "1", page: 0, data: null, pages: null, turning: "none" };
  var spreadMode = window.matchMedia("(min-width: 768px)");
  var el = {
    stage: document.getElementById("stage"), book: document.getElementById("book"), cover: document.getElementById("cover"),
    left: document.getElementById("leaf-left"), right: document.getElementById("leaf-right"),
    prevL: document.getElementById("turn-prev-l"), prevR: document.getElementById("turn-prev-r"), nextR: document.getElementById("turn-next-r"),
    langs: document.getElementById("langs"), toc: document.getElementById("toc-btn"), folio: document.getElementById("folio-ind"),
    overlay: document.getElementById("overlay"), sheet: document.getElementById("sheet"), bottom: document.getElementById("chrome-bottom"),
    coverBtn: document.getElementById("cover-open")
  };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var ORN = {
    rule: '<svg class="orn rule" viewBox="0 0 180 12" fill="none" aria-hidden="true"><path d="M2 6h68" stroke="currentColor" stroke-width=".7" stroke-linecap="round"/><circle cx="90" cy="6" r="1.6" fill="currentColor"/><path d="M78 6h24" stroke="currentColor" stroke-width=".7" opacity=".5"/><path d="M110 6h68" stroke="currentColor" stroke-width=".7" stroke-linecap="round"/></svg>',
    staff: '<svg class="orn staff" viewBox="0 0 96 36" fill="none" aria-hidden="true"><path d="M4 8h88M4 14h88M4 20h88M4 26h88M4 32h88" stroke="currentColor" stroke-width=".7" opacity=".55"/><path d="M22 26c0-7 5-12 8-18 1 8-2 14-2 20 0 3 2 5 4 5 3 0 5-3 5-6 0-5-4-8-7-8-4 0-8 4-8 9 0 6 5 10 11 10 8 0 13-7 13-15" stroke="currentColor" stroke-width="1.15" stroke-linecap="round"/><ellipse cx="58" cy="24" rx="4.2" ry="3" fill="currentColor"/><path d="M62 24V10" stroke="currentColor" stroke-width="1.1"/><ellipse cx="74" cy="18" rx="4.2" ry="3" fill="currentColor"/><path d="M78 18V6" stroke="currentColor" stroke-width="1.1"/></svg>',
    light: '<svg class="orn light" viewBox="0 0 48 72" fill="none" aria-hidden="true"><path d="M24 6c0 18-10 28-10 46 0 8 4.4 14 10 14s10-6 10-14c0-18-10-28-10-46Z" stroke="currentColor" stroke-width="1.2" opacity=".85"/><path d="M24 10v46" stroke="currentColor" stroke-width=".8" opacity=".5"/></svg>',
    bfly: '<svg class="orn bfly" viewBox="0 0 64 48" fill="none" aria-hidden="true"><path d="M32 10c-8-10-22-6-24 6-1.5 9 8 14 24 22 16-8 25.5-13 24-22-2-12-16-16-24-6Z" stroke="currentColor" stroke-width="1.1"/><path d="M32 10v30" stroke="currentColor" stroke-width=".9"/><path d="M32 10c-2-6 2-8 0-10" stroke="currentColor" stroke-width=".9"/></svg>'
  };

  /* ---------- page model ---------- */
  function contentsEntries(D) {
    var out = [{ k: "part", id: "before" }], last = null;
    D.poems.forEach(function (p) {
      if (p.part === "after" && last !== "after") { out.push({ k: "part", id: "after" }); }
      else if (p.part === "before" && p.section && p.section !== last) { out.push({ k: "sec", id: p.section }); }
      last = p.part === "after" ? "after" : p.section;
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
    rightHand(); pages.push({ t: "part", id: "before" });
    var lastSec = null, lastPart = "before";
    D.poems.forEach(function (p) {
      if (p.part === "after" && lastPart !== "after") { rightHand(); pages.push({ t: "part", id: "after" }); }
      else if (p.part === "before" && p.section && p.section !== lastSec) { rightHand(); pages.push({ t: "section", id: p.section }); }
      lastSec = p.section; lastPart = p.part;
      var chunks = p.texts[p.orig].chunks.length;
      if (lang === p.orig) {
        rightHand(); pages.push({ t: "plate", n: p.n });
        for (var c = 0; c < chunks; c++) pages.push({ t: "poem", n: p.n, c: c });
      } else {
        if (pages.length % 2 === 1) pages.push({ t: "blank" });
        for (var c2 = 0; c2 < chunks; c2++) { pages.push({ t: "orig", n: p.n, c: c2 }); pages.push({ t: "poem", n: p.n, c: c2 }); }
      }
    });
    rightHand(); pages.push({ t: "colophon" });
    if (pages.length % 2 === 1) pages.push({ t: "blank" });
    pages.push({ t: "endpaper" });
    return pages;
  }
  function poem(n) { return state.data.poems[n - 1]; }
  function firstPageOf(pages, n, c) {
    c = c || 0;
    for (var i = 0; i < pages.length; i++) {
      var p = pages[i];
      if (p.n === n && (p.t === "orig" || p.t === "poem") && p.c === c) return i;
      if (p.n === n && p.t === "plate" && c === 0) return i;
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
      var cls = "stanza" + (drop && i === 0 && /^\p{L}/u.test(st[0].trim()) ? " drop" : "");
      return '<p class="' + cls + '">' + st.map(function (l) {
        var m = /^\*(.+)\*$/.exec(l.trim());
        return m ? '<span class="note">' + esc(m[1]) + '</span>' : '<span class="l">' + esc(l) + '</span>';
      }).join("") + "</p>";
    }).join("") + "</div>";
  }
  function poemBlock(title, lines, kicker, drop, cont) {
    return '<div class="poem">' + (kicker ? '<p class="kick">' + esc(kicker) + '</p>' : "") +
      '<h2 class="' + (cont ? "cont" : "") + '">' + esc(title) + "</h2>" + ORN.rule + verse(lines, drop) + "</div>";
  }
  function sectionName(id, lang) {
    var D = state.data;
    if (id === "before" || id === "after") return D.parts[id][lang];
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
      return '<li class="p"><a href="' + hrefFn(p) + '" data-n="' + p.n + '"><span class="r">' + p.roman + '</span><span class="t">' + esc(tocTitle(p, lang)) + "</span></a></li>";
    }).join("") + "</ol>";
  }
  function poemHref(p, lang) { return BASE + lang + "/" + p.slug[lang] + ".html"; }
  function render(page, lang) {
    var D = state.data, ui = D.ui[lang];
    switch (page.t) {
      case "endpaper": return { cls: "endpaper", body: '<img src="' + BASE + 'assets/img/endpaper.jpg" alt="">' };
      case "blank": return { body: '<div style="height:100%"></div>' };
      case "epigraph": return { body: '<div class="center">' + ORN.staff + '<p class="epi">Art Knows No Languages</p><p class="epi-by">Oleg Shtereb</p>' + (lang !== "en" ? '<p class="epi-tr">' + esc(ui.epigraph) + "</p>" : "") + "</div>" };
      case "half": return { body: '<div class="center"><p class="kick">' + esc(ui.first) + '</p><h2 class="ht-main">' + esc(ui.main) + '</h2><p class="ht-sub">' + esc(ui.sub) + "</p></div>" };
      case "frontis": return { body: '<figure class="frontis" style="margin:0"><img src="' + BASE + 'assets/img/frontispiece.jpg" alt=""></figure>' };
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
        return { body: '<div class="center">' + mark + '<p class="plate-num">' + p.roman + '</p><h2 class="plate-title">' + esc(p.texts[lang].title) + "</h2></div>" };
      }
      case "orig": {
        var po = poem(page.n), to = po.texts[po.orig];
        return { body: poemBlock(to.title, to.chunks[page.c], page.c === 0 ? ui.original : ui.continued, false, page.c > 0) };
      }
      case "poem": {
        var pp = poem(page.n), tp = pp.texts[lang], isO = lang === pp.orig;
        return { body: poemBlock(tp.title, tp.chunks[page.c], isO ? (page.c > 0 ? ui.continued : "") : (page.c === 0 ? ui.translation : ui.continued), page.c === 0, page.c > 0) };
      }
      case "colophon": return { body: '<div class="center">' + ORN.rule + '<p class="colo">' + esc(ui.colophon) + '</p><p class="colo-house">' + esc(ui.house) + " · " + esc(ui.published) + "</p>" + ORN.rule + "</div>" };
    }
    return { body: "" };
  }
  function leafHTML(page, lang, side, folio) {
    if (!page) return '<div class="leaf"><div class="leaf-body"></div></div>';
    var r = render(page, lang), ui = state.data.ui[lang];
    if (r.cls === "endpaper") return '<div class="leaf endpaper">' + r.body + "</div>";
    var foot = side === "left" ? '<span class="n">' + folio + "</span><span>" + esc(state.data.author[lang]) + "</span>" : "<span>" + esc(ui.main) + '</span><span class="n">' + folio + "</span>";
    return '<div class="leaf"><div class="leaf-body">' + r.body + '</div><footer class="leaf-foot">' + foot + "</footer></div>";
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
    el.bottom.hidden = !state.open;
    el.stage.className = "stage " + (state.open ? "open" : "closed");
    el.cover.dataset.open = state.open ? "true" : "false";
    document.documentElement.lang = state.lang;
    syncURL();
    try { localStorage.setItem("book.lang", state.lang); localStorage.setItem("book.page." + state.lang, String(state.page)); } catch (e) { }
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
    var target = dir > 0 ? Math.min(state.pages.length - 1, state.page + n) : Math.max(0, state.page - n);
    if (target === state.page) return;
    state.page = target;
    el.book.classList.add("turning"); el.book.dataset.dir = dir > 0 ? "next" : "prev";
    clearTimeout(turn.timer);
    turn.timer = setTimeout(function () { el.book.classList.remove("turning"); el.book.dataset.dir = "none"; draw(); }, 170);
  }
  function goToPoem(n, c) { state.page = firstPageOf(state.pages, n, c || 0); state.open = true; draw(); }
  function setLang(lang) {
    if (lang === state.lang) return;
    var cp = currentPoem(), oldPage = state.page;
    state.lang = lang; state.pages = buildPages(state.data, lang);
    if (cp) state.page = firstPageOf(state.pages, cp.n, cp.c || 0); else state.page = Math.min(oldPage, state.pages.length - 1);
    Array.prototype.forEach.call(el.langs.querySelectorAll("a"), function (a) { a.classList.toggle("on", a.dataset.lang === lang); });
    buildSheet(); draw();
  }
  function openBook() { if (state.open) return; state.open = true; state.page = 0; draw(); }
  function buildSheet() {
    var D = state.data, ui = D.ui[state.lang];
    el.sheet.innerHTML = '<button class="close" type="button">' + esc(ui.close) + '</button><p class="kick">' + esc(ui.main) + '</p><h2>' + esc(ui.contents) + '</h2><p class="kick" style="margin-top:.5rem">' + esc(ui.count) + '</p>' +
      '<div class="fm"><a href="#p0" data-p="0">' + esc(ui.epigraph_short) + '</a><a href="#p3" data-p="3">' + esc(ui.titlepage) + '</a><a href="#p' + (state.pages.length - 2) + '" data-p="' + (state.pages.length - 2) + '">' + esc(ui.colophon_short) + '</a></div>' +
      contentsList(D, state.lang, contentsEntries(D), function (p) { return poemHref(p, state.lang); });
  }
  function showSheet(on) { el.overlay.hidden = !on; if (on) { var c = el.sheet.querySelector(".close"); if (c) c.focus(); } }

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
    el.prevL.addEventListener("click", function () { turn(-1, step()); });
    el.prevR.addEventListener("click", function () { turn(-1, step()); });
    el.nextR.addEventListener("click", function () { turn(1, step()); });
    el.toc.addEventListener("click", function () { showSheet(true); });
    el.overlay.addEventListener("click", function (e) {
      if (e.target === el.overlay || e.target.closest(".close")) { showSheet(false); return; }
      var a = e.target.closest("a"); if (!a) return;
      e.preventDefault();
      if (a.dataset.n) goToPoem(+a.dataset.n, 0); else if (a.dataset.p) { state.page = +a.dataset.p; state.open = true; draw(); }
      showSheet(false);
    });
    el.langs.addEventListener("click", function (e) { var a = e.target.closest("a"); if (!a) return; e.preventDefault(); setLang(a.dataset.lang); });
    el.right.addEventListener("click", onTocLink); el.left.addEventListener("click", onTocLink);
    function onTocLink(e) { var a = e.target.closest("a[data-n]"); if (!a) return; e.preventDefault(); goToPoem(+a.dataset.n, 0); }
    document.addEventListener("keydown", function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (!el.overlay.hidden) { if (e.key === "Escape") showSheet(false); return; }
      if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); turn(1, step()); }
      else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); turn(-1, step()); }
      else if (e.key === "Enter" && !state.open) openBook();
      else if (e.key === "Escape" && state.open) showSheet(true);
    });
    var tx = null, ty = null;
    document.addEventListener("touchstart", function (e) { tx = e.changedTouches[0].clientX; ty = e.changedTouches[0].clientY; }, { passive: true });
    document.addEventListener("touchend", function (e) {
      if (tx === null) return; var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty; tx = ty = null;
      if (Math.abs(dx) < 48 || Math.abs(dy) > Math.abs(dx)) return;
      turn(dx < 0 ? 1 : -1, step());
    }, { passive: true });
    spreadMode.addEventListener("change", draw);
    window.addEventListener("popstate", function () { location.reload(); });
  }
  fetch(BASE + "data/poems.json", { cache: "force-cache" }).then(function (r) { return r.json(); }).then(init).catch(function (err) { console.error("book: " + err.message); });
})();
