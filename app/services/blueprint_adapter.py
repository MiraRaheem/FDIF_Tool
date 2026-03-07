import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


def get_class_metadata(class_name):

    url = f"{BASE_URL}/api/query/metadata/{class_name}"

    r = requests.get(url)

    return r.json()


def create_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    r = requests.post(url, json=payload)

    return r.json()


def create_supplier_instance(canonical):

    payload = {

        "individualName": f"MaterialSupplier_{canonical['supplierId']}",

        "dataProperties": [

            {
                "property": "hasSupplierID",
                "value": canonical["supplierId"]
            },

            {
                "property": "hasName",
                "value": canonical["supplierName"]
            },

            {
                "property": "hasCountry",
                "value": canonical["address"]["country"]
            }
        ],

        "objectProperties": []
    }

    return create_instance("MaterialSupplier", payload)
