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

    location_id = f"SupplierLocation_{supplier_id}"

    # -------- Location instance --------

    location_payload = {

        "individualName": location_id,

        "dataProperties": [

            {
                "property": "locationAddress",
                "value": canonical["location"]["address"]
            },

            {
                "property": "postalCode",
                "value": canonical["location"]["postalCode"]
            },

            {
                "property": "city",
                "value": canonical["location"]["city"]
            },

            {
                "property": "country",
                "value": canonical["country"]
            }

        ],

        "objectProperties": []
    }

    create_instance("Location", location_payload)

    # -------- Supplier instance --------

    supplier_payload = {

        "individualName": f"MaterialSupplier_{supplier_id}",

        "dataProperties": [

            {
                "property": "hasSupplierID",
                "value": supplier_id
            },

            {
                "property": "hasCountry",
                "value": canonical["country"]
            },

            {
                "property": "rdfs:label",
                "value": canonical["supplierName"]
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

        "objectProperties": [

            {
                "property": "locatedAt",
                "value": location_id
            }

        ]
    }

    return create_instance("MaterialSupplier", supplier_payload)

def add_supplier_performance(canonical):

    supplier_id = str(canonical["supplierId"])

    data_properties = [

        {
            "property": "hasTotalDeliveries",
            "value": canonical.get("totalDeliveries")
        },

        {
            "property": "hasDelayedDeliveries",
            "value": canonical.get("delayedDeliveries")
        },

        {
            "property": "hasDelayPercentage",
            "value": canonical.get("delayPercentage")
        },

        {
            "property": "hasCurrentEvaluation",
            "value": canonical.get("currentEvaluation")
        },

        {
            "property": "hasPreviousEvaluation",
            "value": canonical.get("previousEvaluation")
        }

    ]
    data_properties = [
    p for p in data_properties if p["value"] is not None]

    payload = {

        "individualName": f"MaterialSupplier_{supplier_id}",

        "dataProperties": clean_properties(data_properties),

        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)
    
def clean_properties(properties):

    cleaned = []

    for p in properties:
        if p["value"] is not None:
            cleaned.append(p)

    return cleaned
