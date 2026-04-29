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
