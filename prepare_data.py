
import pandas as pd
from pathlib import Path

file_path = Path("data") / "Sample - Superstore.csv"
df = pd.read_csv(file_path, encoding="latin1")

df["Order Date"] = pd.to_datetime(
    df["Order Date"], format="mixed"
)
df["Ship Date"] = pd.to_datetime(
    df["Ship Date"], format="mixed"
)

numeric_columns = ["Sales", "Quantity", "Discount", "Profit"]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="raise")

output_path = Path("data") / "Superstore_Prepared.csv"
df.to_csv(output_path, index=False)

print("Data preparation completed successfully!")
print("\nDataset shape:", df.shape)
print("\nUpdated data types:")
print(df.dtypes)
print("\nOrder Date range:")
print(df["Order Date"].min(), "to", df["Order Date"].max())
print("\nShip Date range:")
print(df["Ship Date"].min(), "to", df["Ship Date"].max())
print("\nPrepared file saved at:", output_path)
