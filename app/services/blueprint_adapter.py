import requests
from datetime import datetime

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


# -----------------------------
# Utils
# -----------------------------

# In-memory cache (simple + fast)
INSTANCE_CACHE = {
    "Machine": set(),
    "ProductionMonitoringSensor": set(),
    "ProductionMetric": set(),
    "ProductionSensorObservation": set(),
    "MaintenanceEvent": set(),  # ✅ ADD THIS
    "ConditionMonitoringSensor": set()
}
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


def instance_exists(class_name, individual_name):

    # check cache first
    if class_name not in INSTANCE_CACHE:
        INSTANCE_CACHE[class_name] = set()
    if individual_name in INSTANCE_CACHE[class_name]:
        return True
    # fetch from API
    r = requests.get(f"{BASE_URL}/api/{class_name}")
    instances = r.json().get("instances", [])

    for inst in instances:

        # CASE 1: string URI
        if isinstance(inst, str):
            if inst.split("#")[-1] == individual_name:
                INSTANCE_CACHE[class_name].add(individual_name)
                return True

        # CASE 2: dict
        if isinstance(inst, dict):
            if inst.get("individualName") == individual_name:
                INSTANCE_CACHE[class_name].add(individual_name)
                return True

    return False

def get_or_create(class_name, individual_name, payload):

    if instance_exists(class_name, individual_name):
        return {"status": "exists", "id": individual_name}

    res = create_instance(class_name, payload)

    # only cache if success
    if res and res.get("status") == "success":
        INSTANCE_CACHE[class_name].add(individual_name)

    return {"status": "created", "id": individual_name}

def event_exists(event_id):
    return instance_exists("ProductionSensorObservation", event_id)
# -----------------------------
# API Calls
# -----------------------------

def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    r = requests.post(url, json=payload)

    print("\n--- CREATE ---")
    print("Class:", class_name)
    print("Payload:", payload)
    print("Status:", r.status_code)
    print("Response:", r.text)

    try:
        return r.json()
    except:
        return {"status": "error", "response": r.text}


def update_instance(class_name, instance_id, payload):

    url = f"{BASE_URL}/api/{class_name}/{instance_id}"

    r = requests.put(url, json=payload)

    print("\n--- UPDATE ---")
    print("Class:", class_name)
    print("Instance:", instance_id)
    print("Payload:", payload)
    print("Status:", r.status_code)
    print("Response:", r.text)

    try:
        return r.json()
    except:
        return {"status": "error", "response": r.text}

def create_customer_only(customer_id, canonical):

    payload = {
        "individualName": f"Customer_{customer_id}",
        "dataProperties": clean_properties([
            {"property": "hasCustomerID", "value": customer_id},
            {"property": "hasCustomerName", "value": canonical.get("customerName")},
            {"property": "hasCustomerType", "value": canonical.get("customerType")},

            {"property": "hasCustomerEmail", "value": canonical.get("email")},
            {"property": "hasCustomerPhoneNumber", "value": canonical.get("phoneNumber")},

            {"property": "hasCommissionRate", "value": canonical.get("commissionRate")},

            {"property": "isInternalCustomer", "value": canonical.get("isInternalCustomer")},
            {"property": "isFrozenCustomer", "value": canonical.get("isFrozenCustomer")},
            {"property": "isCustomerDisabled", "value": canonical.get("isCustomerDisabled")},

            {"property": "requiresSalesOrder", "value": canonical.get("requiresSalesOrder")},
            {"property": "requiresDeliveryNote", "value": canonical.get("requiresDeliveryNote")},
        ]),
        "objectProperties": []
    }

    return create_instance("Customer", payload)

