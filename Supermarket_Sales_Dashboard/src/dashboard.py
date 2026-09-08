"""
dashboard.py
------------
Streamlit interactive dashboard for supermarket sales analysis.

Run with:
    streamlit run src/dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable when launched from project root or src/
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import (
    monthly_trend,
    overall_kpis,
    rating_by_branch,
    rating_by_category,
    summary_by_branch,
    summary_by_category,
    summary_by_city,
    summary_by_gender,
    summary_by_payment,
    top_products,
    weekday_breakdown,
)
from data_loader import get_cleaning_report, load_data

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Supermarket Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — modern, clean look
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* Global font & background */
    html, body, [class*="css"] {
        font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
    }

    /* Metric card styling */
    [data-testid="stMetric"] {
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] { color: #57606a; font-size: 13px; }
    [data-testid="stMetricValue"] { color: #1f2328; font-size: 26px; font-weight: 700; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #f0f2f6;
        border-right: 1px solid #e5e7eb;
    }
    section[data-testid="stSidebar"] h2 { color: #1f2328; }

    /* Section headers */
    h2, h3 { color: #1f2328; }

    /* Divider */
    hr { border-color: #e5e7eb; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Loading and cleaning data…")
def get_data() -> pd.DataFrame:
    return load_data()


@st.cache_data(show_spinner=False)
def get_report() -> dict:
    return get_cleaning_report()


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

try:
    df_full = get_data()
except Exception as exc:
    st.error(f"❌ Failed to load dataset: {exc}")
    st.info("Make sure `data/supermarket_sales.csv` exists in the project folder.")
    st.stop()

if df_full.empty:
    st.warning("The dataset loaded but contains no rows. Check the CSV file.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar — filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/shopping-cart.png",
        width=60,
    )
    st.title("🛒 Filters")
    st.markdown("---")

    # Branch
    all_branches = sorted(df_full["Branch"].dropna().unique())
    sel_branches = st.multiselect(
        "Branch",
        options=all_branches,
        default=all_branches,
        help="Filter by store branch (A / B / C / D)",
    )

    # City
    all_cities = sorted(df_full["City"].dropna().unique())
    sel_cities = st.multiselect(
        "City",
        options=all_cities,
        default=all_cities,
        help="Filter by city",
    )

    # Customer Type
    all_ctypes = sorted(df_full["Customer Type"].dropna().unique())
    sel_ctypes = st.multiselect(
        "Customer Type",
        options=all_ctypes,
        default=all_ctypes,
        help="Member or Normal customer",
    )

    # Gender
    all_genders = sorted(df_full["Gender"].dropna().unique())
    sel_genders = st.multiselect(
        "Gender",
        options=all_genders,
        default=all_genders,
    )

    # Category
    all_cats = sorted(df_full["Category"].dropna().unique())
    sel_cats = st.multiselect(
        "Product Category",
        options=all_cats,
        default=all_cats,
    )

    st.markdown("---")
    st.caption("Data quality report")
    with st.expander("View cleaning report"):
        try:
            report = get_report()
            st.json(report)
        except Exception:
            st.write("Report unavailable.")

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

df = df_full.copy()

if sel_branches:
    df = df[df["Branch"].isin(sel_branches)]
if sel_cities:
    df = df[df["City"].isin(sel_cities)]
if sel_ctypes:
    df = df[df["Customer Type"].isin(sel_ctypes)]
if sel_genders:
    df = df[df["Gender"].isin(sel_genders)]
if sel_cats:
    df = df[df["Category"].isin(sel_cats)]

if df.empty:
    st.warning("⚠️ No data matches the selected filters. Please adjust your selections.")
    st.stop()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("## 🛒 Supermarket Sales Dashboard")
st.caption(
    f"Showing **{len(df):,}** of **{len(df_full):,}** transactions "
    f"· {df['Date'].min().date()} → {df['Date'].max().date()}"
)
st.markdown("---")

# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------

kpis = overall_kpis(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Total Revenue",    f"₹{kpis['total_revenue']:,.2f}")
c2.metric("🧾 Transactions",     f"{kpis['total_transactions']:,}")
c3.metric("📦 Avg Transaction",  f"₹{kpis['avg_transaction']:,.2f}")
c4.metric("⭐ Avg Rating",       f"{kpis['avg_rating']:.2f} / 5")
c5.metric("📊 Items Sold",       f"{kpis['total_quantity_sold']:,}")

st.markdown("")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🏆 Top Category", kpis["top_category"])
k2.metric("🏪 Top Branch",   kpis["top_branch"])
k3.metric("🏙 Top City",     kpis["top_city"])
k4.metric("💳 Top Payment",  kpis["top_payment"])

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 1: Monthly Trend + Category Breakdown
# ---------------------------------------------------------------------------

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📈 Monthly Sales Trend")
    try:
        trend_df = monthly_trend(df)
        if trend_df.empty:
            st.info("Not enough data for a monthly trend.")
        else:
            fig_trend = px.line(
                trend_df,
                x="Month",
                y="Total Sales (Rs.)",
                markers=True,
                text="Transactions",
                color_discrete_sequence=["#3b82d4"],
                labels={"Total Sales (Rs.)": "Revenue (Rs.)", "Month": ""},
            )
            fig_trend.update_traces(
                textposition="top center",
                line=dict(width=2.5),
                marker=dict(size=8),
            )
            fig_trend.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="white",
                paper_bgcolor="white",
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0"),
                hovermode="x unified",
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with col_right:
    st.subheader("🗂 Revenue by Category")
    try:
        cat_df = summary_by_category(df)
        fig_cat = px.bar(
            cat_df,
            x="Total Sales (Rs.)",
            y="Category",
            orientation="h",
            color="Avg Rating",
            color_continuous_scale="Blues",
            text="Total Sales (Rs.)",
            labels={"Total Sales (Rs.)": "Revenue (Rs.)"},
        )
        fig_cat.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
        )
        fig_cat.update_layout(
            margin=dict(l=0, r=60, t=10, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(categoryorder="total ascending"),
            coloraxis_colorbar=dict(title="Avg Rating", thickness=12),
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 2: Payment Distribution + Customer Rating by Category
# ---------------------------------------------------------------------------

col2a, col2b = st.columns(2)

with col2a:
    st.subheader("💳 Payment Method Distribution")
    try:
        pay_df = summary_by_payment(df)
        fig_pay = px.pie(
            pay_df,
            names="Payment",
            values="Total Sales (Rs.)",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pay.update_traces(
            textposition="outside",
            textinfo="percent+label",
        )
        fig_pay.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            showlegend=True,
        )
        st.plotly_chart(fig_pay, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with col2b:
    st.subheader("⭐ Avg Customer Rating by Category")
    try:
        rat_df = rating_by_category(df)
        fig_rat = px.bar(
            rat_df,
            x="Category",
            y="Avg Rating",
            color="Avg Rating",
            color_continuous_scale="RdYlGn",
            range_color=[3.5, 4.5],
            text="Avg Rating",
            error_y="Rating Std Dev",
        )
        fig_rat.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_rat.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_tickangle=-20,
            yaxis=dict(range=[3.4, 4.6], gridcolor="#f0f0f0"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_rat, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 3: Branch Comparison + Weekday Heatmap
# ---------------------------------------------------------------------------

col3a, col3b = st.columns(2)

with col3a:
    st.subheader("🏪 Branch Performance")
    try:
        br_df = summary_by_branch(df)
        fig_br = go.Figure()
        fig_br.add_trace(go.Bar(
            name="Total Revenue",
            x=br_df["Branch"],
            y=br_df["Total Sales (Rs.)"],
            marker_color="#3b82d4",
            text=br_df["Total Sales (Rs.)"].apply(lambda v: f"₹{v:,.0f}"),
            textposition="outside",
            yaxis="y",
        ))
        fig_br.add_trace(go.Scatter(
            name="Avg Rating",
            x=br_df["Branch"],
            y=br_df["Avg Rating"],
            mode="lines+markers+text",
            marker=dict(color="#f59e0b", size=10),
            line=dict(color="#f59e0b", width=2),
            text=br_df["Avg Rating"],
            texttemplate="%{text:.2f}",
            textposition="top center",
            yaxis="y2",
        ))
        fig_br.update_layout(
            yaxis=dict(title="Revenue (Rs.)", gridcolor="#f0f0f0"),
            yaxis2=dict(
                title="Avg Rating",
                overlaying="y",
                side="right",
                range=[3.5, 4.5],
                showgrid=False,
            ),
            xaxis_title="Branch",
            barmode="group",
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig_br, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with col3b:
    st.subheader("📅 Sales by Day of Week")
    try:
        wd_df = weekday_breakdown(df)
        fig_wd = px.bar(
            wd_df,
            x="Day of Week",
            y="Total Sales (Rs.)",
            color="Transactions",
            color_continuous_scale="Blues",
            text="Transactions",
            labels={"Total Sales (Rs.)": "Revenue (Rs.)"},
        )
        fig_wd.update_traces(texttemplate="%{text} txns", textposition="outside")
        fig_wd.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_tickangle=-15,
            yaxis=dict(gridcolor="#f0f0f0"),
            coloraxis_colorbar=dict(title="Txns", thickness=12),
        )
        st.plotly_chart(fig_wd, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 4: Top Products + Gender breakdown
# ---------------------------------------------------------------------------

col4a, col4b = st.columns([3, 2])

with col4a:
    st.subheader("🏆 Top 10 Products by Revenue")
    try:
        prod_df = top_products(df, n=10)
        fig_prod = px.bar(
            prod_df,
            x="Total Sales (Rs.)",
            y="Product",
            color="Category",
            orientation="h",
            text="Total Sales (Rs.)",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_prod.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
        )
        fig_prod.update_layout(
            margin=dict(l=0, r=60, t=10, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(categoryorder="total ascending"),
            legend=dict(title="Category"),
        )
        st.plotly_chart(fig_prod, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with col4b:
    st.subheader("👥 Gender & Customer Type")
    try:
        gen_df = summary_by_gender(df)
        ctype_df = summary_by_customer_type(df)  # noqa: F841 (used below)

        fig_gen = px.pie(
            gen_df,
            names="Gender",
            values="Total Sales (Rs.)",
            hole=0.45,
            color_discrete_sequence=["#7c5cd8", "#3b82d4"],
            title="Revenue by Gender",
        )
        fig_gen.update_traces(textposition="outside", textinfo="percent+label")
        fig_gen.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_gen, use_container_width=True)

        fig_ctype = px.pie(
            ctype_df,
            names="Customer Type",
            values="Total Sales (Rs.)",
            hole=0.45,
            color_discrete_sequence=["#10b981", "#f59e0b"],
            title="Revenue by Customer Type",
        )
        fig_ctype.update_traces(textposition="outside", textinfo="percent+label")
        fig_ctype.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_ctype, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 5: City comparison + Rating by Branch
# ---------------------------------------------------------------------------

col5a, col5b = st.columns(2)

with col5a:
    st.subheader("🏙 Revenue by City")
    try:
        city_df = summary_by_city(df)
        fig_city = px.bar(
            city_df,
            x="City",
            y="Total Sales (Rs.)",
            color="Transactions",
            color_continuous_scale="Teal",
            text="Total Sales (Rs.)",
        )
        fig_city.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig_city.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title="City",
            yaxis=dict(gridcolor="#f0f0f0"),
            coloraxis_colorbar=dict(title="Txns", thickness=12),
        )
        st.plotly_chart(fig_city, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

with col5b:
    st.subheader("⭐ Avg Rating by Branch")
    try:
        rb_df = rating_by_branch(df)
        fig_rb = px.bar(
            rb_df,
            x="Branch",
            y="Avg Rating",
            color="Avg Rating",
            color_continuous_scale="RdYlGn",
            range_color=[3.5, 4.5],
            text="Avg Rating",
            error_y="Rating Std Dev",
        )
        fig_rb.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_rb.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[3.4, 4.6], gridcolor="#f0f0f0"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_rb, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Raw data table (collapsible)
# ---------------------------------------------------------------------------

with st.expander("📋 View Raw Data Table", expanded=False):
    st.dataframe(
        df[[
            "Invoice ID", "Date", "Branch", "City", "Customer Type",
            "Gender", "Product", "Category", "Quantity", "Unit Price",
            "Payment", "Rating", "Sales",
        ]].style.format({
            "Unit Price": "₹{:.2f}",
            "Sales": "₹{:.2f}",
            "Rating": "{:.1f}",
        }),
        use_container_width=True,
        height=400,
    )
    st.caption(f"{len(df):,} rows displayed")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <hr style="border-color:#e5e7eb; margin-top:32px;">
    <p style="text-align:center; color:#57606a; font-size:12px;">
        Supermarket Sales Analytics · Built with Streamlit & Plotly
    </p>
    """,
    unsafe_allow_html=True,
)
