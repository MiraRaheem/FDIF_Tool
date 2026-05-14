import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"

session = requests.Session()

MATERIAL_CACHE = None


# -----------------------------
# HELPERS
# -----------------------------
def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {
            "error": "Invalid JSON",
            "status_code": response.status_code
        }


# -----------------------------
# CACHE
# -----------------------------
def load_materials():

    global MATERIAL_CACHE

    if MATERIAL_CACHE is None:

        MATERIAL_CACHE = set()

        r = session.get(f"{BASE_URL}/api/Material")

        data = safe_json(r)

        instances = data.get("instances", [])

        for m in instances:

            if isinstance(m, str) and m:
                MATERIAL_CACHE.add(m)

    return MATERIAL_CACHE


def material_exists(material_id):

    cache = load_materials()

    return material_id in cache


def add_to_cache(material_id):

    global MATERIAL_CACHE

    if MATERIAL_CACHE is not None:
        MATERIAL_CACHE.add(material_id)


# -----------------------------
# API
# -----------------------------
def create_instance(payload):

    r = session.post(
        f"{BASE_URL}/api/Material",
        json=payload
    )

    return safe_json(r)


def update_instance(material_id, payload):

    r = session.put(
        f"{BASE_URL}/api/Material/{material_id}",
        json=payload
    )

    return safe_json(r)


# -----------------------------
# MAIN
# -----------------------------
def create_or_update_material(canonical):

    material_individual = f"Material_{canonical['materialId']}"

    supplier_individual = f"MaterialSupplier_{canonical['supplierId']}"

    payload = {

        "dataProperties": [

            {
                "property": "hasMaterialID",
                "value": canonical["materialId"]
            },

            {
                "property": "hasMaterialName",
                "value": canonical["materialName"]
            },

            {
                "property": "hasMaterialOfType",
                "value": canonical["materialType"]
            },

            {
                "property": "hasMaterialWeight",
                "value": canonical["materialWeight"]
            },

            {
                "property": "materialFamily",
                "value": canonical["materialFamily"]
            },

            {
                "property": "materialSubfamily",
                "value": canonical["materialSubfamily"]
            }

        ],

        "objectProperties": [

            {
                "property": "isSuppliedByMaterialSupplier",
                "value": supplier_individual
            }

        ]
    }

    # -----------------------------
    # CREATE OR UPDATE MATERIAL
    # -----------------------------
    if material_exists(material_individual):

        result = update_instance(
            material_individual,
            payload
        )

        status = "updated"

    else:

        result = create_instance({
            "individualName": material_individual,
            **payload
        })

        status = "created"

        add_to_cache(material_individual)

    # -----------------------------
    # INVERSE RELATION
    # -----------------------------
    session.put(
        f"{BASE_URL}/api/MaterialSupplier/{supplier_individual}",
        json={
            "objectProperties": [
                {
                    "property": "suppliesMaterial",
                    "value": material_individual
                }
            ]
        }
    )

    return {
        "status": status,
        "materialId": material_individual,
        "supplier": supplier_individual,
        "api_response": result
    }
