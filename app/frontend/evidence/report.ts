// Ghi test report (report.md + result.json) cho một test case vào ./test_reports/<tên test case>/.
// Dùng chung cho fixture Playwright (fixture.ts) và bộ quay dòng lệnh (record-cli.ts).
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

export type StepStatus = 'Đạt' | 'Không đạt' | 'Cần người xác nhận' | 'Bị chặn'
export interface StepRecord {
  n: number
  title: string
  expected: string
  actual: string
  status: StepStatus
  screenshots: string[]
}
export interface RunRecord {
  id: string
  title: string
  folder: string
  mode: string
  startedAt: Date
  finishedAt: Date
  steps: StepRecord[]
  videos: string[]
  logs: string[]
  notes?: string[]
  env?: Record<string, string>
}

/** Thư mục gốc repo: đi ngược từ thư mục hiện tại tới nơi có cả app/ và doc/. */
function findRepoRoot(start: string): string {
  let dir = path.resolve(start)
  for (;;) {
    if (fs.existsSync(path.join(dir, 'app')) && fs.existsSync(path.join(dir, 'doc'))) return dir
    const parent = path.dirname(dir)
    if (parent === dir) throw new Error(`Không tìm thấy thư mục gốc repo từ ${start}`)
    dir = parent
  }
}

export const REPO_ROOT = findRepoRoot(process.cwd())
export const REPORTS_ROOT = path.join(REPO_ROOT, 'test_reports')
export const APP_URL = process.env.APP_URL ?? 'http://localhost:8080/'

/**
 * Thư mục artifact của test case, tạo sẵn các thư mục con. Nếu đã có kết quả lần chạy trước thì chuyển nó vào
 * test_reports/_archive/<tên test case>__<thời điểm>/ để thư mục chính luôn là lần chạy mới nhất.
 */
const prepared = new Set<string>()
export function caseDir(folder: string): string {
  const dir = path.join(REPORTS_ROOT, folder)
  if (!prepared.has(folder) && fs.existsSync(path.join(dir, 'report.md'))) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-')
    const archive = path.join(REPORTS_ROOT, '_archive', `${folder}__${stamp}`)
    fs.mkdirSync(path.dirname(archive), { recursive: true })
    fs.renameSync(dir, archive)
  }
  prepared.add(folder)
  for (const sub of ['screenshots', 'video', 'logs']) fs.mkdirSync(path.join(dir, sub), { recursive: true })
  return dir
}

export function buildId(): string {
  try {
    const sha = execSync('git rev-parse --short HEAD', { cwd: REPO_ROOT }).toString().trim()
    const dirty = execSync('git status --porcelain -- app', { cwd: REPO_ROOT }).toString().trim()
    return dirty ? `${sha} + thay đổi chưa commit trong app/` : sha
  } catch {
    return 'không xác định (không có git)'
  }
}

const rel = (dir: string, p: string) => path.relative(dir, p).split(path.sep).join('/')
const esc = (s: unknown) => String(s ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, '<br>')

export function writeReport(dir: string, r: RunRecord): string {
  const failed = r.steps.filter((s) => s.status === 'Không đạt').length
  const review = r.steps.filter((s) => s.status === 'Cần người xác nhận').length
  const blocked = r.steps.filter((s) => s.status === 'Bị chặn').length
  const verdict = failed ? 'KHÔNG ĐẠT' : blocked ? 'BỊ CHẶN' : review ? 'CẦN NGƯỜI XÁC NHẬN' : r.steps.length ? 'ĐẠT' : 'KHÔNG CÓ BƯỚC NÀO'
  const secs = ((r.finishedAt.getTime() - r.startedAt.getTime()) / 1000).toFixed(1)
  const env: Record<string, string> = {
    'URL ứng dụng': APP_URL,
    'Bản build': buildId(),
    'Trình duyệt': 'Microsoft Edge (Playwright, channel msedge)',
    'Hệ điều hành': `${process.platform} ${process.arch}`,
    ...(r.env ?? {}),
  }
  const lines = [
    `# Test report – ${r.id}: ${r.title}`,
    '',
    '| Trường | Giá trị |',
    '|---|---|',
    `| Test case | [${r.id}](../../doc/07-verification/test_cases/${r.folder}.md) |`,
    `| Kết luận | **${verdict}** |`,
    `| Bắt đầu | ${r.startedAt.toISOString()} |`,
    `| Kết thúc | ${r.finishedAt.toISOString()} (${secs} s) |`,
    `| Cách thực hiện | ${r.mode} |`,
    ...Object.entries(env).map(([k, v]) => `| ${k} | ${esc(v)} |`),
    '',
    '## Kết quả từng bước',
    '',
    '| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |',
    '|---|---|---|---|---|---|',
    ...r.steps.map(
      (s) =>
        `| ${s.n} | ${esc(s.title)} | ${esc(s.expected)} | ${esc(s.actual)} | ${s.status} | ` +
        `${s.screenshots.map((p) => `[ảnh](${rel(dir, p)})`).join(' ')} |`,
    ),
    '',
    '## Video',
    '',
    ...(r.videos.length ? r.videos.map((v) => `- [${path.basename(v)}](${rel(dir, v)})`) : ['- (không có)']),
    '',
    '## Ảnh chụp màn hình',
    '',
    ...r.steps.flatMap((s) => s.screenshots.map((p) => `![Bước ${s.n} – ${s.title}](${rel(dir, p)})`)),
    '',
    '## Log',
    '',
    ...(r.logs.length ? r.logs.map((l) => `- [${path.basename(l)}](${rel(dir, l)})`) : ['- (không có)']),
    '',
    '## Ghi chú / lỗi phát hiện',
    '',
    ...(r.notes?.length ? r.notes.map((n) => `- ${n}`) : ['- (không có)']),
    '',
  ]
  fs.writeFileSync(path.join(dir, 'report.md'), lines.join('\n'), 'utf8')
  fs.writeFileSync(
    path.join(dir, 'result.json'),
    JSON.stringify({ ...r, verdict, env, steps: r.steps.map((s) => ({ ...s, screenshots: s.screenshots.map((p) => rel(dir, p)) })), videos: r.videos.map((v) => rel(dir, v)), logs: r.logs.map((l) => rel(dir, l)) }, null, 2),
    'utf8',
  )
  return verdict
}
