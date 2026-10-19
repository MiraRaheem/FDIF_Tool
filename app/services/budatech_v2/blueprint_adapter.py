
import os
from typing import Any

import requests


DEFAULT_BASE_URL = "https://narrate-webapp-tcxs.onrender.com"


class BlueprintAdapter:
    """Independent adapter for the Budatech v2 FDIF implementation."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
    ):
        self.base_url = (
            base_url or os.getenv("NARRATE_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.timeout = timeout

    def create_instance(
        self,
        class_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create one ontology instance through the NARRATE API."""

        url = f"{self.base_url}/api/{class_name}"

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            return {
                "status": "error",
                "message": f"NARRATE API request failed: {exc}",
            }

        try:
            body = response.json()
        except ValueError:
            body = {"response": response.text}

        if not response.ok:
            return {
                "status": "error",
                "http_status": response.status_code,
                "response": body,
            }

        return body

    def create_customer(
        self,
        ontology_record: dict[str, Any],
        individual_name: str,
    ) -> dict[str, Any]:
        """
        Submit an ontology-mapped Customer record.

        Expected input:
        {
            "class": "Customer",
            "properties": {
                "hasCustomerID": "...",
                "hasCustomerName": "...",
                "hasCustomerType": "OEM"
            }
        }
        """

        if ontology_record.get("class") != "Customer":
            return {
                "status": "error",
                "message": "Expected ontology class 'Customer'.",
            }

        properties = ontology_record.get("properties")

        if not isinstance(properties, dict):
            return {
                "status": "error",
                "message": "Customer properties must be a dictionary.",
            }

        data_properties = [
            {"property": property_name, "value": value}
            for property_name, value in properties.items()
            if value is not None
        ]

        payload = {
            "individualName": individual_name,
            "dataProperties": data_properties,
            "objectProperties": [],
        }

        return self.create_instance("Customer", payload)

