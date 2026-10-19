
def harmonize_customer(raw: dict) -> dict:
    """Map a normalized Budatech Customer record to canonical fields."""

    source_type = raw.get("Customer Type")

    customer_type_mapping = {
        "Company": "OEM",
        "Individual": "Individual",
        "Distributor": "Distributer",
        "Distributer": "Distributer",
        "Retailer": "Retailer",
        "OEM": "OEM",
    }

    canonical_type = (
        customer_type_mapping.get(source_type)
        if source_type is not None
        else None
    )

    return {
        "customerId": raw.get("ID"),
        "customerName": raw.get("Customer Name"),
        "customerType": canonical_type,
    }
