from app.services.blueprint_adapter import create_instance, update_instance

def link_bidirectional(class_a, id_a, prop_a_to_b,
                       class_b, id_b, prop_b_to_a):

    # A → B
    update_instance(class_a, id_a, {
        "objectProperties": [
            {"property": prop_a_to_b, "value": id_b}
        ]
    })

    # B → A
    update_instance(class_b, id_b, {
        "objectProperties": [
            {"property": prop_b_to_a, "value": id_a}
        ]
    })
def map_to_ontology(data):

    created = []

    machine_id = f"Machine_{data['machineId']}"
    sensor_id = data["sensorId"]
    timestamp = data["timestamp"]

    # -----------------------------
    # 1. CREATE MACHINE
    # -----------------------------
    create_instance("Machine", {
        "individualName": machine_id,
        "dataProperties": [
            {"property": "hasMachineID", "value": data["machineId"]}
        ]
    })

    # -----------------------------
    # 2. CREATE SENSOR
    # -----------------------------
    create_instance("ConditionMonitoringSensor", {
        "individualName": sensor_id,
        "dataProperties": [
            {"property": "sensorID", "value": sensor_id},
            {"property": "sensorStatus", "value": "Active"},
            {"property": "sensorType", "value": "ProductionPerformanceSensor"}
        ]
    })

    # -----------------------------
    # 3. LINK SENSOR ↔ MACHINE
    # -----------------------------
    link_bidirectional(
        "ConditionMonitoringSensor", sensor_id, "isDeployedOnMachine",
        "Machine", machine_id, "monitoredByConditionSensor"
    )

    # -----------------------------
    # 4. LOOP READINGS → OBSERVATIONS
    # -----------------------------
    for r in data["readings"]:

        # Skip invalid values (optional but recommended)
        if r["value"] is None:
            continue

        param_name = r["type"]
        obs_id = f"OBS_{timestamp}_{param_name}_{data['machineId']}"

        # -----------------------------
        # 4.1 CREATE PARAMETER
        # -----------------------------
        create_instance("PhysicalParameter", {
            "individualName": param_name,
            "dataProperties": [
                {"property": "parameterName", "value": param_name},
                {"property": "unitOfMeasurement", "value": r["unit"]}
            ]
        })

        # -----------------------------
        # 4.2 CREATE OBSERVATION
        # -----------------------------
        create_instance("ConditionSensorObservation", {
            "individualName": obs_id,
            "dataProperties": [
                {"property": "observationID", "value": obs_id},
                {"property": "observedValue", "value": r["value"]},
                {"property": "observationTimestamp", "value": timestamp},
                {"property": "unitOfMeasureSensor", "value": r["unit"]}
            ]
        })

        # -----------------------------
        # 4.3 LINK OBSERVATION ↔ SENSOR
        # -----------------------------
        link_bidirectional(
            "ConditionSensorObservation", obs_id, "conditionObservedBy",
            "ConditionMonitoringSensor", sensor_id, "observesCondition"
        )

        # -----------------------------
        # 4.4 LINK SENSOR ↔ PARAMETER
        # -----------------------------
        link_bidirectional(
            "ConditionMonitoringSensor", sensor_id, "monitorsPhysicalParam",
            "PhysicalParameter", param_name, "physicalParamMonitoredBy"
        )

        created.append(obs_id)

    return created
