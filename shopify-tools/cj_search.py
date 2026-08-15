"""Поиск товаров в каталоге CJ по ключевым словам ниш-кандидатов."""
import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["CJ_ACCESS_TOKEN"]
BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"
HEADERS = {"CJ-Access-Token": TOKEN}

_last_call = 0.0


def _rate_limit():
    global _last_call
    elapsed = time.monotonic() - _last_call
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_call = time.monotonic()


def search(keyword, country_code="US", size=20, verified_only=True):
    params = {
        "keyWord": keyword,
        "page": 1,
        "size": size,
        "countryCode": country_code,
        "orderBy": 4,  # по остатку на складе
    }
    if verified_only:
        params["verifiedWarehouse"] = 1
    for attempt in range(5):
        _rate_limit()
        resp = requests.get(f"{BASE_URL}/product/listV2", headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(2)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def main():
    keyword = sys.argv[1] if len(sys.argv) > 1 else "window cleaning robot"
    data = search(keyword)
    print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
