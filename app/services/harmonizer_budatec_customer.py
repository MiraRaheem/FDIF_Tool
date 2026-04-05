def to_bool(v):
    return v in [1, "1", True, "true", "True"]


def harmonize_budatec_customer(raw):

    return {

        # -------- CORE --------
        "customerId": raw.get("name"),
        "customerName": raw.get("customer_name"),
        "customerType": raw.get("customer_type"),

        "email": raw.get("email_id"),
        "phoneNumber": raw.get("mobile_no"),

        # -------- BUSINESS --------
        "commissionRate": raw.get("default_commission_rate"),
        "isInternalCustomer": to_bool(raw.get("is_internal_customer")),
        "isFrozenCustomer": to_bool(raw.get("is_frozen")),
        "isCustomerDisabled": to_bool(raw.get("disabled")),

        "requiresSalesOrder": to_bool(raw.get("so_required")),
        "requiresDeliveryNote": to_bool(raw.get("dn_required")),

        "language": raw.get("language"),

        # -------- METADATA --------
        "metadata": {
            "recordOwner": raw.get("owner"),
            "creationTimestamp": raw.get("creation"),
            "lastModifiedTimestamp": raw.get("modified"),
            "modifiedByUser": raw.get("modified_by"),
            "documentStatus": raw.get("docstatus"),
            "recordIndex": raw.get("idx"),
            "namingSeries": raw.get("naming_series"),
        },

        # -------- ARRAYS (relations later) --------
        "accounts": raw.get("accounts", []),
        "companies": raw.get("companies", []),
        "sales_team": raw.get("sales_team", []),
        "credit_limits": raw.get("credit_limits", []),
        "portal_users": raw.get("portal_users", [])
    }
