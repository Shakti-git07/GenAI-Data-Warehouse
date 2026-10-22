import os
import pandas as pd
import streamlit as st
import plotly.express as px

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Data Mining Insights",
    page_icon="📈",
    layout="wide"
)

load_dotenv()


# ==================================================
# 2. DARK THEME
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000 !important;
        color: #F5F7FA;
    }

    [data-testid="stHeader"] {
        background-color: #000000 !important;
    }

    [data-testid="stToolbar"] {
        background-color: #000000 !important;
    }

    [data-testid="stDecoration"] {
        background: #000000 !important;
        background-image: none !important;
    }

    header,
    [data-testid="stHeader"] > div {
        background-color: #000000 !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        background-color: #0B0B0F;
        border-right: 1px solid #252532;
    }

    h1, h2, h3 {
        color: #F5F7FA !important;
    }

    .stApp p,
    .stApp label,
    .stApp [data-testid="stCaptionContainer"] {
        color: #B8BFCC;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #111118, #171724);
        border: 1px solid #292941;
        border-radius: 12px;
        padding: 18px 20px;
    }

    [data-testid="stMetricLabel"] {
        color: #B8BFCC !important;
    }

    [data-testid="stMetricValue"] {
        color: #F5F7FA !important;
    }

    [data-testid="stPlotlyChart"] {
        background-color: #0B0B0F;
        border: 1px solid #242432;
        border-radius: 12px;
        padding: 8px;
    }

    [data-testid="stExpander"] {
        background-color: #0D0D12;
        border: 1px solid #292941;
        border-radius: 10px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #292941;
        border-radius: 8px;
    }

    [data-testid="stSelectbox"] {
        color: #F5F7FA;
    }

    hr {
        border-color: #292932 !important;
    }

    .stApp a {
        color: #A9A0FF;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 3. PLOTLY DARK THEME HELPER
# ==================================================

def apply_dark_chart_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#E6E8EF",
            family="Arial"
        ),
        title_font=dict(color="#F5F7FA"),
        legend_title_font=dict(color="#E6E8EF"),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    fig.update_xaxes(
        gridcolor="#292932",
        zerolinecolor="#292932"
    )

    fig.update_yaxes(
        gridcolor="#292932",
        zerolinecolor="#292932"
    )

    return fig


# ==================================================
# 4. PAGE TITLE
# ==================================================

st.title("📈 Data Mining Insights")
st.caption("Customer Segmentation and Business Intelligence")


# ==================================================
# 5. CUSTOMER SEGMENTATION
# ==================================================

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

csv_path = os.path.join(
    project_folder,
    "customer_segments.csv"
)

