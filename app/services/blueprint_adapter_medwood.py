import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


# -----------------------------
# API CALLS
# -----------------------------

def create_instance(class_name, payload):
    url = f"{BASE_URL}/api/{class_name}"
    r = requests.post(url, json=payload)
    return r.json()


def update_instance(class_name, instance_id, payload):
    url = f"{BASE_URL}/api/{class_name}/{instance_id}"
    r = requests.put(url, json=payload)
    return r.json()


def get_instances(class_name):
    r = requests.get(f"{BASE_URL}/api/{class_name}")
    return r.json().get("instances", [])


# -----------------------------
# EXISTENCE CHECKS
# -----------------------------

def supplier_exists(supplier_id):
    suppliers = get_instances("MaterialSupplier")

    for s in suppliers:
        if isinstance(s, str) and supplier_id in s:
            return True
        if isinstance(s, dict) and s.get("hasSupplierID") == supplier_id:
            return True

    return False


def location_exists(location_id):
    locations = get_instances("Location")

    for loc in locations:
        if isinstance(loc, str) and location_id in loc:
            return True
        if isinstance(loc, dict) and loc.get("individualName") == location_id:
            return True

    return False


# -----------------------------
# MEDWOOD SUPPLIER (CREATE OR UPDATE)
# -----------------------------

def create_or_update_supplier(canonical):

    supplier_id = str(canonical["supplierId"])
    supplier_name = f"MaterialSupplier_{supplier_id}"
    location_id = f"Location_{supplier_id}"

    # -----------------------------
    # 1. CREATE OR UPDATE LOCATION
    # -----------------------------
    location_payload = {
        "dataProperties": [
            {"property": "locationAddress", "value": canonical["location"].get("address")},
            {"property": "city", "value": canonical["location"].get("city")},
            {"property": "postalCode", "value": canonical["location"].get("postalCode")},
            {"property": "country", "value": canonical.get("country")}
        ]
    }

    if location_exists(location_id):
        update_instance("Location", location_id, location_payload)
    else:
        create_instance("Location", {
            "individualName": location_id,
            **location_payload,
            "objectProperties": []
        })

    # -----------------------------
    # 2. CREATE OR UPDATE SUPPLIER
    # -----------------------------
    supplier_payload = {
        "dataProperties": [
            {"property": "hasSupplierID", "value": supplier_id},
            {"property": "hasSupplierName", "value": canonical.get("supplierName")},
            {"property": "hasCountry", "value": canonical.get("country")},
            {"property": "hasCapacity", "value": 0},
            {"property": "hasLeadTimeDays", "value": 0},
            {"property": "hasPaymentTerms", "value": "Other"}
        ]
    }

    if supplier_exists(supplier_id):
        update_instance("MaterialSupplier", supplier_name, supplier_payload)
        status = "updated"
    else:
        create_instance("MaterialSupplier", {
            "individualName": supplier_name,
            **supplier_payload,
            "objectProperties": []
        })
        status = "created"

    # -----------------------------
    # 3. LINK RELATIONSHIPS (SAFE)
    # -----------------------------

    # Supplier → Location
    update_instance("MaterialSupplier", supplier_name, {
        "objectProperties": [
            {"property": "locatedAt", "value": location_id}
        ]
    })

    # Location → Supplier
    update_instance("Location", location_id, {
        "objectProperties": [
            {"property": "isLocationOfSupplier", "value": supplier_name}
        ]
    })

    return {
        "status": status,
        "supplierId": supplier_id
    }


# -----------------------------
# MEDWOOD SUPPLIER PERFORMANCE
# -----------------------------

def update_supplier_performance(canonical):

    supplier_id = canonical["supplierId"]
    supplier_name = f"MaterialSupplier_{supplier_id}"

    if not supplier_exists(supplier_id):
        return {
            "status": "error",
            "message": f"Supplier {supplier_id} does not exist"
        }

    # ✔ Use ONLY valid ontology property
    return update_instance("MaterialSupplier", supplier_name, {
        "dataProperties": [
            {"property": "hasRating", "value": canonical.get("currentEvaluation")}
        ]
    })
