
from pathlib import Path
from typing import Any

from app.services.budatech_v2.excel_reader import read_customers
from app.services.budatech_v2.normalizer import normalize_record
from app.services.budatech_v2.harmonizers import harmonize_customer
from app.services.budatech_v2.validators import validate_customer
from app.services.budatech_v2.ontology_mapper import (
    map_customer_to_ontology,
)
from app.services.budatech_v2.blueprint_adapter import BlueprintAdapter



def process_customer_records(
    records: list[dict[str, Any]],
    adapter: BlueprintAdapter | None = None,
) -> dict[str, Any]:
    """Process Customer records, skipping IDs already in NARRATE."""

    adapter = adapter or BlueprintAdapter()
    results = []

    for row_number, raw_record in enumerate(records, start=1):
        try:
            normalized = normalize_record(raw_record)
            canonical = harmonize_customer(normalized)
            errors = validate_customer(canonical)

            if errors:
                results.append({
                    "row": row_number,
                    "status": "validation_error",
                    "customerId": canonical.get("customerId"),
                    "errors": errors,
                })
                continue

            customer_id = canonical["customerId"]

            # Check the ontology before attempting creation.
            if adapter.customer_exists(customer_id):
                results.append({
                    "row": row_number,
                    "status": "duplicate",
                    "customerId": customer_id,
                    "message": (
                        "This Customer ID already exists in NARRATE. "
                        "The record was skipped. If its fields need "
                        "updating, use the update function in the "
                        "NARRATE web app."
                    ),
                })
                continue

            ontology_record = map_customer_to_ontology(canonical)
            individual_name = (
                f"Customer_{adapter._sanitize_id(customer_id)}"
            )

            response = adapter.create_customer(
                ontology_record,
                individual_name,
            )

            succeeded = response.get("status") == "success"

            results.append({
                "row": row_number,
                "customerId": customer_id,
                "status": "success" if succeeded else "error",
                "response": response,
            })

        except Exception as exc:
            results.append({
                "row": row_number,
                "status": "error",
                "customerId": raw_record.get("ID"),
                "message": str(exc),
            })

    duplicates = [
        {
            "row": result["row"],
            "customerId": result["customerId"],
            "message": result["message"],
        }
        for result in results
        if result["status"] == "duplicate"
    ]

    successful = sum(
        result["status"] == "success"
        for result in results
    )
    failed = sum(
        result["status"] in {"error", "validation_error"}
        for result in results
    )

    return {
        "entity": "customers",
        "total_records": len(records),
        "successful_records": successful,
        "duplicate_records_count": len(duplicates),
        "failed_records": failed,
        "duplicates": duplicates,
        "results": results,
    }


def ingest_customer_excel(
    file_path: str | Path,
    adapter: BlueprintAdapter | None = None,
) -> dict[str, Any]:
    """Read and ingest a Customer Excel export."""

    records = read_customers(file_path)
    return process_customer_records(records, adapter=adapter)
