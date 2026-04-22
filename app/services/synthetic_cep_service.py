import json
import random
import time
from datetime import datetime

# =========================
# CONFIGURATION
# =========================

READING_UNITS = {
    "storageTemperature": "°C",
    "storageHumidity": "%",
    "averagePowerConsumption": "kW",
    "compressedAirInput": "bar",
    "noiseChillerLevel": "dB",
    "operatingTemperature": "°C",
    "powerPeakConsumption": "kW",
    "nozzleOperationTime": "hours"
}

ERROR_DEFINITIONS = [
    {
        "code": "AL06",
        "description": "Low operating temperature",
        "severity": "HIGH",
        "category": "MachineFault",
        "logic": "SINGLE",
        "weight": 0.2,
        "conditions": [
            {"type": "operatingTemperature", "operator": "<", "value": 8}
        ]
    },
    {
        "code": "AL02",
        "description": "Low compressed air",
        "severity": "HIGH",
        "category": "MachineFault",
        "logic": "SINGLE",
        "weight": 0.15,
        "conditions": [
            {"type": "compressedAirInput", "operator": "<", "value": 6.8}
        ]
    },
    {
        "code": "AL07",
        "description": "High humidity and high temperature",
        "severity": "MEDIUM",
        "category": "MachineWarning",
        "logic": "AND",
        "weight": 0.4,
        "conditions": [
            {"type": "storageHumidity", "operator": ">", "value": 70},
            {"type": "operatingTemperature", "operator": ">", "value": 25}
        ]
    },
    {
        "code": "AL10",
        "description": "Nozzle worn out",
        "severity": "LOW",
        "category": "MaintenanceRequired",
        "logic": "SINGLE",
        "weight": 0.25,
        "conditions": [
            {"type": "nozzleOperationTime", "operator": "<=", "value": 0}
        ]
    }
]

# =========================
# SHARED LOGIC
# =========================

def generate_reading_values():
    return {
        "storageTemperature": random.randint(0, 50),
        "storageHumidity": random.randint(10, 90),
        "averagePowerConsumption": round(random.uniform(4.5, 7.5), 3),
        "compressedAirInput": round(random.uniform(6.0, 9.5), 3),
        "noiseChillerLevel": random.randint(20, 60),
        "operatingTemperature": random.randint(0, 40),
        "powerPeakConsumption": round(random.uniform(8.5, 11.5), 3),
        "nozzleOperationTime": random.randint(-5, 100)
    }


def build_readings(values):
    return [
        {
            "type": key,
            "value": value,
            "unit": READING_UNITS[key]
        }
        for key, value in values.items()
    ]


def generate_timestamp(i, step=5000):
    ts = int(time.time() * 1000) + i * step
    readable = datetime.fromtimestamp(ts / 1000).strftime("%a, %b %d, %Y %H:%M:%S")
    return ts, readable


# =========================
# READINGS DATASET
# =========================

def generate_readings_dataset(n=100):
    dataset = []

    for i in range(n):
        values = generate_reading_values()
        ts, readable = generate_timestamp(i)

        machine_id = random.randint(0, 5)

        dataset.append({
            "machineId": machine_id,
            "timestamp": ts,
            "timeHR": readable,
            "virtualSensorId": f"VS_MELITO_{machine_id}",
            "readings": build_readings(values),
            "nozzleOperationTime": values["nozzleOperationTime"]
        })

    return dataset


# =========================
# EVENT ENGINE
# =========================

def evaluate_condition(values, condition):
    val = values[condition["type"]]
    op = condition["operator"]
    threshold = condition["value"]

    if op == "<":
        return val < threshold
    elif op == ">":
        return val > threshold
    elif op == "<=":
        return val <= threshold
    elif op == ">=":
        return val >= threshold
    return False


def detect_all_matching_errors(values):
    matches = []

    for error in ERROR_DEFINITIONS:
        results = [evaluate_condition(values, c) for c in error["conditions"]]

        if error["logic"] == "SINGLE" and any(results):
            matches.append(error)

        elif error["logic"] == "AND" and all(results):
            matches.append(error)

    return matches


def select_error(matches):
    if not matches:
        return None

    weights = [e["weight"] for e in matches]
    return random.choices(matches, weights=weights, k=1)[0]


def build_trigger_readings(values, error):
    return [
        {
            "type": cond["type"],
            "value": values[cond["type"]],
            "unit": READING_UNITS[cond["type"]]
        }
        for cond in error["conditions"]
    ]


def build_trigger_condition(error):
    return {
        "logic": error["logic"],
        "conditions": error["conditions"]
    }


def generate_event_status():
    return random.choices(
        ["ACTIVE", "RESOLVED"],
        weights=[0.7, 0.3]
    )[0]


# =========================
# EVENTS DATASET
# =========================

def generate_events_dataset(n=100):
    dataset = []
    i = 0

    while len(dataset) < n:
        values = generate_reading_values()

        matches = detect_all_matching_errors(values)
        error = select_error(matches)

        if not error:
            i += 1
            continue

        ts, readable = generate_timestamp(i, step=7000)
        machine_id = random.randint(0, 5)

        dataset.append({
            "eventId": f"EV_{ts}_{machine_id}",
            "machineId": machine_id,
            "timestamp": ts,
            "timeHR": readable,

            # ✅ derived automatically
            "eventType": error["category"],

            "virtualSensorId": f"VS_MELITO_{machine_id}",

            "triggerReadings": build_trigger_readings(values, error),
            "triggerCondition": build_trigger_condition(error),

            "error": {
                "code": error["code"],
                "description": error["description"],
                "severity": error["severity"]
            },

            "status": generate_event_status()
        })

        i += 1

    return dataset

