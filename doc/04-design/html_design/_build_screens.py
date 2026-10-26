"""Generate self-contained HTML screen designs for the AI Chat PDF MVP.

Each output file is a complete, standalone screen (inline CSS/JS, no external assets).
Source of truth for behaviour: BLUEPRINT.md 2.4/2.5, 3.1 (DE-01..DE-03), API_DESIGN.md 3.6.3/3.7, PRD 4.1/4.2.
"""
import io, os, sys, html

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------- icons
def icon(name, size=16, label=None):
    paths = {
        "check": '<path d="M20 6 9 17l-5-5"/>',
        "x": '<path d="M18 6 6 18M6 6l12 12"/>',
        "alert": '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
        "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
        "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>',
        "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5M12 3v12"/>',
        "trash": '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>',
        "refresh": '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
        "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
        "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
        "close": '<path d="M18 6 6 18M6 6l12 12"/>',
        "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
        "chev-l": '<path d="m15 18-6-6 6-6"/>',
        "chev-r": '<path d="m9 18 6-6-6-6"/>',
        "zoom-in": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3M11 8v6M8 11h6"/>',
        "zoom-out": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3M8 11h6"/>',
        "scale": '<path d="M12 3v18M5 8h14M5 8l-3 7a4 4 0 0 0 6 0Zm14 0-3 7a4 4 0 0 0 6 0Z"/>',
        "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z"/>',
        "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
        "wifi-off": '<path d="M2 2l20 20M8.5 16.5a5 5 0 0 1 7 0M2 8.8a15 15 0 0 1 4.2-2.6M10.7 5.1A15 15 0 0 1 22 8.8M5 12.9a10 10 0 0 1 5.2-2.8M19 12.9a10 10 0 0 0-1.9-1.4M12 20h.01"/>',
    }
    aria = f' role="img" aria-label="{html.escape(label)}"' if label else ' aria-hidden="true"'
    return (f'<svg class="i" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"{aria}>{paths[name]}</svg>')

