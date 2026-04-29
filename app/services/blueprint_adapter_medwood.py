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
# MEDWOOD SUPPLIER
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
            {"property": "hasSupplierName", "value": canonical.get("supplierName")},
            {"property": "hasCountry", "value": canonical.get("country")}
        ],
        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)


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

    return update_instance("MaterialSupplier", supplier_name, {
        "dataProperties": [
            {"property": "hasTotalDeliveries", "value": canonical.get("totalDeliveries")},
            {"property": "hasDelayedDeliveries", "value": canonical.get("delayedDeliveries")},
            {"property": "hasDelayPercentage", "value": canonical.get("delayPercentage")}
        ]
    })
