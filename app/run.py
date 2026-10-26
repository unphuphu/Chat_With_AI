"""Khởi động toàn bộ môi trường dev bằng một lệnh (thay docker-compose + Makefile – xem README.md).

    backend/.venv/Scripts/python.exe run.py            # Windows
    backend/.venv/bin/python run.py                    # Linux/macOS

Tiến trình: devdb (PGlite :54329) → devidp (:8090) → API + worker (:8000, tự chạy migration)
→ web (Vite :8080). Mở http://localhost:8080 rồi đăng nhập bằng người dùng mẫu "p1".
Tùy chọn: --sample  sinh PDF mẫu vào sample-pdfs/;  --no-web  không chạy Vite.
Ctrl+C dừng tất cả.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DEVDB = ROOT / "devdb"
DATA = ROOT / ".data"
WIN = sys.platform == "win32"
NPM = "npm.cmd" if WIN else "npm"
NODE = shutil.which("node") or "node"
COLORS = {"devdb": "35", "devidp": "33", "api": "36", "web": "32"}


def wait_port(port: int, timeout: float, proc: subprocess.Popen[bytes], name: str) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise SystemExit(f"[run] {name} đã dừng (mã {proc.returncode}) – xem log phía trên")
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.3)
    raise SystemExit(f"[run] {name} chưa mở cổng {port} sau {timeout:.0f} s")


def port_busy(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def pump(name: str, proc: subprocess.Popen[bytes]) -> None:
    color = COLORS.get(name, "0")
    assert proc.stdout is not None
    for raw in iter(proc.stdout.readline, b""):
        line = raw.decode("utf-8", "replace").rstrip()
        sys.stdout.write(f"\x1b[{color}m{name:>6}\x1b[0m | {line}\n")
        sys.stdout.flush()


def start(name: str, cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.Popen[bytes]:
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if WIN else 0
    proc = subprocess.Popen(cmd, cwd=cwd, env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})},  # noqa: S603
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags)
    threading.Thread(target=pump, args=(name, proc), daemon=True).start()
    return proc


def ensure_node_modules(folder: Path) -> None:
    if not (folder / "node_modules").exists():
        print(f"[run] npm install trong {folder.name}/ …")
        subprocess.run([NPM, "install", "--no-audit", "--no-fund"], cwd=folder, check=True)  # noqa: S603


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true", help="sinh PDF mẫu vào sample-pdfs/")
    ap.add_argument("--no-web", action="store_true", help="không chạy Vite (chỉ backend)")
    args = ap.parse_args()
    # Console Windows mặc định cp1252 – không in được tiếng Việt
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    py = sys.executable
    if not (ROOT / ".env").exists():
        shutil.copy(ROOT / ".env.example", ROOT / ".env")
        print("[run] đã tạo .env từ .env.example")
    for port in (54329, 8090, 8000, *(() if args.no_web else (8080,))):
        if port_busy(port):
            raise SystemExit(f"[run] cổng {port} đang được dùng – hãy dừng tiến trình đang chiếm cổng rồi chạy lại")
    ensure_node_modules(DEVDB)
    if not args.no_web:
        ensure_node_modules(FRONTEND)
    if args.sample:
        subprocess.run([py, "-m", "tests.fixtures.pdfgen", str(ROOT / "sample-pdfs")], cwd=BACKEND,  # noqa: S603
                       check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    procs: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        DATA.mkdir(exist_ok=True)
        p = start("devdb", [NODE, "server.mjs"], DEVDB, {"DEVDB_DIR": str(DATA / "pgdata"), "DEVDB_PORT": "54329"})
        procs.append(("devdb", p))
        wait_port(54329, 90, p, "devdb")

        p = start("devidp", [py, "serve.py", "devidp.main:app", "--port", "8090"], BACKEND)
        procs.append(("devidp", p))
        wait_port(8090, 60, p, "devidp")

        p = start("api", [py, "serve.py", "app.main:app_factory", "--factory", "--port", "8000"], BACKEND)
        procs.append(("api", p))
        wait_port(8000, 120, p, "api")

        if not args.no_web:
            # Gọi thẳng node (không qua npm.cmd) để terminate() dừng được Vite
            p = start("web", [NODE, "node_modules/vite/bin/vite.js", "--host", "127.0.0.1"], FRONTEND)
            procs.append(("web", p))
            wait_port(8080, 90, p, "web")
        url = "http://localhost:8080" if not args.no_web else "http://localhost:8000/api/v1/docs"
        print(f"\n[run] Sẵn sàng → {url}  (đăng nhập: chọn người dùng mẫu p1). Ctrl+C để dừng.\n", flush=True)
        while all(pr.poll() is None for _, pr in procs):
            time.sleep(0.5)
        dead = next(n for n, pr in procs if pr.poll() is not None)
        print(f"[run] {dead} đã dừng – dừng các tiến trình còn lại")
    except KeyboardInterrupt:
        print("\n[run] đang dừng…")
    finally:
        for _name, pr in reversed(procs):
            if pr.poll() is None:
                pr.terminate()
        for _name, pr in reversed(procs):
            try:
                pr.wait(8)
            except subprocess.TimeoutExpired:
                pr.kill()


if __name__ == "__main__":
    main()
