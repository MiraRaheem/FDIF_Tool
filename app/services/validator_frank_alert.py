def validate_frank_alert(data):

    # -------- REQUIRED --------
    if data.get("eventId") is None:
        raise ValueError("eventId missing")

    if not data.get("eventType"):
        raise ValueError("eventType missing")

    if not data.get("timestamp"):
        raise ValueError("timestamp missing")

    if data.get("machineId") is None:
        raise ValueError("machineId missing")

    # -------- NORMALIZATION --------
    # convert numeric if applicable
    if data.get("currentValue") not in [None, "NA"]:
        try:
            data["currentValue"] = float(data["currentValue"])
        except:
            pass  # keep string (e.g., AL06)

    if data.get("valueThreshold") not in [None, "NA"]:
        try:
            data["valueThreshold"] = float(data["valueThreshold"])
        except:
            pass

    return data
