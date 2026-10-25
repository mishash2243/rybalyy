# ui/inventory_screen.py
"""
Экран инвентаря: купленные и выпавшие награды.
Кнопка «Использовать». Особый случай — «Выбрать себе задание».
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.toast import toast


KV = """
#:import dp kivy.metrics.dp


<InventoryRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(64)
    padding: dp(8)
    spacing: dp(8)
    radius: [dp(12)]
    elevation: 1
    md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.97, 1)

    MDIconButton:
        icon: root.icon_name
        theme_icon_color: "Custom"
        icon_color: root.icon_color
        disabled: True
        size_hint_x: None
        width: dp(40)
        pos_hint: {"center_y": 0.5}

    MDBoxLayout:
        orientation: "vertical"
        size_hint_x: 1
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.item_name
            font_style: "Subtitle1"
            shorten: True
            shorten_from: "right"
            size_hint_y: None
            height: dp(24)

        MDLabel:
            text: root.sub_text
            theme_text_color: "Custom"
            text_color: root.sub_color
            font_style: "Caption"
            size_hint_y: None
            height: dp(18)

    MDRaisedButton:
        text: root.action_text
        size_hint_x: None
        width: dp(120)
        pos_hint: {"center_y": 0.5}
        md_bg_color: 0.16, 0.65, 0.35, 1
        on_release: root.trigger_use()


<InventoryScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Инвентарь"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            elevation: 2

        MDLabel:
            text: root.summary_text
            halign: "center"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: dp(30)

        ScrollView:
            MDList:
                id: inventory_list
"""


class InventoryRow(MDCard):
    item_name = StringProperty("")
    sub_text = StringProperty("")
    icon_name = StringProperty("gift")
    icon_color = ListProperty([0.35, 0.6, 0.9, 1])
    sub_color = ListProperty([0.7, 0.7, 0.7, 1])
    action_text = StringProperty("Использовать")

    def __init__(self, item: dict, screen, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self._screen = screen
        self.item_name = item["name"]

        kind = item.get("kind", "usable")
        if kind == "progress":
            cur = item.get("progress", 0)
            tgt = item.get("target", 5)
            self.sub_text = f"Копится: {cur} из {tgt}"
            self.icon_name = "progress-clock"
            self.icon_color = [0.9, 0.7, 0.3, 1]
            self.action_text = "Добавить"
        elif kind == "pick_task":
            self.sub_text = "Секретный сектор: выбери задание"
            self.icon_name = "star"
            self.icon_color = [0.95, 0.75, 0.2, 1]
            self.action_text = "Выбрать"
        else:
            self.sub_text = f"Получено: {item.get('ts', '')}"
            self.icon_name = "gift"
            self.action_text = "Использовать"

    def trigger_use(self):
        self._screen.use_item(self.item)


class InventoryScreen(MDScreen):
    summary_text = StringProperty("")

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
        lst = self.ids.inventory_list
        lst.clear_widgets()

        items = app.economy.inventory_active()
        if not items:
            lst.add_widget(MDLabel(
                text="Инвентарь пуст\nКупи что-нибудь в магазине или выиграй в Фортуне",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(120),
            ))
            self.summary_text = ""
            return

        self.summary_text = f"Активных наград: {len(items)}"
        for item in items:
            lst.add_widget(InventoryRow(item=item, screen=self))

    # ─── использование ───
    def use_item(self, item: dict):
        app = self._app
        if app is None:
            return
        kind = item.get("kind", "usable")
        if kind == "progress":
            self._progress_item(item)
        elif kind == "pick_task":
            self._pick_task_dialog(item)
        else:
            result = app.economy.inventory_use(item["id"])
            app.economy.commit()
            toast(result["message"])
            self.refresh()

    def _progress_item(self, item: dict):
        """Копится: увеличивает progress на 1. При достижении target — выдаёт награду."""
        item["progress"] = item.get("progress", 0) + 1
        target = item.get("target", 5)
        if item["progress"] >= target:
            item["used"] = True
            app = self._app
            app.economy.add(200, f"Собрана награда: {item['name']}")
            app.economy.commit()
            toast(f"Собрано! +200 рубалов")
        else:
            app = self._app
            app.economy.commit()
            toast(f"Прогресс: {item['progress']} из {target}")
        self.refresh()

    def _pick_task_dialog(self, item: dict):
        """Секретный сектор: брат сам вводит название и сумму."""
        name_field = MDTextField(
            hint_text="Название задания",
            size_hint_y=None,
            height=dp(48),
        )
        amount_field = MDTextField(
            hint_text="Сумма (до 100)",
            input_filter="int",
            helper_text="Максимум 100",
            helper_text_mode="on_error",
            size_hint_y=None,
            height=dp(48),
        )
        from kivymd.uix.boxlayout import MDBoxLayout
        box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(120),
        )
        box.add_widget(name_field)
        box.add_widget(amount_field)

        dlg = MDDialog(
            title="Секретный сектор",
            type="custom",
            content_cls=box,
            buttons=[],
        )
        dlg.pos_hint = {"center_x": 0.5, "top": 0.95}
        dlg.size_hint = (0.9, None)
        dlg.height = dp(320)

        def confirm(*_):
            name = (name_field.text or "").strip()
            try:
                amount = int((amount_field.text or "").strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                amount_field.error = True
                return
            if not name:
                name_field.error = True
                return
            app = self._app
            result = app.economy.inventory_pick_task(item["id"], name, amount)
            app.economy.commit()
            dlg.dismiss()
            toast(f"+{result['amount']} за «{result['name']}»")
            self.refresh()

        dlg.buttons = [
            MDFlatButton(text="Отмена", on_release=lambda *_: dlg.dismiss()),
            MDRaisedButton(text="OK", on_release=confirm),
        ]
        dlg.open()

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