# --------------------------------------------------------------------------- CSS
CSS = r"""
:root{
  --font: "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
  --fs-xs:12px; --fs-sm:13px; --fs-md:14px; --fs-lg:16px; --fs-xl:20px; --fs-2xl:24px;
  --sp-1:4px; --sp-2:8px; --sp-3:12px; --sp-4:16px; --sp-5:20px; --sp-6:24px; --sp-8:32px;
  --r-sm:6px; --r-md:10px; --r-lg:14px;
  --bg:#F5F6F8; --surface:#FFFFFF; --surface-2:#F0F2F5; --border:#D7DCE3; --border-strong:#A9B3C1;
  --text:#18212C; --text-muted:#56606E; --text-inverse:#FFFFFF;
  --primary:#1D5BB8; --primary-hover:#174A96; --primary-soft:#E7EFFB;
  --ok:#1C7342; --ok-soft:#E3F3E9; --warn:#7F5300; --warn-soft:#FFF3D6;
  --danger:#AF2A21; --danger-soft:#FCE9E7; --info:#1D5BB8; --info-soft:#E7EFFB;
  --focus:#1D5BB8; --overlay:rgba(16,22,30,.55); --shadow:0 1px 2px rgba(16,24,40,.06),0 4px 12px rgba(16,24,40,.08);
  --cite:#1D5BB8; --cite-soft:#EAF1FC;
  color-scheme: light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#11151B; --surface:#181E26; --surface-2:#202833; --border:#2F3946; --border-strong:#4A5666;
    --text:#E6EAF0; --text-muted:#A6B0BD; --primary:#6FA3F2; --primary-hover:#8DB6F5; --primary-soft:#1E2C42;
    --ok:#5CC48A; --ok-soft:#173023; --warn:#E8B44C; --warn-soft:#33280F; --danger:#F08A80; --danger-soft:#3A1C1A;
    --info:#6FA3F2; --info-soft:#1E2C42; --focus:#8DB6F5; --cite:#8DB6F5; --cite-soft:#1E2C42;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 4px 12px rgba(0,0,0,.35); --text-inverse:#0F141A;
    color-scheme: dark;
  }
}
:root[data-theme="dark"]{
  --bg:#11151B; --surface:#181E26; --surface-2:#202833; --border:#2F3946; --border-strong:#4A5666;
  --text:#E6EAF0; --text-muted:#A6B0BD; --primary:#6FA3F2; --primary-hover:#8DB6F5; --primary-soft:#1E2C42;
  --ok:#5CC48A; --ok-soft:#173023; --warn:#E8B44C; --warn-soft:#33280F; --danger:#F08A80; --danger-soft:#3A1C1A;
  --info:#6FA3F2; --info-soft:#1E2C42; --focus:#8DB6F5; --cite:#8DB6F5; --cite-soft:#1E2C42;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 4px 12px rgba(0,0,0,.35); --text-inverse:#0F141A;
  color-scheme: dark;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;font-family:var(--font);font-size:var(--fs-md);line-height:1.5;color:var(--text);background:var(--bg);min-width:1280px}
button,input,textarea{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px;border-radius:4px}
.i{flex:none;vertical-align:middle}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.skip{position:absolute;left:8px;top:-40px;background:var(--surface);padding:8px 12px;border-radius:var(--r-sm);z-index:100}
.skip:focus{top:8px}

/* ---------- buttons ---------- */
.btn{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:32px;padding:6px 12px;border-radius:var(--r-sm);
  border:1px solid var(--border-strong);background:var(--surface);cursor:pointer;font-weight:600;font-size:var(--fs-sm);text-decoration:none;color:var(--text)}
.btn:hover{background:var(--surface-2)}
.btn-primary{background:var(--primary);border-color:var(--primary);color:var(--text-inverse)}
.btn-primary:hover{background:var(--primary-hover);border-color:var(--primary-hover)}
.btn-danger{background:var(--danger);border-color:var(--danger);color:#fff}
.btn-ghost{border-color:transparent;background:transparent}
.btn-ghost:hover{background:var(--surface-2)}
.btn[disabled],.btn[aria-disabled="true"]{opacity:.55;cursor:not-allowed}
.icon-btn{display:inline-grid;place-items:center;width:32px;height:32px;border-radius:var(--r-sm);border:1px solid transparent;background:transparent;cursor:pointer;color:var(--text-muted)}
.icon-btn:hover{background:var(--surface-2);color:var(--text)}
.link{color:var(--primary);text-decoration:underline;background:none;border:0;padding:0;cursor:pointer;font-weight:600}

/* ---------- app shell ---------- */
.app{display:grid;grid-template-rows:56px 1fr;height:100vh}
.topbar{display:flex;align-items:center;gap:var(--sp-4);padding:0 var(--sp-6);background:var(--surface);border-bottom:1px solid var(--border)}
.brand{display:flex;align-items:center;gap:var(--sp-2);font-weight:700;font-size:var(--fs-lg)}
.brand-mark{display:grid;place-items:center;width:28px;height:28px;border-radius:8px;background:var(--primary);color:var(--text-inverse)}
.topbar .spacer{flex:1}
.user{display:flex;align-items:center;gap:var(--sp-3);color:var(--text-muted);font-size:var(--fs-sm)}
.avatar{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--primary-soft);color:var(--primary);font-weight:700;font-size:var(--fs-xs)}
.main{display:grid;grid-template-columns:400px 1fr;min-height:0}

/* ---------- documents panel ---------- */
.docs{display:flex;flex-direction:column;min-height:0;background:var(--surface);border-right:1px solid var(--border)}
.panel-head{display:flex;align-items:center;gap:var(--sp-2);padding:var(--sp-4) var(--sp-5) var(--sp-3)}
.panel-head h2{margin:0;font-size:var(--fs-lg)}
.quota{margin-left:auto;font-size:var(--fs-xs);color:var(--text-muted);background:var(--surface-2);border:1px solid var(--border);border-radius:999px;padding:2px 10px}
.quota.near{color:var(--warn);background:var(--warn-soft);border-color:transparent;font-weight:600}
.drop{margin:0 var(--sp-5) var(--sp-3);border:2px dashed var(--border-strong);border-radius:var(--r-md);padding:var(--sp-4);text-align:center;background:var(--surface-2)}
.drop.active{border-color:var(--primary);background:var(--primary-soft)}
.drop p{margin:var(--sp-1) 0 0;color:var(--text-muted);font-size:var(--fs-xs)}
.drop .btn{margin-top:var(--sp-2)}
.drop-title{display:flex;align-items:center;justify-content:center;gap:var(--sp-2);font-weight:600}
.scroll{overflow:auto;min-height:0;flex:1;padding:0 var(--sp-5) var(--sp-5)}
.section-label{font-size:var(--fs-xs);font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--text-muted);margin:var(--sp-4) 0 var(--sp-2)}
.list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:var(--sp-2)}
.row{display:grid;grid-template-columns:20px 1fr auto;gap:var(--sp-3);align-items:start;padding:var(--sp-3);border:1px solid var(--border);border-radius:var(--r-md);background:var(--surface)}
.row .name{font-weight:600;word-break:break-word}
.row .meta{font-size:var(--fs-xs);color:var(--text-muted)}
.row .actions{display:flex;gap:2px;align-items:center}
.row .reason{margin-top:var(--sp-1);font-size:var(--fs-sm);color:var(--danger)}
.row.is-failed{border-color:color-mix(in srgb,var(--danger) 40%,var(--border))}
.row .file-ic{color:var(--text-muted);margin-top:2px}
.status{display:inline-flex;align-items:center;gap:4px;margin-top:var(--sp-1);font-size:var(--fs-xs);font-weight:700;border-radius:999px;padding:1px 8px}
.st-processing{color:var(--info);background:var(--info-soft)}
.st-ready{color:var(--ok);background:var(--ok-soft)}
.st-failed{color:var(--danger);background:var(--danger-soft)}
.st-uploading{color:var(--text-muted);background:var(--surface-2)}
.progress{height:6px;border-radius:999px;background:var(--surface-2);overflow:hidden;margin-top:var(--sp-2)}
.progress>span{display:block;height:100%;background:var(--primary)}
.spin{width:12px;height:12px;border:2px solid currentColor;border-right-color:transparent;border-radius:50%;animation:spin .9s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion: reduce){.spin,.dots span{animation:none}}

/* ---------- empty states & alerts ---------- */
.empty{text-align:center;padding:var(--sp-8) var(--sp-4);color:var(--text-muted)}
.empty h3{margin:var(--sp-3) 0 var(--sp-1);color:var(--text);font-size:var(--fs-lg)}
.empty .ill{display:inline-grid;place-items:center;width:56px;height:56px;border-radius:16px;background:var(--primary-soft);color:var(--primary)}
.steps{list-style:none;padding:0;margin:var(--sp-4) auto 0;max-width:340px;text-align:left;display:flex;flex-direction:column;gap:var(--sp-2)}
.steps li{display:flex;gap:var(--sp-3);align-items:flex-start;color:var(--text)}
.steps b{display:grid;place-items:center;flex:none;width:22px;height:22px;border-radius:50%;background:var(--primary-soft);color:var(--primary);font-size:var(--fs-xs)}
.alert{display:flex;gap:var(--sp-3);align-items:flex-start;padding:var(--sp-3);border-radius:var(--r-md);font-size:var(--fs-sm);border:1px solid transparent}
.alert .t{font-weight:700}
.alert-danger{background:var(--danger-soft);color:var(--danger)}
.alert-danger .body{color:var(--text)}
.alert-warn{background:var(--warn-soft);color:var(--warn)}
.alert-warn .body{color:var(--text)}
.alert-info{background:var(--info-soft);color:var(--info)}
.alert-info .body{color:var(--text)}

/* ---------- chat panel ---------- */
.chat{display:flex;flex-direction:column;min-height:0}
.chat .panel-head{padding:var(--sp-4) var(--sp-8) var(--sp-3);border-bottom:1px solid var(--border);background:var(--surface)}
.chat .panel-head p{margin:0;color:var(--text-muted);font-size:var(--fs-sm)}
.thread{flex:1;overflow:auto;padding:var(--sp-6) var(--sp-8);display:flex;flex-direction:column;gap:var(--sp-5)}
.thread-inner{max-width:880px;width:100%;margin:0 auto;display:flex;flex-direction:column;gap:var(--sp-5)}
.q{align-self:flex-end;max-width:72%;background:var(--primary);color:var(--text-inverse);padding:var(--sp-3) var(--sp-4);border-radius:var(--r-lg) var(--r-lg) 4px var(--r-lg)}
.q .time{display:block;font-size:var(--fs-xs);opacity:.85;margin-top:2px;text-align:right}
.a{align-self:flex-start;max-width:86%;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg) var(--r-lg) var(--r-lg) 4px;padding:var(--sp-4);box-shadow:var(--shadow)}
.a p{margin:0 0 var(--sp-2)}
.a-head{display:flex;align-items:center;gap:var(--sp-2);font-size:var(--fs-xs);color:var(--text-muted);margin-bottom:var(--sp-2)}
.ref{display:inline-grid;place-items:center;min-width:22px;height:20px;padding:0 5px;margin:0 1px;border-radius:5px;border:1px solid var(--cite);background:var(--cite-soft);color:var(--cite);font-size:var(--fs-xs);font-weight:700;cursor:pointer;vertical-align:1px}
.sources{border-top:1px solid var(--border);margin-top:var(--sp-3);padding-top:var(--sp-3)}
.sources h4{margin:0 0 var(--sp-2);font-size:var(--fs-xs);text-transform:uppercase;letter-spacing:.04em;color:var(--text-muted)}
.chips{display:flex;flex-wrap:wrap;gap:var(--sp-2)}
.chip{display:inline-flex;align-items:center;gap:6px;min-height:28px;padding:3px 10px;border-radius:999px;border:1px solid var(--border-strong);background:var(--surface);font-size:var(--fs-sm);cursor:pointer;color:var(--text)}
.chip:hover{border-color:var(--cite);color:var(--cite)}
.chip .n{font-weight:700;color:var(--cite)}
.chip.deleted{border-style:dashed;color:var(--text-muted);cursor:not-allowed}
.badge{display:inline-flex;align-items:center;gap:4px;font-size:var(--fs-xs);font-weight:700;border-radius:999px;padding:2px 8px}
.badge-insufficient{background:var(--warn-soft);color:var(--warn)}
.badge-conflict{background:var(--warn-soft);color:var(--warn)}
.badge-failed{background:var(--danger-soft);color:var(--danger)}
.a.insufficient{border-style:dashed}
.a.failed{border-color:color-mix(in srgb,var(--danger) 45%,var(--border))}
.conflict{margin-top:var(--sp-2);padding:var(--sp-3);border-radius:var(--r-md);background:var(--warn-soft)}
.conflict ul{margin:var(--sp-1) 0 0;padding-left:18px}
.dots{display:inline-flex;gap:4px}
.dots span{width:6px;height:6px;border-radius:50%;background:var(--text-muted);animation:blink 1.2s infinite}
.dots span:nth-child(2){animation-delay:.2s}.dots span:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,80%,100%{opacity:.25}40%{opacity:1}}
.composer{border-top:1px solid var(--border);background:var(--surface);padding:var(--sp-4) var(--sp-8) var(--sp-5)}
.composer-inner{max-width:880px;margin:0 auto}
.box{display:flex;gap:var(--sp-3);align-items:flex-end;border:1px solid var(--border-strong);border-radius:var(--r-lg);padding:var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-4);background:var(--surface)}
.box:focus-within{border-color:var(--focus);box-shadow:0 0 0 3px var(--primary-soft)}
.box textarea{flex:1;border:0;outline:0;resize:none;background:transparent;min-height:44px;max-height:160px;padding:var(--sp-2) 0}
.box.locked{background:var(--surface-2)}
.composer-foot{display:flex;justify-content:space-between;gap:var(--sp-4);margin-top:var(--sp-2);font-size:var(--fs-xs);color:var(--text-muted)}
.counter.over{color:var(--danger);font-weight:700}
.locked-reason{display:flex;align-items:center;gap:var(--sp-2);color:var(--text-muted);font-size:var(--fs-sm);margin-bottom:var(--sp-2)}

/* ---------- toast ---------- */
.toasts{position:fixed;left:var(--sp-5);bottom:var(--sp-5);width:360px;display:flex;flex-direction:column;gap:var(--sp-2);z-index:30}
.toast{display:flex;gap:var(--sp-3);align-items:flex-start;padding:var(--sp-3) var(--sp-4);border-radius:var(--r-md);background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow);font-size:var(--fs-sm)}
.toast .t{font-weight:700}
.toast.ok .lead{color:var(--ok)} .toast.warn .lead{color:var(--warn)} .toast.danger .lead{color:var(--danger)}
.toast .timer{height:3px;background:var(--surface-2);border-radius:2px;margin-top:var(--sp-2);overflow:hidden}
.toast .timer span{display:block;height:100%;width:60%;background:var(--border-strong)}

/* ---------- modal / overlay ---------- */
.overlay{position:fixed;inset:0;background:var(--overlay);display:grid;place-items:center;z-index:40}
.dialog{width:480px;background:var(--surface);border-radius:var(--r-lg);box-shadow:var(--shadow);padding:var(--sp-6)}
.dialog h2{margin:0 0 var(--sp-2);font-size:var(--fs-xl)}
.dialog p{margin:0 0 var(--sp-3);color:var(--text-muted)}
.dialog .foot{display:flex;justify-content:flex-end;gap:var(--sp-2);margin-top:var(--sp-5)}
.viewer{position:fixed;inset:24px 24px 24px 424px;background:var(--surface);border-radius:var(--r-lg);box-shadow:var(--shadow);display:grid;grid-template-rows:56px 1fr;z-index:40;overflow:hidden}
.viewer-bar{display:flex;align-items:center;gap:var(--sp-3);padding:0 var(--sp-4);border-bottom:1px solid var(--border)}
.viewer-bar .title{font-weight:700}
.viewer-bar .pager{display:flex;align-items:center;gap:var(--sp-1);margin-left:auto}
.viewer-bar input{width:52px;text-align:center;border:1px solid var(--border-strong);border-radius:var(--r-sm);padding:4px;background:var(--surface)}
.viewer-body{overflow:auto;background:var(--surface-2);padding:var(--sp-6);display:flex;justify-content:center}
.page{width:640px;min-height:860px;background:#fff;color:#1b1b1b;box-shadow:var(--shadow);padding:56px 64px;font-family:"Times New Roman",Tinos,"Noto Serif",serif;font-size:14px;line-height:1.6;position:relative}
.page h3{font-size:16px;margin:0 0 12px}
.page .pno{position:absolute;bottom:24px;left:0;right:0;text-align:center;font-size:12px;color:#666}
.page .hl{background:#FFF1B8;outline:2px solid #E0B100;outline-offset:2px}
.page .ln{height:9px;background:#E7E7E7;border-radius:3px;margin:10px 0}

/* ---------- standalone pages ---------- */
.center{min-height:100vh;display:grid;place-items:center;padding:var(--sp-8)}
.card{width:520px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);box-shadow:var(--shadow);padding:var(--sp-8);text-align:center}
.card h1{font-size:var(--fs-2xl);margin:var(--sp-4) 0 var(--sp-2)}
.card p{color:var(--text-muted);margin:0 0 var(--sp-3)}
.card .ill{display:inline-grid;place-items:center;width:64px;height:64px;border-radius:18px}
.card .actions{display:flex;justify-content:center;gap:var(--sp-2);margin-top:var(--sp-5)}
.ref-code{font-family:Consolas,monospace;font-size:var(--fs-xs);background:var(--surface-2);border-radius:var(--r-sm);padding:2px 6px}

/* ---------- design spec panel (không thuộc giao diện sản phẩm) ---------- */
.spec{position:fixed;right:0;top:35%;z-index:60;font-size:var(--fs-sm);display:flex;align-items:flex-start;flex-direction:row-reverse}
.spec summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:6px;background:#2B2F36;color:#fff;border-radius:8px 0 0 8px;padding:12px 6px;font-weight:600;writing-mode:vertical-rl;box-shadow:var(--shadow)}
.spec summary::-webkit-details-marker{display:none}
.spec[open] summary{border-radius:8px 0 0 8px}
.spec .spec-body{width:400px;background:#2B2F36;color:#E8EAED;border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);max-height:60vh;overflow:auto}
.spec h4{margin:10px 0 4px;font-size:12px;color:#9FB3C8;text-transform:uppercase;letter-spacing:.04em}
.spec h4:first-child{margin-top:0}
.spec ul{margin:0;padding-left:18px}
.spec code{color:#FFD58A}
"""

