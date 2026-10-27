"""Sinh doc/07-verification/test_cases/*.md (mỗi file 1 test case) từ TEST_PLAN.md v0.2.

Dữ liệu test case nằm trong _tc_data/*.py; chạy lại script này sau khi sửa dữ liệu:
    python doc/07-verification/_build_test_cases.py
"""

from __future__ import annotations

import io
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _tc_data import api, e2e, nonfunc, quality, unit_int  # noqa: E402

OUT = os.path.join(HERE, "test_cases")
APP_URL = "http://localhost:8080/"

MODE_TEXT = {
    "cli": "Tự động – dòng lệnh, ghi bằng `app/frontend/evidence/record-cli.ts`",
    "ui": "Tự động – Playwright trên trình duyệt, ghi bằng `app/frontend/evidence/fixture.ts`",
    "manual": "Bán tự động – Playwright điều khiển trình duyệt và ghi bằng chứng; bước có đánh dấu 👤 cần người đánh giá",
    "staging": "Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo",
}
ORDER = ["UT", "INT", "API", "E2E", "SEC", "ACC", "UI", "PERF", "QLT", "UAT"]
TYPE_NAME = {
    "UT": "Unit", "INT": "Integration", "API": "API", "E2E": "System (E2E)", "SEC": "Security",
    "ACC": "Accessibility", "UI": "UI/UX", "PERF": "Performance", "QLT": "Chất lượng câu trả lời", "UAT": "Acceptance",
}


def slug(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60].rstrip("-")


def folder_of(tc: dict) -> str:
    return f"{tc['id']}_{slug(tc['title'])}"


def md_cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", "<br>")


def agent_tasks(tc: dict, folder: str) -> list[str]:
    mode = tc["mode"]
    out = [
        "## Nhiệm vụ của agent (bắt buộc)",
        "",
        f"Agent thực hiện test case này **trên ứng dụng tại {APP_URL}** và phải tạo đủ bằng chứng sau trong thư mục "
        f"**`./test_reports/{folder}/`** (tính từ thư mục gốc repo):",
        "",
        "| Artifact | Vị trí | Yêu cầu |",
        "|---|---|---|",
        f"| Test report | `test_reports/{folder}/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |",
        f"| Ảnh chụp màn hình | `test_reports/{folder}/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |",
        f"| Video | `test_reports/{folder}/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |",
        f"| Log | `test_reports/{folder}/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |",
        "",
        "**Quy trình:**",
        "",
        f"1. **Kiểm tra môi trường:** mở {APP_URL} và gọi `GET {APP_URL}api/v1/readyz`, phải nhận `{{\"status\":\"ready\"}}`. "
        "Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, "
        "tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.",
    ]
    if mode in ("ui", "manual") or (mode == "staging" and tc.get("spec")):
        out += [
            f"2. **Viết spec** `app/frontend/testcases/{folder}.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. "
            "Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. "
            "Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API "
            "(dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) "
            "và `testcases/API-023_*.spec.ts` (API).",
            "3. **Chạy:** trong `app/frontend`, chạy "
            f"`npx playwright test -c playwright.testcases.config.ts {folder}`. Fixture tự ghi video của mọi tab, chụp ảnh "
            f"sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/{folder}/`.",
        ]
        if mode == "manual":
            out.append("4. **Bước cần người đánh giá (👤):** gọi `ev.step(…, { review: true })` để report đánh dấu "
                       "*Cần người xác nhận*. Người đánh giá xem ảnh/video, điền *Kết quả thực tế* vào `report.md` và đổi "
                       "kết luận. Nếu bước cần công cụ ngoài trình duyệt (NVDA, so sánh với `html_design`), quay toàn màn "
                       "hình bằng Xbox Game Bar (Win + Alt + R) hoặc OBS và lưu vào `video/` của test case.")
    elif mode == "cli":
        cmd = tc["cmd"]
        cwd = tc.get("cwd", "../backend")
        n = 2
        if tc.get("write_test"):
            path, _, hint = tc["write_test"].partition(" (")
            hint = f" ({hint}" if hint else ""
            out.append(f"{n}. **Viết test trước:** test tự động chưa có. Viết `{path}`{hint}, kiểm tra đúng các kết "
                       "quả mong đợi ở bảng *Các bước thực hiện*.")
            n += 1
        out += [
            f"{n}. **Chạy lệnh qua bộ ghi bằng chứng:** trong `app/frontend`, chạy:",
            "",
            "   ```bash",
            f"   node evidence/record-cli.ts --tc {folder} --title \"{tc['title']}\" --cwd {cwd} \\",
            f"     --expect \"{tc.get('cli_expect', 'Lệnh kết thúc với mã 0')}\" -- {cmd}",
            "   ```",
            "",
            "   Bộ ghi hiển thị output trên một trang Edge và quay video, chụp ảnh khi kết thúc, lưu log và ghi `report.md`.",
            f"{n + 1}. **Bổ sung report:** mở `test_reports/{folder}/report.md`, đối chiếu output với từng dòng ở bảng "
            "*Các bước thực hiện*, ghi kết quả từng dòng vào mục *Ghi chú / lỗi phát hiện*.",
        ]
    else:  # staging, không có spec
        out += [
            f"2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: "
            f"`node evidence/record-cli.ts --tc {folder} --title \"{tc['title']}\" -- <lệnh>`. Với k6/ZAP thì đặt "
            f"`BASE_URL={APP_URL}`.",
            "3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho "
            "launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.",
        ]
    out += [
        "",
        "**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; "
        "đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.",
        "",
        f"**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, "
        f"yêu cầu bị ảnh hưởng: {tc['trace']}).",
    ]
    return out


