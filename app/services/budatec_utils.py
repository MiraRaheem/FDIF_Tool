import pandas as pd
import math


# =========================
# BASIC CLEANING
# =========================

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


# =========================
# EXCEL EXTRACTION
# =========================
def extract_rows(file):

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
    # EXTRACT HEADERS (SIMPLE)
    # -----------------------------
    headers = df_raw.iloc[header_row_idx].tolist()
    headers = headers[1:]
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

    df_data = df_data.iloc[:, 1:]
    df_data.columns = headers

    rows = df_data.to_dict(orient="records")

    # -----------------------------
    # CLEAN VALUES
    # -----------------------------
    cleaned_rows = []

    for row in rows:
        new_row = {k: clean_value(v) for k, v in row.items()}
        cleaned_rows.append(new_row)

    return cleaned_rows


def extract_items_rows(file):

    df_raw = pd.read_excel(file, header=None)

    # -----------------------------
    # 1. FIND HEADER ROW ("Column Name:")
    # -----------------------------
    header_row_idx = None

    for i, row in df_raw.iterrows():
        if str(row[0]).strip() == "Column Name:":
            header_row_idx = i
            break

    if header_row_idx is None:
        raise Exception("Column Name row not found")

    # -----------------------------
    # 2. READ TWO HEADER ROWS
    # -----------------------------
    raw_headers = df_raw.iloc[header_row_idx].tolist()         # section row
    column_names = df_raw.iloc[header_row_idx + 1].tolist()    # actual column names

    structured_headers = []
    current_section = "item"

    for i in range(len(column_names)):

        raw = str(raw_headers[i])
        col = str(column_names[i]).strip()

        # -----------------------------
        # SECTION DETECTION (CRITICAL FIX)
        # -----------------------------
        if "Item Supplier" in raw:
            current_section = "supplier"

        elif "Item Customer" in raw:
            current_section = "customer"

        elif "UOM" in raw:
            current_section = "uom"

        elif "Barcode" in raw:
            current_section = "barcode"

        elif "Reorder" in raw:
            current_section = "reorder"

        elif "Variant" in raw:
            current_section = "attribute"

        elif "Item" in raw:
            current_section = "item"
        # -----------------------------
        # ALWAYS ADD HEADER (even if empty)
        # -----------------------------
        if not col or col == "~":
            structured_headers.append(f"{current_section}__unknown_{i}")
        else:
            structured_headers.append(f"{current_section}__{col}")
            

    # -----------------------------
    # 3. FIND DATA START
    # -----------------------------
    data_start_idx = None

    for i, row in df_raw.iterrows():
        if "Start entering data below this line" in str(row[0]):
            data_start_idx = i + 1
            break

    if data_start_idx is None:
        raise Exception("Data start row not found")

    # -----------------------------
    # 4. EXTRACT DATA
    # -----------------------------
    df_data = df_raw.iloc[data_start_idx:].copy()
    df_data = df_data.dropna(how="all")
    
    # align BOTH sides the same way
    df_data = df_data.iloc[:, 1:]
    structured_headers = structured_headers[1:]
    
    # now lengths match
    df_data.columns = structured_headers
    print("DF COLS:", df_data.shape[1])
    print("HEADERS:", len(structured_headers))
    # -----------------------------
    # 5. CLEAN VALUES
    # -----------------------------
    cleaned_rows = []

    for row in rows:
        new_row = {k: clean_value(v) for k, v in row.items()}
        cleaned_rows.append(new_row)

    return cleaned_rows


# =========================
# NORMALIZATION
# =========================

def normalize_supplier(row):

    # fallback for missing name
    if not row.get("name") and row.get("supplier_name"):
        row["name"] = row["supplier_name"]

    if row.get("name"):
        row["name"] = sanitize_id(row["name"])

    return row


def normalize_customer(row):

    if row.get("name"):
        row["name"] = sanitize_id(row["name"])
        return row

    if row.get("customer_name"):
        row["name"] = sanitize_id(row["customer_name"])

    return row

def normalize_item(row):

    if row.get("item_code"):
        row["item_code"] = sanitize_id(row["item_code"])

    return row


def build_structured_headers(raw_headers):
    structured = []
    current_section = "item"

    for h in raw_headers:

        h = str(h).strip()

        # skip empty
        if not h or h == "~":
            continue

        # detect sections
        if "UOM" in h:
            current_section = "uom"
            continue
        elif "Supplier" in h:
            current_section = "supplier"
            continue
        elif "Customer" in h:
            current_section = "customer"
            continue
        elif "Tax" in h:
            current_section = "tax"
            continue
        elif "Barcode" in h:
            current_section = "barcode"
            continue

        structured.append(f"{current_section}__{h}")

    return structured


def split_item_row(row):

    item = {
        k.replace("item__", ""): v
        for k, v in row.items()
        if k.startswith("item__")
    }

    supplier = {
        k.replace("supplier__", ""): v
        for k, v in row.items()
        if k.startswith("supplier__")
    }

    customer = {
        k.replace("customer__", ""): v
        for k, v in row.items()
        if k.startswith("customer__")
    }

    return {
        "item": item,
        "supplier": supplier,
        "customer": customer
    }
