# ui/goals_screen.py
"""
Экран целей: копим на что-то.
Плюс копилка на этом же экране.
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast


KV = """
#:import dp kivy.metrics.dp


<GoalRow>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(110)
    padding: dp(10)
    spacing: dp(4)
    radius: [dp(12)]
    elevation: 1
    md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else (0.95, 0.95, 0.97, 1)

    MDLabel:
        text: root.title_text
        font_style: "Subtitle1"
        bold: True
        size_hint_y: None
        height: dp(24)

    MDLabel:
        text: root.progress_text
        theme_text_color: "Custom"
        text_color: 0.35, 0.75, 0.45, 1
        font_style: "H6"
        size_hint_y: None
        height: dp(28)

    MDBoxLayout:
        orientation: "horizontal"
        spacing: dp(6)
        size_hint_y: None
        height: dp(40)

        MDFlatButton:
            text: "Отложить"
            on_release: root.trigger_put()

        MDFlatButton:
            text: "Вернуть"
            on_release: root.trigger_take()

        MDFlatButton:
            text: "Удалить"
            on_release: root.trigger_delete()


<GoalsScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Цели и копилка"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            right_action_items: [["plus", lambda x: root.on_add_goal()]]
            elevation: 2

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(10)

                MDLabel:
                    text: "🐷 Копилка"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(28)

                StatCardPiggy:

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: dp(6)
                    size_hint_y: None
                    height: dp(44)

                    MDFlatButton:
                        text: "Положить 50"
                        size_hint_x: 1
                        on_release: root.piggy_put_50()

                    MDFlatButton:
                        text: "Достать 50"
                        size_hint_x: 1
                        on_release: root.piggy_take_50()

                    MDFlatButton:
                        text: "Всё"
                        size_hint_x: 1
                        on_release: root.piggy_empty()

                MDLabel:
                    text: "🎯 Цели"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(28)

                MDLabel:
                    text: "Активные цели"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(20)

                MDList:
                    id: goals_list

                MDLabel:
                    text: "Достигнутые цели"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(20)

                MDList:
                    id: goals_done_list

                Widget:
                    size_hint_y: None
                    height: dp(20)


