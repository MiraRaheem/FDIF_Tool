def validate_budatec_item(data):

    if not data.get("productId"):
        raise ValueError("productId missing")

    if not data.get("productName"):
        raise ValueError("productName missing")

    if not data.get("unit"):
        raise ValueError("unit missing")

    return data
