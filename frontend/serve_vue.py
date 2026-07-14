from __future__ import annotations

import argparse
import mimetypes
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse


class VueHandler(SimpleHTTPRequestHandler):
    # Windows 환경에서 .js가 text/plain으로 인식되는 문제를 강제로 교정
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".wasm": "application/wasm",
    }

    def end_headers(self) -> None:
        # 개발 중 캐시로 이전 파일이 남는 문제 방지
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        # 실제 파일이 없고 확장자가 없는 경로라면 Vue SPA 진입점으로 처리
        parsed_path = unquote(urlparse(self.path).path)
        requested = (Path(self.directory) / parsed_path.lstrip("/")).resolve()
        root = Path(self.directory).resolve()

        try:
            requested.relative_to(root)
        except ValueError:
            self.send_error(403, "Forbidden")
            return

        if (
            parsed_path != "/"
            and not requested.exists()
            and "." not in Path(parsed_path).name
        ):
            self.path = "/index.html"

        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Vue dist 폴더용 로컬 서버")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--directory", default="dist")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    index_file = root / "index.html"

    if not index_file.exists():
        raise SystemExit(
            f"[오류] {index_file} 파일이 없습니다.\n"
            "프로젝트 루트에서 실행하거나 --directory 경로를 확인하세요."
        )

    # 운영체제 MIME 등록정보보다 아래 설정을 우선 사용
    mimetypes.add_type("application/javascript", ".js", strict=True)
    mimetypes.add_type("application/javascript", ".mjs", strict=True)
    mimetypes.add_type("text/css", ".css", strict=True)

    handler = lambda *handler_args, **handler_kwargs: VueHandler(
        *handler_args,
        directory=str(root),
        **handler_kwargs,
    )

    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Serving {root}")
    print(f"Open: http://127.0.0.1:{args.port}/")
    print("Stop: Ctrl + C")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