# --------------------------------------------------------------------------- building blocks
def page(title, body, screen_id, spec, script=""):
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} – AI Chat PDF</title>
<meta name="description" content="Thiết kế màn hình {screen_id} – MVP AI Chat với tài liệu PDF (BLUEPRINT v0.3)">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Bỏ qua tới nội dung chính</a>
{body}
{spec_panel(screen_id, title, spec)}
<script>const th=document.getElementById('thread');if(th)th.scrollTop=th.scrollHeight;{script}</script>
</body>
</html>
"""

def spec_panel(screen_id, title, spec):
    items = "".join(f"<h4>{html.escape(k)}</h4><ul>{''.join(f'<li>{v}</li>' for v in vs)}</ul>" for k, vs in spec)
    return (f'<details class="spec"><summary>{icon("info",14)} Ghi chú thiết kế · {screen_id}</summary>'
            f'<div class="spec-body"><h4>Màn hình</h4><ul><li>{html.escape(title)}</li></ul>{items}</div></details>')

def topbar(expiring=False):
    return f"""<header class="topbar">
  <div class="brand"><span class="brand-mark">{icon("chat",16)}</span>AI Chat PDF</div>
  <div class="spacer"></div>
  <div class="user"><span class="avatar" aria-hidden="true">LN</span><span>lan.nguyen@congty.vn</span>
    <button class="btn btn-ghost" type="button">{icon("logout",16)} Đăng xuất</button></div>
