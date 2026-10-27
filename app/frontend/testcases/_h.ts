// Hàm trợ giúp dùng chung cho các spec test case (không phải spec).
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { expect, type Page } from '@playwright/test'
import type { Evidence } from '../evidence/fixture'

export const SAMPLES = path.resolve(process.cwd(), '../sample-pdfs')
export const BACKEND = path.resolve(process.cwd(), '../backend')
export const pdf = (name: string) => path.join(SAMPLES, name)
export const Q_PAY = 'Bên B thanh toán trong vòng bao nhiêu ngày?'
export const Q_OUT = 'Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?'

type Json = Record<string, unknown>

async function csrf(page: Page): Promise<string> {
  const c = (await page.context().cookies()).find((x) => x.name === 'csrf_token')
  return c?.value ?? ''
}

/** Gọi API không ghi vào console bằng chứng (dùng để chuẩn bị dữ liệu). */
export async function quiet(page: Page, method: 'GET' | 'POST' | 'PUT' | 'DELETE', url: string, data?: unknown) {
  const resp = await page.request.fetch(url, { method, data, headers: { 'X-CSRF-Token': await csrf(page) } })
  const ct = resp.headers()['content-type'] ?? ''
  return { status: resp.status(), body: (ct.includes('json') ? await resp.json() : null) as Json }
}

/** Xóa mọi tài liệu của người dùng hiện tại (chuẩn bị dữ liệu). */
export async function purge(page: Page) {
  const r = await quiet(page, 'GET', '/api/v1/documents')
  for (const d of (r.body.items as { id: string }[]) ?? []) await quiet(page, 'DELETE', `/api/v1/documents/${d.id}`)
  await page.reload()
  await page.locator('.docs .empty').first().waitFor()
}

export async function upload(page: Page, ...files: (string | { name: string; mimeType: string; buffer: Buffer })[]) {
  await page.locator('input[type=file]').setInputFiles(files.map((f) => (typeof f === 'string' ? pdf(f) : f)) as never)
}

export function row(page: Page, name: string) {
  return page.locator('li.row', { hasText: name })
}

export async function waitReady(page: Page, name: string, timeout = 90_000) {
  await expect(row(page, name).getByText('Sẵn sàng')).toBeVisible({ timeout })
}

/** Đăng nhập, xóa tài liệu cũ, tải các file và chờ Sẵn sàng. */
export async function prep(ev: Evidence, user: 'p1' | 'p2' | 'admin' = 'p2', files: string[] = []) {
  await ev.login(user)
  await purge(ev.page)
  for (const f of files) {
    await upload(ev.page, f)
    await waitReady(ev.page, f)
  }
}

/** Hỏi trên giao diện và chờ câu trả lời; trả về phần tử câu trả lời mới nhất. */
export async function ask(page: Page, question: string) {
  const n = await page.locator('article.a').count()
  await page.locator('#q').fill(question)
  await page.keyboard.press('Enter')
  await expect(page.locator('article.a')).toHaveCount(n + 1, { timeout: 30_000 })
  const a = page.locator('article.a').last()
  await expect(a).not.toHaveAttribute('aria-busy', 'true', { timeout: 30_000 })
  return a
}

export async function conversationId(ev: Evidence): Promise<string> {
  const r = await ev.api('GET', '/api/v1/conversations/current')
  return (r.body as { id: string }).id
}

export function newCrid() {
  return crypto.randomUUID()
}

export const ask$ = (ev: Evidence, conv: string, question: string, crid = newCrid()) =>
  ev.api('POST', `/api/v1/conversations/${conv}/messages`, { json: { client_request_id: crid, question } })

/** Tạo lô rồi PUT từng file; trả danh sách phản hồi. */
export async function putFiles(ev: Evidence, files: { name: string; buffer: Buffer; cid?: string }[], batchId?: string) {
  let batch = batchId
  if (!batch) {
    const b = await ev.api('POST', '/api/v1/upload-batches', {
      json: { files: files.map((f) => ({ name: f.name, size_bytes: f.buffer.length })) },
    })
    if (b.status !== 201) return { batch: '', results: [b] }
    batch = (b.body as { batch_id: string }).batch_id
  }
  const results = []
  for (const f of files) {
    results.push(
      await ev.api('PUT', `/api/v1/upload-batches/${batch}/files/${f.cid ?? crypto.randomUUID()}`, {
        multipart: { file: { name: f.name, mimeType: 'application/pdf', buffer: f.buffer } },
      }),
    )
  }
  return { batch, results }
}

export const file = (name: string) => ({ name, buffer: fs.readFileSync(pdf(name)) })

/** Chạy lệnh Python trong backend, trả stdout (dùng để đối chiếu với pytest/yaml). */
export function py(args: string[]): string {
  return execFileSync(path.join(BACKEND, '.venv/Scripts/python.exe'), args, {
    cwd: BACKEND,
    encoding: 'utf8',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
  })
}

export const bodyOf = (r: { body: unknown }) => r.body as Json
