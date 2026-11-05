"""Validated, idempotent ingestion for the four MEDWOOD review CSV files."""
from __future__ import annotations

import csv
import io
import json
import math
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any
from urllib.parse import quote

import requests


BASE_URL = os.getenv("NARRATE_BASE_URL", "https://narrate-webapp-tcxs.onrender.com").rstrip("/")
REQUEST_TIMEOUT = 60


class BlueprintClient:
    """Small checked client for NARRATE Blueprint class endpoints."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self._object_property_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}

    @staticmethod
    def _result(response: requests.Response, operation: str) -> Any:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"{operation} failed: HTTP {response.status_code}: {response.text[:1000]}")
        if isinstance(body, dict):
            if str(body.get("status", "")).casefold() in {"error", "failed"} or body.get("success") is False or body.get("error"):
                raise RuntimeError(f"{operation} was rejected: {body.get('message') or body.get('error') or body}")
        return body

    def list_names(self, class_name: str) -> set[str]:
        url = f"{BASE_URL}/api/{quote(class_name, safe='')}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            raise RuntimeError(f"Could not load existing {class_name} instances: {exc}") from exc
        body = self._result(response, f"Loading {class_name} instances")
        if not isinstance(body, dict) or not isinstance(body.get("instances"), list):
            raise RuntimeError(f"NARRATE returned an unexpected {class_name} instance list")
        names: set[str] = set()
        for item in body["instances"]:
            if isinstance(item, str) and item.strip():
                name = item.strip().rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                names.add(name)
            elif isinstance(item, dict):
                name = item.get("individualName")
                if name:
                    names.add(str(name).strip())
        return names

    def validate_blueprint(
        self,
        class_name: str,
        *,
        data_properties: set[str],
        object_properties: set[str] = frozenset(),
        supplied_data_properties: set[str] | None = None,
        allow_required_omissions: bool = False,
    ) -> list[str]:
        """Fail before writes if the deployed blueprint cannot store this mapping."""
        url = f"{BASE_URL}/api/query/metadata/{quote(class_name, safe='')}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            raise RuntimeError(f"Could not load the {class_name} blueprint: {exc}") from exc
        body = self._result(response, f"Loading {class_name} blueprint")
        if not isinstance(body, dict):
            raise RuntimeError(f"NARRATE returned malformed {class_name} blueprint metadata")
        available_data = {
            str(item.get("name")) for item in body.get("dataProperties", [])
            if isinstance(item, dict) and item.get("name")
        }
        available_objects = set(body.get("objectProperties", {})) if isinstance(body.get("objectProperties"), dict) else set()
        if not available_data and not available_objects:
            raise RuntimeError(f"The deployed NARRATE blueprint for {class_name} was not found or exposes no properties")
        missing_data = sorted(data_properties - available_data)
        missing_objects = sorted(object_properties - available_objects)
        if missing_data or missing_objects:
            missing = [*(f"data property {name}" for name in missing_data), *(f"object property {name}" for name in missing_objects)]
            raise RuntimeError(f"The {class_name} blueprint is missing mapped " + ", ".join(missing))

        # ProductType records intentionally contain only IDs. Refuse to write
        # until the deployed ontology has had its required cardinalities relaxed.
        cardinalities = body.get("cardinalities", {})
        if supplied_data_properties is not None and isinstance(cardinalities, dict):
            still_required = sorted(
                name for name, limits in cardinalities.items()
                if name not in supplied_data_properties and isinstance(limits, dict) and int(limits.get("min", 0) or 0) > 0
            )
            if still_required and not allow_required_omissions:
                raise RuntimeError(
                    f"The {class_name} blueprint still requires omitted properties: "
                    + ", ".join(still_required)
                    + ". Relax those minimum cardinalities before ingestion."
                )
            if still_required:
                return still_required
        return []

    def upsert(
        self,
        class_name: str,
        individual_name: str,
        data_properties: list[dict[str, Any]],
        object_properties: list[dict[str, str]],
        existing: set[str],
    ) -> str:
        safe_name = quote(individual_name, safe="")
        if individual_name in existing:
            url = f"{BASE_URL}/api/{quote(class_name, safe='')}/{safe_name}"
            payload: dict[str, Any] = {"dataProperties": data_properties}
            if object_properties:
                payload["objectProperties"] = object_properties
            operation = f"Updating {class_name} {individual_name}"
            try:
                response = self.session.put(url, json=payload, timeout=REQUEST_TIMEOUT)
            except requests.RequestException as exc:
                raise RuntimeError(f"{operation} failed: {exc}") from exc
            self._result(response, operation)
            return "updated"

        url = f"{BASE_URL}/api/{quote(class_name, safe='')}"
        payload = {
            "individualName": individual_name,
            "dataProperties": data_properties,
            "objectProperties": object_properties,
        }
        operation = f"Creating {class_name} {individual_name}"
        try:
            response = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            raise RuntimeError(f"{operation} failed: {exc}") from exc
        self._result(response, operation)
        existing.add(individual_name)
        return "created"

    def add_object_properties(
        self, class_name: str, individual_name: str, properties: list[dict[str, str]]
    ) -> None:
        if not properties:
            return
        key = (class_name, individual_name)
        url = f"{BASE_URL}/api/{quote(class_name, safe='')}/{quote(individual_name, safe='')}"
        if key not in self._object_property_cache:
            try:
                response = self.session.get(
                    f"{BASE_URL}/ontologyReaderAjax",
                    params={"type": "objectPropertyValues", "individual": individual_name},
                    timeout=REQUEST_TIMEOUT,
                )
            except requests.RequestException as exc:
                raise RuntimeError(f"Loading relationships for {class_name} {individual_name} failed: {exc}") from exc
            body = self._result(response, f"Loading {class_name} {individual_name}")
            if not isinstance(body, dict):
                raise RuntimeError(f"NARRATE returned malformed objectProperties for {class_name} {individual_name}")
            current = []
            for property_name, values in body.items():
                if isinstance(values, str):
                    values = [values]
                if not isinstance(values, list):
                    raise RuntimeError(f"NARRATE returned malformed objectProperties for {class_name} {individual_name}")
                current.extend(
                    {"property": property_name, "value": str(value)}
                    for value in values
                    if value is not None and str(value).strip()
                )
            self._object_property_cache[key] = current
        merged = list(self._object_property_cache[key])
        for prop in properties:
            if prop not in merged:
                merged.append(prop)
        try:
            response = self.session.put(
                url,
                json={"objectProperties": merged},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Updating relationships for {class_name} {individual_name} failed: {exc}") from exc
        self._result(response, f"Updating relationships for {class_name} {individual_name}")
        self._object_property_cache[key] = merged


def _read_csv(content: bytes, required_headers: set[str]) -> tuple[list[dict[str, str]], list[str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")
    headers = [str(header or "").strip() for header in reader.fieldnames]
    if len(headers) != len(set(headers)):
        raise ValueError("CSV has duplicate column names after trimming whitespace")
    missing = sorted(required_headers - set(headers))
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
    rows = []
    for source_row, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f"CSV row {source_row} has more fields than the header")
        normalized = {str(key or "").strip(): str(value or "").strip() for key, value in row.items() if key is not None}
        normalized["__sourceRow"] = str(source_row)
        rows.append(normalized)
    if not rows:
        raise ValueError("CSV contains no data rows")
    return rows, headers


def _value(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _number(value: str, field: str, *, minimum: float | None = None) -> int | float | None:
    if not value:
        return None
    candidate = value.replace(" ", "")
    if "," in candidate and "." not in candidate:
        candidate = candidate.replace(",", ".")
    try:
        parsed = float(candidate)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be a finite number")
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field} must be at least {minimum:g}")
    return int(parsed) if parsed.is_integer() else parsed


def _required(value: str, label: str) -> str:
    if not value:
        raise ValueError(f"{label} is required")
    return value


def _ontology_identifier(value: str, field: str) -> str:
    """Keep source identifiers as lexical strings, including leading zeroes."""
    identifier = str(value).strip()
    if not identifier:
        raise ValueError(f"{field} is required")
    return identifier


def _local_part(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")).strip("_")


def _individual(prefix: str, source_id: str) -> str:
    segment = _local_part(source_id)
    if not segment:
        raise ValueError(f"{prefix} ID has no characters allowed in an individual name")
    return f"{prefix}_{segment}"[:180]


def _source_data(row: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in row.items() if key != "__sourceRow"}


def _property(name: str, value: Any) -> dict[str, Any]:
    # These identifiers are xsd:string in the ontology. Always serialize them
    # as JSON strings; never parse numeric-looking IDs as numbers in Python.
    if name in {"hasProductID", "hasWorkOrderID", "hasExecutionID", "hasManufacturedProductID"}:
        value = _ontology_identifier(str(value), name)
    elif name in {
        "hasRequestedQuantity", "hasCompletedQuantity", "hasManufacturedQuantity",
        "hasActualDurationMinutes", "hasOutputQuantity", "hasDefectQuantity",
    } and value is not None:
        # These MEDWOOD quantity/duration properties have xsd:integer ranges.
        numeric = float(value)
        if not math.isfinite(numeric) or not numeric.is_integer():
            raise ValueError(f"{name} must be an integer for the ontology")
        value = int(numeric)
    elif name in {"hasActualStartDate", "hasActualEndDate", "hasProductionDate"} and value is not None:
        # These date properties have xsd:dateTime ranges.
        normalized = str(value).strip().replace("Z", "+00:00")
        try:
            value = datetime.fromisoformat(normalized).isoformat(timespec="auto")
        except ValueError as exc:
            raise ValueError(f"{name} must be normalized to an ISO xsd:dateTime") from exc
    return {"property": name, "value": value}


def _object_property(name: str, value: str) -> dict[str, str]:
    return {"property": name, "value": value}


def _deduplicate(
    records: list[dict[str, Any]], key: str, rejected: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record[key]].append(record)
    keep: list[dict[str, Any]] = []
    for record_id, group in groups.items():
        signatures = {
            json.dumps(
                {k: v for k, v in item.items() if k not in {"sourceRow", "sourceData", key}},
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            for item in group
        }
        if len(signatures) > 1:
            for item in group:
                rejected.append({
                    "sourceRow": item["sourceRow"],
                    "recordId": record_id,
                    "reason": "Conflicting rows have the same identifier; all rows for this identifier were skipped.",
                    "sourceData": item.get("sourceData"),
                })
        else:
            keep.append(group[0])
            for duplicate in group[1:]:
                rejected.append({
                    "sourceRow": duplicate["sourceRow"],
                    "recordId": record_id,
                    "reason": f"Duplicate of source row {group[0]['sourceRow']} with identical mapped values.",
                    "sourceData": duplicate.get("sourceData"),
                })
    return keep


def _base_report(entity: str, total: int) -> dict[str, Any]:
    return {
        "status": "completed",
        "entity": entity,
        "summary": {
            "rowsReceived": total,
            "created": 0,
            "updated": 0,
            "rejected": 0,
            "failed": 0,
            "relationshipFailures": 0,
            "recordWarnings": 0,
        },
        "ingested": [],
        "rejectedRecords": [],
        "failedRecords": [],
        "relationshipFailures": [],
        "recordWarnings": [],
        "warnings": [],
    }


def _finish(report: dict[str, Any]) -> dict[str, Any]:
    report["summary"]["rejected"] = len(report["rejectedRecords"])
    report["summary"]["failed"] = len(report["failedRecords"])
    report["summary"]["relationshipFailures"] = len(report["relationshipFailures"])
    report["summary"]["recordWarnings"] = len(report["recordWarnings"])
    if report["rejectedRecords"] or report["failedRecords"] or report["relationshipFailures"] or report["recordWarnings"]:
        report["status"] = "completed_with_issues"
    return report


def _ingest_rows(
    client: BlueprintClient,
    class_name: str,
    records: list[dict[str, Any]],
    existing: set[str],
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    succeeded = []
    for item in records:
        try:
            action = client.upsert(
                class_name,
                item["individualName"],
                item["dataProperties"],
                item.get("objectProperties", []),
                existing,
            )
            report["summary"][action] += 1
            output = {
                "sourceRow": item["sourceRow"],
                "recordId": item["individualName"],
                "action": action,
                "dataProperties": item.get("dataProperties", []),
            }
            direct_relationships = item.get("objectProperties", [])
            if direct_relationships:
                output["relationships"] = [
                    {
                        "property": relationship["property"],
                        "target": relationship["value"],
                        "status": "linked",
                    }
                    for relationship in direct_relationships
                ]
            report["ingested"].append(output)
            succeeded.append(item)
        except Exception as exc:
            report["failedRecords"].append({
                "sourceRow": item["sourceRow"],
                "recordId": item["individualName"],
                "reason": str(exc),
                "sourceData": item.get("sourceData"),
            })
    return succeeded


def ingest_product_types(content: bytes) -> dict[str, Any]:
    rows, _ = _read_csv(content, {"individualName", "hasProductID"})
    report = _base_report("ProductType", len(rows))
    records = []
    for row in rows:
        source_row = int(row["__sourceRow"])
        try:
            product_id = _ontology_identifier(_value(row, "hasProductID"), "hasProductID")
            name = _required(_value(row, "individualName"), "individualName")
            expected_name = _individual("ProductType", product_id)
            if name != expected_name:
                raise ValueError(f"individualName must be {expected_name!r} for hasProductID")
            records.append({
                "sourceRow": source_row,
                "sourceData": _source_data(row),
                "key": product_id,
                "individualName": name,
                "dataProperties": [_property("hasProductID", product_id)],
                "objectProperties": [],
            })
        except Exception as exc:
            report["rejectedRecords"].append({"sourceRow": source_row, "sourceData": _source_data(row), "reason": str(exc)})
    records = _deduplicate(records, "key", report["rejectedRecords"])
    report["warnings"].append(
        "hasProductName, hasProductCost, hasProductPrice, and hasProductionDate are absent from this review file and are omitted; "
        "these ProductType records are intentionally staged with only their IDs so they can be completed later."
    )
    client = BlueprintClient()
    still_required = client.validate_blueprint(
        "ProductType",
        data_properties={"hasProductID"},
        supplied_data_properties={"hasProductID"},
        allow_required_omissions=True,
    )
    if still_required:
        report["warnings"].append(
            "ProductType IDs are being staged without these required blueprint values, as requested: "
            + ", ".join(still_required)
            + ". Fernando can complete them later."
        )
    existing = client.list_names("ProductType")
    _ingest_rows(client, "ProductType", records, existing, report)
    return _finish(report)


def ingest_work_orders(content: bytes) -> dict[str, Any]:
    rows, _ = _read_csv(content, {"hasWorkOrderID"})
    report = _base_report("WorkOrder", len(rows))
    records = []
    for row in rows:
        source_row = int(row["__sourceRow"])
        try:
            work_order_id = _ontology_identifier(_value(row, "hasWorkOrderID"), "hasWorkOrderID")
            name = _individual("MEDWOOD_WorkOrder", work_order_id)
            data = [_property("hasWorkOrderID", work_order_id)]
            requested_quantity = _number(
                _value(row, "hasRequestedQuantity"), "hasRequestedQuantity", minimum=0
            )
            if requested_quantity is not None:
                if not isinstance(requested_quantity, int):
                    report["recordWarnings"].append({
                        "sourceRow": source_row,
                        "recordId": name,
                        "property": "hasRequestedQuantity",
                        "value": _value(row, "hasRequestedQuantity"),
                        "reason": "Fractional value omitted because the ontology range is xsd:integer; other valid WorkOrder values will still be ingested.",
                    })
                else:
                    data.append(_property("hasRequestedQuantity", requested_quantity))

            completed_quantity = _number(
                _value(row, "unvalidatedSumPiezasBuenasAcrossPerformanceRows"),
                "unvalidatedSumPiezasBuenasAcrossPerformanceRows",
                minimum=0,
            )
            if completed_quantity is not None:
                if not isinstance(completed_quantity, int):
                    report["recordWarnings"].append({
                        "sourceRow": source_row,
                        "recordId": name,
                        "property": "hasCompletedQuantity",
                        "sourceField": "unvalidatedSumPiezasBuenasAcrossPerformanceRows",
                        "value": _value(row, "unvalidatedSumPiezasBuenasAcrossPerformanceRows"),
                        "reason": "Fractional value omitted because the ontology range is xsd:integer; other valid WorkOrder values will still be ingested.",
                    })
                else:
                    data.append(_property("hasCompletedQuantity", completed_quantity))

            actual_start = _ontology_datetime(
                _value(row, "hasActualStartDateCandidate"), "hasActualStartDateCandidate"
            )
            actual_end = _ontology_datetime(
                _value(row, "hasActualEndDateCandidate"), "hasActualEndDateCandidate"
            )
            if actual_start and actual_end and actual_end < actual_start:
                raise ValueError("hasActualEndDateCandidate is earlier than hasActualStartDateCandidate")
            if actual_start:
                data.append(_property("hasActualStartDate", actual_start))
            if actual_end:
                data.append(_property("hasActualEndDate", actual_end))
            records.append({
                "sourceRow": source_row,
                "sourceData": _source_data(row),
                "key": work_order_id,
                "individualName": name,
                "dataProperties": data,
                "objectProperties": [],
            })
        except Exception as exc:
            report["rejectedRecords"].append({
                "sourceRow": source_row,
                "recordId": _value(row, "hasWorkOrderID") or None,
                "reason": str(exc),
                "sourceData": _source_data(row),
            })
    records = _deduplicate(records, "key", report["rejectedRecords"])
    report["warnings"].extend([
        "hasCompletedQuantity uses unvalidatedSumPiezasBuenasAcrossPerformanceRows as requested. This is an unvalidated sum "
        "across Performance rows and may double-count pieces reported at multiple stations; review it before treating it as authoritative.",
        "Actual start/end date candidates accept common date/date-time formats and are normalized to xsd:dateTime. "
        "Date-only values become midnight; timestamps retain their time and timezone when supplied. "
        "Ambiguous slash dates use month/day/year, matching the reviewed export.",
        "appliesToProduct is omitted until ManufacturedProduct individuals exist; the ontology range is ManufacturedProduct. "
        "The ManufacturedProduct ingestion endpoint will add the inverse WorkOrder.appliesToProduct relationship later.",
        "includesExecution is omitted until ProcessExecution individuals exist; the ProcessExecution ingestion endpoint "
        "will add the inverse WorkOrder.includesExecution relationship later.",
    ])
    client = BlueprintClient()
    client.validate_blueprint(
        "WorkOrder",
        data_properties={
            "hasWorkOrderID", "hasRequestedQuantity", "hasCompletedQuantity",
            "hasActualStartDate", "hasActualEndDate",
        },
    )
    existing = client.list_names("WorkOrder")
    _ingest_rows(client, "WorkOrder", records, existing, report)
    return _finish(report)


def ingest_process_executions(content: bytes) -> dict[str, Any]:
    rows, _ = _read_csv(content, {
        "hasExecutionID", "isPartOfWorkOrder", "hasExecutionStartTimeCandidate",
        "hasExecutionEndTimeCandidate", "hasActualDurationMinutesCandidate",
        "hasOutputQuantityCandidate", "hasDefectQuantityCandidate",
        "hasExecutionStatusCandidate", "workCentreLabelCandidate",
    })
    report = _base_report("ProcessExecution", len(rows))
    client = BlueprintClient()
    client.validate_blueprint(
        "ProcessExecution",
        data_properties={
            "hasExecutionID", "hasExecutionStatus", "hasExecutionStartTime",
            "hasExecutionEndTime", "hasActualDurationMinutes", "hasOutputQuantity",
            "hasDefectQuantity",
        },
        object_properties={"isPartOfWorkOrder"},
    )
    client.validate_blueprint("WorkOrder", data_properties=set(), object_properties={"includesExecution"})
    work_orders = client.list_names("WorkOrder")
    process_executions = client.list_names("ProcessExecution")
    records = []
    for row in rows:
        source_row = int(row["__sourceRow"])
        execution_id = _value(row, "hasExecutionID")
        work_order_id = _value(row, "isPartOfWorkOrder")
        try:
            _required(execution_id, "hasExecutionID")
            _required(work_order_id, "isPartOfWorkOrder")
            execution_name = _individual("MEDWOOD_ProcessExecution", execution_id)
            work_order_name = _individual("MEDWOOD_WorkOrder", work_order_id)
            if work_order_name not in work_orders:
                raise ValueError(f"Referenced WorkOrder {work_order_name!r} does not exist; ingest WorkOrders first")
            data = [_property("hasExecutionID", execution_id)]
            start_time = _execution_timestamp(
                _value(row, "hasExecutionStartTimeCandidate"), "hasExecutionStartTimeCandidate"
            )
            end_time = _execution_timestamp(
                _value(row, "hasExecutionEndTimeCandidate"), "hasExecutionEndTimeCandidate"
            )
            if start_time and end_time and end_time < start_time:
                raise ValueError("hasExecutionEndTimeCandidate is earlier than hasExecutionStartTimeCandidate")
            if start_time:
                data.append(_property("hasExecutionStartTime", start_time))
            if end_time:
                data.append(_property("hasExecutionEndTime", end_time))

            for source_field, property_name in (
                ("hasActualDurationMinutesCandidate", "hasActualDurationMinutes"),
                ("hasOutputQuantityCandidate", "hasOutputQuantity"),
                ("hasDefectQuantityCandidate", "hasDefectQuantity"),
            ):
                raw_number = _value(row, source_field)
                number = _number(raw_number, source_field, minimum=0)
                if number is None:
                    continue
                if not isinstance(number, int):
                    report["recordWarnings"].append({
                        "sourceRow": source_row,
                        "recordId": execution_name,
                        "property": property_name,
                        "sourceField": source_field,
                        "value": raw_number,
                        "reason": "Fractional value omitted because the ontology range is xsd:integer; other valid ProcessExecution values will still be ingested.",
                    })
                    continue
                data.append(_property(property_name, number))

            status = _value(row, "hasExecutionStatusCandidate")
            if status:
                allowed_statuses = {"Cancelled", "Completed", "Failed", "Interrupted", "Paused", "Planned", "Running", "Scheduled"}
                if status not in allowed_statuses:
                    raise ValueError(f"Unsupported hasExecutionStatus value {status!r}")
                data.append(_property("hasExecutionStatus", status))
            records.append({
                "sourceRow": source_row,
                "sourceData": _source_data(row),
                "key": execution_id,
                "individualName": execution_name,
                "workOrderName": work_order_name,
                "workCentreLabel": _value(row, "workCentreLabelCandidate") or None,
                "dataProperties": data,
                "objectProperties": [_object_property("isPartOfWorkOrder", work_order_name)],
            })
        except Exception as exc:
            report["rejectedRecords"].append({
                "sourceRow": source_row,
                "recordId": execution_id or None,
                "reason": str(exc),
                "sourceData": _source_data(row),
            })
    records = _deduplicate(records, "key", report["rejectedRecords"])
    report["warnings"].extend([
        "Date-only start/end candidates are stored at 00:00:00Z to satisfy the ontology's xsd:dateTimeStamp range. UTC midnight is a datatype-compatible storage convention; the source does not contain an observed time or timezone.",
        "Duration, good-output, and defect candidates are ingested when they are whole numbers. They are sums across dated rows; confirm those rows are additive before treating the values as authoritative. Missing and fractional values are omitted and fractional values are reported per record.",
        "workCentreLabelCandidate is preserved in the review CSV but not ingested: usesMachineInstance requires a Machine individual, and a text label is not a verified Machine instance.",
        "executesProcess is omitted because no reusable ProductionProcess identifier is present.",
    ])
    succeeded = _ingest_rows(client, "ProcessExecution", records, process_executions, report)
    ingested_by_id = {item["recordId"]: item for item in report["ingested"]}
    reverse_by_work_order: dict[str, list[tuple[dict[str, str], dict[str, Any]]]] = defaultdict(list)
    for item in succeeded:
        reverse_by_work_order[item["workOrderName"]].append((
            _object_property("includesExecution", item["individualName"]), item
        ))
    for work_order_name, entries in reverse_by_work_order.items():
        try:
            client.add_object_properties("WorkOrder", work_order_name, [entry[0] for entry in entries])
            for _, item in entries:
                ingested_by_id[item["individualName"]].setdefault("relationships", []).append({
                    "property": "includesExecution",
                    "target": work_order_name,
                    "status": "linked",
                })
        except Exception as exc:
            for _, item in entries:
                ingested_by_id[item["individualName"]].setdefault("relationships", []).append({
                    "property": "includesExecution",
                    "target": work_order_name,
                    "status": "failed",
                    "reason": str(exc),
                })
                report["relationshipFailures"].append({
                    "sourceRow": item["sourceRow"],
                    "recordId": item["individualName"],
                    "target": work_order_name,
                    "property": "includesExecution",
                    "reason": str(exc),
                    "sourceData": item.get("sourceData"),
                })
    return _finish(report)


def _ontology_datetime(value: str, field: str) -> str | None:
    """Parse common source date formats and normalize them to xsd:dateTime."""
    if not value:
        return None
    normalized = value.strip()
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        parsed = None

    if parsed is None:
        # The reviewed export includes US-style M/D/YYYY values such as
        # 1/7/2026. Try month-first before day-first so ambiguous slash dates
        # follow the source export's convention. If the first component is
        # over 12, month-first cannot match and day-first is used instead.
        accepted_formats = (
            "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p",
            "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
            "%m/%d/%y %I:%M:%S %p", "%m/%d/%y %I:%M %p",
            "%m/%d/%y %H:%M:%S", "%m/%d/%y %H:%M",
            "%m/%d/%Y", "%m/%d/%y",
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
            "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M", "%d/%m/%y",
            "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
            "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y",
            "%d.%m.%y", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
            "%d-%m-%Y", "%d-%m-%y",
        )
        for date_format in accepted_formats:
            try:
                parsed = datetime.strptime(normalized, date_format)
                break
            except ValueError:
                continue

    if parsed is None:
        raise ValueError(
            f"{field} value {value!r} is not a supported date/date-time; "
            "expected ISO, M/D/YYYY, D/M/YYYY, D.M.YYYY, or a supported timestamp format"
        )
    return parsed.isoformat(timespec="auto")


def _execution_timestamp(value: str, field: str) -> str | None:
    """Format reviewed dates for the ProcessExecution xsd:dateTimeStamp range.

    Review candidates are date-only. Midnight UTC is used as a storage
    convention to satisfy the timezone-required datatype; it does not claim
    that a clock time was observed.
    """
    normalized = _ontology_datetime(value, field)
    if normalized is None:
        return None
    if normalized.endswith("Z"):
        return normalized
    if normalized.endswith("+00:00"):
        return normalized[:-6] + "Z"
    if normalized.endswith("T00:00:00"):
        return normalized + "Z"
    raise ValueError(
        f"{field} must include a timezone to satisfy the ontology's xsd:dateTimeStamp range"
    )


def ingest_manufactured_products(content: bytes) -> dict[str, Any]:
    required_headers = {
        "individualName", "hasManufacturedProductID", "isInstanceOfProductType",
        "isProducedByWorkOrder", "producedAtFactory", "hasManufacturedQuantity",
        "hasProductionDate",
    }
    rows, _ = _read_csv(content, required_headers)
    report = _base_report("ManufacturedProduct", len(rows))
    client = BlueprintClient()
    client.validate_blueprint(
        "ManufacturedProduct",
        data_properties={"hasManufacturedProductID", "hasManufacturedQuantity", "hasProductionDate"},
        object_properties={"isInstanceOfProductType", "isProducedByWorkOrder", "producedAtFactory", "isStoredIn"},
    )
    client.validate_blueprint("ProductType", data_properties=set(), object_properties={"hasManufacturedProduct"})
    client.validate_blueprint("WorkOrder", data_properties=set(), object_properties={"appliesToProduct"})
    client.validate_blueprint("Factory", data_properties=set(), object_properties={"manufacturesProduct"})
    client.validate_blueprint("Warehousing", data_properties=set(), object_properties={"storesProduct"})
    product_types = client.list_names("ProductType")
    work_orders = client.list_names("WorkOrder")
    factories = client.list_names("Factory")
    warehouses = client.list_names("Warehousing")
    manufactured_products = client.list_names("ManufacturedProduct")
    records = []
    for row in rows:
        source_row = int(row["__sourceRow"])
        name = _value(row, "individualName")
        try:
            name = _required(name, "individualName")
            product_id = _required(_value(row, "hasManufacturedProductID"), "hasManufacturedProductID")
            if name != product_id:
                raise ValueError("individualName and hasManufacturedProductID must match")
            if not re.fullmatch(r"MEDWOOD_ManufacturedProduct[A-Za-z0-9_-]+_[0-9a-f]{16}_\d+", name):
                raise ValueError("ManufacturedProduct ID must contain the transaction number, 16-character row hash, and occurrence suffix")
            product_type = _required(_value(row, "isInstanceOfProductType"), "isInstanceOfProductType")
            work_order = _required(_value(row, "isProducedByWorkOrder"), "isProducedByWorkOrder")
            factory = _required(_value(row, "producedAtFactory"), "producedAtFactory")
            for class_name, individual, names in (
                ("ProductType", product_type, product_types),
                ("WorkOrder", work_order, work_orders),
                ("Factory", factory, factories),
            ):
                if individual not in names:
                    raise ValueError(f"Referenced {class_name} {individual!r} does not exist")
            data = [_property("hasManufacturedProductID", product_id)]
            quantity = _number(_value(row, "hasManufacturedQuantity"), "hasManufacturedQuantity", minimum=0)
            if quantity is None:
                raise ValueError("hasManufacturedQuantity is required")
            if not isinstance(quantity, int):
                raise ValueError(
                    "hasManufacturedQuantity must be a whole number because its ontology range is xsd:integer"
                )
            data.append(_property("hasManufacturedQuantity", quantity))
            production_date = _ontology_datetime(_value(row, "hasProductionDate"), "hasProductionDate")
            if production_date is None:
                raise ValueError("hasProductionDate is required")
            data.append(_property("hasProductionDate", production_date))
            objects = [
                _object_property("isInstanceOfProductType", product_type),
                _object_property("isProducedByWorkOrder", work_order),
                _object_property("producedAtFactory", factory),
            ]
            warehouse = _value(row, "isStoredIn")
            if warehouse:
                if warehouse in warehouses:
                    objects.append(_object_property("isStoredIn", warehouse))
                else:
                    report["recordWarnings"].append({
                        "sourceRow": source_row,
                        "recordId": name,
                        "property": "isStoredIn",
                        "value": warehouse,
                        "reason": "No matching Warehousing individual exists; the ManufacturedProduct will be ingested without this relationship.",
                    })
            records.append({
                "sourceRow": source_row,
                "sourceData": _source_data(row),
                "key": name,
                "individualName": name,
                "productTypeName": product_type,
                "workOrderName": work_order,
                "factoryName": factory,
                "warehouseName": warehouse if warehouse in warehouses else None,
                "dataProperties": data,
                "objectProperties": objects,
            })
        except Exception as exc:
            report["rejectedRecords"].append({
                "sourceRow": source_row,
                "recordId": name or None,
                "reason": str(exc),
                "sourceData": _source_data(row),
            })
    records = _deduplicate(records, "key", report["rejectedRecords"])
    report["warnings"].append(
        "Generated ManufacturedProduct IDs identify the prepared transaction row; a source row correction changes its hash and therefore its individual name."
    )
    report["warnings"].extend([
        "hasProductionDate accepts common source date/date-time formats and is normalized to ISO xsd:dateTime; date-only values become midnight without claiming an observed time.",
        "hasManufacturedQuantity has an xsd:integer range. Fractional values are rejected instead of truncated or sent with an incompatible datatype.",
        "Direct links are isInstanceOfProductType, isProducedByWorkOrder, producedAtFactory, and isStoredIn when the matching Warehouse exists. The inverse links are synchronized on ProductType, WorkOrder, Factory, and Warehousing.",
    ])
    succeeded = _ingest_rows(client, "ManufacturedProduct", records, manufactured_products, report)
    ingested_by_id = {item["recordId"]: item for item in report["ingested"]}

    reverse_relations: dict[tuple[str, str, str], list[tuple[dict[str, str], dict[str, Any]]]] = defaultdict(list)
    for item in succeeded:
        pairs = [
            ("ProductType", item["productTypeName"], "hasManufacturedProduct"),
            ("WorkOrder", item["workOrderName"], "appliesToProduct"),
            ("Factory", item["factoryName"], "manufacturesProduct"),
        ]
        if item["warehouseName"]:
            pairs.append(("Warehousing", item["warehouseName"], "storesProduct"))
        for class_name, target_name, property_name in pairs:
            key = (class_name, target_name, property_name)
            reverse_relations[key].append((_object_property(property_name, item["individualName"]), item))
    for (class_name, target_name, property_name), entries in reverse_relations.items():
        try:
            client.add_object_properties(class_name, target_name, [entry[0] for entry in entries])
            for _, item in entries:
                ingested_by_id[item["individualName"]].setdefault("relationships", []).append({
                    "property": property_name,
                    "target": target_name,
                    "status": "linked",
                    "direction": "inverse",
                })
        except Exception as exc:
            for _, item in entries:
                ingested_by_id[item["individualName"]].setdefault("relationships", []).append({
                    "property": property_name,
                    "target": target_name,
                    "status": "failed",
                    "direction": "inverse",
                    "reason": str(exc),
                })
                report["relationshipFailures"].append({
                    "sourceRow": item["sourceRow"],
                    "recordId": item["individualName"],
                    "target": target_name,
                    "property": property_name,
                    "reason": str(exc),
                    "sourceData": item.get("sourceData"),
                })
    return _finish(report)
