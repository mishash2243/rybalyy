# ui/items_screen.py
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from ui.item_dialog import ask_item


KV = """
#:import dp kivy.metrics.dp


<ItemRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(64)
    padding: dp(8)
    spacing: dp(8)
    radius: [dp(12)]
    elevation: 1
    md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.97, 1)
    on_release: root.trigger_apply()

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
            text: root.price_text
            theme_text_color: "Custom"
            text_color: root.price_color
            font_style: "Caption"
            size_hint_y: None
            height: dp(18)

    MDIconButton:
        icon: "pencil"
        size_hint_x: None
        width: dp(40)
        pos_hint: {"center_y": 0.5}
        on_release: root.trigger_edit()

    MDIconButton:
        icon: "delete"
        theme_icon_color: "Custom"
        icon_color: (0.8, 0.3, 0.3, 1)
        size_hint_x: None
        width: dp(40)
        pos_hint: {"center_y": 0.5}
        on_release: root.trigger_delete()


<ItemsScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: root.screen_title
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            right_action_items: [["plus", lambda x: root.on_add_new()]]
            elevation: 2

        ScrollView:
            MDList:
                id: items_list

        MDBoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12)
            spacing: dp(12)

            MDFlatButton:
                text: "Назад"
                on_release: root.go_back()
"""


class ItemRow(MDCard):
    item_name = StringProperty("")
    price_text = StringProperty("")
    icon_name = StringProperty("check")
    icon_color = ListProperty([0.3, 0.75, 0.4, 1])
    price_color = ListProperty([0.3, 0.75, 0.4, 1])

    def __init__(self, index: int, item: dict, mode: str, screen, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.mode = mode
        self._screen = screen
        self.item_name = item["name"]

        price = int(item["price"])
        if mode == "fines":
            self.price_text = f"−{abs(price)}"
            self.icon_name = "alert"
            self.icon_color = [0.85, 0.35, 0.35, 1]
            self.price_color = [0.85, 0.35, 0.35, 1]
        elif mode == "rewards":
            self.price_text = f"−{price}"
            self.icon_name = "cart"
            self.icon_color = [0.35, 0.6, 0.9, 1]
            self.price_color = [0.35, 0.6, 0.9, 1]
        else:
            self.price_text = f"+{price}" if price >= 0 else f"{price}"
            self.icon_name = "check"
            self.icon_color = [0.3, 0.75, 0.4, 1]
            self.price_color = [0.3, 0.75, 0.4, 1]

    def trigger_apply(self):
        self._screen._apply(self.index)

    def trigger_edit(self):
        self._screen._edit(self.index)

    def trigger_delete(self):
        self._screen._confirm_delete(self.index)


class ItemsScreen(MDScreen):
    mode = StringProperty("tasks")

    @property
    def state_key(self) -> str:
        return {"tasks": "задания", "fines": "штрафы", "rewards": "призы"}[self.mode]

    @property
    def screen_title(self) -> str:
        return {"tasks": "Задания", "fines": "Штрафы", "rewards": "Магазин"}[self.mode]

    @property
    def _app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def on_kv_post(self, base_widget):
        self.refresh()
        return super().on_kv_post(base_widget)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = self._app
        if app is None:
            return
        lst = self.ids.items_list
        lst.clear_widgets()

        items = app.economy.list_get(self.state_key)
        if not items:
            lst.add_widget(MDLabel(
                text="Пусто",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(80),
            ))
            return

        for idx, item in enumerate(items):
            lst.add_widget(ItemRow(index=idx, item=item, mode=self.mode, screen=self))

    def _apply(self, idx: int):
        app = self._app
        if app is None:
            return
        try:
            if self.mode == "tasks":
                res = app.economy.apply_task(idx)
                if res.get("doubled"):
                    toast("×2! Двойное начисление")
                else:
                    toast("Начислено")
            elif self.mode == "fines":
                res = app.economy.apply_fine(idx)
                if res.get("cancelled"):
                    toast("🎫 Штраф отменён билетом")
                else:
                    toast("Списано")
            elif self.mode == "rewards":
                ok = app.economy.buy_reward(idx)
                if not ok:
                    toast("Недостаточно рубалов")
                    return
                toast("Куплено")
        except Exception as e:
            toast(f"Ошибка: {e}")
            return

    def _edit(self, idx: int):
        app = self._app
        if app is None:
            return
        item = app.economy.list_get(self.state_key)[idx]
        ask_item(
            "Изменить",
            on_confirm=lambda name, price: self._do_update(idx, name, price),
            name=item["name"],
            price=item["price"],
        )

    def _do_update(self, idx: int, name: str, price: int):
        app = self._app
        if app is None:
            return
        if self.mode == "fines":
            price = -abs(price)
        app.economy.item_update(self.state_key, idx, name, price)
        app.economy.commit()
        self.refresh()

    def _confirm_delete(self, idx: int):
        app = self._app
        if app is None:
            return
        item = app.economy.list_get(self.state_key)[idx]
        dlg = MDDialog(
            title="Удалить?",
            text=f"«{item['name']}»",
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(
                    text="Удалить",
                    on_release=lambda *_: (dlg.dismiss(), self._do_delete(idx)),
                ),
            ],
        )
        dlg.open()

    def _do_delete(self, idx: int):
        app = self._app
        if app is None:
            return
        app.economy.item_delete(self.state_key, idx)
        app.economy.commit()
        self.refresh()

    def on_add_new(self):
        ask_item(
            "Новая позиция",
            on_confirm=lambda name, price: self._do_add(name, price),
        )

    def _do_add(self, name: str, price: int):
        app = self._app
        if app is None:
            return
        if self.mode == "fines":
            price = -abs(price)
        app.economy.item_add(self.state_key, name, price)
        app.economy.commit()
        self.refresh()

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
