import requests
from datetime import datetime

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


# -----------------------------
# Utils
# -----------------------------

def sanitize_id(value: str) -> str:
    if not value:
        return value

    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )


def serialize_value(v):
    if isinstance(v, datetime):
        return v.isoformat(sep=" ")
    return v


def clean_properties(properties):
    cleaned = []

    for p in properties:
        value = p["value"]

        if value is None:
            continue

        cleaned.append({
            "property": p["property"],
            "value": serialize_value(value)
        })

    return cleaned


def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    r = requests.post(url, json=payload)

    print("\n--- Blueprint Call ---")
    print("Class:", class_name)
    print("Payload:", payload)
    print("Status:", r.status_code)
    print("Response:", r.text)

    try:
        return r.json()
    except:
        return {
            "status": "error",
            "status_code": r.status_code,
            "response_text": r.text
        }


# -----------------------------
# Supplier existence check
# -----------------------------

def get_existing_suppliers():
    r = requests.get(f"{BASE_URL}/api/MaterialSupplier")
    return r.json().get("instances", [])


def supplier_exists(supplier_id):

    suppliers = get_existing_suppliers()

    for s in suppliers:

        if isinstance(s, str) and supplier_id in s:
            return True

        if isinstance(s, dict) and s.get("hasSupplierID") == supplier_id:
            return True

    return False


# -----------------------------
# CREATE ONLY (NO LINKS)
# -----------------------------

def create_supplier_instance_only(supplier_id, canonical):

    payload = {
        "individualName": f"MaterialSupplier_{supplier_id}",

        "dataProperties": clean_properties([
            {"property": "hasSupplierID", "value": supplier_id},
            {"property": "hasSupplierName", "value": canonical.get("supplierName")},
            {"property": "hasCountry", "value": canonical.get("country")},
            {"property": "hasSupplierType", "value": canonical.get("supplierType")},
            {"property": "hasTaxID", "value": canonical.get("taxId")},
            {"property": "hasPhoneNumber", "value": canonical.get("phoneNumber")},
            {"property": "hasCommunicationLanguage", "value": canonical.get("language")},
            {"property": "hasPrimarySupplierContact", "value": canonical.get("primaryContact")},

            {"property": "isTransportProvider", "value": canonical.get("isTransportProvider")},
            {"property": "isInternalSupplier", "value": canonical.get("isInternalSupplier")},
            {"property": "isSupplierFrozen", "value": canonical.get("isFrozen")},
            {"property": "isSupplierDisabled", "value": canonical.get("isDisabled")},
            {"property": "isOnHold", "value": canonical.get("isOnHold")},
            {"property": "hasSupplierHoldType", "value": canonical.get("holdType")},
        ]),

        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)


def create_metadata_only(supplier_id, metadata):

    payload = {
        "individualName": f"SupplierMetadata_{supplier_id}",

        "dataProperties": clean_properties([
            {"property": "recordOwner", "value": metadata.get("recordOwner")},
            {"property": "creationTimestamp", "value": metadata.get("creationTimestamp")},
            {"property": "lastModifiedTimestamp", "value": metadata.get("lastModifiedTimestamp")},
            {"property": "modifiedByUser", "value": metadata.get("modifiedByUser")},
            {"property": "documentStatus", "value": metadata.get("documentStatus")},
            {"property": "recordIndex", "value": metadata.get("recordIndex")},
            {"property": "namingSeries", "value": metadata.get("namingSeries")},
        ]),

        "objectProperties": []
    }

    return create_instance("SupplierMetadata", payload)


def create_policy_only(supplier_id, policy):

    payload = {
        "individualName": f"SupplierPolicy_{supplier_id}",

        "dataProperties": clean_properties([
            {"property": "allowsInvoiceWithoutPO", "value": policy.get("allowInvoiceWithoutPO")},
            {"property": "allowsInvoiceWithoutReceipt", "value": policy.get("allowInvoiceWithoutReceipt")},
            {"property": "warnBeforeRFQ", "value": policy.get("warnRFQ")},
            {"property": "warnBeforePO", "value": policy.get("warnPO")},
            {"property": "preventRFQCreation", "value": policy.get("preventRFQ")},
            {"property": "preventPOCreation", "value": policy.get("preventPO")},
        ]),

        "objectProperties": []
    }

    return create_instance("SupplierOperationalPolicy", payload)


# -----------------------------
# LINKING (CRITICAL PART)
# -----------------------------

def link_supplier_graph(supplier_id):

    supplier = f"MaterialSupplier_{supplier_id}"
    metadata = f"SupplierMetadata_{supplier_id}"
    policy = f"SupplierPolicy_{supplier_id}"

    # Supplier → Metadata
    create_instance("MaterialSupplier", {
        "individualName": supplier,
        "objectProperties": [
            {"property": "hasSupplierMetadata", "value": metadata}
        ]
    })

    # Supplier → Policy
    create_instance("MaterialSupplier", {
        "individualName": supplier,
        "objectProperties": [
            {"property": "hasSupplierPolicy", "value": policy}
        ]
    })

    # Metadata → Supplier
    create_instance("SupplierMetadata", {
        "individualName": metadata,
        "objectProperties": [
            {"property": "supplierMetadataOf", "value": supplier}
        ]
    })

    # Policy → Supplier
    create_instance("SupplierOperationalPolicy", {
        "individualName": policy,
        "objectProperties": [
            {"property": "operationalPolicyOf", "value": supplier}
        ]
    })


# -----------------------------
# MAIN: Budatec Supplier
# -----------------------------

def create_budatec_supplier(canonical):

    supplier_id = sanitize_id(canonical["supplierId"])

    if supplier_exists(supplier_id):
        return {
            "status": "exists",
            "supplierId": supplier_id
        }

    # 1. CREATE ALL
    supplier_res = create_supplier_instance_only(supplier_id, canonical)

    metadata_res = create_metadata_only(
        supplier_id,
        canonical.get("metadata", {})
    )

    policy_res = create_policy_only(
        supplier_id,
        canonical.get("operationalPolicy", {})
    )

    # 2. LINK ALL (🔥 THIS IS THE FIX)
    link_supplier_graph(supplier_id)

    return {
        "status": "success",
        "supplier": supplier_res,
        "metadata": metadata_res,
        "policy": policy_res
    }


# -----------------------------
# Medwood (KEEP)
# -----------------------------

def create_supplier_instance(canonical):

    supplier_id = str(canonical["supplierId"])

    if supplier_exists(supplier_id):
        return {
            "status": "exists",
            "supplierId": supplier_id
        }

    payload = {
        "individualName": f"MaterialSupplier_{supplier_id}",

        "dataProperties": [
            {"property": "hasSupplierID", "value": supplier_id},
            {"property": "hasCountry", "value": canonical["address"]["country"]},
            {"property": "hasCapacity", "value": "0"},
            {"property": "hasLeadTimeDays", "value": "0"},
            {"property": "hasPaymentTerms", "value": "Other"}
        ],

        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)
