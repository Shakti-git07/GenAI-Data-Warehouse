
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Data Warehouse & ETL",
    page_icon="🗄️",
    layout="wide"
)

PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CSV_PATH = os.path.join(
    PROJECT_FOLDER,
    "data",
    "Superstore_Prepared.csv"
)

# ==================================================
# 2. DARK THEME
# ==================================================

st.markdown("""
<style>
    .stApp {
        background: #000000;
        color: #F5F5F7;
    }
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        background: #000000;
    }
    [data-testid="stSidebar"] {
        background: #08080D;
        border-right: 1px solid #202033;
    }
    [data-testid="stSidebar"] * {
        color: #E5E7EB;
    }
    h1 {
        color: #FFFFFF !important;
        font-weight: 750 !important;
    }
    h2, h3 {
        color: #C4B5FD !important;
    }
    p, label {
        color: #D1D5DB;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #10101A, #141126);
        border: 1px solid #30264F;
        border-radius: 12px;
        padding: 18px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #A5B4FC !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    [data-testid="stDataFrame"],
    [data-testid="stPlotlyChart"] {
        border: 1px solid #292943;
        border-radius: 10px;
    }
    hr {
        border-color: #292943 !important;
    }
</style>
""", unsafe_allow_html=True)


def apply_dark_chart_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB", family="Arial"),
        title_font=dict(color="#C4B5FD", size=18),
        margin=dict(l=20, r=20, t=60, b=30)
    )
    fig.update_xaxes(gridcolor="#242438")
    fig.update_yaxes(gridcolor="#242438")
    return fig


# ==================================================
# 3. LOAD DATA FROM CSV
# ==================================================

