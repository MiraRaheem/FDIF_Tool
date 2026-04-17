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
    "ProductionSensorObservation": set()
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

    # 1. Check cache (FAST)
    if individual_name in INSTANCE_CACHE.get(class_name, set()):
        return True

    # 2. Check Blueprint API (SLOW fallback)
    r = requests.get(f"{BASE_URL}/api/{class_name}")
    instances = r.json().get("instances", [])

    for inst in instances:
        if isinstance(inst, str) and individual_name in inst:
            INSTANCE_CACHE[class_name].add(individual_name)
            return True

    return False


def get_or_create(class_name, individual_name, payload):

    if instance_exists(class_name, individual_name):
        return {"status": "exists", "id": individual_name}

    create_instance(class_name, payload)

    # update cache
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


def create_frank_event(canonical):

    event_type = canonical["eventType"]
    timestamp = canonical["timestamp"]
    machine_id = canonical["machineId"]

    # -------- IDs --------
    sensor_id = f"Sensor_{machine_id}"
    machine_id_clean = f"Machine_{machine_id}"
    metric_id = f"Metric_{event_type}"

    # =============================
    # 0. MACHINE
    # =============================
    get_or_create("Machine", machine_id_clean, {
        "individualName": machine_id_clean,
        "dataProperties": [],
        "objectProperties": []
    })

    # =============================
    # 1. SENSOR
    # =============================
    get_or_create("ProductionMonitoringSensor", sensor_id, {
        "individualName": sensor_id,
        "dataProperties": [],
        "objectProperties": []
    })

    # =============================
    # 2. METRIC
    # =============================
    get_or_create("ProductionMetric", metric_id, {
        "individualName": metric_id,
        "dataProperties": [],
        "objectProperties": []
    })

    # =============================
    # SAFE LINK FUNCTION
    # =============================
    def safe_link(class_name, individual, prop, value):
        update_instance(class_name, individual, {
            "objectProperties": [
                {"property": prop, "value": value}
            ]
        })

    # =============================
    # 3. OBSERVATIONS (FIXED PROPERLY)
    # =============================
    metrics_map = {
        "storageTemperature": canonical.get("storageTemperature"),
        "storageHumidity": canonical.get("storageHumidity"),
        "averagePowerConsumption": canonical.get("averagePowerConsumption"),
        "compressedAirInput": canonical.get("compressedAirInput"),
        "noiseChillerLevel": canonical.get("noiseChillerLevel"),
        "operatingTemperature": canonical.get("operatingTemperature"),
        "powerPeakConsumption": canonical.get("powerPeakConsumption")
    }

    created_any = False

    for metric_name, value in metrics_map.items():

        if value is None:
            continue

        obs_id = f"Observation_{metric_name}_{timestamp}"

        # -------- IDEMPOTENCY PER OBSERVATION --------
        if instance_exists("ProductionSensorObservation", obs_id):
            continue

        # -------- CREATE OBSERVATION --------
        create_instance("ProductionSensorObservation", {
            "individualName": obs_id,
            "dataProperties": clean_properties([
                {"property": "observationTimestamp", "value": timestamp},
                {"property": "observedValue", "value": float(value)}
            ]),
            "objectProperties": []
        })

        INSTANCE_CACHE["ProductionSensorObservation"].add(obs_id)
        created_any = True

        # -------- RELATIONSHIPS --------
        safe_link("ProductionSensorObservation", obs_id, "productionObservedBy", sensor_id)

        safe_link("ProductionMonitoringSensor", sensor_id, "isSensorOfObservation", obs_id)

    # =============================
    # SENSOR RELATIONSHIPS
    # =============================
    safe_link("ProductionMonitoringSensor", sensor_id, "monitorsProdMetric", metric_id)

    safe_link("ProductionMonitoringSensor", sensor_id, "observesMachine", machine_id_clean)

    safe_link("ProductionMetric", metric_id, "isMonitoredBy", sensor_id)

    safe_link("Machine", machine_id_clean, "isObservedBySensor", sensor_id)

    # =============================
    # 4. MAINTENANCE EVENT (FIXED)
    # =============================
    if canonical.get("machineError"):

        maint_id = f"Maintenance_{canonical['machineError']}_{timestamp}"

        get_or_create("MaintenanceEvent", maint_id, {
            "individualName": maint_id,
            "dataProperties": clean_properties([

                {"property": "eventID", "value": maint_id},
                {"property": "eventDescription", "value": canonical.get("machineError")},
                {"property": "eventTimestamp", "value": timestamp},
                {"property": "eventStatus", "value": "OPEN"},
                {"property": "eventSeverity", "value": "HIGH"}

            ]),
            "objectProperties": []
        })

        safe_link("MaintenanceEvent", maint_id, "affectsMachine", machine_id_clean)

        safe_link("Machine", machine_id_clean, "machineAffectedByEvent", maint_id)

    # =============================
    # DONE
    # =============================
    return {
        "status": "success" if created_any else "exists",
        "eventId": f"{event_type}_{timestamp}"
    }
