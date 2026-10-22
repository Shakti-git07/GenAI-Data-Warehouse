import os

import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="GenAI Data Warehouse",
    page_icon="📊",
    layout="wide"
)

load_dotenv()


# ==================================================
# 2. DARK DASHBOARD THEME
# ==================================================

st.markdown(
    """
    <style>
    /* Main application background */
    .stApp {
        background-color: #000000 !important;
        color: #F5F7FA;
    }

    /* Top header */
    [data-testid="stHeader"] {
        background-color: #000000 !important;
    }

    /* Top toolbar */
    [data-testid="stToolbar"] {
        background-color: #000000 !important;
    }

    /* Top decoration strip */
    [data-testid="stDecoration"] {
        background: #000000 !important;
        background-image: none !important;
    }

    /* Header and toolbar containers */
    header,
    [data-testid="stHeader"] > div {
        background-color: #000000 !important;
    }

    /* Main content spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0B0B0F;
        border-right: 1px solid #252532;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #F5F7FA;
    }

    /* Main headings */
    h1, h2, h3 {
        color: #F5F7FA !important;
    }

    /* General text */
    .stApp p,
    .stApp label,
    .stApp [data-testid="stCaptionContainer"] {
        color: #B8BFCC;
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #111118, #171724);
        border: 1px solid #292941;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
    }

    [data-testid="stMetricLabel"] {
        color: #B8BFCC !important;
    }

    [data-testid="stMetricValue"] {
        color: #F5F7FA !important;
    }

    /* Chart containers */
    [data-testid="stPlotlyChart"] {
        background-color: #0B0B0F;
        border: 1px solid #242432;
        border-radius: 12px;
        padding: 8px;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #0D0D12;
        border: 1px solid #292941;
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #4545A5, #6555C8);
        color: #FFFFFF;
        border: 1px solid #7770D6;
        border-radius: 8px;
    }

    .stButton > button:hover {
        border-color: #A39BFF;
        color: #FFFFFF;
    }

    /* Dividers */
    hr {
        border-color: #292932 !important;
    }

    /* Data table */
    [data-testid="stDataFrame"] {
        border: 1px solid #292941;
        border-radius: 8px;
    }

    /* Multiselect and select boxes */
    [data-testid="stMultiSelect"],
    [data-testid="stSelectbox"] {
        color: #F5F7FA;
    }

    /* Links */
    .stApp a {
        color: #A9A0FF;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 3. DASHBOARD TITLE
# ==================================================

st.title("📊 GenAI-Ready Enterprise Data Warehouse")
st.caption("Business Analytics and Decision Support Dashboard")


# ==================================================
# 4. MYSQL CONNECTION
# ==================================================

@st.cache_resource
def get_engine():
    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "genai_data_warehouse")
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True
    )


# ==================================================
# 5. LOAD DATA FROM DATA WAREHOUSE
# ==================================================

@st.cache_data(ttl=60)
def load_sales_data():
    query = """
        SELECT
            f.row_id,
            f.order_id,
            f.sales,
            f.profit,
            f.quantity,
            f.discount,
            f.ship_mode,
            od.full_date AS order_date,
            od.year AS order_year,
            od.month AS order_month,
            od.month_name,
            p.category,
            p.sub_category,
            p.product_name,
            c.segment,
            l.region,
            l.state,
            l.city
        FROM Fact_Sales f
        JOIN Dim_Date od
            ON f.order_date_key = od.date_key
        JOIN Dim_Product p
            ON f.product_key = p.product_key
        JOIN Dim_Customer c
            ON f.customer_key = c.customer_key
        JOIN Dim_Location l
            ON f.location_key = l.location_key
    """

    engine = get_engine()

    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)

    return df


# ==================================================
# 6. MAIN BUSINESS DASHBOARD
# ==================================================

try:
    df = load_sales_data()

    if df.empty:
        st.warning("No sales records found in the warehouse.")
        st.stop()

    df["order_date"] = pd.to_datetime(df["order_date"])

    # --------------------------------------------------
    # 7. SIDEBAR FILTERS
    # --------------------------------------------------

    st.sidebar.header("Dashboard Filters")

    years = sorted(
        df["order_year"].dropna().unique().tolist()
    )

    selected_years = st.sidebar.multiselect(
        "Select Year",
        options=years,
        default=years
    )

    categories = sorted(
        df["category"].dropna().unique().tolist()
    )

    selected_categories = st.sidebar.multiselect(
        "Select Category",
        options=categories,
        default=categories
    )

    regions = sorted(
        df["region"].dropna().unique().tolist()
    )

    selected_regions = st.sidebar.multiselect(
        "Select Region",
        options=regions,
        default=regions
    )

    filtered = df[
        df["order_year"].isin(selected_years)
        & df["category"].isin(selected_categories)
        & df["region"].isin(selected_regions)
    ].copy()

    # --------------------------------------------------
    # 8. KEY PERFORMANCE INDICATORS
    # --------------------------------------------------

    total_sales = filtered["sales"].sum()
    total_profit = filtered["profit"].sum()
    total_orders = filtered["order_id"].nunique()
    total_quantity = filtered["quantity"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Sales", f"${total_sales:,.2f}")
    col2.metric("Total Profit", f"${total_profit:,.2f}")
    col3.metric("Unique Orders", f"{total_orders:,}")
    col4.metric("Quantity Sold", f"{total_quantity:,.0f}")

    st.divider()

    # --------------------------------------------------
    # 9. SALES BY CATEGORY
    # --------------------------------------------------

    left, right = st.columns(2)

    with left:
        st.subheader("Sales by Category")

        category_sales = (
            filtered.groupby("category", as_index=False)["sales"]
            .sum()
            .sort_values("sales", ascending=False)
        )

        fig_category = px.bar(
            category_sales,
            x="category",
            y="sales",
            color="category",
            title="Total Sales by Category",
            labels={
                "category": "Category",
                "sales": "Sales (USD)"
            }
        )

        fig_category.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6E8EF"),
            title_font=dict(color="#F5F7FA"),
            margin=dict(l=20, r=20, t=60, b=20)
        )

        fig_category.update_xaxes(
            gridcolor="#292932",
            zerolinecolor="#292932"
        )

        fig_category.update_yaxes(
            gridcolor="#292932",
            zerolinecolor="#292932"
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

    # --------------------------------------------------
    # 10. PROFIT BY REGION
    # --------------------------------------------------

    with right:
        st.subheader("Profit by Region")

        region_profit = (
            filtered.groupby("region", as_index=False)["profit"]
            .sum()
            .sort_values("profit", ascending=False)
        )

        fig_region = px.bar(
            region_profit,
            x="region",
            y="profit",
            color="region",
            title="Total Profit by Region",
            labels={
                "region": "Region",
                "profit": "Profit (USD)"
            }
        )

        fig_region.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6E8EF"),
            title_font=dict(color="#F5F7FA"),
            margin=dict(l=20, r=20, t=60, b=20)
        )

        fig_region.update_xaxes(
            gridcolor="#292932",
            zerolinecolor="#292932"
        )

        fig_region.update_yaxes(
            gridcolor="#292932",
            zerolinecolor="#292932"
        )

        st.plotly_chart(
            fig_region,
            use_container_width=True
        )

    # --------------------------------------------------
    # 11. MONTHLY SALES TREND
    # --------------------------------------------------

    st.subheader("Monthly Sales Trend")

    if not filtered.empty:
        monthly = filtered.copy()

        monthly["month_year"] = (
            monthly["order_date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        monthly_sales = (
            monthly.groupby("month_year", as_index=False)["sales"]
            .sum()
            .sort_values("month_year")
        )

        fig_monthly = px.line(
            monthly_sales,
            x="month_year",
            y="sales",
            markers=True,
            title="Total Sales per Month",
            labels={
                "month_year": "Month",
                "sales": "Total Sales (USD)"
            }
        )

        fig_monthly.update_xaxes(
            dtick="M3",
            tickformat="%b %Y",
            gridcolor="#292932",
            zerolinecolor="#292932"
        )

        fig_monthly.update_yaxes(
            gridcolor="#292932",
            zerolinecolor="#292932"
        )

        fig_monthly.update_layout(
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6E8EF"),
            title_font=dict(color="#F5F7FA"),
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_monthly,
            use_container_width=True
        )

    else:
        st.info(
            "No sales records match the selected filters. "
            "Please select at least one year, category and region."
        )

    # --------------------------------------------------
    # 12. VIEW SALES RECORDS
    # --------------------------------------------------

    with st.expander("View Sales Records"):
        st.write(f"Records displayed: {len(filtered):,}")

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------
    # 13. DATA SOURCE
    # --------------------------------------------------

    st.caption(
        "Data source: MySQL Data Warehouse | "
        "Superstore Sales Dataset"
    )

# ==================================================
# 14. ERROR HANDLING
# ==================================================

except Exception:
    st.error("Unable to load the dashboard data.")
    st.exception(Exception)
