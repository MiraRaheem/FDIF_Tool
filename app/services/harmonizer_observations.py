def harmonize_observations(raw):

    return {
        "machineId": raw["machineId"],
        "timestamp": raw["timestamp"],
        "sensorId": raw["virtualSensorId"],

        "readings": raw["readings"]  # already structured well
    }
