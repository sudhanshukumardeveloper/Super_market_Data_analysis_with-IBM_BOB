"""
data_loader.py
--------------
Handles reading, parsing, and cleaning the supermarket sales dataset.

The source file uses variable-width whitespace padding (not a standard CSV),
so we use a regex-based parser to reliably extract all 13 fields.

Public API
----------
load_data(path: str | Path = None) -> pd.DataFrame
    Returns a fully cleaned DataFrame ready for analysis.

get_cleaning_report(path: str | Path = None) -> dict
    Returns a dict summarising all cleaning operations performed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_BRANCHES: set[str] = {"A", "B", "C", "D"}
VALID_CUSTOMER_TYPES: set[str] = {"Member", "Normal"}
VALID_GENDERS: set[str] = {"Male", "Female"}
VALID_PAYMENTS: set[str] = {"UPI", "Card", "Cash", "Net Banking"}
VALID_CATEGORIES: set[str] = {
    "Dairy", "Grocery", "Fruits", "Snacks",
    "Personal Care", "Vegetables", "Beverages", "Bakery",
}

# Tolerance (Rs.) when checking Sales == Quantity * Unit Price
SALES_TOLERANCE: float = 0.05

# Regex that matches one data row (all 13 fields)
_ROW_PAT = re.compile(
    r"(INV\d+)"                       # Invoice ID
    r"\s+"
    r"(\d{4}-\d{2}-\d{2})"           # Date
    r"\s+"
    r"([A-Z])"                        # Branch
    r"\s+"
    r"(\S+)"                          # City
    r"\s+"
    r"(Member|Normal)"                # Customer Type
    r"\s+"
    r"(Male|Female)"                  # Gender
    r"\s+"
    r"([\w\s]+?)"                     # Product  (non-greedy)
    r"\s{2,}"
    r"([\w\s]+?)"                     # Category (non-greedy)
    r"\s{2,}"
    r"(\d+)"                          # Quantity
    r"\s+"
    r"([\d.]+)"                       # Unit Price
    r"\s+"
    r"(UPI|Card|Cash|Net Banking)"    # Payment
    r"\s+"
    r"([\d.]+)"                       # Rating
    r"\s+"
    r"([\d.]+)"                       # Sales
)

_COL_NAMES = [
    "Invoice ID", "Date", "Branch", "City", "Customer Type",
    "Gender", "Product", "Category", "Quantity", "Unit Price",
    "Payment", "Rating", "Sales",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_raw(path: str | Path) -> tuple[pd.DataFrame, int]:
    """
    Parse the fixed-width/space-padded file line by line using _ROW_PAT.
    Returns (DataFrame, unparseable_row_count).
    """
    path = Path(path)
    records: list[tuple] = []
    skipped = 0

    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n").strip('"').strip()
            if not line:
                continue
            m = _ROW_PAT.search(line)
            if m:
                records.append(m.groups())
            else:
                # Header row or truly unparseable; skip silently
                skipped += 1

    df = pd.DataFrame(records, columns=_COL_NAMES)
    return df, skipped


def _cast_types(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Cast columns to correct dtypes; return (df, list_of_warnings)."""
    warnings: list[str] = []

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad = df["Date"].isna().sum()
    if bad:
        warnings.append(f"{bad} rows with unparseable dates set to NaT.")

    for col in ("Quantity", "Unit Price", "Rating", "Sales"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        bad = df[col].isna().sum()
        if bad:
            warnings.append(f"{bad} non-numeric values in '{col}' coerced to NaN.")

    df["Quantity"] = df["Quantity"].round().astype("Int64")

    return df, warnings


def _handle_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows that are missing any critical field. Returns (df, dropped_count)."""
    critical = ["Invoice ID", "Date", "Branch", "Sales", "Quantity", "Unit Price"]
    before = len(df)
    df = df.dropna(subset=critical)
    return df, before - len(df)


def _validate_categories(df: pd.DataFrame) -> dict[str, list[str]]:
    """Return {col: [unexpected_values]} for all categorical columns."""
    checks = {
        "Branch": VALID_BRANCHES,
        "Customer Type": VALID_CUSTOMER_TYPES,
        "Gender": VALID_GENDERS,
        "Payment": VALID_PAYMENTS,
        "Category": VALID_CATEGORIES,
    }
    return {
        col: df[col][~df[col].isin(valid)].dropna().unique().tolist()
        for col, valid in checks.items()
        if col in df.columns and df[col][~df[col].isin(valid)].dropna().any()
    }


def _validate_sales(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Verify Sales ~= Quantity * Unit Price (within SALES_TOLERANCE Rs.).
    Corrects mismatches in place; returns (df, corrected_count).
    """
    expected = df["Quantity"].astype(float) * df["Unit Price"]
    mask = (df["Sales"] - expected).abs() > SALES_TOLERANCE
    count = int(mask.sum())
    if count:
        df.loc[mask, "Sales"] = expected[mask]
    return df, count


def _remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop duplicate Invoice IDs (keep first). Returns (df, removed_count)."""
    before = len(df)
    df = df.drop_duplicates(subset=["Invoice ID"])
    return df, before - len(df)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_data(path: str | Path = None) -> pd.DataFrame:
    """
    Load, clean, and return the supermarket sales DataFrame.

    Parameters
    ----------
    path : str or Path, optional
        Path to the dataset. Defaults to the bundled data/supermarket_sales.csv.
    """
    if path is None:
        path = Path(__file__).parent.parent / "data" / "supermarket_sales.csv"

    df, _ = _read_raw(path)
    df, _ = _cast_types(df)
    df, _ = _handle_missing(df)
    df, _ = _remove_duplicates(df)
    df, _ = _validate_sales(df)

    # Derived helper columns
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    df["Day of Week"] = df["Date"].dt.day_name()

    return df.reset_index(drop=True)


def get_cleaning_report(path: str | Path = None) -> dict[str, Any]:
    """
    Run the full cleaning pipeline and return a detailed audit report.
    """
    if path is None:
        path = Path(__file__).parent.parent / "data" / "supermarket_sales.csv"

    df, unparseable = _read_raw(path)
    df, type_warnings = _cast_types(df)
    missing_per_col = {k: int(v) for k, v in df.isnull().sum().items()}
    df, dropped = _handle_missing(df)
    category_issues = _validate_categories(df)
    df, dupes = _remove_duplicates(df)
    df, corrected = _validate_sales(df)

    return {
        "total_rows_parsed": len(df) + dropped,
        "total_rows_after_cleaning": len(df),
        "unparseable_rows_skipped": unparseable - 1,  # -1 for header
        "type_warnings": type_warnings,
        "missing_values_per_column": missing_per_col,
        "rows_dropped_missing_critical": dropped,
        "duplicate_rows_removed": dupes,
        "unexpected_category_values": category_issues,
        "sales_calculation_mismatches_corrected": corrected,
    }
