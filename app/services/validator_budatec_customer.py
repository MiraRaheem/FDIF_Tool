from datetime import datetime


def validate_enum(value, allowed, field):
    if value is None:
        return value
    if value not in allowed:
        raise ValueError(f"{field} must be one of {allowed}")
    return value


def validate_date(v, field):
    if v is None:
        return v

    try:
        return datetime.fromisoformat(str(v))
    except:
        raise ValueError(f"{field} invalid format")


def validate_budatec_customer(data):

    # -------- REQUIRED --------
    if not data.get("customerId"):
        raise ValueError("customerId missing")

    if not data.get("customerName"):
        raise ValueError("customerName missing")

    # -------- ENUM --------
    data["customerType"] = validate_enum(
        data.get("customerType"),
        ["Company", "Individual", "Distributor", "Retailer", "OEM"],
        "customerType"
    )

    # -------- NUMERIC --------
    if data.get("commissionRate") is not None:
        data["commissionRate"] = float(data["commissionRate"])

    # -------- METADATA --------
    meta = data.get("metadata", {})

    meta["creationTimestamp"] = validate_date(
        meta.get("creationTimestamp"),
        "creationTimestamp"
    )

    meta["lastModifiedTimestamp"] = validate_date(
        meta.get("lastModifiedTimestamp"),
        "lastModifiedTimestamp"
    )

    return data
