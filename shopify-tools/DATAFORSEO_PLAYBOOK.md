# DataForSEO - плейбук аналитики

ЧИТАТЬ ПЕРВЫМ для любой задачи про аналитику, поиск ниш, анализ конкурентов, трафик чужих сайтов.

## Подключение

- Аккаунт: login `pervayacena5@gmail.com`, зарегистрирован на **app.dataforseo.com** (проверен как настоящий домен DataForSEO, не подделка - см. историю в retrospectives, если нужны подробности проверки).
- Ключи в `shopify-tools/.env`: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`.
- Никогда не читать `.env` целиком - только `process.env.DATAFORSEO_LOGIN` / `process.env.DATAFORSEO_PASSWORD` в коде.
- Баланс пополняется вручную Геной через app.dataforseo.com, минимум $50 за раз. На конец сессии 2026-07-15 - около $41.
- Оплата: работает и с китайскими платёжными реквизитами, без проблем с санкциями (в отличие от Беларуси - Stripe/Paddle блокируют белорусские реквизиты).

## Рабочие эндпоинты (проверено)

Все запросы - `Basic Auth` = `base64(login:password)`, `Content-Type: application/json`.

### Спрос и сезонность
```
POST https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live
Body: [{"keywords": [...], "location_code": 2840, "language_code": "en", "date_from": "2023-07-01"}]
```
Даёт `search_volume`, `competition`, `cpc`, `monthly_searches` (по месяцам - считать год-к-году и сезонность самостоятельно, не доверять готовому полю `search_volume_trend` без перепроверки - оно один раз разошлось с прямым расчётом в 5+ раз). location_code: США=2840, UK=2826, Германия=2276, Франция=2250.

### Открытие кандидатов (related keywords)
```
POST https://api.dataforseo.com/v3/dataforseo_labs/google/related_keywords/live
Body: [{"keyword": "seed слово", "location_code": 2840, "language_code": "en", "depth": 2, "limit": 200}]
```
Даёт связанные запросы с готовым `search_volume_trend.yearly` - использовать только как наводку для лонглиста, не как финальное число (перепроверять через `search_volume/live` с точной формулировкой - важно: **точная формулировка/порядок слов имеет значение**, "waterproof outdoor lights led" и "outdoor led lights waterproof" дают разные данные).

### Конкуренция на Amazon (рабочий, синхронный)
```
POST https://api.dataforseo.com/v3/merchant/amazon/products/live/advanced
Body: [{"keyword": "...", "location_code": 2840, "language_code": "en_US", "device": "desktop"}]
```
Даёт до ~100+ товаров мгновенно: `price_from`, `rating.value`, `rating.votes_count`, `bought_past_month`, тип (`amazon_serp`=органика / `amazon_paid`=реклама). **Медиана `votes_count` по выдаче - главный индикатор насыщенности ниши.**

### Конкуренция в Google Shopping (асинхронный, был сломан, починили 2026-07-15)
```
POST .../v3/merchant/google/products/task_post   -> {"id": "..."}
GET  .../v3/merchant/google/products/task_get/advanced/{id}
```
Standard-очередь - до 45 минут, Priority (`"priority": 2` в payload) - до 1 минуты, дороже. Если снова падает с `Internal SE Server Error` - писать в чат поддержки на app.dataforseo.com с id задачи текстом.

### Анализ чужого сайта (домен целиком)
```
POST https://api.dataforseo.com/v3/dataforseo_labs/google/domain_rank_overview/live
Body: [{"target": "domain.com", "location_code": 2840, "language_code": "en"}]
```
Даёт органический+платный трафик Google (`etv`, `count` ключевых слов, `estimated_paid_traffic_cost`), распределение по позициям. **НЕ даёт выручку/заказы/прибыль - таких данных не существует ни у одного публичного источника, никогда не показывать точную цифру, только диапазон** (см. `feedback_unverified_analytics_tools` в памяти Claude).

```
POST https://api.dataforseo.com/v3/domain_analytics/whois/overview/live
Body: [{"filters": [["domain", "=", "domain.com"]]}]
```
Даёт возраст домена, регистратора.

## Не работает / не нужно

- `merchant/google/sellers`, `merchant/amazon/products` (task_post-версия) - другая схема параметров, не адаптировано.
- Meta Ads Library, TikTok Creative Center - нет API вообще, только руками в браузере.
- Точная выручка/прибыль/заказы чужого магазина - не существует ни у одного сервиса, включая платные (Owler, Store Leads и т.п. - та же прикидка трафик×конверсия, только без честного disclaimer).

## Готовые скрипты в этой папке

- `niche_demand_check.py` - спрос по списку кандидатов на 4 рынках
- `competition_check.py` - конкуренция на Amazon по списку кандидатов
- `unit_economics.py` - расчёт прибыли на заказ (себестоимость+фрахт+пошлина+3PL+CAC)
- `store_tracker.py <domain>` - честный анализ чужого сайта

## Итоги разведки ниш - см. `business/products/niche-candidates.md`

Не пересобирать методологию заново в новой сессии - там уже финальный список с юнит-экономикой.
