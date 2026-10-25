# core/achievements.py
"""
Список достижений. Каждое — словарь:
    id      — уникальный ключ
    title   — название на экране
    desc    — описание
    reward  — награда в рубалах
    category— группа (для отображения)
    check   — функция(state) -> bool, сработала ли ачивка
"""


def _bal(state, n):
    return state.get("баланс", 0) >= n


def _cnt(state, key):
    return state.get("счётчики", {}).get(key, 0)


ACHIEVEMENTS = [
    # ═══════ Баланс ═══════
    {"id": "balance_100", "category": "Баланс", "title": "Первая сотня",
     "desc": "Баланс ≥ 100", "reward": 10,
     "check": lambda s: _bal(s, 100)},
    {"id": "balance_500", "category": "Баланс", "title": "Пятьсот",
     "desc": "Баланс ≥ 500", "reward": 30,
     "check": lambda s: _bal(s, 500)},
    {"id": "balance_1000", "category": "Баланс", "title": "Первая 1000",
     "desc": "Баланс ≥ 1000", "reward": 50,
     "check": lambda s: _bal(s, 1000)},
    {"id": "balance_5000", "category": "Баланс", "title": "Пять тысяч",
     "desc": "Баланс ≥ 5000", "reward": 200,
     "check": lambda s: _bal(s, 5000)},
    {"id": "balance_10000", "category": "Баланс", "title": "Десятка",
     "desc": "Баланс ≥ 10000", "reward": 500,
     "check": lambda s: _bal(s, 10000)},

    # ═══════ Дисциплина ═══════
    {"id": "clean_day", "category": "Дисциплина", "title": "Чистый день",
     "desc": "День без штрафов", "reward": 20,
     "check": lambda s: _cnt(s, "чистых_дней") >= 1},
    {"id": "no_fines_day_10", "category": "Дисциплина", "title": "10 чистых дней",
     "desc": "10 дней без штрафов (не подряд)", "reward": 80,
     "check": lambda s: _cnt(s, "чистых_дней") >= 10},
    {"id": "no_fines_week", "category": "Дисциплина", "title": "Неделя без штрафов",
     "desc": "7 дней подряд без штрафа", "reward": 100,
     "check": lambda s: _cnt(s, "дней_подряд_без_штрафа") >= 7},
    {"id": "no_fines_month", "category": "Дисциплина", "title": "Месяц без штрафов",
     "desc": "30 дней подряд без штрафа", "reward": 300,
     "check": lambda s: _cnt(s, "дней_подряд_без_штрафа") >= 30},

    # ═══════ Спины ═══════
    {"id": "spin_first", "category": "Спины", "title": "Первый спин",
     "desc": "Покрутил колесо", "reward": 10,
     "check": lambda s: _cnt(s, "спинов_всего") >= 1},
    {"id": "spin_10", "category": "Спины", "title": "10 спинов",
     "desc": "10 любых спинов", "reward": 30,
     "check": lambda s: _cnt(s, "спинов_всего") >= 10},
    {"id": "spin_50", "category": "Спины", "title": "50 спинов",
     "desc": "50 спинов", "reward": 100,
     "check": lambda s: _cnt(s, "спинов_всего") >= 50},
    {"id": "spin_100", "category": "Спины", "title": "Сотка спинов",
     "desc": "100 спинов", "reward": 250,
     "check": lambda s: _cnt(s, "спинов_всего") >= 100},
    {"id": "mini_7", "category": "Спины", "title": "Неделя мини-колёс",
     "desc": "7 раз крутил мини-колесо", "reward": 50,
     "check": lambda s: _cnt(s, "спинов_мини") >= 7},
    {"id": "jackpot_first", "category": "Спины", "title": "Первый джекпот",
     "desc": "Выпал джекпот в Фортуне", "reward": 100,
     "check": lambda s: _cnt(s, "джекпотов") >= 1},
    {"id": "jackpot_3", "category": "Спины", "title": "Три джекпота",
     "desc": "Джекпот выпал 3 раза", "reward": 300,
     "check": lambda s: _cnt(s, "джекпотов") >= 3},

    # ═══════ Магазин ═══════
    {"id": "buy_first", "category": "Магазин", "title": "Первая покупка",
     "desc": "Купил первый приз", "reward": 20,
     "check": lambda s: _cnt(s, "покупок") >= 1},
    {"id": "buy_10", "category": "Магазин", "title": "10 покупок",
     "desc": "Куплено 10 призов", "reward": 80,
     "check": lambda s: _cnt(s, "покупок") >= 10},
    {"id": "buy_50", "category": "Магазин", "title": "Шопоголик",
     "desc": "Куплено 50 призов", "reward": 300,
     "check": lambda s: _cnt(s, "покупок") >= 50},

    # ═══════ Задания ═══════
    {"id": "task_first", "category": "Задания", "title": "Первое задание",
     "desc": "Выполнил 1 задание", "reward": 10,
     "check": lambda s: _cnt(s, "заданий") >= 1},
    {"id": "task_50", "category": "Задания", "title": "50 заданий",
     "desc": "50 выполненных заданий", "reward": 100,
     "check": lambda s: _cnt(s, "заданий") >= 50},
    {"id": "task_200", "category": "Задания", "title": "200 заданий",
     "desc": "200 заданий", "reward": 400,
     "check": lambda s: _cnt(s, "заданий") >= 200},
    {"id": "task_all_day", "category": "Задания", "title": "Все за день",
     "desc": "Все задания выполнены за один день", "reward": 100,
     "check": lambda s: s.get("счётчики", {}).get("все_задания_день_флаг", False)},

    # ═══════ Челленджи ═══════
    {"id": "challenge_first", "category": "Челленджи", "title": "Первый челлендж",
     "desc": "Выполнил 1 челлендж", "reward": 20,
     "check": lambda s: _cnt(s, "челленджей") >= 1},
    {"id": "challenge_10", "category": "Челленджи", "title": "10 челленджей",
     "desc": "10 выполненных", "reward": 100,
     "check": lambda s: _cnt(s, "челленджей") >= 10},
    {"id": "challenge_50", "category": "Челленджи", "title": "50 челленджей",
     "desc": "50 выполненных", "reward": 300,
     "check": lambda s: _cnt(s, "челленджей") >= 50},
    {"id": "challenge_week_done", "category": "Челленджи", "title": "Неделя закрыта",
     "desc": "Выполнил недельный челлендж", "reward": 80,
     "check": lambda s: _cnt(s, "недельных_выполнено") >= 1},

    # ═══════ Уровни ═══════
    {"id": "level_5", "category": "Уровни", "title": "Уровень 5",
     "desc": "Достиг 5-го уровня", "reward": 50,
     "check": lambda s: s.get("уровень", 1) >= 5},
    {"id": "level_10", "category": "Уровни", "title": "Уровень 10",
     "desc": "Достиг 10-го уровня", "reward": 200,
     "check": lambda s: s.get("уровень", 1) >= 10},
    {"id": "level_20", "category": "Уровни", "title": "Уровень 20",
     "desc": "Достиг 20-го уровня", "reward": 500,
     "check": lambda s: s.get("уровень", 1) >= 20},

    # ═══════ Особые ═══════
    {"id": "chips_10", "category": "Особые", "title": "Десятка фишек",
     "desc": "Накопил 10 фишек", "reward": 30,
     "check": lambda s: s.get("фишки", 0) >= 10},
    {"id": "chips_50", "category": "Особые", "title": "50 фишек",
     "desc": "Накопил 50 фишек", "reward": 150,
     "check": lambda s: s.get("фишки", 0) >= 50},
    {"id": "inventory_5", "category": "Особые", "title": "Коллекционер",
     "desc": "5 наград в инвентаре", "reward": 50,
     "check": lambda s: len([i for i in s.get("инвентарь", []) if not i.get("used")]) >= 5},
    {"id": "rich_kopeck", "category": "Особые", "title": "Богач",
     "desc": "Баланс ≥ 5000 (1000 копеек)", "reward": 100,
     "check": lambda s: s.get("баланс", 0) >= 5000},
]
