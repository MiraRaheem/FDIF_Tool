from typing import Dict, Any

# You can later map these to your ontology IRIs (j.0:*). For demo we use "ex".
JSONLD_CONTEXT = {
    "ex": "http://example.org/ontology#",
    "deviceId": "ex:Machine/id",
    "temperature_celsius": "ex:SensorReading/value",
    "timestamp": "ex:Observation/time",
    "location": "ex:Machine/locatedAt"
}

def to_jsonld_observation(validated: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 5: Semantic Tagger (JSON-LD)
    """
    return {
        "@context": JSONLD_CONTEXT,
        "@type": "ex:Observation",
        "deviceId": validated.get("deviceId"),
        "temperature_celsius": validated.get("temperature_celsius"),
        "timestamp": validated.get("timestamp"),
        "status": validated.get("status"),
        "location": validated.get("location"),
    }
