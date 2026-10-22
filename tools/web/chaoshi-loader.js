/* =========================================================================
 * 《超时》网页版开屏与装载层  chaoshi-loader.js
 * -------------------------------------------------------------------------
 * 这是站点唯一的「开屏/进度/报错」UI 真源，由 tools/patch_web.py 复制进
 * build/web/ 并在 index.html 里以 <script> 引入（早于 renpy-pre.js）。
 *
 * 为什么要有它：
 *   1. Ren'Py 自带的 #statusDiv 只吐英文（Downloading engine... /
 *      Could not download game data），且报错后 addRunDependency("error")
 *      会把游戏永久挂住，只留一行英文没人看得懂。
 *   2. 原生进度条在 dataSize 未知时直接 return，弱网下前几秒是一片空白。
 *   3. 启动图曾经把中文烧进 jpg，而字体是子集化的 → 「首/若/此」变方框。
 *      现在文字全部在这一层用系统字体渲染，图上一个字都没有。
 *
 * 设计约定：
 *   - 不接管 Module.print / printErr：原生仍在写隐藏的 #statusTextDiv，
 *     那是出错时「技术细节」唯一可信的数据源。
 *   - 只接管 Module.setStatus（拿引擎进度）与 addRunDependency=="error"
 *     （把挂死变成可点的错误页）。
 *   - 复用页面里已有的 #presplash <img> 当底图，不额外发一次图片请求。
 *   - 整层 pointer-events:none，按钮单独 auto；淡出后 remove()，不留隐形容器。
 *   - prefers-reduced-motion / 1 小时内二次访问 / ?nointro=1 都会压缩片头。
 * ========================================================================= */

