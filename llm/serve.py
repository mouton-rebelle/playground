#!/usr/bin/env python3
"""Tiny dev server with live reload for index.html.

Usage: python3 serve.py [port]
Open http://localhost:8000/  — the page reloads automatically when index.html changes.
"""
import http.server
import os
import socketserver
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WATCH = ROOT / "index.html"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

RELOAD_SNIPPET = b"""
<script>
(() => {
  const es = new EventSource('/__reload');
  es.onmessage = (e) => { if (e.data === 'reload') location.reload(); };
  es.onerror = () => { es.close(); setTimeout(() => location.reload(), 500); };
})();
</script>
</body>"""

# Shared mtime; bumped by the watcher thread, read by SSE handlers.
state = {"mtime": WATCH.stat().st_mtime if WATCH.exists() else 0.0}


def watcher():
    last = state["mtime"]
    while True:
        try:
            m = WATCH.stat().st_mtime
            if m != last:
                last = m
                state["mtime"] = m
        except FileNotFoundError:
            pass
        time.sleep(0.3)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        if "__reload" in (args[0] if args else ""):
            return
        super().log_message(fmt, *args)

    def do_GET(self):
        if self.path == "/__reload":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            last = state["mtime"]
            try:
                while True:
                    if state["mtime"] != last:
                        last = state["mtime"]
                        self.wfile.write(b"data: reload\n\n")
                        self.wfile.flush()
                    else:
                        # heartbeat so the connection doesn't go silent
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                    time.sleep(0.5)
            except (BrokenPipeError, ConnectionResetError):
                return
            return

        # Inject reload snippet into index.html responses.
        if self.path in ("/", "/index.html"):
            try:
                body = WATCH.read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            if b"</body>" in body:
                body = body.replace(b"</body>", RELOAD_SNIPPET, 1)
            else:
                body = body + RELOAD_SNIPPET
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    os.chdir(ROOT)
    threading.Thread(target=watcher, daemon=True).start()
    with ThreadingServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"serving {ROOT} on http://localhost:{PORT}/ (live reload on {WATCH.name})")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")


if __name__ == "__main__":
    main()
