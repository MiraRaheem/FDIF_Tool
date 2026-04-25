import json
from app.services.blueprint_adapter import create_instance, update_instance


# =========================
# LOAD FILES
# =========================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bootstrap_ontology():

    machines = load_json("Machine.json")
    sensors = load_json("Sensor.json")
    parameters = load_json("Physical Parameters.json")

    results = {
        "sensors_created": 0,
        "parameters_created": 0,
        "machines_created": 0,
        "relationships_updated": 0
    }

    # =========================
    # 1. CREATE SENSORS
    # =========================
    for sensor in sensors:

        payload = {
            "individualName": sensor["individualName"],
            "dataProperties": sensor.get("dataProperties", []),
            "objectProperties": []  # ⚠️ skip relations first
        }

        res = create_instance(sensor["className"], payload)

        if res.get("status") == "success":
            results["sensors_created"] += 1

    # =========================
    # 2. CREATE PARAMETERS
    # =========================
    for param in parameters:

        payload = {
            "individualName": param["individualName"],
            "dataProperties": param.get("dataProperties", []),
            "objectProperties": []  # relations later
        }

        res = create_instance(param["className"], payload)

        if res.get("status") == "success":
            results["parameters_created"] += 1

    # =========================
    # 3. CREATE MACHINES
    # =========================
    for machine in machines:

        payload = {
            "individualName": machine["individualName"],
            "dataProperties": machine.get("dataProperties", []),
            "objectProperties": []  # relations later
        }

        res = create_instance(machine["className"], payload)

        if res.get("status") == "success":
            results["machines_created"] += 1

    # =========================
    # 4. UPDATE RELATIONSHIPS
    # =========================

    # ---- Machines → Sensors ----
    for machine in machines:

        update_instance(
            "Machine",
            machine["individualName"],
            {
                "objectProperties": machine.get("objectProperties", [])
            }
        )
        results["relationships_updated"] += 1

    # ---- Sensors → Machines ----
    for sensor in sensors:

        update_instance(
            "ConditionMonitoringSensor",
            sensor["individualName"],
            {
                "objectProperties": sensor.get("objectProperties", [])
            }
        )
        results["relationships_updated"] += 1

    # ---- Parameters → Sensors ----
    for param in parameters:

        update_instance(
            "PhysicalParameter",
            param["individualName"],
            {
                "objectProperties": param.get("objectProperties", [])
            }
        )
        results["relationships_updated"] += 1

    return results