def render(tc: dict) -> str:
    folder = folder_of(tc)
    prefix = tc["id"].split("-")[0]
    lines = [
        f"# {tc['id']} – {tc['title']}",
        "",
        "| Trường | Giá trị |",
        "|---|---|",
        f"| ID | {tc['id']} |",
        f"| Loại | {TYPE_NAME[prefix]} |",
        f"| Ưu tiên | {tc['prio']} |",
        f"| Truy vết | {md_cell(tc['trace'])} |",
        f"| URL ứng dụng | {APP_URL} |",
        f"| Cách thực hiện | {MODE_TEXT[tc['mode']]} |",
        f"| Test tự động hiện có | {md_cell(tc.get('auto', '–'))} |",
        f"| Trạng thái chu kỳ C1 | {tc['c1']} |",
        f"| Thư mục artifact | `./test_reports/{folder}/` |",
        "| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |",
        "",
        "## Mục tiêu",
        "",
        tc["goal"],
        "",
        "## Điều kiện tiên quyết",
        "",
        *[f"- {p}" for p in tc["pre"]],
        "",
        "## Dữ liệu test",
        "",
        *([f"- {d}" for d in tc["data"]] or ["- Không cần dữ liệu riêng"]),
        "",
        "## Các bước thực hiện",
        "",
        "| # | Thao tác | Kết quả mong đợi |",
        "|---|---|---|",
        *[f"| {i} | {md_cell(a)} | {md_cell(e)} |" for i, (a, e) in enumerate(tc["steps"], start=1)],
        "",
        "## Tiêu chí đạt",
        "",
        tc.get("pass", "Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới."),
        "",
    ]
    if tc.get("tools"):
        lines += ["## Lệnh / công cụ", "", *[f"- {t}" for t in tc["tools"]], ""]
    if tc.get("notes"):
        lines += ["## Ghi chú", "", *[f"- {n}" for n in tc["notes"]], ""]
    lines += agent_tasks(tc, folder)
    lines.append("")
    return "\n".join(lines)


