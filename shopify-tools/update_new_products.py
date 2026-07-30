#!/usr/bin/env python3
"""
Обновить цены + остатки для новых товаров магазина (добавленных сегодня).
- Берёт цены донора, применяет DISCOUNT с "красивым" округлением
- Ставит compare_at_price = оригинальная цена донора
- Выставляет остаток TARGET_AVAILABLE для каждого варианта

Запуск:
    python3 update_new_products.py              # товары за сегодня
    python3 update_new_products.py 2026-07-01   # товары за конкретную дату

Переменные в .env:
    SHOPIFY_SHOP, SHOPIFY_ACCESS_TOKEN, SOURCE_STORE_DOMAIN,
    DISCOUNT, TARGET_AVAILABLE, SHOPIFY_LOCATION_ID
"""

import os
import re
import sys
import math
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

SHOP = os.environ["SHOPIFY_SHOP"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
SOURCE_DOMAIN = os.environ["SOURCE_STORE_DOMAIN"]
DISCOUNT = float(os.getenv("DISCOUNT", "0.90"))
TARGET_INVENTORY = int(os.getenv("TARGET_AVAILABLE", "22"))
LOCATION_ID = int(os.getenv("SHOPIFY_LOCATION_ID", "0"))
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")

BASE_URL = f"https://{SHOP}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}
DONOR_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

DELAY = 0.5
TIMEOUT = 30

# Date filter: today or from arg
if len(sys.argv) > 1:
    DATE_FILTER = sys.argv[1]
else:
    DATE_FILTER = datetime.date.today().isoformat()


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


def api_get(url):
    while True:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            print(f"  [429] Ждём {wait}с...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp


def api_put(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(3):
        resp = requests.put(url, headers=HEADERS, json=data, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        if resp.status_code in (503, 504):
            time.sleep(3)
            continue
        resp.raise_for_status()
        return resp.json()


def api_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    while True:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()


def get_location_id():
    if LOCATION_ID:
        return LOCATION_ID
    resp = api_get(f"{BASE_URL}/locations.json")
    locations = resp.json().get("locations", [])
    if not locations:
        raise RuntimeError("Нет локаций в магазине")
    loc_id = locations[0]["id"]
    print(f"  Location ID найден автоматически: {loc_id}")
    return loc_id


def fetch_new_products(date_str):
    """Товары, созданные в указанную дату."""
    products = []
    created_at_min = f"{date_str}T00:00:00"
    created_at_max = f"{date_str}T23:59:59"
    url = (
        f"{BASE_URL}/products.json"
        f"?limit=250&created_at_min={created_at_min}&created_at_max={created_at_max}"
        f"&fields=id,title,handle,variants"
    )
    while url:
        resp = api_get(url)
        batch = resp.json().get("products", [])
        products.extend(batch)
        url = None
        link = resp.headers.get("Link", "")
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        if match:
            url = match.group(1)
        time.sleep(DELAY)
    return products


def fetch_donor_product(handle):
    url = f"https://{SOURCE_DOMAIN}/products/{handle}.json"
    for _ in range(3):
        try:
            resp = requests.get(url, headers=DONOR_HEADERS, timeout=(5, 10))
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 2))
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json().get("product")
        except requests.RequestException as e:
            print(f"    Ошибка донора ({handle}): {e}")
    return None


def main():
    print("=" * 70)
    print(f"НОВЫЕ ТОВАРЫ за {DATE_FILTER}: цены + остатки")
    print(f"Магазин: {SHOP} | Донор: {SOURCE_DOMAIN}")
    print("=" * 70)

    print("\n[1] Получаем location ID...")
    loc_id = get_location_id()

    print(f"\n[2] Загружаем товары за {DATE_FILTER}...")
    products = fetch_new_products(DATE_FILTER)
    print(f"    Найдено новых товаров: {len(products)}")

    if not products:
        print("    Нечего обновлять.")
        return

    stats = {"matched": 0, "not_found": 0, "prices_ok": 0, "inv_ok": 0, "errors": 0}

    print(f"\n[3] Обновляем цены и остатки...\n")

    for i, product in enumerate(products):
        title = product["title"]
        handle = product["handle"]
        our_variants = product.get("variants", [])

        print(f"[{i+1}/{len(products)}] {title}")

        time.sleep(DELAY)
        donor = fetch_donor_product(handle)

        if donor is None:
            print(f"  -> Не найден у донора")
            stats["not_found"] += 1
        else:
            stats["matched"] += 1
            donor_variants = donor.get("variants", [])

            for vi in range(min(len(our_variants), len(donor_variants))):
                our_v = our_variants[vi]
                donor_price = float(donor_variants[vi].get("price", 0))
                if donor_price <= 0:
                    continue
                new_price = nice_price(donor_price)
                compare_at = f"{donor_price:.2f}"
                print(f"  V{vi+1}: ${donor_price:.2f} -> ${new_price}")
                try:
                    api_put(f"/variants/{our_v['id']}.json", {
                        "variant": {
                            "id": our_v["id"],
                            "price": new_price,
                            "compare_at_price": compare_at,
                        }
                    })
                    stats["prices_ok"] += 1
                except Exception as e:
                    print(f"    ОШИБКА цены: {e}")
                    stats["errors"] += 1
                time.sleep(DELAY)

        # Set inventory for all variants
        for v in our_variants:
            try:
                api_post("/inventory_levels/set.json", {
                    "location_id": loc_id,
                    "inventory_item_id": v["inventory_item_id"],
                    "available": TARGET_INVENTORY,
                })
                stats["inv_ok"] += 1
            except Exception as e:
                print(f"    ОШИБКА остатка: {e}")
                stats["errors"] += 1
            time.sleep(DELAY)

    print("\n" + "=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print(f"  Новых товаров:       {len(products)}")
    print(f"  Найдено у донора:    {stats['matched']}")
    print(f"  Не найдено:          {stats['not_found']}")
    print(f"  Цен обновлено:       {stats['prices_ok']}")
    print(f"  Остатков выставлено: {stats['inv_ok']}")
    print(f"  Ошибок:              {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
