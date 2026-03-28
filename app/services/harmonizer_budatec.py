def to_bool(v):
    return str(v) in ["1", "true", "True"]
    
def harmonize_budatec_supplier(raw):

    return {
        "supplierId": raw.get("name"),
        "supplierName": raw.get("supplier_name"),
        "country": raw.get("country"),

        "supplierType": raw.get("supplier_type"),
        "taxId": raw.get("tax_id"),
        "phoneNumber": raw.get("mobile_no"),
        "language": raw.get("language"),
        "primaryContact": raw.get("supplier_primary_contact"),

        "isTransportProvider": to_bool(raw.get("is_transporter")),
        "isInternalSupplier": to_bool(raw.get("is_internal_supplier")),
        "representsCompany": raw.get("represents_company"),

        "isFrozen": to_bool(raw.get("is_frozen")),
        "isDisabled": to_bool(raw.get("disabled")),
        "isOnHold": to_bool(raw.get("on_hold")),
        "holdType": raw.get("hold_type"),

        "operationalPolicy": {
            "allowInvoiceWithoutPO": to_bool(raw.get("allow_purchase_invoice_creation_without_purchase_order")),
            "allowInvoiceWithoutReceipt": to_bool(raw.get("allow_purchase_invoice_creation_without_purchase_receipt")),
            "warnRFQ": to_bool(raw.get("warn_rfqs")),
            "warnPO": to_bool(raw.get("warn_pos")),
            "preventRFQ": to_bool(raw.get("prevent_rfqs")),
            "preventPO": to_bool(raw.get("prevent_pos")),
        },

        "metadata": {
            "recordOwner": raw.get("owner"),
            "creationTimestamp": raw.get("creation"),
            "lastModifiedTimestamp": raw.get("modified"),
            "modifiedByUser": raw.get("modified_by"),
            "documentStatus": raw.get("docstatus"),
            "recordIndex": raw.get("idx"),
            "namingSeries": raw.get("naming_series"),
        }
    }
