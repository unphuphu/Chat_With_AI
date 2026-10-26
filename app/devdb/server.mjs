// PostgreSQL cho môi trường dev khi máy không có Docker/PostgreSQL.
// PGlite = PostgreSQL biên dịch sang WebAssembly; có pgvector; nói giao thức PostgreSQL qua TCP.
// Giới hạn: CHỈ MỘT kết nối tại một thời điểm – backend chạy chế độ một tiến trình (DEV_SINGLE_PROCESS=1).
import { PGlite } from '@electric-sql/pglite'
import { vector } from '@electric-sql/pglite/vector'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import { mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

const rawDir = process.env.DEVDB_DIR ?? '../.data/pgdata'
const inMemory = rawDir === 'memory://'
const dataDir = inMemory ? undefined : resolve(rawDir)
const port = Number(process.env.DEVDB_PORT ?? 54329)
const host = process.env.DEVDB_HOST ?? '127.0.0.1'

if (dataDir) mkdirSync(dataDir, { recursive: true })
const db = await PGlite.create({ dataDir, extensions: { vector } })
const ver = await db.query('select version() as v')
console.log(`[devdb] ${ver.rows[0].v}`)

// PGlite không gửi ParameterStatus sau khi xác thực; libpq/psycopg (bản C) cần client_encoding, DateStyle,
// TimeZone… nếu không sẽ crash khi đọc text/timestamptz. Chèn các message 'S' trước ReadyForQuery đầu tiên.
const PARAMS = {
  server_version: '17.5', server_encoding: 'UTF8', client_encoding: 'UTF8', DateStyle: 'ISO, MDY',
  IntervalStyle: 'postgres', TimeZone: 'UTC', integer_datetimes: 'on', standard_conforming_strings: 'on',
  is_superuser: 'on', session_authorization: 'postgres', application_name: '',
}
const enc = new TextEncoder()
const paramStatus = Buffer.concat(Object.entries(PARAMS).map(([k, v]) => {
  const body = Buffer.concat([enc.encode(k), Buffer.from([0]), enc.encode(v), Buffer.from([0])])
  const head = Buffer.alloc(5)
  head.write('S', 0)
  head.writeInt32BE(body.length + 4, 1)
  return Buffer.concat([head, body])
}))
const AUTH_OK = Buffer.from([0x52, 0, 0, 0, 8, 0, 0, 0, 0])
const rawExec = db.execProtocolRaw.bind(db)
db.execProtocolRaw = async (msg, opts) => {
  const out = await rawExec(msg, opts)
  const buf = Buffer.from(out)
  const z = buf.length - 6
  if (buf.indexOf(AUTH_OK) >= 0 && z >= 0 && buf[z] === 0x5a) {
    return new Uint8Array(Buffer.concat([buf.subarray(0, z), paramStatus, buf.subarray(z)]))
  }
  return out
}

const server = new PGLiteSocketServer({ db, port, host })
server.addEventListener('connection', (e) => console.log(`[devdb] client connected ${e.detail?.clientAddress ?? ''}`))
await server.start()
console.log(`[devdb] listening on postgresql://postgres@${host}:${port}/postgres (data: ${dataDir})`)

const stop = async () => {
  console.log('[devdb] shutting down')
  await server.stop()
  await db.close()
  process.exit(0)
}
// Client ngắt kết nối đột ngột (ECONNRESET) không được làm sập server
process.on('uncaughtException', (err) => console.error(`[devdb] ${err.code ?? ''} ${err.message}`))
process.on('unhandledRejection', (err) => console.error(`[devdb] ${err?.code ?? ''} ${err?.message ?? err}`))
process.on('SIGINT', stop)
process.on('SIGTERM', stop)
