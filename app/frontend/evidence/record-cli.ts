// Chạy một lệnh (pytest, k6, pip-audit…) và thu bằng chứng: output hiển thị trực tiếp trên trang Edge được quay video,
// ảnh chụp màn hình khi kết thúc, log đầy đủ, report.md trong ./test_reports/<tên test case>/.
//
//   node evidence/record-cli.ts --tc UT-001_chunker-property --title "Chunker property" [--cwd ../backend] -- <lệnh…>
import { chromium } from '@playwright/test'
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { caseDir, writeReport } from './report.ts'

const argv = process.argv.slice(2)
const sep = argv.indexOf('--')
if (sep < 0 || sep === argv.length - 1) {
  console.error('Cách dùng: node evidence/record-cli.ts --tc <tên test case> --title "<tiêu đề>" [--cwd <thư mục>] [--expect "<kết quả mong đợi>"] -- <lệnh>')
  process.exit(2)
}
const opts: Record<string, string> = {}
for (let i = 0; i < sep; i += 2) opts[argv[i].replace(/^--/, '')] = argv[i + 1]
const cmd = argv.slice(sep + 1)
if (!opts.tc) throw new Error('Thiếu --tc')
const folder = opts.tc
const id = folder.split('_')[0]
const dir = caseDir(folder)
const cwd = path.resolve(opts.cwd ?? '.')
const logFile = path.join(dir, 'logs', 'output.log')
const startedAt = new Date()

const browser = await chromium.launch({ channel: 'msedge' })
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, recordVideo: { dir: path.join(dir, 'video'), size: { width: 1280, height: 800 } } })
const page = await ctx.newPage()
await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#0f141a;color:#e6eaf0;font:13px/1.45 Consolas,monospace}
header{position:sticky;top:0;background:#1d5bb8;color:#fff;padding:10px 16px;font:600 15px Segoe UI,sans-serif}
header small{display:block;font:12px Consolas,monospace;opacity:.9}#out{padding:12px 16px;white-space:pre-wrap}
.err{color:#f08a80}.done{padding:10px 16px;font:600 15px Segoe UI,sans-serif}</style></head>
<body><header><span id="t"></span><small id="c"></small></header><div id="out"></div></body></html>`)
await page.evaluate(([t, c]) => {
  document.getElementById('t')!.textContent = t
  document.getElementById('c')!.textContent = c
}, [`${id} – ${opts.title ?? ''}`, `$ ${cmd.join(' ')}   (cwd: ${cwd})`])

const log = fs.createWriteStream(logFile, 'utf8')
log.write(`$ ${cmd.join(' ')}\n(cwd: ${cwd})\n\n`)
let buf: [string, boolean][] = []
const flush = async () => {
  if (!buf.length) return
  const chunk = buf
  buf = []
  await page.evaluate((lines) => {
    const out = document.getElementById('out')!
    for (const [text, isErr] of lines) {
      const span = document.createElement('span')
      if (isErr) span.className = 'err'
      span.textContent = text
      out.appendChild(span)
    }
    window.scrollTo(0, document.body.scrollHeight)
  }, chunk)
}
const timer = setInterval(() => void flush(), 300)

// Đường dẫn chương trình (vd. .venv/Scripts/python.exe) được giải theo --cwd và chạy trực tiếp; tên lệnh đơn
// (npx, k6…) chạy qua shell để Windows tìm được file .cmd
const isPath = /[\\/]/.test(cmd[0])
const exe = isPath ? path.resolve(cwd, cmd[0]) : cmd[0]
const child = spawn(exe, cmd.slice(1), {
  cwd,
  shell: !isPath && process.platform === 'win32',
  env: { ...process.env, PYTHONIOENCODING: 'utf-8', FORCE_COLOR: '0' },
})
const onData = (isErr: boolean) => (d: Buffer) => {
  const text = d.toString('utf8')
  log.write(text)
  process.stdout.write(text)
  buf.push([text.replace(/\x1b\[[0-9;]*[A-Za-z]/g, ''), isErr]) // bỏ mã màu ANSI khi hiển thị
}
child.stdout.on('data', onData(false))
child.stderr.on('data', onData(true))
const code = await new Promise<number | null>((resolve) => child.on('close', resolve))
clearInterval(timer)
await flush()
log.end()
const ok = code === 0
await page.evaluate(([ok, code]: [boolean, number | null]) => {
  const d = document.createElement('div')
  d.className = 'done'
  d.style.background = ok ? '#173023' : '#3a1c1a'
  d.textContent = ok ? `✓ Lệnh kết thúc thành công (mã ${code})` : `✗ Lệnh kết thúc với mã ${code}`
  document.body.appendChild(d)
  window.scrollTo(0, document.body.scrollHeight)
}, [ok, code] as [boolean, number | null])
await page.waitForTimeout(1500)
const shot = path.join(dir, 'screenshots', '01-ket-qua-lenh.png')
await page.screenshot({ path: shot })
const shotFull = path.join(dir, 'screenshots', '02-toan-bo-output.png')
await page.screenshot({ path: shotFull, fullPage: true })
const video = page.video()!
await page.close()
const videoFile = path.join(dir, 'video', `${id}-cli.webm`)
await video.saveAs(videoFile)
await video.delete().catch(() => undefined)
await ctx.close()
await browser.close()

const verdict = writeReport(dir, {
  id,
  title: opts.title ?? '',
  folder,
  mode: 'Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts)',
  startedAt,
  finishedAt: new Date(),
  steps: [{ n: 1, title: `Chạy: ${cmd.join(' ')}`, expected: opts.expect ?? 'Lệnh kết thúc với mã 0', actual: `Mã thoát ${code}`, status: ok ? 'Đạt' : 'Không đạt', screenshots: [shot, shotFull] }],
  videos: [videoFile],
  logs: [logFile],
  env: { 'Thư mục chạy': cwd },
})
console.log(`\n[evidence] ${id}: ${verdict} → ${dir}`)
process.exit(ok ? 0 : 1)
