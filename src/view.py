import logging
import threading
import wx

from main import (
    get_cookies_data,
    get_search_templates,
    run_report,
    save_cookies_data,
    save_search_templates,
)

logger = logging.getLogger(__name__)


class TemplateEditDialog(wx.Dialog):
    """Кастомне діалогове вікно для створення або редагування шаблону пошуку.

    Надає текстове поле для введення рядка шаблону, а такожкнопки підтвердження і скасування.
    """

    def __init__(self, parent, title: str, initial_value: str = ""):
        """Ініціалізує діалогове вікно редагування шаблону.

        Args:
            parent (wx.Window): Батьківський компонент інтерфейсу.
            title (str): Заголовок вікна.
            initial_value (str, optional): Початкове значення текстового поля.
                За замовчуванням "".
        """
        super().__init__(parent, title=title, size=(350, 150))
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(self, value=initial_value)
        sizer.Add(self.text_ctrl, 0, wx.EXPAND | wx.ALL, 15)

        btn_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if btn_sizer:
            sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 15)

        self.SetSizer(sizer)
        self.CenterOnParent()

    def get_value(self) -> str:
        """Отримує введене значення шаблону без зайвих пробілів на початку та в кінці.

        Returns:
            str: Очищений рядок шаблону.
        """
        return self.text_ctrl.GetValue().strip()


