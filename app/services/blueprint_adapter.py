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
    "MaintenanceEvent": set()  # ✅ ADD THIS
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


# -------------------
# frank
# -------------------

def create_frank_event(canonical):

    timestamp = canonical["timestamp"]
    machine_id = canonical["machineId"]

    machine_id_clean = f"Machine_{machine_id}"
    sensor_id = f"Sensor_machine_{machine_id}"

    # =============================
    # 1. MACHINE
    # =============================
    get_or_create("Machine", machine_id_clean, {
        "individualName": machine_id_clean,
        "dataProperties": clean_properties([
            {"property": "hasMachineID", "value": machine_id}
        ]),
        "objectProperties": []
    })

    # =============================
    # 2. SENSOR (virtual)
    # =============================
    get_or_create("ProductionMonitoringSensor", sensor_id, {
        "individualName": sensor_id,
        "dataProperties": clean_properties([
            {"property": "sensorID", "value": sensor_id},
            {"property": "sensorType", "value": "ProductionPerformanceSensor"},
            {"property": "dataSourceType", "value": "IoT"}
        ]),
        "objectProperties": []
    })

    # -------- Sensor ↔ Machine --------
    update_instance("ProductionMonitoringSensor", sensor_id, {
        "objectProperties": [
            {"property": "isDeployedOnMachineProductionSensor", "value": machine_id_clean}
        ]
    })

    update_instance("Machine", machine_id_clean, {
        "objectProperties": [
            {"property": "monitoredByProdSensor", "value": sensor_id}
        ]
    })

    # =============================
    # 3. METRICS
    # =============================
    metrics_map = {
        "storageTemperature": ("Temperature", "°C"),
        "storageHumidity": ("Humidity", "%"),
        "averagePowerConsumption": ("PowerConsumption", "kW"),
        "compressedAirInput": ("AirPressure", "bar"),
        "noiseChillerLevel": ("NoiseLevel", "dB"),
        "operatingTemperature": ("OperatingTemperature", "°C"),
        "powerPeakConsumption": ("PeakPower", "kW")
    }

    created_any = False
    created_observations = []

    for field, value in canonical.items():

        if field not in metrics_map or value is None:
            continue

        metric_name, unit = metrics_map[field]

        metric_id = f"Metric_{metric_name}"
        obs_id = f"Observation_{metric_name}_{timestamp}"

        # -------- METRIC --------
        get_or_create("ProductionMetric", metric_id, {
            "individualName": metric_id,
            "dataProperties": clean_properties([
                {"property": "parameterID", "value": metric_id},
                {"property": "parameterName", "value": metric_name},
                {"property": "unitOfMeasurement", "value": unit}
            ]),
            "objectProperties": []
        })

        # -------- Sensor ↔ Metric --------
        update_instance("ProductionMonitoringSensor", sensor_id, {
            "objectProperties": [
                {"property": "monitorsProdMetric", "value": metric_id}
            ]
        })

        update_instance("ProductionMetric", metric_id, {
            "objectProperties": [
                {"property": "prodMetricMonitoredBy", "value": sensor_id}
            ]
        })

        # -------- OBSERVATION --------
        if instance_exists("ProductionSensorObservation", obs_id):
            continue

        create_instance("ProductionSensorObservation", {
            "individualName": obs_id,
            "dataProperties": clean_properties([
                {"property": "observationID", "value": obs_id},
                {"property": "observedValue", "value": float(value)},
                {"property": "observationTimestamp", "value": timestamp},
                {"property": "unitOfMeasureSensor", "value": unit}
            ]),
            "objectProperties": []
        })

        INSTANCE_CACHE["ProductionSensorObservation"].add(obs_id)
        created_any = True
        created_observations.append(obs_id)

        # -------- Sensor ↔ Observation --------
        update_instance("ProductionSensorObservation", obs_id, {
            "objectProperties": [
                {"property": "productionObservedBy", "value": sensor_id}
            ]
        })

        update_instance("ProductionMonitoringSensor", sensor_id, {
            "objectProperties": [
                {"property": "observesProduction", "value": obs_id}
            ]
        })

    # =============================
    # 4. MAINTENANCE EVENT
    # =============================
    if canonical.get("machineError"):

        maint_id = f"Maintenance_{canonical['machineError']}_{timestamp}"

        get_or_create("MaintenanceEvent", maint_id, {
            "individualName": maint_id,
            "dataProperties": clean_properties([
                {"property": "eventID", "value": maint_id},
                {"property": "eventDescription", "value": canonical.get("machineError")},
                {"property": "eventTimestamp", "value": timestamp},
                {"property": "eventStatus", "value": "Detected"},
                {"property": "eventSeverity", "value": "High"}
            ]),
            "objectProperties": []
        })

        # -------- Event ↔ Machine --------
        update_instance("MaintenanceEvent", maint_id, {
            "objectProperties": [
                {"property": "affectsMachine", "value": machine_id_clean}
            ]
        })

        update_instance("Machine", machine_id_clean, {
            "objectProperties": [
                {"property": "machineAffectedByEvent", "value": maint_id}
            ]
        })

        # -------- Observation → Event --------
        for obs_id in created_observations:
            update_instance("ProductionSensorObservation", obs_id, {
                "objectProperties": [
                    {"property": "triggersProductionEvent", "value": maint_id}
                ]
            })

    # =============================
    # DONE
    # =============================
    return {
        "status": "success" if created_any else "exists",
        "machine": machine_id_clean,
        "sensor": sensor_id
    }