if os.path.exists(csv_path):
    customers = pd.read_csv(csv_path)

    st.subheader("Customer Segmentation")

    summary = (
        customers.groupby("segment", as_index=False)
        .agg(
            customer_count=("customer_id", "nunique"),
            average_sales=("total_sales", "mean"),
            average_profit=("total_profit", "mean")
        )
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_count = px.bar(
            summary,
            x="segment",
            y="customer_count",
            color="segment",
            title="Customers in Each Segment",
            labels={
                "segment": "Customer Segment",
                "customer_count": "Number of Customers"
            }
        )

        apply_dark_chart_theme(fig_count)

        st.plotly_chart(
            fig_count,
            use_container_width=True
        )

    with col2:
        fig_sales = px.bar(
            summary,
            x="segment",
            y="average_sales",
            color="segment",
            title="Average Sales per Customer",
            labels={
                "segment": "Customer Segment",
                "average_sales": "Average Sales (USD)"
            }
        )

        apply_dark_chart_theme(fig_sales)

        st.plotly_chart(
            fig_sales,
            use_container_width=True
        )

    st.subheader("Average Profit by Segment")

    fig_profit = px.bar(
        summary,
        x="segment",
        y="average_profit",
        color="segment",
        title="Average Profit per Customer",
        labels={
            "segment": "Customer Segment",
            "average_profit": "Average Profit (USD)"
        }
    )

    apply_dark_chart_theme(fig_profit)

    st.plotly_chart(
        fig_profit,
        use_container_width=True
    )

    st.subheader("Customer Segment Summary")

    st.dataframe(
        summary.round(2),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("View Individual Customer Details"):
        st.dataframe(
            customers,
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning(
        "Customer segmentation file not found. "
        "Run customer_segmentation.py from the project folder first."
    )


# ==================================================
# 6. PRODUCT PROFITABILITY AND LOSS ANALYSIS
# ==================================================

st.divider()
st.header("Product Profitability & Loss Analysis")

st.write(
    "Identify products that generate the highest profit "
    "and products that are operating at a loss."
)


@st.cache_data(ttl=60)
def load_product_profitability():
    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "genai_data_warehouse")
    )

    engine = create_engine(
        connection_url,
        pool_pre_ping=True
    )

    query = """
        SELECT
            p.product_name,
            p.category,
            p.sub_category,
            SUM(f.sales) AS total_sales,
            SUM(f.profit) AS total_profit,
            SUM(f.quantity) AS total_quantity
        FROM Fact_Sales f
        JOIN Dim_Product p
            ON f.product_key = p.product_key
        GROUP BY
            p.product_name,
            p.category,
            p.sub_category
        ORDER BY total_profit DESC
    """

    try:
        with engine.connect() as connection:
            result = pd.read_sql(text(query), connection)
    finally:
        engine.dispose()

    return result


product_df = pd.DataFrame()

try:
    product_df = load_product_profitability()

    if not product_df.empty:
        product_df["profit_status"] = product_df["total_profit"].apply(
            lambda profit: "Profitable" if profit >= 0 else "Loss"
        )

        profitable_products = product_df[
            product_df["total_profit"] >= 0
        ]

        loss_products = product_df[
            product_df["total_profit"] < 0
        ]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Products Analysed",
            f"{len(product_df):,}"
        )

        col2.metric(
            "Profitable Products",
            f"{len(profitable_products):,}"
        )

        col3.metric(
            "Products with Loss",
            f"{len(loss_products):,}"
        )

        st.subheader("Top 10 Most Profitable Products")

        top_products = (
            product_df.nlargest(10, "total_profit")
            .sort_values("total_profit", ascending=True)
        )

        fig_top_products = px.bar(
            top_products,
            x="total_profit",
            y="product_name",
            orientation="h",
            color="total_profit",
            title="Top 10 Products by Total Profit",
            labels={
                "product_name": "Product",
                "total_profit": "Total Profit (USD)"
            },
            color_continuous_scale="Purples"
        )

        apply_dark_chart_theme(fig_top_products)

        st.plotly_chart(
            fig_top_products,
            use_container_width=True
        )

        st.subheader("Top 10 Products with Highest Loss")

        if not loss_products.empty:
            worst_products = (
                loss_products.nsmallest(10, "total_profit")
                .sort_values("total_profit", ascending=True)
            )

            fig_loss_products = px.bar(
                worst_products,
                x="total_profit",
                y="product_name",
                orientation="h",
                color="total_profit",
                title="Products Ranked by Loss",
                labels={
                    "product_name": "Product",
                    "total_profit": "Total Profit / Loss (USD)"
                },
                color_continuous_scale="RdBu"
            )

            apply_dark_chart_theme(fig_loss_products)

            st.plotly_chart(
                fig_loss_products,
                use_container_width=True
            )

        else:
            st.success("No loss-making products found.")

        st.subheader("Product Profitability Details")

        selected_category = st.selectbox(
            "Filter by Category",
            ["All Categories"]
            + sorted(
                product_df["category"].dropna().unique().tolist()
            ),
            key="product_profit_category"
        )

        display_df = product_df.copy()

        if selected_category != "All Categories":
            display_df = display_df[
                display_df["category"] == selected_category
            ]

        st.dataframe(
            display_df.round(2),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No product profitability records found.")

except Exception as error:
    st.error("Unable to load product profitability analysis.")
    st.exception(error)


# ==================================================
# 7. CATEGORY-WISE PROFITABILITY ANALYSIS
# ==================================================

st.divider()
st.header("Category-wise Profitability Analysis")

st.write(
    "Compare total sales and profit across different product categories."
)

if not product_df.empty:
    category_summary = (
        product_df.groupby("category", as_index=False)
        .agg(
            total_sales=("total_sales", "sum"),
            total_profit=("total_profit", "sum"),
            total_quantity=("total_quantity", "sum")
        )
        .sort_values("total_profit", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_category_sales = px.bar(
            category_summary,
            x="category",
            y="total_sales",
            color="category",
            title="Total Sales by Category",
            labels={
                "category": "Product Category",
                "total_sales": "Total Sales (USD)"
            }
        )

        apply_dark_chart_theme(fig_category_sales)

        st.plotly_chart(
            fig_category_sales,
            use_container_width=True
        )

    with col2:
        fig_category_profit = px.bar(
            category_summary,
            x="category",
            y="total_profit",
            color="category",
            title="Total Profit by Category",
            labels={
                "category": "Product Category",
                "total_profit": "Total Profit (USD)"
            }
        )

        apply_dark_chart_theme(fig_category_profit)

        st.plotly_chart(
            fig_category_profit,
            use_container_width=True
        )

    st.subheader("Category Performance Summary")

    st.dataframe(
        category_summary.round(2),
        use_container_width=True,
        hide_index=True
    )


# ==================================================
# 8. SUB-CATEGORY PROFIT ANALYSIS
# ==================================================

st.divider()
st.header("Sub-category Profit Analysis")

st.write(
    "Compare sales and profit across product sub-categories "
    "to identify the strongest and weakest performers."
)

if not product_df.empty:
    subcategory_summary = (
        product_df.groupby(
            ["category", "sub_category"],
            as_index=False
        )
        .agg(
            total_sales=("total_sales", "sum"),
            total_profit=("total_profit", "sum"),
            total_quantity=("total_quantity", "sum")
        )
        .sort_values("total_profit", ascending=False)
    )

    st.subheader("Top 10 Sub-categories by Profit")

    top_subcategories = (
        subcategory_summary
        .nlargest(10, "total_profit")
        .sort_values("total_profit", ascending=True)
    )

    fig_subcategory_profit = px.bar(
        top_subcategories,
        x="total_profit",
        y="sub_category",
        color="category",
        orientation="h",
        hover_data=["total_sales", "total_quantity"],
        title="Top 10 Sub-categories by Total Profit",
        labels={
            "sub_category": "Sub-category",
            "total_profit": "Total Profit (USD)",
            "category": "Category",
            "total_sales": "Total Sales (USD)",
            "total_quantity": "Quantity Sold"
        }
    )

    apply_dark_chart_theme(fig_subcategory_profit)

    st.plotly_chart(
        fig_subcategory_profit,
        use_container_width=True
    )

    st.subheader("Lowest Performing Sub-categories")

    bottom_subcategories = (
        subcategory_summary
        .nsmallest(10, "total_profit")
        .sort_values("total_profit", ascending=True)
    )

    fig_subcategory_loss = px.bar(
        bottom_subcategories,
        x="total_profit",
        y="sub_category",
        color="category",
        orientation="h",
        hover_data=["total_sales", "total_quantity"],
        title="10 Sub-categories with Lowest Profit",
        labels={
            "sub_category": "Sub-category",
            "total_profit": "Total Profit (USD)",
            "category": "Category",
            "total_sales": "Total Sales (USD)",
            "total_quantity": "Quantity Sold"
        }
    )

    apply_dark_chart_theme(fig_subcategory_loss)

    st.plotly_chart(
        fig_subcategory_loss,
        use_container_width=True
    )

    st.subheader("Sub-category Performance Details")

    selected_subcategory_category = st.selectbox(
        "Filter by Product Category",
        ["All Categories"]
        + sorted(
            subcategory_summary["category"].dropna().unique().tolist()
        ),
        key="subcategory_category_filter"
    )

    subcategory_display = subcategory_summary.copy()

    if selected_subcategory_category != "All Categories":
        subcategory_display = subcategory_display[
            subcategory_display["category"]
            == selected_subcategory_category
        ]

    st.dataframe(
        subcategory_display.round(2),
        use_container_width=True,
        hide_index=True
    )
