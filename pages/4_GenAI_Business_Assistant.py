
import os
import json

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="GenAI Business Assistant",
    page_icon="🤖",
    layout="wide"
)

PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(PROJECT_FOLDER, ".env"))


# ==================================================
# 2. BLACK + BLUE/PURPLE THEME
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
        border-right: 1px solid #292943;
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
            135deg, #10101A, #171329
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

    [data-testid="stExpander"] {
        background: #09090F;
        border: 1px solid #30264F;
        border-radius: 10px;
    }

    [data-testid="stTabs"] button {
        color: #C4B5FD;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #A5B4FC;
        border-bottom-color: #8B5CF6;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #292943;
        border-radius: 10px;
        overflow: hidden;
    }

    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {
        background: #10101A;
        color: #FFFFFF;
        border: 1px solid #393052;
        border-radius: 8px;
    }

    [data-testid="stSelectbox"] > div > div {
        background: #10101A;
        color: #FFFFFF;
        border-color: #393052;
    }

    [data-testid="stForm"] {
        background: #09090F;
        border: 1px solid #292943;
        border-radius: 12px;
        padding: 18px;
    }

    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(
            90deg, #4F46E5, #7C3AED
        );
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 650;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(
            90deg, #6366F1, #8B5CF6
        );
        color: #FFFFFF;
        border: none;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    hr {
        border-color: #292943 !important;
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. PAGE HEADER
# ==================================================

st.title("🤖 GenAI Business Assistant")

st.caption(
    "AI-powered business insights using the Enterprise Data Warehouse"
)


# ==================================================
# 4. DATABASE CONNECTION
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
# 5. GEMINI CLIENT
# ==================================================

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key was not found. "
            "Please check the .env file."
        )

    return genai.Client(api_key=api_key)


# ==================================================
# 6. LOAD BUSINESS DATA FROM MYSQL
# ==================================================

@st.cache_data(ttl=60)
def load_business_data():
    engine = get_engine()

    queries = {
        "overall": """
            SELECT
                COUNT(*) AS sales_records,
                COUNT(DISTINCT order_id) AS unique_orders,
                ROUND(SUM(sales), 2) AS total_sales,
                ROUND(SUM(profit), 2) AS total_profit,
                SUM(quantity) AS total_quantity,
                ROUND(AVG(discount), 4) AS average_discount
            FROM Fact_Sales
        """,

        "category": """
            SELECT
                p.category,
                ROUND(SUM(f.sales), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit,
                SUM(f.quantity) AS total_quantity
            FROM Fact_Sales f
            JOIN Dim_Product p
                ON f.product_key = p.product_key
            GROUP BY p.category
            ORDER BY total_profit DESC
        """,

        "subcategory": """
            SELECT
                p.category,
                p.sub_category,
                ROUND(SUM(f.sales), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit,
                SUM(f.quantity) AS total_quantity
            FROM Fact_Sales f
            JOIN Dim_Product p
                ON f.product_key = p.product_key
            GROUP BY p.category, p.sub_category
            ORDER BY total_profit DESC
        """,

        "region": """
            SELECT
                l.region,
                ROUND(SUM(f.sales), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit
            FROM Fact_Sales f
            JOIN Dim_Location l
                ON f.location_key = l.location_key
            GROUP BY l.region
            ORDER BY total_profit DESC
        """,

        "monthly": """
            SELECT
                d.year,
                d.month,
                ROUND(SUM(f.sales), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit
            FROM Fact_Sales f
            JOIN Dim_Date d
                ON f.order_date_key = d.date_key
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month
        """,

        "products": """
            SELECT
                p.product_name,
                p.category,
                p.sub_category,
                ROUND(SUM(f.sales), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit
            FROM Fact_Sales f
            JOIN Dim_Product p
                ON f.product_key = p.product_key
            GROUP BY
                p.product_name,
                p.category,
                p.sub_category
            ORDER BY total_profit DESC
        """
    }

    data = {}

    with engine.connect() as connection:
        for name, query in queries.items():
            data[name] = pd.read_sql(
                text(query),
                connection
            )

    return data


# ==================================================
# 7. CUSTOMER SEGMENTATION RESULTS
# ==================================================

CUSTOMER_SEGMENTATION = [
    {
        "segment": "High Sales",
        "customers": 59,
        "average_orders": 8.27,
        "average_sales": 9370.80,
        "average_profit": 2213.02
    },
    {
        "segment": "Medium Sales",
        "customers": 324,
        "average_orders": 8.34,
        "average_sales": 3461.22,
        "average_profit": 368.91
    },
    {
        "segment": "Low Sales",
        "customers": 410,
        "average_orders": 4.43,
        "average_sales": 1519.24,
        "average_profit": 88.54
    }
]