def create_frank_alert(canonical):

    event_id = canonical["eventId"]
    timestamp = canonical["time"]
    description = canonical.get("descriptionValue")
    alert_text = canonical.get("alert")

    machine_id = canonical["data"]["machineId"]
    current_value = canonical["data"].get("currentValue")
    threshold = canonical["data"].get("valueThreshold")

    machine_id_clean = f"Machine_{machine_id}"
    maint_id = f"Maintenance_{event_id}"

    # =============================
    # 1. MACHINE (ensure exists)
    # =============================
    get_or_create("Machine", machine_id_clean, {
        "individualName": machine_id_clean,
        "dataProperties": clean_properties([
            {"property": "hasMachineID", "value": machine_id}
        ]),
        "objectProperties": []
    })

    # =============================
    # 2. BUILD DESCRIPTION (SMART)
    # =============================
    full_description = description or ""

    if current_value not in ["NA", None]:
        full_description += f" | Current: {current_value}"

    if threshold not in ["NA", None]:
        full_description += f" | Threshold: {threshold}"

    if alert_text:
        full_description += f" | Alert: {alert_text}"

    # =============================
    # 3. DETERMINE SEVERITY
    # =============================
    if canonical["eventType"] == "machineErrorCode":
        severity = "Critical"
        status = "Active"
    else:
        severity = "High"
        status = "Detected"

    # =============================
    # 4. CREATE EVENT
    # =============================
    get_or_create("MaintenanceEvent", maint_id, {
        "individualName": maint_id,
        "dataProperties": clean_properties([
            {"property": "eventID", "value": maint_id},
            {"property": "eventDescription", "value": full_description},
            {"property": "eventTimestamp", "value": timestamp},
            {"property": "eventSeverity", "value": severity},
            {"property": "eventStatus", "value": status}
        ]),
        "objectProperties": []
    })

    # =============================
    # 5. LINK EVENT ↔ MACHINE (BOTH DIRECTIONS)
    # =============================
    update_instance("MaintenanceEvent", maint_id, {
        "objectProperties": [
            {"property": "affectsMachine", "value": machine_id_clean}
        ]
    })

    update_instance("Machine", machine_id_clean, {
        "objectProperties": [
            {"property": "machineAffectedByEvent", "value": maint_id}
        ]
    })

    # =============================
    # DONE
    # =============================
    return {
        "status": "success",
        "eventId": maint_id,
        "machine": machine_id_clean
    }
