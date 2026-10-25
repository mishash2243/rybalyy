# ui/wheel_screen.py
"""
Экран колёс: Мини / Фортуна / Испытания / Скидки / Обмен.
"""
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.toast import toast


KV = """
#:import dp kivy.metrics.dp


<MiniTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(10)

    MDLabel:
        text: "🎡 Мини-колесо"
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(50)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(40)

    Widget:

    MDRaisedButton:
        text: "Крутить бесплатно"
        size_hint_x: 1
        md_bg_color: 0.16, 0.65, 0.35, 1
        disabled: root.disabled_button
        on_release: root.spin()

    MDLabel:
        text: "Призы: +5, +10, +15, +1 фишка, Пусто, +1 к удаче"
        halign: "center"
        theme_text_color: "Secondary"
        font_style: "Caption"
        size_hint_y: None
        height: dp(40)


<FortuneTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(10)

    MDLabel:
        text: "🎰 Колесо Фортуны"
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(50)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(80)

    Widget:

    MDRaisedButton:
        text: "Крутить за " + str(root.stake)
        size_hint_x: 1
        md_bg_color: 0.65, 0.35, 0.85, 1
        on_release: root.spin()

    MDFlatButton:
        text: "Обменять фишки"
        size_hint_x: 1
        on_release: root.open_chips_exchange()

    MDLabel:
        text: "За каждый спин +1 фишка. 10 фишек = приз или бесплатный спин."
        halign: "center"
        theme_text_color: "Secondary"
        font_style: "Caption"
        size_hint_y: None
        height: dp(40)


<TrialTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(10)

    MDLabel:
        text: "💪 Колесо испытаний"
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(50)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(40)

    Widget:

    MDRaisedButton:
        text: "Крутить испытание"
        size_hint_x: 1
        md_bg_color: 0.8, 0.5, 0.2, 1
        disabled: root.disabled_button
        on_release: root.spin()

    MDLabel:
        text: "Выполни — получишь награду. Кулдаун 4 часа."
        halign: "center"
        theme_text_color: "Secondary"
        font_style: "Caption"
        size_hint_y: None
        height: dp(40)


<DiscountTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(10)

    MDLabel:
        text: "🎟 Колесо скидок"
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(50)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(40)

    MDLabel:
        text: root.active_text
        halign: "center"
        theme_text_color: "Custom"
        text_color: 0.35, 0.85, 0.45, 1
        font_style: "Body1"
        size_hint_y: None
        height: dp(80)

    Widget:

    MDRaisedButton:
        text: "Крутить скидку"
        size_hint_x: 1
        md_bg_color: 0.2, 0.7, 0.5, 1
        disabled: root.disabled_button
        on_release: root.spin()

    MDLabel:
        text: "Скидка 30–70% на случайный приз. Действует 24 часа."
        halign: "center"
        theme_text_color: "Secondary"
        font_style: "Caption"
        size_hint_y: None
        height: dp(40)


<ExchangeTab>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(10)

    MDLabel:
        text: "🔄 Колесо обмена"
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: dp(50)

    MDLabel:
        text: root.status_text
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(40)

    Widget:

    MDRaisedButton:
        text: "100 рубалов → 3 фишки"
        size_hint_x: 1
        md_bg_color: 0.3, 0.6, 0.9, 1
        on_release: root.exchange_rub_to_chips(100, 3)

    MDRaisedButton:
        text: "200 рубалов → 7 фишек"
        size_hint_x: 1
        md_bg_color: 0.3, 0.6, 0.9, 1
        on_release: root.exchange_rub_to_chips(200, 7)

    MDRaisedButton:
        text: "5 фишек → 80 рубалов"
        size_hint_x: 1
        md_bg_color: 0.9, 0.6, 0.3, 1
        on_release: root.exchange_chips_to_rub(5, 80)

    MDLabel:
        text: "Обменивай между рубалами и фишками."
        halign: "center"
        theme_text_color: "Secondary"
        font_style: "Caption"
        size_hint_y: None
        height: dp(40)


<WheelScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Колёса"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            elevation: 2

        MDTabs:
            id: tabs
"""


