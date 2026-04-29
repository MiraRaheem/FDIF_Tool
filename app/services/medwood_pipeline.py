import pandas as pd
from app.services.harmonizer import harmonize_medwood_supplier
from app.services.validator import validate_supplier
from app.services.blueprint_adapter import create_supplier_instance


def process_medwood_supplier_json(body):

    raw = body.get("data", {})

    canonical = harmonize_medwood_supplier(raw)
    validated = validate_supplier(canonical)
    result = create_supplier_instance(validated)

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
            create_supplier_instance(validated)

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
