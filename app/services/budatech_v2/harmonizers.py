
def harmonize_customer(raw: dict) -> dict:
    """
    Map a normalized Budatech Customer record
    to the canonical FDIF representation.

    Source: Customer.xlsx
    Target ontology class: Customer
    """

    return {
        "customerId": raw.get("ID"),
        "customerName": raw.get("Customer Name"),
        "customerType": raw.get("Customer Type"),
    }

