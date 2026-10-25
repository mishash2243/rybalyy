# main.py
"""
Приложение «Рубалы» — точка входа.
"""
import os

from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDFlatButton
from ui.lottery_screen import LotteryScreen
from ui.quest_screen import QuestScreen

from core.storage import Storage
from core.economy import Economy
from ui.main_screen import MainScreen
from ui.history_screen import HistoryScreen
from ui.items_screen import ItemsScreen
from ui.wheel_screen import WheelScreen
from ui.challenges_screen import ChallengesScreen
from ui.inventory_screen import InventoryScreen
from ui.achievements_screen import AchievementsScreen
from ui.stats_screen import StatsScreen
from ui.pocket_screen import PocketScreen
from ui.goals_screen import GoalsScreen


def _is_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_ROOT" in os.environ


class RubalyApp(MDApp):
    balance_text = StringProperty("0 рубalов")
    subtitle_text = StringProperty("Уровень 1 · 0 фишек · 0.00 коп.")
    piggy_text = StringProperty("🐷 0 рубалов")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = Storage.load()
        self.economy = Economy(self.state)
        self.sm = None
        self.menu_dialog = None

    def build(self):
        self.title = "Рубалы"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.theme_style = (
            "Dark" if self.state["настройки"].get("dark_theme") else "Light"
        )

        if not _is_android():
            Window.size = (420, 760)

        self.sm = MDScreenManager()
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(ItemsScreen(mode="tasks",   name="tasks"))
        self.sm.add_widget(ItemsScreen(mode="fines",   name="fines"))
        self.sm.add_widget(ItemsScreen(mode="rewards", name="rewards"))
        self.sm.add_widget(WheelScreen(name="wheels"))
        self.sm.add_widget(ChallengesScreen(name="challenges"))
        self.sm.add_widget(InventoryScreen(name="inventory"))
        self.sm.add_widget(AchievementsScreen(name="achievements"))
        self.sm.add_widget(StatsScreen(name="stats"))
        self.sm.add_widget(PocketScreen(name="pocket"))
        self.sm.add_widget(GoalsScreen(name="goals"))
        self.sm.add_widget(HistoryScreen(name="history"))
        self.sm.add_widget(LotteryScreen(name="lottery"))
        self.sm.add_widget(QuestScreen(name="quest"))

        root = MDBoxLayout(orientation="vertical")
        root.add_widget(self._build_toolbar())
        root.add_widget(self.sm)
        return root

    def _build_toolbar(self) -> MDTopAppBar:
        bar = MDTopAppBar(title="Рубалы", elevation=2)
        bar.left_action_items = [
            ["menu", lambda x: self.open_menu(), "Меню"],
        ]
        bar.right_action_items = [
            ["theme-light-dark", lambda x: self.toggle_theme(), "Тема"],
        ]
        return bar

    def open_menu(self):
        entries = [
            ("home",              "Главная",     self.go_main),
            ("check-circle",      "Задания",     lambda: self.go_items("tasks")),
            ("alert-circle",      "Штрафы",      lambda: self.go_items("fines")),
            ("cart",              "Магазин",     lambda: self.go_items("rewards")),
            ("rotate-3d-variant", "Колёса",      self.go_wheels),
            ("trophy",            "Челленджи",   self.go_challenges),
            ("bag-personal",      "Инвентарь",   self.go_inventory),
            ("medal",             "Достижения",  self.go_achievements),
            ("chart-bar",         "Статистика",  self.go_stats),
            ("target",            "Цели",        self.go_goals),
            ("cash",              "Карманные",   self.go_pocket),
            ("ticket",            "Лотерея",     self.go_lottery),
            ("history",           "История",     self.go_history),
            ("sword-cross",       "Квест",        self.go_quest),
        ]

        scroll = MDScrollView(size_hint_y=None, height=dp(48 * len(entries)))
        lst = MDList()
        scroll.add_widget(lst)

        dlg = MDDialog(
            title="Меню",
            type="custom",
            content_cls=scroll,
            buttons=[
                MDFlatButton(
                    text="Закрыть",
                    on_release=lambda *_: dlg.dismiss(),
                ),
            ],
        )

        for icon, text, action in entries:
            item = OneLineIconListItem(text=text)
            item.add_widget(IconLeftWidget(icon=icon))
            item.bind(
                on_release=lambda inst, a=action: (dlg.dismiss(), a())
            )
            lst.add_widget(item)

        self.menu_dialog = dlg
        dlg.open()

    # ─────────── навигация ───────────
    def go_main(self):
        self.sm.current = "main"
        self.sm.get_screen("main").refresh()

    def go_items(self, mode: str):
        name = {"tasks": "tasks", "fines": "fines", "rewards": "rewards"}[mode]
        screen = self.sm.get_screen(name)
        self.sm.current = name
        screen.refresh()

    def go_wheels(self):
        screen = self.sm.get_screen("wheels")
        self.sm.current = "wheels"
        screen.refresh()

    def go_challenges(self):
        screen = self.sm.get_screen("challenges")
        self.sm.current = "challenges"
        screen.refresh()

    def go_inventory(self):
        screen = self.sm.get_screen("inventory")
        self.sm.current = "inventory"
        screen.refresh()

    def go_achievements(self):
        screen = self.sm.get_screen("achievements")
        self.sm.current = "achievements"
        screen.refresh()

    def go_stats(self):
        screen = self.sm.get_screen("stats")
        self.sm.current = "stats"
        screen.refresh()

    def go_pocket(self):
        screen = self.sm.get_screen("pocket")
        self.sm.current = "pocket"
        screen.refresh()

    def go_goals(self):
        screen = self.sm.get_screen("goals")
        self.sm.current = "goals"
        screen.refresh()

    def go_history(self):
        hist = self.sm.get_screen("history")
        hist.refresh()
        self.sm.current = "history"

    def go_lottery(self):
        screen = self.sm.get_screen("lottery")
        self.sm.current = "lottery"
        screen.refresh()

    def go_quest(self):
        screen = self.sm.get_screen("quest")
        self.sm.current = "quest"
        screen.refresh()

    # ─────────── тема ───────────
    def toggle_theme(self):
        dark = self.theme_cls.theme_style == "Dark"
        self.theme_cls.theme_style = "Light" if dark else "Dark"
        self.state["настройки"]["dark_theme"] = not dark
        Storage.save(self.state)

    # ─────────── выход ───────────
    def on_stop(self):
        try:
            self.economy.commit(force=True)
        except Exception:
            pass


if __name__ == "__main__":
    RubalyApp().run()
