// i18n.js - the page in the user's language (1.6.5). The code writes English; this file translates what reaches the
// document: every text node and the title / placeholder / aria-label attributes, by the dictionary of the language
// (i18n_data.js, made by common/gui/i18n_textos.py) -- a whole phrase, or a template whose gaps ({0}, {1}...) take the
// values the code put in the English text ("Exported {0} texts to {1}."). The English a node had is kept, so the
// language can change without reloading. Code, ids and file names (pre, code, .mono, inputs) are never touched.
// The language: the one chosen before (this browser, or the program's settings), else the system's, else English.
'use strict';

(function () {
  const D = window.I18N_DATA || { linguas: {}, modelos: [], textos: {} };
  const LANGS = Object.assign({ en: 'English' }, D.linguas);
  const KEY = 'doctor.lang';
  const ATTRS = ['title', 'placeholder', 'aria-label'];
  const SKIP = 'pre, code, textarea, script, style, input, [translate="no"], .mono, .cmd';
  const orig = new WeakMap();        // text node -> its English
  const written = new WeakMap();     // text node -> what this file wrote into it
  const origAttr = new WeakMap();    // element -> {attribute: English}
  let lang = pick();

  function pick() {
    let saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* storage off: the system's language */ }
    if (saved && LANGS[saved]) return saved;
    for (const l of navigator.languages || [navigator.language || 'en']) {
      const low = String(l).toLowerCase();
      // Chinese in Traditional script: Taiwan, Hong Kong, Macau, or zh-Hant anywhere
      if (/^zh-(tw|hk|mo|hant)\b/.test(low) && LANGS['zh-TW']) return 'zh-TW';
      const code = low.split('-')[0];
      if (LANGS[code]) return code;
    }
    return 'en';
  }

  const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // the templates, the most specific first (the longest fixed text): "{0} failed: {1}" before "{0}: {1}". Each keeps
  // its longest fixed piece (a cheap test before the expression) and how many letters its fixed text has
  // Two expressions per template, the gaps lazy and greedy: with two gaps side by side ("tampered with{0} ({1})."
  // over " (w3p mark) (header size ...)") one split leaves English in a gap and the other does not
  const rxOf = (m, gap) => new RegExp('^' + m.split(/(\{\d+\})/).map(p =>
    /^\{\d+\}$/.test(p) ? gap : escape(p)).join('') + '$');
  const RX = (D.modelos || []).map(m => {
    const fixed = m.split(/\{\d+\}/);
    return [rxOf(m, '([\\s\\S]*?)'), m, fixed.join('').length,
      fixed.reduce((a, b) => (b.length > a.length ? b : a), ''), (fixed.join('').match(/[A-Za-z]/g) || []).length,
      /\{\d+\}[^A-Za-z]*\{\d+\}/.test(m) ? rxOf(m, '([\\s\\S]*)') : null];
  }).sort((a, b) => b[2] - a[2]);
  // a gap that reads as English words, not a value (a number, a name, a path)
  const WORDS = /[A-Za-z]{2,}\s+[A-Za-z]{2,}/;
  const COUNTS = /^(.*?[A-Za-z].*?)((?:\s*\(\d+\))+)$/;
  // a template of bare words and gaps, no punctuation
  const BARE = /^[A-Za-z ]*(\{\d+\}[A-Za-z ]*)+$/;
  // the bullets and the indent of a report line stay as they are around the text
  const LEAD = /^[\s\-*•·>]*/;

  function line(s, depth) {
    const dict = D.textos[lang];
    if (!dict) return s;
    // the whole text first ("· runs in your browser" is a phrase as it is), then without its bullet
    const whole = s.trim();
    if (whole && dict[whole]) return s.slice(0, s.indexOf(whole)) + dict[whole] + s.slice(s.indexOf(whole) + whole.length);
    const lead = s.match(LEAD)[0];
    const core = s.slice(lead.length).trim();
    if (!core || !/[A-Za-z]/.test(core)) return s;
    const trail = s.slice(lead.length + s.slice(lead.length).indexOf(core) + core.length);
    const mid = s.slice(lead.length, lead.length + s.slice(lead.length).indexOf(core));
    if (dict[core]) return lead + mid + dict[core] + trail;
    // counts at the end stay as they are: "Unit events (2) (241)" is "Unit events" and its counts
    const counted = core.match(COUNTS);
    if (counted && !(depth > 0)) {
      const t = line(counted[1], 1);
      if (t !== counted[1]) return lead + mid + t + counted[2] + trail;
    }
    // among every template that matches, the one that leaves the fewest English gaps ("Fix map: result" is the page's
    // "{0}: result", not the report's "Fix map: {0}" with "result" left in English); the longest first on a tie
    let overall = null;
    for (const [rx, m, , piece, letters, greedy] of RX) {
      if (!dict[m] || (piece && core.indexOf(piece) < 0)) continue;
      let best = null;
      for (const r of greedy ? [rx, greedy] : [rx]) {
        const g = core.match(r);
        if (!g) continue;
        const gaps = g.slice(1);
        // a template that is only a few words and a gap ("Player {0}", made for "Player 1") does not take a sentence
        // as its gap: "Player name that activates it" is another text. One with punctuation ("Map: {0}  ({1})") does
        if (letters < 12 && BARE.test(m) && gaps.some(v => WORDS.test(v) && !dict[v.trim()])) continue;
        // each gap that is itself a known text ("Checking the map failed.", an extra's name) is translated too, with
        // the spaces around it kept; the split that leaves the fewest English gaps wins
        let left = 0;
        const done = gaps.map(v => {
          const t = gap(v, depth);
          // English left in a gap: a word, not a name (a file, a path, an identifier, a number)
          if (t === v && /[A-Za-z]{3,}/.test(v) && !/[._\\\/0-9]|[a-z][A-Z]/.test(v.trim())) left++;
          return t;
        });
        if (!best || left < best[1]) best = [done, left];
        if (!left) break;
      }
      if (!best) continue;
      const out = lead + mid + dict[m].replace(/\{(\d+)\}/g, (_x, i) => best[0][+i] || '') + trail;
      if (!best[1]) return out;
      if (!overall || best[1] < overall[1]) overall = [out, best[1]];
    }
    return overall ? overall[0] : s;
  }

  function gap(v, depth) {
    const dict = D.textos[lang];
    const t = v.trim();
    if (!t) return v;
    const pre = v.slice(0, v.indexOf(t)), post = v.slice(v.indexOf(t) + t.length);
    if (dict[t]) return pre + dict[t] + post;
    if ((depth || 0) < 1 && /[A-Za-z]{2,}/.test(t)) {
      const x = line(t, (depth || 0) + 1);
      if (x !== t) return pre + x + post;
    }
    return v;
  }
  // a text with line breaks (the cat's line) goes line by line
  const tr = s => (s.indexOf('\n') >= 0 ? s.split('\n').map(x => line(x)).join('\n') : line(s));

  function skipped(node) {
    const p = node.nodeType === 1 ? node : node.parentElement;
    return !p || !!p.closest(SKIP);
  }

  function doText(node) {
    if (skipped(node)) return;
    let o = orig.get(node);
    if (o === undefined || node.data !== written.get(node)) {
      o = node.data;                    // new English from the code
      orig.set(node, o);
    }
    const out = lang === 'en' ? o : tr(o);
    if (node.data !== out) node.data = out;
    written.set(node, out);
  }

  function doAttrs(el) {
    if (skipped(el)) return;
    let o = origAttr.get(el);
    if (!o) { o = {}; origAttr.set(el, o); }
    for (const a of ATTRS) {
      if (!el.hasAttribute(a)) continue;
      const v = el.getAttribute(a);
      if (o[a] === undefined || v !== o['=' + a]) o[a] = v;
      const out = lang === 'en' ? o[a] : tr(o[a]);
      o['=' + a] = out;
      if (v !== out) el.setAttribute(a, out);
    }
  }

  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) { doText(root); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    if (root.nodeType === 1) doAttrs(root);
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (n.nodeType === 3) doText(n);
      else doAttrs(n);
    }
  }

  const observer = new MutationObserver(list => {
    for (const m of list) {
      if (m.type === 'characterData') doText(m.target);
      else if (m.type === 'attributes') doAttrs(m.target);
      else m.addedNodes.forEach(walk);
    }
  });

  // 1.6.7: the dictionary of each language is its own file (lang/<code>.js), loaded when the language is picked: the
  // page shows English until it arrives, then translates itself
  const loading = {};
  function load(code) {
    if (code === 'en' || D.textos[code]) return Promise.resolve();
    if (!loading[code]) {
      loading[code] = new Promise(resolve => {
        const s = document.createElement('script');
        s.src = 'lang/' + code + '.js';
        s.onload = s.onerror = () => resolve();
        document.head.appendChild(s);
      });
    }
    return loading[code];
  }

  function start() {
    document.documentElement.lang = lang;
    load(lang).then(() => walk(document.body));
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true,
      attributeFilter: ATTRS });
  }

  function setLang(code, quiet) {
    if (!LANGS[code] || code === lang) return;
    lang = code;
    if (!quiet) { try { localStorage.setItem(KEY, code); } catch (e) { /* the program keeps it in its settings */ } }
    document.documentElement.lang = code;
    load(code).then(() => {
      if (lang !== code) return;
      walk(document.body);
      document.dispatchEvent(new CustomEvent('doctor-lang', { detail: code }));
    });
  }

  window.doctorI18n = { langs: LANGS, get lang() { return lang; }, setLang, tr: s => (lang === 'en' ? s : tr(s)) };
  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
