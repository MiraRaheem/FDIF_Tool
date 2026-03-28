def validate_budatec_supplier(data):

    if not data.get("supplierId"):
        raise ValueError("supplierId missing")

    if not data.get("supplierName"):
        raise ValueError("supplierName missing")

    if not data.get("country"):
        raise ValueError("country missing")

    return data
