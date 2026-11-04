from typing import Dict, Any
import pandas as pd
import re

def to_float(v):
    try:
        return float(v)
    except Exception:
        return None

def normalize_id(value):

    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    # Replace every character that is unsafe for an RDF individual
    # with an underscore.
    value = re.sub(r'[^A-Za-z0-9_-]+', '_', value)

    # Remove duplicate underscores
    value = re.sub(r'_+', '_', value)

    # Remove underscores from beginning/end
    value = value.strip('_')

    return value
    
def harmonize_medwood_supplier(row):

    return {
        "supplierId": row.get("Cuenta de Cliente"),
        "supplierName": row.get("Razón Social"),
        "country": row.get("País"),
        "location": {
            "address": row.get("Calle"),
            "postalCode": row.get("Código Postal"),
            "city": row.get("Localidad")
        }
    }


def harmonize_supplier_performance(row):

    return {
        "supplierId": str(row.get("Cuenta del proveedor")),
        "supplierName": row.get("Nombre"),
        "totalDeliveries": row.get("Entregas"),
        "delayedDeliveries": row.get("Retrasos"),
        "delayPercentage": row.get("Porcentaje de Retraso"),
        "currentEvaluation": row.get("Evaluación"),
        "previousEvaluation": row.get("Evaluación actual")
    }


def harmonize_medwood_station(row):

    name = row.get("CENTROS DE TRABAJO")

    if pd.isna(name):
        name = None
    else:
        name = str(name).strip()

    def station_number(value):
        if value is None or pd.isna(value):
            return None
        if isinstance(value, str):
            value = value.strip().replace(" ", "")
            if "," in value and "." not in value:
                value = value.replace(",", ".")
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    quantity = station_number(row.get("Cantidad"))
    capacity_hours_per_day = station_number(row.get("Capacidad horas día"))
    source_station_id = name

    return {
        "stationId": normalize_id(name),
        "sourceStationId": source_station_id,
        "stationName": name,
        # The ontology defines maxCapacity as a number of simultaneous
        # processes or machines, so map the machine count rather than hours/day.
        "maxCapacity": quantity,
        "capacityHoursPerDay": capacity_hours_per_day,
        "machineCount": quantity,
        "stationLocatedInFactory": row.get("stationLocatedInFactory"),
        "description": "; ".join(part for part in (
            f"Machines: {quantity:g}" if quantity is not None else None,
            f"Capacity hours per day: {capacity_hours_per_day:g}" if capacity_hours_per_day is not None else None,
        ) if part) or None,
    }

def harmonize_medwood_material(row):

    return {

        "materialId": str(
            row.get("materialId") or row.get("Material ID")
        ).strip(),

        "materialName":
            row.get("materialName")
            or row.get("Material Name"),

        "materialType":
            row.get("materialType")
            or row.get("Tipo de material"),

        "materialWeight":
            row.get("materialWeight")
            or row.get("Net Weight"),

        "materialFamily":
            row.get("materialFamily"),

        "materialSubfamily":
            row.get("materialSubfamily"),

        "supplierId": str(
            row.get("supplierId")
            or row.get("Supplier")
        ).strip()
    }

def clean_price(value):

    if value is None:
        return 0

    value = (
        str(value)
        .replace("€", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return float(value)

    except:
        return 0


def harmonize_component(row):

    return {
        "componentID": str(row.get("componentID")).strip(),
        "componentName": str(row.get("componentName")).strip(),
        "hasUnitCostEuro": clean_price(row.get("hasUnitCostEuro")),
        "componentWeight": float(row.get("componentWeight", 0))
    }

def harmonize_medwood_product_type(row):

    return {
        "productId": row.get("Artículo/Recurso"),
        "productName": row.get("Descripción"),
        "productFamily": row.get("TIPO"),
        "productCost": to_float(
            str(row.get("Precio de coste total por unidad", ""))
            .replace("€", "")
            .replace(",", ".")
            .strip()
        ),
        "productPrice": to_float(
            str(row.get("Precio de ventas total por unidad", ""))
            .replace("€", "")
            .replace(",", ".")
            .strip()
        ),
        "productWeight": to_float(
            row.get("Peso neto por unidad")
        )
    }
def harmonize_bom(df):

    first_row = df.iloc[0]

    return {
        "bomId": str(first_row["Artículo/Recurso"]).strip(),
        "productName": first_row["Descripción"],
        "version": "v1",
        "note": "Imported from Medwood ERP"
    }
