"""Quét lỗ hổng thư viện phụ thuộc (SEC-014): pip-audit cho backend, npm audit cho frontend và devdb.

Thoát mã 1 nếu có lỗ hổng mức High/Critical. Dùng: python scripts/audit_deps.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NPM = shutil.which("npm") or "npm"
bad = False


def run(title: str, cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    print(f"\n=== {title}\n$ {' '.join(cmd)}  (cwd: {cwd})", flush=True)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


r = run("pip-audit (backend)",
        [sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "--progress-spinner", "off"], ROOT / "backend")
print((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "(không có output)")
if r.returncode != 0:
    bad = True
    print("pip-audit báo lỗ hổng hoặc lỗi – xem log đầy đủ")

for name in ("frontend", "devdb"):
    r = run(f"npm audit --omit=dev ({name})", [NPM, "audit", "--omit=dev", "--json"], ROOT / name)
    try:
        meta = json.loads(r.stdout)["metadata"]["vulnerabilities"]
    except (json.JSONDecodeError, KeyError):
        print(f"Không đọc được kết quả npm audit: {r.stdout[:300]} {r.stderr[:300]}")
        bad = True
        continue
    print(f"Lỗ hổng: {meta}")
    if meta.get("high", 0) or meta.get("critical", 0):
        bad = True

print("\nKẾT LUẬN:", "CÓ lỗ hổng High/Critical" if bad else "Không có lỗ hổng High/Critical")
sys.exit(1 if bad else 0)
