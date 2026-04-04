import requests


BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


# -----------------------------
# Utils
# -----------------------------

def clean_properties(properties):

    cleaned = []

    for p in properties:
        value = p["value"]

        if value is None:
            continue

        value = serialize_value(value)

        cleaned.append({
            "property": p["property"],
            "value": value
        })

    return cleaned

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
    from datetime import datetime

    if isinstance(v, datetime):
        return v.isoformat(sep=" ")
    return v


def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    headers = {
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

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
    url = f"{BASE_URL}/api/MaterialSupplier"
    r = requests.get(url)
    return r.json().get("instances", [])


def supplier_exists(supplier_id):

    suppliers = get_existing_suppliers()

    for s in suppliers:

        if isinstance(s, str) and supplier_id in s:
            return True

        if isinstance(s, dict):
            if s.get("hasSupplierID") == supplier_id:
                return True

    return False


# -----------------------------
# Supplier Metadata (GENERIC CLASS, SUPPLIER CONTEXT)
# -----------------------------

def create_supplier_metadata_instance(supplier_id, metadata):

    if not isinstance(metadata, dict):
        metadata = {}

    metadata_id = f"SupplierMetadata_{supplier_id}"

    payload = {
        "individualName": metadata_id,

        "dataProperties": clean_properties([
            {"property": "recordOwner", "value": metadata.get("recordOwner")},
            {"property": "creationTimestamp", "value": metadata.get("creationTimestamp")},
            {"property": "lastModifiedTimestamp", "value": metadata.get("lastModifiedTimestamp")},
            {"property": "modifiedByUser", "value": metadata.get("modifiedByUser")},
            {"property": "documentStatus", "value": metadata.get("documentStatus")},
            {"property": "recordIndex", "value": metadata.get("recordIndex")},
            {"property": "namingSeries", "value": metadata.get("namingSeries")},
        ]),

        "objectProperties": [
            {
                # 🔥 CORRECT ONTOLOGY RELATION (inverse)
                "property": "supplierMetadataOf",
                "value": f"MaterialSupplier_{supplier_id}"
            }
        ]
    }

    return create_instance("SupplierMetadata", payload)


# -----------------------------
# Supplier Operational Policy
# -----------------------------

def create_supplier_policy_instance(supplier_id, policy):

    if not isinstance(policy, dict):
        policy = {}

    policy_id = f"SupplierPolicy_{supplier_id}"

    payload = {
        "individualName": policy_id,

        "dataProperties": clean_properties([
            {"property": "allowsInvoiceWithoutPO", "value": policy.get("allowInvoiceWithoutPO")},
            {"property": "allowsInvoiceWithoutReceipt", "value": policy.get("allowInvoiceWithoutReceipt")},
            {"property": "warnBeforeRFQ", "value": policy.get("warnRFQ")},
            {"property": "warnBeforePO", "value": policy.get("warnPO")},
            {"property": "preventRFQCreation", "value": policy.get("preventRFQ")},
            {"property": "preventPOCreation", "value": policy.get("preventPO")},
        ]),

        "objectProperties": [
            {
                # 🔥 CORRECT ONTOLOGY RELATION (inverse)
                "property": "operationalPolicyOf",
                "value": f"MaterialSupplier_{supplier_id}"
            }
        ]
    }

    return create_instance("SupplierOperationalPolicy", payload)


# -----------------------------
# MAIN: Supplier Creation
# -----------------------------

def create_budatec_supplier(canonical):

    supplier_id = sanitize_id(canonical["supplierId"])

    # ---- existence check ----
    if supplier_exists(supplier_id):
        return {
            "status": "exists",
            "supplierId": supplier_id
        }

    # ---- create metadata ----
    metadata_res = create_supplier_metadata_instance(
        supplier_id,
        canonical.get("metadata", {})
    )

    # ---- create policy ----
    policy_res = create_supplier_policy_instance(
        supplier_id,
        canonical.get("operationalPolicy", {})
    )

    if "error" in str(metadata_res) or "error" in str(policy_res):
        return {
            "status": "error",
            "message": "Failed to create metadata or policy",
            "metadata_response": metadata_res,
            "policy_response": policy_res
        }

    # ---- create supplier ----
    supplier_payload = {
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

        "objectProperties": [
            {
                "property": "hasSupplierMetadata",
                "value": f"SupplierMetadata_{supplier_id}"
            },
            {
                "property": "hasSupplierPolicy",
                "value": f"SupplierPolicy_{supplier_id}"
            }
        ]
    }

    return create_instance("MaterialSupplier", supplier_payload)

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

            {
                "property": "hasSupplierID",
                "value": supplier_id
            },

            {
                "property": "hasCountry",
                "value": canonical["address"]["country"]
            },

            {
                "property": "hasCapacity",
                "value": "0"
            },

            {
                "property": "hasLeadTimeDays",
                "value": "0"
            },

            {
                "property": "hasPaymentTerms",
                "value": "Other"
            }

        ],

        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)