(function () {
  'use strict';

  /* ---------------------------------------------------------------- 常量 */

  var VERSION = '2';

  // 片头总时长（片名 + 台词）。加载更慢时会停在最后一帧等下载。
  var INTRO_MS = 2900;
  var INTRO_QUICK_MS = 1200;

  // 时间轴节点（毫秒）
  var T_TITLE = 380;
  var T_LINE = 1750;
  var T_SUB = 2450;
  var T_BG = 900;

  var FADE_OUT_MS = 560;

  // 引擎装载占总进度的 85%，剧本 15%（引擎 36 MB vs 剧本 6.7 MB，
  // 但剧本值得单独一段，让「快好了」有明确反馈）
  var W_ENGINE = 0.85;

  // 6.7 MB / 34 KB/s ≈ 200 s；给足预算，超时由空闲检测负责，不是墙钟
  var SEEN_KEY = 'chaoshi_seen_at';
  var SEEN_TTL = 3600 * 1000;

  /* ---------------------------------------------------------------- 环境 */

  var qs = new URLSearchParams(location.search);
  var NOINTRO = qs.has('nointro');
  var NOPREFETCH = qs.has('noprefetch');
  var REDUCED = false;
  try {
    REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) { /* 老浏览器 */ }

  var lastSeen = 0;
  try { lastSeen = parseInt(localStorage.getItem(SEEN_KEY), 10) || 0; } catch (e) { /* 隐身模式 */ }
  var REPEAT_VISIT = (Date.now() - lastSeen) < SEEN_TTL;

  var INTRO_LEN = (REDUCED || REPEAT_VISIT) ? INTRO_QUICK_MS : INTRO_MS;
  if (NOINTRO) INTRO_LEN = 0;

  var MIRRORS = window.CHAOSHI_MIRRORS || {
    gh: 'https://gongfpp.github.io/chaoshi-2018/',
    cf: 'https://chaoshi-2018.pages.dev/'
  };

  /* ---------------------------------------------------------------- 状态 */

  var S = {
    t0: performance.now(),
    timedOut: false,

    engineDone: 0,
    engineTotal: 0,
    zipDone: 0,
    zipTotal: (window.gameZipTotal || 0),

    // 分项字节账本（见 bytes()）：wasm 由 fetch 观测，data 由 setStatus 上报
    wasm: { done: 0, total: 0 },
    data: { done: 0, total: 0 },
    sz: window.CHAOSHI_SIZES || {},

    phase: 'boot',        // boot | engine | zip | ready | error
    errorKind: null,
    errorDetail: '',

    samples: [],          // [[ms, bytes], ...] 用于算瞬时速率
    lastSpeed: 0,
    lastActivity: performance.now(),   // 最后一次进度变化，用于判「真的卡死」
    slowHintShown: false,

    readyAt: 0,
    dead: false,
    domReady: false
  };

  var el = {};            // DOM 引用
  var logs = [];          // 供「技术细节」用

  /* ---------------------------------------------------------------- 工具 */

  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }

  function mb(bytes) {
    if (!isFinite(bytes) || bytes <= 0) { return '—'; }
    return (bytes / 1048576).toFixed(1);
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function now() { return performance.now(); }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function track(event, fields) {
    try {
      if (typeof window.chaoshiTrack === 'function') {
        var o = { event: event };
        if (fields) { for (var k in fields) { if (fields.hasOwnProperty(k)) o[k] = fields[k]; } }
        window.chaoshiTrack(JSON.stringify(o));
      }
    } catch (e) { /* 埋点不能影响加载 */ }
  }

  function logLine(s) {
    logs.push(String(s).slice(0, 300));
    if (logs.length > 40) logs.shift();
  }

  /* ---------------------------------------------------------------- 样式 */

  var CSS = [
    // 根层必须透明：底图是页面里已有的 #presplash <img>，在 root 下面
    '#chaoshiBoot{position:fixed;inset:0;z-index:60;pointer-events:none;',
    '  background:transparent;overflow:hidden;',
    '  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",',
    '    "Microsoft YaHei","Noto Sans SC","Source Han Sans SC",sans-serif;',
    '  color:#E8E4DC;-webkit-font-smoothing:antialiased;',
    '  transition:opacity ' + FADE_OUT_MS + 'ms linear;}',
    '#chaoshiBoot.cb-gone{opacity:0}',

    // 底图：复用页面里的 #presplash，不改它自身的布局，只接管透明度
    // 起手一块纯黑，T_BG 时化开露出底图
    '#chaoshiBoot .cb-veil{position:absolute;inset:0;background:#07090C;',
    '  opacity:1;transition:opacity 1200ms ease;}',
    '#chaoshiBoot.cb-bg .cb-veil{opacity:0}',
    // 底图放在我们自己的层里（而不是依赖 Ren'Py 的 #presplash —— 它会在
    // presplashEnd 时被 remove，快机器上片头还没放完菜单就透出来了）。
    // 关键：图片本身不做透明度动画。它在 .cb-veil（纯黑）下面瞬时出现，
    // 由 veil 的淡出完成「化开」——否则两层同时变透明时，中间的 canvas
    // 会透出来，出现「标题和主菜单叠在一起」的重影。
    '#chaoshiBoot .cb-art{position:absolute;inset:0;width:100%;height:100%;',
    '  object-fit:cover;object-position:center 46%;opacity:0;',
    '  filter:brightness(.86) saturate(.94) contrast(1.02);}',
    '#chaoshiBoot.cb-bg .cb-art{opacity:1}',
    // 文字可读性用的压暗层，一直留着
    '#chaoshiBoot .cb-scrim{position:absolute;inset:0;',
    '  background:radial-gradient(120% 90% at 50% 42%,rgba(7,9,12,.18) 0%,rgba(7,9,12,.70) 66%,#07090C 100%);}',
    '#chaoshiBoot .cb-vig{position:absolute;inset:0;',
    '  background:linear-gradient(180deg,rgba(7,9,12,.92) 0%,rgba(7,9,12,0) 34%,',
    '    rgba(7,9,12,0) 58%,rgba(7,9,12,.94) 100%);}',

    '#chaoshiBoot .cb-stage{position:absolute;inset:0;display:flex;flex-direction:column;',
    '  align-items:center;justify-content:center;padding:0 24px;}',

    // 片名：宋体系，重字距，靠 letter-spacing 收拢做「落定」感
    '#chaoshiBoot .cb-title{font-family:"Songti SC","STSong","Noto Serif SC",',
    '  "Source Han Serif SC","SimSun",serif;',
    '  font-size:clamp(48px,8.4vw,124px);letter-spacing:.30em;text-indent:.30em;',
    '  color:#EFEBE3;opacity:0;transform:translateY(10px);',
    '  text-shadow:0 2px 40px rgba(0,0,0,.85);transition:opacity 1100ms ease,',
    '    letter-spacing 1400ms cubic-bezier(.16,.84,.24,1),transform 1100ms ease;}',
    '#chaoshiBoot.cb-t1 .cb-title{opacity:1;letter-spacing:.16em;text-indent:.16em;transform:none;}',

    '#chaoshiBoot .cb-line{margin-top:clamp(18px,3.4vw,40px);',
    '  font-size:clamp(14px,2.05vw,21px);letter-spacing:.16em;color:#C79A4B;',
    '  opacity:0;transform:translateY(6px);',
    '  transition:opacity 900ms ease,transform 900ms ease;}',
    '#chaoshiBoot.cb-t2 .cb-line{opacity:1;transform:none;}',
    '#chaoshiBoot.cb-t3 .cb-line{opacity:.42;}',

    '#chaoshiBoot .cb-sub{margin-top:14px;font-size:clamp(11px,1.5vw,13px);',
    '  letter-spacing:.30em;text-indent:.30em;color:#8A857C;',
    '  opacity:0;transition:opacity 900ms ease;}',
    // 副题在片名之后出现；一旦底部进度面板亮起就退场，避免和面板挤在一起
    '#chaoshiBoot.cb-t2 .cb-sub{opacity:.55;}',
    '#chaoshiBoot.cb-panel-on .cb-sub{opacity:0;}',

    // 进度面板：贴在下方，不遮脸
    '#chaoshiBoot .cb-panel{position:absolute;left:50%;bottom:clamp(28px,7vh,72px);',
    '  transform:translateX(-50%);width:min(560px,84vw);opacity:0;',
    '  transition:opacity 700ms ease;}',
    '#chaoshiBoot.cb-panel-on .cb-panel{opacity:1;}',

    '#chaoshiBoot .cb-row{display:flex;align-items:baseline;justify-content:space-between;',
    '  gap:16px;margin-bottom:10px;font-size:13px;letter-spacing:.06em;}',
    '#chaoshiBoot .cb-stage-name{color:#A8A39A;}',
    '#chaoshiBoot .cb-num{color:#E8E4DC;font-variant-numeric:tabular-nums;',
    '  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;}',
    '#chaoshiBoot .cb-num em{font-style:normal;color:#C79A4B;}',

    '#chaoshiBoot .cb-bar{position:relative;height:2px;background:rgba(232,228,220,.14);',
    '  overflow:hidden;}',
    '#chaoshiBoot .cb-fill{position:absolute;inset:0 auto 0 0;width:0%;',
    '  background:linear-gradient(90deg,#8A6B34,#C79A4B 60%,#E2B86A);',
    '  box-shadow:0 0 12px rgba(199,154,75,.55);transition:width 320ms ease-out;}',
    '#chaoshiBoot .cb-bar.cb-indet .cb-fill{width:34%;animation:cbSweep 1.5s ease-in-out infinite;}',
    '@keyframes cbSweep{0%{left:-34%}100%{left:100%}}',

    '#chaoshiBoot .cb-hintline{margin-top:12px;font-size:11.5px;letter-spacing:.05em;',
    '  color:#6E6A63;min-height:1.4em;}',
    '#chaoshiBoot .cb-hintline a{color:#C79A4B;text-decoration:none;pointer-events:auto;',
    '  border-bottom:1px solid rgba(199,154,75,.35);cursor:pointer;}',

    // 错误态
    '#chaoshiBoot .cb-err{display:none;position:absolute;left:50%;top:50%;',
    '  transform:translate(-50%,-50%);width:min(620px,88vw);',
    '  background:rgba(12,14,18,.94);border:1px solid rgba(199,154,75,.28);',
    '  border-radius:4px;padding:clamp(22px,3.4vw,34px);pointer-events:auto;',
    '  box-shadow:0 24px 80px rgba(0,0,0,.72);}',
    '#chaoshiBoot.cb-dead .cb-err{display:block;}',
    '#chaoshiBoot.cb-dead .cb-stage,#chaoshiBoot.cb-dead .cb-panel{opacity:.18;}',
    '#chaoshiBoot .cb-err h2{margin:0 0 12px;font-size:19px;font-weight:500;',
    '  letter-spacing:.06em;color:#E8E4DC;}',
    '#chaoshiBoot .cb-err p{margin:0 0 8px;font-size:13.5px;line-height:1.85;color:#A8A39A;}',
    '#chaoshiBoot .cb-err .cb-why{color:#D9A45B;}',
    '#chaoshiBoot .cb-acts{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 4px;}',
    '#chaoshiBoot .cb-btn{pointer-events:auto;cursor:pointer;font:inherit;font-size:13px;',
    '  letter-spacing:.08em;padding:9px 18px;border-radius:2px;text-decoration:none;',
    '  color:#E8E4DC;background:rgba(232,228,220,.06);',
    '  border:1px solid rgba(232,228,220,.22);transition:all .18s ease;',
    '  min-height:40px;display:inline-flex;align-items:center;}',
    '#chaoshiBoot .cb-btn:hover{background:rgba(232,228,220,.12);border-color:rgba(232,228,220,.4);}',
    '#chaoshiBoot .cb-btn.primary{background:rgba(199,154,75,.16);',
    '  border-color:rgba(199,154,75,.55);color:#EFD9AE;}',
    '#chaoshiBoot .cb-btn.primary:hover{background:rgba(199,154,75,.28);}',

    '#chaoshiBoot details{margin-top:16px;font-size:11.5px;color:#6E6A63;}',
    '#chaoshiBoot summary{cursor:pointer;pointer-events:auto;letter-spacing:.06em;',
    '  padding:4px 0;outline:none;}',
    '#chaoshiBoot pre{margin:10px 0 0;max-height:180px;overflow:auto;white-space:pre-wrap;',
    '  word-break:break-all;font-size:11px;line-height:1.7;color:#5D5A54;',
    '  background:rgba(0,0,0,.35);padding:10px;border-radius:2px;}',

    '#chaoshiBoot .cb-corner{position:absolute;right:18px;bottom:14px;font-size:10.5px;',
    '  letter-spacing:.14em;color:#3E3B36;}',

    // 窄屏：片名与台词收一点，面板贴底
    '@media (max-width:520px){',
    '  #chaoshiBoot .cb-title{font-size:clamp(38px,13vw,64px);}',
    '  #chaoshiBoot .cb-line{font-size:13px;}',
    '  #chaoshiBoot .cb-panel{bottom:24px;width:88vw;}',
    '  #chaoshiBoot .cb-row{font-size:12px;}',
    '}',
    '@media (max-height:430px){',
    '  #chaoshiBoot .cb-sub{display:none}',
    '  #chaoshiBoot .cb-panel{bottom:12px}',
    '}',

    // 原生 UI 一律隐藏（#statusDiv 必须留在 DOM 里，renpy-pre.js 顶层会 getElementById）
    '#statusDiv{display:none!important}',
    '#inputDiv{z-index:61}',
    '#presplash{transition:opacity 1200ms ease;opacity:0}'
  ].join('\n');

  /* ---------------------------------------------------------------- DOM */

  function build() {
    if (S.domReady) return;
    S.domReady = true;

    var st = document.createElement('style');
    st.id = 'chaoshi-boot-style';
    st.textContent = CSS;
    (document.head || document.documentElement).appendChild(st);

    var root = document.createElement('div');
    root.id = 'chaoshiBoot';
    root.innerHTML = [
      '<img class="cb-art" src="web-presplash.jpg" alt="">',
      '<div class="cb-veil"></div>',
      '<div class="cb-scrim"></div>',
      '<div class="cb-vig"></div>',
      '<div class="cb-stage">',
      '  <div class="cb-title">超时</div>',
      '  <div class="cb-line">再跑一单，就回去。</div>',
      '  <div class="cb-sub">一个骑手的五年 · 2018—2023</div>',
      '</div>',
      '<div class="cb-panel">',
      '  <div class="cb-row">',
      '    <span class="cb-stage-name">正在连接</span>',
      '    <span class="cb-num"><em>0</em>%</span>',
      '  </div>',
      '  <div class="cb-bar cb-indet"><div class="cb-fill"></div></div>',
      '  <div class="cb-hintline"></div>',
      '</div>',
      '<div class="cb-err">',
      '  <h2>装载没有完成</h2>',
      '  <p class="cb-why"></p>',
      '  <p>已经下载的部分不会重来。点「重新加载」通常几秒就能进；如果反复失败，换一条线路试试。</p>',
      '  <div class="cb-acts">',
      '    <button class="cb-btn primary" data-act="reload">重新加载</button>',
      '    <a class="cb-btn" data-act="gh" href="#">换 GitHub 线路</a>',
      '    <a class="cb-btn" data-act="cf" href="#">换 Cloudflare 线路</a>',
      '  </div>',
      '  <details><summary>技术细节</summary><pre></pre></details>',
      '</div>',
      '<div class="cb-corner">CHAOSHI / BOOT ' + VERSION + '</div>'
    ].join('');
    document.body.appendChild(root);

    el.root = root;
    el.art = root.querySelector('.cb-art');
    el.title = root.querySelector('.cb-title');
    el.stageBox = root.querySelector('.cb-stage');
    el.panel = root.querySelector('.cb-panel');
    el.stageName = root.querySelector('.cb-stage-name');
    el.num = root.querySelector('.cb-num');
    el.bar = root.querySelector('.cb-bar');
    el.fill = root.querySelector('.cb-fill');
    el.hint = root.querySelector('.cb-hintline');
    el.err = root.querySelector('.cb-err');
    el.why = root.querySelector('.cb-why');
    el.details = root.querySelector('.cb-err pre');
    el.presplash = document.getElementById('presplash');

    root.addEventListener('click', function (ev) {
      var t = ev.target;
      while (t && t !== root && !t.getAttribute) { t = t.parentNode; }
      if (!t || !t.getAttribute) return;
      var act = t.getAttribute('data-act');
      if (!act) return;
      ev.preventDefault();
      if (act === 'reload') { hardReload(); return; }
      var url = MIRRORS[act];
      if (!url) return;
      try { localStorage.setItem('chaoshi_prefer_mirror', act); } catch (e) {}
      location.href = url + '?from=' + encodeURIComponent(location.host);
    });

    // 片头时间轴：只在独立计时器里推进，不受下载事件干扰
    if (INTRO_LEN === 0) {
      root.className = 'cb-t3 cb-panel-on cb-bg';
    } else {
      var k = INTRO_LEN / INTRO_MS;   // 快速片头按比例压缩
      setTimeout(function () { addCls('cb-t1'); }, T_TITLE * k);
      setTimeout(function () { addCls('cb-t2'); fadeBg(); }, T_LINE * k);
      setTimeout(function () { addCls('cb-t3'); addCls('cb-panel-on'); }, T_SUB * k);
    }
  }

  function addCls(c) {
    if (!el.root) return;
    if ((' ' + el.root.className + ' ').indexOf(' ' + c + ' ') === -1) {
      el.root.className = (el.root.className + ' ' + c).trim();
    }
  }

  function removeCls(c) {
    if (!el.root) return;
    el.root.className = (' ' + el.root.className + ' ')
      .replace(' ' + c + ' ', ' ').trim();
  }

  function fadeBg() {
    // 等底图真正解码完再化开黑场，否则会有半帧看到 canvas 里的主菜单
    if (!el.art || (el.art.complete && el.art.naturalWidth)) {
      addCls('cb-bg');
      return;
    }
    var done = false;
    function go() {
      if (done) { return; }
      done = true;
      addCls('cb-bg');
    }
    el.art.addEventListener('load', go, { once: true });
    el.art.addEventListener('error', go, { once: true });
    setTimeout(go, 1500);       // 图坏了也别一直黑着
  }

  /* ---------------------------------------------------------------- 进度 */

  // 一条按「字节」记账的总进度，而不是按阶段拍脑袋估权重：
  //   renpy.wasm(21.6 MB) + renpy.data(15.1 MB) + game.zip 分片(8.5 MB)
  // 三者的真实体积由 tools/patch_web.py 在构建时写进 window.CHAOSHI_SIZES。
  //
  // 为什么不能只用 Module.setStatus：它只报 renpy.data 那一份（14.4 MB），
  // 而 wasm 的 21.6 MB 在此之前就下完了，且完全不上报 —— 于是弱网下玩家
  // 会盯着「0%」看 40 秒，正是「一直在 loading」的观感来源。
  function bytes() {
    var sz = S.sz || {};
    var wasmT = S.wasm.total || sz.wasm || 0;
    var dataT = S.data.total || sz.data || 0;
    var zipT = S.zipTotal || sz.zip || 0;

    // wasm 的字节由 fetch / XHR 旁路观测（installNetTap / installXhrTap）。
    // 观测不到就按 0 计：宁可少报，也不要提前把它算成已完成 —— 那会让
    // 进度条在 wasm 还在下的时候直接跳到 50%，比没有进度更让人困惑。
    var wasmD = S.wasm.total ? Math.min(S.wasm.done, S.wasm.total) : S.wasm.done;
    var dataD = dataT ? Math.min(S.data.done, dataT) : S.data.done;
    var zipD = zipT ? Math.min(S.zipDone, zipT) : S.zipDone;

    return [wasmD + dataD + zipD, wasmT + dataT + zipT];
  }

  function sample() {
    var b = bytes()[0];
    var t = now();
    S.samples.push([t, b]);
    while (S.samples.length > 2 && t - S.samples[0][0] > 3000) { S.samples.shift(); }
    if (S.samples.length >= 2) {
      var a = S.samples[0], z = S.samples[S.samples.length - 1];
      var dt = (z[0] - a[0]) / 1000;
      if (dt > 0.25) { S.lastSpeed = (z[1] - a[1]) / dt; }
    }
  }

  function pct() {
    if (S.phase === 'ready') { return 100; }
    var b = bytes();
    if (!b[1]) { return 0; }
    return clamp(b[0] / b[1], 0, 1) * 100;
  }

  var paintQueued = false;
  var paintPending = false;

  function schedulePaint() {
    if (S.dead) return;
    if (paintQueued) { paintPending = true; return; }
    paintQueued = true;
    requestAnimationFrame(function () {
      paintQueued = false;
      paint();
      if (paintPending) { paintPending = false; schedulePaint(); }
    });
  }

  var lastPaint = 0;

  function paint() {
    if (!el.root || S.dead) return;
    var t = now();
    // 250ms 节流：4 条流每个 chunk 都改 DOM 会让进度条抖成一片
    if (t - lastPaint < 250) {
      var wait = 250 - (t - lastPaint);
      setTimeout(function () { schedulePaint(); }, wait);
      return;
    }
    lastPaint = t;

    sample();

    var p = pct();
    var smooth = Math.round(p);

    // 阶段文案
    var b = bytes();
    var engineLeft = (b[0] < b[1]) && (
      (S.wasm.total ? S.wasm.done < S.wasm.total : true) ||
      (S.data.total ? S.data.done < S.data.total : true));
    var zipLeft = S.zipTotal ? S.zipDone < S.zipTotal : true;

    var name, num;
    if (S.phase === 'ready') {
      name = '准备就绪';
      num = '';
    } else if (zipLeft && !engineLeft) {
      name = '正在装载剧本';
      num = mb(S.zipDone) + ' / ' + mb(S.zipTotal) + ' MB';
    } else if (!engineLeft && !zipLeft) {
      name = '正在启动引擎';
      num = '';
    } else {
      name = '正在装载引擎';
      num = mb(b[0]) + ' / ' + mb(b[1]) + ' MB';
    }
    el.stageName.textContent = name;

    var speedTxt = '';
    if (S.lastSpeed > 4096 && S.phase !== 'ready') {
      speedTxt = ' · ' + (S.lastSpeed > 1048576
        ? (S.lastSpeed / 1048576).toFixed(1) + ' MB/s'
        : Math.round(S.lastSpeed / 1024) + ' KB/s');
    }

    el.num.innerHTML = '<em>' + smooth + '</em>%' +
      (num ? '　<span style="opacity:.55">' + esc(num) + '</span>' : '') +
      (speedTxt ? '<span style="opacity:.4">' + esc(speedTxt) + '</span>' : '');

    // 条
    var indet = (b[1] === 0);
    if (indet) {
      if (el.bar.className.indexOf('cb-indet') === -1) {
        el.bar.className = 'cb-bar cb-indet';
      }
    } else {
      if (el.bar.className.indexOf('cb-indet') !== -1) {
        el.bar.className = 'cb-bar';
      }
      el.fill.style.width = p.toFixed(1) + '%';
    }

    // 弱网提示：12 秒后仍低于 60 KB/s 且没走完一半，给一条换线路的路
    if (S.phase === 'engine' && p < 50 && t - S.t0 > 12000 &&
        S.lastSpeed > 0 && S.lastSpeed < 61440 && !S.slowHintShown) {
      S.slowHintShown = true;
      showSlowHint();
    }
    if (!S.slowHintShown && S.phase === 'engine' && t - S.t0 > 12000 && !S.lastSpeed) {
      S.slowHintShown = true;
      showSlowHint();
    }
  }

  function showSlowHint() {
    if (!el.hint) return;
    var alt = (location.host.indexOf('github.io') !== -1) ? 'cf' : 'gh';
    var label = alt === 'gh' ? 'GitHub 线路' : 'Cloudflare 线路';
    el.hint.innerHTML = '这条线路有点慢。<a data-act="' + alt + '">换' + label + '</a>';
  }

  /* ---------------------------------------------------------------- 公共 API */

  var api = {
    version: VERSION,

    /** emscripten 的 Module.setStatus("Downloading data... (123/456)") */
    engineProgress: function (done, total) {
      if (S.dead) return;
      if (done !== S.data.done) { S.lastActivity = now(); }
      S.data.done = done;
      if (total > 0) { S.data.total = total; }
      S.engineDone = done;
      S.engineTotal = S.data.total;
      if (S.phase === 'boot' || S.phase === 'engine') { S.phase = 'engine'; }
      schedulePaint();
    },

    /** wasm / data 的流式字节观测（installNetTap 注入的 fetch 包装调用） */
    netProgress: function (kind, done, total) {
      if (S.dead) return;
      var box = (kind === 'wasm') ? S.wasm : S.data;
      box.done = done;
      if (total > 0) { box.total = total; }
      if (S.phase === 'boot') { S.phase = 'engine'; }
      schedulePaint();
    },

    /** 分片下载器上报：Σ st.got 与 game.zip 总长 */
    zipProgress: function (done, total) {
      if (S.dead) return;
      S.zipDone = done;
      if (total) { S.zipTotal = total; }
      schedulePaint();
    },

    /** 引擎显示初始化完成（presplashEnd 或 canvas 尺寸变化） */
    ready: function () {
      if (S.dead || S.phase === 'ready') return;
      S.phase = 'ready';
      S.readyAt = now();
      schedulePaint();
      track('boot_ready', { ms: Math.round(now() - S.t0) });

      var wait = Math.max(0, INTRO_LEN - (now() - S.t0));
      setTimeout(finish, wait + 120);
    },

    /** 致命错误：kind = idle | http | incomplete | abort | engine | unknown */
    fatal: function (kind, detail) {
      if (S.dead) return;
      if (S.phase === 'ready') return;      // 已经进游戏了，别盖住画面
      S.dead = true;
      S.errorKind = kind || 'unknown';
      S.errorDetail = detail || '';

      build();
      var copy = {
        idle: '网络在传输中途停住了，服务器一直没有再发数据。',
        http: '服务器返回了错误状态，这条线路这会儿可能不通。',
        incomplete: '下载下来的剧本数据不完整，通常是中途断流导致的。',
        abort: '装载被中断了（可能是切换了标签页或断网）。',
        engine: '引擎初始化失败，这台设备或浏览器可能不满足运行条件。',
        unknown: '装载过程中出现了意外错误。'
      }[S.errorKind] || '装载过程中出现了意外错误。';

      el.why.textContent = copy;
      removeCls('cb-panel-on');
      addCls('cb-dead');

      var tech = [];
      if (S.errorDetail) { tech.push(String(S.errorDetail)); }
      tech.push('kind=' + S.errorKind + '  version=' + VERSION + '  ua=' + navigator.userAgent);
      tech.push('engine=' + S.engineDone + '/' + S.engineTotal +
        '  zip=' + S.zipDone + '/' + S.zipTotal);
      var native = document.getElementById('statusTextDiv');
      if (native && native.innerText) {
        tech.push('--- native ---');
        tech.push(native.innerText.split('\n').slice(-16).join('\n'));
      }
      if (logs.length) {
        tech.push('--- loader ---');
        tech.push(logs.slice(-16).join('\n'));
      }
      el.details.textContent = tech.join('\n');

      track('error', { reason: 'loader:' + S.errorKind });
      console.error('[chaoshi] boot failed:', S.errorKind, S.errorDetail || '');
    },

    /** 按需资源下载失败（由 web_fixes.rpy 的 installAssetRetry 调用） */
    assetError: function (path) {
      logLine('asset error: ' + path);
      track('error', { reason: 'asset:' + String(path).slice(0, 80) });
      // 这里不接管 UI：Python 侧会抛中文错误页，玩家能看到是哪个资源
    },

    isDone: function () { return S.phase === 'ready' || S.dead; },

    log: logLine,

    /** 供预取/按需下载互相避让 */
    isPrefetching: function (path) {
      return !!PREFETCH.index[path];
    },

    mirror: function () {
      try { return MIRRORS[localStorage.getItem('chaoshi_prefer_mirror')] || null; }
      catch (e) { return null; }
    },

    _state: S
  };

  window.ChaoshiLoader = api;

  /* ------------------------------------------------------------ 流式观测 */

  /**
   * 给 fetch 套一层，把 renpy.wasm / renpy.data 的下载字节数变成可见进度。
   *
   * 为什么要这么做：emscripten 只在下载 renpy.data 时回调 Module.setStatus，
   * 21.6 MB 的 wasm 在此之前静默下载完 —— 弱网上玩家会对着 0% 干等。
   * 这里用 Response.clone() 旁路读一份（同一份网络流，不重复下载），
   * 原 response 原封不动交给 emscripten。
   */
  function installNetTap() {
    var of = window.fetch;
    if (!of || of.__chaoshiTap) { return; }
    var wrapped = function (input) {
      var url = '';
      try {
        url = (typeof input === 'string') ? input : ((input && input.url) || '');
      } catch (e) { url = ''; }

      var p = of.apply(this, arguments);
      if (!/\.(wasm|data)(\?|#|$)/.test(url)) { return p; }
      var kind = /\.wasm/.test(url) ? 'wasm' : 'data';

      return p.then(function (resp) {
        try {
          var len = parseInt(resp.headers.get('content-length') || '0', 10) || 0;
          if (len) { api.netProgress(kind, 0, len); }
          var clone = resp.clone();
          if (!clone.body || !clone.body.getReader) {
            if (len) { api.netProgress(kind, len, len); }
            return resp;
          }
          var reader = clone.body.getReader();
          var got = 0;
          (function pump() {
            reader.read().then(function (c) {
              if (c.done) {
                api.netProgress(kind, len || got, len || got);
                return;
              }
              got += c.value.length;
              api.netProgress(kind, got, len || got);
              pump();
            }).catch(function () { /* 旁路失败不影响主下载 */ });
          })();
        } catch (e) { /* 老浏览器没有 clone/stream，退回阶段估算 */ }
        return resp;
      });
    };
    wrapped.__chaoshiTap = true;
    try { window.fetch = wrapped; } catch (e) { /* 只读属性，忽略 */ }
  }

  /**
   * XHR 版本的字节观测。emscripten 在部分构建下用 XMLHttpRequest 取
   * renpy.wasm（fetch 旁路就抓不到），所以两条路都要挂。
   */
  function installXhrTap() {
    var X = window.XMLHttpRequest;
    if (!X || !X.prototype || X.prototype.__chaoshiTap) { return; }
    var origOpen = X.prototype.open;
    var origSend = X.prototype.send;

    X.prototype.open = function (method, url) {
      try {
        var u = String(url || '');
        this.__csKind = /\.wasm(\?|#|$)/.test(u) ? 'wasm'
          : (/\.data(\?|#|$)/.test(u) ? 'data' : '');
      } catch (e) { this.__csKind = ''; }
      return origOpen.apply(this, arguments);
    };

    X.prototype.send = function () {
      var self = this;
      if (self.__csKind) {
        try {
          self.addEventListener('progress', function (ev) {
            api.netProgress(self.__csKind, ev.loaded, ev.lengthComputable ? ev.total : ev.loaded);
          });
          self.addEventListener('load', function () {
            var n = (self.response && self.response.byteLength) || 0;
            if (n) { api.netProgress(self.__csKind, n, n); }
          });
        } catch (e) { /* 忽略 */ }
      }
      return origSend.apply(this, arguments);
    };
    X.prototype.__chaoshiTap = true;
  }

  installNetTap();
  installXhrTap();

  /* ---------------------------------------------------------------- 钩子 */

  function hardReload() {
    try { location.reload(); } catch (e) { location.href = location.href; }
  }

  function installHooks() {
    // 1) presplashEnd：Ren'Py 显示初始化前的最后一刻
    var origPse = window.presplashEnd;
    window.presplashEnd = function () {
      try { api.ready(); } catch (e) {}
      if (typeof origPse === 'function') { return origPse.apply(this, arguments); }
    };

    // 2) atExit / onAbort：原生会 remove canvas 并报错，我们同步转成中文错误态
    var origExit = window.atExit;
    window.atExit = function () {
      try { api.fatal('abort'); } catch (e) {}
      if (typeof origExit === 'function') { return origExit.apply(this, arguments); }
    };
    var origAbort = window.Module && window.Module.onAbort;
    if (window.Module) {
      window.Module.onAbort = function () {
        try { api.fatal('abort'); } catch (e) {}
        if (typeof origAbort === 'function') { return origAbort.apply(this, arguments); }
      };
    }

    // 3) Module.setStatus：唯一的引擎进度来源。
    //    这里只「包一层」，不替换 —— 原生还会把 dataDownloaded/dataSize 记进
    //    #statusTextDiv，那是出错时「技术细节」唯一可信的来源。
    if (window.Module && typeof window.Module.setStatus === 'function') {
      var origStatus = window.Module.setStatus;
      window.Module.setStatus = function (s) {
        try { origStatus.call(window.Module, s); } catch (e) { /* 原生实现别影响我们 */ }
        try {
          // 引擎的进度串形如 "Downloading data... (14417920/36997120)"，
          // 也可能带单位 "(14.4/35.3 MB)"。这里只取括号里的 a/b，
          // 注意分组只有 1、2 两个 —— 早先照抄 renpy-pre.js 用 m[4] 取到
          // undefined，parseInt 出来是 NaN，进度条一直是 0%。
          var m = String(s).match(/\(\s*(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)\s*(?:[A-Za-z%]+)?\s*\)/);
          if (m) {
            var a = parseFloat(m[1]);
            var b = parseFloat(m[2]);
            if (isFinite(a) && isFinite(b) && b > 0) {
              api.engineProgress(a, b);
            }
          } else {
            logLine('status: ' + s);
          }
        } catch (e) { /* 解析失败不影响装载 */ }
      };
    }

    // 4) addRunDependency("error") 是原生把游戏钉死的那一根 —— 转成可点错误页
    hookRunDependency();
  }

  function hookRunDependency() {
    var tries = 0;
    (function loop() {
      var M = window.Module;
      if (M && typeof M.addRunDependency === 'function') {
        if (!M.addRunDependency.__csHook) {
          var orig = M.addRunDependency;
          var wrapped = function (id) {
            if (id === 'error') {
              try { api.fatal('engine'); } catch (e) {}
            }
            return orig.apply(M, arguments);
          };
          wrapped.__csHook = true;
          M.addRunDependency = wrapped;
        }
        return;
      }
      if (++tries > 400) { return; }        // 20 秒还没出现就算了
      setTimeout(loop, 50);
    })();
  }

  // renpy-pre.js 是后加载的，等它把 presplashEnd 挂上再接管
  (function waitRenpyPre() {
    var tries = 0;
    (function loop() {
      if (typeof window.presplashEnd === 'function') {
        installHooks();
        return;
      }
      if (++tries > 600) {
        // renpy-pre.js 没起来（资源 404 / 被拦），直接报错，别让玩家对着黑屏
        api.fatal('http', 'renpy-pre.js 未能执行');
        return;
      }
      setTimeout(loop, 50);
    })();
  })();

  /* --------------------------------------------------- canvas 尺寸兜底就绪 */

  (function watchCanvas() {
    var iv = setInterval(function () {
      if (S.dead) { clearInterval(iv); return; }
      var c = document.querySelector('canvas');
      if (c && c.width > 640) {
        clearInterval(iv);
        api.ready();
      } else if (now() - S.t0 > 150000 && !S.dead) {
        clearInterval(iv);
        api.fatal('idle', '150 秒内引擎没有完成初始化');
      }
    }, 400);
  })();

  /* ------------------------------------------------------------ 收尾淡出 */

  function finish() {
    if (!el.root) { return; }
    try { localStorage.setItem(SEEN_KEY, String(Date.now())); } catch (e) {}
    el.root.className = (el.root.className + ' cb-gone').trim();
    if (el.presplash && el.presplash.parentNode) {
      el.presplash.style.opacity = '0';
    }
    setTimeout(function () {
      if (el.root && el.root.parentNode) { el.root.parentNode.removeChild(el.root); }
      var st = document.getElementById('chaoshi-boot-style');
      if (st && st.parentNode) { st.parentNode.removeChild(st); }
      el.root = null;
    }, FADE_OUT_MS + 80);
    startPrefetch();
  }

  /* -------------------------------------------------------------- 预取 */

  var PREFETCH = { index: {}, started: false, done: 0, total: 0, t0: 0, bytes: 0 };

  function netInfo() {
    var c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (!c) { return { type: 'unknown', saveData: false }; }
    return { type: c.effectiveType || 'unknown', saveData: !!c.saveData };
  }

  function startPrefetch() {
    if (NOPREFETCH || PREFETCH.started) { return; }
    PREFETCH.started = true;

    var net = netInfo();
    if (net.saveData || net.type === 'slow-2g' || net.type === '2g') {
      logLine('prefetch skipped: ' + net.type + (net.saveData ? ' (saveData)' : ''));
      return;
    }

    // 进入主菜单后再等 2 秒，别和 Ren'Py 解包脚本抢带宽
    setTimeout(function () { runPrefetch(net); }, 2000);
  }

  function runPrefetch(net) {
    var url = 'chaoshi_prefetch.json' + (window.CHAOSHI_BUILD ? '?b=' + window.CHAOSHI_BUILD : '');
    fetch(url, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) { throw new Error('HTTP ' + r.status); }
      return r.json();
    }).then(function (man) {
      var files = (man.files || []).slice();

      // 门控：只下该下的
      var maxPrio = 5;
      if (net.type === '3g') { maxPrio = 2; }
      if (S.lastSpeed && S.lastSpeed < 153600) { maxPrio = Math.min(maxPrio, 1); }
      files = files.filter(function (f) { return (f.prio || 0) <= maxPrio; });

      // 优先级 → 体积升序
      files.sort(function (a, b) {
        if ((a.prio || 0) !== (b.prio || 0)) { return (a.prio || 0) - (b.prio || 0); }
        return (a.b || 0) - (b.b || 0);
      });

      PREFETCH.total = files.length;
      PREFETCH.index = {};
      for (var i = 0; i < files.length; i++) { PREFETCH.index[files[i].p] = 1; }
      PREFETCH.t0 = now();

      var conc = (net.type === '3g') ? 1 : 2;
      var cursor = 0;
      var stopped = false;
      var budget = 12 * 1048576;     // 最多 12 MB
      var deadline = now() + 8 * 60000;

      function busyWithGame() {
        // Ren'Py 正在按需拉资源时让路
        try {
          if (window.RenPyWeb && RenPyWeb.xhrs) {
            return Object.keys(RenPyWeb.xhrs).length > 0;
          }
        } catch (e) {}
        return false;
      }

      function next() {
        if (stopped || cursor >= files.length) { return Promise.resolve(); }
        var f = files[cursor++];

        if (PREFETCH.bytes > budget || now() > deadline) {
          stopped = true;
          logLine('prefetch stopped (budget/time)');
          return Promise.resolve();
        }
        if (busyWithGame()) {
          return new Promise(function (r) { setTimeout(r, 800); }).then(next);
        }

        var u = 'game/' + f.p + (window.CHAOSHI_BUILD ? '?b=' + window.CHAOSHI_BUILD : '');
        return fetch(u, { cache: 'force-cache' }).then(function (r) {
          // 必须把 body 消费完，否则不进 HTTP 缓存
          return r.arrayBuffer();
        }).then(function (buf) {
          PREFETCH.bytes += buf.byteLength;
          PREFETCH.done++;
        }).catch(function (e) {
          logLine('prefetch miss: ' + f.p + ' ' + (e && e.message));
        }).then(next);
      }

      var workers = [];
      for (var w = 0; w < conc; w++) { workers.push(next()); }
      Promise.all(workers).then(function () {
        track('prefetch', {
          files: PREFETCH.done, total: PREFETCH.total,
          mb: Math.round(PREFETCH.bytes / 1048576),
          ms: Math.round(now() - PREFETCH.t0),
          maxPrio: maxPrio
        });
        logLine('prefetch done ' + PREFETCH.done + '/' + PREFETCH.total +
          ' ' + Math.round(PREFETCH.bytes / 1048576) + 'MB');
      });
    }).catch(function (e) {
      logLine('prefetch manifest failed: ' + (e && e.message));
    });
  }

  /* ------------------------------------------------- 按需下载重试（可选） */

  /**
   * 由 game/game/web_fixes.rpy 在 init 时调用：给 Ren'Py 的按需资源 XHR
   * 加上「20 秒无数据才中断 + 最多 4 次 + 后两次换镜像」。
   * 关键点：重试期间 readyState 保持 0，占位图继续显示，Python 侧不会抛错。
   */
  api.installAssetRetry = function () {
    if (!window.RenPyWeb || RenPyWeb.__csRetry) { return false; }

    var IDLE = 20000;
    var MAXTRY = 4;

    RenPyWeb.dl_new = function (path) {
      var id = RenPyWeb.xhr_id++;
      var st = { readyState: 0, status: 0, statusText: '', _n: 0, _path: path };
      RenPyWeb.xhrs[id] = st;

      function attempt() {
        st._n++;
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        var idle = setTimeout(function () { try { xhr.abort(); } catch (e) {} }, IDLE);
        var arm = function () { clearTimeout(idle); idle = setTimeout(function () { try { xhr.abort(); } catch (e) {} }, IDLE); };

        xhr.onprogress = arm;

        xhr.onload = function () {
          clearTimeout(idle);
          if (xhr.status === 200 || xhr.status === 304 || xhr.status === 206 ||
              (xhr.status === 0 && xhr.response)) {
            try { FS.unlink(path); } catch (e) {}
            FS.writeFile(path, new Uint8Array(xhr.response), { canOwn: true });
            st.readyState = 4; st.status = xhr.status; st.statusText = xhr.statusText || 'OK';
            return;
          }
          retry('http ' + xhr.status);
        };
        xhr.onerror = xhr.ontimeout = xhr.onabort = function () {
          clearTimeout(idle); retry('net');
        };

        var base = '';
        if (st._n >= 3) {
          var m = api.mirror();
          if (m) { base = m; }
        }
        xhr.open('GET', base + path);
        xhr.send();
      }

      function retry(why) {
        if (st._n >= MAXTRY) {
          st.readyState = 4;
          st.status = 0;
          st.statusText = '重试 ' + MAXTRY + ' 次仍失败（' + why + '）';
          api.assetError(path);
          return;
        }
        setTimeout(attempt, 600 * Math.pow(2, st._n - 1));
      }

      attempt();
      return id;
    };

    RenPyWeb.dl_get = function (xhr_id) { return RenPyWeb.xhrs[xhr_id]; };
    RenPyWeb.dl_free = function (xhr_id) { delete RenPyWeb.xhrs[xhr_id]; };
    RenPyWeb.__csRetry = true;
    logLine('asset retry installed');
    return true;
  };

  /* ---------------------------------------------------------------- 启动 */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }

  // 首屏就给一个「正在连接」的确定反馈，而不是黑屏
  schedulePaint();

})();
