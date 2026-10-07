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
      const code = String(l).toLowerCase().split('-')[0];
      if (LANGS[code]) return code;
    }
    return 'en';
  }

  const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // the templates, the most specific first (the longest fixed text): "{0} failed: {1}" before "{0}: {1}"
  const RX = (D.modelos || []).map(m => [new RegExp('^' + m.split(/(\{\d+\})/).map(p =>
    /^\{\d+\}$/.test(p) ? '([\\s\\S]*?)' : escape(p)).join('') + '$'), m,
  m.replace(/\{\d+\}/g, '').length]).sort((a, b) => b[2] - a[2]);

  function line(s) {
    const dict = D.textos[lang];
    if (!dict) return s;
    const core = s.trim();
    if (!core || !/[A-Za-z]/.test(core)) return s;
    const lead = s.slice(0, s.indexOf(core)), trail = s.slice(s.indexOf(core) + core.length);
    if (dict[core]) return lead + dict[core] + trail;
    for (const [rx, m] of RX) {
      if (!dict[m]) continue;
      const g = core.match(rx);
      // a gap that is itself a known phrase ("Checking the map failed.") is translated too
      if (g) return lead + dict[m].replace(/\{(\d+)\}/g, (_x, i) => {
        const v = g[+i + 1] || '';
        return dict[v.trim()] || v;
      }) + trail;
    }
    return s;
  }
  // a text with line breaks (the cat's line) goes line by line
  const tr = s => (s.indexOf('\n') >= 0 ? s.split('\n').map(line).join('\n') : line(s));

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

  function start() {
    document.documentElement.lang = lang;
    walk(document.body);
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true,
      attributeFilter: ATTRS });
  }

  function setLang(code, quiet) {
    if (!LANGS[code] || code === lang) return;
    lang = code;
    if (!quiet) { try { localStorage.setItem(KEY, code); } catch (e) { /* the program keeps it in its settings */ } }
    document.documentElement.lang = code;
    walk(document.body);
    document.dispatchEvent(new CustomEvent('doctor-lang', { detail: code }));
  }

  window.doctorI18n = { langs: LANGS, get lang() { return lang; }, setLang, tr: s => (lang === 'en' ? s : tr(s)) };
  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
