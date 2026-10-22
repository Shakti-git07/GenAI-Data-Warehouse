
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(connection_url)

df = pd.read_csv("data/Superstore_Prepared.csv")

# Convert dates
df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Ship Date"] = pd.to_datetime(df["Ship Date"])

# Create date keys
df["order_date_key"] = (
    df["Order Date"].dt.strftime("%Y%m%d").astype(int)
)
df["ship_date_key"] = (
    df["Ship Date"].dt.strftime("%Y%m%d").astype(int)
)

try:
    with engine.begin() as connection:

        # Read dimension tables and build lookup dictionaries
        customers = pd.read_sql(
            text("SELECT customer_key, customer_id FROM Dim_Customer"),
            connection
        )
        products = pd.read_sql(
            text("SELECT product_key, product_id FROM Dim_Product"),
            connection
        )
        dates = pd.read_sql(
            text("SELECT date_key, full_date FROM Dim_Date"),
            connection
        )
        locations = pd.read_sql(
            text("""
                SELECT location_key, city, state, postal_code,
                       region, country
                FROM Dim_Location
            """),
            connection
        )

        customer_map = dict(zip(
            customers["customer_id"], customers["customer_key"]
        ))
        product_map = dict(zip(
            products["product_id"], products["product_key"]
        ))
        date_map = {
            pd.Timestamp(row.full_date).strftime("%Y-%m-%d"): row.date_key
            for row in dates.itertuples(index=False)
        }

        def postal_code(value):
            if pd.isna(value):
                return None
            return str(int(value)) if float(value).is_integer() else str(value)

        location_map = {
            (
                row.city, row.state, postal_code(row.postal_code),
                row.region, row.country
            ): row.location_key
            for row in locations.itertuples(index=False)
        }

        # Resolve dimension keys for every transaction
        df["customer_key"] = df["Customer ID"].map(customer_map)
        df["product_key"] = df["Product ID"].map(product_map)
        df["order_date_key"] = df["order_date_key"].astype(int)
        df["ship_date_key"] = df["ship_date_key"].astype(int)

        df["location_key"] = df.apply(
            lambda row: location_map.get((
                row["City"],
                row["State"],
                postal_code(row["Postal Code"]),
                row["Region"],
                row["Country"]
            )),
            axis=1
        )

        # Stop if any dimension mapping is missing
        key_columns = [
            "customer_key", "product_key", "order_date_key",
            "ship_date_key", "location_key"
        ]

        if df[key_columns].isna().any().any():
            raise ValueError(
                "Some dimension keys are missing. "
                "Fact data was not inserted."
            )

        # Insert transactions
        insert_sql = text("""
            INSERT INTO Fact_Sales
            (row_id, order_id, customer_key, product_key,
             order_date_key, ship_date_key, location_key,
             ship_mode, sales, quantity, discount, profit)
            VALUES
            (:row_id, :order_id, :customer_key, :product_key,
             :order_date_key, :ship_date_key, :location_key,
             :ship_mode, :sales, :quantity, :discount, :profit)
            ON DUPLICATE KEY UPDATE
                order_id = VALUES(order_id),
                customer_key = VALUES(customer_key),
                product_key = VALUES(product_key),
                order_date_key = VALUES(order_date_key),
                ship_date_key = VALUES(ship_date_key),
                location_key = VALUES(location_key),
                ship_mode = VALUES(ship_mode),
                sales = VALUES(sales),
                quantity = VALUES(quantity),
                discount = VALUES(discount),
                profit = VALUES(profit)
        """)

        for start in range(0, len(df), 500):
            batch = df.iloc[start:start + 500]

            records = []
            for _, row in batch.iterrows():
                records.append({
                    "row_id": int(row["Row ID"]),
                    "order_id": row["Order ID"],
                    "customer_key": int(row["customer_key"]),
                    "product_key": int(row["product_key"]),
                    "order_date_key": int(row["order_date_key"]),
                    "ship_date_key": int(row["ship_date_key"]),
                    "location_key": int(row["location_key"]),
                    "ship_mode": row["Ship Mode"],
                    "sales": float(row["Sales"]),
                    "quantity": int(row["Quantity"]),
                    "discount": float(row["Discount"]),
                    "profit": float(row["Profit"])
                })

            connection.execute(insert_sql, records)

        fact_count = connection.execute(
            text("SELECT COUNT(*) FROM Fact_Sales")
        ).scalar()

        print("Fact table loaded successfully!")
        print("Rows in source CSV:", len(df))
        print("Rows in Fact_Sales:", fact_count)

except Exception as error:
    print("Error loading fact data:", error)

finally:
    engine.dispose()
