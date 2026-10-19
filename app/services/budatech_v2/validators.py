
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



def validate_company(company: dict[str, Any]) -> list[str]:
    """Validate a canonical Company record before ontology ingestion."""
    errors: list[str] = []

    for field in ("companyId", "companyName"):
        value = company.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{field} is required and must be a non-empty string."
            )

    country = company.get("country")
    if country is not None and (
        not isinstance(country, str) or not country.strip()
    ):
        errors.append("country must be a non-empty string when provided.")

    return errors

def validate_supplier(supplier: dict[str, Any]) -> list[str]:
    """
    Validate a canonical Supplier record.

    Supplier ID and name are required.
    Supplier type is preserved but is not restricted to an
    enum that has not been confirmed in the ontology metadata.
    """

    errors: list[str] = []

    for field in ("supplierId", "supplierName"):
        value = supplier.get(field)

        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{field} is required and must be a non-empty string."
            )

    supplier_type = supplier.get("supplierType")

    if supplier_type is not None and (
        not isinstance(supplier_type, str)
        or not supplier_type.strip()
    ):
        errors.append(
            "supplierType must be a non-empty string when provided."
        )

    return errors



