from typing import Dict, Any, Tuple
import math

def validate_supplier(canonical):

    if not canonical.get("supplierId"):
        raise ValueError("supplierId is required")

    if not canonical.get("supplierName"):
        raise ValueError("supplierName is required")

    if not canonical.get("country"):
        raise ValueError("country is required")

    location = canonical.get("location", {})

    if not location.get("city"):
        raise ValueError("city is required")

    return canonical


def validate_supplier_performance(data):

    if not data.get("supplierId"):
        raise ValueError("supplierId is required")

    return data


def validate_station(data):
    if not data.get("stationName"):
        raise ValueError("Missing station name/source ID from CENTROS DE TRABAJO")

    if not data.get("stationId"):
        raise ValueError("Station ID is empty after normalization")

    capacity = data.get("maxCapacity")
    if capacity is None:
        raise ValueError("Missing machine count for ontology maxCapacity")
    try:
        capacity = float(capacity)
    except (TypeError, ValueError):
        raise ValueError("Machine count for maxCapacity must be numeric")
    if not math.isfinite(capacity) or capacity <= 0 or not capacity.is_integer():
        raise ValueError("Machine count for maxCapacity must be a positive whole number")

    hours = data.get("capacityHoursPerDay")
    if hours is not None:
        try:
            hours = float(hours)
        except (TypeError, ValueError):
            raise ValueError("Capacidad horas día must be numeric when provided")
        if not math.isfinite(hours) or hours < 0:
            raise ValueError("Capacidad horas día must be a non-negative number when provided")

    return data

def validate_material(data):

    if not data.get("materialId"):
        raise ValueError("materialId is required")

    if not data.get("materialName"):
        raise ValueError("materialName is required")

    return data

def validate_product_type(data):

    if not data.get("productId"):
        raise ValueError("Missing productId")

    if not data.get("productName"):
        raise ValueError("Missing productName")

    return data
