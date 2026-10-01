import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from calculator import calculate_other_expenses
from exporter import export_period_data_to_excel
from parser import parse_period_data

BASE_DIR = Path(__file__).resolve().parent.parent
SEARCH_TEMPLATES_PATH = BASE_DIR / "search_templates.json"
COOKIES_PATH = BASE_DIR / "cookies.json"

logger = logging.getLogger(__name__)


def _load_json(filepath: Path, default_value: Any) -> Any:
    """Завантажує дані з JSON-файлу.

    Args:
        filepath (Path): Шлях до цільового JSON-файлу.
        default_value (Any):  Дефолтне значення, що повертається за відсутності
            файлу чи через помилки читання/декодування.

    Returns:
        Any: Декодовані дані з JSON-файлу або `default_value` якщо стається збій.
    """
    if not filepath.exists():
        return default_value
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error reading {filepath}: {e}")
        return default_value


def _save_json(filepath: Path, data: Any) -> bool:
    """Зберігає дані у JSON-файл з кодуванням UTF-8 та форматуванням.

    Args:
        filepath (Path): Шлях для зберігання файлу.
        data (Any): Дані, що потрібно серіалізувати у JSON.

    Returns:
        bool: True, якщо запис пройшов успішно, в іншому випадку False.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        logger.error(f"Error writing to {filepath}: {e}")
        return False


def get_search_templates() -> List[str]:
    """Завантажує список пошукових шаблонів з локального конфігураційного файлу.

    Returns:
        List[str]: Список рядків з текстовими шаблонами для пошуку.
            За відсутності файлу або при помилці повератє порожній список.
    """
    return _load_json(SEARCH_TEMPLATES_PATH, default_value=[])


def save_search_templates(templates: List[str]) -> bool:
    """Завантажує оновлений список пошукових шаблонів у локальний файл.

    Args:
        templates (List[str]): Список пошукових шаблонів.

    Returns:
        bool: True в разі успішного запису файлу, інакше False.
    """
    return _save_json(SEARCH_TEMPLATES_PATH, templates)


def get_cookies_data() -> Dict[str, Any]:
    """Завантажує збережені параметри сесії та авторизаційні cookies.

    Returns:
        Dict[str, Any]: Словник з кукі-даними (наприклад, PHPSESSID, lang).
            За відсутності файлу або при помилці повератє порожній словник.
    """
    return _load_json(COOKIES_PATH, default_value={})


def save_cookies_data(phpsessid: str) -> bool:
    """Оновлює значення PHPSESSID та зберігає конфігурацію cookies.

    Оновлює та додає переданий `PHPSESSID`, а також гарантує наявність 
    дефолтних параметрів (`lang`: "russian", `tur_cookie_hide`: "1").

    Args:
        phpsessid (str): Значення ідентифікатору сесії PHPSESSID.

    Returns:
        bool: True в разі успішного запису файлу, інакше False.
    """
    data = get_cookies_data()
    data["PHPSESSID"] = phpsessid
    data.setdefault("lang", "russian")
    data.setdefault("tur_cookie_hide", "1")
    return _save_json(COOKIES_PATH, data)


def run_report(start_date: str, end_date: str, file_path: str, calculate_other: bool = False) -> str:
    """Запускає повний проес збірки звіту за вказаний період.

    Виконує парсинг витрат з сайту TurboSMS за обраний інтервал
    дат на основі збережених пошукових шаблонів та cookie-файлів.
    За необхідністю обчислює витрати за повідомлення поза шаблонами
    через модуль `calculator`. В кінці форматує отримані дані та 
    експортує їх в Excel-файл.

    Args:
        start_date (str): Початкова дата періоду (формат 'ДД.ММ.ГГГГ').
        end_date (str): Кінцева дата періоду (формат 'ДД.ММ.ГГГГ').
        file_path (str): Шлях до файлу для збереження звіту (.xlsx).
        calculate_other (bool, optional): Флаг увімкнення розрахунку витрат
            на повідомлення поза шаблонами. За вмовчанням, False.

    Returns:
        str: Абсолютний шлях до створеного та збереженого файлу Excel.

    Raises:
        Exception: Помилки, що виникають під час парсингу веб-сторінок або запису Excel-файлу.
    """
    parsed_data = parse_period_data(
        start_date=start_date,
        end_date=end_date,
        templates_path=SEARCH_TEMPLATES_PATH,
        cookies_path=COOKIES_PATH,
    )

    if calculate_other:
        total_spent = parsed_data.get("total_spent", 0.0)
        template_results = parsed_data.get("template_results", {})
        parsed_data["other_spent"] = calculate_other_expenses(
            total_spent, template_results
        )
        
    return export_period_data_to_excel(parsed_data, file_path)