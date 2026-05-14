from typing import Dict, Any

def to_float(v):
    try:
        return float(v)
    except Exception:
        return None

def normalize_id(value):
    if value is None:
        return None
    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )

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

    return {
        "stationId": normalize_id(name),
        "stationName": name,
        "capacityHoursPerDay": row.get("Capacidad horas día"),
        "machineCount": row.get("Cantidad"),
        "stationLocatedInFactory":row.get("stationLocatedInFactory"),
        "description": f"Machines: {row.get('Cantidad')}"
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
