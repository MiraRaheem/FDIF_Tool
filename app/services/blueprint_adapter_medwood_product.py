import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"

session = requests.Session()


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {
            "error": response.text,
            "status_code": response.status_code
        }


def create_instance(payload):

    r = session.post(
        f"{BASE_URL}/api/ProductType",
        json=payload
    )

    return safe_json(r)


def update_instance(product_id, payload):

    r = session.put(
        f"{BASE_URL}/api/ProductType/{product_id}",
        json=payload
    )

    return safe_json(r)


def get_instances():

    r = session.get(
        f"{BASE_URL}/api/ProductType"
    )

    return safe_json(r).get("instances", [])


def product_exists(product_id):

    products = get_instances()

    for p in products:

        if isinstance(p, str) and product_id in p:
            return True

        if isinstance(p, dict):
            if p.get("hasProductID") == product_id:
                return True

    return False


def create_or_update_product_type(canonical):

    product_id = canonical["productId"]

    individual_name = f"ProductType_{product_id}"

    payload = {

        "dataProperties": [

            {
                "property": "hasProductID",
                "value": canonical["productId"]
            },

            {
                "property": "hasProductName",
                "value": canonical["productName"]
            },

            {
                "property": "hasProductFamily",
                "value": canonical["productFamily"]
            },

            {
                "property": "hasProductCost",
                "value": canonical["productCost"]
            },

            {
                "property": "hasProductPrice",
                "value": canonical["productPrice"]
            }
        ],

        "objectProperties": []
    }

    if product_exists(product_id):

        result = update_instance(
            individual_name,
            payload
        )

        status = "updated"

    else:

        result = create_instance({
            "individualName": individual_name,
            **payload
        })

        status = "created"

    return {
        "status": status,
        "productId": product_id,
        "blueprint": result
    }
