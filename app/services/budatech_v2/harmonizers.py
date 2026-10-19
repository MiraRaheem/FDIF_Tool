
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



def harmonize_supplier(raw: dict) -> dict:
    """
    Normalize a raw Budatech Supplier record into the
    canonical representation used by the v2 pipeline.

    Source: Supplier.xlsx
    Ontology target: MaterialSupplier
    """

    return {
        "supplierId": raw.get("ID"),
        "supplierName": raw.get("Supplier Name"),
        "supplierType": raw.get("Supplier Type"),
    }


def harmonize_company(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a normalized Budatech Company row to canonical FDIF fields.

    The source export's ID column contains the company identifier; in the
    supplied workbook it currently duplicates the Company name.
    """
    return {
        "companyId": raw.get("ID"),
        "companyName": raw.get("Company"),
        "abbreviation": raw.get("Abbr"),
        "defaultCurrency": raw.get("Default Currency"),
        "country": raw.get("Country"),
    }


