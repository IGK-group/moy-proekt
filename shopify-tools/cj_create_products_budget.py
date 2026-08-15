#!/usr/bin/env python3
"""
Второй заход по тем же двум нишам - более дешёвые (но проверенные легитимные,
не игрушечные) кандидаты из CJ, добавлены как бюджетная альтернатива к уже
созданным премиум-товарам (см. cj_create_products.py).

    1. Window Cleaning Robot (budget) - pid 2604270838171612800, $36.15 COGS,
       только US plug (W17S) - ограничение по рынку ЕС, см. описание.
    2. Black Robot Vacuum Mop 3-in-1 (budget) - pid 2013441167481827329, $43.40 COGS,
       <1000Pa, без auto-recharge/app - слабее премиум Yq16pro, но легитимный товар.

Отсеяны при отборе (не добавлены): товары <$10 COGS в этих нишах - проверены
через product/query и оказались игрушечными мини-пылесосами (287-300г, "random"
механический режим), не соответствуют товару, который ищут по запросу
"robot vacuum and mop" - риск возвратов/плохих отзывов.

Запуск:
    python3 cj_create_products_budget.py
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

BASE_URL = f"https://{SHOP}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}
DELAY = 0.6
TIMEOUT = 30

PRODUCTS = [
    {
        "title": "Compact Window Cleaning Robot - Spray & Wipe, Budget Pick",
        "body_html": (
            "<p>A lighter, more affordable window cleaning robot for spot cleaning "
            "and smaller glass surfaces - built-in 30ml spray reservoir for a wipe-and-clean pass.</p>"
            "<ul>"
            "<li>Built-in 30ml water spray tank</li>"
            "<li>Compact and lightweight design</li>"
            "<li>US plug (110-120V) - North America only</li>"
            "</ul>"
            "<p>Note: this is our budget option. For multi-plug (EU/UK/US) coverage and "
            "vacuum-suction climbing with auto glass-frame detection, see our "
            "DYP Automatic Window Cleaning Robot.</p>"
        ),
        "vendor": "CJdropshipping",
        "product_type": "Home Appliances",
        "tags": "cj-sourced, cj-pid-2604270838171612800, window-cleaning-robot, active-launch, budget-tier",
        "images": [
            {"src": "https://oss-cf.cjdropshipping.com/product/2026/04/27/08/dbe18bca-d830-4dca-bbe7-12d898e7a553_water.jpeg"},
            {"src": "https://oss-cf.cjdropshipping.com/product/2026/04/27/08/eaa89a9e-86e8-4e91-bdb3-7883ba9a7d73_water.jpeg"},
            {"src": "https://oss-cf.cjdropshipping.com/product/2026/04/27/08/faa2829b-a7d5-448c-9bb6-1d6f92516947_water.jpeg"},
            {"src": "https://oss-cf.cjdropshipping.com/product/2026/04/27/08/33059e3f-cf46-4416-ba4f-5aaed8c373c1_water.jpeg"},
        ],
        "variants": [
            {"price": "129.99", "compare_at_price": "179.99",
             "sku": "CJ-WCR-BUDGET-US", "inventory_management": "shopify"},
        ],
    },
    {
        "title": "Black Robot Vacuum Mop 3-in-1 - Budget Pick",
        "body_html": (
            "<p>An entry-level 3-in-1 robot that sweeps, vacuums and mops - a lighter, "
            "more affordable way to try automated floor cleaning.</p>"
            "<ul>"
            "<li>3-in-1: sweeping, vacuuming and mopping in one pass</li>"
            "<li>Scheduled cleaning timer</li>"
            "<li>Covers up to 90 sq. meters with random-path navigation</li>"
            "<li>USB rechargeable, quiet operation under 36dB</li>"
            "<li>Low-voltage safety protection</li>"
            "</ul>"
            "<p>Note: this is our budget option (no auto-recharge, no app control). "
            "For 4-level suction, auto-recharge and WiFi app scheduling, see our "
            "Yq16pro Smart Robot Vacuum & Mop.</p>"
        ),
        "vendor": "CJdropshipping",
        "product_type": "Home Appliances",
        "tags": "cj-sourced, cj-pid-2013441167481827329, robot-vacuum-mop, active-launch, budget-tier",
        "images": [
            {"src": "https://cf.cjdropshipping.com/e8398bd9-d2f9-4948-b03f-1ae42fd8b425.png"},
            {"src": "https://cf.cjdropshipping.com/7a855a92-0526-413f-bc54-a1d49626be10.jfif"},
            {"src": "https://cf.cjdropshipping.com/db8853b0-4bfc-42cb-92a0-2aeccb8415f7.png"},
        ],
        "variants": [
            {"price": "149.99", "compare_at_price": "199.99",
             "sku": "CJ-RVM-BUDGET-BLK", "inventory_management": "shopify"},
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


def get_location_id():
    """location_id без read_locations scope - через inventory_levels любого товара."""
    resp = requests.get(f"{BASE_URL}/products.json?limit=1&fields=id,variants", headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    products = resp.json().get("products", [])
    inv_item_id = products[0]["variants"][0]["inventory_item_id"]
    resp2 = requests.get(f"{BASE_URL}/inventory_levels.json?inventory_item_ids={inv_item_id}", headers=HEADERS, timeout=TIMEOUT)
    resp2.raise_for_status()
    return resp2.json()["inventory_levels"][0]["location_id"]


def main():
    print("=" * 70)
    print("СОЗДАНИЕ БЮДЖЕТНЫХ АЛЬТЕРНАТИВ ИЗ CJ КАТАЛОГА")
    print("=" * 70)

    loc_id = get_location_id()
    print(f"Location ID: {loc_id}")

    for product in PRODUCTS:
        print(f"\nСоздаём: {product['title']}")
        resp = api_post("/products.json", {"product": product})
        created = resp["product"]
        print(f"  -> product_id {created['id']}, handle {created['handle']}")

        for v in created["variants"]:
            time.sleep(DELAY)
            api_post("/inventory_levels/set.json", {
                "location_id": loc_id,
                "inventory_item_id": v["inventory_item_id"],
                "available": TARGET_INVENTORY,
            })
            print(f"    variant {v['id']}: остаток {TARGET_INVENTORY} выставлен")

        time.sleep(DELAY)

    print("\n" + "=" * 70)
    print("ГОТОВО")
    print("=" * 70)


if __name__ == "__main__":
    main()
