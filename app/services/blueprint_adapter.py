import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


# -----------------------------
# Utils
# -----------------------------

def clean_properties(properties):
    return [p for p in properties if p["value"] is not None]


def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    headers = {
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("\n--- Blueprint Call ---")
    print("Class:", class_name)
    print("URL:", url)
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

    data = r.json()

    return data.get("instances", [])


def supplier_exists(supplier_id):

    suppliers = get_existing_suppliers()

    for s in suppliers:

        # Case 1: string (most likely your case)
        if isinstance(s, str) and supplier_id in s:
            return True

        # Case 2: dict (future-safe)
        if isinstance(s, dict):
            if s.get("hasSupplierID") == supplier_id:
                return True

    return False

# -----------------------------
# Budatec Metadata
# -----------------------------

def create_budatec_metadata(supplier_id, metadata):

    if not isinstance(metadata, dict):
        metadata = {}

    payload = {
        "individualName": f"SupplierMetadata_{supplier_id}",
        "dataProperties": clean_properties([

            {"property": "hasRecordOwner", "value": metadata.get("recordOwner")},
            {"property": "hasCreationTimestamp", "value": metadata.get("creationTimestamp")},
            {"property": "hasLastModifiedTimestamp", "value": metadata.get("lastModifiedTimestamp")},
            {"property": "hasModifiedBy", "value": metadata.get("modifiedByUser")},
            {"property": "hasDocumentStatus", "value": metadata.get("documentStatus")},
            {"property": "hasRecordIndex", "value": metadata.get("recordIndex")},
            {"property": "hasNamingSeries", "value": metadata.get("namingSeries")}

        ]),
        "objectProperties": []
    }

    return create_instance("SupplierMetadata", payload)

# -----------------------------
# Budatec Operational Policy
# -----------------------------

def create_budatec_policy(supplier_id, policy):

    if not isinstance(policy, dict):
        policy = {}

    payload = {
        "individualName": f"SupplierPolicy_{supplier_id}",
        "dataProperties": clean_properties([

            {"property": "allowsInvoiceWithoutPO", "value": policy.get("allowInvoiceWithoutPO")},
            {"property": "allowsInvoiceWithoutReceipt", "value": policy.get("allowInvoiceWithoutReceipt")},
            {"property": "warnBeforeRFQ", "value": policy.get("warnRFQ")},
            {"property": "warnBeforePO", "value": policy.get("warnPO")},
            {"property": "preventRFQCreation", "value": policy.get("preventRFQ")},
            {"property": "preventPOCreation", "value": policy.get("preventPO")}

        ]),
        "objectProperties": []
    }

    return create_instance("SupplierOperationalPolicy", payload)
    
# -----------------------------
# Budatec Supplier (MAIN)
# -----------------------------

def create_budatec_supplier(canonical):

    supplier_id = str(canonical["supplierId"])

    # ---- Check existence ----
    if supplier_exists(supplier_id):
        return {
            "status": "exists",
            "supplierId": supplier_id
        }

    # ---- 1. Create Metadata ----
    metadata_res = create_budatec_metadata(
        supplier_id,
        canonical.get("metadata", {})
    )

    # ---- 2. Create Policy ----
    policy_res = create_budatec_policy(
        supplier_id,
        canonical.get("operationalPolicy", {})
    )

    # 🚨 Stop if failed
    if "error" in str(metadata_res) or "error" in str(policy_res):
        return {
            "status": "error",
            "message": "Failed to create metadata or policy",
            "metadata_response": metadata_res,
            "policy_response": policy_res
        }

    # ---- 3. Create Supplier ----
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
    return create_instance("MaterialSupplier", payload)

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



    
