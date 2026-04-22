from fastapi import HTTPException
from app.services.blueprint_adapter import instance_exists


def validate_events(data):

    machine_id = f"Machine_{data['machineId']}"
    sensor_id = data["sensorId"]

    if not instance_exists("Machine", machine_id):
        raise HTTPException(400, f"Machine {machine_id} does not exist")

    if not instance_exists("ConditionMonitoringSensor", sensor_id):
        raise HTTPException(400, f"Sensor {sensor_id} does not exist")

    for r in data["triggerReadings"]:
        if not instance_exists("PhysicalParameter", r["type"]):
            raise HTTPException(
                400, f"Parameter {r['type']} does not exist"
            )
