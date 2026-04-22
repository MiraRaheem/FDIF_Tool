from app.services.blueprint_adapter import create_instance, update_instance, instance_exists


def link_bidirectional(class_a, id_a, prop_a_to_b,
                       class_b, id_b, prop_b_to_a):

    update_instance(class_a, id_a, {
        "objectProperties": [{"property": prop_a_to_b, "value": id_b}]
    })

    update_instance(class_b, id_b, {
        "objectProperties": [{"property": prop_b_to_a, "value": id_a}]
    })


def map_events(data):

    machine_id = f"Machine_{data['machineId']}"
    sensor_id = data["sensorId"]
    event_id = data["eventId"]
    timestamp = data["timestamp"]

    created_observations = []

    # -----------------------------
    # 1. CREATE TRIGGER OBSERVATIONS
    # -----------------------------
    for r in data["triggerReadings"]:

        param = r["type"]
        obs_id = f"OBS_EVT_{timestamp}_{param}_{data['machineId']}"

        if not instance_exists("ConditionSensorObservation", obs_id):

            create_instance("ConditionSensorObservation", {
                "individualName": obs_id,
                "dataProperties": [
                    {"property": "observationID", "value": obs_id},
                    {"property": "observedValue", "value": r["value"]},
                    {"property": "observationTimestamp", "value": timestamp},
                    {"property": "unitOfMeasureSensor", "value": r["unit"]}
                ]
            })

        # Observation ↔ Sensor
        link_bidirectional(
            "ConditionSensorObservation", obs_id, "conditionObservedBy",
            "ConditionMonitoringSensor", sensor_id, "observesCondition"
        )

        # Sensor ↔ Parameter
        link_bidirectional(
            "ConditionMonitoringSensor", sensor_id, "monitorsPhysicalParam",
            "PhysicalParameter", param, "physicalParamMonitoredBy"
        )

        created_observations.append(obs_id)

    # -----------------------------
    # 2. CREATE EVENT
    # -----------------------------
    if not instance_exists("MaintenanceEvent", event_id):

        create_instance("MaintenanceEvent", {
            "individualName": event_id,
            "dataProperties": [
                {"property": "eventID", "value": event_id},
                {"property": "eventTimestamp", "value": timestamp},
                {"property": "eventStatus", "value": data["status"]},
                {"property": "eventSeverity", "value": data["severity"]},
                {"property": "eventDescription", "value": data["description"]}
            ]
        })

    # -----------------------------
    # 3. LINK EVENT ↔ MACHINE
    # -----------------------------
    link_bidirectional(
        "MaintenanceEvent", event_id, "affectsMachine",
        "Machine", machine_id, "machineAffectedByEvent"
    )

    # -----------------------------
    # 4. LINK OBSERVATIONS ↔ EVENT (CRITICAL)
    # -----------------------------
    for obs_id in created_observations:

        link_bidirectional(
            "ConditionSensorObservation", obs_id, "triggersMaintenanceEvent",
            "MaintenanceEvent", event_id, "maintenanceEventTriggeredBy"
        )

    return {
        "eventId": event_id,
        "observations": created_observations
    }
