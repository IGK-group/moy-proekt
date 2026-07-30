#!/usr/bin/env python3
"""
import_taobao.py — импорт товара с Taobao в Shopify.
Бесплатно. Без подписок. Без токенов.

Использование:
    python3 import_taobao.py <taobao_url> [наценка_в_процентах]

Пример:
    python3 import_taobao.py "https://item.taobao.com/item.htm?id=123456" 150
"""
import sys
import os
import re
import json
import time
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

SHOP  = os.environ["SHOPIFY_SHOP"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
API   = f"https://{SHOP}/admin/api/2024-01"
MARKUP = float(sys.argv[2]) / 100 if len(sys.argv) > 2 else 2.5  # x2.5 по умолчанию

HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def taobao_id(url):
    m = re.search(r'[?&]id=(\d+)', url)
    return m.group(1) if m else None


def fetch_taobao(item_id):
    """Тянет данные через публичный Taobao API."""
    api_url = f"https://h5api.m.taobao.com/h5/mtop.taobao.item.get.app/4.0/?api=mtop.taobao.item.get.app&id={item_id}&appKey=12574478"
    req = urllib.request.Request(api_url, headers={"User-Agent": UA, "Referer": "https://item.taobao.com/"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fetch_via_html(url):
    """Запасной вариант — парсим HTML страницу."""
    try:
        from bs4 import BeautifulSoup
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")

        # Ищем JSON с данными товара
        match = re.search(r'g_page_config\s*=\s*(\{.+?\});', html, re.S)
        if match:
            data = json.loads(match.group(1))
            item = data.get("mods", {}).get("itemDetail", {}).get("data", {})
            if item:
                return {
                    "title": item.get("title", ""),
                    "price": float(item.get("price", "0").replace(",", ".")),
                    "images": item.get("images", [])[:10],
                    "description": item.get("detail", ""),
                }
    except Exception as e:
        print(f"HTML парсинг: {e}")
    return None


def translate_text(text):
    """Простой перевод через Google Translate (бесплатно, без ключа)."""
    if not text:
        return text
    try:
        text_enc = urllib.parse.quote(text[:500])
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={text_enc}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        translated = "".join([item[0] for item in result[0] if item[0]])
        return translated
    except Exception:
        return text


def nice_price(cny_price, markup):
    usd = cny_price / 7.2 * markup
    if usd < 50:
        return round(usd) - 0.01
    elif usd < 200:
        return round(usd / 5) * 5 - 0.01
    else:
        return round(usd / 10) * 10 - 0.01


def shopify_post(endpoint, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{API}/{endpoint}", data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"Shopify ошибка {e.code}: {e.read().decode()[:300]}")
        return None


def create_shopify_product(title_en, desc_en, price_usd, images, taobao_url):
    payload = {
        "product": {
            "title": title_en,
            "body_html": f"<p>{desc_en}</p><p><em>Sourced from China. Ships 10-18 days.</em></p>",
            "vendor": "MebelShop",
            "product_type": "Furniture",
            "tags": "taobao,furniture,china",
            "variants": [{
                "price": str(round(price_usd, 2)),
                "inventory_quantity": 20,
                "inventory_management": "shopify",
            }],
            "images": [{"src": img} for img in images[:10]],
            "metafields": [{
                "namespace": "custom",
                "key": "taobao_url",
                "value": taobao_url,
                "type": "single_line_text_field",
            }],
        }
    }
    return shopify_post("products.json", payload)


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 import_taobao.py <taobao_url> [наценка%]")
        sys.exit(1)

    url = sys.argv[1]
    item_id = taobao_id(url)
    if not item_id:
        print("Не могу найти ID товара в ссылке")
        sys.exit(1)

    print(f"Товар ID: {item_id}")
    print("Получаю данные с Taobao...")

    # Пробуем API
    data = fetch_via_html(url)

    if not data:
        print("Не удалось получить данные — Taobao требует авторизацию для этого товара")
        sys.exit(1)

    title_cn = data.get("title", "")
    price_cny = data.get("price", 0)
    images = data.get("images", [])
    desc_cn = data.get("description", "")

    print(f"Название (CN): {title_cn[:60]}")
    print(f"Цена (CNY): ¥{price_cny}")
    print(f"Фото: {len(images)} шт.")

    print("Перевожу на английский...")
    title_en = translate_text(title_cn)
    desc_en = translate_text(desc_cn) if desc_cn else "High quality furniture directly from Chinese manufacturer."

    price_usd = nice_price(float(price_cny), MARKUP)
    print(f"Цена в магазине (USD): ${price_usd}")
    print(f"Название (EN): {title_en[:60]}")

    print("Создаю товар в Shopify...")
    result = create_shopify_product(title_en, desc_en, price_usd, images, url)

    if result and result.get("product"):
        p = result["product"]
        print(f"\nТовар создан:")
        print(f"  ID: {p['id']}")
        print(f"  Название: {p['title']}")
        print(f"  Цена: ${p['variants'][0]['price']}")
        print(f"  Фото: {len(p['images'])} шт.")
        print(f"  Ссылка: https://{SHOP}/admin/products/{p['id']}")
    else:
        print("Ошибка создания товара")


if __name__ == "__main__":
    main()
