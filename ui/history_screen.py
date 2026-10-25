# ui/history_screen.py
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarListItem, IconLeftWidget


KV = """
#:import dp kivy.metrics.dp

<HistoryScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "История"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            elevation: 2

        ScrollView:
            MDList:
                id: history_list
"""


class HistoryScreen(MDScreen):
    def on_kv_post(self, base_widget):
        self.refresh()
        return super().on_kv_post(base_widget)

    @property
    def _app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def refresh(self):
        app = self._app
        if app is None:
            return
        lst = self.ids.history_list
        lst.clear_widgets()
        # было 500 — стало 100
        for entry in reversed(app.state["история"][-100:]):
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

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
