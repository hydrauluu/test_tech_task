# Сверка данных — RpaBank vs Pindodo

Тестовое задание, скрипт парсит данные из двух отчётов, сверяет транзакции и экспортирует результат в Excel.

---

## Структура проекта

```
test_tech_task/
├── RPA/
│   └── RpaBank_report.txt        # Отчёт RpaBank (фиксированные колонки)
├── PINDODO/
│   └── Pindodo_report.txt        # Отчёт Pindodo (вертикальный формат)
├── Результат/
│   └── reconciliation.xlsx       # Итоговый Excel (генерируется автоматически)
├── script/
│   ├── config.py                 # Пути и ключи сверки
│   ├── parsers.py                # Парсинг текстовых файлов → DataFrame
│   ├── reconcile.py              # Логика сверки
│   ├── export.py                 # Экспорт в Excel
│   ├── logger.py                 # Настройка loguru
│   └── main.py                   # Точка входа
└── logs/
    └── reconciliation.log        # Лог-файл (генерируется автоматически)
```

---

## Требования

- Python 3.10+
- Зависимости:

```bash
pip install pandas openpyxl loguru
```

---

## Запуск

```bash
# Из корня проекта
git clone https://github.com/hydrauluu/test_tech_task.git
cd test_tech_task
python3 script/main.py
```

---

## Форматы входных файлов

### RpaBank_report.txt

Фиксированные колонки, данные частично слипшиеся:

```
10   1   20250625id4173628491057384629105   10000.00KGS249861   42344552
     ^         ^                                ^      ^             ^
   Index   DateTime+ID                  Amount+Currency CardNum  TerminalID
```

| Поле | Формат | Особенность |
|------|--------|-------------|
| Date | `YYYYMMDD` | Слипшееся с Transaction ID |
| Transaction ID | `id...` | Слипшееся с датой |
| Amount | `10000.00` | Слипшееся с валютой |
| Currency | `KGS` / `USD` / `EUR` | Слипшееся с суммой |
| Card Number | `6 цифр` | Ведущие нули значимы |
| Terminal ID | строка | Может содержать буквы (`ATM19104`) |

### Pindodo_report.txt

Вертикальный формат — каждая транзакция представлена блоком пар `Поле → Значение`, блоки разделены строками из тире:

```
      Local Transaction Date and Time    20250625002000
      Transaction Date                   2025-06-25
      Transaction Amount                 22.34
      Transaction Currency               EUR
      Retrieval Reference Number         063534
      Card Acceptor Terminal ID          32445551
      -------------------------------------------------------------------
```

---

## Логика сверки

Транзакция считается **успешной** если одновременно совпадают все 5 полей:

| RpaBank | Pindodo |
|---------|---------|
| `date` | `transaction_date` |
| `amount` | `amount` |
| `currency` | `currency` |
| `card_number` | `retrieval_reference_number` |
| `terminal_id` | `card_acceptor_terminal_id` |

Сверка реализована через `pandas.merge` с `how="outer"` и `indicator=True` — один проход, O(n), hash join на уровне C.

---

## Результат

Excel-файл с тремя листами:

| Лист | Цвет | Содержимое |
|------|------|------------|
| **Успешные** | 🟢 Зелёный | Транзакции, найденные в обоих отчётах |
| **RpaBank_неуспешные** | 🔴 Красный | Транзакции только в RpaBank |
| **Pindodo_неуспешные** | 🟠 Оранжевый | Транзакции только в Pindodo |

---

## Логирование

Используется `loguru`. Логи пишутся одновременно в два места:

| Назначение | Уровень | Формат |
|------------|---------|--------|
| Консоль | `INFO` и выше | Цветной, компактный |
| `logs/reconciliation.log` | `DEBUG` и выше | Полный, с модулем и строкой |

Ротация лог-файла: **10 MB**, хранение: **7 дней**.

Что логируется:

```
INFO  | Запуск / завершение скрипта
INFO  | Кол-во загруженных записей из каждого файла
INFO  | Итоги сверки: % совпадений, кол-во неуспешных
DEBUG | Нераспознанные строки файла
DEBUG | RRN неуспешных транзакций
WARNING | Пропущенные неполные блоки в Pindodo
ERROR | Файл не найден / пустой файл
```

Пример вывода в консоль:
```
2025-06-26 10:00:01 | INFO     | parsers   - Парсим RpaBank: RPA/RpaBank_report.txt
2025-06-26 10:00:01 | INFO     | parsers   - RpaBank: загружено 126 записей
2025-06-26 10:00:01 | INFO     | parsers   - Парсим Pindodo: PINDODO/Pindodo_report.txt
2025-06-26 10:00:01 | INFO     | parsers   - Pindodo: загружено 121 записей
2025-06-26 10:00:01 | INFO     | reconcile - Начинаем сверку: RpaBank=126, Pindodo=121
2025-06-26 10:00:01 | INFO     | reconcile - ✓ Успешные:         116 (89.9%)
2025-06-26 10:00:01 | INFO     | reconcile - ✗ Только RpaBank:   10
2025-06-26 10:00:01 | INFO     | reconcile - ✗ Только Pindodo:   5
2025-06-26 10:00:01 | INFO     | export    - Excel сохранён: Результат/reconciliation.xlsx
```

---

## Архитектура

Проект построен по принципу **pipeline-архитектуры**: данные текут через независимые функции-трансформации, каждый модуль делает ровно одну вещь.

```
RpaBank_report.txt  ──► parse_rpabank()  ──┐
                                            ├──► reconcile() ──► export_to_excel()
Pindodo_report.txt  ──► parse_pindodo()  ──┘
```

Такой подход позволяет легко:
- **Добавить новый источник** — новая функция `parse_X()` в `parsers.py`
- **Подключить БД** — если в будущем понадобится сохранять данные в БД, то достаточно создать модуль `db.py` и подключить его
- **Сменить формат экспорта** — достаточно сменить только `export.py`, остальное не трогать
- **Тестировать изолированно** — каждая функция независима
