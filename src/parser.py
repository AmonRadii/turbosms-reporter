import json
import re
from pathlib import Path
from typing import Dict, List, Union

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


def load_templates(filepath: Union[str, Path] = "search_templates.json") -> List[str]:
    """Вивантажує пошукові шаблони зі списку всередині 'search_templates.json'."""
    path = Path(filepath)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_authenticated_session(cookies_path: Union[str, Path] = "cookies.json") -> requests.Session:
    """Створює сесію з локального файлу 'cookies.json' та перевіряє її валідність."""
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
            "Сесія застаріла або недійсна. Будь ласка, оновіть PHPSESSID."
        )

    return session


def fetch_spent_amount(
    session: requests.Session,
    start_date: str,
    end_date: str,
    text_fragment: str = "",
) -> float:
    """Відправляє POST-запит до TurboSMS та повертає суму витрачених грошей за період."""
    payload = DEFAULT_PAYLOAD.copy()
    payload.update({
        "date_from": start_date,
        "date_to": end_date,
        "text": text_fragment,
    })

    response = session.post(DATA_URL, data=payload, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    span = soup.select_one("div.result-info-row span")
    if not span:
        return 0.0

    raw_text = span.get_text(strip=True)
    match = re.search(r"([\d\s\xa0\.,]+)\s*грн", raw_text)
    if match:
        clean_str = match.group(1).replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    return 0.0


def parse_period_data(
    start_date: str,
    end_date: str,
    templates_path: Union[str, Path] = "search_templates.json",
    cookies_path: Union[str, Path] = "cookies.json",
) -> Dict:
    """Збирає дані про витрати на відправку SMS за вказаний період часу."""
    templates = load_templates(templates_path)
    session = get_authenticated_session(cookies_path)

    total_spent = fetch_spent_amount(session, start_date, end_date, text_fragment="")

    template_results = {}
    for fragment in templates:
        amount = fetch_spent_amount(session, start_date, end_date, text_fragment=fragment)
        template_results[fragment] = amount

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_spent": total_spent,
        "template_results": template_results,
    }
