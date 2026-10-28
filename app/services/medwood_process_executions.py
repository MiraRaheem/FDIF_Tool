"""Build ProcessExecution review, issues, and summary outputs from MEDWOOD data.

One ProcessExecution candidate is created per distinct ``Trabajo`` source ID.
Rows repeated under the same ID are treated as dated reports for that execution.
Aggregated duration and quantity values remain candidates until MEDWOOD confirms
that the row-level values are incremental.

Requires pandas and openpyxl (``pip install pandas openpyxl``).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_PERFORMANCE_FILE = "Production work performance Jan-May-2026 AUTO (2).xlsx"
DEFAULT_WORK_ORDERS_FILE = Path("work_order_outputs") / "work_orders_review.csv"
DEFAULT_OUTPUT_DIR = "process_execution_outputs"


def _identifier(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _num(value: Any) -> int | float | None:
    if pd.isna(value):
        return None
    value = round(float(value), 6)
    return int(value) if value.is_integer() else value


def _unique_text(values: pd.Series) -> list[str]:
    return sorted({str(v).strip() for v in values.dropna() if str(v).strip()})


def _summary_value(values: pd.Series) -> int | float | None:
    numbers = pd.to_numeric(values, errors="coerce").dropna()
    return _num(numbers.sum()) if not numbers.empty else None


def build_process_execution_outputs(
    performance_path: str | Path = DEFAULT_PERFORMANCE_FILE,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    *,
    performance_sheet: str | int = 0,
    work_orders_path: str | Path | None = DEFAULT_WORK_ORDERS_FILE,
) -> dict[str, Path]:
    """Create the requested review CSV, issues CSV, and JSON report."""
    performance_path = Path(performance_path)
    output_dir = Path(output_dir)
    if not performance_path.is_file():
        raise FileNotFoundError(f"Performance workbook not found: {performance_path}")

    data = pd.read_excel(
        performance_path,
        sheet_name=performance_sheet,
        dtype={"Trabajo": "string", "Producción": "string"},
    )
    required = {
        "Fecha", "Producción", "Trabajo", "Centro de Trabajo", "Trabajo Terminado",
        "Horas Máquina Real", "Piezas Buenas", "Piezas Malas",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Performance workbook missing columns: {sorted(missing)}")

    data = data.copy()
    data["_excel_row"] = data.index + 2
    data["_execution_id"] = data["Trabajo"].map(_identifier)
    data["_work_order_id"] = data["Producción"].map(_identifier)
    data["_date"] = pd.to_datetime(data["Fecha"], errors="coerce")
    fecha_text = data["Fecha"].astype("string").str.strip().str.casefold()
    footer_rows = fecha_text.eq("total") | fecha_text.str.startswith("filtros aplicados", na=False)
    blank_rows = data[list(required)].isna().all(axis=1)
    excluded_nondata_rows = int((footer_rows | blank_rows).sum())
    data = data.loc[~(footer_rows | blank_rows)].copy()
    data["_duration_hours"] = pd.to_numeric(data["Horas Máquina Real"], errors="coerce")
    data["_good"] = pd.to_numeric(data["Piezas Buenas"], errors="coerce")
    data["_defects"] = pd.to_numeric(data["Piezas Malas"], errors="coerce")

    work_order_ids: set[str] | None = None
    work_orders_file_used: str | None = None
    if work_orders_path is not None:
        work_orders_path = Path(work_orders_path)
        if work_orders_path.is_file():
            work_orders = pd.read_csv(work_orders_path, dtype={"hasWorkOrderID": "string"})
            if "hasWorkOrderID" not in work_orders.columns:
                raise ValueError(f"Work Order CSV lacks hasWorkOrderID: {work_orders_path}")
            work_order_ids = {
                value for value in work_orders["hasWorkOrderID"].map(_identifier) if value
            }
            work_orders_file_used = str(work_orders_path)

    review_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []

    def add_issue(
        *, scope: str, source_row: int | None, execution_id: str | None,
        work_order_id: str | None, code: str, field: str, value: Any, handling: str,
    ) -> None:
        issue_rows.append({
            "issue_scope": scope,
            "source_excel_row": source_row,
            "execution_id": execution_id,
            "work_order_id": work_order_id,
            "issue_code": code,
            "source_field": field,
            "source_value": value,
            "handling": handling,
        })

    # Source-row issues retain the location and value needed for manual review.
    for _, row in data.iterrows():
        excel_row = int(row["_excel_row"])
        execution_id = row["_execution_id"]
        work_order_id = row["_work_order_id"]
        if not execution_id:
            add_issue(scope="source_row", source_row=excel_row, execution_id=None,
                      work_order_id=work_order_id, code="missing_execution_id", field="Trabajo",
                      value=None, handling="Cannot create a ProcessExecution without the source ID.")
        if not work_order_id:
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=None, code="missing_work_order_id", field="Producción",
                      value=None, handling="Work Order relationship is unavailable for this row.")
        elif work_order_ids is not None and work_order_id not in work_order_ids:
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=work_order_id, code="unresolved_work_order_id", field="Producción",
                      value=work_order_id, handling="No matching hasWorkOrderID in the supplied Work Order review.")

        if pd.isna(row["_date"]):
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=work_order_id, code="missing_or_invalid_execution_date", field="Fecha",
                      value=row["Fecha"], handling="No date candidate can be derived from this row.")

        hours = row["_duration_hours"]
        if pd.isna(hours):
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=work_order_id, code="missing_actual_machine_hours", field="Horas Máquina Real",
                      value=row["Horas Máquina Real"], handling="Keep missing; do not convert to zero.")
        elif hours <= 0:
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=work_order_id, code="nonpositive_actual_machine_hours", field="Horas Máquina Real",
                      value=_num(hours), handling="Excluded from positive-hours duration candidate; review source value.")

        for field, parsed, code in (
            ("Piezas Buenas", row["_good"], "missing_good_piece_quantity"),
            ("Piezas Malas", row["_defects"], "missing_defect_quantity"),
        ):
            if pd.isna(parsed):
                add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                          work_order_id=work_order_id, code=code, field=field,
                          value=row[field], handling="Keep missing; do not treat as zero.")

        status = str(row["Trabajo Terminado"]).strip().upper() if not pd.isna(row["Trabajo Terminado"]) else ""
        if status == "NO":
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=work_order_id, code="execution_not_marked_complete", field="Trabajo Terminado",
                      value="NO", handling="Not mapped; source value does not distinguish Running, Paused, or other status.")
        elif not status:
            add_issue(scope="source_row", source_row=excel_row, execution_id=execution_id,
                      work_order_id=work_order_id, code="missing_execution_status", field="Trabajo Terminado",
                      value=None, handling="Leave execution status unmapped.")

    identified = data[data["_execution_id"].notna()]
    for execution_id, rows in identified.groupby("_execution_id", sort=True):
        order_ids = _unique_text(rows["_work_order_id"])
        stations = _unique_text(rows["Centro de Trabajo"])
        statuses = _unique_text(rows["Trabajo Terminado"].astype("string").str.upper())
        dates = rows["_date"].dropna()

        if len(order_ids) > 1:
            add_issue(scope="execution", source_row=None, execution_id=execution_id,
                      work_order_id=None, code="conflicting_work_order_ids", field="Producción",
                      value=" | ".join(order_ids), handling="Do not assign a single Work Order until the conflict is resolved.")
        if len(stations) > 1:
            add_issue(scope="execution", source_row=None, execution_id=execution_id,
                      work_order_id=order_ids[0] if len(order_ids) == 1 else None,
                      code="multiple_work_centres_for_execution", field="Centro de Trabajo",
                      value=" | ".join(stations), handling="Review execution grouping; one Trabajo maps to multiple work centres.")
        if len(statuses) > 1:
            add_issue(scope="execution", source_row=None, execution_id=execution_id,
                      work_order_id=order_ids[0] if len(order_ids) == 1 else None,
                      code="conflicting_execution_status", field="Trabajo Terminado",
                      value=" | ".join(statuses), handling="Leave status unmapped until source status conflict is resolved.")

        hours = rows["_duration_hours"]
        positive_hours = hours[hours > 0].dropna()
        output_values = rows["_good"].dropna()
        defect_values = rows["_defects"].dropna()
        status = statuses[0] if len(statuses) == 1 else None
        status_candidate = "Completed" if status == "SI" else None
        start_date_candidate = dates.min().date().isoformat() if not dates.empty else None
        end_date_candidate = dates.max().date().isoformat() if not dates.empty else None
        work_order_id = order_ids[0] if len(order_ids) == 1 else None
        if work_order_id is None:
            work_order_status = "missing or conflicting source Work Order ID"
        elif work_order_ids is None:
            work_order_status = "candidate; cross-check against Work Order instances before ingestion"
        elif work_order_id in work_order_ids:
            work_order_status = "resolved against supplied hasWorkOrderID set"
        else:
            work_order_status = "unresolved against supplied hasWorkOrderID set"

        output_missing = int(rows["_good"].isna().sum())
        defect_missing = int(rows["_defects"].isna().sum())
        duration_invalid = int((rows["_duration_hours"].isna() | (rows["_duration_hours"] <= 0)).sum())
        review_rows.append({
            "hasExecutionID": execution_id,
            "executionIDMappingStatus": "source ID: Performance.Trabajo; one review record per distinct ID",
            "isPartOfWorkOrder": work_order_id,
            "workOrderLinkMappingStatus": work_order_status,
            "executesProcess": None,
            "processLinkMappingStatus": "unmapped: Trabajo identifies this execution; no confirmed reusable ProductionProcess ID",
            "hasExecutionStartTimeCandidate": start_date_candidate,
            "executionStartTimeMappingStatus": "date-only candidate: earliest recorded Fecha for this Trabajo; not confirmed as actual start; no clock time",
            "hasExecutionEndTimeCandidate": end_date_candidate,
            "executionEndTimeMappingStatus": "date-only candidate: latest recorded Fecha for this Trabajo; not confirmed as actual end; no clock time",
            "hasActualDurationMinutesCandidate": _num(positive_hours.sum() * 60) if not positive_hours.empty else None,
            "durationSourceRows": int(len(positive_hours)),
            "durationInvalidOrMissingRows": duration_invalid,
            "actualDurationMappingStatus": "candidate: sum of positive Horas Máquina Real × 60 within Trabajo; confirm additivity and review invalid rows",
            "hasOutputQuantityCandidate": _num(output_values.sum()) if not output_values.empty else None,
            "outputQuantitySourceRows": int(len(output_values)),
            "outputQuantityMissingRows": output_missing,
            "outputQuantityMappingStatus": "candidate: sum of observed Piezas Buenas within Trabajo; confirm dated rows are incremental",
            "hasDefectQuantityCandidate": _num(defect_values.sum()) if not defect_values.empty else None,
            "defectQuantitySourceRows": int(len(defect_values)),
            "defectQuantityMissingRows": defect_missing,
            "defectQuantityMappingStatus": "candidate: sum of observed Piezas Malas within Trabajo; confirm dated rows are incremental",
            "hasExecutionStatusCandidate": status_candidate,
            "executionStatusMappingStatus": "SI → Completed; NO is unmapped; review conflicting or missing values",
            "workCentreLabelCandidate": stations[0] if len(stations) == 1 else " | ".join(stations) or None,
            "workCentreMappingStatus": "label only; not linked to Machine or Station instance",
            "sourceRowCount": int(len(rows)),
            "hasExecutionNote": None,
            "consumesComponentInput": None,
            "consumesMaterialInput": None,
            "producesExecutionOutput": None,
            "usesMachineInstance": None,
            "performedByOperator": None,
            "unmappedStatus": "notes, input/output instance links, machine instance, operator identity; Nº Operarios is only a count",
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    review_path = output_dir / "medwood_process_executions_review.csv"
    issues_path = output_dir / "medwood_process_executions_issues.csv"
    report_path = output_dir / "medwood_process_executions_report.json"
    pd.DataFrame(review_rows).to_csv(review_path, index=False, encoding="utf-8-sig")
    issue_columns = [
        "issue_scope", "source_excel_row", "execution_id", "work_order_id",
        "issue_code", "source_field", "source_value", "handling",
    ]
    pd.DataFrame(issue_rows, columns=issue_columns).to_csv(
        issues_path, index=False, encoding="utf-8-sig"
    )

    status_counts = data["Trabajo Terminado"].astype("string").str.strip().str.upper().value_counts(dropna=False)
    execution_status_counts = identified.groupby("_execution_id")["Trabajo Terminado"].agg(
        lambda s: " | ".join(_unique_text(s.astype("string").str.upper())) or "missing"
    ).value_counts()
    report = {
        "source_file": str(performance_path),
        "work_order_review_file": work_orders_file_used,
        "source_rows": int(len(data)),
        "excluded_nondata_footer_rows": excluded_nondata_rows,
        "distinct_nonblank_execution_ids": int(identified["_execution_id"].nunique()),
        "source_rows_missing_execution_id": int(data["_execution_id"].isna().sum()),
        "execution_review_records": int(len(review_rows)),
        "issues": {
            "total_issue_rows": int(len(issue_rows)),
            "by_code": {str(k): int(v) for k, v in pd.Series([x["issue_code"] for x in issue_rows]).value_counts().items()},
        },
        "source_row_status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "execution_status_counts": {str(k): int(v) for k, v in execution_status_counts.items()},
        "mapping_decisions": {
            "hasExecutionID": "Use Performance.Trabajo directly; aggregate repeated dated rows by this ID.",
            "isPartOfWorkOrder": "Use Performance.Producción; cross-check against WorkOrder.hasWorkOrderID when supplied.",
            "executesProcess": "Unmapped pending a reusable ProductionProcess identifier; do not reuse Trabajo.",
            "hasExecutionStartTime": "Earliest recorded Fecha per Trabajo; date-only candidate, not confirmed as actual start or timestamp.",
            "hasExecutionEndTime": "Latest recorded Fecha per Trabajo; date-only candidate, not confirmed as actual end or timestamp.",
            "hasActualDurationMinutes": "Positive Horas Máquina Real values summed within Trabajo and converted from hours to minutes; additivity requires confirmation.",
            "hasOutputQuantity": "Observed Piezas Buenas values summed within Trabajo; dated-row increment semantics require confirmation.",
            "hasDefectQuantity": "Observed Piezas Malas values summed within Trabajo; dated-row increment semantics require confirmation.",
            "hasExecutionStatus": "SI maps to Completed; NO and missing values remain unmapped.",
            "workCentreLabel": "Preserved as a label only; not asserted to be a Machine or Station instance.",
        },
        "unmapped_properties": [
            "hasExecutionNote", "consumesComponentInput", "consumesMaterialInput",
            "producesExecutionOutput", "usesMachineInstance", "performedByOperator",
        ],
        "limitations": [
            "Missing quantities are excluded from observed sums but separately counted; sums may be partial.",
            "No completed Work Order total is derived from ProcessExecution outputs.",
            "Date-only earliest/latest report dates are candidates, not confirmed actual boundaries, and are not expanded to invented times.",
        ],
        "output_files": [issues_path.name, report_path.name, review_path.name],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "medwood_process_executions_issues": issues_path,
        "medwood_process_executions_report": report_path,
        "medwood_process_executions_review": review_path,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--performance", default=DEFAULT_PERFORMANCE_FILE)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--work-orders", default=str(DEFAULT_WORK_ORDERS_FILE))
    parser.add_argument("--no-work-order-crosscheck", action="store_true")
    args = parser.parse_args()
    paths = build_process_execution_outputs(
        performance_path=args.performance,
        output_dir=args.output_dir,
        work_orders_path=None if args.no_work_order_crosscheck else args.work_orders,
    )
    for name, path in paths.items():
        print(f"{name}: {path.resolve()}")
