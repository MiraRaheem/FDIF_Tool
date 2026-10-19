
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



from typing import Any


def map_supplier_to_ontology(
    supplier: dict[str, Any],
) -> dict[str, Any]:
    """
    Map canonical Supplier data to the MaterialSupplier ontology class.

    Only properties confirmed by the available ontology metadata
    are included. Source fields without a confirmed ontology
    property remain in the canonical record.
    """

    property_mapping = {
        "supplierId": "hasSupplierID",
        "supplierName": "hasSupplierName",
    }

    ontology_properties = {}

    for canonical_field, ontology_property in property_mapping.items():
        value = supplier.get(canonical_field)

        if value is not None:
            ontology_properties[ontology_property] = value

    return {
        "class": "MaterialSupplier",
        "properties": ontology_properties,
    }

