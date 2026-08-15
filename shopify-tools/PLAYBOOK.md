# Shopify Tools - Полный плейбук запуска

Всё что нужно знать чтобы запустить проект с нуля. Читай в начале каждой сессии.

## Магазин

| | |
|---|---|
| Админка | `admin.shopify.com/store/ghnjxs-hh` |
| Витрина | `ghnjxs-hh.myshopify.com` |
| Email аккаунта | igk-group@mail.ru |
| Статус | Пароль включён (Opening soon) - витрина закрыта для посетителей |

## Как входить в Shopify Admin

**Подтверждено:** магазин был создан через AdsPower (профиль "store 1", Socks5 USA/NY) - аккаунт "держится" на этом прокси, то есть Shopify связывает identity магазина с этим IP/фингерпринтом. Входить нужно **через AdsPower, профиль "store 1"**, не с произвольного/реального IP - смена IP относительно того, на котором магазин создавался, сама по себе может выглядеть подозрительно для антифрода Shopify.

Причина логична и с учётом статуса Гены: гражданин Беларуси, физически в Китае. Заход напрямую с китайского IP при белорусских данных аккаунта - несовпадение, которое антифрод-системы отслеживают (см. риски в `content-factory/payments-risks.md`). AdsPower с американским прокси даёт консистентную identity, с которой магазин и был зарегистрирован.

**Раньше был случай "Review your security settings"** при входе через AdsPower - это НЕ повод переходить на реальный IP, скорее всего дело было в закончившемся балансе/лимите прокси, не в самом факте антидетекта.

**Прокси профиля "store 1" - провайдер Astro (astroproxy.com), НЕ IPRoyal** (IPRoyal - это отдельный пул прокси для content-factory/GeeLark, не путать). Подтверждено 2026-08-09: "пропал интернет" на профиле "store 1" был вызван исчерпанным прогреваемым трафиком (Prepaid traffic, 102.4MB лимит, использовано 205.1MB) - порт ушёл в Astro "Archived ports". Проверка: astroproxy.com -> Прокси -> Active/Archived ports -> "Traffic consumption: Left". Чинится через "Renew selected" с баланса аккаунта Astro (login gendosku@g...).

**Порядок входа:**
- Перед входом - убедиться, что на прокси AdsPower ("store 1") есть баланс/оплаченный лимит.
- Заходить только через этот профиль AdsPower, не через обычный браузер с реального IP.
- Если появится "Review your security settings" - нажать **"Remind me next time"** внизу, это не блокировка.
- Если попал на витрину (Opening soon) - нажать **"Log in here"** внизу страницы.

## Как работает подключение Claude к магазину

Подключение через OAuth (Partner App в Dev Dashboard):

- Приложение: **shop1** в dev.shopify.com/dashboard/224306950/apps/391227179009
- Client ID: `10f186538a54da4b09953caecca9db7b`
- Токен получен 2026-06-30 через OAuth flow (`get_token.py`)
- Токен хранится в `shopify-tools/.env` как `SHOPIFY_ACCESS_TOKEN`
- Scopes: read/write products, inventory, content, themes, orders, markets

### Если токен протух (ошибка 401)

Запусти процедуру переполучения токена:

```bash
cd shopify-tools/
python3 get_token.py
```

Скрипт напечатает ссылку - открой в браузере, подтверди установку.
Если браузер не открывается автоматически - скопируй URL из консоли вручную.
После авторизации токен автоматически обновится в `.env`.

**Важно про redirect_uri:** `get_token.py` слушает `localhost:3456` на машине, где выполняется Bash Claude Code. Если вход в Shopify Admin происходит через AdsPower на ДРУГОЙ машине (например, отдельный Windows-компьютер, а Claude Code - на сервере), колбэк на `localhost:3456` физически не дойдёт - браузер AdsPower покажет `ERR_CONNECTION_REFUSED`, потому что "localhost" для него - это его собственная машина. Признак, что авторизация всё равно прошла: в адресной строке будет `localhost:3456/callback?code=...&hmac=...`. В этом случае - скопировать код из URL вручную и обменять его на токен напрямую (`POST /admin/oauth/access_token` с `client_id`, `client_secret`, `code`), не дожидаясь колбэка.

