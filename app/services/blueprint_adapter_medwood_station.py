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

        r = session.get(
            f"{BASE_URL}/api/Station",
            timeout=60
        )

        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to load stations. "
                f"Status={r.status_code}, Response={r.text}"
            )

        data = safe_json(r)
        instances = data.get("instances", [])

        for station in instances:

            # API may return instance names directly
            if isinstance(station, str):
                if station:
                    STATION_CACHE.add(station)

            # API may return dictionaries
            elif isinstance(station, dict):

                individual_name = station.get("individualName")

                if individual_name:
                    STATION_CACHE.add(individual_name)

                station_id = station.get("stationID")

                if station_id:
                    STATION_CACHE.add(
                        f"Station_{normalize_id(station_id)}"
                    )

    return STATION_CACHE


def station_exists(station_id):
    return station_id in load_stations()


def add_to_cache(station_id):
    global STATION_CACHE

    if STATION_CACHE is None:
        STATION_CACHE = set()

    STATION_CACHE.add(station_id)
# -----------------------------
# API CALLS (WITH DEBUG)
# -----------------------------
def create_instance(payload):

    url = f"{BASE_URL}/api/Station"

    try:
        r = session.post(
            url,
            json=payload,
            timeout=60
        )

        print("CREATE STATION")
        print("URL:", url)
        print("Payload:", payload)
        print("Status:", r.status_code)
        print("Response:", r.text)

        if r.status_code not in [200, 201]:
            raise RuntimeError(
                f"Failed to create station. "
                f"Status={r.status_code}, "
                f"Response={r.text}"
            )

        result = safe_json(r)

        # Narrate can return HTTP 200 for an application-level error
        if isinstance(result, dict):
            if result.get("status") == "error":
                raise RuntimeError(
                    f"Narrate rejected station creation: "
                    f"{result.get('message', result)}"
                )

        return result

    except requests.RequestException as e:
        raise RuntimeError(
            f"Create station request failed: {e}"
        )

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

