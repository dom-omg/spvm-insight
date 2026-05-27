#!/usr/bin/env python3
"""Serveur minimal pour SPVM INSIGHT — aucune dépendance externe requise."""
import http.server, socketserver, os

PORT = int(os.environ.get("PORT", 5200))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} → {fmt % args}")

print(f"\n🚔 SPVM INSIGHT — http://localhost:{PORT}\n")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
