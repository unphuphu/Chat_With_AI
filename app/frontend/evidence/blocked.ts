// Ghi report cho test case KHÔNG thể thực thi ở môi trường hiện tại (thiếu staging, bộ câu hỏi, công cụ…).
// Vẫn tạo đủ artifact: ảnh chụp trang nêu lý do + điều kiện cần, video, report.md (kết luận BỊ CHẶN).
//   node evidence/blocked.ts --tc <tên test case> --title "<tiêu đề>" --reason "<lý do>" --need "<việc cần để chạy>"
import { chromium } from '@playwright/test'
import path from 'node:path'
import { caseDir, writeReport } from './report.ts'

const o: Record<string, string> = {}
const a = process.argv.slice(2)
for (let i = 0; i < a.length; i += 2) o[a[i].replace(/^--/, '')] = a[i + 1]
if (!o.tc || !o.reason) throw new Error('Cách dùng: --tc <tên> --title <tiêu đề> --reason <lý do> --need <điều kiện>')
const id = o.tc.split('_')[0]
const dir = caseDir(o.tc)
const startedAt = new Date()
const esc = (s: string) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]!)

const browser = await chromium.launch({ channel: 'msedge' })
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: path.join(dir, 'video'), size: { width: 1280, height: 720 } } })
const page = await ctx.newPage()
await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#11151b;color:#e6eaf0;font:16px/1.6 Segoe UI,sans-serif}
header{background:#7f5300;color:#fff;padding:14px 24px;font-weight:700;font-size:18px}
main{padding:24px}h2{font-size:15px;color:#e8b44c;margin:18px 0 4px}p{margin:0}
.tag{display:inline-block;background:#33280f;color:#e8b44c;border-radius:999px;padding:2px 12px;font-weight:700}</style></head>
<body><header>${esc(id)} – ${esc(o.title ?? '')}</header><main>
<p><span class="tag">BỊ CHẶN</span> Test case chưa thực thi được trên môi trường hiện tại (http://localhost:8080/)</p>
<h2>Lý do</h2><p>${esc(o.reason)}</p>
<h2>Cần gì để chạy</h2><p>${esc(o.need ?? '')}</p>
<h2>Hướng dẫn thực thi</h2><p>Xem doc/07-verification/test_cases/${esc(o.tc)}.md</p></main></body></html>`)
await page.waitForTimeout(2500)
const shot = path.join(dir, 'screenshots', '01-ly-do-bi-chan.png')
await page.screenshot({ path: shot })
const video = page.video()!
await page.close()
const videoFile = path.join(dir, 'video', `${id}-blocked.webm`)
await video.saveAs(videoFile)
await video.delete().catch(() => undefined)
await ctx.close()
await browser.close()
const verdict = writeReport(dir, {
  id, title: o.title ?? '', folder: o.tc, mode: 'Không thực thi – bị chặn (evidence/blocked.ts)', startedAt, finishedAt: new Date(),
  steps: [{ n: 1, title: 'Kiểm tra điều kiện thực thi', expected: o.need ?? 'Đủ điều kiện', actual: o.reason, status: 'Bị chặn', screenshots: [shot] }],
  videos: [videoFile], logs: [], notes: [`Bị chặn: ${o.reason}`, `Cần: ${o.need ?? ''}`],
})
console.log(`[evidence] ${id}: ${verdict}`)