@st.cache_data(ttl=60)
def load_sales_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            "File not found: data/Superstore_Prepared.csv"
        )

    df = pd.read_csv(CSV_PATH)

    required_columns = [
        "Order ID", "Order Date", "Customer ID",
        "Product ID", "Sales", "Profit", "Quantity",
        "Category", "Sub-Category", "Region",
        "Customer Name", "Product Name", "City", "State"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing CSV columns: " + ", ".join(missing)
        )

    df["Order Date"] = pd.to_datetime(
        df["Order Date"], errors="coerce"
    )

    df["Ship Date"] = pd.to_datetime(
        df["Ship Date"], errors="coerce"
    )

    for col in ["Sales", "Profit", "Quantity", "Discount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

    df = df.dropna(
        subset=["Order ID", "Order Date", "Sales", "Profit"]
    )

    return df


# ==================================================
# 4. PAGE TITLE
# ==================================================

st.title("🗄️ Data Warehouse & ETL")
st.caption(
    "Enterprise Data Warehouse Architecture, "
    "ETL Monitoring and Data Quality"
)

try:
    df = load_sales_data()

    # ==================================================
    # 5. WAREHOUSE OVERVIEW
    # ==================================================

    st.subheader("📊 Warehouse Overview")

    total_rows = len(df)
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_quantity = int(df["Quantity"].sum())
    total_orders = df["Order ID"].nunique()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Fact Sales Records", f"{total_rows:,}")
    c2.metric("Total Sales", f"${total_sales:,.2f}")
    c3.metric("Total Profit", f"${total_profit:,.2f}")
    c4.metric("Unique Orders", f"{total_orders:,}")

    st.divider()

    # ==================================================
    # 6. WAREHOUSE TABLES
    # ==================================================

    st.subheader("🗂️ Data Warehouse Tables")

    table_data = pd.DataFrame({
        "Table Name": [
            "Dim_Customer",
            "Dim_Product",
            "Dim_Date",
            "Dim_Location",
            "Fact_Sales"
        ],
        "Table Type": [
            "Dimension",
            "Dimension",
            "Dimension",
            "Dimension",
            "Fact"
        ],
        "Record Count": [
            df["Customer ID"].nunique(),
            df["Product ID"].nunique(),
            df["Order Date"].dt.date.nunique(),
            df[["City", "State", "Region"]].drop_duplicates().shape[0],
            total_rows
        ]
    })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True
    )

    fig_tables = px.bar(
        table_data,
        x="Table Name",
        y="Record Count",
        color="Table Type",
        title="Records Represented in Warehouse Tables",
        text="Record Count",
        color_discrete_map={
            "Dimension": "#818CF8",
            "Fact": "#A78BFA"
        }
    )

    fig_tables.update_traces(textposition="outside")
    st.plotly_chart(
        apply_dark_chart_theme(fig_tables),
        use_container_width=True
    )

    st.info(
        "The fact table contains sales transactions. "
        "Dimension tables represent customers, products, "
        "dates and locations. Dimension counts are derived "
        "from the prepared source CSV."
    )

    st.divider()

    # ==================================================
    # 7. ETL PROCESS
    # ==================================================

    st.subheader("⚙️ ETL Process")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 1. Extract")
        st.write(
            "Read sales transaction data from "
            "the prepared Superstore CSV dataset."
        )

    with c2:
        st.markdown("### 2. Transform")
        st.write(
            "Convert dates and numeric fields, check missing "
            "values and organise customer, product, date "
            "and location attributes."
        )

    with c3:
        st.markdown("### 3. Load")
        st.write(
            "The project warehouse schema uses dimension "
            "tables and a Fact_Sales table. This deployed "
            "page reads the prepared CSV for cloud compatibility."
        )

    st.caption(
        "Note: this page displays the prepared dataset; "
        "it does not execute a live ETL load into MySQL."
    )

    st.divider()

    # ==================================================
    # 8. DATA QUALITY
    # ==================================================

    st.subheader("🔍 Data Quality Checks")

    quality_checks = {
        "Missing Order ID": int(df["Order ID"].isna().sum()),
        "Missing Customer ID": int(df["Customer ID"].isna().sum()),
        "Missing Product ID": int(df["Product ID"].isna().sum()),
        "Missing Order Date": int(df["Order Date"].isna().sum()),
        "Missing Sales": int(df["Sales"].isna().sum()),
        "Missing Profit": int(df["Profit"].isna().sum())
    }

    quality_df = pd.DataFrame({
        "Quality Check": list(quality_checks.keys()),
        "Issue Count": list(quality_checks.values())
    })

    total_issues = sum(quality_checks.values())
    completeness = (
        100.0 if total_rows == 0
        else (1 - total_issues / (total_rows * len(quality_checks))) * 100
    )

    q1, q2, q3 = st.columns(3)

    q1.metric("Rows Checked", f"{total_rows:,}")
    q2.metric("Missing Values Checked", f"{total_issues:,}")
    q3.metric("Field Completeness", f"{completeness:.2f}%")

    st.dataframe(
        quality_df,
        use_container_width=True,
        hide_index=True
    )

    if total_issues == 0:
        st.success("No missing values found in the checked fields.")
    else:
        st.warning(
            "Missing values were detected in one or more fields."
        )

    st.divider()

    # ==================================================
    # 9. SALES SUMMARY
    # ==================================================

    st.subheader("💰 Warehouse Sales Summary")

    summary_data = pd.DataFrame({
        "Metric": [
            "Sales Transactions",
            "Unique Orders",
            "Unique Customers",
            "Unique Products",
            "Total Quantity Sold",
            "Total Sales",
            "Total Profit"
        ],
        "Value": [
            f"{total_rows:,}",
            f"{total_orders:,}",
            f"{df['Customer ID'].nunique():,}",
            f"{df['Product ID'].nunique():,}",
            f"{total_quantity:,}",
            f"${total_sales:,.2f}",
            f"${total_profit:,.2f}"
        ]
    })

    st.dataframe(
        summary_data,
        use_container_width=True,
        hide_index=True
    )

    # ==================================================
    # 10. DATE-WISE SALES TREND
    # ==================================================

    st.divider()
    st.subheader("📅 Year-wise Sales Trend")

    yearly_sales = (
        df.assign(Year=df["Order Date"].dt.year)
        .groupby("Year", as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum")
        )
        .sort_values("Year")
    )

    fig_year = px.line(
        yearly_sales,
        x="Year",
        y=["Sales", "Profit"],
        markers=True,
        title="Yearly Sales and Profit"
    )

    st.plotly_chart(
        apply_dark_chart_theme(fig_year),
        use_container_width=True
    )

    # ==================================================
    # 11. REGION-WISE SALES
    # ==================================================

    st.subheader("🌎 Region-wise Sales")

    region_sales = (
        df.groupby("Region", as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum")
        )
        .sort_values("Sales", ascending=False)
    )

    c1, c2 = st.columns(2)

    with c1:
        fig_region_sales = px.bar(
            region_sales,
            x="Region",
            y="Sales",
            color="Region",
            title="Sales by Region"
        )

        st.plotly_chart(
            apply_dark_chart_theme(fig_region_sales),
            use_container_width=True
        )

    with c2:
        fig_region_profit = px.bar(
            region_sales,
            x="Region",
            y="Profit",
            color="Region",
            title="Profit by Region"
        )

        st.plotly_chart(
            apply_dark_chart_theme(fig_region_profit),
            use_container_width=True
        )

    st.dataframe(
        region_sales.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.caption("Data source: data/Superstore_Prepared.csv")

except Exception as error:
    st.error(
        "Unable to load the prepared dataset. "
        "Check that data/Superstore_Prepared.csv is included "
        "in the GitHub repository."
    )
    st.exception(error)
