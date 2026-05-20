import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"
session = requests.Session()


# =========================================================
# HELPERS
# =========================================================

def put_object_properties(class_name, individual_name, properties):

    payload = {
        "objectProperties": properties
    }

    r = session.put(
        f"{BASE_URL}/api/{class_name}/{individual_name}",
        json=payload
    )

    print(f"PUT {class_name}/{individual_name} -> {r.status_code}")

    if r.status_code >= 400:
        print(r.text)

    return r


def create_individual(class_name, individual_name,
                      data_properties=None,
                      object_properties=None):

    payload = {
        "individualName": individual_name,
        "dataProperties": data_properties or [],
        "objectProperties": object_properties or []
    }

    r = session.post(
        f"{BASE_URL}/api/{class_name}",
        json=payload
    )

    print(f"POST {class_name}/{individual_name} -> {r.status_code}")

    if r.status_code >= 400:
        print(r.text)

    return r


# =========================================================
# CREATE BOM
# =========================================================

def create_or_update_bom(canonical):

    bom_id = f"BOM_{canonical['bomId']}"

    create_individual(
        class_name="BillOfMaterials",
        individual_name=bom_id,
        data_properties=[
            {
                "property": "hasBOMID",
                "value": str(canonical["bomId"])
            },
            {
                "property": "hasBOMVersion",
                "value": str(canonical["version"])
            },
            {
                "property": "hasBOMNote",
                "value": str(canonical["note"])
            }
        ]
    )

    return bom_id


# =========================================================
# LINK BOM <-> PRODUCT
# =========================================================

def link_bom_to_product(product_id, bom_id):

    product_name = f"ProductType_{product_id}"

    # BOM -> Product
    put_object_properties(
        class_name="BillOfMaterials",
        individual_name=bom_id,
        properties=[
            {
                "property": "isBOMOf",
                "value": product_name
            }
        ]
    )

    # Product -> BOM
    put_object_properties(
        class_name="ProductType",
        individual_name=product_name,
        properties=[
            {
                "property": "hasBOM",
                "value": bom_id
            }
        ]
    )


# =========================================================
# LINK MANY MATERIALS TO BOM
# =========================================================

def link_materials_to_bom(material_ids, bom_id):

    bom_properties = []

    for material_id in material_ids:

        material_name = f"Material_{material_id}"

        # collect ALL materials in ONE PUT
        bom_properties.append({
            "property": "includesMaterial",
            "value": material_name
        })

        # reverse relation
        put_object_properties(
            class_name="Material",
            individual_name=material_name,
            properties=[
                {
                    "property": "materialOfBOM",
                    "value": bom_id
                }
            ]
        )

    # ONE SINGLE PUT
    put_object_properties(
        class_name="BillOfMaterials",
        individual_name=bom_id,
        properties=bom_properties
    )


# =========================================================
# LINK MANY COMPONENTS TO BOM
# =========================================================

def link_components_to_bom(component_ids, bom_id):

    bom_properties = []

    for component_id in component_ids:

        component_name = f"ManufacturedComponent_{component_id}"

        # collect ALL components in ONE PUT
        bom_properties.append({
            "property": "includesComponent",
            "value": component_name
        })

        # reverse relation
        put_object_properties(
            class_name="ManufacturedComponent",
            individual_name=component_name,
            properties=[
                {
                    "property": "isIncludedInBOM",
                    "value": bom_id
                }
            ]
        )

    # ONE SINGLE PUT
    put_object_properties(
        class_name="BillOfMaterials",
        individual_name=bom_id,
        properties=bom_properties
    )


# =========================================================
# FULL BOM INGESTION
# =========================================================

def ingest_bom(canonical):

    bom_id = create_or_update_bom(canonical)

    # product relation
    link_bom_to_product(
        canonical["productId"],
        bom_id
    )

    # materials
    link_materials_to_bom(
        canonical["materials"],
        bom_id
    )

    # components
    link_components_to_bom(
        canonical["components"],
        bom_id
    )

    return bom_id
