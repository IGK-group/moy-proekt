#!/usr/bin/env python3
"""
Создать в Shopify два товара, отобранных из каталога CJdropshipping
для активного потока "умные гаджеты" (см. plans/2026-08-09-cj-api-integration.md).

Отбор и цены - результат ручного анализа (см. retrospectives), не общий импорт:
    1. DYP Window Cleaning Robot (pid 1382262788063367168) - $85.65 COGS, 3 варианта вилки
    2. Yq16pro Smart Robot Vacuum-Mop (pid 2014591964245168129) - $88.00 COGS, auto-recharge, app control

Запуск:
    python3 cj_create_products.py
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SHOP = os.environ["SHOPIFY_SHOP"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")
TARGET_INVENTORY = int(os.getenv("TARGET_AVAILABLE", "22"))
LOCATION_ID = int(os.getenv("SHOPIFY_LOCATION_ID", "0"))

BASE_URL = f"https://{SHOP}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}
DELAY = 0.6
TIMEOUT = 30

PRODUCTS = [
    {
        "title": "DYP Automatic Window Cleaning Robot - Vacuum Suction Glass Cleaner",
        "body_html": (
            "<p>Hands-free window cleaning with real vacuum-suction climbing - no magnets, "
            "no second person needed on the other side of the glass.</p>"
            "<ul>"
            "<li>Vacuum adsorption climbing - holds securely on vertical glass</li>"
            "<li>Automatic glass-frame detection - stops before reaching the edge</li>"
            "<li>Remote control or fully automatic cleaning mode</li>"
            "<li>Anti-fall safety: backup UPS battery + safety rope included</li>"
            "<li>Cleans glass panels 35x35cm and larger, ~0.23 m2/min</li>"
            "<li>Universal voltage 100-240V - works worldwide</li>"
            "<li>Compact and light at 0.95kg</li>"
            "</ul>"
            "<p>Includes plug adapter for your region (EU / UK / US).</p>"
        ),
        "vendor": "CJdropshipping",
        "product_type": "Home Appliances",
        "tags": "cj-sourced, cj-pid-1382262788063367168, window-cleaning-robot, active-launch",
        "images": [
            {"src": "https://cf.cjdropshipping.com/1618391591141.jpg"},
            {"src": "https://cf.cjdropshipping.com/1618391591145.jpg"},
            {"src": "https://cf.cjdropshipping.com/1618391591146.jpg"},
            {"src": "https://cf.cjdropshipping.com/1618391591119.png"},
            {"src": "https://cf.cjdropshipping.com/1618391591112.jpg"},
        ],
        "options": [{"name": "Plug Standard", "values": ["EU", "UK", "US"]}],
        "variants": [
            {"option1": "EU", "price": "249.99", "compare_at_price": "329.99",
             "sku": "CJ-DYPWCR-EU", "inventory_management": "shopify"},
            {"option1": "UK", "price": "249.99", "compare_at_price": "329.99",
             "sku": "CJ-DYPWCR-UK", "inventory_management": "shopify"},
            {"option1": "US", "price": "249.99", "compare_at_price": "329.99",
             "sku": "CJ-DYPWCR-US", "inventory_management": "shopify"},
        ],
    },
    {
        "title": "Yq16pro Smart Robot Vacuum & Mop - App Control, Auto-Recharge",
        "body_html": (
            "<p>3-in-1 sweep, suction and mop robot with app control and automatic docking - "
            "set a schedule and let it run.</p>"
            "<ul>"
            "<li>4-level suction: Quiet (1000Pa) / Normal (2000Pa) / Strong (3000Pa) / Turbo (4000Pa)</li>"
            "<li>Auto-recharge - returns to the dock when battery drops below 20%</li>"
            "<li>App scheduling over WiFi, plus manual controls on the unit</li>"
            "<li>Gyroscope + path planning for full-room coverage, no dead zones</li>"
            "<li>Slim 7.8cm profile fits under sofas and beds</li>"
            "<li>100ml water tank covers up to 150 sq. meters per fill</li>"
            "<li>Dual collision protection + infrared anti-fall sensors</li>"
            "<li>Suitable for wood, tile, marble, laminate and short-pile carpet</li>"
            "</ul>"
            "<p>Includes EU / US / UK / AU plug adapter, charging dock and full accessory kit.</p>"
        ),
        "vendor": "CJdropshipping",
        "product_type": "Home Appliances",
        "tags": "cj-sourced, cj-pid-2014591964245168129, robot-vacuum-mop, active-launch",
        "images": [
            {"src": "https://cf.cjdropshipping.com/5aded186-a158-4c63-a6fc-3bac85783912.png"},
            {"src": "https://cf.cjdropshipping.com/6c864a8e-dbd7-4fbf-9378-952787f7f048.png"},
            {"src": "https://cf.cjdropshipping.com/81bf2935-c484-447a-9fd7-1fd7c559bac2.png"},
        ],
        "variants": [
            {"price": "279.99", "compare_at_price": "349.99",
             "sku": "CJ-YQ16PRO-WHT", "inventory_management": "shopify"},
        ],
    },
]


def api_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    while True:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        if not resp.ok:
            print("ERROR body:", resp.text[:500])
        resp.raise_for_status()
        return resp.json()


def api_get(url):
    while True:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp


def get_location_id():
    if LOCATION_ID:
        return LOCATION_ID
    resp = api_get(f"{BASE_URL}/locations.json")
    locations = resp.json().get("locations", [])
    if not locations:
        raise RuntimeError("Нет локаций в магазине")
    return locations[0]["id"]


def main():
    print("=" * 70)
    print("СОЗДАНИЕ ТОВАРОВ ИЗ CJ КАТАЛОГА")
    print("=" * 70)

    try:
        loc_id = get_location_id()
        print(f"Location ID: {loc_id}")
    except requests.exceptions.HTTPError as e:
        loc_id = None
        print(f"Нет доступа к locations.json ({e}) - остатки выставим отдельно после расширения scope.")

    created_products = []
    for product in PRODUCTS:
        print(f"\nСоздаём: {product['title']}")
        resp = api_post("/products.json", {"product": product})
        created = resp["product"]
        created_products.append(created)
        print(f"  -> product_id {created['id']}, handle {created['handle']}")

        if loc_id:
            for v in created["variants"]:
                time.sleep(DELAY)
                api_post("/inventory_levels/set.json", {
                    "location_id": loc_id,
                    "inventory_item_id": v["inventory_item_id"],
                    "available": TARGET_INVENTORY,
                })
                print(f"    variant {v['id']} ({v.get('title')}): остаток {TARGET_INVENTORY} выставлен")

        time.sleep(DELAY)

    print("\n" + "=" * 70)
    print("ГОТОВО")
    if not loc_id:
        print("Остатки НЕ выставлены (нет scope read_locations/write_inventory).")
        print("Product ID для повторного запуска inventory-шага:")
        for p in created_products:
            print(f"  {p['id']} - {p['title']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
