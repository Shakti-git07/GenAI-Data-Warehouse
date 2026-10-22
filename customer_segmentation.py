
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load database settings from .env
load_dotenv()

# Connect to MySQL Data Warehouse
connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "genai_data_warehouse")
)

engine = create_engine(connection_url, pool_pre_ping=True)

# Get customer-level sales information
query = """
    SELECT
        c.customer_id,
        c.customer_name,
        COUNT(DISTINCT f.order_id) AS total_orders,
        SUM(f.sales) AS total_sales,
        SUM(f.profit) AS total_profit
    FROM Fact_Sales f
    JOIN Dim_Customer c
        ON f.customer_key = c.customer_key
    GROUP BY c.customer_id, c.customer_name
"""

with engine.connect() as connection:
    customers = pd.read_sql(text(query), connection)

if customers.empty:
    raise ValueError("No customer records found in the warehouse.")

# Prepare features for clustering
features = customers[
    ["total_orders", "total_sales", "total_profit"]
].copy()

# Replace any missing numeric values
features = features.fillna(0)

# Scale features because their ranges differ
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Divide customers into 3 clusters
model = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

customers["cluster"] = model.fit_predict(scaled_features)

# Create understandable cluster labels using average sales
cluster_sales = customers.groupby("cluster")["total_sales"].mean()
ranked_clusters = cluster_sales.sort_values().index.tolist()

cluster_names = {
    ranked_clusters[0]: "Low Sales",
    ranked_clusters[1]: "Medium Sales",
    ranked_clusters[2]: "High Sales"
}

customers["segment"] = customers["cluster"].map(cluster_names)

# Summarize each customer segment
summary = (
    customers.groupby("segment", as_index=False)
    .agg(
        customer_count=("customer_id", "count"),
        average_orders=("total_orders", "mean"),
        average_sales=("total_sales", "mean"),
        average_profit=("total_profit", "mean")
    )
)

# Display results
print("\nCUSTOMER SEGMENTATION COMPLETED")
print("--------------------------------")
print(f"Total customers analysed: {len(customers)}")

print("\nSEGMENT SUMMARY:")
print(summary.round(2).to_string(index=False))

print("\nSAMPLE CUSTOMER RESULTS:")
print(
    customers[
        [
            "customer_id",
            "customer_name",
            "total_orders",
            "total_sales",
            "total_profit",
            "segment"
        ]
    ]
    .head(10)
    .round(2)
    .to_string(index=False)
)

# Save results for later dashboard integration
output_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "customer_segments.csv"
)

customers.to_csv(output_path, index=False)

print(f"\nResults saved to: {output_path}")