</header>"""

def drop(active=False, disabled=False):
    return f"""<div class="drop{' active' if active else ''}" aria-label="Vùng tải tài liệu">
  <div class="drop-title">{icon("upload",18)} Kéo thả file PDF vào đây</div>
  <p>hoặc</p>
  <button class="btn btn-primary" type="button"{' disabled' if disabled else ''}>{icon("upload",16)} Chọn file PDF</button>
  <p>Tối đa 10 file mỗi lần · mỗi file ≤ 20 MB và ≤ 300 trang · chỉ PDF có chữ (chưa hỗ trợ PDF scan)</p>
</div>"""

STATUS = {
    "processing": ('st-processing', '<span class="spin" aria-hidden="true"></span> Đang xử lý'),
    "ready": ('st-ready', icon("check", 12) + ' Sẵn sàng'),
    "failed": ('st-failed', icon("x", 12) + ' Thất bại'),
}

def doc_row(name, meta, status, reason=None, retry=False):
    cls, label = STATUS[status]
    actions = ""
    retry_html = f'<div style="margin-top:8px"><button class="btn" type="button">{icon("refresh",14)} Xử lý lại</button></div>' if retry else ""
    actions += f'<button class="icon-btn" type="button" aria-label="Xóa {html.escape(name)}">{icon("trash",16)}</button>'
    reason_html = f'<div class="reason">{reason}</div>' if reason else ""
    return f"""<li class="row{' is-failed' if status=='failed' else ''}">
  <span class="file-ic">{icon("file",18)}</span>
  <div><div class="name">{html.escape(name)}</div><div class="meta">{meta}</div>
    <span class="status {cls}">{label}</span>{reason_html}{retry_html}</div>
  <div class="actions">{actions}</div>
</li>"""

def upload_row(name, meta, state, progress=None, reason=None):
    if state == "uploading":
        status = f'<span class="status st-uploading"><span class="spin" aria-hidden="true"></span> Đang tải lên {progress}%</span>'
        extra = f'<div class="progress" role="progressbar" aria-label="Tiến độ tải {html.escape(name)}" aria-valuenow="{progress}" aria-valuemin="0" aria-valuemax="100"><span style="width:{progress}%"></span></div>'
        actions = ""
        cls = ""
    elif state == "queued":
        status = f'<span class="status st-uploading">{icon("clock",12)} Đang chờ tải lên</span>'
        extra, actions, cls = "", "", ""
    elif state == "rejected":
        status = f'<span class="status st-failed">{icon("x",12)} Không nhận</span>'
        extra = f'<div class="reason">{reason}</div>'
        actions = f'<button class="icon-btn" type="button" aria-label="Đóng thông báo về {html.escape(name)}">{icon("close",16)}</button>'
        cls = " is-failed"
    else:  # failed (network)
        status = f'<span class="status st-failed">{icon("wifi-off",12)} Tải lên thất bại</span>'
        extra = f'<div class="reason">{reason}</div><div style="margin-top:8px"><button class="btn" type="button">{icon("refresh",14)} Tải lại</button></div>'
        actions = ''
        cls = " is-failed"
    return f"""<li class="row{cls}">
  <span class="file-ic">{icon("file",18)}</span>
  <div><div class="name">{html.escape(name)}</div><div class="meta">{meta}</div>{status}{extra}</div>
  <div class="actions">{actions}</div>
</li>"""

def docs_panel(content, quota="0/100", quota_near=False, drop_html=None):
    return f"""<section class="docs" aria-labelledby="docs-title">
  <div class="panel-head"><h2 id="docs-title">Tài liệu</h2>
    <span class="quota{' near' if quota_near else ''}" title="Số tài liệu đang dùng / giới hạn">{quota} tài liệu</span></div>
  {drop_html if drop_html is not None else drop()}
  <div class="scroll" aria-live="polite">{content}</div>
</section>"""

def composer(state="ready", value="", reason=None, counter=None):
    locked = state in ("locked", "sending", "rate")
    reason_html = f'<div class="locked-reason">{icon("lock",14)} {reason}</div>' if reason else ""
    cnt = counter or f"{len(value)}/2.000"
    btn_label = "Đang gửi…" if state == "sending" else "Gửi"
    return f"""<div class="composer">
  <div class="composer-inner">
    {reason_html}
    <form class="box{' locked' if locked else ''}" onsubmit="return false" aria-label="Đặt câu hỏi">
      <label class="sr-only" for="q">Câu hỏi về tài liệu</label>
      <textarea id="q" rows="2" maxlength="2000" placeholder="Hỏi về nội dung tài liệu, ví dụ: Điều khoản thanh toán trong hợp đồng A là gì?"{' disabled' if locked else ''}>{html.escape(value)}</textarea>
      <button class="btn btn-primary" type="submit"{' disabled' if locked or not value else ''}>{icon("send",16)} {btn_label}</button>
    </form>
    <div class="composer-foot"><span>Enter để gửi · Shift + Enter để xuống dòng · Câu trả lời chỉ dựa trên tài liệu Sẵn sàng của bạn</span><span class="counter" id="counter">{cnt}</span></div>
  </div>
</div>"""

def chat_panel(thread_html, composer_html):
    return f"""<section class="chat" aria-labelledby="chat-title">
  <div class="panel-head"><div><h2 id="chat-title" style="margin:0;font-size:var(--fs-lg)">Hỏi đáp</h2>
    <p>Hỏi bằng tiếng Việt hoặc tiếng Anh. Mỗi câu trả lời kèm tên tài liệu và số trang để bạn kiểm chứng.</p></div></div>
  <div class="thread" id="thread" aria-live="polite" aria-label="Hội thoại">{thread_html}</div>
  {composer_html}
</section>"""

def app(docs_html, chat_html, extra=""):
    return f"""<div class="app">
{topbar()}
<main class="main" id="main">
{docs_html}
{chat_html}
</main>
</div>
{extra}"""

def q(text, time):
    return f'<div class="q"><span class="sr-only">Bạn hỏi: </span>{html.escape(text)}<span class="time">{time}</span></div>'

def chip(n, name, page=None, deleted=False):
    label = f'{html.escape(name)}' + (f' · tr.{page}' if page else '') + (' (đã xóa)' if deleted else '')
    if deleted:
        return f'<span class="chip deleted" aria-disabled="true" title="Tài liệu đã bị xóa"><span class="n">[{n}]</span> {label}</span>'
    return f'<button class="chip" type="button" aria-label="Mở nguồn {n}: {label}"><span class="n">[{n}]</span> {icon("file",14)} {label}</button>'

def ref(n): return f'<button class="ref" type="button" aria-label="Xem nguồn {n}">{n}</button>'

def a_answered(paragraphs, chips, conflict=None, time="14:21"):
    conflict_html = ""
    if conflict:
        conflict_html = (f'<div class="conflict"><span class="badge badge-conflict">{icon("scale",12)} Các tài liệu không thống nhất</span>'
                         f'<ul>{"".join(f"<li>{c}</li>" for c in conflict)}</ul></div>')
    return f"""<article class="a" aria-label="Câu trả lời">
  <div class="a-head">{icon("chat",14)} Trợ lý tài liệu · {time}</div>
  {''.join(f'<p>{p}</p>' for p in paragraphs)}
  {conflict_html}
  <div class="sources"><h4>Nguồn tham chiếu</h4><div class="chips">{''.join(chips)}</div></div>
</article>"""

def a_insufficient(time="14:24"):
    return f"""<article class="a insufficient" aria-label="Câu trả lời: chưa đủ thông tin">
  <div class="a-head"><span class="badge badge-insufficient">{icon("info",12)} Chưa đủ thông tin</span> · {time}</div>
  <p>Các tài liệu Sẵn sàng của bạn chưa có thông tin để trả lời câu hỏi này. Hệ thống không suy đoán ngoài tài liệu.</p>
  <p style="color:var(--text-muted);font-size:var(--fs-sm);margin:0">Gợi ý: tải thêm tài liệu có chứa thông tin này, hoặc diễn đạt lại câu hỏi cụ thể hơn.</p>
