from typing import Dict, Any

def to_float(v):
    try:
        return float(v)
    except Exception:
        return None

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

def normalize_id(value):
    if value is None:
        return None
    return str(value).strip()


def harmonize_medwood_station(row):

    name = row.get("CENTROS DE TRABAJO")

    return {
        "stationId": normalize_id(name),
        "stationName": name,
        "capacityHoursPerDay": row.get("Capacidad horas día"),
        "machineCount": row.get("Cantidad"),
        "description": f"Machines: {row.get('Cantidad')}"
    }
