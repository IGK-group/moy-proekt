#!/usr/bin/env python3
"""
Выставить остаток TARGET_AVAILABLE для ВСЕХ вариантов ВСЕХ товаров в магазине.

Используется при первом запуске магазина или для полного сброса остатков.
Для дропшиппинга: постоянно держим "в наличии" фиксированное количество.

Запуск:
    python3 set_inventory.py

Переменные в .env:
    SHOPIFY_SHOP, SHOPIFY_ACCESS_TOKEN, TARGET_AVAILABLE, SHOPIFY_LOCATION_ID
"""

import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SHOP = os.environ["SHOPIFY_SHOP"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
TARGET_INVENTORY = int(os.getenv("TARGET_AVAILABLE", "22"))
LOCATION_ID = int(os.getenv("SHOPIFY_LOCATION_ID", "0"))
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")

BASE_URL = f"https://{SHOP}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}
DELAY = 1.0
TIMEOUT = 30


def api_get(url, params=None):
    while True:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            print(f"  [429] Ждём {wait}с...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp


def api_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    while True:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            print(f"  [429] Ждём {wait}с...")
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


def fetch_all_products():
    products = []
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,variants"
    while url:
        print(f"  Загружаем страницу... (уже {len(products)} товаров)")
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


def main():
    print("=" * 70)
    print(f"ВЫСТАВИТЬ ОСТАТКИ: {TARGET_INVENTORY} шт для всех вариантов")
    print(f"Магазин: {SHOP}")
    print("=" * 70)

    print("\n[1] Получаем location ID...")
    loc_id = get_location_id()
    time.sleep(DELAY)

    print("\n[2] Загружаем все товары...")
    products = fetch_all_products()
    print(f"    Итого товаров: {len(products)}")

    variants = []
    for p in products:
        for v in p.get("variants", []):
            variants.append({
                "title": p["title"],
                "variant_id": v["id"],
                "inventory_item_id": v["inventory_item_id"],
            })
    print(f"    Итого вариантов: {len(variants)}")

    print(f"\n[3] Выставляем остаток {TARGET_INVENTORY} для каждого варианта...")
    success = 0
    errors = 0

    for i, v in enumerate(variants, 1):
        try:
            api_post("/inventory_levels/set.json", {
                "location_id": loc_id,
                "inventory_item_id": v["inventory_item_id"],
                "available": TARGET_INVENTORY,
            })
            success += 1
        except Exception as e:
            errors += 1
            print(f"  ОШИБКА {v['variant_id']} ({v['title']}): {e}")

        if i % 50 == 0:
            print(f"  Прогресс: {i}/{len(variants)} ({success} ok, {errors} ошибок)")

        time.sleep(DELAY)

    print("\n" + "=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print(f"  Товаров:           {len(products)}")
    print(f"  Вариантов:         {len(variants)}")
    print(f"  Успешно:           {success}")
    print(f"  Ошибок:            {errors}")
    print(f"  Остаток выставлен: {TARGET_INVENTORY}")
    print("=" * 70)


if __name__ == "__main__":
    main()
