
import math
from typing import Any


def normalize_value(value: Any) -> Any:
    """Clean a value without changing its underlying meaning."""

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, str):
        value = value.strip()

        # Remove matching quotes around exported IDs.
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ('"', "'")
        ):
            value = value[1:-1].strip()

        return value or None

    return value


def normalize_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    """Normalize values while preserving the original field names."""

    return {
        field: normalize_value(value)
        for field, value in record.items()
    }


def normalize_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize every record in a dataset."""

    return [
        normalize_record(record)
        for record in records
    ]

