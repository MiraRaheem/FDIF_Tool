
from pathlib import Path
from typing import Any

import pandas as pd


def read_excel_records(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Read an Excel export whose first row contains the column headers.

    Returns one dictionary per non-empty row.
    """
    df = pd.read_excel(file_path, dtype=object)

    # Remove completely empty rows and columns.
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # Normalize column names without changing their meaning.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # Remove accidental whitespace from string values.
    for column in df.columns:
        df[column] = df[column].map(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

    # Convert missing values to None for easier JSON handling.
    df = df.astype(object).where(pd.notna(df), None)

    return df.to_dict(orient="records")


def read_suppliers(file_path: str | Path) -> list[dict[str, Any]]:
    return read_excel_records(file_path)


def read_customers(file_path: str | Path) -> list[dict[str, Any]]:
    return read_excel_records(file_path)


def read_items(file_path: str | Path) -> list[dict[str, Any]]:
    return read_excel_records(file_path)




def read_companies(file_path: str | Path) -> list[dict[str, Any]]:
    """Read a Budatech Company Excel export."""
    return read_excel_records(file_path)
