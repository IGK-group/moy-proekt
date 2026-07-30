"""
Проверка реальной конкуренции на Amazon через рабочий live-эндпоинт
merchant/amazon/products/live/advanced (не через сломанный task_post/task_get).

Критерии 4/6 методологии: предложение vs спрос, доступность рынка новичку.
"""
import base64
import json
import urllib.request
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

CANDIDATES_TIER2 = [
    "weighted blanket",
    "student desk for students",
    "electric bike",
    "scalp massager for hair growth",
]

TOTAL_COST = 0.0


def load_env():
    env = {}
    for raw in ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("\"", "'"):
            v = v[1:-1]
        env[k] = v
    return env


def post(path, payload, cred):
    global TOTAL_COST
    req = urllib.request.Request(
        f"https://api.dataforseo.com{path}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Authorization": f"Basic {cred}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read())
    task = data.get("tasks", [{}])[0]
    TOTAL_COST += task.get("cost", 0) or 0
    return task


def analyze(keyword, cred):
    task = post(
        "/v3/merchant/amazon/products/live/advanced",
        [{"keyword": keyword, "location_code": 2840, "language_code": "en_US", "device": "desktop"}],
        cred,
    )
    if task.get("status_code") != 20000:
        print(f"{keyword}: ERROR {task.get('status_message')}")
        return

    result = (task.get("result") or [{}])[0]
    items = [i for i in (result.get("items") or []) if i.get("type") in ("amazon_serp", "amazon_paid")]
    organic = [i for i in items if i.get("type") == "amazon_serp"]
    paid = [i for i in items if i.get("type") == "amazon_paid"]

    prices = [i["price_from"] for i in items if i.get("price_from")]
    ratings = [i["rating"]["value"] for i in items if i.get("rating") and i["rating"].get("value")]
    reviews = [i["rating"]["votes_count"] for i in items if i.get("rating") and i["rating"].get("votes_count")]
    bought = [i["bought_past_month"] for i in items if i.get("bought_past_month")]
    amazon_choice = sum(1 for i in items if i.get("is_amazon_choice"))

    high_review_count = sum(1 for r in reviews if r and r > 1000)

    print(f"\n=== {keyword} ===")
    print(f"  найдено товаров: {len(items)} (органика: {len(organic)}, реклама: {len(paid)})")
    if prices:
        sp = sorted(prices)
        print(f"  цена: ${min(prices):.2f} - ${max(prices):.2f}, медиана ~${median(sp):.2f}")
    if reviews:
        sr = sorted(reviews)
        print(f"  отзывы: медиана {int(median(sr))}, макс {max(reviews)}")
        print(f"  товаров с >1000 отзывов (устоявшиеся игроки): {high_review_count} из {len(items)}")
    if bought:
        print(f"  'куплено за месяц' указано у {len(bought)} товаров, макс {max(bought)}+")
    if ratings:
        print(f"  средний рейтинг: {sum(ratings)/len(ratings):.2f}")
    print(f"  реклама в выдаче (amazon_paid): {len(paid)} из {len(items)} - {'высокая конкуренция за клики' if len(paid) > 10 else 'умеренная'}")

    top5 = sorted(items, key=lambda i: (i.get("rating") or {}).get("votes_count", 0) or 0, reverse=True)[:5]
    print("  топ-5 по числу отзывов:")
    for i in top5:
        r = i.get("rating") or {}
        bpm = f"{i.get('bought_past_month')}+ куплено/мес" if i.get("bought_past_month") else ""
        print(f"    - {i.get('title', '')[:55]:55s} | ${i.get('price_from', 0) or 0:>7.2f} | "
              f"{r.get('votes_count', 0):>6} отз | {r.get('value', 0)}★ | {bpm}")


def main():
    env = load_env()
    cred = base64.b64encode(f"{env['DATAFORSEO_LOGIN']}:{env['DATAFORSEO_PASSWORD']}".encode()).decode()

    for kw in CANDIDATES_TIER2:
        analyze(kw, cred)

    print(f"\n{'='*70}")
    print(f"ИТОГО потрачено: ${TOTAL_COST:.4f}")


if __name__ == "__main__":
    main()
