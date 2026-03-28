import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


def get_class_metadata(class_name):

    url = f"{BASE_URL}/api/query/metadata/{class_name}"

    r = requests.get(url)

    return r.json()

def get_existing_suppliers():

    url = f"{BASE_URL}/api/MaterialSupplier"

    r = requests.get(url)

    data = r.json()

    return data.get("instances", [])
    
def supplier_exists(supplier_id):

    supplier_id = str(supplier_id)

    suppliers = get_existing_suppliers()

    for s in suppliers:

        if supplier_id in s:
            return True

    return False
    
def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    headers = {
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("Blueprint URL:", url)
    print("Status:", r.status_code)
    print("Response:", r.text)

    try:
        return r.json()
    except:
        return {
            "status_code": r.status_code,
            "response_text": r.text
        }

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

def create_budatec_supplier(canonical):

    supplier_id = str(canonical["supplierId"])

    if supplier_exists(supplier_id):
        return {
            "status": "exists",
            "supplierId": supplier_id
        }

    # ---- 1. Create Metadata ----
    create_budatec_metadata(supplier_id, canonical.get("metadata", {}))

    # ---- 2. Create Policy ----
    create_budatec_policy(supplier_id, canonical.get("operationalPolicy", {}))

    # ---- 3. Create Supplier ----
    payload = {
        "individualName": f"MaterialSupplier_{supplier_id}",

        "dataProperties": [

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
        ],

        "objectProperties": [
            {
                "property": "hasMetadata",
                "value": f"SupplierMetadata_{supplier_id}"
            },
            {
                "property": "hasOperationalPolicy",
                "value": f"SupplierPolicy_{supplier_id}"
            }
        ]
    }

    return create_instance("MaterialSupplier", payload)


def create_budatec_metadata(supplier_id, metadata):

    payload = {
        "individualName": f"SupplierMetadata_{supplier_id}",
        "dataProperties": [

            {"property": "hasRecordOwner", "value": metadata.get("recordOwner")},
            {"property": "hasCreationTimestamp", "value": metadata.get("creationTimestamp")},
            {"property": "hasLastModifiedTimestamp", "value": metadata.get("lastModifiedTimestamp")},
            {"property": "hasModifiedBy", "value": metadata.get("modifiedByUser")},
            {"property": "hasDocumentStatus", "value": metadata.get("documentStatus")},
            {"property": "hasRecordIndex", "value": metadata.get("recordIndex")},
            {"property": "hasNamingSeries", "value": metadata.get("namingSeries")}

        ],
        "objectProperties": []
    }

    return create_instance("SupplierMetadata", payload)

def create_budatec_policy(supplier_id, policy):

    payload = {
        "individualName": f"SupplierPolicy_{supplier_id}",
        "dataProperties": [

            {"property": "allowsInvoiceWithoutPO", "value": policy.get("allowInvoiceWithoutPO")},
            {"property": "allowsInvoiceWithoutReceipt", "value": policy.get("allowInvoiceWithoutReceipt")},
            {"property": "warnBeforeRFQ", "value": policy.get("warnRFQ")},
            {"property": "warnBeforePO", "value": policy.get("warnPO")},
            {"property": "preventRFQCreation", "value": policy.get("preventRFQ")},
            {"property": "preventPOCreation", "value": policy.get("preventPO")}

        ],
        "objectProperties": []
    }

    return create_instance("SupplierOperationalPolicy", payload)
