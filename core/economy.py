# core/economy.py
"""
Логика над балансом + колёса, челленджи, фишки, инвентарь, достижения, цели, копилка.
Оптимизировано: кэш достижений, debounce автосейва.
"""
import random
import time
from datetime import datetime, timedelta

from core.storage import Storage
from core.achievements import ACHIEVEMENTS


class Economy:
    def __init__(self, state: dict):
        self.state = state
        self._done_cache = set(state.get("достижения", []))
        self._last_save = 0.0

    # ═══════════ Баланс ═══════════
    def add(self, amount: int, reason: str = "Ручное начисление") -> None:
        if amount <= 0:
            raise ValueError("Сумма начисления должна быть > 0")
        self.state["баланс"] += amount
        self._recalc_level()
        self._log("+", amount, reason)
        self._update_clean_days()

    def subtract(self, amount: int, reason: str = "Ручное списание") -> None:
        if amount <= 0:
            raise ValueError("Сумма списания должна быть > 0")
        self.state["баланс"] -= amount
        self._recalc_level()
        self._log("−", amount, reason)

    def remove_fine(self, amount: int, reason: str = "Снятие штрафа (ручное)") -> None:
        self.add(amount, reason)

    def random_bonus(self, lo: int = 10, hi: int = 20) -> int:
        value = random.randint(lo, hi)
        self.add(value, "Бонус за старание")
        return value

    # ═══════════ Применение ═══════════
    def apply_task(self, index: int) -> dict:
        item = self.state["задания"][index]
        base = int(item["price"])
        doubled = False
        if self.state["активные_эффекты"].get("double_task"):
            base *= 2
            doubled = True
            self.state["активные_эффекты"]["double_task"] = False
            self._log("+", 0, "×2 к заданию применён (эффект сгорел)")
        self.add(base, f"Задание: {item['name']}")

        c = self.state["счётчики"]
        c["заданий"] = c.get("заданий", 0) + 1
        self._track_task_today(item["name"])
        self._check_all_tasks_today()

        self.check_achievements()
        self.commit()
        return {"amount": base, "doubled": doubled}

    def apply_fine(self, index: int) -> dict:
        item = self.state["штрафы"][index]
        price = abs(int(item["price"]))
        if self.state["активные_эффекты"].get("golden_ticket"):
            self.state["активные_эффекты"]["golden_ticket"] = False
            self._log("+", 0, f"🎫 Золотой билет отменил штраф: {item['name']}")
            self.check_achievements()
            self.commit()
            return {"amount": 0, "cancelled": True}
        self.subtract(price, f"Штраф: {item['name']}")
        c = self.state["счётчики"]
        c["дней_подряд_без_штрафа"] = 0
        c["последний_штраф_день"] = self._today_iso()
        self.check_achievements()
        self.commit()
        return {"amount": price, "cancelled": False}

    def buy_reward(self, index: int) -> bool:
        item = self.state["призы"][index]
        price = int(item["price"])
        if self.state["баланс"] < price:
            return False
        self.subtract(price, f"Покупка: {item['name']}")
        name = item["name"]
        if "сюрприз" in name.lower():
            self._open_surprise_box()
        elif "игрушка" in name.lower() or "игра" in name.lower():
            self.inventory_add(name, kind="progress", target=5)
        else:
            self.inventory_add(name, kind="usable")
        self.state["счётчики"]["покупок"] = self.state["счётчики"].get("покупок", 0) + 1
        self.check_achievements()
        self.commit()
        return True

    # ═══════════ CRUD ═══════════
    def list_get(self, key: str) -> list:
        return self.state[key]

    def item_add(self, key: str, name: str, price: int) -> None:
        self.state[key].append({"name": name, "price": int(price)})

    def item_update(self, key: str, index: int, name: str, price: int) -> None:
        self.state[key][index] = {"name": name, "price": int(price)}

    def item_delete(self, key: str, index: int) -> None:
        if 0 <= index < len(self.state[key]):
            del self.state[key][index]

    # ═══════════ Уровни ═══════════
    def _recalc_level(self) -> None:
        step = int(self.state["настройки"].get("level_step", 500) or 500)
        bal = self.state["баланс"]
        self.state["уровень"] = 1 if bal < 0 else bal // step + 1

    # ═══════════ История ═══════════
    def _log(self, sign: str, amount: int, reason: str) -> None:
        self.state["история"].append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "sign": sign,
            "amount": amount,
            "reason": reason,
            "balance_after": self.state["баланс"],
        })
        if len(self.state["история"]) > 5000:
            self.state["история"] = self.state["история"][-5000:]

    # ═══════════ Курс ═══════════
    def to_kopecks(self, rubaly: int | None = None) -> float:
        if rubaly is None:
            rubaly = self.state["баланс"]
        rate = int(self.state["настройки"].get("rate_per_kopeck", 5) or 5)
        return rubaly / rate if rate else 0.0

    def rubaly_for_kopecks(self, kopecks: float) -> int:
        rate = int(self.state["настройки"].get("rate_per_kopeck", 5) or 5)
        return int(round(kopecks * rate))

    def to_kopecks_string(self) -> str:
        return f"{self.to_kopecks():.2f} коп."

    def withdraw_to_kopecks(self, kopecks: float) -> dict:
        if kopecks <= 0:
            return {"ok": False, "rubaly": 0, "kopecks": 0, "message": "Сумма должна быть > 0"}
        rubaly = self.rubaly_for_kopecks(kopecks)
        if rubaly <= 0:
            return {"ok": False, "rubaly": 0, "kopecks": 0, "message": "Слишком мелкая сумма"}
        if self.state["баланс"] < rubaly:
            return {
                "ok": False, "rubaly": rubaly, "kopecks": kopecks,
                "message": f"Не хватает: нужно {rubaly} рубалов",
            }
        self.subtract(rubaly, f"Вывод карманных: {kopecks:.2f} коп. ({rubaly} руб.)")
        self.check_achievements()
        self.commit()
        return {
            "ok": True, "rubaly": rubaly, "kopecks": kopecks,
            "message": f"Выведено {kopecks:.2f} коп. за {rubaly} руб.",
        }

    def max_kopecks_available(self) -> float:
        return self.to_kopecks()

    def has_debt(self) -> bool:
        return self.state.get("баланс", 0) < 0

    def debt_amount(self) -> int:
        bal = self.state.get("баланс", 0)
        return abs(bal) if bal < 0 else 0

    def debt_message(self) -> str:
        if not self.has_debt():
            return ""
        return f"⚠ Долг: {self.debt_amount()} рубалов"

    # ═══════════ Фишки ═══════════
    def chips_exchange_small(self, cost: int, reward: int, reason: str) -> bool:
        if self.state["фишки"] < cost:
            return False
        self.state["фишки"] -= cost
        self.add(reward, reason)
        self.commit()
        return True

    def chips_exchange_guaranteed(self) -> dict:
        if self.state["фишки"] < 10:
            raise ValueError("Нужно 10 фишек")
        self.state["фишки"] -= 10
        prize = random.randint(100, 150)
        self.add(prize, f"Обмен 10 фишек: гарантированный приз +{prize}")
        self.commit()
        return {"prize": prize}

    def chips_exchange_free_spin(self) -> bool:
        if self.state["фишки"] < 10:
            return False
        self.state["фишки"] -= 10
        self._log("+", 0, "Обмен 10 фишек: бесплатный спин Фортуны")
        self.commit()
        return True

    # ═══════════ Колёса ═══════════
    def can_spin_mini(self) -> bool:
        last = self.state["настройки"].get("mini_wheel_last") or ""
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return True
        return datetime.now() - last_dt >= timedelta(hours=24)

    def mini_wheel_cooldown_left(self) -> str:
        last = self.state["настройки"].get("mini_wheel_last") or ""
        if not last:
            return ""
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return ""
        remaining = last_dt + timedelta(hours=24) - datetime.now()
        if remaining.total_seconds() <= 0:
            return ""
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return f"осталось {hours} ч {minutes} мин"

    def spin_mini_wheel(self) -> dict:
        if not self.can_spin_mini():
            raise ValueError("Мини-колесо ещё не готово")

        sectors = [
            {"prize": "+5 рубалов",  "amount": 5,  "chips": 0},
            {"prize": "+10 рубалов", "amount": 10, "chips": 0},
            {"prize": "+15 рубалов", "amount": 15, "chips": 0},
            {"prize": "+1 фишка",    "amount": 0,  "chips": 1},
            {"prize": "Пусто",       "amount": 0,  "chips": 0},
            {"prize": "+1 к удаче",  "amount": 0,  "chips": 0, "luck": 1},
        ]
        result = random.choice(sectors).copy()

        if result["amount"] > 0:
            self.add(result["amount"], f"Мини-колесо: {result['prize']}")
        if result["chips"] > 0:
            self.state["фишки"] += 1
            self._log("+", 0, f"Мини-колесо: {result['prize']} (фишка)")
        if result.get("luck"):
            self.state["удача"] = self.state.get("удача", 0) + 1
            self._log("+", 0, f"Мини-колесо: +1 к удаче (теперь {self.state['удача']})")
        if result["amount"] == 0 and result["chips"] == 0 and not result.get("luck"):
            self._log("−", 0, "Мини-колесо: Пусто")

        self.state["настройки"]["mini_wheel_last"] = datetime.now().isoformat(timespec="seconds")

        self.state["счётчики"]["спинов_всего"] = self.state["счётчики"].get("спинов_всего", 0) + 1
        self.state["счётчики"]["спинов_мини"] = self.state["счётчики"].get("спинов_мини", 0) + 1
        self.check_achievements()
        self.commit()
        return result

    def spin_fortune_wheel(self, free: bool = False) -> dict:
        stake = int(self.state.get("джекпот", 130))

        if not free:
            if self.state["баланс"] < stake:
                raise ValueError(f"Нужно {stake} рубалов для спина")
            self.subtract(stake, f"Ставка в колесе фортуны: {stake}")
        else:
            self._log("+", 0, "Бесплатный спин Фортуны (за фишки)")

        before = self.state["баланс"]

        luck = self.state.get("удача", 0)
        jackpot_chance = min(0.05 + luck * 0.005, 0.15)
        r = random.random()
        jackpot_hit = False
        prize_name = ""
        payout = 0
        chips = 1
        special = None

        if r < jackpot_chance:
            jackpot_hit = True
            prize_name = "🎉 ДЖЕКПОТ!"
            payout = stake * 2
        elif r < jackpot_chance + 0.08:
            prize_name = "+80"
            payout = stake + 80
        elif r < jackpot_chance + 0.13:
            prize_name = "🎫 Золотой билет (отмена штрафа)"
            payout = stake
            special = "golden_ticket"
        elif r < jackpot_chance + 0.25:
            prize_name = "+50"
            payout = stake + 50
        elif r < jackpot_chance + 0.35:
            prize_name = "×2 к следующему заданию"
            payout = stake
            special = "double_task"
        elif r < jackpot_chance + 0.45:
            prize_name = "🕹 Час гаджетов вне очереди"
            payout = stake
            special = "gadget_hour"
        elif r < jackpot_chance + 0.53:
            prize_name = "🎬 Выбор фильма на вечер"
            payout = stake
            special = "movie_choice"
        elif r < jackpot_chance + 0.68:
            prize_name = "+20"
            payout = stake + 20
        elif r < jackpot_chance + 0.90:
            prize_name = "Пусто"
            payout = 0
        else:
            prize_name = "⭐ Секретный сектор: выбери себе задание"
            payout = stake
            special = "pick_own_task"

        if free and payout >= stake:
            payout -= stake

        if payout > 0:
            self.add(payout, f"Фортуна: {prize_name}")
        else:
            self._log("−", 0, f"Фортуна: {prize_name}")

        if special == "golden_ticket":
            self.state["активные_эффекты"]["golden_ticket"] = True
            self._log("+", 0, "🎫 Золотой билет активирован")
        elif special == "double_task":
            self.state["активные_эффекты"]["double_task"] = True
            self._log("+", 0, "×2 к следующему заданию активирован")
        elif special == "gadget_hour":
            self.inventory_add("Час гаджетов вне очереди", kind="usable")
            self._log("+", 0, "🕹 Час гаджетов добавлен в инвентарь")
        elif special == "movie_choice":
            self.inventory_add("Выбор фильма на вечер", kind="usable")
            self._log("+", 0, "🎬 Выбор фильма добавлен в инвентарь")
        elif special == "pick_own_task":
            self.inventory_add("⭐ Выбрать себе задание", kind="pick_task")
            self._log("+", 0, "⭐ Секретный сектор: в инвентаре")

        self.state["фишки"] += chips
        self._log("+", 0, f"Фортуна: +{chips} фишка")

        if jackpot_hit:
            self.state["джекпот"] = int(self.state["настройки"].get("jackpot_base", 130))
        else:
            self.state["джекпот"] = min(int(self.state["джекпот"]) + 10, 180)

        after = self.state["баланс"]
        delta = after - before

        self.state["счётчики"]["спинов_всего"] = self.state["счётчики"].get("спинов_всего", 0) + 1
        if jackpot_hit:
            self.state["счётчики"]["джекпотов"] = self.state["счётчики"].get("джекпотов", 0) + 1
        self.check_achievements()
        self.commit()

        return {
            "prize": prize_name,
            "delta": delta,
            "jackpot": jackpot_hit,
            "special": special,
            "luck": luck,
            "jackpot_chance": jackpot_chance,
        }

    # ═══════════ Челленджи ═══════════
    def _today_iso(self) -> str:
        return datetime.now().date().isoformat()

    def _current_week_iso(self) -> str:
        y, w, _ = datetime.now().isocalendar()
        return f"{y}-W{w:02d}"

    def get_daily_challenge(self) -> dict | None:
        ch = self.state.get("активный_челлендж_дня")
        if not ch:
            return None
        if ch.get("date") != self._today_iso():
            return None
        return ch

    def get_weekly_challenge(self) -> dict | None:
        ch = self.state.get("активный_челлендж_недели")
        if not ch:
            return None
        if ch.get("week") != self._current_week_iso():
            return None
        return ch

    def new_daily_challenge(self, exclude_text: str | None = None) -> dict:
        """Выбирает случайный челлендж на сегодня. 15% — секретный."""
        from core.defaults import SECRET_CHALLENGES
        is_secret = random.random() < 0.15
        pool = SECRET_CHALLENGES if is_secret else self.state["челленджи_ежедневные"]
        if exclude_text and len(pool) > 1:
            pool = [c for c in pool if c["text"] != exclude_text] or pool
        ch = random.choice(pool).copy()
        ch["date"] = self._today_iso()
        ch["status"] = "active"
        ch["secret"] = is_secret
        self.state["активный_челлендж_дня"] = ch
        if is_secret:
            self._log("+", 0, f"⭐ Секретный челлендж дня: {ch['text']}")
        return ch

    def new_weekly_challenge(self, exclude_text: str | None = None) -> dict:
        pool = self.state["челленджи_недельные"]
        if exclude_text and len(pool) > 1:
            pool = [c for c in pool if c["text"] != exclude_text] or pool
        ch = random.choice(pool).copy()
        ch["week"] = self._current_week_iso()
        ch["status"] = "active"
        self.state["активный_челлендж_недели"] = ch
        return ch

    def complete_daily_challenge(self) -> dict | None:
        ch = self.get_daily_challenge()
        if not ch or ch.get("status") != "active":
            return None
        reward = int(ch.get("reward", 0))
        if reward > 0:
            self.add(reward, f"Челлендж дня: {ch['text']}")
        else:
            self._log("+", 0, f"Челлендж дня: {ch['text']} (без награды)")
        ch["status"] = "done"
        self.state["счётчики"]["челленджей"] = self.state["счётчики"].get("челленджей", 0) + 1
        self.check_achievements()
        self.commit()
        return ch

    def fail_daily_challenge(self) -> dict | None:
        ch = self.get_daily_challenge()
        if not ch or ch.get("status") != "active":
            return None
        ch["status"] = "failed"
        self._log("−", 0, f"Челлендж дня провален: {ch['text']}")
        self.commit()
        return ch

    def complete_weekly_challenge(self) -> dict | None:
        ch = self.get_weekly_challenge()
        if not ch or ch.get("status") != "active":
            return None
        reward = int(ch.get("reward", 0))
        if reward > 0:
            self.add(reward, f"Недельный челлендж: {ch['text']}")
        else:
            self._log("+", 0, f"Недельный челлендж: {ch['text']} (без награды)")
        ch["status"] = "done"
        self.state["счётчики"]["челленджей"] = self.state["счётчики"].get("челленджей", 0) + 1
        self.state["счётчики"]["недельных_выполнено"] = self.state["счётчики"].get("недельных_выполнено", 0) + 1
        self.check_achievements()
        self.commit()
        return ch

    def fail_weekly_challenge(self) -> dict | None:
        ch = self.get_weekly_challenge()
        if not ch or ch.get("status") != "active":
            return None
        ch["status"] = "failed"
        self._log("−", 0, f"Недельный челлендж провален: {ch['text']}")
        self.commit()
        return ch

    # ═══════════ Инвентарь ═══════════
    def inventory_add(self, name: str, kind: str = "usable", target: int = 1) -> None:
        self.state["инвентарь"].append({
            "id": self._next_inventory_id(),
            "name": name,
            "kind": kind,
            "progress": 0,
            "target": target,
            "used": False,
            "ts": datetime.now().isoformat(timespec="seconds"),
        })

    def _next_inventory_id(self) -> int:
        items = self.state["инвентарь"]
        if not items:
            return 1
        return max(i["id"] for i in items) + 1

    def inventory_active(self) -> list:
        return [i for i in self.state["инвентарь"] if not i["used"]]

    def inventory_use(self, item_id: int) -> dict:
        items = self.state["инвентарь"]
        item = next((i for i in items if i["id"] == item_id), None)
        if item is None or item["used"]:
            return {"used": None, "message": "Уже использован"}
        item["used"] = True
        self._log("+", 0, f"Использована награда: {item['name']}")
        self.commit()
        return {"used": item["name"], "message": f"«{item['name']}» использовано"}

    def inventory_pick_task(self, item_id: int, name: str, amount: int) -> dict:
        amount = min(int(amount), 100)
        self.add(amount, f"Секретный сектор: {name}")
        self.inventory_use(item_id)
        return {"amount": amount, "name": name}

    # ═══════════ Прочее ═══════════
    def _open_surprise_box(self) -> dict:
        variants = [
            ("+30 рубалов", lambda: self.add(30, "Сюрприз-бокс: +30")),
            ("+50 рубалов", lambda: self.add(50, "Сюрприз-бокс: +50")),
            ("+80 рубалов", lambda: self.add(80, "Сюрприз-бокс: +80")),
            ("+100 рубалов", lambda: self.add(100, "Сюрприз-бокс: +100")),
            ("+3 фишки", lambda: self.state.update({"фишки": self.state["фишки"] + 3})),
            ("Золотой билет", lambda: self.state["активные_эффекты"].update({"golden_ticket": True})),
        ]
        name, fn = random.choice(variants)
        fn()
        self._log("+", 0, f"🎁 Сюрприз-бокс: {name}")
        return {"prize": name}

    # ═══════════ Достижения ═══════════
    def check_achievements(self) -> list:
        if len(self._done_cache) >= len(ACHIEVEMENTS):
            return []
        opened = []
        for ach in ACHIEVEMENTS:
            if ach["id"] in self._done_cache:
                continue
            try:
                if ach["check"](self.state):
                    self._done_cache.add(ach["id"])
                    reward = int(ach.get("reward", 0))
                    if reward > 0:
                        self.state["баланс"] += reward
                        self._recalc_level()
                    self._log("+", reward, f"🏆 Достижение: {ach['title']}")
                    opened.append(ach)
            except Exception:
                continue
        if opened:
            self.state["достижения"] = list(self._done_cache)
        return opened

    def _track_task_today(self, task_name: str) -> None:
        c = self.state["счётчики"]
        today = self._today_iso()
        if c.get("дата_заданий_сегодня") != today:
            c["задания_сегодня"] = []
            c["дата_заданий_сегодня"] = today
        lst = c.get("задания_сегодня", [])
        lst.append(task_name)
        c["задания_сегодня"] = lst

    def _check_all_tasks_today(self) -> None:
        c = self.state["счётчики"]
        names_today = set(c.get("задания_сегодня", []))
        all_names = {t["name"] for t in self.state["задания"]}
        if all_names and all_names.issubset(names_today):
            c["все_задания_день_флаг"] = True

    def _update_clean_days(self) -> None:
        c = self.state["счётчики"]
        today = self._today_iso()
        last = c.get("последний_день_захода", "")
        if last == today:
            return
        if c.get("последний_штраф_день") != today:
            c["дней_подряд_без_штрафа"] = c.get("дней_подряд_без_штрафа", 0) + 1
            c["чистых_дней"] = c.get("чистых_дней", 0) + 1
        c["последний_день_захода"] = today

    def achievements_all(self) -> list:
        return [(a, a["id"] in self._done_cache) for a in ACHIEVEMENTS]

    # ═══════════ ЦЕЛИ ═══════════
    def goal_add(self, name: str, target: int, saved: int = 0) -> dict:
        goal = {
            "id": self._next_goal_id(),
            "name": name,
            "target": int(target),
            "saved": int(saved),
            "created": datetime.now().isoformat(timespec="seconds"),
            "done": False,
        }
        self.state["цели"].append(goal)
        self._log("+", 0, f"🎯 Создана цель: {name} ({saved}/{target})")
        self.commit()
        return goal

    def _next_goal_id(self) -> int:
        goals = self.state["цели"]
        if not goals:
            return 1
        return max(g["id"] for g in goals) + 1

    def goal_put(self, goal_id: int, amount: int) -> dict:
        if amount <= 0:
            return {"ok": False, "message": "Сумма должна быть > 0"}
        if self.state["баланс"] < amount:
            return {"ok": False, "message": f"Не хватает: нужно {amount}"}
        goal = self._find_goal(goal_id)
        if goal is None or goal["done"]:
            return {"ok": False, "message": "Цель не найдена"}
        self.subtract(amount, f"🎯 В цель «{goal['name']}»: {amount}")
        goal["saved"] += amount
        if goal["saved"] >= goal["target"]:
            goal["done"] = True
            self._log("+", 0, f"🎯 Цель «{goal['name']}» достигнута!")
        self.commit()
        return {"ok": True, "message": f"Отложено {amount} в «{goal['name']}»"}

    def goal_take(self, goal_id: int, amount: int) -> dict:
        if amount <= 0:
            return {"ok": False, "message": "Сумма должна быть > 0"}
        goal = self._find_goal(goal_id)
        if goal is None:
            return {"ok": False, "message": "Цель не найдена"}
        if goal["saved"] < amount:
            return {"ok": False, "message": f"В цели только {goal['saved']}"}
        goal["saved"] -= amount
        if goal["saved"] < goal["target"]:
            goal["done"] = False
        self.add(amount, f"🎯 Возврат из цели «{goal['name']}»: {amount}")
        self.commit()
        return {"ok": True, "message": f"Возвращено {amount}"}

    def goal_delete(self, goal_id: int) -> dict:
        goal = self._find_goal(goal_id)
        if goal is None:
            return {"ok": False, "message": "Не найдено"}
        saved = goal["saved"]
        if saved > 0:
            self.add(saved, f"🎯 Возврат из удалённой цели «{goal['name']}»")
        self.state["цели"] = [g for g in self.state["цели"] if g["id"] != goal_id]
        self.commit()
        return {"ok": True, "message": f"Удалено (возвращено {saved})"}

    def _find_goal(self, goal_id: int):
        for g in self.state["цели"]:
            if g["id"] == goal_id:
                return g
        return None

    def goals_active(self) -> list:
        return [g for g in self.state["цели"] if not g["done"]]

    def goals_done(self) -> list:
        return [g for g in self.state["цели"] if g["done"]]

    # ═══════════ КОПИЛКА ═══════════
    def piggy_put(self, amount: int) -> dict:
        if amount <= 0:
            return {"ok": False, "message": "Сумма должна быть > 0"}
        if self.state["баланс"] < amount:
            return {"ok": False, "message": f"Не хватает: нужно {amount}"}
        self.subtract(amount, f"🐷 В копилку: {amount}")
        self.state["копилка"] = self.state.get("копилка", 0) + amount
        self.commit()
        return {"ok": True, "message": f"В копилке теперь {self.state['копилка']}"}

    def piggy_take(self, amount: int) -> dict:
        if amount <= 0:
            return {"ok": False, "message": "Сумма должна быть > 0"}
        piggy = self.state.get("копилка", 0)
        if piggy < amount:
            return {"ok": False, "message": f"В копилке только {piggy}"}
        self.state["копилка"] = piggy - amount
        self.add(amount, f"🐷 Из копилки: {amount}")
        self.commit()
        return {"ok": True, "message": f"Достано {amount}. В копилке {self.state['копилка']}"}

    def piggy_empty(self) -> dict:
        piggy = self.state.get("копилка", 0)
        if piggy <= 0:
            return {"ok": False, "message": "Копилка пуста"}
        self.state["копилка"] = 0
        self.add(piggy, f"🐷 Опустошена копилка: {piggy}")
        self.commit()
        return {"ok": True, "message": f"Вернули {piggy} из копилки"}

        # ═══════════ ЛОТЕРЕЯ ═══════════
    LOTTERY_TICKET_PRICE = 50

    def lottery_buy_ticket(self) -> dict:
        """
        Покупает билет и сразу разыгрывает приз.
        Возвращает {'ok', 'prize', 'amount', 'message'}.
        """
        price = self.LOTTERY_TICKET_PRICE
        if self.state["баланс"] < price:
            return {
                "ok": False,
                "prize": "",
                "amount": 0,
                "message": f"Нужно {price} рубалов на билет",
            }

        self.subtract(price, f"🎟 Лотерейный билет: {price}")

        # розыгрыш
        r = random.random()
        amount = 0
        prize = ""
        special = None

        if r < 0.01:
            amount = 500
            prize = "🎉 ДЖЕКПОТ +500"
        elif r < 0.03:
            amount = 200
            prize = "+200"
        elif r < 0.08:
            amount = 100
            prize = "+100"
        elif r < 0.18:
            amount = 50
            prize = "+50"
        elif r < 0.33:
            amount = 30
            prize = "+30"
        elif r < 0.58:
            amount = 10
            prize = "+10"
        elif r < 0.68:
            prize = "5 фишек"
            special = "chips_5"
        elif r < 0.70:
            prize = "🎫 Золотой билет"
            special = "golden_ticket"
        else:
            prize = "Пусто"
            amount = 0

        # применяем
        if amount > 0:
            self.add(amount, f"🎟 Лотерея: {prize}")
        if special == "chips_5":
            self.state["фишки"] += 5
            self._log("+", 0, "🎟 Лотерея: +5 фишек")
        if special == "golden_ticket":
            self.state["активные_эффекты"]["golden_ticket"] = True
            self._log("+", 0, "🎟 Лотерея: золотой билет активирован")
        if amount == 0 and not special:
            self._log("−", 0, "🎟 Лотерея: пусто")

        # счётчики
        c = self.state.setdefault("счётчики", {})
        c["лотерея_куплено"] = c.get("лотерея_куплено", 0) + 1
        if amount > 0:
            c["лотерея_выиграно_руб"] = c.get("лотерея_выиграно_руб", 0) + amount
        c["лотерея_потрачено"] = c.get("лотерея_потрачено", 0) + price

        self.check_achievements()
        self.commit()

        net = amount - price
        if amount > 0:
            message = f"{prize}\nИтого: {net:+d} рубалов"
        elif special == "chips_5":
            message = f"{prize} (без рубалов)"
        elif special == "golden_ticket":
            message = "Золотой билет активирован!"
        else:
            message = "Пусто. Бывает."

        return {
            "ok": True,
            "prize": prize,
            "amount": amount,
            "message": message,
        }

    def lottery_stats(self) -> dict:
        c = self.state.get("счётчики", {})
        return {
            "куплено": c.get("лотерея_куплено", 0),
            "выиграно_руб": c.get("лотерея_выиграно_руб", 0),
            "потрачено": c.get("лотерея_потрачено", 0),
        }

    # ═══════════ КВЕСТ-ЦЕПОЧКА ═══════════
    def quest_current(self) -> dict | None:
        """Возвращает активный квест или None."""
        return self.state.get("активный_квест")

    def quest_start_new(self, exclude_id: str | None = None) -> dict:
        """Начинает новый случайный квест."""
        from core.quests import QUESTS
        pool = QUESTS
        if exclude_id and len(pool) > 1:
            pool = [q for q in QUESTS if q["id"] != exclude_id] or QUESTS
        q = random.choice(pool).copy()
        self.state["активный_квест"] = {
            "id": q["id"],
            "title": q["title"],
            "steps": q["steps"],
            "reward": q["reward"],
            "step_index": 0,
            "done": False,
            "started": datetime.now().isoformat(timespec="seconds"),
        }
        self._log("+", 0, f"⚔ Начат квест: {q['title']}")
        self.commit()
        return self.state["активный_квест"]

    def quest_complete_step(self) -> dict:
        """Отмечает текущий этап выполненным. Если это был последний — выдаёт награду."""
        q = self.quest_current()
        if q is None or q.get("done"):
            return {"ok": False, "message": "Нет активного квеста"}
        step = q["steps"][q["step_index"]]
        q["step_index"] += 1
        self._log("+", 0, f"⚔ Квест: этап «{step}» выполнен")

        finished = q["step_index"] >= len(q["steps"])
        reward = 0
        if finished:
            q["done"] = True
            reward = int(q["reward"])
            self.add(reward, f"⚔ Квест завершён: {q['title']}")

            # счётчик
            c = self.state.setdefault("счётчики", {})
            c["квестов_пройдено"] = c.get("квестов_пройдено", 0) + 1
            self.check_achievements()

        self.commit()
        return {
            "ok": True,
            "finished": finished,
            "step": step,
            "reward": reward,
            "message": f"Этап «{step}» готов!" if not finished else f"🎉 Квест завершён! +{reward}",
        }

    def quest_abandon(self) -> dict:
        q = self.quest_current()
        if q is None:
            return {"ok": False, "message": "Нет квеста"}
        self._log("−", 0, f"⚔ Квест отменён: {q['title']}")
        self.state["активный_квест"] = None
        self.commit()
        return {"ok": True, "message": "Квест отменён"}

    # ═══════════ КОЛЕСО ИСПЫТАНИЙ ═══════════
    def can_spin_trial(self) -> bool:
        """Кулдаун 4 часа."""
        last = self.state["настройки"].get("trial_wheel_last") or ""
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return True
        return datetime.now() - last_dt >= timedelta(hours=4)

    def trial_cooldown_left(self) -> str:
        last = self.state["настройки"].get("trial_wheel_last") or ""
        if not last:
            return ""
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return ""
        remaining = last_dt + timedelta(hours=4) - datetime.now()
        if remaining.total_seconds() <= 0:
            return ""
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return f"осталось {hours} ч {minutes} мин"

    def spin_trial_wheel(self) -> dict:
        """Крутит колесо испытаний. Кладёт испытание в инвентарь."""
        if not self.can_spin_trial():
            raise ValueError("Колесо испытаний ещё не готово")

        sectors = [
            {"name": "Сделай 20 приседаний",   "reward": 50},
            {"name": "Помой посуду",           "reward": 60},
            {"name": "30 минут без телефона",  "reward": 40},
            {"name": "Погуляй 20 минут",       "reward": 30},
            {"name": "Прочитай 5 страниц",     "reward": 40},
            {"name": "Помоги маме",            "reward": 70},
            {"name": "Съешь фрукт",            "reward": 20},
            {"name": "Пусто",                  "reward": 0},
        ]
        result = random.choice(sectors).copy()

        if result["reward"] > 0:
            self.inventory_add(
                f"💪 Испытание: {result['name']} (+{result['reward']})",
                kind="trial",
                target=result["reward"],
            )
            self._log("+", 0, f"💪 Испытание выпало: {result['name']} (+{result['reward']})")
        else:
            self._log("−", 0, "💪 Испытание: Пусто")

        self.state["настройки"]["trial_wheel_last"] = datetime.now().isoformat(timespec="seconds")
        self.state["счётчики"]["испытаний_выпало"] = self.state["счётчики"].get("испытаний_выпало", 0) + 1
        self.commit()
        return result

    def trial_complete(self, item_id: int) -> dict:
        """Отмечает испытание выполненным. Начисляет reward, закрывает инвентарь-запись."""
        items = self.state["инвентарь"]
        item = next((i for i in items if i["id"] == item_id), None)
        if item is None or item["used"]:
            return {"ok": False, "message": "Уже закрыто"}
        reward = int(item.get("target", 0))
        item["used"] = True
        if reward > 0:
            self.add(reward, f"💪 Испытание выполнено: {item['name']}")
        else:
            self._log("+", 0, "💪 Испытание закрыто без награды")
        self.state["счётчики"]["испытаний_выполнено"] = self.state["счётчики"].get("испытаний_выполнено", 0) + 1
        self.commit()
        return {"ok": True, "reward": reward, "message": f"Испытание засчитано! +{reward}"}

    # ═══════════ КОЛЕСО СКИДОК ═══════════
    def can_spin_discount(self) -> bool:
        """Раз в 24 часа."""
        last = self.state["настройки"].get("discount_wheel_last") or ""
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return True
        return datetime.now() - last_dt >= timedelta(hours=24)

    def discount_cooldown_left(self) -> str:
        last = self.state["настройки"].get("discount_wheel_last") or ""
        if not last:
            return ""
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return ""
        remaining = last_dt + timedelta(hours=24) - datetime.now()
        if remaining.total_seconds() <= 0:
            return ""
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return f"осталось {hours} ч {minutes} мин"

    def spin_discount_wheel(self) -> dict:
        """Выпадает скидка на случайный приз."""
        if not self.can_spin_discount():
            raise ValueError("Колесо скидок ещё не готово")

        sectors = [
            {"discount": 30, "chance": 0.30},
            {"discount": 40, "chance": 0.25},
            {"discount": 50, "chance": 0.20},
            {"discount": 60, "chance": 0.15},
            {"discount": 70, "chance": 0.05},
            {"discount": 0,  "chance": 0.05},   # пусто
        ]
        r = random.random()
        acc = 0.0
        chosen = 0
        for s in sectors:
            acc += s["chance"]
            if r <= acc:
                chosen = s["discount"]
                break

        # выбираем случайный приз
        rewards = self.state["призы"]
        prize = random.choice(rewards) if rewards else {"name": "—", "price": 0}

        now = datetime.now()
        expires = (now + timedelta(hours=24)).isoformat(timespec="seconds")

        if chosen > 0:
            new_price = max(1, int(int(prize["price"]) * (100 - chosen) / 100))
            self.state["скидка"] = {
                "prize_name": prize["name"],
                "original_price": int(prize["price"]),
                "new_price": new_price,
                "discount": chosen,
                "expires": expires,
            }
            self._log("+", 0, f"🎟 Скидка {chosen}% на «{prize['name']}» (до {expires[:16]})")
        else:
            self.state["скидка"] = None
            self._log("−", 0, "🎟 Колесо скидок: пусто")

        self.state["настройки"]["discount_wheel_last"] = now.isoformat(timespec="seconds")
        self.commit()
        return {
            "discount": chosen,
            "prize_name": prize["name"],
            "original_price": int(prize["price"]),
            "new_price": max(1, int(int(prize["price"]) * (100 - chosen) / 100)) if chosen else 0,
        }

    def active_discount(self) -> dict | None:
        """Возвращает активную скидку или None (если истекла — чистит)."""
        disc = self.state.get("скидка")
        if not disc:
            return None
        try:
            exp = datetime.fromisoformat(disc["expires"])
        except (ValueError, KeyError):
            return None
        if datetime.now() > exp:
            self.state["скидка"] = None
            return None
        return disc

    # ═══════════ КОЛЕСО ОБМЕНА ═══════════
    def exchange_rubaly_to_chips(self, rubaly: int, chips: int) -> dict:
        """Обмен рубалов на фишки."""
        if rubaly <= 0 or chips <= 0:
            return {"ok": False, "message": "Некорректные числа"}
        if self.state["баланс"] < rubaly:
            return {"ok": False, "message": f"Не хватает: нужно {rubaly}"}
        self.subtract(rubaly, f"🔄 Обмен: {rubaly} руб. → {chips} фишек")
        self.state["фишки"] += chips
        self._log("+", 0, f"🔄 Получено {chips} фишек")
        self.commit()
        return {"ok": True, "message": f"Обменяно: {rubaly} → {chips} фишек"}

    def exchange_chips_to_rubaly(self, chips: int, rubaly: int) -> dict:
        """Обмен фишек на рубалов."""
        if rubaly <= 0 or chips <= 0:
            return {"ok": False, "message": "Некорректные числа"}
        if self.state["фишки"] < chips:
            return {"ok": False, "message": f"Не хватает: нужно {chips} фишек"}
        self.state["фишки"] -= chips
        self.add(rubaly, f"🔄 Обмен: {chips} фишек → {rubaly} руб.")
        self.commit()
        return {"ok": True, "message": f"Обменяно: {chips} фишек → {rubaly}"}
    
    # ═══════════ Сохранение ═══════════
    def commit(self, force: bool = False) -> None:
        now = time.time()
        if force or (now - self._last_save) >= 5.0:
            Storage.save(self.state)
            self._last_save = now