<StatCardPiggy>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(70)
    padding: dp(12)
    radius: [dp(12)]
    elevation: 1
    md_bg_color: 0.25, 0.35, 0.45, 1

    MDLabel:
        text: app.piggy_text
        halign: "center"
        font_style: "H5"
        bold: True
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1)
"""


class StatCardPiggy(MDCard):
    pass


class GoalRow(MDCard):
    title_text = StringProperty("")
    progress_text = StringProperty("")

    def __init__(self, goal: dict, screen, **kwargs):
        super().__init__(**kwargs)
        self.goal = goal
        self._screen = screen
        self.title_text = goal["name"]
        t = goal["target"]
        s = goal["saved"]
        pct = int(s / t * 100) if t > 0 else 0
        marker = "✅ " if goal.get("done") else ""
        self.progress_text = f"{marker}{s} / {t}  ({pct}%)"

    def trigger_put(self):
        self._screen.goal_put_dialog(self.goal)

    def trigger_take(self):
        self._screen.goal_take_dialog(self.goal)

    def trigger_delete(self):
        self._screen.goal_delete_confirm(self.goal)


class GoalsScreen(MDScreen):

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
        # копилка
        piggy = app.state.get("копилка", 0)
        app.piggy_text = f"🐷 {piggy} рубалов"

        # активные цели
        lst = self.ids.goals_list
        lst.clear_widgets()
        active = app.economy.goals_active()
        if not active:
            lst.add_widget(MDLabel(
                text="Нет активных целей. Нажми + чтобы добавить.",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(40),
                halign="center",
            ))
        else:
            for g in active:
                lst.add_widget(GoalRow(goal=g, screen=self))

        # достигнутые
        lst2 = self.ids.goals_done_list
        lst2.clear_widgets()
        done = app.economy.goals_done()
        if not done:
            lst2.add_widget(MDLabel(
                text="—",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(30),
                halign="center",
            ))
        else:
            for g in done:
                lst2.add_widget(GoalRow(goal=g, screen=self))

    # ─────────── создание цели ───────────
    def on_add_goal(self):
        name_field = MDTextField(
            hint_text="На что копим?",
            size_hint_y=None,
            height=dp(48),
        )
        target_field = MDTextField(
            hint_text="Сколько нужно?",
            input_filter="int",
            size_hint_y=None,
            height=dp(48),
        )
        box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(110),
        )
        box.add_widget(name_field)
        box.add_widget(target_field)

        dlg = MDDialog(
            title="🎯 Новая цель",
            type="custom",
            content_cls=box,
            buttons=[],
        )
        dlg.pos_hint = {"center_x": 0.5, "top": 0.95}
        dlg.size_hint = (0.9, None)
        dlg.height = dp(320)

        def confirm(*_):
            name = (name_field.text or "").strip()
            t_text = (target_field.text or "").strip()
            if not name:
                name_field.error = True
                return
            try:
                target = int(t_text)
                if target <= 0:
                    raise ValueError
            except ValueError:
                target_field.error = True
                return
            app = self._app
            app.economy.goal_add(name, target)
            dlg.dismiss()
            toast(f"Цель создана: {name}")
            self.refresh()

        dlg.buttons = [
            MDFlatButton(text="Отмена", on_release=lambda *_: dlg.dismiss()),
            MDRaisedButton(text="Создать", on_release=confirm),
        ]
        dlg.open()

    # ─────────── операции с целями ───────────
    def _amount_dialog(self, title: str, on_ok, max_hint: str = ""):
        field = MDTextField(
            hint_text="Сумма",
            input_filter="int",
            helper_text=max_hint,
            helper_text_mode="on_error",
            size_hint_y=None,
            height=dp(48),
        )
        dlg = MDDialog(
            title=title,
            type="custom",
            content_cls=field,
            buttons=[],
        )
        dlg.pos_hint = {"center_x": 0.5, "top": 0.95}
        dlg.size_hint = (0.9, None)
        dlg.height = dp(280)

        def confirm(*_):
            text = (field.text or "").strip()
            try:
                value = int(text)
                if value <= 0:
                    raise ValueError
            except ValueError:
                field.error = True
                return
            dlg.dismiss()
            on_ok(value)

        dlg.buttons = [
            MDFlatButton(text="Отмена", on_release=lambda *_: dlg.dismiss()),
            MDRaisedButton(text="OK", on_release=confirm),
        ]
        dlg.open()

    def goal_put_dialog(self, goal: dict):
        app = self._app
        bal = app.state["баланс"]
        self._amount_dialog(
            f"Отложить в «{goal['name']}»",
            on_ok=lambda v: self._do_goal_put(goal["id"], v),
            max_hint=f"На балансе: {bal}",
        )

    def _do_goal_put(self, goal_id: int, amount: int):
        app = self._app
        res = app.economy.goal_put(goal_id, amount)
        toast(res["message"])
        self.refresh()
        app.refresh_main() if hasattr(app, "refresh_main") else None

    def goal_take_dialog(self, goal: dict):
        self._amount_dialog(
            f"Вернуть из «{goal['name']}»",
            on_ok=lambda v: self._do_goal_take(goal["id"], v),
            max_hint=f"В цели: {goal['saved']}",
        )

    def _do_goal_take(self, goal_id: int, amount: int):
        app = self._app
        res = app.economy.goal_take(goal_id, amount)
        toast(res["message"])
        self.refresh()

    def goal_delete_confirm(self, goal: dict):
        dlg = MDDialog(
            title="Удалить цель?",
            text=f"«{goal['name']}»\n{saved_note(goal)}",
            buttons=[],
        )

        def do_delete(*_):
            app = self._app
            res = app.economy.goal_delete(goal["id"])
            dlg.dismiss()
            toast(res["message"])
            self.refresh()

        dlg.buttons = [
            MDFlatButton(text="Отмена", on_release=lambda *_: dlg.dismiss()),
            MDRaisedButton(text="Удалить", on_release=do_delete),
        ]
        dlg.open()

    # ─────────── копилка ───────────
    def piggy_put_50(self):
        app = self._app
        res = app.economy.piggy_put(50)
        toast(res["message"])
        self.refresh()

    def piggy_take_50(self):
        app = self._app
        res = app.economy.piggy_take(50)
        toast(res["message"])
        self.refresh()

    def piggy_empty(self):
        app = self._app
        res = app.economy.piggy_empty()
        toast(res["message"])
        self.refresh()

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


def saved_note(goal: dict) -> str:
    s = goal.get("saved", 0)
    if s > 0:
        return f"В цели {s} — они вернутся на баланс."
    return "Цель пустая."


Builder.load_string(KV)
