// Tổng hợp kết quả mọi test case thành test_reports/README.md (+ summary.json).
//   node evidence/summary.ts
import fs from 'node:fs'
import path from 'node:path'
import { REPORTS_ROOT } from './report.ts'

interface Result {
  id: string
  title: string
  folder: string
  verdict: string
  startedAt: string
  finishedAt: string
  steps: { status: string; screenshots: string[] }[]
  videos: string[]
  notes?: string[]
}

const TESTCASES = path.join(REPORTS_ROOT, '..', 'doc', '07-verification', 'test_cases')
const expected = fs.existsSync(TESTCASES) ? fs.readdirSync(TESTCASES).filter((f) => /^[A-Z0-9]+-\d+_.*\.md$/.test(f)).map((f) => f.replace(/\.md$/, '')) : []
const rows: (Result & { missing?: boolean })[] = []
for (const folder of expected) {
  const file = path.join(REPORTS_ROOT, folder, 'result.json')
  if (!fs.existsSync(file)) {
    rows.push({ id: folder.split('_')[0], title: folder, folder, verdict: 'CHƯA CHẠY', startedAt: '', finishedAt: '', steps: [], videos: [], missing: true })
    continue
  }
  rows.push(JSON.parse(fs.readFileSync(file, 'utf8')) as Result)
}
const order = ['UT', 'INT', 'API', 'E2E', 'SEC', 'ACC', 'UI', 'PERF', 'QLT', 'UAT']
rows.sort((a, b) => order.indexOf(a.id.split('-')[0]) - order.indexOf(b.id.split('-')[0]) || a.id.localeCompare(b.id, 'en', { numeric: true }))
const count: Record<string, number> = {}
for (const r of rows) count[r.verdict] = (count[r.verdict] ?? 0) + 1
const mb = (f: string) => {
  try {
    return (fs.statSync(f).size / 1024 / 1024).toFixed(1)
  } catch {
    return '0'
  }
}
const lines = [
  '# Kết quả thực thi test case',
  '',
  `Tạo lúc ${new Date().toISOString()} bằng \`app/frontend/evidence/summary.ts\`. Mỗi test case có thư mục riêng \`test_reports/<tên test case>/\` gồm \`report.md\`, \`result.json\`, \`screenshots/\`, \`video/\`, \`logs/\`. Ứng dụng được kiểm thử tại **http://localhost:8080/**.`,
  '',
  '## Tổng hợp',
  '',
  '| Kết luận | Số test case |',
  '|---|---|',
  ...Object.entries(count).map(([k, v]) => `| ${k} | ${v} |`),
  `| **Tổng** | **${rows.length}** |`,
  '',
  '## Chi tiết',
  '',
  '| ID | Tiêu đề | Kết luận | Bước (đạt/tổng) | Ảnh | Video (MB) | Report |',
  '|---|---|---|---|---|---|---|',
  ...rows.map((r) => {
    const ok = r.steps.filter((s) => s.status === 'Đạt').length
    const shots = r.steps.reduce((n, s) => n + s.screenshots.length, 0)
    const vids = r.videos.map((v) => mb(path.join(REPORTS_ROOT, r.folder, v))).join(' + ') || '–'
    const link = r.missing ? '–' : `[report](${r.folder}/report.md)`
    return `| ${r.id} | ${r.title.replace(/\|/g, '\\|')} | ${r.verdict} | ${ok}/${r.steps.length} | ${shots} | ${vids} | ${link} |`
  }),
  '',
]
fs.writeFileSync(path.join(REPORTS_ROOT, 'README.md'), lines.join('\n'), 'utf8')
fs.writeFileSync(path.join(REPORTS_ROOT, 'summary.json'), JSON.stringify({ count, total: rows.length, rows: rows.map((r) => ({ id: r.id, verdict: r.verdict, folder: r.folder })) }, null, 2), 'utf8')
console.log(JSON.stringify(count))
