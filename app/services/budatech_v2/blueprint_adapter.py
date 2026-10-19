
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

    
    @staticmethod
    def _sanitize_id(value: str) -> str:
        """Build the same safe identifier used for Customer instances."""
        return (
            str(value)
            .strip()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace("(", "")
            .replace(")", "")
        )

    def customer_exists(self, customer_id: str) -> bool:
        """Check whether a Customer with this ID already exists."""

        url = f"{self.base_url}/api/Customer"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(
                f"Could not check whether Customer ID "
                f"'{customer_id}' exists: {exc}"
            ) from exc

        instances = body.get("instances", [])
        expected_name = f"Customer_{self._sanitize_id(customer_id)}"

        for instance in instances:
            # Some API responses contain full instance URIs.
            if isinstance(instance, str):
                instance_name = instance.rstrip("/").split("#")[-1]
                instance_name = instance_name.split("/")[-1]

                if instance_name == expected_name:
                    return True

            elif isinstance(instance, dict):
                # Support APIs that return the ID directly.
                if instance.get("hasCustomerID") == customer_id:
                    return True

                # Or return dataProperties as a list of property/value pairs.
                data_properties = instance.get("dataProperties", [])

                if isinstance(data_properties, list):
                    for prop in data_properties:
                        if (
                            isinstance(prop, dict)
                            and prop.get("property") == "hasCustomerID"
                            and prop.get("value") == customer_id
                        ):
                            return True

                # Or return dataProperties as a dictionary.
                elif isinstance(data_properties, dict):
                    if data_properties.get("hasCustomerID") == customer_id:
                        return True

                # Check the instance name if the ID property isn't included.
                if instance.get("individualName") == expected_name:
                    return True

        return False

    
    def supplier_exists(self, supplier_id: str) -> bool:
        """Check whether a MaterialSupplier with this ID already exists."""

        url = f"{self.base_url}/api/MaterialSupplier"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(
                f"Could not check whether Supplier ID "
                f"'{supplier_id}' exists: {exc}"
            ) from exc

        instances = body.get("instances", [])
        expected_name = f"MaterialSupplier_{self._sanitize_id(supplier_id)}"

        for instance in instances:
            if isinstance(instance, str):
                instance_name = instance.rstrip("/").split("#")[-1]
                instance_name = instance_name.split("/")[-1]

                if instance_name == expected_name:
                    return True

            elif isinstance(instance, dict):
                if instance.get("hasSupplierID") == supplier_id:
                    return True

                data_properties = instance.get("dataProperties", [])

                if isinstance(data_properties, list):
                    for prop in data_properties:
                        if (
                            isinstance(prop, dict)
                            and prop.get("property") == "hasSupplierID"
                            and prop.get("value") == supplier_id
                        ):
                            return True

                elif isinstance(data_properties, dict):
                    if data_properties.get("hasSupplierID") == supplier_id:
                        return True

                if instance.get("individualName") == expected_name:
                    return True

        return False



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


def create_supplier(
    self,
    ontology_record: dict[str, Any],
    individual_name: str,
) -> dict[str, Any]:
    """Submit an ontology-mapped MaterialSupplier record."""

    if ontology_record.get("class") != "MaterialSupplier":
        return {
            "status": "error",
            "message": "Expected ontology class 'MaterialSupplier'.",
        }

    properties = ontology_record.get("properties")

    if not isinstance(properties, dict):
        return {
            "status": "error",
            "message": "Supplier properties must be a dictionary.",
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

    return self.create_instance("MaterialSupplier", payload)

