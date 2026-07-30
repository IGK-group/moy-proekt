#!/usr/bin/env python3
"""
Обновить цены в MebelShop по ценам донора.
- Берёт цену донора через публичный /products/{handle}.json
- Ставит цену = цена_донора * DISCOUNT с "красивым" округлением
- compare_at_price = оригинальная цена донора (зачёркнутая)

Запуск:
    python3 update_prices.py          # все товары
    python3 update_prices.py 50       # продолжить с 50-го (если прервалось)

Переменные в .env:
    SHOPIFY_SHOP, SHOPIFY_ACCESS_TOKEN, SOURCE_STORE_DOMAIN, DISCOUNT
"""

import os
import re
import sys
import math
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SHOP = os.environ["SHOPIFY_SHOP"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
SOURCE_DOMAIN = os.environ["SOURCE_STORE_DOMAIN"]
DISCOUNT = float(os.getenv("DISCOUNT", "0.90"))
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")

BASE_URL = f"https://{SHOP}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}
DONOR_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

START_FROM = int(sys.argv[1]) if len(sys.argv) > 1 else 0
DELAY = 0.4
TIMEOUT = 30


def nice_price(price):
    """Красивое округление: $199.99, $49.99, $999.99"""
    discounted = price * DISCOUNT
    if discounted < 20:
        nice = round(discounted) - 0.01
        nice = max(nice, 0.99)
    elif discounted < 100:
        nice = math.floor(discounted / 5) * 5 - 0.01
        nice = max(nice, 19.99)
    elif discounted < 500:
        nice = math.floor(discounted / 10) * 10 - 0.01
        nice = max(nice, 99.99)
    else:
        nice = math.floor(discounted / 50) * 50 - 0.01
        nice = max(nice, 499.99)
    return f"{nice:.2f}"


def shopify_get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    while True:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            print(f"  [429] Shopify rate limit, ждём {wait}с...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()


def shopify_put(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(3):
        resp = requests.put(url, headers=HEADERS, json=data, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            print(f"  [429] Shopify rate limit, ждём {wait}с...")
            time.sleep(wait)
            continue
        if resp.status_code in (503, 504):
            print(f"  [{resp.status_code}] Попытка {attempt+1}/3...")
            time.sleep(3)
            continue
        resp.raise_for_status()
        return resp.json()


def fetch_all_products():
    """Получить все товары магазина с пагинацией."""
    products = []
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,handle,variants"
    while url:
        print(f"  Загружаем страницу... (уже {len(products)} товаров)")
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        batch = resp.json().get("products", [])
        products.extend(batch)
        url = None
        link = resp.headers.get("Link", "")
        for part in link.split(","):
            if 'rel="next"' in part:
                m = re.search(r'<(.+?)>', part)
                if m:
                    url = m.group(1)
        time.sleep(DELAY)
    return products


def fetch_donor_product(handle):
    """Получить товар донора по handle. None если не найден."""
    url = f"https://{SOURCE_DOMAIN}/products/{handle}.json"
    for _ in range(3):
        try:
            resp = requests.get(url, headers=DONOR_HEADERS, timeout=(5, 10))
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 2))
                print(f"    Донор rate limit, ждём {wait}с...")
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("product")
        except requests.RequestException as e:
            print(f"    Ошибка запроса к донору ({handle}): {e}")
    return None


def main():
    print("=" * 70)
    print(f"ОБНОВЛЕНИЕ ЦЕН: {SOURCE_DOMAIN} -> {SHOP} (скидка {int((1-DISCOUNT)*100)}%)")
    print("=" * 70)

    print("\n[1] Загружаем товары магазина...")
    products = fetch_all_products()
    print(f"    Итого товаров: {len(products)}")

    if START_FROM:
        print(f"    Продолжаем с товара #{START_FROM}")

    print(f"\n[2] Обновляем цены...\n")

    stats = {"matched": 0, "not_found": 0, "updated": 0, "skipped": 0, "errors": 0}
    updated_list = []

    for i, product in enumerate(products):
        if i < START_FROM:
            continue

        title = product["title"]
        handle = product["handle"]
        our_variants = product.get("variants", [])

        print(f"[{i+1}/{len(products)}] {title}")

        time.sleep(DELAY)
        donor = fetch_donor_product(handle)

        if donor is None:
            print(f"  -> Не найден у донора, пропуск")
            stats["not_found"] += 1
            continue

        stats["matched"] += 1
        donor_variants = donor.get("variants", [])

        for vi in range(min(len(our_variants), len(donor_variants))):
            our_v = our_variants[vi]
            donor_v = donor_variants[vi]
            donor_price = float(donor_v.get("price", 0))

            if donor_price <= 0:
                continue

            new_price = nice_price(donor_price)
            compare_at = f"{donor_price:.2f}"
            current_price = our_v.get("price", "0")

            if current_price == new_price:
                stats["skipped"] += 1
                continue

            print(f"  V{vi+1}: ${donor_price:.2f} -> -{int((1-DISCOUNT)*100)}% -> ${new_price} (было ${current_price})")

            try:
                time.sleep(DELAY)
                shopify_put(f"/variants/{our_v['id']}.json", {
                    "variant": {
                        "id": our_v["id"],
                        "price": new_price,
                        "compare_at_price": compare_at,
                    }
                })
                print(f"    OK")
                stats["updated"] += 1
            except Exception as e:
                print(f"    ОШИБКА: {e}")
                stats["errors"] += 1

        updated_list.append(title)

    print("\n" + "=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print(f"  Всего товаров:       {len(products)}")
    print(f"  Найдено у донора:    {stats['matched']}")
    print(f"  Не найдено:          {stats['not_found']}")
    print(f"  Вариантов обновлено: {stats['updated']}")
    print(f"  Пропущено (те же):   {stats['skipped']}")
    print(f"  Ошибок:              {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
