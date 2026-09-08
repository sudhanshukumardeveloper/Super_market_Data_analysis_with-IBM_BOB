# 🛒 Supermarket Sales Dashboard

An interactive Python data analytics project for supermarket sales analysis,
built with **Streamlit** and **Plotly**.

---

## 📁 Project Structure

```
Supermarket_Sales_Dashboard/
├── data/
│   └── supermarket_sales.csv       ← Raw dataset (500 transactions)
├── src/
│   ├── __init__.py
│   ├── data_loader.py              ← Data loading, parsing & cleaning
│   ├── analytics.py                ← Descriptive analytics functions
│   └── dashboard.py                ← Streamlit interactive dashboard
├── requirements.txt                ← Python dependencies
├── run_dashboard.bat               ← One-click launcher (Windows)
└── README.md
```

---

## 🚀 Quick Start

### Option 1 — Double-click launcher (Windows)
Double-click **`run_dashboard.bat`** — it installs dependencies and opens the dashboard automatically.

### Option 2 — Command line
```bash
# Install dependencies (only needed once)
pip install -r requirements.txt

# Launch the dashboard
streamlit run src/dashboard.py
```

Then open **http://localhost:8501** in your browser.

---

## 📊 Dashboard Features

| Section | Description |
|---|---|
| **KPI Cards** | Total Revenue · Transactions · Avg Sale · Avg Rating · Items Sold |
| **Monthly Sales Trend** | Interactive line chart with transaction labels |
| **Revenue by Category** | Horizontal bar chart colour-coded by Avg Rating |
| **Payment Method** | Donut chart (UPI / Card / Cash / Net Banking) |
| **Customer Ratings** | Bar chart with error bars per category |
| **Branch Performance** | Dual-axis chart (Revenue + Avg Rating) |
| **Day of Week** | Sales breakdown by weekday |
| **Top 10 Products** | Horizontal bar coloured by product category |
| **Gender & Customer Type** | Revenue split via donut charts |
| **Revenue by City** | City-wise bar chart |
| **Raw Data Table** | Filterable, collapsible with ₹ formatting |

### Sidebar Filters (live, affect all charts)
- **Branch** · **City** · **Customer Type** · **Gender** · **Product Category**

---

## 🗃 Dataset Columns

| Column | Type | Description |
|---|---|---|
| Invoice ID | String | Unique transaction ID |
| Date | Date | Transaction date (YYYY-MM-DD) |
| Branch | Category | Store branch (A / B / C / D) |
| City | Category | Jaipur · Delhi · Mumbai · Bengaluru |
| Customer Type | Category | Member / Normal |
| Gender | Category | Male / Female |
| Product | String | Product name |
| Category | Category | Dairy, Grocery, Fruits, Snacks, Personal Care, Vegetables, Beverages, Bakery |
| Quantity | Integer | Units purchased |
| Unit Price | Float | Price per unit (₹) |
| Payment | Category | UPI / Card / Cash / Net Banking |
| Rating | Float | Customer rating (1–5) |
| Sales | Float | Total sale = Quantity × Unit Price |

---

## 🧹 Data Cleaning (auto on load)
- Regex-based fixed-width parser (handles irregular whitespace)
- Type casting: dates, integers, floats
- Missing value detection and reporting
- Duplicate Invoice ID removal
- Sales = Quantity × Unit Price validation & auto-correction

---

## 📦 Dependencies

```
pandas>=2.0.0
numpy>=1.24.0
streamlit>=1.32.0
plotly>=5.20.0
openpyxl>=3.1.0
```
