# ui/lottery_screen.py
"""
Экран лотереи: купить билет, разыграть приз.
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.toast import toast


KV = """
#:import dp kivy.metrics.dp


<PrizeRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(34)
    padding: (dp(10), 0, dp(10), 0)

    MDLabel:
        text: root.left
        theme_text_color: "Custom"
        text_color: (0.85, 0.85, 0.85, 1) if app.theme_cls.theme_style == "Dark" else (0.2, 0.2, 0.2, 1)
        font_style: "Body2"

    MDLabel:
        text: root.right
        halign: "right"
        theme_text_color: "Custom"
        text_color: 0.35, 0.75, 0.45, 1
        font_style: "Body2"


<StatCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(100)
    padding: dp(14)
    spacing: dp(6)
    radius: [dp(14)]
    elevation: 1
    md_bg_color: 0.35, 0.25, 0.45, 1

    MDLabel:
        text: "🎟 Лотерея"
        halign: "center"
        font_style: "H5"
        bold: True
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1)

    MDLabel:
        text: "Билет: 50 рубалов"
        halign: "center"
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 0.85)
        font_style: "Body1"


<LotteryScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Лотерея"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            elevation: 2

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(14)
                spacing: dp(12)

                StatCard:

                MDRaisedButton:
                    text: "🎲 Купить билет (50)"
                    size_hint_x: 1
                    md_bg_color: 0.65, 0.35, 0.85, 1
                    on_release: root.buy_ticket()

                MDLabel:
                    text: "Статистика"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(28)

                MDLabel:
                    text: root.stats_text
                    theme_text_color: "Secondary"
                    font_style: "Body1"
                    size_hint_y: None
                    height: dp(80)

                MDLabel:
                    text: "Возможные призы"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(28)

                PrizeRow:
                    left: "🎉 Джекпот"
                    right: "+500 (1%)"
                PrizeRow:
                    left: "+200"
                    right: "2%"
                PrizeRow:
                    left: "+100"
                    right: "5%"
                PrizeRow:
                    left: "+50"
                    right: "10%"
                PrizeRow:
                    left: "+30"
                    right: "15%"
                PrizeRow:
                    left: "+10"
                    right: "25%"
                PrizeRow:
                    left: "🎯 5 фишек"
                    right: "10%"
                PrizeRow:
                    left: "🎫 Золотой билет"
                    right: "2%"
                PrizeRow:
                    left: "Пусто"
                    right: "30%"

                Widget:
                    size_hint_y: None
                    height: dp(20)
"""


class PrizeRow(MDBoxLayout):
    left = StringProperty("")
    right = StringProperty("")


class StatCard(MDCard):
    pass


class LotteryScreen(MDScreen):
    stats_text = StringProperty("")

    @property
    def _app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = self._app
        if app is None:
            return
        s = app.economy.lottery_stats()
        net = s["выиграно_руб"] - s["потрачено"]
        self.stats_text = (
            f"Билетов куплено: {s['куплено']}\n"
            f"Потрачено: {s['потрачено']}\n"
            f"Выиграно: {s['выиграно_руб']}\n"
            f"Итог: {net:+d}"
        )

    def buy_ticket(self):
        app = self._app
        if app is None:
            return
        res = app.economy.lottery_buy_ticket()
        if not res["ok"]:
            toast(res["message"])
            return
        self.refresh()
        self._show_result(res["prize"] or "Пусто", res["message"])

    def _show_result(self, title: str, text: str):
        dlg = MDDialog(
            title=f"🎟 {title}",
            text=text,
            buttons=[
                MDRaisedButton(text="ОК", on_release=lambda *_: dlg.dismiss()),
            ],
        )
        dlg.open()

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
