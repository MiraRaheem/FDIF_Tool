def harmonize_events(raw):

    return {
        "eventId": raw["eventId"],
        "machineId": raw["machineId"],
        "timestamp": raw["timestamp"],
        "sensorId": raw["virtualSensorId"],
        "eventType": raw["eventType"],
        "status": raw["status"],
        "severity": raw["error"]["severity"],
        "description": f"{raw['error']['code']} - {raw['error']['description']}",
        "triggerReadings": raw["triggerReadings"]
    }