</article>"""

def a_sending():
    return f"""<article class="a" aria-label="Đang soạn câu trả lời" aria-busy="true">
  <div class="a-head">{icon("chat",14)} Trợ lý tài liệu</div>
  <div style="display:flex;align-items:center;gap:10px;color:var(--text-muted)"><span class="dots" aria-hidden="true"><span></span><span></span><span></span></span> Đang tìm trong tài liệu và soạn câu trả lời… (thường dưới 15 giây)</div>
</article>"""

def a_failed(title, detail, time="14:30"):
    return f"""<article class="a failed" aria-label="Lỗi khi tạo câu trả lời" role="alert">
  <div class="a-head"><span class="badge badge-failed">{icon("alert",12)} Chưa trả lời được</span> · {time}</div>
  <p><strong>{title}</strong></p>
  <p style="color:var(--text-muted);font-size:var(--fs-sm)">{detail}</p>
  <button class="btn" type="button">{icon("refresh",14)} Gửi lại</button>
</article>"""

def toast(kind, title, body, icon_name):
    return f"""<div class="toast {kind}" role="status">
  <span class="lead">{icon(icon_name,18)}</span>
  <div style="flex:1"><div class="t">{title}</div><div>{body}</div><div class="timer" aria-hidden="true"><span></span></div></div>
  <button class="icon-btn" type="button" aria-label="Đóng thông báo">{icon("close",14)}</button>
