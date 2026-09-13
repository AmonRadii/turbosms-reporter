import json
import re

from pathlib import Path

from bs4 import BeautifulSoup
import requests

BASE_URL = "https://turbosms.ua"
DATA_URL = f"{BASE_URL}/sended/get.html"
SENDED_URL = f"{BASE_URL}/sended.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE_URL,
    "Referer": SENDED_URL,
}

DEFAULT_PAYLOAD = {
    "sign": "",
    "number": "",
    "date_from": "",
    "date_to": "",
    "date": "added",
    "text": "",
    "bases": "null",
    "start": "0",
    "type": "all",
    "status": "0",
    "group": "1",
    "sort_by": "added",
    "sort_order": "desc",
}

def load_templates(filepath: str = "search_templates.json") -> list[str]:
    """Вивантажує пошукові шаблони зі списку всередині 'search_templates.json'
    
    Args:
        filepath (str): Шлях до файлу, в якому зберігається список шаблонів пошуку.

    Returns:
        list[str]: Список текстових шаблонів пошуку.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Файл з шаблонами {filepath} не знайдений.")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_authenticated_session(cookies_path: str = "cookies.json") -> requests.Session:
    """Створює сесію з локального файлу 'cookies.json' (або іншого файлу за вказаним в аргументі шляхом) та перевіряє її валідність."""
    path = Path(cookies_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Файл {cookies_path} не знайдено! Створіть його та вкажіть актуальний PHPSESSID."
        )

    with open(path, "r", encoding="utf-8") as f:
        cookies_data = json.load(f)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(cookies_data)
    response = session.get(SENDED_URL, timeout=10)

    if "auth.html" in response.url or "authorization" in response.text.lower():
        raise PermissionError(
            "Сесія застаріла. Будь-ласка, оновіть PHPSESSID в cookies.json"
        )

    return session


def fetch_spent_amount(
    session: requests.Session,
    start_date: str,
    end_date: str,
    text_fragment: str = "",
) -> float:
    """Відправляє POST-запит до TurboSMS та повертає суму витрачених грошей на СМС повідомлення за визначений проміжок часу.
    Опціонально фільтрує результат за фрагментом повідомлення.
    
    Args: 
        session (requests.Session): Відкрита сесія, зазвичай отримується з 'get_authenticated_session()'.
        start_date (str): Початок часового проміжку, записується в форматі 'DD.MM.YYYY hh.mm'.
        end_date (str): Кінець часового проміжку, записується в форматі 'DD.MM.YYYY hh.mm'.
        text_fragment (str): Опціональний фрагмент тексту повідомлення, за співпадінням з яким фільтрується запит.

    Returns:
        float: Отримана сума грошей.
    """
    
    # payload на основі базового шаблону
    payload = DEFAULT_PAYLOAD.copy()
    payload.update({
        "date_from": start_date,
        "date_to": end_date,
        "text": text_fragment,
    })

    response = session.post(DATA_URL, data=payload, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    
    # Пошук спана через CSS-селектор
    span = soup.select_one("div.result-info-row span")
    if not span:
        return 0.0

    raw_text = span.get_text(strip=True)

    # Пошук числа з можливими пробілами в розрядах тисяч (наприклад: "2 941.44 грн")
    match = re.search(r"([\d\s\xa0\.,]+)\s*грн", raw_text)
    if match:
        # Форматування: видалення звичайних та нерозривних пробілів, заміна коми на крапку.
        clean_str = match.group(1).replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    return 0.0


def parse_period_data(
    start_date: str,
    end_date: str,
    templates_path: str = "search_templates.json",
    cookies_path: str = "cookies.json",
) -> dict:
    """Збирає дані про витрати на відправку SMS за вказаний період часу.

    Функція запитує загальну суму витрат за виданий інтервал дат,
    а також виконує пошук сум витрат за кожним шаблоном з файлу конфігурації.

    Args:
        start_date (str): Початкова дата та час періоду в форматі 'DD.MM.YYYY hh.mm.'
        end_date (str): Кінцева дата та час періоду в форматі 'DD.MM.YYYY hh.mm.'
        templates_path (str): Шлях до JSON-файлу зі списком пошукових шаблонів.
            За вмовчанням "search_templates.json".
        cookies_path (str): Шлях до JSON-файлу з куками сесії авторизації.
            За вмовчанням "cookies.json".

    Returns:
        dict: Словник з наступною структурою:
            {
                "total_spent": float,  # Загальні витрати за перід
                "template_results": {  # Витрати за кожним шаблоном
                    "фрагмент_тексту": float,
                    ...
                }
            }

    Raises:
        FileNotFoundError: Якщо файл шаблонів файл cookies не знайдено.
        PermissionError: Якщо сесія застаріла або не дійсна.
    """
    templates = load_templates(templates_path)
    session = get_authenticated_session(cookies_path)

    total_spent = fetch_spent_amount(session, start_date, end_date, text_fragment="")

    template_results = {}
    for fragment in templates:
        amount = fetch_spent_amount(
            session, start_date, end_date, text_fragment=fragment
        )
        template_results[fragment] = amount

    return {
        "total_spent": total_spent,
        "template_results": template_results,
    }

# Внизу і далі код для тестування
if __name__ == "__main__":
    TEST_START = "01.08.2026 00:00"
    TEST_END = "31.08.2026 23:59"

    try:
        data = parse_period_data(TEST_START, TEST_END)
        print("Дані успішно зібрано:")
        print(f"Загальні витрати: {data['total_spent']} грн.")
        print("Витрати за шаблонами:")
        for tmpl, spent in data["template_results"].items():
            print(f"  - '{tmpl}': {spent} грн.")
    except Exception as err:
        print(f"Помилка при роботі парсера: {err}")