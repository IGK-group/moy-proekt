import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
SHOP = os.environ["SHOPIFY_SHOP"]
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
HEADERS = {"X-Shopify-Access-Token": TOKEN}
BASE = f"https://{SHOP}/admin/api/2024-01"

resp = requests.get(f"{BASE}/products.json?limit=250&fields=id,title,images", headers=HEADERS, timeout=30)
for p in resp.json()["products"]:
    print(f"\n=== {p['title']} (id={p['id']}) - {len(p['images'])} фото ===")
    for img in p["images"]:
        print(img["src"])
