from app.services.harmonizer_budatec import harmonize_budatec_supplier
from app.services.validator_budatec import validate_budatec_supplier
from app.services.blueprint_adapter import create_budatec_supplier

from app.services.harmonizer_budatec_customer import harmonize_budatec_customer
from app.services.validator_budatec_customer import validate_budatec_customer
from app.services.blueprint_adapter import create_budatec_customer
from app.services.budatec_utils import extract_rows, normalize_customer
from app.services.harmonizer_budatec_customer import harmonize_budatec_customer
from app.services.validator_budatec_customer import validate_budatec_customer
from app.services.blueprint_adapter import create_budatec_customer
from app.services.budatec_utils import extract_rows, normalize_supplier, normalize_customer
from app.services.budatec_utils import split_item_row
from app.services.harmonizer_budatec_item import harmonize_budatec_item
from app.services.validator_budatec_item import validate_budatec_item
from app.services.blueprint_adapter import create_budatec_item
from app.services.budatec_utils import normalize_item
import json


# =========================
# SUPPLIER
# =========================

def process_supplier_json(body):

    raw = body.get("data", {})

    if isinstance(raw, str):
        raw = json.loads(raw)

    raw = normalize_supplier(raw)

    canonical = harmonize_budatec_supplier(raw)
    validated = validate_budatec_supplier(canonical)
    result = create_budatec_supplier(validated)

    return {
        "status": "success",
        "entity": "supplier",
        "canonical": canonical,
        "blueprint": result
    }


def process_supplier_excel(file):

    rows = extract_rows(file.file)

    results = []

    for i, row in enumerate(rows):

        try:
            row = normalize_supplier(row)

            canonical = harmonize_budatec_supplier(row)
            validated = validate_budatec_supplier(canonical)
            blueprint = create_budatec_supplier(validated)

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

def process_customer_json(body):

    raw = body.get("data", {})

    raw = normalize_customer(raw)

    canonical = harmonize_budatec_customer(raw)
    validated = validate_budatec_customer(canonical)
    result = create_budatec_customer(validated)

    return {
        "status": "success",
        "entity": "customer",
        "canonical": canonical,
        "blueprint": result
    }

# =========================
# CUSTOMER (EXCEL)
# =========================

def process_customer_excel(file):

    rows = extract_rows(file.file)

    results = []

    for i, row in enumerate(rows):

        try:
            row = normalize_customer(row)

            canonical = harmonize_budatec_customer(row)
            validated = validate_budatec_customer(canonical)
            blueprint = create_budatec_customer(validated)

            results.append({
                "row": i,
                "status": "success",
                "id": validated.get("customerId")
            })

        except Exception as e:
            results.append({
                "row": i,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "customer",
        "total": len(rows),
        "results": results[:10]
    }


def process_item_json(body):

    raw = body.get("data", {})

    if isinstance(raw, str):
        raw = json.loads(raw)

    raw = normalize_item(raw)

    canonical = harmonize_budatec_item(raw)
    validated = validate_budatec_item(canonical)
    result = create_budatec_item(validated)

    return {
        "status": "success",
        "entity": "item",
        "canonical": canonical,
        "blueprint": result
    }
    
def process_item_excel(file):

    from app.services.budatec_utils import extract_items_rows

    rows = extract_items_rows(file.file)

    results = []

    for i, row in enumerate(rows):

        try:
            split = split_item_row(row)
            print("SPLIT:", split)

            # -------- ITEM --------
            item = normalize_item(split["item"])

            if not item.get("item_code"):
                continue

            canonical = harmonize_budatec_item(item)
            validated = validate_budatec_item(canonical)
            blueprint = create_budatec_item(validated)

            # -------- SUPPLIER --------
            supplier_data = split.get("supplier", {})

            if supplier_data and any(v for v in supplier_data.values()):
                process_supplier_json({"data": supplier_data})

            # -------- CUSTOMER --------
            customer_data = split.get("customer", {})

            if customer_data and any(v for v in customer_data.values()):
                process_customer_json({"data": customer_data})

            results.append({
                "row": i,
                "status": "success",
                "id": validated["productId"]
            })

        except Exception as e:
            results.append({
                "row": i,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "entity": "item",
        "total": len(rows),
        "results": results[:10]
    }
