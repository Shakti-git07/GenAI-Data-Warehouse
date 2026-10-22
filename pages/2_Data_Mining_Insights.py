
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Data Mining Insights",
    page_icon="📈",
    layout="wide"
)

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

    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
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
# 3. HELPER FUNCTIONS
# ==================================================

def apply_dark_chart_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E6E8EF", family="Arial"),
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


PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CSV_PATH = os.path.join(
    PROJECT_FOLDER,
    "data",
    "Superstore_Prepared.csv"
)


@st.cache_data(ttl=60)
def load_product_profitability():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            "data/Superstore_Prepared.csv was not found."
        )

    df = pd.read_csv(CSV_PATH)

    df = df.rename(columns={
        "Product Name": "product_name",
        "Category": "category",
        "Sub-Category": "sub_category",
        "Sales": "total_sales",
        "Profit": "total_profit",
        "Quantity": "total_quantity"
    })

    required = [
        "product_name",
        "category",
        "sub_category",
        "total_sales",
        "total_profit",
        "total_quantity"
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            "CSV columns missing: " + ", ".join(missing)
        )

    for col in ["total_sales", "total_profit", "total_quantity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)

    result = (
        df.groupby(
            ["product_name", "category", "sub_category"],
            as_index=False
        )
        .agg(
            total_sales=("total_sales", "sum"),
            total_profit=("total_profit", "sum"),
            total_quantity=("total_quantity", "sum")
        )
        .sort_values("total_profit", ascending=False)
    )

    return result


@st.cache_data(ttl=60)
def load_customer_segments():
    csv_path = os.path.join(
        PROJECT_FOLDER,
        "customer_segments.csv"
    )

    if not os.path.exists(csv_path):
        return pd.DataFrame()

    return pd.read_csv(csv_path)


# ==================================================
# 4. PAGE TITLE
# ==================================================

st.title("📈 Data Mining Insights")
st.caption("Customer Segmentation and Business Intelligence")


# ==================================================
# 5. CUSTOMER SEGMENTATION
# ==================================================

st.header("Customer Segmentation")

customers = load_customer_segments()

if not customers.empty:
    required_customer_cols = [
        "customer_id",
        "segment",
        "total_sales",
        "total_profit"
    ]

    missing = [
        col for col in required_customer_cols
        if col not in customers.columns
    ]

    if missing:
        st.warning(
            "Customer segmentation file is missing columns: "
            + ", ".join(missing)
        )
    else:
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

            st.plotly_chart(
                apply_dark_chart_theme(fig_count),
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

            st.plotly_chart(
                apply_dark_chart_theme(fig_sales),
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

        st.plotly_chart(
            apply_dark_chart_theme(fig_profit),
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
    st.info(
        "Customer segmentation CSV is not available. "
        "Product and category analysis can still be viewed below."
    )


# ==================================================
# 6. PRODUCT PROFITABILITY AND LOSS ANALYSIS
# ==================================================

st.divider()
st.header("Product Profitability & Loss Analysis")

st.write(
    "Identify products that generate the highest profit "
    "and products that operate at a loss."
)

try:
    product_df = load_product_profitability()

    if product_df.empty:
        st.info("No product profitability records found.")
    else:
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

        col1.metric("Products Analysed", f"{len(product_df):,}")
        col2.metric("Profitable Products", f"{len(profitable_products):,}")
        col3.metric("Products with Loss", f"{len(loss_products):,}")

        st.subheader("Top 10 Most Profitable Products")

        top_products = (
            product_df.nlargest(10, "total_profit")
            .sort_values("total_profit", ascending=True)
        )

        fig_top = px.bar(
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

        st.plotly_chart(
            apply_dark_chart_theme(fig_top),
            use_container_width=True
        )

        st.subheader("Top 10 Products with Highest Loss")

        if not loss_products.empty:
            worst_products = (
                loss_products.nsmallest(10, "total_profit")
                .sort_values("total_profit", ascending=True)
            )

            fig_loss = px.bar(
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

            st.plotly_chart(
                apply_dark_chart_theme(fig_loss),
                use_container_width=True
            )
        else:
            st.success("No loss-making products found.")

        st.subheader("Product Profitability Details")

        selected_category = st.selectbox(
            "Filter by Category",
            ["All Categories"] + sorted(
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

except Exception as error:
    st.error("Unable to load product profitability analysis.")
    st.exception(error)


# ==================================================
# 7. CATEGORY-WISE PROFITABILITY ANALYSIS
# ==================================================

st.divider()
st.header("Category-wise Profitability Analysis")

if "product_df" in locals() and not product_df.empty:
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
        fig_cat_sales = px.bar(
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

        st.plotly_chart(
            apply_dark_chart_theme(fig_cat_sales),
            use_container_width=True
        )

    with col2:
        fig_cat_profit = px.bar(
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

        st.plotly_chart(
            apply_dark_chart_theme(fig_cat_profit),
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

if "product_df" in locals() and not product_df.empty:
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
        subcategory_summary.nlargest(10, "total_profit")
        .sort_values("total_profit", ascending=True)
    )

    fig_sub = px.bar(
        top_subcategories,
        x="total_profit",
        y="sub_category",
        color="category",
        orientation="h",
        title="Top 10 Sub-categories by Total Profit",
        labels={
            "sub_category": "Sub-category",
            "total_profit": "Total Profit (USD)",
            "category": "Category"
        }
    )

    st.plotly_chart(
        apply_dark_chart_theme(fig_sub),
        use_container_width=True
    )

    st.subheader("Lowest Performing Sub-categories")

    bottom_subcategories = (
        subcategory_summary.nsmallest(10, "total_profit")
        .sort_values("total_profit", ascending=True)
    )

    fig_sub_loss = px.bar(
        bottom_subcategories,
        x="total_profit",
        y="sub_category",
        color="category",
        orientation="h",
        title="10 Sub-categories with Lowest Profit",
        labels={
            "sub_category": "Sub-category",
            "total_profit": "Total Profit (USD)",
            "category": "Category"
        }
    )

    st.plotly_chart(
        apply_dark_chart_theme(fig_sub_loss),
        use_container_width=True
    )

    st.subheader("Sub-category Performance Details")

    selected_category_sub = st.selectbox(
        "Filter by Product Category",
        ["All Categories"] + sorted(
            subcategory_summary["category"].dropna().unique().tolist()
        ),
        key="subcategory_category_filter"
    )

    subcategory_display = subcategory_summary.copy()

    if selected_category_sub != "All Categories":
        subcategory_display = subcategory_display[
            subcategory_display["category"] == selected_category_sub
        ]

    st.dataframe(
        subcategory_display.round(2),
        use_container_width=True,
        hide_index=True
    )

st.caption("Data source: Superstore Prepared CSV Dataset")
