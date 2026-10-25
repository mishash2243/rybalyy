# ui/pocket_screen.py
"""
Экран «Карманные деньги»: обмен рубалов на копейки.
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.toast import toast
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField


KV = """
#:import dp kivy.metrics.dp

<PocketScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Карманные деньги"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            elevation: 2

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(14)

            MDLabel:
                text: root.info_text
                halign: "center"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: dp(60)

            MDTextField:
                id: kop_field
                hint_text: "Сколько копеек вывести?"
                input_filter: "float"
                size_hint_y: None
                height: dp(56)

            MDRaisedButton:
                text: "Вывести"
                size_hint_x: 1
                md_bg_color: 0.16, 0.65, 0.35, 1
                on_release: root.withdraw_typed()

            MDLabel:
                text: "Быстрый вывод:"
                halign: "center"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: dp(30)

            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(8)
                size_hint_y: None
                height: dp(50)

                MDFlatButton:
                    text: "1 коп."
                    size_hint_x: 1
                    on_release: root.withdraw_quick(1.0)

                MDFlatButton:
                    text: "5 коп."
                    size_hint_x: 1
                    on_release: root.withdraw_quick(5.0)

                MDFlatButton:
                    text: "10 коп."
                    size_hint_x: 1
                    on_release: root.withdraw_quick(10.0)

                MDFlatButton:
                    text: "Всё"
                    size_hint_x: 1
                    on_release: root.withdraw_all()

            Widget:
"""


class PocketScreen(MDScreen):
    info_text = StringProperty("")

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
        kop = app.economy.max_kopecks_available()
        bal = app.state["баланс"]
        self.info_text = (
            f"Курс: 5 рубалов = 1 копейка\n"
            f"Баланс: {bal} руб. = {kop:.2f} коп."
        )

    def withdraw_quick(self, value: float):
        app = self._app
        if app is None:
            return
        res = app.economy.withdraw_to_kopecks(value)
        toast(res["message"])
        self.refresh()

    def withdraw_all(self):
        app = self._app
        if app is None:
            return
        kop = app.economy.max_kopecks_available()
        if kop <= 0:
            toast("Нечего выводить")
            return
        self.withdraw_quick(kop)

    def withdraw_typed(self):
        app = self._app
        if app is None:
            return
        field = self.ids.kop_field
        text = (field.text or "").strip().replace(",", ".")
        if not text:
            toast("Введи сумму копеек")
            return
        try:
            value = float(text)
            if value <= 0:
                raise ValueError
        except ValueError:
            toast("Некорректное число")
            return
        self.withdraw_quick(value)
        field.text = ""

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
