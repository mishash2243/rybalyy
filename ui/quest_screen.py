# ui/quest_screen.py
"""
Экран квест-цепочки. Все элементы строятся в Python.
"""
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.toast import toast


class QuestScreen(MDScreen):
    _built = False

    def on_kv_post(self, base_widget):
        if not self._built:
            self._build_ui()
            self._built = True
        return super().on_kv_post(base_widget)

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        bar = MDTopAppBar(title="Квест", elevation=2)
        bar.left_action_items = [["arrow-left", lambda x: self.go_back()]]
        root.add_widget(bar)

        scroll = ScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(14),
            spacing=dp(10),
        )
        content.bind(minimum_height=content.setter("height"))

        # Карточка квеста
        self.card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=dp(14),
            spacing=dp(6),
            radius=[dp(14)],
            elevation=2,
        )
        self.title_label = MDLabel(
            text="",
            font_style="H5",
            bold=True,
            size_hint_y=None,
            height=dp(40),
        )
        self.progress_label = MDLabel(
            text="",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(26),
        )
        self.step_label = MDLabel(
            text="",
            font_style="H6",
            halign="left",
            valign="top",
        )
        self.step_label.bind(size=self.step_label.setter("text_size"))
        self.reward_label = MDLabel(
            text="",
            font_style="Body1",
            size_hint_y=None,
            height=dp(24),
        )

        self.card.add_widget(self.title_label)
        self.card.add_widget(self.progress_label)
        self.card.add_widget(self.step_label)
        self.card.add_widget(self.reward_label)
        content.add_widget(self.card)

        # Кнопки
        self.btn_done = MDRaisedButton(
            text="✅ Этап выполнен",
            size_hint_x=1,
            md_bg_color=(0.16, 0.65, 0.35, 1),
        )
        self.btn_done.bind(on_release=lambda *_: self.on_step_done())
        content.add_widget(self.btn_done)

        self.btn_new = MDFlatButton(text="🔄 Новый квест", size_hint_x=1)
        self.btn_new.bind(on_release=lambda *_: self.on_new_quest())
        content.add_widget(self.btn_new)

        self.btn_abandon = MDFlatButton(text="❌ Отменить квест", size_hint_x=1)
        self.btn_abandon.bind(on_release=lambda *_: self.on_abandon())
        content.add_widget(self.btn_abandon)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    @property
    def _app(self):
        return MDApp.get_running_app()

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = self._app
        if app is None or not self._built:
            return
        q = app.economy.quest_current()
        if q is None:
            app.economy.quest_start_new()
            q = app.economy.quest_current()

        if q is None:
            return

        self.title_label.text = q["title"]
        total = len(q["steps"])
        idx = q.get("step_index", 0)
        self.progress_label.text = f"Этап {min(idx + 1, total)} из {total}"
        self.reward_label.text = f"🏆 Награда: +{q['reward']} рубалов"

        if q.get("done"):
            self.step_label.text = "🎉 Квест завершён!"
            self.btn_done.disabled = True
            self.btn_done.text = "✅ Готово"
            self.btn_new.disabled = False
            self.btn_abandon.disabled = True
        else:
            self.step_label.text = f"→ {q['steps'][idx]}"
            self.btn_done.disabled = False
            self.btn_done.text = "✅ Этап выполнен"
            self.btn_new.disabled = True
            self.btn_abandon.disabled = False

    def on_step_done(self):
        app = self._app
        if app is None:
            return
        res = app.economy.quest_complete_step()
        if not res.get("ok"):
            toast(res.get("message", "Ошибка"))
            return
        toast(res["message"])
        self.refresh()

    def on_new_quest(self):
        app = self._app
        if app is None:
            return
        cur = app.economy.quest_current()
        cur_id = cur["id"] if cur else None
        app.economy.quest_start_new(exclude_id=cur_id)
        toast("Новый квест")
        self.refresh()

    def on_abandon(self):
        app = self._app
        if app is None:
            return
        res = app.economy.quest_abandon()
        toast(res.get("message", ""))
        # сразу запустим новый, чтобы экран не пустовал
        app.economy.quest_start_new()
        self.refresh()

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()
