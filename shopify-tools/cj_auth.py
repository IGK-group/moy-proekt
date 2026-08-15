"""Обмен CJ_API_KEY на accessToken/refreshToken, запись в .env."""
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"


def upsert_env_var(key: str, value: str) -> None:
    with open(ENV_PATH, "r") as f:
        lines = f.readlines()

    pattern = re.compile(rf"^{re.escape(key)}=")
    found = False
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w") as f:
        f.writelines(lines)


def main():
    api_key = os.environ["CJ_API_KEY"]
    resp = requests.post(AUTH_URL, json={"apiKey": api_key})
    resp.raise_for_status()
    data = resp.json()

    if not data.get("result"):
        print(f"Ошибка авторизации CJ API: {data.get('message')}")
        return

    payload = data["data"]
    upsert_env_var("CJ_ACCESS_TOKEN", payload["accessToken"])
    upsert_env_var("CJ_REFRESH_TOKEN", payload["refreshToken"])
    upsert_env_var("CJ_ACCESS_TOKEN_EXPIRY", payload["accessTokenExpiryDate"])

    print("CJ API подключён.")
    print(f"Access token истекает: {payload['accessTokenExpiryDate']}")
    print(f"Refresh token истекает: {payload['refreshTokenExpiryDate']}")


if __name__ == "__main__":
    main()