class MiniTab(MDBoxLayout, MDTabsBase):
    status_text = StringProperty("")
    disabled_button = BooleanProperty(False)
    _parent_screen = None

    def spin(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        try:
            result = app.economy.spin_mini_wheel()
        except ValueError as e:
            toast(str(e))
            return
        app.economy.commit()
        self._parent_screen.refresh()
        _show_result("Мини-колесо", result["prize"])


class FortuneTab(MDBoxLayout, MDTabsBase):
    status_text = StringProperty("")
    stake = NumericProperty(130)
    _parent_screen = None

    def spin(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        try:
            result = app.economy.spin_fortune_wheel()
        except ValueError as e:
            toast(str(e))
            return
        app.economy.commit()
        self._parent_screen.refresh()
        title = "🎉 ДЖЕКПОТ!" if result["jackpot"] else "Колесо фортуны"
        delta = result["delta"]
        if delta > 0:
            text = f"{result['prize']}\n\nБаланс: +{delta} рубалов"
        elif delta < 0:
            text = f"{result['prize']}\n\nБаланс: {delta} рубалов"
        else:
            text = f"{result['prize']}"
        _show_result(title, text)

    def open_chips_exchange(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        chips = app.state["фишки"]
        info = (
            f"Фишек: {chips}\n\n"
            f"• 3 фишки → +20 рубалов\n"
            f"• 5 фишек → +50 рубалов\n"
            f"• 10 фишек → гарантированный приз (100–150)\n"
            f"• 10 фишек → бесплатный спин Фортуны"
        )
        dlg = MDDialog(title="Обмен фишек", text=info, buttons=[])
        dlg.pos_hint = {"center_x": 0.5, "top": 0.95}
        dlg.size_hint = (0.9, None)
        dlg.height = dp(400)

        def do_3(*_):
            if app.economy.chips_exchange_small(3, 20, "Обмен 3 фишек: +20"):
                app.economy.commit()
                dlg.dismiss()
                toast("+20 рубалов")
                self._parent_screen.refresh()
            else:
                toast("Не хватает фишек")

        def do_5(*_):
            if app.economy.chips_exchange_small(5, 50, "Обмен 5 фишек: +50"):
                app.economy.commit()
                dlg.dismiss()
                toast("+50 рубалов")
                self._parent_screen.refresh()
            else:
                toast("Не хватает фишек")

        def do_10_prize(*_):
            try:
                res = app.economy.chips_exchange_guaranteed()
            except ValueError as e:
                toast(str(e))
                return
            app.economy.commit()
            dlg.dismiss()
            toast(f"Приз: +{res['prize']} рубалов")
            self._parent_screen.refresh()

        def do_10_spin(*_):
            if not app.economy.chips_exchange_free_spin():
                toast("Не хватает фишек")
                return
            app.economy.commit()
            dlg.dismiss()
            try:
                result = app.economy.spin_fortune_wheel(free=True)
            except ValueError as e:
                toast(str(e))
                return
            app.economy.commit()
            self._parent_screen.refresh()
            _show_result("Бесплатный спин", result["prize"])

        dlg.buttons = [
            MDFlatButton(text="3→+20", on_release=do_3),
            MDFlatButton(text="5→+50", on_release=do_5),
            MDFlatButton(text="10→приз", on_release=do_10_prize),
            MDFlatButton(text="10→спин", on_release=do_10_spin),
        ]
        dlg.open()


class TrialTab(MDBoxLayout, MDTabsBase):
    status_text = StringProperty("")
    disabled_button = BooleanProperty(False)
    _parent_screen = None

    def spin(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        try:
            res = app.economy.spin_trial_wheel()
        except ValueError as e:
            toast(str(e))
            return
        app.economy.commit()
        self._parent_screen.refresh()
        if res["reward"] > 0:
            toast(f"Выпало: {res['name']} (+{res['reward']})")
        else:
            toast("Пусто")


class DiscountTab(MDBoxLayout, MDTabsBase):
    status_text = StringProperty("")
    active_text = StringProperty("")
    disabled_button = BooleanProperty(False)
    _parent_screen = None

    def spin(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        try:
            res = app.economy.spin_discount_wheel()
        except ValueError as e:
            toast(str(e))
            return
        app.economy.commit()
        self._parent_screen.refresh()
        if res["discount"] > 0:
            toast(f"Скидка {res['discount']}% на «{res['prize_name']}»")
        else:
            toast("Пусто")


class ExchangeTab(MDBoxLayout, MDTabsBase):
    status_text = StringProperty("")
    _parent_screen = None

    def exchange_rub_to_chips(self, rubaly, chips):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        res = app.economy.exchange_rubaly_to_chips(rubaly, chips)
        toast(res["message"])
        if res["ok"]:
            self._parent_screen.refresh()

    def exchange_chips_to_rub(self, chips, rubaly):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        res = app.economy.exchange_chips_to_rubaly(chips, rubaly)
        toast(res["message"])
        if res["ok"]:
            self._parent_screen.refresh()


class WheelScreen(MDScreen):
    def on_kv_post(self, base_widget):
        self._mini = MiniTab(title="Мини")
        self._fortune = FortuneTab(title="Фортуна")
        self._trial = TrialTab(title="Испытания")
        self._discount = DiscountTab(title="Скидки")
        self._exchange = ExchangeTab(title="Обмен")
        for t in (self._mini, self._fortune, self._trial, self._discount, self._exchange):
            t._parent_screen = self
            self.ids.tabs.add_widget(t)
        self.refresh()
        return super().on_kv_post(base_widget)

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
        eco = app.economy

        # мини
        if eco.can_spin_mini():
            self._mini.status_text = "Сегодня ещё не крутил!"
            self._mini.disabled_button = False
        else:
            self._mini.status_text = eco.mini_wheel_cooldown_left()
            self._mini.disabled_button = True

        # фортуна
        stake = int(app.state.get("джекпот", 130))
        luck = app.state.get("удача", 0)
        jc = min(0.05 + luck * 0.005, 0.15)
        self._fortune.stake = stake
        self._fortune.status_text = (
            f"Ставка: {stake} руб.\n"
            f"Баланс: {app.state['баланс']} · Фишек: {app.state['фишки']}\n"
            f"Удача: +{luck} (шанс джекпота: {jc*100:.1f}%)"
        )

        # испытания
        if eco.can_spin_trial():
            self._trial.status_text = "Готово к спину!"
            self._trial.disabled_button = False
        else:
            self._trial.status_text = eco.trial_cooldown_left()
            self._trial.disabled_button = True

        # скидки
        if eco.can_spin_discount():
            self._discount.status_text = "Готово к спину!"
            self._discount.disabled_button = False
        else:
            self._discount.status_text = eco.discount_cooldown_left()
            self._discount.disabled_button = True

        disc = eco.active_discount()
        if disc:
            self._discount.active_text = (
                f"Активная скидка: {disc['discount']}%\n"
                f"«{disc['prize_name']}»: {disc['original_price']} → {disc['new_price']}"
            )
        else:
            self._discount.active_text = ""

        # обмен
        self._exchange.status_text = (
            f"Баланс: {app.state['баланс']} руб.\n"
            f"Фишек: {app.state['фишки']}"
        )

    def go_back(self):
        app = self._app
        if app is not None:
            app.go_main()


def _show_result(title: str, text: str):
    dlg = MDDialog(
        title=title,
        text=text,
        buttons=[MDRaisedButton(text="ОК", on_release=lambda *_: dlg.dismiss())],
    )
    dlg.open()


Builder.load_string(KV)