**Важно про scope:** приложение **shop1** в Partner Dashboard, судя по всему, само определяет полный набор выдаваемых прав при установке - `SHOPIFY_OAUTH_SCOPES` в `.env` влияет не на 100% ("read_locations" запрашивался явно, но выдан не был: `403 [API] This action requires merchant approval for read_locations scope` - этот scope нужно сначала добавить в конфигурацию приложения в dev.shopify.com/dashboard, не только в URL авторизации). **Обходной путь без read_locations:** location_id можно получить через `GET /inventory_levels.json?inventory_item_ids=<id>` (есть у любого товара) - в ответе есть `location_id`, эндпоинт работает при наличии `write_inventory`/`read_inventory`, `/locations.json` не нужен.

Если get_token.py не запускается - проверь `.env`:
```
SHOPIFY_CLIENT_ID=10f186538a54da4b09953caecca9db7b
SHOPIFY_CLIENT_SECRET=...             # см. shopify-tools/.env, не хранить значение здесь
SHOPIFY_SHOP=ghnjxs-hh.myshopify.com
SHOPIFY_AUTH_REDIRECT=http://localhost:3456/callback
```

### Проверить что соединение работает

```bash
cd shopify-tools/
python3 -c "
from dotenv import load_dotenv
import os, requests
load_dotenv()
shop = os.environ['SHOPIFY_SHOP']
token = os.environ['SHOPIFY_ACCESS_TOKEN']
resp = requests.get(f'https://{shop}/admin/api/2024-01/shop.json', headers={'X-Shopify-Access-Token': token})
print(resp.json()['shop']['name'])
"
```

## Переменные .env

```
SHOPIFY_SHOP=ghnjxs-hh.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_...        # активный токен
SHOPIFY_API_VERSION=2024-01
SHOPIFY_LOCATION_ID=0                 # 0 = автоопределение
TARGET_AVAILABLE=22                   # остаток для дропшиппинга

SOURCE_STORE_DOMAIN=                  # домен магазина-донора (не задан)
DISCOUNT=0.90                         # 0.90 = -10% от цены донора

SHOPIFY_CLIENT_ID=10f186538a54da4b09953caecca9db7b
SHOPIFY_CLIENT_SECRET=...             # см. shopify-tools/.env, не хранить значение здесь
SHOPIFY_AUTH_REDIRECT=http://localhost:3456/callback
SHOPIFY_OAUTH_SCOPES=read_products,write_products,read_inventory,write_inventory,read_content,write_content
```

## Скрипты - порядок первого запуска

```bash
cd shopify-tools/

# 1. Установить зависимости (один раз)
pip3 install -r requirements.txt --break-system-packages

# 2. Выставить остатки для всех товаров (первый запуск)
python3 set_inventory.py

# 3. Обновить цены по донору
python3 update_prices.py

# 4. Ежедневно - новые товары
python3 update_new_products.py
```

## AdsPower - антидетект браузер

- Профиль: **store 1**, Profile ID: k1e0pbin
- Прокси: Socks5, USA / New York (172.56.163.173)
- Запуск: через интерфейс AdsPower, кнопка "Start"

**Назначение (подтверждено) - создание и вход в Shopify Admin.** Магазин был создан через этот профиль, аккаунт держится на этом прокси - не менять IP произвольно. Это НЕ инструмент контент-завода - для GeeLark-профилей соцсетей используется отдельный набор прокси/аккаунтов, см. `content-factory/architecture.md`.

## Как Shopify связан с остальными системами

```
Контент-завод (GeeLark -> соцсети -> Linktree)
        ↓ трафик покупателей
Shopify-магазин ghnjxs-hh.myshopify.com  <-- Claude управляет через API
        ↓ заказ
Гена закупает у фабрики и доставляет
```

| Система | Связь с Shopify | Где детали |
|---|---|---|
| Контент-завод / GeeLark | Гонит трафик в магазин через Linktree | `../content-factory/INDEX.md` |
| AdsPower "store 1" | Браузерный вход в Shopify Admin | этот файл, секция выше |
| Claude / shopify-tools | Читает/пишет товары, цены, остатки через API | этот файл |
| Higgsfield | Видеоконтент для соцсетей -> трафик в магазин | `../ai-clone/reference/README.md` |
| CLAUDE.md | Таблица всех активных подключений | `../CLAUDE.md` секция "Активные подключения" |

## Платежи - Shopify Payments (настроено 2026-07-31)