def create_customer_metadata(customer_id, metadata):

    payload = {
        "individualName": f"CustomerMetadata_{customer_id}",
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

    return create_instance("CustomerMetadata", payload)
    

# -----------------------------
# Supplier existence
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
# Customer existence
# -----------------------------

def get_existing_customers():
    r = requests.get(f"{BASE_URL}/api/Customer")
    return r.json().get("instances", [])


def customer_exists(customer_id):

    customers = get_existing_customers()

    for c in customers:
        if isinstance(c, str) and customer_id in c:
            return True
        if isinstance(c, dict) and c.get("hasCustomerID") == customer_id:
            return True

    return False


# -----------------------------
# CREATE (NO RELATIONS)
# -----------------------------

def create_supplier_only(supplier_id, canonical):

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
# LINKING (PUT - FINAL FIX)
# -----------------------------

def link_supplier_graph(supplier_id):

    supplier = f"MaterialSupplier_{supplier_id}"
    metadata = f"SupplierMetadata_{supplier_id}"
    policy = f"SupplierPolicy_{supplier_id}"

    # Supplier → Metadata + Policy
    update_instance("MaterialSupplier", supplier, {
        "objectProperties": [
            {"property": "hasSupplierMetadata", "value": metadata},
            {"property": "hasSupplierPolicy", "value": policy}
        ]
    })

    # Metadata → Supplier
    update_instance("SupplierMetadata", metadata, {
        "objectProperties": [
            {"property": "supplierMetadataOf", "value": supplier}
        ]
    })

    # Policy → Supplier
    update_instance("SupplierOperationalPolicy", policy, {
        "objectProperties": [
            {"property": "operationalPolicyOf", "value": supplier}
        ]
    })

def link_customer_graph(customer_id):

    customer = f"Customer_{customer_id}"
    metadata = f"CustomerMetadata_{customer_id}"

    update_instance("Customer", customer, {
        "objectProperties": [
            {"property": "hasCustomerMetadata", "value": metadata}
        ]
    })

    update_instance("CustomerMetadata", metadata, {
        "objectProperties": [
            {"property": "customerMetadataOf", "value": customer}
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
    create_supplier_only(supplier_id, canonical)
    create_metadata_only(supplier_id, canonical.get("metadata", {}))
    create_policy_only(supplier_id, canonical.get("operationalPolicy", {}))

    # 2. LINK (🔥 THIS WAS MISSING)
    link_supplier_graph(supplier_id)

    return {
        "status": "success",
        "supplierId": supplier_id
    }

def create_budatec_customer(canonical):

    customer_id = sanitize_id(canonical["customerId"])

    if customer_exists(customer_id):
        return {
            "status": "exists",
            "customerId": customer_id
        }

    create_customer_only(customer_id, canonical)
    create_customer_metadata(customer_id, canonical.get("metadata", {}))

    link_customer_graph(customer_id)

    return {
        "status": "success",
        "customerId": customer_id
    }
    
# -----------------------------
# Medwood (UNCHANGED)
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

"""
def create_budatec_item(canonical):

    product_id = sanitize_id(canonical["productId"])
    product_name = f"Product_{product_id}"

    # -----------------------------
    # CREATE PRODUCT
    # -----------------------------
    create_instance("Product", {
        "individualName": product_name,
        "dataProperties": clean_properties([
            {"property": "hasProductID", "value": product_id},
            {"property": "hasProductName", "value": canonical.get("productName")},
            {"property": "hasProductDescription", "value": canonical.get("description")},
            {"property": "hasProductCategory", "value": canonical.get("category")},
            {"property": "hasProductUnit", "value": canonical.get("unit")},
            {"property": "hasProductWeight", "value": canonical.get("weight")},
            {"property": "hasProductCost", "value": canonical.get("cost")},
            {"property": "hasProductPrice", "value": canonical.get("price")},
            {"property": "hasExpiryDate", "value": canonical.get("expiryDate")}
        ]),
        "objectProperties": []
    })

    # -----------------------------
    # OPTIONAL: BOM
    # -----------------------------
    bom_id = canonical.get("bomId")

    if bom_id:

        bom_name = f"MBOM_{sanitize_id(bom_id)}"

        create_instance("MBOM", {
            "individualName": bom_name,
            "dataProperties": [
                {"property": "hasMBOM_ID", "value": bom_id}
            ],
            "objectProperties": []
        })

        update_instance("Product", product_name, {
            "objectProperties": [
                {"property": "hasBOM", "value": bom_name}
            ]
        })

    return {
        "status": "success",
        "productId": product_id
    }
"""

def create_budatec_item(canonical):

    product_id = sanitize_id(canonical["productId"])
    product_name = f"Product_{product_id}"

    # -----------------------------
    # 1. CREATE PRODUCT
    # -----------------------------
    create_instance("Product", {
        "individualName": product_name,
        "dataProperties": clean_properties([
            {"property": "hasProductID", "value": product_id},
            {"property": "hasProductName", "value": canonical.get("productName")},
            {"property": "hasProductDescription", "value": canonical.get("description")},
            {"property": "hasProductCategory", "value": canonical.get("category")},
            {"property": "hasProductUnit", "value": canonical.get("unit")},
            {"property": "hasProductWeight", "value": canonical.get("weight")},
            {"property": "hasProductCost", "value": canonical.get("cost")},
            {"property": "hasProductPrice", "value": canonical.get("price")},
            {"property": "hasExpiryDate", "value": canonical.get("expiryDate")}
        ])
    })

    # -----------------------------
    # 2. BOM (same as before)
    # -----------------------------
    bom_id = canonical.get("bomId")

    if bom_id:
        bom_name = f"MBOM_{sanitize_id(bom_id)}"

        create_instance("MBOM", {
            "individualName": bom_name,
            "dataProperties": [
                {"property": "hasMBOM_ID", "value": bom_id}
            ]
        })

        update_instance("Product", product_name, {
            "objectProperties": [
                {"property": "hasBOM", "value": bom_name}
            ]
        })

    # -----------------------------
    # 3. SUPPLIER LINK
    # -----------------------------
    supplier = canonical.get("supplier")

    if supplier and supplier.get("supplierId"):

        supplier_name = ensure_supplier_exists(supplier)

        update_instance("Product", product_name, {
            "objectProperties": [
                {"property": "hasSupplier", "value": supplier_name}
            ]
        })

    # -----------------------------
    # 4. CUSTOMER LINK
    # -----------------------------
    customer = canonical.get("customer")

    if customer and customer.get("customerId"):

        customer_name = ensure_customer_exists(customer)

        update_instance("Product", product_name, {
            "objectProperties": [
                {"property": "hasCustomer", "value": customer_name}
            ]
        })

    return {
        "status": "success",
        "productId": product_id
    }

def ensure_supplier_exists(canonical_supplier):

    supplier_id = sanitize_id(canonical_supplier["supplierId"])
    supplier_name = f"Supplier_{supplier_id}"

    if not instance_exists("Supplier", supplier_name):
        create_budatec_supplier(canonical_supplier)

    return supplier_name


def ensure_customer_exists(canonical_customer):

    customer_id = sanitize_id(canonical_customer["customerId"])
    customer_name = f"Customer_{customer_id}"

    if not instance_exists("Customer", customer_name):
        create_budatec_customer(canonical_customer)

    return customer_name
