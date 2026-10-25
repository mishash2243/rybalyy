# ui/stats_screen.py
"""
Экран статистики. Все карточки строятся в Python.
"""
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar


class StatsScreen(MDScreen):
    _built = False   # ← class-атрибут, доступен до __init__

    def on_kv_post(self, base_widget):
        if not self._built:
            self._build_ui()
            self._built = True
        return super().on_kv_post(base_widget)

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        bar = MDTopAppBar(title="Статистика", elevation=2)
        bar.left_action_items = [["arrow-left", lambda x: self.go_back()]]
        root.add_widget(bar)

        scroll = ScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(12),
            spacing=dp(10),
        )
        content.bind(minimum_height=content.setter("height"))

        self.card_balance = self._make_card("Баланс")
        self.card_today = self._make_card("Сегодня")
        self.card_week = self._make_card("За неделю")
        self.card_month = self._make_card("За месяц")
        self.card_top_tasks = self._make_card("Топ-3 задания")
        self.card_top_fines = self._make_card("Топ-3 штрафа")
        self.card_spins = self._make_card("Спины")
        self.card_chart = self._make_card("Заработок за 7 дней")

        for c in (
            self.card_balance, self.card_today, self.card_week, self.card_month,
            self.card_top_tasks, self.card_top_fines, self.card_spins, self.card_chart,
        ):
            content.add_widget(c)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _make_card(self, title: str) -> MDCard:
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(130),
            padding=dp(14),
            spacing=dp(6),
            radius=[dp(14)],
            elevation=1,
        )
        t = MDLabel(
            text=title,
            font_style="H6",
            bold=True,
            size_hint_y=None,
            height=dp(28),
        )
        b = MDLabel(
            text="",
            font_style="Body1",
            halign="left",
            valign="top",
        )
        b.bind(size=b.setter("text_size"))
        card.add_widget(t)
        card.add_widget(b)
        card.body_label = b
        return card

    @property
    def _app(self):
        return MDApp.get_running_app()

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = self._app
        if app is None or not self._built:
            return
        from core.stats import Stats
        s = Stats(app.state).full_summary()

        self.card_balance.body_label.text = (
            f"Баланс: {s['balance']} рубалов\n"
            f"Уровень: {s['level']} · Фишек: {s['chips']}"
        )

        t = s["today"]
        self.card_today.body_label.text = (
            f"Заработано: +{t['earned']}\n"
            f"Потрачено: −{t['spent']}\n"
            f"Итого: {t['net']:+d}"
        )

        w = s["week"]
        self.card_week.body_label.text = (
            f"Заработано: +{w['earned']}\n"
            f"Потрачено: −{w['spent']}\n"
            f"Итого: {w['net']:+d}"
        )

        m = s["month"]
        self.card_month.body_label.text = (
            f"Заработано: +{m['earned']}\n"
            f"Потрачено: −{m['spent']}\n"
            f"Итого: {m['net']:+d}\n"
            f"Средний в день: {s['avg_day']:.1f}"
        )

        if s["tasks"]:
            self.card_top_tasks.body_label.text = "\n".join(
                f"{i+1}. {name} — {cnt}" for i, (name, cnt) in enumerate(s["tasks"])
            )
        else:
            self.card_top_tasks.body_label.text = "Пока нет данных"

        if s["fines"]:
            self.card_top_fines.body_label.text = "\n".join(
                f"{i+1}. {name} — {cnt}" for i, (name, cnt) in enumerate(s["fines"])
            )
        else:
            self.card_top_fines.body_label.text = "Пока нет данных"

        sp = s["spins"]
        self.card_spins.body_label.text = (
            f"Всего: {sp['total']}\n"
            f"Мини-колесо: {sp['mini']}\n"
            f"Фортуна: {sp['fortune']}\n"
            f"Джекпотов: {sp['jackpots']}"
        )

        self.card_chart.body_label.text = s["chart"]

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()
