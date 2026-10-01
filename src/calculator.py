from typing import Dict


def calculate_other_expenses(
    total_spent: float, template_results: Dict[str, float]
) -> float:
    """Обчислює суму витрат на повідомлення, що не підпали під жоден із шаблонів.

    Віднімає суму знайдених витрат за всіма шаблонами від загальної
    суми витрат за період.

    Args:
        total_spent (float): Загальна сума витрат за обраний період.
        template_results (Dict[str, float]): Словник, де ключем є текст шаблону,
            а значенням — сума витрат за цим шаблоном.

    Returns:
        float: Сума витрат на інші повідомлення (округлена до 2 знаків).
            Якщо сума за шаблонами більша за загальні витрати, повертає 0.0.
    """
    templates_total = sum(template_results.values())
    other_total = total_spent - templates_total
    return max(0.0, round(other_total, 2))