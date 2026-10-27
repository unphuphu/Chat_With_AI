// Khởi động / dừng ứng dụng (app/run.py) với biến môi trường riêng cho test case, rồi chờ http://localhost:8080/ sẵn sàng.
//   node evidence/app.ts start [KEY=VALUE …]     # chạy nền, ghi PID vào test_reports/_app/app.pid
//   node evidence/app.ts restart [KEY=VALUE …]   # dừng bản do công cụ này khởi động rồi chạy lại với cấu hình mới
//   node evidence/app.ts stop
// Trong spec: await ev.restartApp({ LLM_PROVIDER: 'anthropic', LLM_API_KEY: 'sk-ant-invalid' })
import { execSync, spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { REPO_ROOT, REPORTS_ROOT } from './report.ts'

const STATE_DIR = path.join(REPORTS_ROOT, '_app')
const PID_FILE = path.join(STATE_DIR, 'app.pid')
const LOG_FILE = path.join(STATE_DIR, 'app.log')
const APP_DIR = path.join(REPO_ROOT, 'app')
const RUN_PIDS = path.join(APP_DIR, '.data', 'run.pids.json')
const PY = process.platform === 'win32' ? 'backend/.venv/Scripts/python.exe' : 'backend/.venv/bin/python'
const READY_URL = 'http://localhost:8080/api/v1/readyz'

async function isReady(): Promise<boolean> {
  try {
    const r = await fetch(READY_URL, { signal: AbortSignal.timeout(2000) })
    return r.ok && (await r.text()).includes('ready')
  } catch {
    return false
  }
}

async function isUp(): Promise<boolean> {
  try {
    await fetch('http://localhost:8080/', { signal: AbortSignal.timeout(2000) })
    return true
  } catch {
    return false
  }
}

export async function waitReady(timeoutMs = 180_000): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await isReady()) return
    await new Promise((r) => setTimeout(r, 1000))
  }
  throw new Error(`Ứng dụng chưa sẵn sàng sau ${timeoutMs / 1000} s – xem ${LOG_FILE}`)
}

export async function stopApp(): Promise<void> {
  if (!fs.existsSync(PID_FILE)) {
    if (await isUp()) {
      throw new Error('Ứng dụng đang chạy nhưng không do evidence/app.ts khởi động. Dừng run.py hiện tại (Ctrl+C) rồi chạy lại.')
    }
    return
  }
  // run.py ghi PID của nó và từng tiến trình con (devdb, devidp, api, web) vào app/.data/run.pids.json.
  // Trên Windows, taskkill /T từ trình khởi chạy của venv không lần tới các tiến trình con, nên phải dừng từng PID.
  const pids = [Number(fs.readFileSync(PID_FILE, 'utf8'))]
  if (fs.existsSync(RUN_PIDS)) pids.push(...Object.values(JSON.parse(fs.readFileSync(RUN_PIDS, 'utf8')) as number[]))
  for (const pid of pids) {
    try {
      if (process.platform === 'win32') execSync(`taskkill /PID ${pid} /T /F`, { stdio: 'ignore' })
      else process.kill(pid, 'SIGTERM')
    } catch {
      /* tiến trình đã dừng */
    }
  }
  fs.rmSync(PID_FILE, { force: true })
  fs.rmSync(RUN_PIDS, { force: true })
  const deadline = Date.now() + 30_000
  while (Date.now() < deadline && (await isUp())) await new Promise((r) => setTimeout(r, 500))
}

export async function startApp(env: Record<string, string> = {}): Promise<void> {
  if (await isUp()) throw new Error('Cổng 8080 đang được dùng – gọi restart hoặc dừng run.py hiện tại trước.')
  fs.mkdirSync(STATE_DIR, { recursive: true })
  const out = fs.openSync(LOG_FILE, 'a')
  fs.writeSync(out, `\n=== ${new Date().toISOString()} start ${JSON.stringify(env)}\n`)
  const child = spawn(path.join(APP_DIR, PY), ['run.py'], {
    cwd: APP_DIR,
    env: { ...process.env, ...env, PYTHONIOENCODING: 'utf-8' },
    detached: true, // tách hẳn khỏi tiến trình khởi chạy: khi app.ts thoát, ứng dụng vẫn chạy và đường ống log còn nguyên
    stdio: ['ignore', out, out],
    windowsHide: true,
  })
  child.unref()
  fs.writeFileSync(PID_FILE, String(child.pid))
  await waitReady()
}

export async function restartApp(env: Record<string, string> = {}): Promise<void> {
  await stopApp()
  await startApp(env)
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(import.meta.filename ?? '')
if (isMain) {
  const [cmd, ...pairs] = process.argv.slice(2)
  const env = Object.fromEntries(pairs.map((p) => p.split(/=(.*)/s).slice(0, 2) as [string, string]))
  const run = { start: () => startApp(env), restart: () => restartApp(env), stop: () => stopApp() }[cmd ?? '']
  if (!run) {
    console.error('Cách dùng: node evidence/app.ts start|restart|stop [KEY=VALUE …]')
    process.exit(2)
  }
  run().then(
    () => console.log(`[app] ${cmd} xong${cmd === 'stop' ? '' : ' – http://localhost:8080/ sẵn sàng'}`),
    (e: Error) => {
      console.error(`[app] ${e.message}`)
      process.exit(1)
    },
  )
}
