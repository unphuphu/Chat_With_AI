// Chạy lần lượt các test case dạng dòng lệnh trong evidence/cli-cases.json qua record-cli.ts.
//   node evidence/run-cli-cases.ts [ID …]      # không có ID = chạy tất cả (trừ --skip)
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

interface Case {
  tc: string
  id: string
  title: string
  cmd: string
  cwd: string
  expect: string
}
const here = path.dirname(fileURLToPath(import.meta.url))
const cases: Case[] = JSON.parse(fs.readFileSync(path.join(here, 'cli-cases.json'), 'utf8'))
const args = process.argv.slice(2)
const skip = new Set(args.filter((a) => a.startsWith('--skip=')).flatMap((a) => a.slice(7).split(',')))
const only = new Set(args.filter((a) => !a.startsWith('--')))
const results: string[] = []
for (const c of cases) {
  if (skip.has(c.id) || (only.size && !only.has(c.id))) continue
  const r = spawnSync(
    process.execPath,
    ['evidence/record-cli.ts', '--tc', c.tc, '--title', c.title, '--cwd', c.cwd, '--expect', c.expect, '--', ...c.cmd.split(' ')],
    { cwd: path.join(here, '..'), encoding: 'utf8' },
  )
  const line = (r.stdout.match(/\[evidence\] .*/g) ?? [`[evidence] ${c.id}: LỖI CÔNG CỤ ${r.stderr.slice(-200)}`]).pop()!
  console.log(line)
  results.push(line)
}
fs.writeFileSync(path.join(here, '..', '..', '..', 'test_reports', '_cli-run.log'), results.join('\n') + '\n')
