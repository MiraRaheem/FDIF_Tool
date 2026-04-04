from datetime import datetime


# -----------------------------
# Helpers
# -----------------------------

def validate_enum(value, allowed, field_name):
    if value is None:
        return value

    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")

    return value


def validate_date(value, field_name):

    if value is None:
        return value

    # Try ISO format (already fine)
    try:
        return datetime.fromisoformat(str(value))
    except:
        pass

    # Try dd.mm.yyyy
    try:
        return datetime.strptime(value, "%d.%m.%Y")
    except:
        raise ValueError(f"{field_name} invalid date format")


def validate_bool(value):
    return str(value) in ["1", "true", "True"]


# -----------------------------
# Main Validator
# -----------------------------

def validate_budatec_supplier(data):

    # ---- REQUIRED ----
    if not data.get("supplierId"):
        raise ValueError("supplierId missing")

    if not data.get("supplierName"):
        raise ValueError("supplierName missing")

    if not data.get("country"):
        raise ValueError("country missing")

    # -----------------------------
    # ENUM VALIDATION
    # -----------------------------

    data["supplierType"] = validate_enum(
        data.get("supplierType"),
        ["Company", "Individual", "Partnership"],
        "supplierType"
    )

    data["holdType"] = validate_enum(
        data.get("holdType"),
        ["All", "Invoices", "Payments", None],
        "holdType"
    )

    # -----------------------------
    # DATE VALIDATION
    # -----------------------------

    metadata = data.get("metadata", {})

    metadata["creationTimestamp"] = validate_date(
        metadata.get("creationTimestamp"),
        "creationTimestamp"
    )

    metadata["lastModifiedTimestamp"] = validate_date(
        metadata.get("lastModifiedTimestamp"),
        "lastModifiedTimestamp"
    )

    # -----------------------------
    # BOOLEAN NORMALIZATION
    # -----------------------------

    data["isTransportProvider"] = validate_bool(data.get("isTransportProvider"))
    data["isInternalSupplier"] = validate_bool(data.get("isInternalSupplier"))
    data["isFrozen"] = validate_bool(data.get("isFrozen"))
    data["isDisabled"] = validate_bool(data.get("isDisabled"))
    data["isOnHold"] = validate_bool(data.get("isOnHold"))

    # -----------------------------
    # OPTIONAL CLEANUPS
    # -----------------------------

    if data.get("language"):
        data["language"] = data["language"].lower()

    return data
