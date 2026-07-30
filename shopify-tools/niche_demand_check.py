"""
Проверка спроса и сезонности кандидатов-ниш через DataForSEO Keywords Data API.
Критерии 1-3 методологии: растущий рынок, сезонность, рост спроса.

Использование: python3 niche_demand_check.py
Читает DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD из .env в корне проекта.
"""
import base64
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

LOCATIONS = {
    "US": 2840,
    "UK": 2826,
    "DE": 2276,
    "FR": 2250,
}

CANDIDATES = [
    "weighted blanket",
    "humidifier",
    "space heater",
    "desk organizer",
    "led desk lamp",
    "dog sweater",
    "gua sha tool",
    "sleep mask",
]

TOTAL_COST = 0.0


def load_env():
    env = {}
    if not ENV_PATH.exists():
        raise SystemExit(".env not found at project root")
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


def auth_header(env):
    login = env.get("DATAFORSEO_LOGIN", "")
    password = env.get("DATAFORSEO_PASSWORD", "")
    return base64.b64encode(f"{login}:{password}".encode()).decode()


def post(path, payload, cred):
    req = urllib.request.Request(
        f"https://api.dataforseo.com{path}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {cred}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def search_volume(keywords, location_code, cred):
    global TOTAL_COST
    payload = [{
        "keywords": keywords,
        "location_code": location_code,
        "language_code": "en",
        "date_from": "2023-07-01",
    }]
    data = post("/v3/keywords_data/google_ads/search_volume/live", payload, cred)
    TOTAL_COST += data.get("cost", 0)
    task = data.get("tasks", [{}])[0]
    if task.get("status_code") != 20000:
        print(f"  ! task error: {task.get('status_message')}")
        return []
    return task.get("result") or []


def yoy_growth(monthly_searches):
    """Сравнивает одинаковые месяцы год к году (последние 3 полных месяца
    против тех же месяцев год назад) - убирает сезонность из расчёта роста."""
    if not monthly_searches:
        return None
    ms = sorted(monthly_searches, key=lambda m: (m["year"], m["month"]))
    by_ym = {(m["year"], m["month"]): m["search_volume"] for m in ms}
    latest_y, latest_m = ms[-1]["year"], ms[-1]["month"]

    recent_vals, prior_vals = [], []
    y, m = latest_y, latest_m
    for _ in range(3):
        recent_vals.append(by_ym.get((y, m)))
        py = y - 1
        prior_vals.append(by_ym.get((py, m)))
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    recent_vals = [v for v in recent_vals if v is not None]
    prior_vals = [v for v in prior_vals if v is not None]
    if not recent_vals or not prior_vals or sum(prior_vals) == 0:
        return None
    recent_avg = sum(recent_vals) / len(recent_vals)
    prior_avg = sum(prior_vals) / len(prior_vals)
    return ((recent_avg - prior_avg) / prior_avg) * 100


def seasonality(monthly_searches, current_month=7):
    """Пиковый месяц спроса + сколько месяцев осталось до входа в сезон
    (с учётом того, что старт сейчас - июль)."""
    if not monthly_searches:
        return None, None
    by_month = {}
    for m in monthly_searches:
        by_month.setdefault(m["month"], []).append(m["search_volume"])
    avg_by_month = {mo: sum(v) / len(v) for mo, v in by_month.items()}
    peak_month = max(avg_by_month, key=avg_by_month.get)
    months_to_peak = (peak_month - current_month) % 12
    return peak_month, months_to_peak


def main():
    env = load_env()
    cred = auth_header(env)

    print(f"Кандидаты: {len(CANDIDATES)} | Рынки: {', '.join(LOCATIONS)}")
    print("=" * 100)

    results = {kw: {} for kw in CANDIDATES}

    for market, loc_code in LOCATIONS.items():
        print(f"\n--- {market} (location_code={loc_code}) ---")
        try:
            rows = search_volume(CANDIDATES, loc_code, cred)
        except urllib.error.HTTPError as e:
            print(f"  HTTP ERROR {e.code}: {e.reason}")
            continue

        by_kw = {r["keyword"]: r for r in rows if r}
        for kw in CANDIDATES:
            r = by_kw.get(kw)
            if not r or r.get("search_volume") is None:
                print(f"  {kw:20s} -> нет данных")
                results[kw][market] = None
                continue
            ms_data = r.get("monthly_searches") or []
            growth_pct = yoy_growth(ms_data)
            peak_month, months_to_peak = seasonality(ms_data)
            results[kw][market] = {
                "volume": r.get("search_volume"),
                "competition": r.get("competition"),
                "cpc": r.get("cpc"),
                "yoy_growth_pct": growth_pct,
                "peak_month": peak_month,
                "months_to_peak": months_to_peak,
            }
            growth_str = f"{growth_pct:+.0f}%" if growth_pct is not None else "н/д"
            peak_str = datetime(2000, peak_month, 1).strftime("%b") if peak_month else "н/д"
            season_flag = "ВХОДИТ В СЕЗОН" if months_to_peak is not None and months_to_peak <= 2 else ""
            print(f"  {kw:20s} vol={r.get('search_volume'):>7} "
                  f"comp={str(r.get('competition')):6s} cpc=${r.get('cpc') or 0:5.2f} "
                  f"год-к-году={growth_str:>7} пик={peak_str:4s} {season_flag}")

    print("\n" + "=" * 100)
    print(f"ИТОГО потрачено на этот прогон: ${TOTAL_COST:.4f}")

    out_path = ROOT / "shopify-tools" / "niche_demand_results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Результаты сохранены: {out_path}")


if __name__ == "__main__":
    main()
