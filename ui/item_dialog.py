# ui/item_dialog.py
"""
Диалог добавления / редактирования позиции (задание, штраф, приз).
Два поля: название и цена.
"""
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField


class ItemForm(MDBoxLayout):
    """Контейнер для двух полей ввода."""

    def __init__(self, name: str = "", price: str = "", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(150)
        self.padding = (0, dp(8), 0, 0)

        self.name_field = MDTextField(
            hint_text="Название",
            text=name,
            size_hint_y=None,
            height=dp(48),
        )
        self.price_field = MDTextField(
            hint_text="Цена (целое число)",
            text=price,
            input_filter="int",
            size_hint_y=None,
            height=dp(48),
        )
        self.add_widget(self.name_field)
        self.add_widget(self.price_field)


def ask_item(title: str, on_confirm, *, name: str = "", price: int | str = ""):
    """
    Открывает диалог ввода позиции.
    on_confirm(name: str, price: int) — вызывается при OK.
    price для штрафов можно вводить положительным — знак применится отдельно.
    """
    form = ItemForm(name=name, price=str(price) if price != "" else "")

    dialog = MDDialog(
        title=title,
        type="custom",
        content_cls=form,
        buttons=[],
    )
    dialog.pos_hint = {"center_x": 0.5, "top": 0.95}
    dialog.size_hint = (0.9, None)
    dialog.height = dp(340)

    def cancel(*_):
        dialog.dismiss()

    def confirm(*_):
        n = (form.name_field.text or "").strip()
        p_text = (form.price_field.text or "").strip()
        ok = True
        if not n:
            form.name_field.error = True
            ok = False
        try:
            p = int(p_text)
        except ValueError:
            form.price_field.error = True
            ok = False
            p = 0
        if not ok:
            return
        dialog.dismiss()
        on_confirm(n, p)

    form.price_field.on_text_validate = confirm

    dialog.buttons = [
        MDFlatButton(text="Отмена", on_release=cancel),
        MDRaisedButton(text="OK", on_release=confirm),
    ]
    dialog.open()
    return dialog
