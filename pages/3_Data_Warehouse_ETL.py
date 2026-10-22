
import os

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Data Warehouse & ETL",
    page_icon="🗄️",
    layout="wide"
)

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(project_folder, ".env"))


# ==================================================
# 2. BLACK + BLUE/PURPLE THEME
# ==================================================

st.markdown("""
<style>
    .stApp {
        background: #000000;
        color: #F5F5F7;
    }

    [data-testid="stHeader"] {
        background: #000000;
    }

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
        font-weight: 650 !important;
    }

    p, label, .stMarkdown, .stCaption {
        color: #D1D5DB;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(
            135deg, #10101A, #141126
        );
        border: 1px solid #30264F;
        border-radius: 12px;
        padding: 18px 16px;
    }

    [data-testid="stMetricLabel"] {
        color: #A5B4FC !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 750;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #292943;
        border-radius: 10px;
        overflow: hidden;
    }

    [data-testid="stPlotlyChart"] {
        background: #08080D;
        border: 1px solid #292943;
        border-radius: 12px;
        padding: 8px;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    hr {
        border-color: #292943 !important;
    }

    div[data-testid="stVerticalBlock"] > div {
        scroll-margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)


def apply_dark_chart_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#E5E7EB",
            family="Arial",
            size=12
        ),
        title_font=dict(
            color="#C4B5FD",
            size=18
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#D1D5DB")
        ),
        margin=dict(l=20, r=20, t=60, b=30)
    )

    fig.update_xaxes(
        gridcolor="#242438",
        linecolor="#35354D",
        zerolinecolor="#35354D",
        tickfont=dict(color="#D1D5DB"),
        title_font=dict(color="#C4B5FD")
    )

    fig.update_yaxes(
        gridcolor="#242438",
        linecolor="#35354D",
        zerolinecolor="#35354D",
        tickfont=dict(color="#D1D5DB"),
        title_font=dict(color="#C4B5FD")
    )

    return fig


st.title("🗄️ Data Warehouse & ETL")
st.caption(
    "Enterprise Data Warehouse Architecture, "
    "ETL Monitoring and Data Quality"
)


# ==================================================
# 3. DATABASE CONNECTION
# ==================================================

@st.cache_resource
def get_engine():
    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv(
            "DB_NAME",
            "genai_data_warehouse"
        )
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True
    )


# ==================================================
# 4. LOAD WAREHOUSE STATISTICS
# ==================================================

@st.cache_data(ttl=60)
def load_warehouse_stats():
    engine = get_engine()

    queries = {
        "Dim_Customer": "SELECT COUNT(*) FROM Dim_Customer",
        "Dim_Product": "SELECT COUNT(*) FROM Dim_Product",
        "Dim_Date": "SELECT COUNT(*) FROM Dim_Date",
        "Dim_Location": "SELECT COUNT(*) FROM Dim_Location",
        "Fact_Sales": "SELECT COUNT(*) FROM Fact_Sales"
    }

    counts = {}

    with engine.connect() as connection:
        for table_name, query in queries.items():
            counts[table_name] = connection.execute(
                text(query)
            ).scalar_one()

        totals_query = """
            SELECT
                COALESCE(SUM(sales), 0) AS total_sales,
                COALESCE(SUM(profit), 0) AS total_profit,
                COALESCE(SUM(quantity), 0) AS total_quantity,
                COUNT(DISTINCT order_id) AS total_orders
            FROM Fact_Sales
        """

        totals = pd.read_sql(
            text(totals_query),
            connection
        )

        quality_query = """
            SELECT
                COUNT(*) AS total_rows,
                SUM(
                    CASE WHEN customer_key IS NULL
                    THEN 1 ELSE 0 END
                ) AS missing_customer,
                SUM(
                    CASE WHEN product_key IS NULL
                    THEN 1 ELSE 0 END
                ) AS missing_product,
                SUM(
                    CASE WHEN order_date_key IS NULL
                    THEN 1 ELSE 0 END
                ) AS missing_order_date,
                SUM(
                    CASE WHEN location_key IS NULL
                    THEN 1 ELSE 0 END
                ) AS missing_location
            FROM Fact_Sales
        """

        quality = pd.read_sql(
            text(quality_query),
            connection
        )

    return counts, totals, quality


# ==================================================
# 5. WAREHOUSE OVERVIEW
# ==================================================

try:
    counts, totals, quality = load_warehouse_stats()

    total_rows = counts["Fact_Sales"]
    total_sales = float(totals.loc[0, "total_sales"])
    total_profit = float(totals.loc[0, "total_profit"])
    total_quantity = int(totals.loc[0, "total_quantity"])
    total_orders = int(totals.loc[0, "total_orders"])

    st.subheader("📊 Warehouse Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Fact Sales Records",
        f"{total_rows:,}"
    )
    col2.metric(
        "Total Sales",
        f"${total_sales:,.2f}"
    )
    col3.metric(
        "Total Profit",
        f"${total_profit:,.2f}"
    )
    col4.metric(
        "Unique Orders",
        f"{total_orders:,}"
    )

    st.divider()


    # ==================================================
    # 6. WAREHOUSE TABLES
    # ==================================================

    st.subheader("🗂️ Data Warehouse Tables")

    table_data = pd.DataFrame({
        "Table Name": list(counts.keys()),
        "Table Type": [
            "Dimension",
            "Dimension",
            "Dimension",
            "Dimension",
            "Fact"
        ],
        "Record Count": list(counts.values())
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
        title="Records Stored in Warehouse Tables",
        text="Record Count",
        color_discrete_map={
            "Dimension": "#818CF8",
            "Fact": "#A78BFA"
        }
    )

    fig_tables.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    fig_tables = apply_dark_chart_theme(fig_tables)

    st.plotly_chart(
        fig_tables,
        use_container_width=True
    )

    st.info(
        "Fact_Sales stores sales transactions. "
        "Dimension tables provide customer, product, "
        "date and location details."
    )

    st.divider()


    # ==================================================
    # 7. ETL PROCESS EXPLANATION
    # ==================================================

    st.subheader("⚙️ ETL Process")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 1. Extract")
        st.write(
            "Read the source Superstore CSV dataset "
            "containing sales transactions."
        )

    with col2:
        st.markdown("### 2. Transform")
        st.write(
            "Prepare dates and numeric values, "
            "organise dimension data and prepare "
            "records for warehouse loading."
        )

    with col3:
        st.markdown("### 3. Load")
        st.write(
            "Load customer, product, date and location "
            "dimensions, followed by Fact_Sales in MySQL."
        )

    st.caption(
        "ETL description reflects the project's data "
        "preparation and loading workflow."
    )

    st.divider()


    # ==================================================
    # 8. DATA QUALITY CHECK
    # ==================================================

    st.subheader("🔍 Data Quality Checks")

    missing_customer = int(
        quality.loc[0, "missing_customer"] or 0
    )
    missing_product = int(
        quality.loc[0, "missing_product"] or 0
    )
    missing_date = int(
        quality.loc[0, "missing_order_date"] or 0
    )
    missing_location = int(
        quality.loc[0, "missing_location"] or 0
    )

    missing_total = (
        missing_customer
        + missing_product
        + missing_date
        + missing_location
    )

    q1, q2, q3 = st.columns(3)

    q1.metric(
        "Rows Checked",
        f"{total_rows:,}"
    )

    q2.metric(
        "Missing Foreign Keys",
        f"{missing_total:,}"
    )

    completeness = (
        100
        if total_rows == 0 or missing_total == 0
        else max(
            0,
            (1 - missing_total / (total_rows * 4)) * 100
        )
    )

    q3.metric(
        "Foreign Key Completeness",
        f"{completeness:.2f}%"
    )

    quality_details = pd.DataFrame({
        "Quality Check": [
            "Missing Customer Keys",
            "Missing Product Keys",
            "Missing Order Date Keys",
            "Missing Location Keys"
        ],
        "Issue Count": [
            missing_customer,
            missing_product,
            missing_date,
            missing_location
        ]
    })

    st.dataframe(
        quality_details,
        use_container_width=True,
        hide_index=True
    )

    if missing_total == 0:
        st.success(
            "No missing foreign keys were found "
            "in the checked Fact_Sales columns."
        )
    else:
        st.warning(
            "Some foreign keys are missing. "
            "Review the warehouse records."
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
            "Total Quantity Sold",
            "Total Sales",
            "Total Profit"
        ],
        "Value": [
            f"{total_rows:,}",
            f"{total_orders:,}",
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

    st.caption(
        "Source: MySQL genai_data_warehouse database"
    )

except Exception as error:
    st.error(
        "Unable to load Data Warehouse statistics. "
        "Check your MySQL connection and .env settings."
    )
    st.exception(error)
