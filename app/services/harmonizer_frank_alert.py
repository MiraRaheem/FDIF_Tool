def harmonize_frank_alert(raw):

    return {

        # -------- CORE --------
        "eventId": raw.get("eventId"),
        "eventType": raw.get("eventType"),
        "timestamp": raw.get("time"),
        "timestampHR": raw.get("timeHR"),

        # -------- META --------
        "sensorType": raw.get("sensorType"),
        "descriptionValue": raw.get("descriptionValue"),
        "alert": raw.get("alert"),

        # -------- DATA --------
        "valueThreshold": raw.get("data", {}).get("valueThreshold"),
        "currentValue": raw.get("data", {}).get("currentValue"),
        "units": raw.get("data", {}).get("units"),
        "machineId": raw.get("data", {}).get("machineId"),
    }
