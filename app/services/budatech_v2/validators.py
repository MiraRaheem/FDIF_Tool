
from typing import Any


CUSTOMER_TYPES = {
    "Company",
    "Individual",
    "Distributor",
    "Distributer",
    "OEM",
    "Retailer",
}


def validate_customer(customer: dict[str, Any]) -> list[str]:
    """
    Validate a canonical Customer record before ingestion.

    Returns an empty list when the record is valid.
    Otherwise, returns a list of validation errors.
    """

    errors = []

    # Required fields
    for field in ("customerId", "customerName"):
        value = customer.get(field)

        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required and must be a non-empty string.")

    # Optional customer type
    customer_type = customer.get("customerType")

    if customer_type is not None:
        if not isinstance(customer_type, str) or not customer_type.strip():
            errors.append("customerType must be a non-empty string when provided.")
        elif customer_type not in CUSTOMER_TYPES:
            errors.append(
                f"Unsupported customerType '{customer_type}'. "
                f"Accepted values: {', '.join(sorted(CUSTOMER_TYPES)}."
            )

    return errors

