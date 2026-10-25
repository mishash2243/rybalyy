# ui/achievements_screen.py
"""
Экран достижений: список всех ачивок.
Разблокированные — цветные, заблокированные — серые.
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton


KV = """
#:import dp kivy.metrics.dp


<AchievementRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(72)
    padding: dp(10)
    spacing: dp(10)
    radius: [dp(12)]
    elevation: 1
    md_bg_color: root.card_color

    MDIconButton:
        icon: root.icon_name
        theme_icon_color: "Custom"
        icon_color: root.icon_color
        disabled: True
        size_hint_x: None
        width: dp(48)
        pos_hint: {"center_y": 0.5}

    MDBoxLayout:
        orientation: "vertical"
        size_hint_x: 1
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.title_text
            font_style: "Subtitle1"
            bold: True
            shorten: True
            shorten_from: "right"
            size_hint_y: None
            height: dp(24)

        MDLabel:
            text: root.desc_text
            theme_text_color: "Custom"
            text_color: root.desc_color
            font_style: "Caption"
            size_hint_y: None
            height: dp(18)

        MDLabel:
            text: root.reward_text
            theme_text_color: "Custom"
            text_color: root.reward_color
            font_style: "Caption"
            size_hint_y: None
            height: dp(18)


<AchievementsScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Достижения"
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
                id: ach_list
"""


class AchievementRow(MDCard):
    title_text = StringProperty("")
    desc_text = StringProperty("")
    reward_text = StringProperty("")
    icon_name = StringProperty("trophy-outline")
    icon_color = ListProperty([0.5, 0.5, 0.5, 1])
    card_color = ListProperty([0.2, 0.2, 0.25, 0.6])
    desc_color = ListProperty([0.7, 0.7, 0.7, 1])
    reward_color = ListProperty([0.7, 0.7, 0.7, 1])

    def __init__(self, ach: dict, unlocked: bool, **kwargs):
        super().__init__(**kwargs)
        self.title_text = ach["title"]
        self.desc_text = ach["desc"]
        reward = ach.get("reward", 0)
        self.reward_text = f"Награда: +{reward}" if reward > 0 else "Без награды"

        if unlocked:
            self.icon_name = "trophy"
            self.icon_color = [0.95, 0.75, 0.2, 1]
            self.card_color = [0.18, 0.30, 0.20, 1]
            self.desc_color = [0.85, 0.85, 0.85, 1]
            self.reward_color = [0.35, 0.85, 0.45, 1]
        else:
            self.icon_name = "lock-outline"
            self.icon_color = [0.55, 0.55, 0.55, 1]
            self.card_color = [0.16, 0.16, 0.20, 1]
            self.desc_color = [0.55, 0.55, 0.55, 1]
            self.reward_color = [0.55, 0.55, 0.55, 1]


class AchievementsScreen(MDScreen):
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
        lst = self.ids.ach_list
        lst.clear_widgets()

        all_ach = app.economy.achievements_all()
        unlocked = sum(1 for _, u in all_ach if u)
        total = len(all_ach)
        self.summary_text = f"Разблокировано: {unlocked} из {total}"

        # сортировка: сначала разблокированные, потом по категории
        all_ach_sorted = sorted(all_ach, key=lambda t: (not t[1], t[0]["category"], t[0]["title"]))

        current_cat = None
        for ach, is_unlocked in all_ach_sorted:
            cat = ach["category"]
            if cat != current_cat:
                current_cat = cat
                header = MDLabel(
                    text=f"── {cat} ──",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height=dp(36),
                    font_style="Subtitle2",
                )
                lst.add_widget(header)
            lst.add_widget(AchievementRow(ach=ach, unlocked=is_unlocked))

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


Builder.load_string(KV)
