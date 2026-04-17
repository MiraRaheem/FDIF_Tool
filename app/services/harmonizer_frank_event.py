def harmonize_frank_event(raw):

    return {

        # -------- CORE --------
        "eventType": raw.get("eventType"),
        "timestamp": raw.get("time"),
        "timestampHR": raw.get("timeHR"),

        # -------- MACHINE --------
        "machineId": raw.get("machineId"),

        # -------- SENSOR DATA --------
        "storageTemperature": raw.get("storageTemperature"),
        "storageHumidity": raw.get("storageHumidity"),
        "averagePowerConsumption": raw.get("averagePowerConsumption"),
        "compressedAirInput": raw.get("compressedAirInput"),
        "noiseChillerLevel": raw.get("noiseChillerLevel"),
        "operatingTemperature": raw.get("operatingTemperature"),
        "powerPeakConsumption": raw.get("powerPeakConsumption"),

        # -------- STATUS --------
        "machineError": raw.get("machineError"),
        "nozzleOperationTime": raw.get("nozzleOperationTime"),
    }

def harmonize_frank_argon(raw):
    return {
        "eventType": raw.get("eventType"),
        "timestamp": raw.get("time"),
        "timestampHR": raw.get("timeHR"),

        "register1": raw.get("register1"),
        "register2": raw.get("register2"),
        "register3": raw.get("register3"),
    }