# ==================================================
# 8. LOAD AND DISPLAY WAREHOUSE SUMMARY
# ==================================================

try:
    business_data = load_business_data()
    overall = business_data["overall"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    total_sales = overall["total_sales"]
    total_profit = overall["total_profit"]

    col1.metric(
        "Total Sales",
        (
            f"${total_sales:,.2f}"
            if pd.notna(total_sales)
            else "N/A"
        )
    )

    col2.metric(
        "Total Profit",
        (
            f"${total_profit:,.2f}"
            if pd.notna(total_profit)
            else "N/A"
        )
    )

    col3.metric(
        "Unique Orders",
        f"{int(overall['unique_orders']):,}"
    )

    col4.metric(
        "Sales Records",
        f"{int(overall['sales_records']):,}"
    )

except Exception as error:
    st.error(
        "Unable to connect to the Data Warehouse. "
        "Please check the MySQL service and database configuration."
    )
    st.exception(error)
    st.stop()


# ==================================================
# 9. BUSINESS DATA PREVIEW
# ==================================================

st.subheader("📊 Explore Business Data")

with st.expander(
    "Explore Business Data",
    expanded=False
):

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Categories",
            "Sub-Categories",
            "Regions",
            "Products",
            "Customer Segments"
        ]
    )

    with tab1:
        st.dataframe(
            business_data["category"],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.dataframe(
            business_data["subcategory"],
            use_container_width=True,
            hide_index=True
        )

    with tab3:
        st.dataframe(
            business_data["region"],
            use_container_width=True,
            hide_index=True
        )

    with tab4:
        st.dataframe(
            business_data["products"].head(20),
            use_container_width=True,
            hide_index=True
        )

    with tab5:
        st.dataframe(
            pd.DataFrame(CUSTOMER_SEGMENTATION),
            use_container_width=True,
            hide_index=True,
            column_config={
                "segment": "Customer Segment",
                "customers": st.column_config.NumberColumn(
                    "Number of Customers",
                    format="%d"
                ),
                "average_orders": st.column_config.NumberColumn(
                    "Average Orders",
                    format="%.2f"
                ),
                "average_sales": st.column_config.NumberColumn(
                    "Average Sales",
                    format="$%.2f"
                ),
                "average_profit": st.column_config.NumberColumn(
                    "Average Profit",
                    format="$%.2f"
                )
            }
        )


# ==================================================
# 10. BUSINESS QUESTION SUGGESTIONS
# ==================================================

st.divider()

st.subheader("💡 Ask Your Business Question")

st.write(
    "Ask questions about sales, profit, products, categories, "
    "regions, monthly trends, or customer segmentation."
)

suggested_questions = [
    "Which category generates the highest profit?",
    "Which region has the highest sales?",
    "Which products are making losses?",
    "Summarize the overall business performance.",
    "What are the monthly sales trends?",
    "Which sub-categories generate the lowest profit?",
    "Identify the 5 most loss-making products. Include each product name and exact total profit from the warehouse data.",
    "Explain the customer segmentation results.",
    "Which customer segment has the highest average sales and profit?",
    "Compare High Sales, Medium Sales and Low Sales customers."
]

selected_question = st.selectbox(
    "Choose a sample question",
    ["Select a question..."] + suggested_questions
)

with st.form("business_question_form"):

    user_question = st.text_area(
        "Enter your question",
        value=(
            selected_question
            if selected_question != "Select a question..."
            else ""
        ),
        placeholder=(
            "Example: Which category generates the highest profit?"
        ),
        height=100
    )

    submitted = st.form_submit_button(
        "✨ Generate Business Insights",
        type="primary",
        use_container_width=True
    )


# ==================================================
# 11. GENERATE AI INSIGHTS
# ==================================================

if submitted:

    if not user_question.strip():
        st.warning("Please enter a business question.")

    else:
        try:
            client = get_gemini_client()

            products = business_data["products"]

            loss_making_products = (
                products.loc[
                    products["total_profit"] < 0
                ]
                .sort_values(
                    by="total_profit",
                    ascending=True
                )
                .head(10)
            )

            profitable_products = (
                products.loc[
                    products["total_profit"] > 0
                ]
                .sort_values(
                    by="total_profit",
                    ascending=False
                )
                .head(10)
            )

            # Display verified loss-making products.

            with st.expander(
                "📉 View Verified Loss-Making Products",
                expanded=False
            ):
                st.caption(
                    "These figures are calculated from the MySQL Data Warehouse."
                )

                st.dataframe(
                    loss_making_products[
                        [
                            "product_name",
                            "category",
                            "sub_category",
                            "total_sales",
                            "total_profit"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "product_name": "Product",
                        "category": "Category",
                        "sub_category": "Sub-Category",
                        "total_sales": st.column_config.NumberColumn(
                            "Total Sales",
                            format="$%.2f"
                        ),
                        "total_profit": st.column_config.NumberColumn(
                            "Total Profit",
                            format="$%.2f"
                        )
                    }
                )

            # Prepare business data for Gemini.

            context = {
                "overall_business_summary":
                    business_data["overall"].to_dict(
                        orient="records"
                    ),

                "category_performance":
                    business_data["category"].to_dict(
                        orient="records"
                    ),

                "subcategory_performance":
                    business_data["subcategory"].to_dict(
                        orient="records"
                    ),

                "regional_performance":
                    business_data["region"].to_dict(
                        orient="records"
                    ),

                "monthly_performance":
                    business_data["monthly"].tail(24).to_dict(
                        orient="records"
                    ),

                "top_10_profitable_products":
                    profitable_products.to_dict(
                        orient="records"
                    ),

                "top_10_loss_making_products":
                    loss_making_products.to_dict(
                        orient="records"
                    ),

                "customer_segmentation":
                    CUSTOMER_SEGMENTATION
            }

            business_context = json.dumps(
                context,
                indent=2,
                default=str
            )

            prompt = f"""
You are an AI Business Analytics Assistant.

Answer the user's question using only the business data
provided below.

RULES:

1. Use the supplied warehouse data as the source of truth.
2. Do not invent figures, records, or business facts.
3. If the data does not answer a question, explain the limitation.
4. Clearly distinguish sales from profit.
5. Format monetary values in US dollars.
6. Provide a clear answer followed by useful business insights.
7. Keep the response professional and easy to understand.
8. Treat negative profit as a loss.
9. When discussing loss-making products, rank the largest losses first.
10. Distinguish observed results from possible explanations.
11. Do not execute SQL or request database credentials.
12. Format monetary values clearly, for example $145,455.66.
13. Copy product sales and profit figures exactly from the supplied data.
14. Never estimate or change a supplied product figure.
15. For loss-making products, show the exact negative profit value.
16. Do not combine, repeat, or corrupt numbers or currency symbols.
17. If a value is unavailable, state that it is unavailable.
18. Keep tables and bullet points readable and correctly formatted.
19. Customer segmentation data is provided under
    "customer_segmentation".
20. When asked about customer segments, use those supplied values.
21. Do not claim that customer segmentation data is unavailable
    when it is present in the supplied context.
22. The customer counts are:
    High Sales: 59,
    Medium Sales: 324,
    Low Sales: 410.
23. Average sales and average profit are different metrics.
    Never confuse them.
24. Explain the customer segment comparison using the exact
    supplied values.
25. Do not claim a cause for a business result unless the data
    supports it.
26. Use readable Markdown tables when comparisons are helpful.

BUSINESS DATA:

{business_context}

USER QUESTION:

{user_question}
"""

            with st.spinner(
                "🤖 Analyzing business data..."
            ):

                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt
                )

            if response.text and response.text.strip():

                st.divider()

                st.subheader(
                    "✨ AI-Generated Business Insights"
                )

                # Display AI response as readable Markdown.
                st.markdown(response.text)

                st.caption(
                    "Generated using Gemini and data retrieved "
                    "from the MySQL Data Warehouse."
                )

            else:
                st.warning(
                    "The AI model returned an empty response. "
                    "Please try again."
                )

        except Exception as error:

            error_message = str(error).lower()

            if (
                "429" in error_message
                or "resource_exhausted" in error_message
                or "quota" in error_message
            ):
                st.warning(
                    "The AI service is temporarily rate-limited "
                    "or its available quota has been reached. "
                    "Please check your Gemini API usage and try again later."
                )

            elif (
                "api key" in error_message
                or "401" in error_message
                or "403" in error_message
                or "unauthenticated" in error_message
            ):
                st.error(
                    "The AI service could not authenticate the request. "
                    "Please check the API key configuration in the .env file."
                )

            else:
                st.error(
                    "Unable to generate business insights. "
                    "Please check the connection and try again."
                )

                st.caption(
                    f"Technical details: {error}"
                )


# ==================================================
# 12. FOOTER
# ==================================================

st.divider()

st.caption(
    "GenAI-Ready Enterprise Data Warehouse | "
    "AI-Powered Business Decision Support"
)
