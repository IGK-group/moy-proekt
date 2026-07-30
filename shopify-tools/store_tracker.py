"""
Честный трекер магазина-конкурента: только реально измеримые данные.

Не показывает выдуманные "выручка/прибыль/заказы" - только то, что можно
подтвердить через DataForSEO (органика + платный поиск Google) и открытые
источники (соцсети, отзывы). Опциональная расчётная выручка помечается явно
как оценка, не факт.

Использование: python3 store_tracker.py <domain>
"""
import base64
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


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


def domain_overview(domain, cred, location_code=2840):
    req = urllib.request.Request(
        "https://api.dataforseo.com/v3/dataforseo_labs/google/domain_rank_overview/live",
        data=json.dumps([{"target": domain, "location_code": location_code, "language_code": "en"}]).encode(),
        method="POST",
        headers={"Authorization": f"Basic {cred}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    task = data.get("tasks", [{}])[0]
    if task.get("status_code") != 20000:
        return None, task.get("status_message"), task.get("cost", 0)
    items = (task.get("result") or [{}])[0].get("items") or []
    return (items[0]["metrics"] if items else None), None, task.get("cost", 0)


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 store_tracker.py <domain>")
        sys.exit(1)
    domain = sys.argv[1].replace("https://", "").replace("http://", "").strip("/")

    env = load_env()
    cred = base64.b64encode(f"{env['DATAFORSEO_LOGIN']}:{env['DATAFORSEO_PASSWORD']}".encode()).decode()

    print(f"{'='*70}")
    print(f"ЧЕСТНЫЙ ОТЧЁТ: {domain}")
    print(f"{'='*70}")
    print("(только измеримые данные - без выдуманных выручки/прибыли/заказов)\n")

    metrics, err, cost = domain_overview(domain, cred)
    if err:
        print(f"Ошибка DataForSEO: {err}")
    elif metrics:
        org = metrics["organic"]
        paid = metrics["paid"]
        print("ОРГАНИЧЕСКИЙ ПОИСК (Google):")
        print(f"  Ключевых слов в топ-100: {org['count']}")
        print(f"  Оценка трафика (ETV): {org['etv']:.0f}/мес")
        print(f"  Эквивалент в рекламном бюджете: ${org['estimated_paid_traffic_cost']:.2f}/мес")
        print()
        print("ПЛАТНЫЙ ПОИСК (Google Ads):")
        if paid["count"] > 0:
            print(f"  Ключевых слов в рекламе: {paid['count']}")
            print(f"  Оценка расходов: ${paid['estimated_paid_traffic_cost']:.2f}/мес")
        else:
            print("  Не рекламируются в Google Ads (0 ключевых слов)")
        print()
        print("  ПРИМЕЧАНИЕ: нет данных по Google Ads не значит 'нет рекламы вообще' -")
        print("  трафик может идти через Meta/TikTok, куда у нас нет API-доступа.")

    print(f"\n(стоимость запроса: ${cost:.4f})")
    print()
    print("СОЦСЕТИ И РЕПУТАЦИЯ: искать отдельно через WebSearch по названию бренда")
    print("(это не автоматизировано в скрипте - соцсети не имеют предсказуемого API")
    print(" для поиска по домену, нужен разовый поиск по имени бренда)")


if __name__ == "__main__":
    main()
