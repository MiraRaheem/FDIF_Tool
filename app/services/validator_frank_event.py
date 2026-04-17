def validate_frank_event(data):

    # -------- REQUIRED --------
    if not data.get("eventType"):
        raise ValueError("eventType missing")

    if not data.get("timestamp"):
        raise ValueError("timestamp missing")

    if data.get("machineId") is None:
        raise ValueError("machineId missing")

    # -------- NUMERIC --------
    numeric_fields = [
        "storageTemperature",
        "storageHumidity",
        "averagePowerConsumption",
        "compressedAirInput",
        "noiseChillerLevel",
        "operatingTemperature",
        "powerPeakConsumption",
        "nozzleOperationTime"
    ]

    for field in numeric_fields:
        if data.get(field) is not None:
            data[field] = float(data[field])

    return data


def validate_frank_argon(data):

    if not data.get("eventType"):
        raise ValueError("eventType missing")

    if data.get("timestamp") is None:
        raise ValueError("timestamp missing")

    return data