</div>"""

COUNTER_JS = """
const ta=document.getElementById('q'),c=document.getElementById('counter');
if(ta&&c&&!ta.disabled){const send=ta.form.querySelector('button[type=submit]');
const upd=()=>{const n=ta.value.length;c.textContent=n.toLocaleString('vi-VN')+'/2.000';c.classList.toggle('over',n>=2000);send.disabled=!ta.value.trim();};
ta.addEventListener('input',upd);upd();}
"""

# --------------------------------------------------------------------------- common data
DOCS_READY = [
    doc_row("hop-dong-A.pdf", "12 trang · 1,0 MB · 24/10/2026 09:12", "ready"),
    doc_row("chinh-sach-ban-hang-2026.pdf", "48 trang · 3,4 MB · 24/10/2026 09:12", "ready"),
    doc_row("bang-gia-Q4.pdf", "3 trang · 512 KB · 24/10/2026 09:13", "ready"),
]
SCREENS = []

def add(fname, title, sid, body, spec, script=""):
    SCREENS.append((fname, sid, title, spec))
    io.open(os.path.join(OUT, fname), "w", encoding="utf-8", newline="\n").write(page(title, body, sid, spec, script))

# --------------------------------------------------------------------------- S01 empty
empty_docs = f"""<div class="empty"><span class="ill">{icon("file",26)}</span>
  <h3>Chưa có tài liệu nào</h3>
  <p>Tải lên các file PDF của dự án để bắt đầu hỏi đáp.</p></div>"""
empty_chat = f"""<div class="thread-inner"><div class="empty" style="padding-top:64px"><span class="ill">{icon("chat",26)}</span>
  <h3>Hỏi đáp với tài liệu của bạn</h3>
  <p>Chỉ cần ba bước:</p>
  <ol class="steps">
    <li><b>1</b><span>Tải lên một hoặc nhiều file PDF ở khu vực <strong>Tài liệu</strong> bên trái.</span></li>
    <li><b>2</b><span>Chờ tài liệu chuyển sang <strong>Sẵn sàng</strong> (thường dưới 3 phút).</span></li>
    <li><b>3</b><span>Đặt câu hỏi – câu trả lời luôn kèm tên tài liệu và số trang để bạn kiểm chứng.</span></li>
  </ol></div></div>"""
add("S01_main_empty.html", "Màn hình chính – chưa có tài liệu", "S01",
    app(docs_panel(empty_docs, "0/100"),
        chat_panel(empty_chat, composer("locked", reason="Cần ít nhất một tài liệu Sẵn sàng để bắt đầu hỏi."))),
    [("Story / trường hợp", ["US-006 (trạng thái trống), US-012 AC 2 (ô hỏi bị khóa)", "E-01"]),
     ("API", ["<code>GET /me</code>, <code>GET /documents</code> (items rỗng), <code>GET /conversations/current</code>, <code>GET /events</code>"]),
     ("Hành vi", ["Ô hỏi bị khóa kèm lý do bằng chữ (không chỉ màu)", "Nút 'Chọn file PDF' mở hộp chọn file; kéo thả cũng được", "Giới hạn hiển thị lấy từ <code>/me.limits</code>, không hard-code"])])

# --------------------------------------------------------------------------- S02 uploading
up_list = f"""<div class="section-label">Đang tải lên (3/5)</div>
<ul class="list">
{upload_row("hop-dong-A.pdf", "1,0 MB", "uploading", progress=72)}
{upload_row("chinh-sach-ban-hang-2026.pdf", "3,4 MB", "uploading", progress=35)}
{upload_row("bang-gia-Q4.pdf", "512 KB", "queued")}
{upload_row("bao-gia-khach-hang.docx", "220 KB", "rejected", reason='"bao-gia-khach-hang.docx" không phải file PDF hợp lệ.')}
{upload_row("ho-so-nang-luc.pdf", "18,2 MB", "failed", reason="Mất kết nối khi đang tải lên. Bấm <strong>Tải lại</strong> – file sẽ không bị trùng.")}
</ul>
<div class="section-label">Tài liệu của bạn</div>
<div class="empty" style="padding:16px 0"><p>Tài liệu sẽ xuất hiện ở đây khi tải lên xong.</p></div>"""
add("S02_main_uploading.html", "Màn hình chính – đang tải lên nhiều file", "S02",
    app(docs_panel(up_list, "0/100", drop_html=drop(active=True)),
        chat_panel(empty_chat, composer("locked", reason="Đang xử lý tài liệu, bạn có thể hỏi khi có ít nhất một tài liệu Sẵn sàng."))),
    [("Story / trường hợp", ["US-001 (tiến độ tải lên), US-002 (nhiều file), US-003 (không phải PDF), US-026 (lỗi tải lên)", "E-02, E-04, E-07"]),
     ("API", ["<code>POST /upload-batches</code> → <code>PUT /upload-batches/{batch_id}/files/{client_file_id}</code> (tối đa 3 song song, XHR có tiến độ)", "422 <code>not_pdf</code>; lỗi mạng → 'Tải lại' cùng <code>client_file_id</code> (API AD-06)"]),
     ("Hành vi", ["File sai đuôi bị chặn ngay ở client, không gửi", "Thanh tiến độ có <code>role=progressbar</code>", "Vùng kéo thả ở trạng thái active khi đang kéo file vào"])])

# --------------------------------------------------------------------------- S03 document states
states_list = f"""<ul class="list">
{doc_row("hop-dong-A.pdf", "12 trang · 1,0 MB · 24/10/2026 09:12", "ready")}
{doc_row("chinh-sach-ban-hang-2026.pdf", "48 trang · 3,4 MB · 24/10/2026 09:12", "processing")}
{doc_row("bang-gia-Q4.pdf", "3 trang · 512 KB · 24/10/2026 09:13", "processing")}
{doc_row("ho-so-scan-2019.pdf", "5 trang · 2,0 MB · 24/10/2026 09:13", "failed", reason="File không chứa văn bản trích xuất được (PDF scan chưa được hỗ trợ). Hãy tải bản PDF có chữ.")}
{doc_row("bao-cao-thi-truong.pdf", "120 trang · 9,8 MB · 24/10/2026 09:14", "failed", reason="Lỗi xử lý tạm thời. Bạn có thể xử lý lại mà không cần tải lại file.", retry=True)}
{doc_row("hop-dong-mat-khau.pdf", "8 trang · 640 KB · 24/10/2026 09:14", "failed", reason="File được bảo vệ bằng mật khẩu. Hãy gỡ mật khẩu rồi tải lại.")}
</ul>"""
ready_chat = f"""<div class="thread-inner"><div class="empty" style="padding-top:64px"><span class="ill">{icon("chat",26)}</span>
  <h3>Bạn có thể bắt đầu hỏi</h3>
  <p>1 tài liệu đã Sẵn sàng. Các tài liệu đang xử lý sẽ tự được dùng khi sẵn sàng.</p></div></div>"""
add("S03_main_document_states.html", "Màn hình chính – trạng thái tài liệu", "S03",
    app(docs_panel(states_list, "6/100"), chat_panel(ready_chat, composer("ready")),
        extra='<div class="toasts" aria-live="polite">' + toast("ok", "Tài liệu đã Sẵn sàng", "hop-dong-A.pdf đã có thể dùng để hỏi đáp.", "check") + '</div>'),
    [("Story / trường hợp", ["US-005, US-006, US-007 (thông báo Sẵn sàng), US-008 (Thất bại + lý do), US-009 (Xử lý lại chỉ với R-04), US-025", "E-03, E-09, E-10"]),
     ("Mã lý do", ["R-01 không đọc được · R-02 có mật khẩu · R-03 PDF scan · R-04 lỗi tạm thời (chỉ R-04 có nút Xử lý lại)"]),
     ("API", ["SSE <code>document.status_changed</code> → làm mới dòng, hiện thông báo", "<code>POST /documents/{id}/reprocess</code> → 202"]),
     ("Hành vi", ["Trạng thái = biểu tượng + chữ (WCAG 1.4.1)", "Thông báo góc dưới trái, tự ẩn ≤ 5 s, không che ô hỏi", "Thanh dưới thông báo thể hiện thời gian còn lại"])],
    COUNTER_JS)

# --------------------------------------------------------------------------- S04 chat answers
thread = f"""<div class="thread-inner">
{q("Điều khoản thanh toán với khách hàng chiến lược là gì?", "14:20")}
{a_answered([
    f"Theo hợp đồng A, bên mua thanh toán trong vòng <strong>30 ngày</strong> kể từ ngày nhận hóa đơn hợp lệ {ref(1)}.",
    f"Chính sách bán hàng 2026 cho phép kéo dài tối đa <strong>45 ngày</strong> với khách hàng được xếp loại chiến lược, cần phê duyệt của Giám đốc kinh doanh {ref(2)}."],
    [chip(1, "hop-dong-A.pdf", 4), chip(2, "chinh-sach-ban-hang-2026.pdf", 12)], time="14:20")}
{q("Giá gói Premium hiện tại là bao nhiêu?", "14:22")}
{a_answered([f"Hai tài liệu nêu giá gói Premium khác nhau:"],
    [chip(1, "bang-gia-Q4.pdf", 2), chip(2, "chinh-sach-ban-hang-2026.pdf", 31)],
    conflict=[f"<strong>12.500.000 đ/tháng</strong> theo bảng giá Q4 {ref(1)}",
              f"<strong>11.900.000 đ/tháng</strong> theo chính sách bán hàng 2026 {ref(2)}",
              "Hãy kiểm tra tài liệu nào mới hơn trước khi báo giá cho khách hàng."], time="14:22")}
{q("Đối thủ chính của chúng ta ở thị trường Nhật là ai?", "14:24")}
{a_insufficient("14:24")}
{q("Hợp đồng A có hiệu lực bao lâu?", "14:25")}
{a_sending()}
</div>"""
add("S04_main_chat_answers.html", "Màn hình chính – hỏi đáp có trích dẫn", "S04",
    app(docs_panel('<ul class="list">' + "".join(DOCS_READY) + "</ul>", "3/100"),
        chat_panel(thread, composer("sending", value="", reason=None))),
    [("Story / trường hợp", ["US-012, US-013, US-014 (nhiều câu trong phiên), US-016 (Chưa đủ thông tin), US-017 (đa tài liệu), US-018 (mâu thuẫn), US-020/021 (tên + trang), US-025 (đang soạn)", "E-16"]),
     ("API", ["<code>POST /conversations/{id}/messages</code> → <code>Answer</code> với <code>status</code> ANSWERED/INSUFFICIENT, <code>citations[]</code>", "Dấu <code>[n]</code> trong <code>answer</code> khớp <code>Citation.ordinal</code>; SPA tách thành nút (CA-04), không dựng HTML từ câu trả lời"]),
     ("Hành vi", ["Câu trả lời 'Chưa đủ thông tin' có nhãn riêng, viền nét đứt, không có phần nguồn", "Mâu thuẫn: liệt kê từng giá trị kèm nguồn", "Trong lúc chờ: ô hỏi khóa, chỉ báo ba chấm (tắt hiệu ứng khi prefers-reduced-motion)", "Bấm nhãn nguồn → S06 trình xem PDF"])])

# --------------------------------------------------------------------------- S05 chat errors
thread_err = f"""<div class="thread-inner">
{q("Phí phạt chậm thanh toán trong hợp đồng A là bao nhiêu?", "14:28")}
{a_answered([f"Bên mua chịu lãi chậm trả <strong>0,05%/ngày</strong> trên số tiền chậm thanh toán, tối đa 10% giá trị hợp đồng {ref(1)}. Mức này giống quy định trong chính sách bán hàng cũ {ref(2)}."],
    [chip(1, "hop-dong-A.pdf", 5), chip(2, "chinh-sach-2025.pdf", 9, deleted=True)], time="14:28")}
{q("Tóm tắt các điều kiện bảo hành trong hợp đồng A.", "14:30")}
{a_failed("Không thể tạo câu trả lời lúc này, vui lòng thử lại.", "Câu hỏi của bạn vẫn được giữ nguyên. Bấm Gửi lại để thử lần nữa.")}
</div>"""
alert_rate = f"""<div class="alert alert-warn" role="status" style="margin-bottom:8px">{icon("clock",16)}<div class="body"><span class="t">Bạn thao tác quá nhanh.</span> Vui lòng thử lại sau <strong>42 giây</strong>.</div></div>"""
composer_rate = composer("rate", value="Hợp đồng A có cho phép chuyển nhượng không?", counter="44/2.000").replace('<div class="composer-inner">', '<div class="composer-inner">' + alert_rate, 1)
add("S05_main_chat_errors.html", "Màn hình chính – lỗi và giới hạn khi hỏi", "S05",
    app(docs_panel('<ul class="list">' + "".join(DOCS_READY) + "</ul>", "3/100"),
        chat_panel(thread_err, composer_rate),
        extra='<div class="toasts" aria-live="polite">' + toast("warn", "Phiên sắp hết hạn", "Phiên làm việc sẽ hết hạn sau 5 phút. Câu hỏi đang soạn sẽ được giữ lại khi bạn đăng nhập lại.", "clock") + '</div>'),
    [("Story / trường hợp", ["US-026 (báo lỗi câu hỏi), US-027 (Gửi lại – cùng <code>client_request_id</code>), E-05, E-06, E-13/E-19 (nguồn đã xóa), E-17 (sắp hết phiên)"]),
     ("API", ["503 <code>ai_unavailable</code> / 504 <code>ai_timeout</code> → thẻ lỗi tại vị trí câu trả lời", "429 <code>rate_limited</code> + <code>Retry-After</code> → đếm ngược, tự mở khóa", "SSE <code>session.expiring</code> → thông báo cảnh báo"]),
     ("Hành vi", ["Lỗi hiển thị đúng chỗ, câu hỏi gốc vẫn hiện; không cần tải lại trang (UX-06)", "Nhãn nguồn của tài liệu đã xóa: viền nét đứt, '(đã xóa)', không bấm được", "Nội dung ô hỏi được giữ trong lúc chờ hết giới hạn"])])

# --------------------------------------------------------------------------- S06 PDF viewer
viewer = f"""<div class="overlay" style="background:rgba(16,22,30,.35)"></div>
<div class="viewer" role="dialog" aria-modal="true" aria-labelledby="viewer-title">
  <div class="viewer-bar">
    {icon("file",18)}<span class="title" id="viewer-title">hop-dong-A.pdf</span>
    <span class="badge" style="background:var(--cite-soft);color:var(--cite)">Mở từ nguồn [1] · trang 4</span>
    <div class="pager">
      <button class="icon-btn" type="button" aria-label="Trang trước">{icon("chev-l",18)}</button>
      <label class="sr-only" for="pg">Trang</label><input id="pg" value="4" inputmode="numeric"> <span style="color:var(--text-muted)">/ 12</span>
      <button class="icon-btn" type="button" aria-label="Trang sau">{icon("chev-r",18)}</button>
      <span style="width:12px"></span>
      <button class="icon-btn" type="button" aria-label="Thu nhỏ">{icon("zoom-out",18)}</button>
      <span style="color:var(--text-muted);font-size:var(--fs-sm)">100%</span>
      <button class="icon-btn" type="button" aria-label="Phóng to">{icon("zoom-in",18)}</button>
    </div>
    <button class="btn" type="button" aria-label="Đóng trình xem (Esc)">{icon("close",16)} Đóng</button>
  </div>
  <div class="viewer-body">
    <div class="page" aria-label="Trang 4 của hop-dong-A.pdf">
      <h3>ĐIỀU 5. THANH TOÁN</h3>
      <p>5.1. Giá trị hợp đồng được thanh toán bằng chuyển khoản vào tài khoản của Bên Bán theo thông tin tại Phụ lục 2.</p>
      <p>5.2. Bên Mua thanh toán trong vòng 30 (ba mươi) ngày kể từ ngày nhận được hóa đơn giá trị gia tăng hợp lệ và biên bản nghiệm thu.</p>
      <p>5.3. Trường hợp chậm thanh toán, Bên Mua chịu lãi chậm trả theo quy định tại Điều 6.</p>
      <div class="ln" style="width:92%"></div><div class="ln" style="width:85%"></div><div class="ln" style="width:88%"></div>
      <h3 style="margin-top:24px">ĐIỀU 6. LÃI CHẬM TRẢ</h3>
      <div class="ln" style="width:95%"></div><div class="ln" style="width:80%"></div><div class="ln" style="width:90%"></div><div class="ln" style="width:60%"></div>
      <div class="pno">Trang 4/12</div>
    </div>
  </div>
