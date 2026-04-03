from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from fastapi import UploadFile, File
import pandas as pd

import math
from app.services.harmonizer_budatec import harmonize_budatec_supplier
from app.services.validator_budatec import validate_budatec_supplier
from app.services.blueprint_adapter import create_budatec_supplier

router = APIRouter(tags=["BUDATEC"])

import pandas as pd

import pandas as pd
import math


def extract_budatec_rows(file):

    # ---- 1. Read raw file ----
    df_raw = pd.read_excel(file, header=None)

    # ---- 2. Find "Column Name:" row ----
    header_row_idx = None
    for i, row in df_raw.iterrows():
        if str(row[0]).strip() == "Column Name:":
            header_row_idx = i
            break

    if header_row_idx is None:
        raise Exception("Could not find 'Column Name:' row")

    # ---- 3. Extract headers ----
    headers = df_raw.iloc[header_row_idx].tolist()

    # remove first cell ("Column Name:")
    headers = headers[1:]

    # remove junk columns (~ etc.)
    headers = [h for h in headers if h not in [None, "~"]]

    # ---- 4. Find data start ----
    data_start_idx = None
    for i, row in df_raw.iterrows():
        if "Start entering data below this line" in str(row[0]):
            data_start_idx = i + 1
            break

    if data_start_idx is None:
        raise Exception("Could not find data start")

    # ---- 5. Extract data ----
    df_data = df_raw.iloc[data_start_idx:].copy()

    # drop empty rows
    df_data = df_data.dropna(how="all")

    # ---- 6. DROP ONLY FIRST COLUMN (blank one) ----
    df_data = df_data.iloc[:, 1:]

    # trim to header length (avoid overflow columns)
    df_data = df_data.iloc[:, :len(headers)]

    df_data.columns = headers

    # ---- 7. Convert to dict ----
    rows = df_data.to_dict(orient="records")

    # ---- 8. CLEAN rows ----
    cleaned_rows = []

    for row in rows:

        new_row = {}

        for k, v in row.items():

            # fix NaN
            if isinstance(v, float) and math.isnan(v):
                v = None

            # remove quotes
            if isinstance(v, str):
                v = v.strip().strip('"')

            new_row[k] = v

        # ---- 9. FIX ID ISSUE (THIS IS THE REAL FIX) ----
        # If name is missing but supplier_name exists → use it
        if not new_row.get("name") and new_row.get("supplier_name"):
            new_row["name"] = new_row["supplier_name"]

        cleaned_rows.append(new_row)

    return cleaned_rows
    
@router.post("/budatec/upload")
async def upload_budatec_suppliers(file: UploadFile = File(...)):

    try:
        # ---- 1. Read Excel ----
        rows = extract_budatec_rows(file.file)
        # 🔥 FIX NaN
        def clean_nan(row):
            return {
                k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in row.items()
            }
        rows = [clean_nan(r) for r in rows]
        results = []

        # ---- 2. Process each row ----
        for i, row in enumerate(rows):
            
            try:
                canonical = harmonize_budatec_supplier(row)
                validated = validate_budatec_supplier(canonical)

                blueprint_res = create_budatec_supplier(validated)

                results.append({
                    "row": i,
                    "status": "success",
                    "supplierId": validated.get("supplierId"),
                    "blueprint": blueprint_res
                })

            except Exception as row_error:

                results.append({
                    "row": i,
                    "status": "error",
                    "error": str(row_error),
                    "raw": row
                })
            print(f"\n--- ROW {i} ---")
            print("RAW:", row)
            print("CANONICAL:", canonical)

        return {
            "status": "completed",
            "total_rows": len(rows),
            "processed": len(results),
            "results": results[:10]  # preview only
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/budatec/{entity_type}")
def ingest_budatec(entity_type: str, body: Dict[str, Any]):

    try:
        raw = body.get("data", {})   # ✅ FIX HERE
        
        # 🔥 FORCE DICT
        if isinstance(raw, str):
            import json
            raw = json.loads(raw)

        if entity_type == "supplier":
            canonical = harmonize_budatec_supplier(raw)
            validated = validate_budatec_supplier(canonical)
            print("\n--- DEBUG ---")
            print("RAW TYPE:", type(raw))
            print("CANONICAL TYPE:", type(canonical))
            print("METADATA TYPE:", type(canonical.get("metadata")))
            print("POLICY TYPE:", type(canonical.get("operationalPolicy")))
            print("CANONICAL:", canonical)
            result = create_budatec_supplier(validated)
            

        else:
            raise HTTPException(400, f"Unsupported entity_type: {entity_type}")

        return {
            "status": "success",
            "canonical": canonical,
            "blueprint": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
