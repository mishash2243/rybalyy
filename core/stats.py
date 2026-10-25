# core/stats.py
"""
Статистика: заработал / потратил за периоды, топы, средние, график.
Всё считается из state['история'] и state['счётчики'].
"""
from datetime import datetime, timedelta


class Stats:
    def __init__(self, state: dict):
        self.state = state

    # ─────────── Вспомогательное ───────────
    def _parse_ts(self, ts: str):
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None

    def _entries_since(self, days: int) -> list:
        """Все записи истории за последние N дней."""
        now = datetime.now()
        threshold = now - timedelta(days=days)
        out = []
        for e in self.state.get("история", []):
            dt = self._parse_ts(e.get("ts", ""))
            if dt and dt >= threshold:
                out.append(e)
        return out

    def _entries_today(self) -> list:
        today = datetime.now().date().isoformat()
        return [
            e for e in self.state.get("история", [])
            if e.get("ts", "").startswith(today)
        ]

    # ─────────── Итоги по периодам ───────────
    def summary(self, days: int) -> dict:
        """
        Заработал / потратил за N дней.
        Учитываются только записи с ненулевой суммой.
        """
        entries = self._entries_since(days)
        earned = 0
        spent = 0
        for e in entries:
            amt = int(e.get("amount", 0))
            if amt <= 0:
                continue
            if e.get("sign") == "+":
                earned += amt
            elif e.get("sign") == "−":
                spent += amt
        return {
            "earned": earned,
            "spent": spent,
            "net": earned - spent,
            "count": len(entries),
        }

    def summary_today(self) -> dict:
        entries = self._entries_today()
        earned = sum(int(e["amount"]) for e in entries if e.get("sign") == "+" and int(e.get("amount", 0)) > 0)
        spent = sum(int(e["amount"]) for e in entries if e.get("sign") == "−" and int(e.get("amount", 0)) > 0)
        return {"earned": earned, "spent": spent, "net": earned - spent, "count": len(entries)}

    def average_per_day(self, days: int = 30) -> float:
        s = self.summary(days)
        return s["earned"] / max(days, 1)

    # ─────────── Топы ───────────
    def top_tasks(self, limit: int = 3) -> list:
        """Самые частые задания из истории."""
        counts = {}
        for e in self.state.get("история", []):
            r = e.get("reason", "")
            if r.startswith("Задание: "):
                name = r[len("Задание: "):]
                counts[name] = counts.get(name, 0) + 1
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    def top_fines(self, limit: int = 3) -> list:
        counts = {}
        for e in self.state.get("история", []):
            r = e.get("reason", "")
            if r.startswith("Штраф: "):
                name = r[len("Штраф: "):]
                counts[name] = counts.get(name, 0) + 1
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    def top_purchases(self, limit: int = 3) -> list:
        counts = {}
        for e in self.state.get("история", []):
            r = e.get("reason", "")
            if r.startswith("Покупка: "):
                name = r[len("Покупка: "):]
                counts[name] = counts.get(name, 0) + 1
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    # ─────────── Спины ───────────
    def spins_stats(self) -> dict:
        c = self.state.get("счётчики", {})
        total = c.get("спинов_всего", 0)
        mini = c.get("спинов_мини", 0)
        fortune = max(total - mini, 0)
        jackpots = c.get("джекпотов", 0)
        # побед/проигрышей считаем по истории
        wins = 0
        losses = 0
        for e in self.state.get("история", []):
            r = e.get("reason", "")
            if r.startswith("Фортуна:"):
                if "Пусто" in r:
                    losses += 1
                elif "фишка" not in r:
                    wins += 1
        return {
            "total": total,
            "mini": mini,
            "fortune": fortune,
            "jackpots": jackpots,
            "wins": wins,
            "losses": losses,
        }

    # ─────────── График по дням ───────────
    def daily_earned(self, days: int = 7) -> list:
        """
        Список (дата, заработано) за последние N дней.
        Возвращает список словарей {'date': 'DD.MM', 'earned': int}
        """
        today = datetime.now().date()
        result = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            key = d.isoformat()
            earned = 0
            for e in self.state.get("история", []):
                if e.get("ts", "").startswith(key) and e.get("sign") == "+":
                    amt = int(e.get("amount", 0))
                    if amt > 0:
                        earned += amt
            result.append({"date": d.strftime("%d.%m"), "earned": earned})
        return result

    def text_chart(self, days: int = 7) -> str:
        """Текстовый график из блоков."""
        data = self.daily_earned(days)
        max_val = max((d["earned"] for d in data), default=0)
        if max_val == 0:
            return "Нет данных за период"
        lines = []
        for d in data:
            bars = int(d["earned"] / max_val * 20)
            lines.append(f"{d['date']}  {'█' * bars}  {d['earned']}")
        return "\n".join(lines)

    # ─────────── Сводка для экрана ───────────
    def full_summary(self) -> dict:
        return {
            "today": self.summary_today(),
            "week": self.summary(7),
            "month": self.summary(30),
            "avg_day": self.average_per_day(30),
            "tasks": self.top_tasks(3),
            "fines": self.top_fines(3),
            "purchases": self.top_purchases(3),
            "spins": self.spins_stats(),
            "chart": self.text_chart(7),
            "balance": self.state.get("баланс", 0),
            "level": self.state.get("уровень", 1),
            "chips": self.state.get("фишки", 0),
            "history_count": len(self.state.get("история", [])),
        }
