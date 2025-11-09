from typing import Dict, Any, Tuple

ALLOWED_UNITS = {"C", "F", "K"}

def convert_to_celsius(value: float, unit: str) -> float:
    if unit == "C":
        return value
    if unit == "K":
        return value - 273.15
    if unit == "F":
        return (value - 32.0) * 5.0/9.0
    # unknown -> return as-is
    return value

def validate_and_enrich(harmonized: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    Step 4: Validation Engine (structure + semantics)
    - required fields
    - unit in {C,F,K}
    - compute temperature_celsius
    """
    dev = harmonized.get("deviceId")
    t = harmonized.get("temperature")
    u = harmonized.get("temperature_unit")
    ts = harmonized.get("timestamp")

    if not dev:
        return False, harmonized, "deviceId missing"
    if t is None:
        return False, harmonized, "temperature missing or not numeric"
    if not u or u not in ALLOWED_UNITS:
        return False, harmonized, f"temperature_unit must be one of {sorted(ALLOWED_UNITS)}"
    if not ts:
        return False, harmonized, "timestamp missing"

    t_c = round(convert_to_celsius(float(t), u), 2)
    enriched = dict(harmonized)
    enriched["temperature_celsius"] = t_c
    # normalize unit to 'C' for downstream (optional)
    return True, enriched, ""
