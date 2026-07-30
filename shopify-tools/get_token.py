#!/usr/bin/env python3
"""
Shopify OAuth - получить Admin API access token.
1. Печатает ссылку для авторизации - открой в браузере
2. Слушает callback на localhost:3456
3. Обменивает code на токен
4. Сохраняет токен в .env (строка SHOPIFY_ACCESS_TOKEN)

Запуск:
    python3 get_token.py
"""

import http.server
import json
import os
import sys
import urllib.parse
import urllib.request
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
STORE = os.environ["SHOPIFY_SHOP"]
REDIRECT_URI = os.getenv("SHOPIFY_AUTH_REDIRECT", "http://localhost:3456/callback")
SCOPES = os.getenv(
    "SHOPIFY_OAUTH_SCOPES",
    "read_products,write_products,read_inventory,write_inventory,read_content,write_content"
)

token_result = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]

        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received")
            return

        data = json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
        }).encode()

        req = urllib.request.Request(
            f"https://{STORE}/admin/oauth/access_token",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                token = result.get("access_token", "")
                token_result["access_token"] = token

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>Готово! Токен получен. Закрой вкладку.</h1>".encode("utf-8"))

            print(f"\n{'='*60}")
            print(f"ТОКЕН ПОЛУЧЕН: {token}")
            print(f"{'='*60}\n")

            # Update SHOPIFY_ACCESS_TOKEN in .env
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith("SHOPIFY_ACCESS_TOKEN="):
                        lines[i] = f"SHOPIFY_ACCESS_TOKEN={token}\n"
                        updated = True
                        break
                if not updated:
                    lines.append(f"SHOPIFY_ACCESS_TOKEN={token}\n")
                with open(env_path, "w") as f:
                    f.writelines(lines)
                print(f"Токен записан в {env_path}")
            else:
                print(f"Файл .env не найден, токен только в консоли выше")

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Ошибка: {e}".encode())
            print(f"Ошибка: {e}")

    def log_message(self, format, *args):
        pass


def main():
    auth_url = (
        f"https://{STORE}/admin/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&scope={urllib.parse.quote(SCOPES)}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    )

    print("=" * 60)
    print("SHOPIFY OAUTH - получение токена")
    print("=" * 60)
    print(f"\nОткрой эту ссылку в браузере:\n")
    print(auth_url)
    print(f"\nЖду callback на {REDIRECT_URI} ...\n")

    server = http.server.HTTPServer(("localhost", 3456), Handler)

    while not token_result.get("access_token"):
        server.handle_request()

    server.server_close()
    print("Готово!")


if __name__ == "__main__":
    main()
