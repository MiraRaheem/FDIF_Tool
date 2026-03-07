import requests

BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


def create_blueprint_instance(class_name, payload):

    url = f"{BASE_URL}/api/{class_name}"

    response = requests.post(url, json=payload)

    return response.json()