# =========================
# ARGON SIMULATION CONFIG
# =========================

ARGON_UNIT = "%"
TIME_UNIT = "hours"


def initialize_argon_state():
    return {
        "register1": 100.0,
        "register2": 100.0,
        "register3": 100.0
    }


def consume_argon(state):
    # random total consumption per step
    total_consumption = random.uniform(0.1, 1.5)

    # randomly distribute across bottles
    weights = [random.random() for _ in range(3)]
    total_weight = sum(weights)

    for i, key in enumerate(state.keys()):
        portion = (weights[i] / total_weight) * total_consumption
        state[key] = max(0.0, state[key] - portion)

    return state


def check_refill(state):
    return any(v <= 0 for v in state.values())


def refill(state):
    return {
        "register1": 100.0,
        "register2": 100.0,
        "register3": 100.0
    }


def estimate_depletion_time(prev_state, current_state, delta_time_hours=0.002):
    # simple linear depletion estimate
    rates = []

    for key in current_state:
        diff = prev_state[key] - current_state[key]
        if diff > 0:
            rate = diff / delta_time_hours
            remaining = current_state[key]
            rates.append(remaining / rate if rate > 0 else 999)

    if not rates:
        return None

    return min(rates)  # earliest depletion


# =========================
# 1. ARGON READINGS
# =========================

def generate_argon_readings_dataset(n=100):
    dataset = []
    state = initialize_argon_state()

    for i in range(n):
        prev_state = state.copy()
        state = consume_argon(state)

        ts, readable = generate_timestamp(i, step=5000)
        machine_id = random.randint(0, 5)

        dataset.append({
            "machineId": machine_id,
            "timestamp": ts,
            "timeHR": readable,
            "virtualSensorId": f"VS_ARGON_{machine_id}",
            "readings": [
                {"type": "argonBottle1Level", "value": state["register1"], "unit": ARGON_UNIT},
                {"type": "argonBottle2Level", "value": state["register2"], "unit": ARGON_UNIT},
                {"type": "argonBottle3Level", "value": state["register3"], "unit": ARGON_UNIT}
            ]
        })

        # refill logic
        if check_refill(state):
            state = refill(state)

    return dataset


# =========================
# 2. ARGON PREDICTIONS
# =========================

def generate_argon_predictions_dataset(n=100):
    dataset = []
    state = initialize_argon_state()

    for i in range(n):
        prev_state = state.copy()
        state = consume_argon(state)

        prediction = estimate_depletion_time(prev_state, state)

        if prediction is None:
            continue

        ts, readable = generate_timestamp(i, step=5000)
        machine_id = random.randint(0, 5)

        dataset.append({
            "eventId": f"EV_ARGON_PRED_{ts}_{machine_id}",
            "machineId": machine_id,
            "timestamp": ts,
            "timeHR": readable,
            "virtualSensorId": f"VS_ARGON_{machine_id}",

            "eventType": "PredictiveMaintenance",

            "prediction": {
                "target": "ArgonGasDepletion",
                "predictedTimeToDepletion": round(prediction, 3),
                "unit": TIME_UNIT,
                "method": "linearInterpolation"
            },

            "basedOn": [
                {"type": "argonBottle1Level", "value": state["register1"], "unit": ARGON_UNIT},
                {"type": "argonBottle2Level", "value": state["register2"], "unit": ARGON_UNIT},
                {"type": "argonBottle3Level", "value": state["register3"], "unit": ARGON_UNIT}
            ],

            "severity": "MEDIUM"
        })

        if check_refill(state):
            state = refill(state)

    return dataset


# =========================
# 3. MAINTENANCE EVENTS
# =========================

def generate_maintenance_events_dataset(n=100):
    dataset = []
    state = initialize_argon_state()

    count = 0
    i = 0

    while count < n:
        state = consume_argon(state)

        if check_refill(state):
            ts, readable = generate_timestamp(i, step=5000)
            machine_id = random.randint(0, 5)

            dataset.append({
                "eventId": f"EV_ARGON_REFILL_{ts}_{machine_id}",
                "machineId": machine_id,
                "timestamp": ts,
                "timeHR": readable,

                "eventType": "MaintenancePerformed",

                "details": {
                    "action": "Refill Argon Gas",
                    "affectedComponents": [
                        "argonBottle1",
                        "argonBottle2",
                        "argonBottle3"
                    ]
                },

                "status": "COMPLETED"
            })

            state = refill(state)
            count += 1

        i += 1

    return dataset
# =========================
# PUBLIC API (FOR ROUTER)
# =========================

def get_melito_readings(n=1000):
    return generate_readings_dataset(n)


def get_melito_events(n=1000):
    return generate_events_dataset(n)


def get_argon_readings(n=1000):
    return generate_argon_readings_dataset(n)


def get_argon_predictions(n=1000):
    return generate_argon_predictions_dataset(n)

def get_argon_maintenance(n=50):
    return generate_maintenance_events_dataset(n)
