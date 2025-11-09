from typing import Dict, Any

def map_to_blueprint(observation_ld: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 6: Blueprint Mapper
    - Build the digital-twin shape for a Machine node with a temperature sensor
    """
    return {
        "machine": {
            "id": observation_ld.get("deviceId"),
            "metadata": {
                "location": observation_ld.get("location")
            },
            "sensors": {
                "temperature": {
                    "currentValue": observation_ld.get("temperature_celsius"),
                    "unit": "C",
                    "lastUpdated": observation_ld.get("timestamp")
                }
            }
        }
    }
