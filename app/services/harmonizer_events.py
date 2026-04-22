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

def harmonize_argon_prediction(raw):

    prediction = raw["prediction"]

    description = (
        f"Predicted {prediction['target']} in "
        f"{prediction['predictedTimeToDepletion']} {prediction['unit']} "
        f"using {prediction['method']}"
    )

    return {
        "eventId": raw["eventId"],
        "machineId": raw["machineId"],
        "timestamp": raw["timestamp"],
        "sensorId": raw["virtualSensorId"],
        "severity": raw["severity"],
        "description": description,
        "basedOn": raw["basedOn"]
    }
