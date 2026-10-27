import { expect, test } from '../evidence/fixture'
import { bodyOf, file, prep, putFiles } from './_h'

test('Từ chối file không hợp lệ', async ({ ev }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  const names = ['qua-nhieu-trang.pdf', 'hop-dong-mat-khau.pdf', 'hong.pdf', 'bao-gia.docx', 'gia-mao.pdf', 'ho-so-scan-2019.pdf']
  const all = names.map(file)
  const { batch } = await ev.api('POST', '/api/v1/upload-batches', {
    json: { files: all.map((f) => ({ name: f.name, size_bytes: f.buffer.length })) },
  }).then((b) => ({ batch: bodyOf(b).batch_id as string }))
  const one = async (i: number) => (await putFiles(ev, [all[i]], batch)).results[0]
  await ev.step('PUT qua-nhieu-trang.pdf (301 trang)', '422 too_many_pages; detail nêu tên file và giới hạn', async () => {
    const r = await one(0)
    expect(r.status).toBe(422)
    expect(bodyOf(r).code).toBe('too_many_pages')
    expect(String(bodyOf(r).detail)).toContain('qua-nhieu-trang.pdf')
  })
  await ev.step('PUT hop-dong-mat-khau.pdf', '422 encrypted; "… được bảo vệ bằng mật khẩu."', async () => {
    const r = await one(1)
    expect(r.status).toBe(422)
    expect(bodyOf(r).code).toBe('encrypted')
    expect(String(bodyOf(r).detail)).toContain('mật khẩu')
  })
  await ev.step('PUT hong.pdf, bao-gia.docx, gia-mao.pdf', 'Mỗi file 422 not_pdf, application/problem+json', async () => {
    for (const i of [2, 3, 4]) {
      const r = await one(i)
      expect(r.status).toBe(422)
      expect(bodyOf(r).code).toBe('not_pdf')
      expect(r.headers['content-type']).toContain('application/problem+json')
    }
  })
  let scanId = ''
  await ev.step('PUT ho-so-scan-2019.pdf', '201 PROCESSING', async () => {
    const r = await one(5)
    expect(r.status).toBe(201)
    scanId = bodyOf(r).id as string
  })
  await ev.step('Chờ xử lý; GET /documents', 'Chỉ có ho-so-scan-2019.pdf: FAILED R-03, retryable=false; file bị từ chối không xuất hiện', async () => {
    await expect
      .poll(async () => {
        const r = await ev.api('GET', '/api/v1/documents')
        return (bodyOf(r).items as { id: string; status: string }[]).find((d) => d.id === scanId)?.status
      }, { timeout: 60_000 })
      .toBe('FAILED')
    const items = bodyOf(await ev.api('GET', '/api/v1/documents')).items as Record<string, unknown>[]
    expect(items).toHaveLength(1)
    expect(items[0]).toMatchObject({ failure_code: 'R-03', retryable: false })
  })
  ev.note('DEF-T-002: PDF hỏng/có mật khẩu bị từ chối 422 ngay lúc tải lên (theo thiết kế), PRD yêu cầu "Thất bại" R-01/R-02 – chờ PO quyết định.')
})
