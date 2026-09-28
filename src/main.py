from exporter import export_period_data_to_excel
from parser import parse_period_data


def run_report(start_date: str, end_date: str, output_excel_path: str = "report.xlsx"):
    """Запускає парсинг даних за допомогою функції 'parse_period_data()' за вказаний в аргументах період часу. 
       Передає отриманий словник в 'export_period_data_to_excel()' для форматування в Excel-таблицю.

    Args:
        start_date (str): Початкова дата та час періоду в форматі 'DD.MM.YYYY hh.mm.'
        end_date (str): Кінцева дата та час періоду в форматі 'DD.MM.YYYY hh.mm.'
        output_excel_path (str): Шлях для збереження .xlsx файлу.

    Returns:
        str: Абсолютний шлях до створеного файлу.
    """
    parsed_data = parse_period_data(start_date, end_date)

    file_path = export_period_data_to_excel(
        parsed_data, output_path=output_excel_path
    )

    return file_path
