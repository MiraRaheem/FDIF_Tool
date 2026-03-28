def to_bool(v):
    if v in [1, "1", True, "true", "True"]:
        return True
    return False

def harmonize_budatec_supplier(raw):

    return {
        # -------- CORE --------
        "supplierId": raw.get("name"),
        "supplierName": raw.get("supplier_name"),
        "country": raw.get("country"),

        "supplierType": raw.get("supplier_type"),
        "taxId": raw.get("tax_id"),
        "phoneNumber": raw.get("mobile_no"),
        "language": raw.get("language"),
        "primaryContact": raw.get("supplier_primary_contact"),

        # -------- CLASSIFICATION --------
        "isTransportProvider": to_bool(raw.get("is_transporter")),
        "isInternalSupplier": to_bool(raw.get("is_internal_supplier")),
        "representsCompany": raw.get("represents_company") or None,

        # -------- STATUS --------
        "isFrozen": to_bool(raw.get("is_frozen")),
        "isDisabled": to_bool(raw.get("disabled")),
        "isOnHold": to_bool(raw.get("on_hold")),
        "holdType": raw.get("hold_type") or None,

        # -------- OPERATIONAL POLICY --------
        "operationalPolicy": {
            "allowInvoiceWithoutPO": to_bool(raw.get("allow_purchase_invoice_creation_without_purchase_order")),
            "allowInvoiceWithoutReceipt": to_bool(raw.get("allow_purchase_invoice_creation_without_purchase_receipt")),
            "warnRFQ": to_bool(raw.get("warn_rfqs")),
            "warnPO": to_bool(raw.get("warn_pos")),
            "preventRFQ": to_bool(raw.get("prevent_rfqs")),
            "preventPO": to_bool(raw.get("prevent_pos")),
        },

        # -------- METADATA (FIXED) --------
        "metadata": {
            "recordOwner": raw.get("owner") or None,
            "creationTimestamp": raw.get("creation") or None,
            "lastModifiedTimestamp": raw.get("modified") or None,
            "modifiedByUser": raw.get("modified_by") or None,
            "documentStatus": int(raw.get("docstatus")) if raw.get("docstatus") is not None else None,
            "recordIndex": int(raw.get("idx")) if raw.get("idx") is not None else None,
            "namingSeries": raw.get("naming_series") or None,
        },

        # -------- COLLECTIONS (PREP FOR NEXT STEP) --------
        "portalUsers": raw.get("portal_users", []),
        "accounts": raw.get("accounts", []),
        "companies": raw.get("companies", [])
    }
