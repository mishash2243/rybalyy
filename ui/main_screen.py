# ui/main_screen.py
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.list import TwoLineAvatarListItem, IconLeftWidget
from kivymd.toast import toast

from ui.dialogs import ask_amount


KV = """
#:import dp kivy.metrics.dp


<BalanceCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(150)
    padding: dp(16)
    spacing: dp(6)
    radius: [dp(20)]
    elevation: 2
    md_bg_color: app.theme_cls.primary_color

    MDLabel:
        text: app.balance_text
        halign: "center"
        font_style: "H3"
        bold: True
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1)

    MDLabel:
        text: app.subtitle_text
        halign: "center"
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 0.85)


<MainScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(10)

        BalanceCard:

        MDLabel:
            text: root.debt_text
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0.95, 0.35, 0.35, 1
            font_style: "H6"
            size_hint_y: None
            height: dp(24) if root.debt_text else 0
            opacity: 1 if root.debt_text else 0

        MDBoxLayout:
            orientation: "horizontal"
            spacing: dp(10)
            size_hint_y: None
            height: dp(56)

            MDRaisedButton:
                text: "+ Добавить"
                size_hint_x: 1
                md_bg_color: 0.16, 0.65, 0.35, 1
                on_release: root.on_add()

            MDRaisedButton:
                text: "− Снять"
                size_hint_x: 1
                md_bg_color: 0.75, 0.25, 0.25, 1
                on_release: root.on_subtract()

        MDBoxLayout:
            orientation: "horizontal"
            spacing: dp(10)
            size_hint_y: None
            height: dp(44)

            MDFlatButton:
                text: "+ Бонус"
                size_hint_x: 1
                on_release: root.on_bonus()

            MDFlatButton:
                text: "Снять штраф"
                size_hint_x: 1
                on_release: root.on_remove_fine()

        MDLabel:
            text: "История (последние 30)"
            font_style: "H6"
            size_hint_y: None
            height: dp(26)

        ScrollView:
            MDList:
                id: history_list
"""


class BalanceCard(MDCard):
    pass


class MainScreen(MDScreen):
    debt_text = StringProperty("")

    def on_kv_post(self, base_widget):
        self.refresh()
        return super().on_kv_post(base_widget)

    @property
    def _app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def on_add(self):
        ask_amount(
            "Начислить",
            "Сколько добавить?",
            lambda v: self._apply_add(v, "Ручное начисление"),
        )

    def on_subtract(self):
        ask_amount(
            "Снять",
            "Сколько снять?",
            lambda v: self._apply_sub(v, "Ручное списание"),
        )

    def on_bonus(self):
        app = self._app
        if app is None:
            return
        v = app.economy.random_bonus()
        app.economy.check_achievements()
        app.economy.commit()
        self.refresh()
        toast(f"+{v} бонус!")

    def on_remove_fine(self):
        ask_amount(
            "Снять штраф",
            "Какую сумму вернуть?",
            lambda v: self._apply_add(v, "Снятие штрафа (ручное)"),
        )

    def _apply_add(self, value: int, reason: str):
        app = self._app
        if app is None:
            return
        app.economy.add(value, reason)
        app.economy.check_achievements()
        app.economy.commit()
        self.refresh()

    def _apply_sub(self, value: int, reason: str):
        app = self._app
        if app is None:
            return
        app.economy.subtract(value, reason)
        app.economy.commit()
        self.refresh()

    def refresh(self):
        self.refresh_header()
        self.refresh_debt()
        self.refresh_history()

    def refresh_header(self):
        app = self._app
        if app is None:
            return
        state = app.state
        cur = state["настройки"].get("currency_name", "рубалы")
        bal = state["баланс"]
        lvl = state["уровень"]
        chips = state["фишки"]
        kop = app.economy.to_kopecks(bal)
        app.balance_text = f"{bal} {cur}"
        app.subtitle_text = f"Уровень {lvl} · {chips} фишек · {kop:.2f} коп."

    def refresh_debt(self):
        app = self._app
        if app is None:
            return
        self.debt_text = app.economy.debt_message()

    def refresh_history(self):
        app = self._app
        if app is None:
            return
        lst = self.ids.history_list
        lst.clear_widgets()
        for entry in reversed(app.state["история"][-30:]):
            ts = entry["ts"].replace("T", " ")
            sign = entry["sign"]
            color = (0.3, 0.75, 0.4, 1) if sign == "+" else (0.85, 0.35, 0.35, 1)
            item = TwoLineAvatarListItem(
                text=f"{sign}{entry['amount']}  ·  {entry['reason']}",
                secondary_text=f"{ts}   →  баланс: {entry['balance_after']}",
            )
            icon = IconLeftWidget(icon="plus" if sign == "+" else "minus")
            icon.theme_text_color = "Custom"
            icon.text_color = color
            item.add_widget(icon)
            lst.add_widget(item)


Builder.load_string(KV)
