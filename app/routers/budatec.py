from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
import pandas as pd
import math
import json

# -----------------------------
# Services
# -----------------------------

from app.services.harmonizer_budatec import harmonize_budatec_supplier
from app.services.validator_budatec import validate_budatec_supplier
from app.services.blueprint_adapter import create_budatec_supplier

from app.services.harmonizer_budatec_customer import harmonize_budatec_customer
from app.services.validator_budatec_customer import validate_budatec_customer
from app.services.blueprint_adapter import create_budatec_customer


router = APIRouter(tags=["BUDATEC"])


# =========================================================
# UTILS
# =========================================================

def sanitize_id(value: str) -> str:
    if not value:
        return value

    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )


def clean_value(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, str):
        return v.strip().strip('"').strip("'")
    return v
# =========================================================
# EXCEL EXTRACTION (GENERIC)
# =========================================================

def extract_budatec_rows(file):

    df_raw = pd.read_excel(file, header=None)

    # -----------------------------
    # FIND HEADER ROW
    # -----------------------------
    header_row_idx = None
    for i, row in df_raw.iterrows():
        if str(row[0]).strip() == "Column Name:":
            header_row_idx = i
            break

    if header_row_idx is None:
        raise Exception("Column Name row not found")

    # -----------------------------
    # EXTRACT HEADERS (FIXED)
    # -----------------------------
    headers = df_raw.iloc[header_row_idx].tolist()
    headers = headers[1:]  # remove first column label

    # remove "~" separators
    headers = [h for h in headers if h not in [None, "~"]]

    # -----------------------------
    # FIND DATA START
    # -----------------------------
    data_start_idx = None
    for i, row in df_raw.iterrows():
        if "Start entering data below this line" in str(row[0]):
            data_start_idx = i + 1
            break

    if data_start_idx is None:
        raise Exception("Data start row not found")

    # -----------------------------
    # EXTRACT DATA
    # -----------------------------
    df_data = df_raw.iloc[data_start_idx:].copy()
    df_data = df_data.dropna(how="all")

    # drop first blank column
    df_data = df_data.iloc[:, 1:]

    # align with headers
    df_data = df_data.iloc[:, :len(headers)]
    df_data.columns = headers

    rows = df_data.to_dict(orient="records")

    # -----------------------------
    # CLEAN VALUES ONLY
    # -----------------------------
    cleaned_rows = []

    for row in rows:
        new_row = {k: clean_value(v) for k, v in row.items()}
        cleaned_rows.append(new_row)

    return cleaned_rows


# =========================================================
# ENTITY NORMALIZATION (CRITICAL FIX)
# =========================================================

def normalize_supplier_row(row):

    # generate ID if missing
    if not row.get("name") and row.get("supplier_name"):
        row["name"] = row["supplier_name"]

    if row.get("name"):
        row["name"] = sanitize_id(row["name"])

    return row


def normalize_customer_row(row):

    # PRIORITY 1: use ERP ID (name column)
    if row.get("name"):
        row["name"] = sanitize_id(row["name"])
        return row

    # PRIORITY 2: fallback ONLY if name missing
    if row.get("customer_name"):
        row["name"] = sanitize_id(row["customer_name"])

    return row

# =========================================================
# GENERIC PROCESSOR (REUSABLE PIPELINE)
# =========================================================

def process_upload(rows, entity_type):

    results = []

    for i, row in enumerate(rows):

        try:
            # -----------------------------
            # SUPPLIER FLOW
            # -----------------------------
            if entity_type == "supplier":

                row = normalize_supplier_row(row)

                canonical = harmonize_budatec_supplier(row)
                validated = validate_budatec_supplier(canonical)
                blueprint_res = create_budatec_supplier(validated)

                results.append({
                    "row": i,
                    "status": "success",
                    "supplierId": validated.get("supplierId"),
                    "blueprint": blueprint_res
                })

            # -----------------------------
            # CUSTOMER FLOW
            # -----------------------------
            elif entity_type == "customer":

                row = normalize_customer_row(row)

                canonical = harmonize_budatec_customer(row)
                validated = validate_budatec_customer(canonical)
                blueprint_res = create_budatec_customer(validated)

                results.append({
                    "row": i,
                    "status": "success",
                    "customerId": validated.get("customerId"),
                    "blueprint": blueprint_res
                })

            else:
                raise Exception(f"Unsupported entity_type: {entity_type}")

        except Exception as row_error:

            results.append({
                "row": i,
                "status": "error",
                "error": str(row_error),
                "raw": row
            })

    return results


# =========================================================
# EXCEL ENDPOINTS
# =========================================================

@router.post("/budatec/upload")
async def upload_budatec_suppliers(file: UploadFile = File(...)):

    try:
        rows = extract_budatec_rows(file.file)

        results = process_upload(rows, "supplier")

        return {
            "status": "completed",
            "entity": "supplier",
            "total_rows": len(rows),
            "processed": len(results),
            "results": results[:10]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/budatec/customer/upload")
async def upload_budatec_customers(file: UploadFile = File(...)):

    try:
        rows = extract_budatec_rows(file.file)

        results = process_upload(rows, "customer")

        return {
            "status": "completed",
            "entity": "customer",
            "total_rows": len(rows),
            "processed": len(results),
            "results": results[:10]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# JSON INGEST ENDPOINT
# =========================================================

@router.post("/budatec/{entity_type}")
def ingest_budatec(entity_type: str, body: Dict[str, Any]):

    try:
        raw = body.get("data", {})

        if isinstance(raw, str):
            raw = json.loads(raw)

        # sanitize ID early
        if raw.get("name"):
            raw["name"] = sanitize_id(raw["name"])

        # -----------------------------
        # SUPPLIER
        # -----------------------------
        if entity_type == "supplier":

            canonical = harmonize_budatec_supplier(raw)
            validated = validate_budatec_supplier(canonical)
            result = create_budatec_supplier(validated)

            return {
                "status": "success",
                "entity": "supplier",
                "canonical": canonical,
                "blueprint": result
            }

        # -----------------------------
        # CUSTOMER
        # -----------------------------
        elif entity_type == "customer":

            canonical = harmonize_budatec_customer(raw)
            validated = validate_budatec_customer(canonical)
            result = create_budatec_customer(validated)

            return {
                "status": "success",
                "entity": "customer",
                "canonical": canonical,
                "blueprint": result
            }

        # -----------------------------
        # INVALID
        # -----------------------------
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported entity_type: {entity_type}"
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
