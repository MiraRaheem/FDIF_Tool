
from typing import Any


CUSTOMER_TYPES = {
    "Distributer",
    "Individual",
    "OEM",
    "Retailer",
}


def validate_customer(customer: dict[str, Any]) -> list[str]:
    """
    Validate a canonical Customer record before ingestion.
    Returns an empty list when valid, otherwise validation errors.
    """

    errors = []

    for field in ("customerId", "customerName"):
        value = customer.get(field)

        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{field} is required and must be a non-empty string."
            )

    customer_type = customer.get("customerType")

    if customer_type is not None:
        if not isinstance(customer_type, str):
            errors.append("customerType must be a string.")
        elif customer_type not in CUSTOMER_TYPES:
            errors.append(
                f"Unsupported customerType '{customer_type}'. "
                f"Allowed values: {', '.join(sorted(CUSTOMER_TYPES))}."
            )

    return errors
