from app.services.blueprint_adapter import update_instance, create_instance, instance_exists


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
    # 1. LINK SENSOR ↔ MACHINE
    # (NO CREATION — assumed existing)
    # -----------------------------
    link_bidirectional(
        "ConditionMonitoringSensor", sensor_id, "isDeployedOnMachine",
        "Machine", machine_id, "monitoredByConditionSensor"
    )

    # -----------------------------
    # 2. LOOP READINGS → OBSERVATIONS
    # -----------------------------
    for r in data["readings"]:

        # Skip invalid values
        if r["value"] is None:
            continue

        param_name = r["type"]
        obs_id = f"OBS_{timestamp}_{param_name}_{data['machineId']}"

        # -----------------------------
        # 2.1 DEDUP OBSERVATION
        # -----------------------------
        if instance_exists("ConditionSensorObservation", obs_id):
            continue

        # -----------------------------
        # 2.2 CREATE OBSERVATION ONLY
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
        # 2.3 LINK OBSERVATION ↔ SENSOR
        # -----------------------------
        link_bidirectional(
            "ConditionSensorObservation", obs_id, "conditionObservedBy",
            "ConditionMonitoringSensor", sensor_id, "observesCondition"
        )

        # -----------------------------
        # 2.4 LINK SENSOR ↔ PARAMETER
        # (NO CREATION — assumed existing)
        # -----------------------------
        link_bidirectional(
            "ConditionMonitoringSensor", sensor_id, "monitorsPhysicalParam",
            "PhysicalParameter", param_name, "physicalParamMonitoredBy"
        )

        created.append(obs_id)

    return created
