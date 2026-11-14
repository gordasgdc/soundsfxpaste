(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const T = window.I18N;
  const el = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) { if (v === false || v == null) continue; if (k === 'class') n.className = v; else if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v === true ? '' : v); }
    for (const c of kids.flat()) if (c != null) n.append(c.nodeType ? c : document.createTextNode(String(c)));
    return n;
  };
  const icon = (id) => { const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); s.setAttribute('class', 'ic'); const u = document.createElementNS('http://www.w3.org/2000/svg', 'use'); u.setAttribute('href', `#i-${id}`); s.append(u); return s; };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  window.addEventListener('unhandledrejection', (e) => setMsg('err', 'ERR_INTERNAL: ' + (e.reason && (e.reason.stack || e.reason.message) || e.reason)));
  window.addEventListener('error', (e) => setMsg('err', 'ERR_INTERNAL: ' + e.message + ' @' + e.lineno + ':' + e.colno));
  // ---------- state ----------
  let L = 'en', B = null, cfg = {}, files = [], byPath = new Map(), tab = 'folders', node = 'all', q = '', sel = null, view = [];
  let status = null, route = null, rm = null, pendingLong = null, logLines = [], settingsDir = '';
  const defaults = { roots: [], favorites: [], recent: [], vol: 80, dens: 45, hover: false, warn: 10 };
  const t = (k, v = {}) => (T[L][k] ?? T.en[k] ?? k).replace(/\{(\w+)\}/g, (_, x) => v[x] ?? '');
  const saveCfg = (patch) => { Object.assign(cfg, patch); return window.ssfx.saveCfg(patch); };
  const errText = (r) => t(r.code || 'ERR_INTERNAL', { detail: r.detail || '' });

  async function api(path, body) {
    if (!B) return { ok: false, code: 'ERR_NO_RESOLVE' };
    const o = { headers: { 'X-SSFX-Token': B.token, 'Content-Type': 'application/json' } };
    if (body !== undefined) { o.method = 'POST'; o.body = JSON.stringify(body); }
    const r = await fetch(`http://127.0.0.1:${B.port}${path}`, o); return r.json();
  }
  const audioUrl = (f) => `http://127.0.0.1:${B.port}/audio?path=${encodeURIComponent(f.path)}&t=${encodeURIComponent(B.token)}`;

  // ---------- time helpers ----------
  const fmtDur = (s) => (s == null ? '–' : s < 10 ? s.toFixed(2).replace(/^0/, '0') + ' s' : s < 60 ? s.toFixed(1) + ' s' : `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`);
  const tcOf = (rel) => { const r = Math.round(status.fps), a = status.start + rel, f = a % r, s = Math.floor(a / r); return [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60].map((x) => String(x).padStart(2, '0')).join(':') + ':' + String(f).padStart(2, '0'); };
  const khz = (sr) => (sr ? (sr % 1000 ? (sr / 1000).toFixed(1) : String(sr / 1000)) + ' kHz' : null);

  // ---------- messages / log ----------
  const txt = (x) => (typeof x === 'function' ? x() : x);
  let curMsg = null;
  function setMsg(kind, text, code) { curMsg = { kind, text }; renderMsg(); logLines.unshift({ kind, text, at: new Date() }); logLines.length = Math.min(logLines.length, 80); renderLog(); try { window.ssfx.log(kind === 'err' ? 'WARN' : 'INFO', 'ui', txt(text) + (code ? ` [${code}]` : '')); } catch {} }
  function renderMsg() { const m = $('msg'); m.className = 'msg ' + (curMsg ? curMsg.kind : ''); m.textContent = curMsg ? txt(curMsg.text) : ''; }
  function clearMsg() { curMsg = null; renderMsg(); }
  function renderLog() { const ul = $('log-list'); ul.textContent = ''; for (const l of logLines) ul.append(el('li', { class: l.kind }, `${l.at.toLocaleTimeString()}  ${txt(l.text)}`)); }

  // ---------- IndexedDB cache for waveforms ----------
  let dbp = null;
  const db = () => dbp || (dbp = new Promise((res) => { try { const r = indexedDB.open('ssfx', 1); r.onupgradeneeded = () => r.result.createObjectStore('peaks'); r.onsuccess = () => res(r.result); r.onerror = () => res(null); } catch { res(null); } }));
  const idb = async (mode, fn) => { const d = await db(); if (!d) return null; return new Promise((res) => { try { const tx = d.transaction('peaks', mode); const rq = fn(tx.objectStore('peaks')); tx.oncomplete = () => res(rq && rq.result); tx.onerror = () => res(null); } catch { res(null); } }); };
  const keyOf = (f) => `${f.path}|${f.size}|${f.mtime}`;

  // ---------- decode / analysis ----------
  let ctx = null; const gainNode = { n: null };
  const ac = () => { if (!ctx) { ctx = new AudioContext(); gainNode.n = ctx.createGain(); gainNode.n.connect(ctx.destination); setVol(); } return ctx; };
  const bufs = new Map(); const meta = new Map(); // meta: path -> {peaks, duration}
  function setVol() { if (gainNode.n) gainNode.n.gain.value = Math.pow(cfg.vol / 100, 2); }
  let active = 0; const waiters = [];
  const slot = () => new Promise((r) => { if (active < 3) { active++; r(); } else waiters.push(r); });
  const free = () => { active--; const w = waiters.shift(); if (w) { active++; w(); } };
  async function decode(f) {
    if (bufs.has(f.path)) { const b = bufs.get(f.path); bufs.delete(f.path); bufs.set(f.path, b); return b; }
    const ab = await (await fetch(audioUrl(f))).arrayBuffer();
    const buf = await ac().decodeAudioData(ab);
    bufs.set(f.path, buf); if (bufs.size > 10) bufs.delete(bufs.keys().next().value);
    return buf;
  }
  function peaksOf(buf, n = 160) {
    const out = new Float32Array(n), ch = buf.numberOfChannels, len = buf.length, step = len / n;
    const data = []; for (let c = 0; c < ch; c++) data.push(buf.getChannelData(c));
    for (let i = 0; i < n; i++) { let m = 0; const a = Math.floor(i * step), b = Math.min(len, Math.floor((i + 1) * step)); const hop = Math.max(1, Math.floor((b - a) / 64));
      for (let j = a; j < b; j += hop) for (let c = 0; c < ch; c++) { const v = Math.abs(data[c][j]); if (v > m) m = v; } out[i] = m; }
    return out;
  }
  async function analyze(f) {
    if (meta.has(f.path)) return meta.get(f.path);
    const cached = await idb('readonly', (s) => s.get(keyOf(f)));
    if (cached && cached.peaks) { meta.set(f.path, cached); return cached; }
    await slot();
    try {
      const buf = await decode(f); const m = { peaks: peaksOf(buf), duration: buf.duration };
      meta.set(f.path, m); idb('readwrite', (s) => s.put(m, keyOf(f))); return m;
    } catch { const m = { peaks: null, duration: f.duration || null, error: true }; meta.set(f.path, m); return m; } finally { free(); }
  }
  const durOf = (f) => (f.duration != null ? f.duration : meta.get(f.path)?.duration ?? null);

  function drawWave(canvas, peaks, color = getComputedStyle(document.documentElement).getPropertyValue('--wave') || '#d9c9ad', range) {
    const dpr = window.devicePixelRatio || 1, w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    const g = canvas.getContext('2d'); g.scale(dpr, dpr); g.clearRect(0, 0, w, h);
    if (!peaks) { g.fillStyle = 'rgba(255,255,255,.12)'; g.fillRect(0, h / 2 - .5, w, 1); return; }
    const n = peaks.length, bw = w / n; g.fillStyle = color.trim();
    for (let i = 0; i < n; i++) { const a = Math.max(1, peaks[i] * (h - 2)); const x = i * bw;
      if (range) { const p = i / n; g.globalAlpha = p >= range[0] && p <= range[1] ? 1 : .28; } g.fillRect(x + .5, (h - a) / 2, Math.max(1, bw - 1), a); }
    g.globalAlpha = 1;
  }

  // ---------- audition ----------
  let cur = null; // {path, src, t0, dur, card}
  function stopPlay() { if (!cur) return; try { cur.src.onended = null; cur.src.stop(); } catch {} cur.card?.classList.remove('playing'); if (cur.prog) cur.prog.style.width = '0'; cancelAnimationFrame(cur.raf); const icn = cur.card?.querySelector('.play use'); if (icn) icn.setAttribute('href', '#i-play'); cur = null; }
  async function play(f, card) {
    if (cur && cur.path === f.path) { stopPlay(); return; }
    stopPlay(); ac(); if (ctx.state === 'suspended') await ctx.resume();
    let buf; try { buf = await decode(f); } catch { setMsg('err', () => t('ERR_DECODE')); return; }
    const src = ctx.createBufferSource(); src.buffer = buf; src.connect(gainNode.n); src.start();
    const prog = card?.querySelector('.prog'); cur = { path: f.path, src, t0: ctx.currentTime, dur: buf.duration, card, prog };
    card?.classList.add('playing'); card?.querySelector('.play use')?.setAttribute('href', '#i-stop');
    src.onended = () => { if (cur && cur.src === src) stopPlay(); };
    const tick = () => { if (!cur || cur.src !== src) return; const p = clamp((ctx.currentTime - cur.t0) / cur.dur, 0, 1); if (prog) prog.style.width = (p * 100) + '%'; cur.raf = requestAnimationFrame(tick); }; tick();
  }

  // ---------- library ----------
  async function loadLibrary() {
    await api('/library/set', { roots: cfg.roots }); files = [];
    for (const r of cfg.roots) { const d = await api('/library/list', { root: r }); if (d.ok) for (const f of d.files) { f.root = r; f.dir = f.rel.includes('/') ? f.rel.slice(0, f.rel.lastIndexOf('/')) : ''; files.push(f); } }
    byPath = new Map(files.map((f) => [f.path, f])); buildTree(); render();
  }
  let treeNodes = [];
  function buildTree() {
    treeNodes = [{ key: 'all', label: () => t('allSounds'), depth: 0, count: files.length }];
    for (const r of cfg.roots) {
      const rf = files.filter((f) => f.root === r); treeNodes.push({ key: r + '|', label: () => r.split('/').pop(), depth: 0, count: rf.length, root: r });
      const dirs = [...new Set(rf.map((f) => f.dir).filter(Boolean))]; const all = new Set();
      for (const d of dirs) { const parts = d.split('/'); for (let i = 1; i <= parts.length; i++) all.add(parts.slice(0, i).join('/')); }
      for (const d of [...all].sort()) treeNodes.push({ key: r + '|' + d, label: () => d.split('/').pop(), depth: d.split('/').length, count: rf.filter((f) => f.dir === d || f.dir.startsWith(d + '/')).length });
    }
    if (!treeNodes.some((n) => n.key === node)) node = 'all';
  }
  function renderTree() {
    const tree = $('tree'); tree.textContent = '';
    for (const n of treeNodes) {
      const row = el('div', { class: 'node', role: 'treeitem', 'aria-selected': String(n.key === node), style: `padding-left:${8 + n.depth * 12}px`, onclick: () => { node = n.key; if (tab !== 'folders') setTab('folders'); else render(); } },
        icon('folder'), el('span', { class: 'n' }, n.label()), el('span', { class: 'c' }, n.count));
      if (n.root) row.append(el('button', { class: 'icon sm rm', title: t('removeFolder'), onclick: async (e) => { e.stopPropagation(); await saveCfg({ roots: cfg.roots.filter((r) => r !== n.root) }); await loadLibrary(); } }, icon('trash')));
      tree.append(row);
    }
    const ns = $('narrow-folder'); ns.textContent = ''; for (const n of treeNodes) ns.append(el('option', { value: n.key, selected: n.key === node }, ' '.repeat(n.depth * 2) + n.label()));
  }
  function filtered() {
    let list;
    if (tab === 'fav') { const s = new Set(cfg.favorites); list = files.filter((f) => s.has(f.path)); }
    else if (tab === 'recent') list = cfg.recent.map((p) => byPath.get(p)).filter(Boolean);
    else if (node === 'all') list = files;
    else { const [r, d] = node.split('|'); list = files.filter((f) => f.root === r && (!d || f.dir === d || f.dir.startsWith(d + '/'))); }
    const s = q.trim().toLowerCase(); return s ? list.filter((f) => f.rel.toLowerCase().includes(s)) : list;
  }

  let io = null;
  function render() {
    renderTree(); renderTabs();
    const auto = tab === 'auto'; $('grid').hidden = auto; $('auto').hidden = !auto; document.querySelector('.searchbar').style.display = auto && !rm ? 'none' : '';
    renderRm();
    if (auto) { renderAuto(); $('empty').hidden = true; return; }
    view = filtered(); const g = $('grid'); g.textContent = ''; stopPlay();
    io?.disconnect(); io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { io.unobserve(e.target); const f = byPath.get(e.target.dataset.p); analyze(f).then((m) => { drawWave(e.target.querySelector('canvas'), m.peaks); updateCardMeta(e.target, f); }); } }), { root: g, rootMargin: '200px' });
    for (const f of view) g.append(card(f));
    const em = $('empty'); em.hidden = view.length > 0; em.textContent = !files.length ? t('emptyLib') : tab === 'fav' ? t('emptyFav') : tab === 'recent' ? t('emptyRecent') : t('noMatch');
    if (sel && !view.some((f) => f.path === sel)) sel = null; markSel();
  }
  const isFav = (p) => cfg.favorites.includes(p);
  function updateCardMeta(c, f) { const d = durOf(f); const m = c.querySelector('.dur'); if (m) m.textContent = fmtDur(d); }
  function card(f) {
    const c = el('div', { class: 'card', role: 'option', 'aria-selected': 'false', 'data-p': f.path, draggable: 'true', title: f.rel },
      el('div', { class: 'wv' }, el('canvas'), el('div', { class: 'prog' })),
      el('div', { class: 'name' }, f.name.replace(/\.[^.]+$/, '')),
      el('div', { class: 'meta' }, el('span', { class: 'dur' }, fmtDur(durOf(f))), khz(f.sr) && el('span', { class: 'badge' }, khz(f.sr)), f.ch && el('span', { class: 'badge' }, f.ch === 1 ? 'Mono' : f.ch === 2 ? 'Stereo' : f.ch + ' ch')),
      el('button', { class: 'play icon sm', title: t('audition'), onclick: (e) => { e.stopPropagation(); choose(f.path); play(f, c); } }, icon('play')),
      el('div', { class: 'acts' },
        el('button', { class: 'fav', title: t('favorite'), 'aria-pressed': String(isFav(f.path)), onclick: (e) => { e.stopPropagation(); toggleFav(f.path); } }, icon('star')),
        el('button', { title: t('placeHere'), onclick: (e) => { e.stopPropagation(); choose(f.path); place(f); } }, icon('place'))));
    c.addEventListener('click', () => { choose(f.path); play(f, c); });
    c.addEventListener('dblclick', () => place(f));
    c.addEventListener('dragstart', (e) => { e.preventDefault(); window.ssfx.startDrag(f.path); });
    let ht; c.addEventListener('mouseenter', () => { if (cfg.hover) ht = setTimeout(() => play(f, c), 220); }); c.addEventListener('mouseleave', () => { clearTimeout(ht); if (cfg.hover && cur && cur.path === f.path) stopPlay(); });
    io?.observe(c); return c;
  }
  function choose(p) { sel = p; pendingLong = null; markSel(); }
  function markSel() { document.querySelectorAll('.card').forEach((c) => c.setAttribute('aria-selected', String(c.dataset.p === sel))); }
  async function toggleFav(p) { const s = new Set(cfg.favorites); s.has(p) ? s.delete(p) : s.add(p); await saveCfg({ favorites: [...s] }); document.querySelectorAll('.card').forEach((c) => c.querySelector('.fav')?.setAttribute('aria-pressed', String(s.has(c.dataset.p)))); if (tab === 'fav') render(); }

  // ---------- tabs ----------
  const TABS = [['folders', 'tabFolders'], ['fav', 'tabFav'], ['recent', 'tabRecent'], ['auto', 'tabAuto']];
  function renderTabs() { const n = $('tabs'); n.textContent = ''; for (const [id, k] of TABS) n.append(el('button', { role: 'tab', 'aria-selected': String(tab === id), onclick: () => setTab(id) }, t(k))); }
  function setTab(id) { clearMsg(); tab = id; if (id !== 'auto') route = route; render(); }

  // ---------- status / destination ----------
  async function refresh() {
    try { status = await api('/status'); } catch { status = { ok: false, code: 'ERR_NO_RESOLVE' }; }
    const c = $('d-conn');
    if (!status.ok) { c.textContent = t('disconnected'); c.className = 'chip off'; $('d-tl').textContent = ''; $('d-pos').textContent = ''; $('btn-place').disabled = true; $('btn-trim').disabled = true; return; }
    c.textContent = t('connected'); c.className = 'chip on'; $('btn-place').disabled = false; $('btn-trim').disabled = false;
    $('d-tl').textContent = `${status.project} · ${status.timeline}`;
    $('d-pos').textContent = rm ? tcOf(rm.list[rm.i].frame) : status.playhead_tc;
    const s = $('track'), keep = s.value; s.textContent = '';
    for (const tr of status.tracks) s.append(el('option', { value: tr.index }, `A${tr.index}${tr.name && tr.name !== `Audio ${tr.index}` ? ' · ' + tr.name : ''}${tr.locked ? ' · ' + t('locked') : ''}`));
    if (keep && [...s.options].some((o) => o.value === keep)) s.value = keep;
  }
  const trackLabel = (n) => `A${n}`;

  // ---------- placing ----------
  async function place(f, opts = {}) {
    f = f || byPath.get(sel); if (!f) return setMsg('warn', () => t('selectFirst'));
    if (!status?.ok) return setMsg('err', () => t('failed', { reason: t(status?.code || 'ERR_NO_RESOLVE') }));
    const dur = opts.in_sec != null ? opts.out_sec - opts.in_sec : durOf(f) ?? (await analyze(f)).duration;
    if (dur && dur > cfg.warn && pendingLong !== f.path && opts.in_sec == null) { pendingLong = f.path; return setMsg('warn', () => t('confirmLong', { name: f.name, secs: dur.toFixed(1) })); }
    pendingLong = null;
    const req = { path: f.path, project: status.project, timeline_id: status.timeline_id, track: Number($('track').value), record_frame: rm ? status.start + rm.list[rm.i].frame : 'playhead', ...opts };
    const r = await api('/place', req);
    if (r.ok) {
      setMsg('ok', () => t('placed', { name: f.name.replace(/\.[^.]+$/, ''), track: trackLabel(r.track), tc: tcOf(r.start), secs: (r.frames / status.fps).toFixed(1) }));
      saveCfg({ recent: [f.path, ...cfg.recent.filter((p) => p !== f.path)].slice(0, 60) });
      if (rm) await rmAdvance(1);
    } else { r.code === 'ERR_RESOLVE_REFUSED' ? setMsg('err', () => t('placeRefused'), r.code) : setMsg('err', () => t('failed', { reason: errText(r) }), r.code); if (r.code === 'ERR_IDENTITY_MISMATCH') rm = null; }
    await refresh();
  }

  // ---------- trim dialog ----------
  let trimState = null;
  async function openTrim() {
    const f = byPath.get(sel); if (!f) return setMsg('warn', () => t('selectFirst'));
    const m = await analyze(f); if (!m.peaks) return setMsg('err', () => t('ERR_DECODE'));
    trimState = { f, dur: m.duration, a: 0, b: 1, peaks: m.peaks }; $('trimdlg').showModal(); requestAnimationFrame(drawTrim);
  }
  function drawTrim() { const s = trimState; if (!s) return; const c = $('trimc'); drawWave(c, s.peaks, undefined, [s.a, s.b]); $('trim-r').textContent = t('trimRange', { a: (s.a * s.dur).toFixed(2), b: (s.b * s.dur).toFixed(2) }); }
  function trimPointer(e) { const s = trimState, r = $('trimc').getBoundingClientRect(), p = clamp((e.clientX - r.left) / r.width, 0, 1);
    if (e.type === 'pointerdown') { s.drag = Math.abs(p - s.a) < Math.abs(p - s.b) ? 'a' : 'b'; $('trimc').setPointerCapture(e.pointerId); }
    if (!s.drag) return; s[s.drag] = p; if (s.a > s.b) { [s.a, s.b] = [s.b, s.a]; s.drag = s.drag === 'a' ? 'b' : 'a'; } if (e.type === 'pointerup') s.drag = null; drawTrim(); }

  // ---------- Auto SFX ----------
  function renderRm() {
    document.querySelectorAll('.banner.rmb').forEach((b) => b.remove()); if (!rm) return;
    const m = rm.list[rm.i];
    const b = el('div', { class: 'banner rmb' }, el('b', {}, t('mapTarget', { name: m.name || t('marker'), i: rm.i + 1, n: rm.list.length })), el('span', { class: 'hint' }, tcOf(m.frame)), el('span', { class: 'grow' }),
      el('button', { onclick: () => rmAdvance(-1) }, t('mapPrev')), el('button', { onclick: () => rmAdvance(1) }, t('mapSkip')), el('button', { onclick: () => { rm = null; render(); } }, t('mapExit')));
    $('content').prepend(b);
  }
  async function rmAdvance(d) {
    const i = rm.i + d; if (i >= rm.list.length) { const total = rm.list.length; setMsg('ok', () => t('mapDone', { n: total })); rm = null; render(); return; } rm.i = clamp(i, 0, rm.list.length - 1);
    await api('/playhead', { project: status.project, timeline_id: status.timeline_id, frame: rm.list[rm.i].frame }); renderRm(); refresh();
  }
  const ident = () => ({ project: status.project, timeline_id: status.timeline_id });
  const need = () => { if (!status?.ok) { setMsg('err', () => t('failed', { reason: t(status?.code || 'ERR_NO_RESOLVE') })); return false; } return true; };
  function back() { return el('button', { class: 'icon', title: t('back'), onclick: () => { route = null; render(); } }, icon('back')); }
  function renderAuto() {
    const a = $('auto'); a.textContent = '';
    if (!route) {
      a.append(el('div', { class: 'ws-head' }, el('h2', {}, t('autoTitle'))),
        el('div', { class: 'routes' }, ...[['random', 'dice', 'rRandom', 'rRandomD'], ['replace', 'swap', 'rReplace', 'rReplaceD'], ['markers', 'flag', 'rMarkers', 'rMarkersD'], ['map', 'steps', 'rMap', 'rMapD']]
          .map(([id, ic, k, d]) => el('button', { class: 'route', onclick: () => { route = id; renderAuto(); } }, icon(ic), el('b', {}, t(k)), el('span', {}, t(d))))));
      return;
    }
    ({ random: wsRandom, replace: wsReplace, markers: wsMarkers, map: wsMap })[route](a);
  }
  // Random Fill
  let fillSrc = 'lib', fillMax = 5, fillPlan = null, fillSeed = 1;
  function wsRandom(a) {
    const out = el('div'); const sel1 = el('select', { onchange: (e) => { fillSrc = e.target.value; } }, el('option', { value: 'lib', selected: fillSrc === 'lib' }, t('fillLib')), el('option', { value: 'fav', selected: fillSrc === 'fav' }, t('fillFav')));
    const mx = el('input', { type: 'number', min: 1, max: 30, value: fillMax, style: 'width:70px', onchange: (e) => { fillMax = clamp(Number(e.target.value) || 5, 1, 30); } });
    const planBtn = el('button', { onclick: () => doPlan(false) }, t('fillPlan')), reBtn = el('button', { onclick: () => doPlan(true) }, t('fillReshuffle'));
    a.append(el('div', { class: 'ws-head' }, back(), el('h2', {}, t('rRandom'))), el('p', { class: 'hint' }, t('fillNeed')),
      el('div', { class: 'ws-tools' }, el('label', {}, t('fillSource') + ' ', sel1), el('label', {}, t('fillMax') + ' ', mx), planBtn, reBtn), out);
    async function doPlan(reshuffle) {
      if (!need()) return; if (reshuffle) fillSeed = Math.floor(Math.random() * 1e9); out.textContent = '';
      const mk = await api('/markers'); if (!mk.markers?.length) return void out.append(el('p', { class: 'hint' }, t('fillNoMarkers')));
      let src = fillSrc === 'fav' ? files.filter((f) => isFav(f.path)) : filtered_lib(); await Promise.all(src.filter((f) => f.duration == null && !meta.has(f.path)).slice(0, 300).map(analyze));
      const pool = src.map((f) => ({ path: f.path, duration: durOf(f) })).filter((f) => f.duration && f.duration <= fillMax);
      if (!pool.length) return void out.append(el('p', { class: 'hint' }, t('fillNoSounds')));
      let s = fillSeed; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
      const items = mk.markers.map((m) => ({ path: pool[Math.floor(rnd() * pool.length)].path, track: Number($('track').value), record_frame: status.start + m.frame, _m: m }));
      const r = await api('/place_batch', { ...ident(), dry_run: true, items: items.map(({ _m, ...x }) => x) }); fillPlan = { items, r };
      const rows = items.map((it, i) => { const p = r.plans[i]; return el('tr', { class: p.ok ? '' : 'bad' }, el('td', {}, tcOf(it._m.frame)), el('td', {}, it._m.name || t('marker')), el('td', {}, byPath.get(it.path).name), el('td', {}, p.ok ? el('span', { class: 'ok' }, 'OK') : errText(p))); });
      const apply = el('button', { class: 'primary', disabled: !r.ok, onclick: async () => { const x = await api('/place_batch', { ...ident(), items: items.map(({ _m, ...y }) => y) }); x.ok ? setMsg('ok', () => t('fillDone', { n: x.executed, track: trackLabel(items[0].track) })) : setMsg('err', () => t('failed', { reason: errText(x.plans?.find((p) => !p.ok) || x.results?.find((p) => !p.ok) || x) })); apply.disabled = true; refresh(); } }, t('fillApply', { n: items.length }));
      out.append(el('table', { class: 'tbl' }, el('thead', {}, el('tr', {}, el('th', {}, 'TC'), el('th', {}, t('marker')), el('th', {}, ''), el('th', {}, ''))), el('tbody', {}, rows)), el('div', { class: 'ws-tools', style: 'margin-top:10px' }, apply));
    }
  }
  const filtered_lib = () => { if (node === 'all') return files; const [r, d] = node.split('|'); return files.filter((f) => f.root === r && (!d || f.dir === d || f.dir.startsWith(d + '/'))); };
  // Replace
  let repMode = 'selected', repKeep = false;
  function wsReplace(a) {
    const out = el('div'); const f = byPath.get(sel);
    const modes = el('select', { onchange: (e) => { repMode = e.target.value; } }, el('option', { value: 'selected', selected: repMode === 'selected' }, t('repSelected')), el('option', { value: 'playhead', selected: repMode === 'playhead' }, t('repCursor')));
    a.append(el('div', { class: 'ws-head' }, back(), el('h2', {}, t('rReplace'))), el('p', { class: 'hint' }, f ? f.name : t('repPick')),
      el('div', { class: 'ws-tools' }, el('label', {}, t('repTarget') + ' ', modes), el('label', {}, el('input', { type: 'checkbox', checked: repKeep, onchange: (e) => { repKeep = e.target.checked; } }), ' ' + t('repKeep')), el('button', { onclick: () => run(true) }, t('repPlan'))), out);
    async function run(dry) {
      const f2 = byPath.get(sel); if (!f2) return setMsg('warn', () => t('selectFirst')); if (!need()) return;
      const r = await api('/replace', { ...ident(), path: f2.path, mode: repMode, keep_length: repKeep, dry_run: dry });
      if (!dry) { setMsg(r.ok ? 'ok' : 'err', () => (r.ok ? t('repDone', { n: r.executed }) : t('failed', { reason: errText(r) }))); refresh(); }
      out.textContent = ''; if (!r.results?.length) return void out.append(el('p', { class: 'hint' }, r.code ? errText(r).replace(/^./, (c) => c.toUpperCase()) : t('repNoTarget')));
      out.append(el('table', { class: 'tbl' }, el('thead', {}, el('tr', {}, el('th', {}, t('repOld')), el('th', {}, t('track')), el('th', {}, 'TC'), el('th', {}, ''))),
        el('tbody', {}, r.results.map((x) => el('tr', { class: x.ok || x.done ? '' : 'bad' }, el('td', {}, x.old), el('td', {}, trackLabel(x.track)), el('td', {}, tcOf(x.start)), el('td', {}, x.ok ? el('span', { class: 'ok' }, x.done ? 'OK' : `${(x.frames / status.fps).toFixed(1)} s`) : errText(x)))))));
      if (dry && r.ok) out.append(el('div', { class: 'ws-tools', style: 'margin-top:10px' }, el('button', { class: 'primary', onclick: () => run(false) }, t('repApply'))));
    }
  }
  // Manage markers
  function wsMarkers(a) {
    const out = el('div'); a.append(el('div', { class: 'ws-head' }, back(), el('h2', {}, t('rMarkers')), el('span', { class: 'grow' }), el('button', { class: 'icon', title: t('refresh'), onclick: load }, icon('refresh'))), out);
    async function op(o) { const r = await api('/markers/op', { ...ident(), ...o }); if (!r.ok) setMsg('err', () => t('failed', { reason: errText(r) })); return r; }
    async function load() {
      if (!need()) return; const r = await api('/markers'); out.textContent = ''; if (!r.markers?.length) return void out.append(el('p', { class: 'hint' }, t('mkEmpty')));
      out.append(el('table', { class: 'tbl' }, el('thead', {}, el('tr', {}, el('th', {}, 'TC'), el('th', {}, t('mkRename')), el('th', {}, t('mkTags')), el('th', {}, ''))), el('tbody', {}, r.markers.map((m) => {
        const tagBox = el('td', {}); const draw = () => { tagBox.textContent = ''; m.tags.forEach((g) => tagBox.append(el('span', { class: 'tag' }, g, el('button', { title: t('mkDelete'), onclick: async () => { m.tags = m.tags.filter((x) => x !== g); if ((await op({ op: 'tags', frame: m.frame, tags: m.tags })).ok) draw(); } }, icon('x'))))); tagBox.append(el('input', { type: 'text', placeholder: t('mkAddTag'), style: 'width:110px', onkeydown: async (e) => { if (e.key === 'Enter' && e.target.value.trim()) { m.tags = [...m.tags, e.target.value.trim()]; if ((await op({ op: 'tags', frame: m.frame, tags: m.tags })).ok) draw(); } } })); }; draw();
        return el('tr', {}, el('td', {}, tcOf(m.frame)), el('td', {}, el('input', { type: 'text', value: m.name, 'aria-label': t('mkRename'), onchange: async (e) => { const r2 = await op({ op: 'rename', frame: m.frame, name: e.target.value }); if (r2.ok) setMsg('ok', () => t('mkDone')); } })), tagBox,
          el('td', {}, el('button', { class: 'icon sm', title: t('mkDelete'), onclick: async () => { if ((await op({ op: 'delete', frame: m.frame })).ok) load(); } }, icon('trash')))); }))),
        el('div', { class: 'ws-tools', style: 'margin-top:10px', id: 'trash-box' }, el('button', { onclick: (e) => { const box = $('trash-box'); box.textContent = ''; box.append(el('span', {}, t('mkTrashConfirm', { n: r.markers.length })), el('button', { class: 'primary', onclick: async () => { if ((await op({ op: 'trash_all', confirm: true })).ok) load(); } }, t('mkYes')), el('button', { onclick: load }, t('cancel'))); } }, icon('trash'), t('mkTrash'))));
    } load();
  }
  // Rapid Mapping
  function wsMap(a) {
    a.append(el('div', { class: 'ws-head' }, back(), el('h2', {}, t('rMap'))), el('p', { class: 'hint' }, t('mapHint')),
      el('div', { class: 'ws-tools' }, el('button', { class: 'primary', onclick: async () => { if (!need()) return; const r = await api('/markers'); if (!r.markers?.length) return setMsg('warn', () => t('mapNone')); rm = { list: r.markers, i: 0 }; await api('/playhead', { ...ident(), frame: rm.list[0].frame }); tab = 'folders'; render(); refresh(); } }, icon('steps'), t('mapStart'))));
  }

  // ---------- i18n / settings ----------
  function applyI18n() {
    document.documentElement.lang = L; document.querySelectorAll('[data-i]').forEach((e) => (e.textContent = t(e.dataset.i)));
    $('q').placeholder = t('search'); $('q').setAttribute('aria-label', t('search')); $('btn-add').title = t('addFolder'); $('btn-refresh').title = t('refresh'); $('btn-settings').title = t('settings'); setPinUi(); $('btn-addtrack').title = t('addTrack');
    $('s-cache').textContent = t('clearCache'); $('btn-log').textContent = logOpen ? t('logClose') : t('logOpen'); $('log-clear').textContent = t('clear');
    $('trim-clear').textContent = t('clearSel'); $('trim-cancel').textContent = t('cancel'); $('trim-ok').textContent = t('trimPlace');
    document.querySelectorAll('#settings label').forEach((l) => { const k = l.dataset.k; if (k) l.firstChild.textContent = t(k) + ' '; });
    $('s-dir').textContent = `${t('settingsFolder')}: ${settingsDir}`; refreshStatic(); render(); refresh();
    $('s-deps').textContent = t('depsOpen'); $('s-credit').textContent = t('credits'); $('s-ver').textContent = t('updVersion', { v: appVersion }); $('s-upd').textContent = t('updCheck'); $('s-log').textContent = t('openLog'); $('s-uninstall').textContent = t('uninstallBtn');
    $('deps-h').textContent = t('depsTitle'); $('deps-re').textContent = t('depsRecheck'); $('deps-close').textContent = t('depsClose'); $('deps-log').textContent = t('openLog');
    $('upd-later').textContent = t('updLater'); $('upd-now').textContent = t('updNow'); $('uni-h').textContent = t('uninstallBtn'); $('uni-p').textContent = t('uninstallAsk'); $('uni-no').textContent = t('cancel'); $('uni-yes').textContent = t('uninstallYes');
    if (updInfo) $('upd-t').textContent = t('updNewer', { v: updInfo.app_version || updInfo.version });
    renderMsg(); renderLog(); if ($('depsdlg').open) runDeps();
  }
  function setPinUi() { const on = cfg.pin !== false; const b = $('btn-pin'); b.setAttribute('aria-pressed', on); b.title = t(on ? 'pinOn' : 'pinOff'); b.setAttribute('aria-label', t('pinOff')); }
  function refreshStatic() { const ls = document.querySelectorAll('#settings > label'); ls[0].firstChild.textContent = t('language') + ' '; ls[2].firstChild.textContent = t('reviewWarn') + ' '; $('vol').title = t('volume'); $('dens').title = t('density'); }
  // ---------- dependencies / update / uninstall ----------
  let appVersion = '', initInfo = {}, updInfo = null;
  const DEPKEY = { python: ['depPython', 'depPythonOk', 'depPythonNo', 'depPythonFix'], module: ['depModule', 'depModuleOk', 'depModuleNo', 'depModuleFix'], resolve: ['depResolve', 'depResolveOk', 'depResolveNo', 'depResolveFix'],
    project: ['depProject', 'depProjectOk', 'depProjectNo', 'depProjectFix'], timeline: ['depTimeline', 'depTimelineOk', 'depTimelineNo', 'depTimelineFix'], tc: ['depTc', 'depTcOk', 'depTcNo', 'depTcFix'], bridge: ['depBridge', null, 'depBridgeNo', 'depBridgeFix'] };
  async function runDeps() {
    let items;
    if (initInfo.error === 'ERR_NO_PYTHON') items = [{ id: 'python', ok: false }];
    else if (initInfo.error === 'ERR_PYTHON_PATH') items = [{ id: 'python', ok: false, path: true, info: initInfo.pyTried || '' }];
    else if (initInfo.error) items = [{ id: 'python', ok: true, info: (initInfo.python && initInfo.python.version) || '' }, { id: 'bridge', ok: false }];
    else { const r = await api('/deps'); items = r.items || [{ id: 'resolve', ok: false }]; }
    const ul = $('deps-list'); ul.textContent = ''; let bad = 0;
    for (const it of items) {
      const k = DEPKEY[it.id]; if (!k) continue; if (!it.ok) bad++;
      const info = it.id === 'python' ? String(it.info || '').split(' · ')[0] : it.info || '';
      const main = it.ok ? t(k[1], { info }) : it.path ? t('depPythonPathNo', { info }) : t(k[2], { info });
      const fix = it.ok ? null : it.path ? t('depPythonPathFix') : t(k[3]);
      ul.append(el('li', { class: it.ok ? '' : 'bad' }, el('span', { class: 'dot', 'aria-hidden': 'true' }), el('div', {}, el('b', {}, t(k[0])), el('span', {}, main), fix && el('div', { class: 'fix' }, fix))));
    }
    $('deps-sum').textContent = bad ? t('depsSome') : t('depsAllOk');
  }
  function openDeps() { if (!$('depsdlg').open) $('depsdlg').showModal(); runDeps(); }
  async function checkUpdates(manual) {
    const r = await window.ssfx.checkUpdate();
    if (r.state === 'newer') { updInfo = r.info; $('upd-t').textContent = t('updNewer', { v: r.info.app_version || r.info.version }); $('upd').hidden = false; if (manual) setMsg('ok', () => t('updNewer', { v: r.info.app_version || r.info.version })); }
    else if (manual) setMsg(r.state === 'current' ? 'ok' : 'err', () => (r.state === 'current' ? t('updCurrent') : t('updFail', { reason: r.reason || '' })));
    return r;
  }
  async function doUpdate() {
    $('upd-now').disabled = true; setMsg('warn', () => t('updWorking'));
    const r = await window.ssfx.installUpdate(updInfo); $('upd-now').disabled = false;
    if (r.ok) { $('upd').hidden = true; setMsg('ok', () => t('updDone')); } else setMsg('err', () => t('updInstallFail', { reason: r.reason || '' }));
  }

  let logOpen = false;
  function densityPx() { return Math.round(120 + (cfg.dens / 100) * 150); }

  async function boot() {
    const init = await window.ssfx.init();
    cfg = { ...defaults, ...(init.cfg || {}) }; L = T[cfg.locale || init.locale] ? (cfg.locale || init.locale) : 'en'; settingsDir = init.settingsDir || '';
    $('s-lang').value = L; $('s-hover').checked = !!cfg.hover; $('s-warn').value = cfg.warn; $('vol').value = cfg.vol; $('dens').value = cfg.dens; document.documentElement.style.setProperty('--card-w', densityPx() + 'px');
    $('s-lang').onchange = (e) => { L = e.target.value; saveCfg({ locale: L }); applyI18n(); };
    $('s-hover').onchange = (e) => saveCfg({ hover: e.target.checked }); $('s-warn').onchange = (e) => saveCfg({ warn: clamp(Number(e.target.value) || 10, 1, 600) });
    $('s-cache').onclick = async () => { await idb('readwrite', (s) => s.clear()); meta.clear(); setMsg('ok', () => t('cacheCleared')); render(); };
    $('btn-pin').onclick = async () => { cfg.pin = !(cfg.pin !== false); await window.ssfx.pin(cfg.pin); setPinUi(); };
    $('btn-settings').onclick = () => { $('settings').hidden = !$('settings').hidden; };
    $('vol').oninput = (e) => { cfg.vol = Number(e.target.value); setVol(); }; $('vol').onchange = () => saveCfg({ vol: cfg.vol });
    $('dens').oninput = (e) => { cfg.dens = Number(e.target.value); document.documentElement.style.setProperty('--card-w', densityPx() + 'px'); }; $('dens').onchange = () => saveCfg({ dens: cfg.dens });
    $('q').oninput = (e) => { q = e.target.value; render(); }; $('narrow-folder').onchange = (e) => { node = e.target.value; render(); };
    $('btn-add').onclick = async () => { const p = await window.ssfx.chooseFolder(); if (!p) return; if (!cfg.roots.includes(p)) await saveCfg({ roots: [...cfg.roots, p] }); await loadLibrary(); };
    $('btn-refresh').onclick = () => loadLibrary();
    $('btn-place').onclick = () => place(); $('btn-trim').onclick = openTrim;
    $('btn-addtrack').onclick = async () => { if (!need()) return; const r = await api('/track/add', ident()); setMsg(r.ok ? 'ok' : 'err', () => (r.ok ? `A${r.tracks}` : t('failed', { reason: errText(r) }))); await refresh(); $('track').value = String(r.tracks || $('track').value); };
    $('btn-log').onclick = () => { logOpen = !logOpen; $('log').hidden = !logOpen; $('btn-log').textContent = logOpen ? t('logClose') : t('logOpen'); }; $('log-clear').onclick = () => { logLines = []; renderLog(); };
    const tc = $('trimc'); ['pointerdown', 'pointermove', 'pointerup'].forEach((ev) => tc.addEventListener(ev, trimPointer));
    $('trim-clear').onclick = () => { trimState.a = 0; trimState.b = 1; drawTrim(); }; $('trim-cancel').onclick = () => { $('trimdlg').close(); trimState = null; };
    $('trim-ok').onclick = () => { const s = trimState; $('trimdlg').close(); trimState = null; place(s.f, { in_sec: +(s.a * s.dur).toFixed(3), out_sec: +(s.b * s.dur).toFixed(3) }); };
    $('grid').onkeydown = (e) => {
      const cols = getComputedStyle($('grid')).gridTemplateColumns.split(' ').length, i = view.findIndex((f) => f.path === sel), mv = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: cols, ArrowUp: -cols }[e.key];
      if (mv) { e.preventDefault(); const n = clamp((i < 0 ? 0 : i + mv), 0, view.length - 1); choose(view[n].path); $('grid').children[n]?.scrollIntoView({ block: 'nearest' }); }
      else if (e.key === 'Enter' && sel) { e.preventDefault(); place(byPath.get(sel)); } else if (e.key === ' ' && sel) { e.preventDefault(); play(byPath.get(sel), $('grid').querySelector(`[data-p="${CSS.escape(sel)}"]`)); }
      else if ((e.key === 'f' || e.key === 'F') && sel) toggleFav(sel); else if ((e.key === 't' || e.key === 'T') && sel) openTrim();
    };
    document.addEventListener('pointerdown', () => { if (ctx && ctx.state === 'suspended') ctx.resume(); }, { once: true });
    appVersion = init.version || ''; initInfo = init;
    $('d-conn').onclick = openDeps; $('s-deps').onclick = () => { $('settings').hidden = true; openDeps(); }; $('deps-re').onclick = runDeps; $('deps-close').onclick = () => $('depsdlg').close(); $('deps-log').onclick = () => window.ssfx.openLog(); $('s-log').onclick = () => window.ssfx.openLog();
    $('s-upd').onclick = () => checkUpdates(true); $('upd-later').onclick = () => { $('upd').hidden = true; }; $('upd-now').onclick = doUpdate;
    $('s-uninstall').onclick = () => { $('settings').hidden = true; $('unidlg').showModal(); }; $('uni-no').onclick = () => $('unidlg').close();
    $('uni-yes').onclick = async () => { $('unidlg').close(); const r = await window.ssfx.uninstall(); setMsg(r.ok ? 'ok' : 'warn', () => t(r.ok ? 'uninstallDone' : 'uninstallPartial')); };
    if (init.error) { applyI18n(); openDeps(); return; }
    B = init; applyI18n(); await loadLibrary(); await refresh(); setInterval(refresh, 2000); checkUpdates(false);
  }
  boot();
})();
