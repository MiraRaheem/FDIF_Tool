import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


def get_class_metadata(class_name):

    url = f"{BASE_URL}/api/query/metadata/{class_name}"

    r = requests.get(url)

    return r.json()

def get_existing_suppliers():

    url = f"{BASE_URL}/api/query/instances/MaterialSupplier"

    r = requests.get(url)

    return r.json()

def supplier_exists(supplier_id):

    supplier_id = str(supplier_id)   # convert Excel numeric IDs to string

    suppliers = get_existing_suppliers()

    for s in suppliers:

        # If API returns string names
        if isinstance(s, str):
            if supplier_id in s:
                return True

        # If API returns object dictionaries
        if isinstance(s, dict):
            if supplier_id in str(s.get("individualName", "")):
                return True

    return False
def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    r = requests.post(url, json=payload)

    return r.json()

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

            # REQUIRED ontology properties
            {
                "property": "hasLeadTimeDays",
                "value": 0
            },

            {
                "property": "hasCapacity",
                "value": 0
            },

            {
                "property": "hasPaymentTerms",
                "value": "Other"
            }

        ],

        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)