</div>"""
add("S06_pdf_viewer.html", "Trình xem tài liệu gốc tại trang", "S06",
    app(docs_panel('<ul class="list">' + "".join(DOCS_READY) + "</ul>", "3/100"),
        chat_panel(f'<div class="thread-inner">{q("Điều khoản thanh toán với khách hàng chiến lược là gì?", "14:20")}</div>', composer("ready")),
        extra=viewer),
    [("Story / trường hợp", ["US-022 (P1, chờ OQ-014), E-19"]),
     ("API", ["<code>GET /documents/{id}/file?from=citation&page=4</code> (máy chủ ghi EVT-09 <code>citation_clicked</code>)", "410 <code>deleted</code> → không mở, hiện 'Tài liệu đã bị xóa'"]),
     ("Hành vi", ["Lớp phủ dạng dialog (<code>aria-modal</code>), Esc để đóng, focus quay lại nhãn nguồn đã bấm", "Mở đúng trang được trích dẫn; nguồn không có số trang → mở trang 1", "pdf.js tải lười khi mở lần đầu (UX-03)", "Khu vực tài liệu bên trái vẫn nhìn thấy để giữ ngữ cảnh"]),
     ("Chưa có trong thiết kế", ["Tô sáng đoạn được trích dẫn: API hiện chỉ trả số trang, không trả vị trí đoạn"])])

# --------------------------------------------------------------------------- S07 delete confirm
dialog = f"""<div class="overlay">
  <div class="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dlg-t" aria-describedby="dlg-d">
    <h2 id="dlg-t">Xóa tài liệu?</h2>
    <p id="dlg-d"><strong style="color:var(--text)">hop-dong-A.pdf</strong> sẽ bị xóa khỏi danh sách và <strong style="color:var(--text)">không còn được dùng để trả lời câu hỏi</strong> từ bây giờ.</p>
    <div class="alert alert-info">{icon("info",16)}<div class="body">File gốc sẽ được xóa hoàn toàn khỏi hệ thống trong vòng 24 giờ. Thao tác này không thể hoàn tác.</div></div>
    <div class="foot">
      <button class="btn" type="button" autofocus>Hủy</button>
      <button class="btn btn-danger" type="button">{icon("trash",16)} Xóa tài liệu</button>
    </div>
  </div>
</div>"""
all_ready_chat = f"""<div class="thread-inner"><div class="empty" style="padding-top:64px"><span class="ill">{icon("chat",26)}</span>
  <h3>Bạn có thể bắt đầu hỏi</h3>
  <p>3 tài liệu đã Sẵn sàng. Câu trả lời có thể tổng hợp từ nhiều tài liệu.</p></div></div>"""
add("S07_delete_confirm.html", "Xác nhận xóa tài liệu", "S07",
    app(docs_panel('<ul class="list">' + "".join(DOCS_READY) + "</ul>", "3/100"),
        chat_panel(all_ready_chat, composer("ready")), extra=dialog),
    [("Story / trường hợp", ["US-010 (xác nhận trước khi xóa), US-011, E-13"]),
     ("API", ["<code>DELETE /documents/{id}</code> → 204; 404 nếu đã bị xóa ở tab khác (làm mới danh sách)"]),
     ("Hành vi", ["<code>role=alertdialog</code>, focus mặc định ở nút Hủy (thao tác an toàn)", "Sau khi xóa: ẩn dòng ngay (lạc quan), khôi phục nếu lỗi khác 404", "Xóa khi tài liệu đang xử lý → hủy xử lý"])])

# --------------------------------------------------------------------------- S08 upload limits
limit_list = f"""<div class="alert alert-danger" role="alert" style="margin-top:4px">{icon("alert",16)}<div class="body"><span class="t">Chưa có file nào được tải lên.</span><br>Mỗi lần chỉ tải tối đa <strong>10 file</strong> – bạn đã chọn 12 file. Hãy chọn lại tối đa 10 file.</div></div>
<div class="alert alert-warn" role="status" style="margin-top:8px">{icon("alert",16)}<div class="body"><span class="t">Sắp đạt giới hạn tài liệu.</span><br>Bạn còn có thể thêm <strong>2 tài liệu</strong> (98/100). Xóa tài liệu không còn dùng để có thêm chỗ.</div></div>
<div class="section-label">Tài liệu của bạn</div>
<ul class="list">{''.join(DOCS_READY)}</ul>
<p class="meta" style="text-align:center;color:var(--text-muted);font-size:var(--fs-xs)">… và 95 tài liệu khác (cuộn để xem)</p>"""
add("S08_upload_limits.html", "Màn hình chính – vượt giới hạn tải lên", "S08",
    app(docs_panel(limit_list, "98/100", quota_near=True), chat_panel(all_ready_chat, composer("ready"))),
    [("Story / trường hợp", ["US-002 (N+1 file → không tải file nào), I-01 (hạn mức 100), US-004 (quá dung lượng/số trang – hiển thị trên dòng file như S02)", "E-08"]),
     ("API", ["422 <code>too_many_files</code>; 422 <code>quota_exceeded</code> kèm <code>remaining</code>", "Kiểm tra trước ở client bằng <code>/me.limits</code>; máy chủ vẫn kiểm tra lại"]),
     ("Hành vi", ["Huy hiệu hạn mức đổi sang màu cảnh báo khi còn ≤ 5 chỗ", "Thông báo lỗi nói rõ việc cần làm, không hiện mã kỹ thuật"])],
    COUNTER_JS)

# --------------------------------------------------------------------------- standalone pages
def standalone(ill_bg, ill_fg, ill_icon, title, text, actions, foot=""):
    return f"""<main class="center" id="main">
  <div class="card" role="main">
    <span class="ill" style="background:{ill_bg};color:{ill_fg}">{icon(ill_icon,30)}</span>
    <h1>{title}</h1>
    {text}
    <div class="actions">{actions}</div>
    {foot}
  </div>
