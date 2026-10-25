# ui/challenges_screen.py
"""
Экран челленджей: ежедневный и недельный.
Автовыбор при входе, кнопки «Выполнено» / «Провалено» / «Сменить».
Поддержка секретных челленджей (⭐, золотой цвет).
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.toast import toast


KV = """
#:import dp kivy.metrics.dp


<DailyTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(12)

    MDLabel:
        text: "Ежедневный челлендж"
        halign: "center"
        font_style: "H6"
        size_hint_y: None
        height: dp(40)

    MDLabel:
        text: root.challenge_text
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(120)
        theme_text_color: "Custom"
        text_color: (0.95, 0.75, 0.2, 1) if root.is_secret else ((1, 1, 1, 1) if app.theme_cls.theme_style == "Dark" else (0, 0, 0, 1))

    MDLabel:
        text: root.reward_text
        halign: "center"
        theme_text_color: "Custom"
        text_color: 0.3, 0.75, 0.4, 1
        font_style: "H6"
        size_hint_y: None
        height: dp(40)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(30)

    Widget:

    MDRaisedButton:
        text: "Выполнено"
        size_hint_x: 1
        md_bg_color: 0.16, 0.65, 0.35, 1
        disabled: root.action_disabled
        on_release: root.on_done()

    MDFlatButton:
        text: "Провалено"
        size_hint_x: 1
        disabled: root.action_disabled
        on_release: root.on_fail()

    MDFlatButton:
        text: "Сменить челлендж"
        size_hint_x: 1
        disabled: root.action_disabled
        on_release: root.on_reroll()


<WeeklyTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(12)

    MDLabel:
        text: "Недельный челлендж"
        halign: "center"
        font_style: "H6"
        size_hint_y: None
        height: dp(40)

    MDLabel:
        text: root.challenge_text
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(120)

    MDLabel:
        text: root.reward_text
        halign: "center"
        theme_text_color: "Custom"
        text_color: 0.3, 0.75, 0.4, 1
        font_style: "H6"
        size_hint_y: None
        height: dp(40)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(30)

    Widget:

    MDRaisedButton:
        text: "Выполнено"
        size_hint_x: 1
        md_bg_color: 0.16, 0.65, 0.35, 1
        disabled: root.action_disabled
        on_release: root.on_done()

    MDFlatButton:
        text: "Провалено"
        size_hint_x: 1
        disabled: root.action_disabled
        on_release: root.on_fail()

    MDFlatButton:
        text: "Сменить челлендж"
        size_hint_x: 1
        disabled: root.action_disabled
        on_release: root.on_reroll()


<ChallengesScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Челленджи"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            elevation: 2

        MDTabs:
            id: tabs
"""


class DailyTab(MDBoxLayout, MDTabsBase):
    challenge_text = StringProperty("")
    reward_text = StringProperty("")
    status_text = StringProperty("")
    action_disabled = BooleanProperty(False)
    is_secret = BooleanProperty(False)

    _parent = None

    def on_done(self):
        app = self._get_app()
        if app is None:
            return
        ch = app.economy.complete_daily_challenge()
        if ch is None:
            toast("Уже закрыто")
            return
        app.economy.commit()
        toast(f"Награда: +{ch['reward']}")
        self._parent.refresh()

    def on_fail(self):
        app = self._get_app()
        if app is None:
            return
        ch = app.economy.fail_daily_challenge()
        if ch is None:
            toast("Уже закрыто")
            return
        app.economy.commit()
        toast("Отмечено как провалено")
        self._parent.refresh()

    def on_reroll(self):
        app = self._get_app()
        if app is None:
            return
        cur = app.economy.get_daily_challenge()
        cur_text = cur["text"] if cur else None
        app.economy.new_daily_challenge(exclude_text=cur_text)
        app.economy.commit()
        toast("Новый челлендж дня")
        self._parent.refresh()

    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()


class WeeklyTab(MDBoxLayout, MDTabsBase):
    challenge_text = StringProperty("")
    reward_text = StringProperty("")
    status_text = StringProperty("")
    action_disabled = BooleanProperty(False)

    _parent = None

    def on_done(self):
        app = self._get_app()
        if app is None:
            return
        ch = app.economy.complete_weekly_challenge()
        if ch is None:
            toast("Уже закрыто")
            return
        app.economy.commit()
        toast(f"Награда: +{ch['reward']}")
        self._parent.refresh()

    def on_fail(self):
        app = self._get_app()
        if app is None:
            return
        ch = app.economy.fail_weekly_challenge()
        if ch is None:
            toast("Уже закрыто")
            return
        app.economy.commit()
        toast("Отмечено как провалено")
        self._parent.refresh()

    def on_reroll(self):
        app = self._get_app()
        if app is None:
            return
        cur = app.economy.get_weekly_challenge()
        cur_text = cur["text"] if cur else None
        app.economy.new_weekly_challenge(exclude_text=cur_text)
        app.economy.commit()
        toast("Новый недельный челлендж")
        self._parent.refresh()

    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()


class ChallengesScreen(MDScreen):
    def on_kv_post(self, base_widget):
        self._daily = DailyTab(title="Ежедневный")
        self._weekly = WeeklyTab(title="Недельный")
        self._daily._parent = self
        self._weekly._parent = self
        self.ids.tabs.add_widget(self._daily)
        self.ids.tabs.add_widget(self._weekly)
        self.refresh()
        return super().on_kv_post(base_widget)

    @property
    def _app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def on_pre_enter(self, *args):
        self._ensure_challenges()
        self.refresh()

    def _ensure_challenges(self):
        app = self._app
        if app is None:
            return
        eco = app.economy
        if eco.get_daily_challenge() is None:
            eco.new_daily_challenge()
        if eco.get_weekly_challenge() is None:
            eco.new_weekly_challenge()
        eco.commit()

    def refresh(self):
        app = self._app
        if app is None:
            return

        # дневной
        ch = app.economy.get_daily_challenge()
        if ch:
            prefix = "⭐ " if ch.get("secret") else ""
            self._daily.challenge_text = prefix + ch["text"]
            self._daily.reward_text = f"Награда: +{ch['reward']}" if ch['reward'] else "Без награды"
            self._daily.status_text = self._status_label(ch["status"])
            self._daily.action_disabled = ch["status"] != "active"
            self._daily.is_secret = bool(ch.get("secret"))
        else:
            self._daily.challenge_text = "—"
            self._daily.reward_text = ""
            self._daily.status_text = "Челлендж дня не назначен"
            self._daily.action_disabled = True
            self._daily.is_secret = False

        # недельный
        ch = app.economy.get_weekly_challenge()
        if ch:
            self._weekly.challenge_text = ch["text"]
            self._weekly.reward_text = f"Награда: +{ch['reward']}" if ch['reward'] else "Без награды"
            self._weekly.status_text = self._status_label(ch["status"])
            self._weekly.action_disabled = ch["status"] != "active"
        else:
            self._weekly.challenge_text = "—"
            self._weekly.reward_text = ""
            self._weekly.status_text = "Челлендж недели не назначен"
            self._weekly.action_disabled = True

    @staticmethod
    def _status_label(status: str) -> str:
        return {
            "active": "В процессе",
            "done": "✅ Выполнено",
            "failed": "❌ Провалено",
        }.get(status, "")

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
