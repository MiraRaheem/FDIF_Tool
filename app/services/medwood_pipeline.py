import pandas as pd
from app.services.harmonizer import (
    harmonize_medwood_supplier,
    harmonize_supplier_performance
)

from app.services.validator import (
    validate_supplier,
    validate_supplier_performance
)

from app.services.blueprint_adapter_medwood import (
    create_or_update_supplier,
    update_supplier_performance
)
from app.services.harmonizer import harmonize_medwood_material
from app.services.validator import validate_material

from app.services.blueprint_adapter_medwood_material import (
    create_or_update_material
)

from app.services.harmonizer import harmonize_component

from app.services.blueprint_adapter_medwood_component import (
    create_or_update_component
)
from app.services.harmonizer import (
    harmonize_medwood_product_type
)

from app.services.validator import (
    validate_product_type
)

from app.services.blueprint_adapter_medwood_product import (
    create_or_update_product_type
)
def process_medwood_supplier_json(body):

    raw = body.get("data", {})

    canonical = harmonize_medwood_supplier(raw)
    validated = validate_supplier(canonical)
    result = create_or_update_supplier(validated)

    return {
        "status": "success",
        "entity": "supplier",
        "canonical": canonical,
        "blueprint": result
    }


def process_medwood_supplier_excel(file):

    df = pd.read_excel(file.file)
    rows = df.to_dict(orient="records")

    results = []

    for i, row in enumerate(rows):
        try:
            canonical = harmonize_medwood_supplier(row)
            validated = validate_supplier(canonical)
            create_or_update_supplier(validated)

            results.append({
                "row": i,
                "status": "success",
                "id": validated["supplierId"]
            })

        except Exception as e:
            results.append({
                "row": i,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "supplier",
        "total": len(rows),
        "results": results[:10]
    }


def process_supplier_performance_json(body):

    raw = body.get("data", {})

    canonical = harmonize_supplier_performance(raw)
    validated = validate_supplier_performance(canonical)

    result = update_supplier_performance(validated)

    return {
        "status": "success",
        "entity": "supplier_performance",
        "canonical": canonical,
        "blueprint": result
    }

def process_supplier_performance_excel(file):

    import pandas as pd

    df = pd.read_excel(file.file)
    rows = df.to_dict(orient="records")

    results = []

    for i, row in enumerate(rows):
        try:
            canonical = harmonize_supplier_performance(row)
            validated = validate_supplier_performance(canonical)

            update_supplier_performance(validated)

            results.append({
                "row": i,
                "status": "success",
                "id": validated["supplierId"]
            })

        except Exception as e:
            results.append({
                "row": i,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "supplier_performance",
        "total": len(rows),
        "results": results[:10]
    }


import pandas as pd

from app.services.harmonizer import harmonize_medwood_station
from app.services.validator import validate_station
from app.services.blueprint_adapter_medwood_station import (
    create_or_update_station
)


def process_station_json(body):

    raw = body.get("data", {})

    canonical = harmonize_medwood_station(raw)
    validated = validate_station(canonical)

    result = create_or_update_station(validated)

    return {
        "status": "success",
        "entity": "station",
        "canonical": canonical,
        "blueprint": result
    }


def process_station_excel(file):

    df = pd.read_excel(file.file)
    rows = df.to_dict(orient="records")

    results = []

    for i, row in enumerate(rows):
        try:
            canonical = harmonize_medwood_station(row)
            validated = validate_station(canonical)

            create_or_update_station(validated)

            results.append({
                "row": i,
                "status": "success",
                "id": canonical["stationId"]
            })

        except Exception as e:
            results.append({
                "row": i,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "station",
        "total": len(rows),
        "results": results[:10]
    }

def process_material_json(body):

    raw = body.get("data", {})

    canonical = harmonize_medwood_material(raw)

    validated = validate_material(canonical)

    result = create_or_update_material(validated)

    return {
        "status": "success",
        "entity": "material",
        "canonical": canonical,
        "blueprint": result
    }


def process_material_excel(file):

    df = pd.read_excel(file.file)

    rows = df.to_dict(orient="records")

    results = []

    for i, row in enumerate(rows):

        try:

            canonical = harmonize_medwood_material(row)

            validated = validate_material(canonical)

            create_or_update_material(validated)

            results.append({
                "row": i,
                "status": "success",
                "id": canonical["materialId"]
            })

        except Exception as e:

            results.append({
                "row": i,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "material",
        "total": len(rows),
        "results": results[:10]
    }

def process_component_json(payload):

    canonical = harmonize_component(payload)

    blueprint = create_or_update_component(canonical)

    return {
        "status": "success",
        "entity": "component",
        "canonical": canonical,
        "blueprint": blueprint
    }


def process_component_excel(df):

    results = []

    for index, row in df.iterrows():

        try:

            canonical = harmonize_component(row)

            blueprint = create_or_update_component(canonical)

            results.append({
                "row": index,
                "status": "success",
                "componentID": canonical["componentID"]
            })

        except Exception as e:

            results.append({
                "row": index,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "component",
        "total": len(results),
        "results": results
    }

def process_product_type_json(body):

    raw = body.get("data", {})

    canonical = harmonize_medwood_product_type(raw)

    validated = validate_product_type(canonical)

    result = create_or_update_product_type(validated)

    return {
        "status": "success",
        "entity": "product_type",
        "canonical": canonical,
        "blueprint": result
    }
