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
from app.services.harmonizer import harmonize_bom

from app.services.blueprint_adapter_medwood_bom import (
    create_or_update_bom,
    link_bom_to_product,
    link_material_to_bom,
    link_component_to_bom
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
    create_or_update_station,
    ensure_factory_exists,
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
    required_columns = {"CENTROS DE TRABAJO", "Cantidad"}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise ValueError(f"Station workbook is missing required columns: {missing_columns}")

    prepared = []
    rejected = []
    for index, row in df.iterrows():
        excel_row = int(index) + 2
        source_name = row.get("CENTROS DE TRABAJO")
        source_name = None if pd.isna(source_name) else str(source_name).strip()
        try:
            canonical = harmonize_medwood_station(row)
            validated = validate_station(canonical)
            prepared.append({"row": excel_row, "canonical": validated})
        except Exception as e:
            rejected.append({"row": excel_row, "stationName": source_name, "reason": str(e)})

    # Reject all rows involved in a conflicting normalized ID before making
    # any writes. Repeated identical rows keep the first and report the rest.
    groups = {}
    for item in prepared:
        groups.setdefault(item["canonical"]["stationId"], []).append(item)

    conflicted_rows = set()
    duplicate_rows = set()
    for station_id, items in groups.items():
        if len(items) < 2:
            continue
        signatures = {
            (
                item["canonical"].get("sourceStationId"),
                item["canonical"].get("stationName"),
                item["canonical"].get("maxCapacity"),
                item["canonical"].get("capacityHoursPerDay"),
            )
            for item in items
        }
        if len(signatures) > 1:
            conflicted_rows.update(item["row"] for item in items)
            for item in items:
                rejected.append({
                    "row": item["row"],
                    "stationName": item["canonical"].get("stationName"),
                    "reason": f"Station ID '{station_id}' conflicts with another row after ID normalization; all rows with this ID were skipped.",
                })
        else:
            duplicate_rows.update(item["row"] for item in items[1:])
            for item in items[1:]:
                rejected.append({
                    "row": item["row"],
                    "stationName": item["canonical"].get("stationName"),
                    "reason": f"Duplicate of row {items[0]['row']} with identical Station data; duplicate row was skipped.",
                })

    ingested = []
    ingestion_failures = []
    eligible = [
        item for item in prepared
        if item["row"] not in conflicted_rows and item["row"] not in duplicate_rows
    ]
    if eligible:
        try:
            ensure_factory_exists()
        except Exception as e:
            ingestion_failures.extend({
                "row": item["row"],
                "stationId": item["canonical"]["stationId"],
                "reason": str(e),
            } for item in eligible)
            eligible = []

    for item in eligible:
        canonical = item["canonical"]
        try:
            result = create_or_update_station(canonical)
            ingested.append({
                "row": item["row"],
                "stationId": canonical["stationId"],
                "status": result.get("status", "success") if isinstance(result, dict) else "success",
            })
        except Exception as e:
            ingestion_failures.append({
                "row": item["row"],
                "stationId": canonical["stationId"],
                "reason": str(e),
            })

    return {
        "status": "completed_with_issues" if rejected or ingestion_failures else "completed",
        "entity": "station",
        "total": len(df),
        "ingestedCount": len(ingested),
        "rejectedCount": len(rejected),
        "ingestionFailureCount": len(ingestion_failures),
        "ingested": ingested,
        "rejected": rejected,
        "ingestionFailures": ingestion_failures,
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


def process_bom_excel(file):

    df = pd.read_excel(file.file)

    # --------------------------------
    # CREATE BOM
    # --------------------------------
    canonical = harmonize_bom(df)

    bom_id = create_or_update_bom(canonical)

    # --------------------------------
    # LINK PRODUCT
    # --------------------------------
    product_id = canonical["bomId"]

    link_bom_to_product(product_id, bom_id)

    material_count = 0
    component_count = 0

    # --------------------------------
    # LOOP ROWS
    # --------------------------------
    rows = df.to_dict(orient="records")

    for row in rows:

        tipo = str(row.get("TIPO", "")).strip()

        entity_id = str(row.get("Artículo/Recurso")).strip()

        # --------------------------------
        # MATERIALS
        # --------------------------------
        if tipo == "Materia prima":

            link_material_to_bom(entity_id, bom_id)
            material_count += 1

        # --------------------------------
        # COMPONENTS
        # --------------------------------
        elif tipo == "Semielaborado":

            link_component_to_bom(entity_id, bom_id)
            component_count += 1

    return {
        "status": "completed",
        "bom": bom_id,
        "materialsLinked": material_count,
        "componentsLinked": component_count
    }
