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

**Раньше был случай "Review your security settings"** при входе через AdsPower - это НЕ повод переходить на реальный IP, скорее всего дело было в закончившемся балансе/лимите прокси, не в самом факте антидетекта (см. `content-factory/payments-risks.md` про баланс IPRoyal/прокси).

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

## Текущий статус (на 2026-06-30)

- [x] OAuth подключение работает
- [x] API токен активен
- [x] Скрипты готовы
- [ ] Товары в магазин не добавлены
- [ ] Магазин-донор не задан (SOURCE_STORE_DOMAIN пустой)
- [ ] Витрина закрыта паролем (Opening soon)