class TemplatesDialog(wx.Dialog):
    """Вікно управління списками шаблонів пошуку.

    Дозволяє переглядати, додавати, редагувати та видаляти текстові шаблони,
    які використовуються для фільтрації та підрахунку витрат у звіті.
    """

    def __init__(self, parent):
        """Ініціалізує вікно управління шаблонами та завантажує їхній список.

        Args:
            parent (wx.Window): Батьківський компонент інтерфейсу.
        """
        super().__init__(parent, title="Шаблони пошуку", size=(450, 350))

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.list_box = wx.ListBox(self, style=wx.LB_SINGLE)
        sizer.Add(self.list_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_add = wx.Button(self, label="Додати")
        self.btn_edit = wx.Button(self, label="Редагувати")
        self.btn_delete = wx.Button(self, label="Видалити")

        btn_sizer.Add(self.btn_add, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_edit, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_delete, 0)

        sizer.Add(btn_sizer, 0, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)

        self.SetSizer(sizer)

        self.btn_add.Bind(wx.EVT_BUTTON, self._add_item)
        self.btn_edit.Bind(wx.EVT_BUTTON, self._edit_item)
        self.btn_delete.Bind(wx.EVT_BUTTON, self._delete_item)

        self._load_templates()

    def _load_templates(self):
        """Завантажує список шаблонів із конфігураційного файлу та відображає їх у списку."""
        self.list_box.Clear()
        templates = get_search_templates()
        for t in templates:
            self.list_box.Append(t)

    def _save_templates(self):
        """Зберігає поточний вміст елемента ListBox у конфігураційний файл.

        Виводить повідомлення про помилку, якщо запис не вдався.
        """
        templates = [self.list_box.GetString(i) for i in range(self.list_box.GetCount())]
        if not save_search_templates(templates):
            wx.MessageBox("Не вдалося зберегти шаблони!", "Помилка", wx.OK | wx.ICON_ERROR)

    def _add_item(self, event):
        """Обробник події натискання кнопки додавання нового шаблону.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        dlg = TemplateEditDialog(self, title="Новий шаблон")
        if dlg.ShowModal() == wx.ID_OK:
            text = dlg.get_value()
            if text:
                self.list_box.Append(text)
                self._save_templates()
        dlg.Destroy()

    def _edit_item(self, event):
        """Обробник події натискання кнопки редагування обраного шаблону.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        sel = self.list_box.GetSelection()
        if sel == wx.NOT_FOUND:
            return

        current_text = self.list_box.GetString(sel)
        dlg = TemplateEditDialog(self, title="Редагувати шаблон", initial_value=current_text)
        if dlg.ShowModal() == wx.ID_OK:
            text = dlg.get_value()
            if text:
                self.list_box.SetString(sel, text)
                self._save_templates()
        dlg.Destroy()

    def _delete_item(self, event):
        """Обробник події натискання кнопки видалення обраного шаблону.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        sel = self.list_box.GetSelection()
        if sel != wx.NOT_FOUND:
            self.list_box.Delete(sel)
            self._save_templates()


class CookiesDialog(wx.Dialog):
    """Вікно оновлення токена сесії PHPSESSID.

    Забезпечує можливість введення та збереження значення cookies, необхідного
    для авторизації запитів до особистого кабінету TurboSMS.
    """

    def __init__(self, parent):
        """Ініціалізує вікно оновлення cookies та завантажує поточне значення.

        Args:
            parent (wx.Window): Батьківський компонент інтерфейсу.
        """
        super().__init__(parent, title="Оновлення PHPSESSID", size=(380, 160))

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, label='Ключ "PHPSESSID":')
        self.entry_sessid = wx.TextCtrl(self)

        sizer.Add(label, 0, wx.ALL, 10)
        sizer.Add(self.entry_sessid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.btn_save = wx.Button(self, label="Зберегти")
        sizer.Add(self.btn_save, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(sizer)

        self.btn_save.Bind(wx.EVT_BUTTON, self._save_cookie)
        self._load_cookie()

    def _load_cookie(self):
        """Завантажує поточне значення PHPSESSID із конфігураційного файлу."""
        cookies = get_cookies_data()
        self.entry_sessid.SetValue(cookies.get("PHPSESSID", ""))

    def _save_cookie(self, event):
        """Зберігає нове значення PHPSESSID у конфігураційний файл.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        new_id = self.entry_sessid.GetValue().strip()
        if not new_id:
            return

        if save_cookies_data(new_id):
            wx.MessageBox("PHPSESSID успішно оновлено!", "Успіх", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("Не вдалося зберегти PHPSESSID!", "Помилка", wx.OK | wx.ICON_ERROR)


class MainFrame(wx.Frame):
    """Головне вікно програми TurboSMS Report Generator.

    Містить елементи управління для введення часового інтервалу, виклику
    допоміжних діалогових вікон та запуску процесу генерації звіту.
    """

    def __init__(self):
        """Ініціалізує головне вікно програми, його макет та обробники подій."""
        super().__init__(
            None,
            title="TurboSMS Report Generator",
            size=(460, 250),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        flex_sizer = wx.FlexGridSizer(2, 2, 10, 10)
        flex_sizer.AddGrowableCol(1, 1)

        flex_sizer.Add(wx.StaticText(panel, label="Початок періоду:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.entry_start = wx.TextCtrl(panel, value="")
        self.entry_start.SetHint("01.08.2026 00:00")
        flex_sizer.Add(self.entry_start, 1, wx.EXPAND)

        flex_sizer.Add(wx.StaticText(panel, label="Кінець періоду:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.entry_end = wx.TextCtrl(panel, value="")
        self.entry_end.SetHint("31.08.2026 23:59")
        flex_sizer.Add(self.entry_end, 1, wx.EXPAND)

        main_sizer.Add(flex_sizer, 0, wx.EXPAND | wx.ALL, 15)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_templates = wx.Button(panel, label="Шаблони пошуку")
        self.btn_cookies = wx.Button(panel, label="Оновити PHPSESSID")

        self.btn_cookies.SetToolTip(
            "PHPSESSID — це токен вашої активної сесії на сайті turbosms.ua.\n\n"
            "1. Залогіньтесь на turbosms.ua у браузері.\n"
            "2. Натисніть F12 -> вкладка 'Application' (або 'Storage') -> Cookies.\n"
            "3. Скопіюйте значення ключа PHPSESSID і вставте сюди."
        )

        btn_sizer.Add(self.btn_templates, 1, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_cookies, 1, wx.LEFT, 5)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

        self.btn_generate = wx.Button(panel, label="Сформувати звіт")
        font = self.btn_generate.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.btn_generate.SetFont(font)

        main_sizer.Add(self.btn_generate, 0, wx.EXPAND | wx.ALL, 15)

        panel.SetSizer(main_sizer)
        self.Center()

        self.btn_templates.Bind(wx.EVT_BUTTON, self._open_templates)
        self.btn_cookies.Bind(wx.EVT_BUTTON, self._open_cookies)
        self.btn_generate.Bind(wx.EVT_BUTTON, self._generate_report)

    def _open_templates(self, event):
        """Відкриває діалогове вікно управління шаблонами пошуку.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        dlg = TemplatesDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def _open_cookies(self, event):
        """Відкриває діалогове вікно оновлення авторизаційного токена PHPSESSID.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        dlg = CookiesDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def _generate_report(self, event):
        """Обробляє натискання кнопки формування звіту.

        Валідує введення дат, запитує шлях для збереження файлу через `wx.FileDialog`
        та запускає окремий фоновий потік для виконання парсингу та експорту
        без блокування головного інтерфейсу.

        Args:
            event (wx.CommandEvent): Об'єкт події wxPython.
        """
        start_date = self.entry_start.GetValue().strip()
        end_date = self.entry_end.GetValue().strip()

        if not start_date or not end_date:
            wx.MessageBox("Будь ласка, заповніть початкову та кінцеву дати!", "Увага", wx.OK | wx.ICON_WARNING)
            return

        with wx.FileDialog(
            self,
            "Зберегти звіт як...",
            wildcard="Excel files (*.xlsx)|*.xlsx",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile="turbosms_report.xlsx",
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            file_path = fileDialog.GetPath()

        self.btn_generate.Disable()
        self.btn_generate.SetLabel("Формування...")

        def _worker():
            try:
                saved_file = run_report(start_date, end_date, file_path)
                wx.CallAfter(
                    wx.MessageBox,
                    f"Звіт успішно збережено за шляхом:\n{saved_file}",
                    "Успіх",
                    wx.OK | wx.ICON_INFORMATION,
                )
            except Exception as e:
                wx.CallAfter(
                    wx.MessageBox,
                    f"Сталася помилка під час формування звіту:\n{e}",
                    "Помилка",
                    wx.OK | wx.ICON_ERROR,
                )
            finally:
                wx.CallAfter(self._reset_generate_button)

        threading.Thread(target=_worker, daemon=True).start()

    def _reset_generate_button(self):
        """Відновлює початковий активний стан та заголовок кнопки формування звіту."""
        self.btn_generate.Enable()
        self.btn_generate.SetLabel("Сформувати звіт")


def main():
    """Точка входу для запуску графічного додатка wxPython.

    Створює екземпляр `wx.App`, ініціалізує та відображає `MainFrame`,
    після чого запускає головний цикл обробки подій `MainLoop`.
    """
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()