</main>"""

add("S09_access_denied.html", "Chưa được cấp quyền truy cập", "S09",
    standalone("var(--warn-soft)", "var(--warn)", "shield", "Bạn chưa được cấp quyền dùng ứng dụng",
        "<p>Tài khoản <strong style=\"color:var(--text)\">minh.tran@congty.vn</strong> đã đăng nhập thành công nhưng chưa thuộc nhóm người dùng của <strong style=\"color:var(--text)\">AI Chat PDF</strong>.</p><p>Hãy liên hệ quản trị viên để được thêm vào nhóm <span class=\"ref-code\">aichat-users</span>, sau đó đăng nhập lại.</p>",
        '<a class="btn btn-primary" href="#">Đăng nhập lại</a><a class="btn" href="#">Đăng xuất khỏi tài khoản này</a>'),
    [("Story / trường hợp", ["US-023 AC 1, US-C01 (quyền qua nhóm IdP)"]),
     ("API", ["<code>GET /auth/callback</code> → 302 <code>/access-denied</code> khi không thuộc nhóm <code>aichat-users</code>/<code>aichat-admins</code>; ghi <code>login_denied</code>"]),
     ("Hành vi", ["Không hiển thị bất kỳ dữ liệu nào của ứng dụng", "Không có màn hình quản trị trong ứng dụng – quyền quản lý trên IdP"])])

add("S10_login_error.html", "Lỗi đăng nhập", "S10",
    standalone("var(--danger-soft)", "var(--danger)", "alert", "Không thể đăng nhập",
        "<p>Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Điều này có thể xảy ra nếu bạn mở trang đăng nhập quá lâu hoặc ở nhiều tab.</p>",
        '<a class="btn btn-primary" href="#">Thử đăng nhập lại</a>',
        '<p style="margin-top:20px;font-size:var(--fs-xs)">Nếu lỗi lặp lại, gửi mã tham chiếu này cho bộ phận hỗ trợ: <span class="ref-code">2b7f0d1e-9a43-4f7e-9d0a-1c1a2f3b4c5d</span></p>'),
    [("Story / trường hợp", ["US-023"]),
     ("API", ["<code>GET /auth/callback</code> lỗi state/nonce → 302 <code>/login-error</code>"]),
     ("Hành vi", ["Hiển thị <code>request_id</code> làm mã tham chiếu, không hiển thị chi tiết kỹ thuật"])])

add("S11_session_expired.html", "Phiên làm việc đã hết hạn", "S11",
    standalone("var(--info-soft)", "var(--info)", "clock", "Phiên làm việc đã hết hạn",
        "<p>Để bảo vệ tài liệu, bạn cần đăng nhập lại. Đang chuyển tới trang đăng nhập…</p>"
        "<div class=\"alert alert-info\" style=\"text-align:left;margin-top:12px\">" + icon("info",16) + "<div class=\"body\">Câu hỏi bạn đang soạn đã được lưu và sẽ hiện lại sau khi đăng nhập. Lịch sử hội thoại của phiên trước không được giữ lại.</div></div>"
        "<p style=\"margin-top:16px\"><span class=\"spin\" style=\"color:var(--primary)\" aria-hidden=\"true\"></span> Tự chuyển sau <strong id=\"cd\">5</strong> giây</p>",
        '<a class="btn btn-primary" href="#">Đăng nhập ngay</a>'),
    [("Story / trường hợp", ["US-023 AC 2, E-17, NFR-024"]),
     ("API", ["Bất kỳ request nào trả 401 <code>session_expired</code> → <code>useSessionGuard</code> lưu nháp vào <code>sessionStorage</code> rồi chuyển <code>/api/v1/auth/login?return_to=/</code>"]),
     ("Hành vi", ["Nói rõ điều gì được giữ (nháp câu hỏi) và điều gì không (hội thoại cũ)", "Đếm ngược có thể bỏ qua bằng nút 'Đăng nhập ngay'"])],
    "let n=5;const el=document.getElementById('cd');const t=setInterval(()=>{n=Math.max(0,n-1);el.textContent=n;if(!n)clearInterval(t)},1000);")

# --------------------------------------------------------------------------- index
rows = "".join(
    f'<li class="row" style="grid-template-columns:56px 1fr auto"><span class="badge" style="background:var(--primary-soft);color:var(--primary);justify-content:center">{sid}</span>'
    f'<div><a class="name" style="color:var(--text)" href="{f}">{html.escape(t)}</a><div class="meta">{spec[0][1][0]}</div></div>'
    f'<a class="btn" href="{f}">Mở</a></li>' for f, sid, t, spec in SCREENS)
index_body = f"""<main id="main" style="max-width:960px;margin:0 auto;padding:40px 24px">
  <div class="brand" style="font-size:var(--fs-2xl)"><span class="brand-mark">{icon("chat",16)}</span>AI Chat PDF – Thiết kế màn hình</div>
  <p style="color:var(--text-muted)">MVP · bám theo BLUEPRINT v0.3 (UX-01…UX-10, DE-01…DE-03), API_DESIGN v0.1, PRD v0.2 mục 4. Mỗi file là một màn hình hoàn chỉnh, không phụ thuộc tài nguyên ngoài.
  Mỗi màn hình có nút <strong>Ghi chú thiết kế</strong> ở mép phải màn hình (story, API, hành vi) – phần này chỉ dành cho người đọc thiết kế, không thuộc giao diện sản phẩm. Thiết kế cho máy tính ≥ 1280 px, hỗ trợ giao diện sáng/tối theo hệ điều hành.</p>
  <ul class="list">{rows}</ul>
</main>"""
io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n").write(
    page("Danh sách màn hình", index_body, "INDEX", [("Ghi chú", ["Trang mục lục, không phải màn hình của sản phẩm"])]))
print("screens:", len(SCREENS))
