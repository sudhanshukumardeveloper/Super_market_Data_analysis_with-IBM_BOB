"""
analytics.py
------------
Descriptive analytics functions for the supermarket sales dataset.

All functions accept a pandas DataFrame (as returned by data_loader.load_data())
and return summary DataFrames ready for display or charting.

Public API
----------
summary_by_branch(df)          -> DataFrame  totals, averages, txn counts per branch
summary_by_city(df)            -> DataFrame
summary_by_category(df)        -> DataFrame
summary_by_payment(df)         -> DataFrame
summary_by_customer_type(df)   -> DataFrame
summary_by_gender(df)          -> DataFrame
monthly_trend(df)              -> DataFrame  monthly sales/transactions over time
top_products(df, n=10)         -> DataFrame  top-n products by total revenue
rating_by_category(df)         -> DataFrame  avg rating per category
rating_by_branch(df)           -> DataFrame  avg rating per branch
hourly_or_weekday_breakdown(df)-> DataFrame  transactions by day-of-week
overall_kpis(df)               -> dict       scalar headline numbers
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sales_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    Generic groupby on a single column.
    Returns: group_col | Total Sales | Avg Sale | Transactions | Avg Rating
    """
    agg = (
        df.groupby(group_col, sort=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Avg_Sale=("Sales", "mean"),
            Transactions=("Invoice ID", "count"),
            Avg_Rating=("Rating", "mean"),
            Avg_Unit_Price=("Unit Price", "mean"),
            Total_Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    agg["Total_Sales"] = agg["Total_Sales"].round(2)
    agg["Avg_Sale"] = agg["Avg_Sale"].round(2)
    agg["Avg_Rating"] = agg["Avg_Rating"].round(2)
    agg["Avg_Unit_Price"] = agg["Avg_Unit_Price"].round(2)
    agg = agg.rename(columns={
        "Total_Sales":    "Total Sales (Rs.)",
        "Avg_Sale":       "Avg Sale (Rs.)",
        "Transactions":   "Transactions",
        "Avg_Rating":     "Avg Rating",
        "Avg_Unit_Price": "Avg Unit Price (Rs.)",
        "Total_Quantity": "Total Quantity Sold",
    })
    return agg.sort_values("Total Sales (Rs.)", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Per-dimension summaries
# ---------------------------------------------------------------------------

def summary_by_branch(df: pd.DataFrame) -> pd.DataFrame:
    """Total/average sales, transactions, and ratings grouped by Branch."""
    return _sales_summary(df, "Branch")


def summary_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """Total/average sales, transactions, and ratings grouped by City."""
    return _sales_summary(df, "City")


def summary_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Total/average sales, transactions, and ratings grouped by Product Category."""
    return _sales_summary(df, "Category")


def summary_by_payment(df: pd.DataFrame) -> pd.DataFrame:
    """Total/average sales, transactions, and ratings grouped by Payment method."""
    return _sales_summary(df, "Payment")


def summary_by_customer_type(df: pd.DataFrame) -> pd.DataFrame:
    """Total/average sales, transactions, and ratings grouped by Customer Type."""
    return _sales_summary(df, "Customer Type")


def summary_by_gender(df: pd.DataFrame) -> pd.DataFrame:
    """Total/average sales, transactions, and ratings grouped by Gender."""
    return _sales_summary(df, "Gender")


# ---------------------------------------------------------------------------
# Trend analysis
# ---------------------------------------------------------------------------

def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Monthly aggregation of total sales and transaction count, sorted by month.
    Returns: Month | Total Sales (Rs.) | Transactions | Avg Sale (Rs.)
    """
    trend = (
        df.groupby("Month", sort=True)
        .agg(
            Total_Sales=("Sales", "sum"),
            Transactions=("Invoice ID", "count"),
            Avg_Sale=("Sales", "mean"),
        )
        .reset_index()
    )
    trend["Total_Sales"] = trend["Total_Sales"].round(2)
    trend["Avg_Sale"] = trend["Avg_Sale"].round(2)
    trend = trend.rename(columns={
        "Total_Sales":  "Total Sales (Rs.)",
        "Transactions": "Transactions",
        "Avg_Sale":     "Avg Sale (Rs.)",
    })
    return trend.sort_values("Month").reset_index(drop=True)


def weekday_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transaction count and total sales broken down by day of week.
    Days are sorted Mon–Sun.
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    breakdown = (
        df.groupby("Day of Week", sort=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Transactions=("Invoice ID", "count"),
        )
        .reindex(day_order, fill_value=0)
        .reset_index()
    )
    breakdown["Total_Sales"] = breakdown["Total_Sales"].round(2)
    breakdown = breakdown.rename(columns={
        "Day of Week":  "Day of Week",
        "Total_Sales":  "Total Sales (Rs.)",
        "Transactions": "Transactions",
    })
    return breakdown


# ---------------------------------------------------------------------------
# Product-level analysis
# ---------------------------------------------------------------------------

def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Top-n products by total revenue.
    Returns: Product | Category | Total Sales (Rs.) | Transactions | Avg Unit Price (Rs.)
    """
    prod = (
        df.groupby(["Product", "Category"], sort=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Transactions=("Invoice ID", "count"),
            Avg_Unit_Price=("Unit Price", "mean"),
        )
        .reset_index()
    )
    prod["Total_Sales"] = prod["Total_Sales"].round(2)
    prod["Avg_Unit_Price"] = prod["Avg_Unit_Price"].round(2)
    prod = prod.rename(columns={
        "Total_Sales":    "Total Sales (Rs.)",
        "Transactions":   "Transactions",
        "Avg_Unit_Price": "Avg Unit Price (Rs.)",
    })
    return prod.sort_values("Total Sales (Rs.)", ascending=False).head(n).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Rating analysis
# ---------------------------------------------------------------------------

def rating_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Average customer rating per product category, sorted descending."""
    rating = (
        df.groupby("Category")["Rating"]
        .agg(["mean", "count", "std"])
        .reset_index()
    )
    rating.columns = ["Category", "Avg Rating", "Review Count", "Rating Std Dev"]
    rating["Avg Rating"] = rating["Avg Rating"].round(2)
    rating["Rating Std Dev"] = rating["Rating Std Dev"].round(2)
    return rating.sort_values("Avg Rating", ascending=False).reset_index(drop=True)


def rating_by_branch(df: pd.DataFrame) -> pd.DataFrame:
    """Average customer rating per branch, sorted descending."""
    rating = (
        df.groupby("Branch")["Rating"]
        .agg(["mean", "count", "std"])
        .reset_index()
    )
    rating.columns = ["Branch", "Avg Rating", "Review Count", "Rating Std Dev"]
    rating["Avg Rating"] = rating["Avg Rating"].round(2)
    rating["Rating Std Dev"] = rating["Rating Std Dev"].round(2)
    return rating.sort_values("Avg Rating", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

def overall_kpis(df: pd.DataFrame) -> dict:
    """
    Return a dict of scalar headline KPIs for dashboard cards.
    """
    return {
        "total_revenue":      round(float(df["Sales"].sum()), 2),
        "total_transactions": int(len(df)),
        "avg_transaction":    round(float(df["Sales"].mean()), 2),
        "avg_rating":         round(float(df["Rating"].mean()), 2),
        "total_quantity_sold":int(df["Quantity"].sum()),
        "top_category":       str(df.groupby("Category")["Sales"].sum().idxmax()),
        "top_branch":         str(df.groupby("Branch")["Sales"].sum().idxmax()),
        "top_city":           str(df.groupby("City")["Sales"].sum().idxmax()),
        "top_payment":        str(df.groupby("Payment")["Sales"].sum().idxmax()),
        "date_range_start":   str(df["Date"].min().date()),
        "date_range_end":     str(df["Date"].max().date()),
    }
