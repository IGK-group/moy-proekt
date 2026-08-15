"""
Юнит-экономика по топ-кандидатам ниш.
Единая методология для честного сравнения между нишами разного габарита.

Все цифры - оценки на основе категории товара (вес/габарит/себестоимость),
НЕ проверены напрямую у фабрик - см. предупреждение в выводе.
"""

PAYMENT_FEE_PCT = 0.029
PAYMENT_FEE_FIXED = 0.30
SUPPLIER_TRANSFER_FEE_PCT = 0.03
US_DUTY_PCT = 0.30  # усреднённая оценка, требует проверки по реальному HTS-коду

# Стратегия - органика (content-factory/GeeLark), НЕ платная реклама, см. business/marketing/channels.md
# (все платные каналы там помечены "планируется, CAC не определено").
# ORGANIC_CAC - плановая оценка из content-factory/architecture.md ("CAC (органика) ~$10"),
# выведена под мебельный поток ($300 чек, живые видео с фабрик), НЕ подтверждена для
# гаджет-потока и НЕ измерена фактически - контент-завод (GeeLark) ещё не подключён
# (см. CLAUDE.md "Активные подключения"). Использовать как ориентир, не как факт.
ORGANIC_CAC = 10.0

# (ниша, цена продажи, % COGS от цены, фрахт на ед., 3PL сборка+хранение, доставка последней мили, категория-габарит)
NICHES = [
    ("Window cleaning robot", 130, 0.22, 9, 4, 8, "малый-средний"),
    ("Monitor light bar", 40, 0.20, 2.5, 1.5, 5, "малый"),
    ("Inflatable paddle board", 150, 0.30, 25, 5, 18, "крупный/объёмный"),
    ("Neck massager", 45, 0.20, 2, 1.5, 5, "малый"),
    ("Single dose coffee grinder", 70, 0.25, 6, 2.5, 7, "средний"),
    ("Cable management tray", 22, 0.25, 2, 1, 5, "малый"),
    ("Handheld vacuum sealer", 32, 0.25, 3, 2, 6, "малый"),
    ("Humidifier for bedroom", 38, 0.22, 5, 2, 7, "средний"),
    ("Robot vacuum and mop", 280, 0.25, 20, 5, 12, "средний-тяжёлый"),
    ("Air fryer liners (бандл)", 15, 0.25, 1, 1, 4, "малый"),
]


def calc(name, price, cogs_pct, freight, threepl, last_mile, size):
    cogs = price * cogs_pct
    duty = (cogs + freight) * US_DUTY_PCT
    payment_fee = price * PAYMENT_FEE_PCT + PAYMENT_FEE_FIXED
    supplier_fee = cogs * SUPPLIER_TRANSFER_FEE_PCT

    total_costs = cogs + freight + duty + threepl + last_mile + payment_fee + supplier_fee
    margin = price - total_costs
    margin_pct = margin / price * 100

    cac = ORGANIC_CAC
    profit = margin - cac
    max_sustainable_cac = margin  # сколько можно потратить на привлечение и остаться в нуле

    return {
        "name": name, "price": price, "size": size,
        "cogs": cogs, "freight": freight, "duty": duty,
        "3pl": threepl, "last_mile": last_mile,
        "payment_fee": payment_fee, "supplier_fee": supplier_fee,
        "total_costs": total_costs, "margin": margin, "margin_pct": margin_pct,
        "cac": cac, "profit": profit, "max_sustainable_cac": max_sustainable_cac,
    }


def main():
    results = [calc(*n) for n in NICHES]
    results.sort(key=lambda r: -r["profit"])

    print(f"{'Ниша':<28} {'Цена':>7} {'Маржа%':>8} {'CAC(орг.)':>10} {'Прибыль/зак.':>13} {'Запас на CAC':>13}")
    print("-" * 90)
    for r in results:
        print(f"{r['name']:<28} ${r['price']:>5.0f}  {r['margin_pct']:>6.1f}%  "
              f"${r['cac']:>8.2f}  ${r['profit']:>11.2f}  ${r['max_sustainable_cac']:>11.2f}")

    print()
    print("=" * 90)
    print("Детализация по каждой позиции:")
    for r in results:
        print(f"\n--- {r['name']} (цена ${r['price']}, габарит: {r['size']}) ---")
        print(f"  Себестоимость 1688:      -${r['cogs']:.2f}")
        print(f"  Фрахт:                   -${r['freight']:.2f}")
        print(f"  Пошлина США (~30%):      -${r['duty']:.2f}")
        print(f"  3PL хранение+сборка:     -${r['3pl']:.2f}")
        print(f"  Доставка последней мили: -${r['last_mile']:.2f}")
        print(f"  Комиссия оплаты клиента: -${r['payment_fee']:.2f}")
        print(f"  Комиссия перевода фабрике:-${r['supplier_fee']:.2f}")
        print(f"  ИТОГО расходов:          -${r['total_costs']:.2f}")
        print(f"  Маржа до привлечения:     ${r['margin']:.2f} ({r['margin_pct']:.1f}%)")
        print(f"  CAC (органика, оценка):  -${r['cac']:.2f}")
        print(f"  ЧИСТАЯ ПРИБЫЛЬ/заказ:     ${r['profit']:.2f}")
        print(f"  Запас на привлечение:     ${r['max_sustainable_cac']:.2f} (маржа до вычета CAC - сколько можно потратить и остаться в нуле)")


if __name__ == "__main__":
    main()
