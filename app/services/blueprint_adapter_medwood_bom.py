import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"
session = requests.Session()

def create_or_update_bom(canonical):

    bom_id = f"BOM_{canonical['bomId']}"

    payload = {
        "dataProperties": [
            {
                "property": "hasBOMID",
                "value": canonical["bomId"]
            },
            {
                "property": "hasBOMVersion",
                "value": canonical["version"]
            },
            {
                "property": "hasBOMNote",
                "value": canonical["note"]
            }
        ]
    }

    r = session.post(
        f"{BASE_URL}/api/BillOfMaterials",
        json={
            "individualName": bom_id,
            **payload,
            "objectProperties": []
        }
    )

    return bom_id

def link_bom_to_product(product_id, bom_id):

    product_name = f"ProductType_{product_id}"

    # BOM -> Product
    session.put(
        f"{BASE_URL}/api/BillOfMaterials/{bom_id}",
        json={
            "objectProperties": [
                {
                    "property": "isBOMOf",
                    "value": product_name
                }
            ]
        }
    )

    # Product -> BOM
    session.put(
        f"{BASE_URL}/api/ProductType/{product_name}",
        json={
            "objectProperties": [
                {
                    "property": "hasBOM",
                    "value": bom_id
                }
            ]
        }
    )

def link_material_to_bom(material_id, bom_id):

    material_name = f"Material_{material_id}"

    # BOM -> Material
    session.put(
        f"{BASE_URL}/api/BillOfMaterials/{bom_id}",
        json={
            "objectProperties": [
                {
                    "property": "includesMaterial",
                    "value": material_name
                }
            ]
        }
    )

    # Material -> BOM
    session.put(
        f"{BASE_URL}/api/Material/{material_name}",
        json={
            "objectProperties": [
                {
                    "property": "materialOfBOM",
                    "value": bom_id
                }
            ]
        }
    )

def link_component_to_bom(component_id, bom_id):

    component_name = f"ManufacturedComponent_{component_id}"

    # BOM -> Component
    session.put(
        f"{BASE_URL}/api/BillOfMaterials/{bom_id}",
        json={
            "objectProperties": [
                {
                    "property": "includesComponent",
                    "value": component_name
                }
            ]
        }
    )

    # Component -> BOM
    session.put(
        f"{BASE_URL}/api/ManufacturedComponent/{component_name}",
        json={
            "objectProperties": [
                {
                    "property": "isIncludedInBOM",
                    "value": bom_id
                }
            ]
        }
    )