Активная business entity: **Ilya Myshalou (Canada)**

| Параметр | Значение |
|---|---|
| Entity | Ilya Myshalou |
| Страна | Canada |
| Адрес | 2333 Street NW, Edmonton, Alberta T6K 3H1 |
| Дата рождения | August 10, 1983 |
| Тип | Individual |
| Статус | **АКТИВЕН** - банковские реквизиты заполнены, Shopify Payments подключён |

**Важно:** Магазин имеет две entity:
- `My Store - entity` (United States) - деактивирована
- `Ilya Myshalou` (Canada) - активная, используется для Shopify Payments

## Закупка и логистика - CJdropshipping (установлено 2026-08-09)

Приложение **CJdropshipping: Much Faster** установлено в магазине (`app_installations/app/cucheng`). Роль: **полная замена ручной закупки на 1688/Taobao** для активного потока (умные гаджеты, см. `business/products/overview.md`) - CJ сам находит поставщика, закупает и отгружает по заказу. Это осознанный пересмотр модели, а не тест: живая съёмка с конкретных фабрик для этого потока не планируется (см. `business/INDEX.md` про два потока), контент - AI-хук + демо-видео поставщика.

Для потока "мебель" (на паузе) сорсинг остаётся отдельным вопросом на момент его запуска - см. `plans/2026-08-01-usa-dropship-store.md`, где CJ фигурирует только как один из поставщиков США-склада для ниши текстиля в другом магазине, это не то же самое приложение/решение.

- [x] Первые 2 карточки созданы через CJ API напрямую (не через встроенный импорт приложения) - см. `plans/2026-08-09-cj-api-integration.md`
- [ ] Настроить каталог/синхронизацию товаров CJ -> Shopify для масштабирования (сейчас процесс ручной-аналитический, скрипт `cj_create_products.py` хардкодит 2 товара)
- [ ] Проверить условия оплаты и реальные сроки доставки CJ до США/Европы (оба выбранных товара - склад CN, не US, расчёт в плане пока оценочный)
- [x] Сверился - оба выбранных товара соответствуют window cleaning robot / robot vacuum из `business/products/niche-candidates.md`

## Доставка - Shipping profiles (проверено 2026-08-09)

**Важно про API:** легаси REST-эндпоинт `/admin/api/2024-01/shipping_zones.json` **не показывает** тарифы, настроенные через современную систему "Shipping profiles" (Settings -> Shipping and delivery) - поля `price_based_shipping_rates`/`weight_based_shipping_rates` в его ответе были пустые, хотя реальные тарифы в магазине есть. Проверять тарифы доставки только глазами в Admin UI (Settings -> Shipping and delivery -> General profile) или через GraphQL (`deliveryProfile`), не через этот REST-эндпоинт - иначе можно ошибочно решить, что тариф не настроен, и создать дубль.

Один профиль **"General profile"** (Store default) на все товары, 2 зоны:

| Зона | Способ | Срок | Цена |
|---|---|---|---|
| **Domestic (United States)** | Express | 1-2 дня | $15.00 |
| Domestic (United States) | Standard | 3-5 дней | $8.00, **бесплатно от $70** |
| **International** (EU/UK + ещё 24 страны) | через carrier (похоже на USPS) | - | не проверено визуально, только видно что carrier-провайдер подключён |

Все 4 CJ-товара стоят $129.99-$279.99 - выше порога $70, значит покупатель из США всегда увидит Standard-доставку бесплатной. Согласуется с моделью `unit_economics.py` (стоимость фрахта уже заложена внутрь цены товара, не выставляется отдельно).

Открыто: тарифы International не проверены визуально (только подтверждено через API, что carrier-provider подключён) - стоит свериться в Admin UI аналогично Domestic.

## Текущий статус (обновлено 2026-08-09)

- [x] OAuth подключение работает
- [x] API токен активен
- [x] Скрипты готовы
- [x] Канадская business entity создана (Ilya Myshalou, Edmonton AB)
- [x] Shopify Payments переключён на канадскую entity
- [x] Shopify Payments активен - банковские реквизиты заполнены
- [ ] Товары в магазин не добавлены
- [ ] Магазин-донор не задан (SOURCE_STORE_DOMAIN пустой)
- [ ] Витрина закрыта паролем (Opening soon)
