import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"
session = requests.Session()


# -----------------------------
# CACHE
# -----------------------------
STATION_CACHE = None


def load_stations():
    global STATION_CACHE

    if STATION_CACHE is None:
        STATION_CACHE = set()

        r = session.get(f"{BASE_URL}/api/Station")
        instances = r.json().get("instances", [])

        for s in instances:
            if isinstance(s, str):
                STATION_CACHE.add(s)
            elif isinstance(s, dict):
                STATION_CACHE.add(s.get("stationName"))

    return STATION_CACHE


def station_exists(station_name):
    cache = load_stations()
    return station_name in cache


# -----------------------------
# API CALLS
# -----------------------------

def create_instance(payload):
    url = f"{BASE_URL}/api/Station"
    return session.post(url, json=payload).json()


def update_instance(station_id, payload):
    url = f"{BASE_URL}/api/Station/{station_id}"
    return session.put(url, json=payload).json()


# -----------------------------
# MAIN FUNCTION
# -----------------------------

def create_or_update_station(canonical):

    station_id = f"Station_{canonical['stationId']}"

    payload = {
        "dataProperties": [
            {"property": "stationName", "value": canonical["stationName"]},
            {"property": "maxCapacity", "value": canonical["capacityHoursPerDay"]},
            {"property": "stationDescription", "value": canonical["description"]}
        ]
    }

    if station_exists(canonical["stationName"]):
        update_instance(station_id, payload)
        status = "updated"
    else:
        create_instance({
            "individualName": station_id,
            **payload,
            "objectProperties": []
        })
        status = "created"

    return {
        "status": status,
        "stationId": station_id
    }
