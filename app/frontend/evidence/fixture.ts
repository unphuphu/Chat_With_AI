// Fixture Playwright thu bằng chứng cho test case (doc/07-verification/test_cases/*.md).
// Spec đặt tại app/frontend/testcases/<tên test case>.spec.ts; artifact ghi vào ./test_reports/<tên test case>/.
import { test as base, expect, type APIResponse, type Page } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { APP_URL, caseDir, REPO_ROOT, type StepRecord, writeReport } from './report'

const USERS = {
  p1: /Nguyễn Lan/,
  p2: /Trần Minh/,
  admin: /Quản trị viên/,
  outsider: /Người ngoài nhóm/,
} as const

const CONSOLE_HTML = `<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>API evidence</title>
<style>body{font:13px Consolas,monospace;background:#11151b;color:#e6eaf0;margin:0;padding:16px}
h1{font:600 16px Segoe UI,sans-serif;margin:0 0 12px}.e{border:1px solid #2f3946;border-radius:8px;margin:0 0 10px;padding:10px}
.r{color:#8db6f5}.ok{color:#5cc48a}.bad{color:#f08a80}pre{white-space:pre-wrap;margin:6px 0 0;max-height:260px;overflow:auto}</style>
</head><body><h1 id="t"></h1><div id="log"></div></body></html>`

export class Evidence {
  readonly dir: string
  readonly folder: string
  readonly id: string
  private steps: StepRecord[] = []
  private notes: string[] = []
  private logs = new Set<string>()
  private consolePage: Page | null = null
  private apiInStep = false
  private shotNo = 0
  readonly startedAt = new Date()
  readonly page: Page
  readonly title: string

  constructor(page: Page, folder: string, title: string) {
    this.page = page
    this.title = title
    this.folder = folder
    this.id = folder.split('_')[0]
    this.dir = caseDir(folder)
  }

  private current(): StepRecord {
    return this.steps[this.steps.length - 1]
  }

  /** Chụp ảnh trang (mặc định: trang ứng dụng) và gắn vào bước hiện tại. */
  async shot(name: string, page: Page = this.page): Promise<string> {
    this.shotNo += 1
    const file = path.join(this.dir, 'screenshots', `${String(this.shotNo).padStart(2, '0')}-${slug(name)}.png`)
    await page.screenshot({ path: file, fullPage: false })
    this.current()?.screenshots.push(file)
    return file
  }

  /**
   * Một bước của test case. Luôn chụp ảnh sau bước (kể cả khi lỗi).
   * `review: true` = bước cần người đánh giá (so sánh trực quan, trình đọc màn hình…).
   */
  async step(title: string, expected: string, fn: () => Promise<string | void>, opts: { review?: boolean } = {}) {
    const rec: StepRecord = { n: this.steps.length + 1, title, expected, actual: 'Bước không hoàn tất (test bị ngắt hoặc hết thời gian)', status: 'Không đạt', screenshots: [] }
    this.steps.push(rec)
    this.apiInStep = false
    try {
      rec.actual = (await fn()) || 'Như mong đợi'
      rec.status = 'Đạt'
      if (opts.review) rec.status = 'Cần người xác nhận'
      // Quy ước: hàm trả về chuỗi bắt đầu bằng 'BỊ CHẶN:' khi bước không thể thực hiện ở môi trường này
      if (rec.actual.startsWith('BỊ CHẶN:')) rec.status = 'Bị chặn'
    } catch (e) {
      rec.status = 'Không đạt'
      rec.actual = (e as Error).message.split('\n').slice(0, 6).join(' ')
      throw e
    } finally {
      // Bước có gọi API → chụp trang console API; ngược lại chụp trang ứng dụng
      const target = this.apiInStep && this.consolePage ? this.consolePage : this.page
      if (!target.isClosed()) await this.shot(title, target).catch(() => undefined)
    }
  }

  note(text: string) {
    this.notes.push(text)
  }

  /**
   * Khởi động lại ứng dụng với biến môi trường riêng (vd. LLM_PROVIDER, SESSION_IDLE_MIN) qua evidence/app.ts.
   * Gọi `restartApp()` không tham số ở cuối test để trả ứng dụng về cấu hình mặc định.
   */
  async restartApp(env: Record<string, string> = {}) {
    const args = ['evidence/app.ts', 'restart', ...Object.entries(env).map(([k, v]) => `${k}=${v}`)]
    const out = execFileSync(process.execPath, args, { cwd: path.join(REPO_ROOT, 'app', 'frontend'), encoding: 'utf8' })
    this.note(`Khởi động lại ứng dụng với ${JSON.stringify(env)}: ${out.trim()}`)
    if (!this.page.isClosed()) {
      await this.page.goto('/').catch(() => undefined)
      await this.page.locator('.docs, .card').first().waitFor({ timeout: 30_000 }).catch(() => undefined) // SPA nạp xong (không dùng networkidle: SSE giữ kết nối mở)
    }
  }

