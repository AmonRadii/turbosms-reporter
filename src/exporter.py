from pathlib import Path
from typing import Dict

import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def export_period_data_to_excel(
    parsed_data: Dict, output_path: str = "report.xlsx"
) -> str:
    """Форматує отримані дані в Excel-таблицю та зберігає у .xlsx файл."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчет TurboSMS"

    bold_font = Font(bold=True)
    currency_format = '# ##0.00" грн."'

    start_date = parsed_data.get("start_date", "")
    end_date = parsed_data.get("end_date", "")
    total_spent = parsed_data.get("total_spent", 0.0)
    template_results = parsed_data.get("template_results", {})

    # 1. Загальні витрати за період
    ws["A1"] = f"Всього витрачено за період {start_date} — {end_date}:"
    ws["A1"].font = bold_font
    ws["B1"] = total_spent
    ws["B1"].number_format = currency_format
    ws["B1"].font = bold_font

    # 2. Заголовок розділу шаблонів
    ws["A2"] = "Витрачено на повідомлення зі змістом:"
    ws["A2"].font = bold_font
    ws.merge_cells("A2:B2")

    # 3. Шаблони та їх суми
    current_row = 3
    for template_text, amount in template_results.items():
        ws[f"A{current_row}"] = f'"{template_text}":'
        ws[f"B{current_row}"] = amount
        ws[f"B{current_row}"].number_format = currency_format
        current_row += 1

    # 4. Автоматичне розширення колонок
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)

        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max(max_len + 3, 20)

    save_path = Path(output_path)
    wb.save(save_path)

    return str(save_path.resolve())


