from typing import Dict, Any

def to_float(v):
    try:
        return float(v)
    except Exception:
        return None

def harmonize_raw_iot(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Schema Harmonizer
    - Rename TMP -> temperature
    - Ensure numeric type
    - Keep unit (C/F/K) as provided
    - Normalize location structure
    """
    temperature = raw.get("temperature")
    if temperature is None and "TMP" in raw:
        temperature = to_float(raw.get("TMP"))

    unit = raw.get("temperature_unit") or raw.get("unit")
    location = raw.get("location") or raw.get("meta") or {}
    site = location.get("site") or location.get("locationName")
    line = location.get("line")

    return {
        "deviceId": raw.get("deviceId"),
        "temperature": to_float(temperature),
        "temperature_unit": unit,
        "timestamp": raw.get("timestamp"),
        "status": raw.get("status"),
        "location": {
            "site": site,
            "line": line,
        },
    }
