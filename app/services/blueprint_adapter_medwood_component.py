import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"

session = requests.Session()


# -----------------------------------
# HELPERS
# -----------------------------------

def normalize_id(value):

    if value is None:
        return None

    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )


def safe_json(response):

    try:
        return response.json()

    except Exception:
        return {
            "error": "Invalid JSON response",
            "status_code": response.status_code
        }


# -----------------------------------
# CACHE
# -----------------------------------

COMPONENT_CACHE = None


def load_components():

    global COMPONENT_CACHE

    if COMPONENT_CACHE is None:

        COMPONENT_CACHE = set()

        r = session.get(f"{BASE_URL}/api/ManufacturedComponent")

        data = safe_json(r)

        instances = data.get("instances", [])

        for c in instances:

            if isinstance(c, str) and c:

                COMPONENT_CACHE.add(c)

    return COMPONENT_CACHE


def component_exists(component_id):

    cache = load_components()

    return component_id in cache


def add_to_cache(component_id):

    global COMPONENT_CACHE

    if COMPONENT_CACHE is not None:

        COMPONENT_CACHE.add(component_id)


# -----------------------------------
# API CALLS
# -----------------------------------

def create_instance(payload):

    url = f"{BASE_URL}/api/ManufacturedComponent"

    r = session.post(url, json=payload)

    if r.status_code not in [200, 201]:

        print("❌ CREATE FAILED:", r.status_code, r.text)

    return safe_json(r)


def update_instance(component_id, payload):

    url = f"{BASE_URL}/api/ManufacturedComponent/{component_id}"

    r = session.put(url, json=payload)

    if r.status_code not in [200, 201]:

        print("❌ UPDATE FAILED:", r.status_code, r.text)

    return safe_json(r)


# -----------------------------------
# MAIN FUNCTION
# -----------------------------------

def create_or_update_component(canonical):

    clean_id = normalize_id(canonical["componentID"])

    component_id = f"ManufacturedComponent_{clean_id}"

    payload = {
        "dataProperties": [
            {
                "property": "componentID",
                "value": canonical["componentID"]
            },
            {
                "property": "componentName",
                "value": canonical["componentName"]
            },
            {
                "property": "hasUnitCostEuro",
                "value": canonical["hasUnitCostEuro"]
            },
            {
                "property": "componentWeight",
                "value": canonical["componentWeight"]
            },
            {
                "property": "componentDescription",
                "value": canonical["componentName"]
            }
        ]
    }

    # -----------------------------------
    # CREATE OR UPDATE
    # -----------------------------------

    if component_exists(component_id):

        result = update_instance(component_id, payload)

        status = "updated"

    else:

        result = create_instance({
            "individualName": component_id,
            **payload,
            "objectProperties": []
        })

        status = "created"

        add_to_cache(component_id)

    return {
        "status": status,
        "componentID": component_id,
        "api_response": result
    }
