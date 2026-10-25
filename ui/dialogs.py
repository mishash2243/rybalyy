# ui/dialogs.py
from kivy.metrics import dp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField


def ask_amount(title: str, hint: str, on_confirm, *, helper: str = "Целое число"):
    field = MDTextField(
        hint_text=hint,
        input_filter="int",
        helper_text=helper,
        helper_text_mode="on_error",
        size_hint_y=None,
        height=dp(48),
    )

    dialog = MDDialog(
        title=title,
        type="custom",
        content_cls=field,
        buttons=[],
    )

    def cancel(*_):
        dialog.dismiss()

    def confirm(*_):
        text = (field.text or "").strip()
        try:
            value = int(text)
        except ValueError:
            field.error = True
            return
        if value <= 0:
            field.error = True
            return
        dialog.dismiss()
        on_confirm(value)

    field.on_text_validate = confirm

    def focus(*_):
        field.focus = True
    dialog.bind(on_open=focus)

    dialog.buttons = [
        MDFlatButton(text="Отмена", on_release=cancel),
        MDRaisedButton(text="OK", on_release=confirm),
    ]
    dialog.open()
    return dialog


def confirm(title: str, text: str, on_yes, *, yes_text: str = "Да", no_text: str = "Отмена"):
    """Простой диалог подтверждения."""
    dlg = MDDialog(
        title=title,
        text=text,
        buttons=[
            MDFlatButton(text=no_text, on_release=lambda *_: dlg.dismiss()),
            MDRaisedButton(
                text=yes_text,
                on_release=lambda *_: (dlg.dismiss(), on_yes()),
            ),
        ],
    )
    dlg.open()
    return dlg
