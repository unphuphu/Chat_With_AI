import fs from 'node:fs'
import { expect, test } from '../evidence/fixture'
import { bodyOf, file, pdf, prep, putFiles } from './_h'

test('Kiểm tra file tải lên an toàn', async ({ ev }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  await ev.step('PUT gia-mao.pdf, hong.pdf và file ~20,5 MB', '422 cho từng file', async () => {
    const big = { name: 'lon.pdf', buffer: Buffer.concat([Buffer.from('%PDF-1.4\n'), Buffer.alloc(20 * 1024 * 1024 + 500 * 1024, 48)]) }
    for (const f of [file('gia-mao.pdf'), file('hong.pdf'), big]) {
      const { results } = await putFiles(ev, [f])
      expect(results[0].status, f.name).toBe(422)
    }
  })
  await ev.step('PUT PDF hợp lệ với tên ../../etc/passwd.pdf', '201; file_name = passwd.pdf (đã bỏ đường dẫn)', async () => {
    const { results } = await putFiles(ev, [{ name: '../../etc/passwd.pdf', buffer: fs.readFileSync(pdf('hop-dong-A.pdf')) }])
    expect(results[0].status).toBe(201)
    expect(bodyOf(results[0]).file_name).toBe('passwd.pdf')
  })
  await ev.step('Gọi GET /api/v1/readyz sau các bước trên', '200 ready – API vẫn hoạt động', async () => {
    const r = await ev.api('GET', '/api/v1/readyz', { csrf: false })
    expect(r.status).toBe(200)
  })
})
