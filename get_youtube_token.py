#!/usr/bin/env python3
"""
Obtenir un YouTube Refresh Token permanent
Lance ce script UNE FOIS sur ton PC, puis colle le refresh_token dans Railway.
"""

import os, requests, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── REMPLIS CES VALEURS ───────────────────────────────────────────────────────
CLIENT_ID     = "COLLE_TON_CLIENT_ID_ICI"
CLIENT_SECRET = "COLLE_TON_CLIENT_SECRET_ICI"
# ──────────────────────────────────────────────────────────────────────────────

REDIRECT_URI  = "http://localhost:8080"
SCOPE         = "https://www.googleapis.com/auth/youtube.upload"

auth_url = (
    f"https://accounts.google.com/o/oauth2/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope={SCOPE}"
    f"&access_type=offline"
    f"&prompt=consent"
)

print("Ouverture du navigateur pour autorisation YouTube...")
webbrowser.open(auth_url)

code_received = []

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        code = params.get("code", [None])[0]
        if code:
            code_received.append(code)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h1>OK ! Tu peux fermer cet onglet.</h1>")
    def log_message(self, *args): pass

server = HTTPServer(("localhost", 8080), Handler)
print("En attente du callback OAuth...")
while not code_received:
    server.handle_request()

code = code_received[0]
r = requests.post("https://oauth2.googleapis.com/token", data={
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
})
tokens = r.json()
print("\n✅ TOKENS OBTENUS !")
print(f"Access Token  : {tokens.get('access_token','')}")
print(f"Refresh Token : {tokens.get('refresh_token','')}")
print(f"\n→ Colle le REFRESH_TOKEN dans Railway comme variable YOUTUBE_REFRESH_TOKEN")
print(f"→ Puis mets aussi YOUTUBE_CLIENT_ID et YOUTUBE_CLIENT_SECRET")
