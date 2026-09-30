import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from exporter import export_period_data_to_excel
from parser import parse_period_data

BASE_DIR = Path(__file__).resolve().parent.parent
SEARCH_TEMPLATES_PATH = BASE_DIR / "search_templates.json"
COOKIES_PATH = BASE_DIR / "cookies.json"

logger = logging.getLogger(__name__)


def _load_json(filepath: Path, default_value: Any) -> Any:
    if not filepath.exists():
        return default_value
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error reading {filepath}: {e}")
        return default_value


def _save_json(filepath: Path, data: Any) -> bool:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        logger.error(f"Error writing to {filepath}: {e}")
        return False


def get_search_templates() -> List[str]:
    return _load_json(SEARCH_TEMPLATES_PATH, default_value=[])


def save_search_templates(templates: List[str]) -> bool:
    return _save_json(SEARCH_TEMPLATES_PATH, templates)


def get_cookies_data() -> Dict[str, Any]:
    return _load_json(COOKIES_PATH, default_value={})


def save_cookies_data(phpsessid: str) -> bool:
    data = get_cookies_data()
    data["PHPSESSID"] = phpsessid
    data.setdefault("lang", "russian")
    data.setdefault("tur_cookie_hide", "1")
    return _save_json(COOKIES_PATH, data)


def run_report(start_date: str, end_date: str, file_path: str) -> str:
    parsed_data = parse_period_data(
        start_date=start_date,
        end_date=end_date,
        templates_path=SEARCH_TEMPLATES_PATH,
        cookies_path=COOKIES_PATH,
    )
    return export_period_data_to_excel(parsed_data, file_path)