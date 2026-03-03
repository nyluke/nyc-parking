#!/usr/bin/env python3
"""Simple HTTP server with gzip support for serving parking data."""

import http.server
import os

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))


class GzipHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        # Serve pre-gzipped JSON if the browser accepts gzip
        if self.path == "/parking_data.json":
            gz_path = os.path.join(DIR, "parking_data.json.gz")
            if os.path.exists(gz_path) and "gzip" in self.headers.get("Accept-Encoding", ""):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(os.path.getsize(gz_path)))
                self.end_headers()
                with open(gz_path, "rb") as f:
                    self.wfile.write(f.read())
                return
        super().do_GET()


print(f"Serving at http://localhost:{PORT}")
http.server.HTTPServer(("", PORT), GzipHandler).serve_forever()
