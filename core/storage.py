# core/storage.py
"""
Загрузка и сохранение состояния приложения в JSON.
Работает и на ПК, и на Android.
"""
import json
from pathlib import Path

from core.defaults import (
    DEFAULT_TASKS, DEFAULT_FINES, DEFAULT_REWARDS,
    DAILY_CHALLENGES, WEEKLY_CHALLENGES, DEFAULT_SETTINGS,
)


def _detect_data_dir() -> Path:
    try:
        import os
        if "ANDROID_ARGUMENT" in os.environ or "ANDROID_ROOT" in os.environ:
            from android.storage import app_storage_path  # type: ignore
            return Path(app_storage_path())
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent / "data"


DATA_DIR = _detect_data_dir()
DATA_FILE = DATA_DIR / "state.json"


class Storage:

    @staticmethod
    def default_state() -> dict:
        return {
            "баланс": 0,
            "уровень": 1,
            "фишки": 0,
            "джекпот": DEFAULT_SETTINGS["jackpot_base"],
            "удача": 0,
            "задания": list(DEFAULT_TASKS),
            "штрафы": list(DEFAULT_FINES),
            "призы": list(DEFAULT_REWARDS),
            "челленджи_ежедневные": list(DAILY_CHALLENGES),
            "челленджи_недельные": list(WEEKLY_CHALLENGES),
            "история": [],
            "настройки": dict(DEFAULT_SETTINGS),
            "активный_челлендж_дня": None,
            "активный_челлендж_недели": None,
            "инвентарь": [],
            "активные_эффекты": {
                "golden_ticket": False,
                "double_task": False,
            },
            "достижения": [],
            "счётчики": {
                "спинов_всего": 0,
                "спинов_мини": 0,
                "джекпотов": 0,
                "покупок": 0,
                "заданий": 0,
                "челленджей": 0,
                "недельных_выполнено": 0,
                "чистых_дней": 0,
                "дней_подряд_без_штрафа": 0,
                "последний_штраф_день": "",
                "последний_день_захода": "",
                "задания_сегодня": [],
                "дата_заданий_сегодня": "",
                "все_задания_день_флаг": False,
                "лотерея_куплено": 0,
                "лотерея_выиграно_руб": 0,
                "лотерея_потрачено": 0,
                "испытаний_выпало": 0,
                "испытаний_выполнено": 0,
            },
            "цели": [],
            "копилка": 0,
            "активный_квест": None,
            "скидка": None,
        }

    @classmethod
    def load(cls) -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            state = cls.default_state()
            cls.save(state)
            return state

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Storage] Ошибка чтения {DATA_FILE}: {e}. Создаю новый.")
            state = cls.default_state()
            cls.save(state)
            return state

        default = cls.default_state()
        for key, value in default.items():
            state.setdefault(key, value)
        for k, v in default["настройки"].items():
            state["настройки"].setdefault(k, v)
        for k, v in default["счётчики"].items():
            state["счётчики"].setdefault(k, v)
        for k, v in default["активные_эффекты"].items():
            state["активные_эффекты"].setdefault(k, v)
        return state

    @staticmethod
    def save(state: dict) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = DATA_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        tmp.replace(DATA_FILE)

    @staticmethod
    def export_to(path: str, state: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    @staticmethod
    def import_from(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
