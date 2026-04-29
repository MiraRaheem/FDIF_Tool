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
    r = session.post(url, json=payload)

    if r.status_code not in [200, 201]:
        print("❌ CREATE FAILED:", r.status_code, r.text)

    return safe_json(r)


def update_instance(station_id, payload):
    url = f"{BASE_URL}/api/Station/{station_id}"
    r = session.put(url, json=payload)

    if r.status_code not in [200, 201]:
        print("❌ UPDATE FAILED:", r.status_code, r.text)

    return safe_json(r)


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def create_or_update_station(canonical):

    # 🔥 ALWAYS sanitize ID
    clean_id = normalize_id(canonical["stationId"])
    station_id = f"Station_{clean_id}"

    payload = {
        "dataProperties": [
            {"property": "stationName", "value": canonical["stationName"]},
            {"property": "maxCapacity", "value": canonical["capacityHoursPerDay"]},
            {"property": "stationDescription", "value": canonical["description"]}
        ]
    }

    # -----------------------------
    # CREATE OR UPDATE
    # -----------------------------
    if station_exists(station_id):

        result = update_instance(station_id, payload)
        status = "updated"

    else:

        result = create_instance({
            "individualName": station_id,
            **payload,
            "objectProperties": []
        })

        status = "created"

        # ✅ update cache immediately
        add_to_cache(station_id)

    return {
        "status": status,
        "stationId": station_id,
        "api_response": result  # 🔥 helps debugging
    }