def index(cases: list[dict]) -> str:
    rows = []
    for tc in cases:
        f = folder_of(tc)
        rows.append(f"| [{tc['id']}]({f}.md) | {md_cell(tc['title'])} | {TYPE_NAME[tc['id'].split('-')[0]]} | {tc['prio']} | "
                    f"{tc['mode']} | {tc['c1']} | `test_reports/{f}/` |")
    by_type = {p: sum(1 for t in cases if t["id"].startswith(p + "-")) for p in ORDER}
    return "\n".join([
        "# Test case – AI Chat PDF",
        "",
        f"{len(cases)} test case tách từ [TEST_PLAN.md v0.2](../TEST_PLAN.md), mỗi file một test case. Mọi test case chạy "
        f"trên ứng dụng tại **{APP_URL}**. Artifact (report, ảnh chụp, video, log) của mỗi test case lưu trong "
        "`./test_reports/<tên test case>/` ở gốc repo.",
        "",
        "Số lượng: " + " · ".join(f"{p} {n}" for p, n in by_type.items()),
        "",
        "**Kết quả thực thi chu kỳ C2:** xem [test_reports/README.md](../../../test_reports/README.md) và [TEST_PLAN Phụ lục D](../TEST_PLAN.md#phụ-lục-d--kết-quả-thực-thi-chu-kỳ-c2-27102026).",
        "",
        "## Chuẩn bị (một lần)",
        "",
        "```bash",
        "cd app",
        "backend/.venv/Scripts/python.exe run.py --sample     # chỉ lần đầu: sinh PDF mẫu (Ctrl+C sau khi thấy 'Sẵn sàng')",
        "cd frontend && npm install && npx playwright install ffmpeg   # ffmpeg để Playwright ghi video",
        "node evidence/app.ts start                            # ứng dụng tại http://localhost:8080/ (chạy nền)",
        "```",
        "",
        "Khởi động ứng dụng bằng `evidence/app.ts` (thay vì chạy `run.py` bằng tay) để các test case cần cấu hình riêng "
        "(`LLM_PROVIDER`, `SESSION_IDLE_MIN`, `MAX_DOCS_PER_WORKSPACE`…) tự khởi động lại được: "
        "`node evidence/app.ts restart KEY=VALUE`, hoặc `await ev.restartApp({...})` trong spec. "
        "Dừng: `node evidence/app.ts stop`. Log ứng dụng: `test_reports/_app/app.log`.",
        "",
        "## Công cụ thu bằng chứng (`app/frontend/evidence/`)",
        "",
        "| File | Dùng cho | Tạo ra |",
        "|---|---|---|",
        "| `fixture.ts` | Test giao diện và API (mode `ui`, `manual`) – spec ở `app/frontend/testcases/<tên test case>.spec.ts`, chạy bằng `npx playwright test -c playwright.testcases.config.ts <tên>` | Video mọi tab, ảnh sau mỗi `ev.step`, `logs/api.log`, `report.md`, `result.json` |",
        "| `record-cli.ts` | Test chạy bằng lệnh (mode `cli`, `staging`): pytest, smoke, k6, pip-audit… – `node evidence/record-cli.ts --tc <tên> --title … -- <lệnh>` | Video trang hiển thị output, ảnh kết quả, `logs/output.log`, `report.md`, `result.json` |",
        "| `app.ts` | Khởi động / khởi động lại / dừng ứng dụng với biến môi trường riêng, chờ `readyz` | `test_reports/_app/app.log` |",
        "| `report.ts` | Mẫu report dùng chung; tự lưu trữ lần chạy cũ vào `test_reports/_archive/` | – |",
        "",
        "Cấu trúc thư mục artifact:",
        "",
        "```text",
        "test_reports/",
        "└── E2E-002_nguoi-ngoai-nhom-bi-tu-choi/",
        "    ├── report.md          # test report (kết luận, môi trường, bảng bước, link ảnh/video)",
        "    ├── result.json        # cùng nội dung, dạng máy đọc",
        "    ├── screenshots/       # 01-<bước>.png, 02-…",
        "    ├── video/             # <ID>-app.webm (tab ứng dụng), <ID>-page2.webm (tab API) hoặc <ID>-cli.webm",
        "    └── logs/              # api.log hoặc output.log",
        "```",
        "",
        "**Mode:** `cli` = chạy lệnh · `ui` = Playwright tự động · `manual` = Playwright + người đánh giá bước 👤 · "
        "`staging` = kết quả chính thức cần ENV-STAGING, chạy trên localhost để tham khảo.",
        "",
        "## Danh sách",
        "",
        "| ID | Tiêu đề | Loại | Ưu tiên | Mode | Trạng thái C1 | Artifact |",
        "|---|---|---|---|---|---|---|",
        *rows,
        "",
        "_File được sinh bằng `doc/07-verification/_build_test_cases.py` – sửa dữ liệu trong `_tc_data/` rồi chạy lại script._",
        "",
    ])


def main() -> None:
    cases = [*unit_int.CASES, *api.CASES, *e2e.CASES, *nonfunc.CASES, *quality.CASES]
    cases.sort(key=lambda t: (ORDER.index(t["id"].split("-")[0]), t["id"]))
    ids = [t["id"] for t in cases]
    dup = {i for i in ids if ids.count(i) > 1}
    assert not dup, f"Trùng ID: {dup}"
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith(".md"):
            os.remove(os.path.join(OUT, old))
    for tc in cases:
        for key in ("id", "title", "prio", "trace", "mode", "c1", "goal", "pre", "data", "steps"):
            assert key in tc, f"{tc.get('id')}: thiếu {key}"
        if tc["mode"] == "cli":
            assert tc.get("cmd"), f"{tc['id']}: thiếu cmd"
        io.open(os.path.join(OUT, folder_of(tc) + ".md"), "w", encoding="utf-8", newline="\n").write(render(tc))
    io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n").write(index(cases))
    print(f"test cases: {len(cases)} -> {OUT}")


if __name__ == "__main__":
    main()
