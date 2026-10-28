"""Aggregate MEDWOOD workbooks and export Work Order review CSV files.

The function deliberately preserves review status for fields whose meaning has
not been confirmed. The command line writes work_orders_review.csv,
work_orders_issues.csv, and performance_rows_missing_order_id.csv.

Requires pandas and openpyxl (``pip install pandas openpyxl``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_TRANSACTIONS_FILE = "Transactions Jan-May-2026.xlsx"
DEFAULT_PERFORMANCE_FILE = "Production work performance Jan-May-2026 AUTO (2).xlsx"


def _text_id(value: Any) -> str | None:
    """Normalize Excel identifiers without turning integral numbers into '123.0'."""
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip() or None


def _number(value: Any) -> int | float | None:
    if pd.isna(value):
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def aggregate_work_orders(
    transactions_path: str | Path = DEFAULT_TRANSACTIONS_FILE,
    performance_path: str | Path = DEFAULT_PERFORMANCE_FILE,
    *,
    transactions_sheet: str | int = 0,
    performance_sheet: str | int = 0,
) -> list[dict[str, Any]]:
    """Return one JSON-serializable record per observed Work Order.

    Work Order IDs are the normalized union of ``Performance.Producción`` and
    ``Transactions.Número`` on rows whose ``Referencia`` is ``Producción``.
    The latter rows provide a candidate product code. Transaction movement
    quantities are not used as requested or completed quantities.

    Candidate date and requested quantity fields remain explicitly labeled
    because their source semantics have not been confirmed. The sum of
    ``Piezas Buenas`` is exposed only as a diagnostic; it is not mapped to
    completed quantity because rows may count output at multiple stations.
    """
    transactions_path = Path(transactions_path)
    performance_path = Path(performance_path)
    if not transactions_path.is_file():
        raise FileNotFoundError(f"Transactions workbook not found: {transactions_path}")
    if not performance_path.is_file():
        raise FileNotFoundError(f"Performance workbook not found: {performance_path}")

    transactions = pd.read_excel(transactions_path, sheet_name=transactions_sheet)
    performance = pd.read_excel(performance_path, sheet_name=performance_sheet)

    required_transactions = {"Número", "Referencia", "Código de artículo"}
    required_performance = {
        "Producción", "Nº Piezas Teórico", "Fecha", "Piezas Buenas", "Centro de Trabajo"
    }
    missing_transactions = required_transactions - set(transactions.columns)
    missing_performance = required_performance - set(performance.columns)
    if missing_transactions or missing_performance:
        problems = []
        if missing_transactions:
            problems.append(f"Transactions missing columns: {sorted(missing_transactions)}")
        if missing_performance:
            problems.append(f"Performance missing columns: {sorted(missing_performance)}")
        raise ValueError("; ".join(problems))

    # Normalize keys before grouping. Aggregate separately before combining so
    # repeated transaction movements cannot multiply performance quantities.
    performance = performance.copy()
    performance["_work_order_id"] = performance["Producción"].map(_text_id)
    performance = performance[performance["_work_order_id"].notna()]

    perf_records: dict[str, dict[str, Any]] = {}
    for work_order_id, rows in performance.groupby("_work_order_id", sort=False):
        quantities = pd.to_numeric(rows["Nº Piezas Teórico"], errors="coerce").dropna()
        unique_quantities = sorted(set(float(value) for value in quantities))
        dates = pd.to_datetime(rows["Fecha"], errors="coerce").dropna()
        good_pieces = pd.to_numeric(rows["Piezas Buenas"], errors="coerce").dropna()

        perf_records[work_order_id] = {
            "requested_quantity": unique_quantities[0] if len(unique_quantities) == 1 else None,
            "requested_quantity_source_values": [_number(value) for value in unique_quantities],
            "first_recorded_date_candidate": dates.min().date().isoformat() if not dates.empty else None,
            "last_recorded_date_candidate": dates.max().date().isoformat() if not dates.empty else None,
            # Diagnostic only: one order can appear at several stations, so
            # this sum may count the same physical pieces at multiple stages.
            "unvalidated_good_pieces_sum": _number(good_pieces.sum()) if not good_pieces.empty else None,
            "performance_row_count": int(len(rows)),
            "distinct_station_count": int(rows["Centro de Trabajo"].nunique(dropna=True)),
        }

    production_movements = transactions[
        transactions["Referencia"].astype("string").str.strip().eq("Producción")
    ].copy()
    production_movements["_work_order_id"] = production_movements["Número"].map(_text_id)
    production_movements["_product_code"] = production_movements["Código de artículo"].map(_text_id)
    production_movements = production_movements[
        production_movements["_work_order_id"].notna()
    ]

    product_codes: dict[str, list[str]] = {}
    for work_order_id, rows in production_movements.groupby("_work_order_id", sort=False):
        product_codes[work_order_id] = sorted(
            set(rows["_product_code"].dropna().tolist())
        )

    work_order_ids = sorted(set(perf_records) | set(product_codes))
    result: list[dict[str, Any]] = []
    for work_order_id in work_order_ids:
        perf = perf_records.get(work_order_id, {})
        codes = product_codes.get(work_order_id, [])
        source_values = perf.get("requested_quantity_source_values", [])
        issues: list[str] = []
        if not perf:
            issues.append("No matching Performance row; quantity and date fields unavailable.")
        if len(source_values) > 1:
            issues.append("Conflicting theoretical quantities within this Work Order.")
        if len(codes) != 1:
            issues.append(
                "Expected one product code from Transactions rows with Referencia='Producción'; "
                f"found {len(codes)}."
            )
        requested_quantity = perf.get("requested_quantity")
        diagnostic_good_sum = perf.get("unvalidated_good_pieces_sum")
        if (
            requested_quantity is not None
            and diagnostic_good_sum is not None
            and diagnostic_good_sum > requested_quantity
        ):
            issues.append(
                "Sum of Piezas Buenas across Performance rows exceeds requested quantity; "
                "review process/station grain before interpreting it as completed quantity."
            )

        result.append({
            "hasWorkOrderID": work_order_id,
            "hasRequestedQuantity": _number(perf.get("requested_quantity")),
            "requestedQuantityMappingStatus": "candidate: Nº Piezas Teórico; one distinct value per order required",
            "appliesToProductCodeCandidate": codes[0] if len(codes) == 1 else None,
            "productCodeMappingStatus": "candidate: Código de artículo on Referencia='Producción' transaction rows",
            "hasActualStartDateCandidate": perf.get("first_recorded_date_candidate"),
            "hasActualEndDateCandidate": perf.get("last_recorded_date_candidate"),
            "actualDateMappingStatus": "candidate only: first/last recorded dates are not confirmed actual start/end",
            "hasCompletedQuantityCandidate": None,
            "completedQuantityMappingStatus": "unmapped pending confirmation: Performance rows can cover multiple process stations; row sum is diagnostic only",
            "unvalidatedSumPiezasBuenasAcrossPerformanceRows": _number(perf.get("unvalidated_good_pieces_sum")),
            "performanceRowCount": perf.get("performance_row_count", 0),
            "distinctPerformanceStations": perf.get("distinct_station_count", 0),
            "unmapped": {
                "hasPlannedStartDate": None,
                "hasPlannedEndDate": None,
                "hasWorkOrderType": None,
                "hasWorkOrderStatus": None,
                "hasWorkOrderNote": None,
                "hasPriorityLevel": None,
            },
            "reviewIssues": issues,
        })

    return result


def write_work_order_csvs(
    output_dir: str | Path = "work_order_outputs",
    transactions_path: str | Path = DEFAULT_TRANSACTIONS_FILE,
    performance_path: str | Path = DEFAULT_PERFORMANCE_FILE,
    *,
    transactions_sheet: str | int = 0,
    performance_sheet: str | int = 0,
) -> dict[str, Path]:
    """Write the three Excel-friendly CSV reports and return their paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = aggregate_work_orders(
        transactions_path,
        performance_path,
        transactions_sheet=transactions_sheet,
        performance_sheet=performance_sheet,
    )

    # Flatten candidate values and unmapped ontology properties for easy review
    # in Excel and straightforward ingestion by a future endpoint.
    review_rows = []
    issue_rows = []
    for record in records:
        review_rows.append({
            "hasWorkOrderID": record["hasWorkOrderID"],
            "hasRequestedQuantity": record["hasRequestedQuantity"],
            "requestedQuantityMappingStatus": record["requestedQuantityMappingStatus"],
            "appliesToProductCodeCandidate": record["appliesToProductCodeCandidate"],
            "productCodeMappingStatus": record["productCodeMappingStatus"],
            "hasActualStartDateCandidate": record["hasActualStartDateCandidate"],
            "hasActualEndDateCandidate": record["hasActualEndDateCandidate"],
            "actualDateMappingStatus": record["actualDateMappingStatus"],
            "hasCompletedQuantityCandidate": record["hasCompletedQuantityCandidate"],
            "completedQuantityMappingStatus": record["completedQuantityMappingStatus"],
            "unvalidatedSumPiezasBuenasAcrossPerformanceRows": record["unvalidatedSumPiezasBuenasAcrossPerformanceRows"],
            "performanceRowCount": record["performanceRowCount"],
            "distinctPerformanceStations": record["distinctPerformanceStations"],
            **record["unmapped"],
            "reviewIssues": " | ".join(record["reviewIssues"]),
        })
        for issue in record["reviewIssues"]:
            if "No matching Performance row" in issue:
                issue_code = "missing_performance_rows"
            elif "Conflicting theoretical quantities" in issue:
                issue_code = "conflicting_requested_quantity"
            elif "Expected one product code" in issue:
                issue_code = "product_code_cardinality"
            elif "Sum of Piezas Buenas across Performance rows exceeds requested quantity" in issue:
                issue_code = "good_piece_sum_exceeds_requested_quantity"
            else:
                issue_code = "review_required"
            issue_rows.append({
                "work_order_id": record["hasWorkOrderID"],
                "issue_code": issue_code,
                "issue": issue,
            })

    performance = pd.read_excel(performance_path, sheet_name=performance_sheet)
    missing_id_rows = performance[performance["Producción"].map(_text_id).isna()].copy()
    missing_id_rows.insert(0, "source_excel_row", missing_id_rows.index + 2)

    paths = {
        "work_orders_review": output_dir / "work_orders_review.csv",
        "work_orders_issues": output_dir / "work_orders_issues.csv",
        "performance_rows_missing_order_id": output_dir / "performance_rows_missing_order_id.csv",
    }
    pd.DataFrame(review_rows).to_csv(paths["work_orders_review"], index=False, encoding="utf-8-sig")
    pd.DataFrame(issue_rows, columns=["work_order_id", "issue_code", "issue"]).to_csv(
        paths["work_orders_issues"], index=False, encoding="utf-8-sig"
    )
    missing_id_rows.to_csv(paths["performance_rows_missing_order_id"], index=False, encoding="utf-8-sig")
    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", default=DEFAULT_TRANSACTIONS_FILE)
    parser.add_argument("--performance", default=DEFAULT_PERFORMANCE_FILE)
    parser.add_argument("--output-dir", default="work_order_outputs")
    args = parser.parse_args()
    for name, path in write_work_order_csvs(
        args.output_dir,
        args.transactions,
        args.performance,
    ).items():
        print(f"{name}: {path.resolve()}")
