"""Chạy một ứng dụng ASGI bằng uvicorn trên SelectorEventLoop.

psycopg async không chạy được trên ProactorEventLoop (mặc định của Windows), nên không dùng thẳng
lệnh `uvicorn`. Cách dùng: python serve.py app.main:app_factory --factory --port 8000
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import uvicorn


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("target")
    p.add_argument("--factory", action="store_true")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    a = p.parse_args()
    config = uvicorn.Config(a.target, factory=a.factory, host=a.host, port=a.port, proxy_headers=True,
                            log_level="info", access_log=False)
    server = uvicorn.Server(config)
    if sys.platform == "win32":
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()
