import path from 'node:path'
import { expect, test } from '../evidence/fixture'
import { BACKEND, py } from './_h'

test('Hợp đồng API so với openapi.yaml', async ({ ev, page }) => {
  await ev.step('Mở http://localhost:8080/api/v1/docs (chế độ dev) và chụp', 'Trang tài liệu API tải được (HTTP 200)', async () => {
    const resp = await page.goto('/api/v1/docs')
    expect(resp!.status()).toBe(200)
    await page.waitForTimeout(3000)
    return 'HTTP 200 (giao diện Swagger tải thư viện từ CDN; có thể trống nếu chính sách CSP chặn – không ảnh hưởng hợp đồng API)'
  })
  await ev.step('GET /api/v1/openapi.json và so sánh path/method với app/contracts/openapi.yaml', 'Không thiếu thao tác nào (15/15)', async () => {
    const r = await ev.api('GET', '/api/v1/openapi.json', { csrf: false })
    expect(r.status).toBe(200)
    const live = Object.entries((r.body as { paths: Record<string, object> }).paths).flatMap(([p, ops]) =>
      Object.keys(ops).filter((m) => ['get', 'post', 'put', 'delete'].includes(m)).map((m) => `${m.toUpperCase()} ${p}`),
    )
    const yaml = path.join(BACKEND, '..', 'contracts', 'openapi.yaml')
    const expected: string[] = JSON.parse(
      py(['-c', `import yaml,json;s=yaml.safe_load(open(r'${yaml}',encoding='utf-8'));print(json.dumps([m.upper()+' '+p for p,i in s['paths'].items() for m in i if m in('get','post','put','delete')]))`]),
    )
    const have = new Set(live.flatMap((o) => [o, o.replace(' /api/v1', ' ')]))
    const missing = expected.filter((e) => !have.has(e) && !have.has(e.replace(' /', ' /api/v1/').replace('/api/v1//', '/api/v1/')))
    expect(expected).toHaveLength(15)
    expect(missing).toEqual([])
    return `Hợp đồng: ${expected.length} thao tác; ứng dụng: ${live.length} thao tác; thiếu: ${missing.length}`
  })
})
