from fastapi import HTTPException
from app.services.blueprint_adapter import instance_exists


def validate_melito_entities(data):

    machine_id = f"Machine_{data['machineId']}"
    sensor_id = data["sensorId"]

    # -----------------------------
    # 1. MACHINE
    # -----------------------------
    if not instance_exists("Machine", machine_id):
        raise HTTPException(
            status_code=400,
            detail=f"Machine {machine_id} does not exist in ontology"
        )

    # -----------------------------
    # 2. SENSOR
    # -----------------------------
    if not instance_exists("ConditionMonitoringSensor", sensor_id):
        raise HTTPException(
            status_code=400,
            detail=f"Sensor {sensor_id} does not exist in ontology"
        )

    # -----------------------------
    # 3. PARAMETERS
    # -----------------------------
    for r in data["readings"]:
        param = r["type"]

        if not instance_exists("PhysicalParameter", param):
            raise HTTPException(
                status_code=400,
                detail=f"Parameter {param} does not exist in ontology"
            )

    return True
