
from typing import Any


def map_customer_to_ontology(
    customer: dict[str, Any],
) -> dict[str, Any]:
    """
    Map a validated canonical Customer record to ontology properties.

    Input: canonical FDIF Customer fields.
    Output: ontology class and its populated data properties.

    This function does not perform API ingestion.
    """

    property_mapping = {
        "customerId": "hasCustomerID",
        "customerName": "hasCustomerName",
        "customerType": "hasCustomerType",
    }

    ontology_properties = {}

    for canonical_field, ontology_property in property_mapping.items():
        value = customer.get(canonical_field)

        # Do not create ontology properties for missing optional values.
        if value is not None:
            ontology_properties[ontology_property] = value

    return {
        "class": "Customer",
        "properties": ontology_properties,
    }

