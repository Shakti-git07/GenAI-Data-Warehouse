
import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None


# ==================================================
# 1. CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="GenAI Business Assistant",
    page_icon="🤖",
    layout="wide"
)

PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CSV_PATH = os.path.join(
    PROJECT_FOLDER, "data", "Superstore_Prepared.csv"
)

load_dotenv(os.path.join(PROJECT_FOLDER, ".env"))


def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY", "")


# ==================================================
# 2. THEME
# ==================================================

st.markdown("""
<style>
.stApp { background:#000000; color:#F5F5F7; }
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background:#000000;
}
[data-testid="stSidebar"] {
    background:#08080D;
    border-right:1px solid #292943;
}
h1 { color:#FFFFFF !important; }
h2, h3 { color:#C4B5FD !important; }
p, label { color:#D1D5DB; }
[data-testid="stMetric"] {
    background:linear-gradient(135deg,#10101A,#171329);
    border:1px solid #30264F;
    border-radius:12px;
    padding:18px;
}
[data-testid="stMetricLabel"] { color:#A5B4FC !important; }
[data-testid="stMetricValue"] { color:#FFFFFF !important; }
[data-testid="stDataFrame"] {
    border:1px solid #292943;
    border-radius:10px;
}
[data-testid="stForm"] {
    background:#09090F;
    border:1px solid #292943;
    border-radius:12px;
    padding:18px;
}
hr { border-color:#292943 !important; }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. DATA LOADING
# ==================================================

@st.cache_data(ttl=60)
def load_business_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            "data/Superstore_Prepared.csv not found in the repository."
        )

    df = pd.read_csv(CSV_PATH)

    required = [
        "Order ID", "Order Date", "Customer ID",
        "Product ID", "Product Name", "Category",
        "Sub-Category", "Region", "Sales", "Profit",
        "Quantity", "Discount"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            "Missing columns in CSV: " + ", ".join(missing)
        )

    df["Order Date"] = pd.to_datetime(
        df["Order Date"], errors="coerce"
    )

    for col in ["Sales", "Profit", "Quantity", "Discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["Order ID", "Order Date", "Sales", "Profit"]
    ).copy()

    overall = pd.DataFrame([{
        "sales_records": len(df),
        "unique_orders": df["Order ID"].nunique(),
        "total_sales": df["Sales"].sum(),
        "total_profit": df["Profit"].sum(),
        "total_quantity": df["Quantity"].sum(),
        "average_discount": df["Discount"].mean()
    }])

    category = (
        df.groupby("Category", as_index=False)
        .agg(
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum"),
            total_quantity=("Quantity", "sum")
        )
        .rename(columns={"Category": "category"})
        .sort_values("total_profit", ascending=False)
    )

    subcategory = (
        df.groupby(["Category", "Sub-Category"], as_index=False)
        .agg(
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum"),
            total_quantity=("Quantity", "sum")
        )
        .rename(columns={
            "Category": "category",
            "Sub-Category": "sub_category"
        })
        .sort_values("total_profit", ascending=False)
    )

    region = (
        df.groupby("Region", as_index=False)
        .agg(
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum")
        )
        .rename(columns={"Region": "region"})
        .sort_values("total_profit", ascending=False)
    )

    monthly = (
        df.assign(
            year=df["Order Date"].dt.year,
            month=df["Order Date"].dt.month
        )
        .groupby(["year", "month"], as_index=False)
        .agg(
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum")
        )
        .sort_values(["year", "month"])
    )

    products = (
        df.groupby(
            ["Product Name", "Category", "Sub-Category"],
            as_index=False
        )
        .agg(
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum")
        )
        .rename(columns={
            "Product Name": "product_name",
            "Category": "category",
            "Sub-Category": "sub_category"
        })
        .sort_values("total_profit", ascending=False)
    )

    # Customer segmentation using total customer sales.
    customer = (
        df.groupby(["Customer ID"], as_index=False)
        .agg(
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum"),
            total_orders=("Order ID", "nunique")
        )
    )

    low_cut = customer["total_sales"].quantile(1 / 3)
    high_cut = customer["total_sales"].quantile(2 / 3)

    customer["segment"] = customer["total_sales"].apply(
        lambda x: (
            "Low Sales" if x <= low_cut
            else "Medium Sales" if x <= high_cut
            else "High Sales"
        )
    )

    segments = (
        customer.groupby("segment", as_index=False)
        .agg(
            customers=("Customer ID", "nunique"),
            average_orders=("total_orders", "mean"),
            average_sales=("total_sales", "mean"),
            average_profit=("total_profit", "mean")
        )
    )

    segment_order = ["High Sales", "Medium Sales", "Low Sales"]
    segments["segment"] = pd.Categorical(
        segments["segment"],
        categories=segment_order,
        ordered=True
    )
    segments = segments.sort_values("segment")
    segments["segment"] = segments["segment"].astype(str)

    return {
        "raw": df,
        "overall": overall,
        "category": category,
        "subcategory": subcategory,
        "region": region,
        "monthly": monthly,
        "products": products,
        "segments": segments
    }


# ==================================================
# 4. GEMINI CLIENT
# ==================================================

def generate_ai_answer(question, context):
    api_key = get_api_key()

    if not api_key:
        return None, (
            "Gemini API key is not configured. Add "
            "GEMINI_API_KEY to Streamlit Cloud → Settings → Secrets, "
            "or to your local .env file."
        )

    if genai is None:
        return None, (
            "The google-genai package is not installed. "
            "Add google-genai to requirements.txt."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an AI Business Analytics Assistant.

Answer the question using only the supplied Superstore business data.
Do not invent numbers. Clearly distinguish sales and profit.
Format currency in USD. Negative profit means a loss.
Use readable Markdown and provide practical, data-supported insights.
If the data does not answer the question, say so.

BUSINESS DATA:
{json.dumps(context, indent=2, default=str)}

USER QUESTION:
{question}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return response.text, None


# ==================================================
# 5. PAGE HEADER
# ==================================================

st.title("🤖 GenAI Business Assistant")
st.caption(
    "AI-powered business insights using the prepared enterprise dataset"
)


# ==================================================
# 6. LOAD AND DISPLAY SUMMARY
# ==================================================

try:
    business_data = load_business_data()
except Exception as error:
    st.error("Unable to load the business dataset.")
    st.exception(error)
    st.stop()

overall = business_data["overall"].iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"${overall['total_sales']:,.2f}")
c2.metric("Total Profit", f"${overall['total_profit']:,.2f}")
c3.metric("Unique Orders", f"{int(overall['unique_orders']):,}")
c4.metric("Sales Records", f"{int(overall['sales_records']):,}")


# ==================================================
# 7. EXPLORE BUSINESS DATA
# ==================================================

st.divider()
st.subheader("📊 Explore Business Data")

with st.expander("Explore Business Data", expanded=False):
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Categories", "Sub-Categories", "Regions",
        "Products", "Customer Segments"
    ])

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
            business_data["segments"].round(2),
            use_container_width=True,
            hide_index=True
        )


# ==================================================
# 8. SUGGESTED QUESTIONS
# ==================================================

st.divider()
st.subheader("💡 Ask Your Business Question")

suggested_questions = [
    "Which category generates the highest profit?",
    "Which region has the highest sales?",
    "Which products are making losses?",
    "Summarize overall business performance.",
    "What are the monthly sales trends?",
    "Which sub-categories generate the lowest profit?",
    "List the 5 most loss-making products with exact profit.",
    "Explain customer segmentation results.",
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
        placeholder="Example: Which category generates the highest profit?",
        height=100
    )

    submitted = st.form_submit_button(
        "✨ Generate Business Insights",
        type="primary",
        use_container_width=True
    )


# ==================================================
# 9. AI ANSWER
# ==================================================

if submitted:
    if not user_question.strip():
        st.warning("Please enter a business question.")
    else:
        df_products = business_data["products"]

        loss_products = (
            df_products[df_products["total_profit"] < 0]
            .sort_values("total_profit")
            .head(10)
        )

        top_products = (
            df_products[df_products["total_profit"] > 0]
            .sort_values("total_profit", ascending=False)
            .head(10)
        )

        context = {
            "overall": business_data["overall"].to_dict("records"),
            "category": business_data["category"].to_dict("records"),
            "subcategory": business_data["subcategory"].to_dict("records"),
            "region": business_data["region"].to_dict("records"),
            "monthly_last_24": business_data["monthly"].tail(24).to_dict("records"),
            "top_profitable_products": top_products.to_dict("records"),
            "loss_making_products": loss_products.to_dict("records"),
            "customer_segmentation": business_data["segments"].to_dict("records")
        }

        with st.expander("📉 View Verified Loss-Making Products"):
            st.dataframe(
                loss_products,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "total_sales": st.column_config.NumberColumn(
                        "Total Sales", format="$%.2f"
                    ),
                    "total_profit": st.column_config.NumberColumn(
                        "Total Profit", format="$%.2f"
                    )
                }
            )

        with st.spinner("🤖 Analyzing business data..."):
            try:
                answer, error_message = generate_ai_answer(
                    user_question,
                    context
                )

                if error_message:
                    st.warning(error_message)
                elif answer:
                    st.divider()
                    st.subheader("✨ AI-Generated Business Insights")
                    st.markdown(answer)
                else:
                    st.warning("The AI model returned an empty response.")

            except Exception as error:
                message = str(error).lower()

                if "429" in message or "quota" in message:
                    st.warning(
                        "Gemini API quota/rate limit reached. "
                        "Check your API usage and try again later."
                    )
                elif "api key" in message or "401" in message or "403" in message:
                    st.error(
                        "Gemini authentication failed. Check your API key."
                    )
                else:
                    st.error("Unable to generate AI insights.")
                    st.caption(f"Technical details: {error}")


# ==================================================
# 10. FOOTER
# ==================================================

st.divider()
st.caption(
    "GenAI-Ready Enterprise Data Warehouse | "
    "AI-Powered Business Decision Support"
)
