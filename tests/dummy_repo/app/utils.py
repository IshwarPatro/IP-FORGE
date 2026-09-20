"""
Dummy Repository: Utility Functions
Helper calculations and string formatters.
"""


def calculate_discount(price: float, discount_percentage: float) -> float:
    """Calculates discounted price given a base price and percentage."""
    if discount_percentage < 0 or discount_percentage > 100:
        raise ValueError("Discount percentage must be between 0 and 100")
    discount = price * (discount_percentage / 100.0)
    return round(price - discount, 2)


def format_currency(amount: float, symbol: str = "$") -> str:
    """Formats numeric amount into localized currency string."""
    return f"{symbol}{amount:,.2f}"
