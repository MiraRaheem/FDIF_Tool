import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"
session = requests.Session()


# -----------------------------
# HELPERS
# -----------------------------
def normalize_id(value):
    if value is None:
        return None
    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {"error": "Invalid JSON response", "status_code": response.status_code}


# -----------------------------
# CACHE
# -----------------------------
STATION_CACHE = None


def load_stations():
    global STATION_CACHE

    if STATION_CACHE is None:
        STATION_CACHE = set()

        r = session.get(f"{BASE_URL}/api/Station")
        data = safe_json(r)

        instances = data.get("instances", [])

        for s in instances:
            if isinstance(s, str) and s:
                STATION_CACHE.add(s)

    return STATION_CACHE


def station_exists(station_id):
    cache = load_stations()
    return station_id in cache


def add_to_cache(station_id):
    global STATION_CACHE
    if STATION_CACHE is not None:
        STATION_CACHE.add(station_id)


# -----------------------------
# API CALLS (WITH DEBUG)
# -----------------------------
def create_instance(payload):
    url = f"{BASE_URL}/api/Station"

    try:
        r = session.post(url, json=payload, timeout=60)

        print("CREATE STATION")
        print("URL:", url)
        print("Status:", r.status_code)
        print("Response:", r.text)

        if r.status_code not in [200, 201]:
            print("❌ CREATE FAILED:", r.status_code, r.text)
            return None

        return safe_json(r)

    except requests.RequestException as e:
        print("❌ CREATE REQUEST FAILED:", e)
        return None

def update_instance(station_id, payload):
    url = f"{BASE_URL}/api/Station/{station_id}"

    try:
        r = session.put(url, json=payload, timeout=60)

        print("UPDATE STATION")
        print("URL:", url)
        print("Status:", r.status_code)
        print("Response:", r.text)

        if r.status_code not in [200, 201]:
            print("❌ UPDATE FAILED:", r.status_code, r.text)
            return None

        return safe_json(r)

    except requests.RequestException as e:
        print("❌ UPDATE REQUEST FAILED:", e)
        return None

def create_or_update_station(canonical):

    clean_id = normalize_id(canonical["stationId"])
    station_id = f"Station_{clean_id}"

    factory_individual = "MEDWOOD_Factory"

    # -----------------------------
    # STATION PAYLOAD
    # -----------------------------
    payload = {
        "dataProperties": [
            {
                "property": "stationID",
                "value": canonical["stationId"]
            },
            {
                "property": "stationName",
                "value": canonical["stationName"]
            },
            {
                "property": "maxCapacity",
                "value": canonical["capacityHoursPerDay"]
            },
            {
                "property": "stationDescription",
                "value": canonical["description"]
            }
        ],
        "objectProperties": [
            {
                "property": "stationLocatedInFactory",
                "value": factory_individual
            }
        ]
    }

    # -----------------------------
    # CREATE OR UPDATE STATION
    # -----------------------------

    if station_exists(station_id):

        result = update_instance(
            station_id,
            payload
        )

        if result is None:
            raise RuntimeError(
                f"Failed to update station: {station_id}"
            )

        status = "updated"

    else:

        result = create_instance({
            "individualName": station_id,
            "className": "Station",
            **payload
        })

        if result is None:
            raise RuntimeError(
                f"Failed to create station: {station_id}"
            )

        status = "created"

        add_to_cache(station_id)

    # -----------------------------
    # UPDATE FACTORY
    # -----------------------------
    #
    # ONLY do this after the station
    # operation succeeded.
    #

    factory_payload = {
        "objectProperties": [
            {
                "property": "factoryHasStation",
                "value": station_id
            }
        ]
    }

    try:

        factory_response = session.put(
            f"{BASE_URL}/api/Factory/{factory_individual}",
            json=factory_payload,
            timeout=60
        )

        print("UPDATE FACTORY")
        print("Status:", factory_response.status_code)
        print("Response:", factory_response.text)

        if factory_response.status_code not in [200, 201]:
            raise RuntimeError(
                f"Failed to update factory. "
                f"Status={factory_response.status_code}, "
                f"Response={factory_response.text}"
            )

        factory_result = safe_json(factory_response)

    except requests.RequestException as e:

        raise RuntimeError(
            f"Factory update request failed: {e}"
        )

    return {
        "status": status,
        "stationId": station_id,
        "station_response": result,
        "factory_response": factory_result
    }