  /** Đăng nhập qua IdP giả lập bằng tài khoản mẫu. */
  async login(user: keyof typeof USERS) {
    await this.page.goto('/')
    await this.page.getByRole('button', { name: USERS[user] }).first().click()
    if (user === 'outsider') {
      await expect(this.page.getByRole('heading', { name: /chưa được cấp quyền/ })).toBeVisible()
    } else {
      await this.page.locator('.docs .empty, .docs li.row').first().waitFor()
    }
  }

  /** Gọi API qua cùng origin (http://localhost:8080/api/v1/…) với cookie phiên của trình duyệt; ghi log + hiển thị để quay video. */
  async api(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    opts: { json?: unknown; multipart?: Record<string, unknown>; csrf?: boolean; headers?: Record<string, string> } = {},
  ): Promise<{ status: number; headers: Record<string, string>; body: unknown; raw: APIResponse }> {
    const cookies = await this.page.context().cookies()
    const csrf = cookies.find((c) => c.name === 'csrf_token')?.value ?? ''
    const headers = { ...(opts.csrf === false ? {} : { 'X-CSRF-Token': csrf }), ...(opts.headers ?? {}) }
    const resp = await this.page.request.fetch(url, { method, headers, data: opts.json, multipart: opts.multipart as never })
    let body: unknown = null
    const ctype = resp.headers()['content-type'] ?? ''
    if (ctype.includes('json')) body = await resp.json()
    else if (ctype.startsWith('text/')) body = (await resp.text()).slice(0, 2000)
    else body = `<${ctype || 'binary'}, ${(await resp.body()).length} byte>`
    const entry = { at: new Date().toISOString(), method, url, request: opts.json ?? (opts.multipart ? Object.keys(opts.multipart) : null), status: resp.status(), headers: resp.headers(), body }
    const log = path.join(this.dir, 'logs', 'api.log')
    fs.appendFileSync(log, JSON.stringify(entry) + '\n', 'utf8')
    this.logs.add(log)
    this.apiInStep = true
    await this.showApi(entry)
    return { status: resp.status(), headers: resp.headers(), body, raw: resp }
  }

  private async showApi(entry: { method: string; url: string; status: number; request: unknown; body: unknown }) {
    if (!this.consolePage) {
      this.consolePage = await this.page.context().newPage()
      await this.consolePage.setContent(CONSOLE_HTML)
      await this.consolePage.evaluate((t) => (document.getElementById('t')!.textContent = t), `${this.id} – ${this.title}`)
    }
    await this.consolePage.evaluate((e) => {
      const div = document.createElement('div')
      div.className = 'e'
      const cls = e.status < 400 ? 'ok' : 'bad'
      div.innerHTML = `<span class="r"></span> <b class="${cls}"></b><pre></pre>`
      div.querySelector('.r')!.textContent = `${e.method} ${e.url}`
      div.querySelector('b')!.textContent = String(e.status)
      div.querySelector('pre')!.textContent =
        (e.request ? `request: ${JSON.stringify(e.request)}\n` : '') + `response: ${JSON.stringify(e.body, null, 2)}`
      document.getElementById('log')!.appendChild(div)
      div.scrollIntoView()
    }, entry)
  }

  /** Lưu video của mọi trang trong context và ghi report. Gọi tự động khi test kết thúc. */
  async finish() {
    const videos: string[] = []
    const pages = this.page.context().pages()
    for (const [i, p] of pages.entries()) {
      const v = p.video()
      if (!p.isClosed()) await p.close()
      if (v) {
        const file = path.join(this.dir, 'video', `${this.id}-${i === 0 ? 'app' : `page${i + 1}`}.webm`)
        await v.saveAs(file)
        await v.delete().catch(() => undefined)
        videos.push(file)
      }
    }
    return writeReport(this.dir, {
      id: this.id,
      title: this.title,
      folder: this.folder,
      mode: 'Tự động – Playwright (app/frontend/evidence/fixture.ts)',
      startedAt: this.startedAt,
      finishedAt: new Date(),
      steps: this.steps,
      videos,
      logs: [...this.logs],
      notes: this.notes,
      env: { 'Spec': `app/frontend/testcases/${this.folder}.spec.ts` },
    })
  }
}

function slug(s: string) {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/gi, 'd')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 50)
}

export const test = base.extend<{ ev: Evidence }>({
  ev: async ({ page }, use, testInfo) => {
    const folder = path.basename(testInfo.file).replace(/\.spec\.ts$/, '')
    const ev = new Evidence(page, folder, testInfo.title)
    await use(ev)
    const verdict = await ev.finish()
    testInfo.annotations.push({ type: 'verdict', description: verdict })
  },
})

export { APP_URL, expect }
