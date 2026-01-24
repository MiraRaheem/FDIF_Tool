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

# app/services/semantics.py
from typing import Dict, Any

def tag_work_order(canonical: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic tagging for Work Orders.
    SAFE version:
    - Uses ONLY Amal's Blueprint namespace (j.0)
    - Uses CFX only for value semantics
    - Does NOT redefine ontology structure
    """

    wo = canonical["workOrder"]
    product = canonical.get("product", {})
    bom_items = canonical.get("billOfMaterials", {}).get("items", [])

    work_order_id = wo["id"]

    tagged = {
        "@context": {
            "j.0": "http://www.semanticweb.org/amal.elgammal/ontologies/2025/3/untitled-ontology-31#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "cfx": "http://www.ipc.org/CFX#",
            "fdif": "http://fdif.eu/ontology#",

            "id": "@id",
            "type": "@type"
        },

        "@id": f"fdif:WorkOrder/{work_order_id}",
        "@type": "j.0:WorkOrder",

        # value semantics (safe)
        "j.0:hasStatus": f"cfx:{wo['status']}",
        "j.0:requestedQuantity": wo["requestedQuantity"]
    }

    # product relation (ONLY if product exists)
    if "id" in product:
        tagged["j.0:producesProduct"] = f"fdif:Product/{product['id']}"

    # BOM materials
    if bom_items:
        tagged["j.0:requiresMaterial"] = [
            f"fdif:Material/{item['materialId']}"
            for item in bom_items
            if "materialId" in item
        ]

    return tagged
