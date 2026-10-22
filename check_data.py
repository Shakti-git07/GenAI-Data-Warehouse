
import pandas as pd
from pathlib import Path

# Load the dataset
file_path = Path("data") / "Sample - Superstore.csv"
df = pd.read_csv(file_path, encoding="latin1")

print("Dataset loaded successfully!")

print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names:")
print(df.columns.tolist())

print("\nTotal rows and columns:")
print(df.shape)

print("\nMissing values in each column:")
print(df.isnull().sum())

print("\nTotal duplicate rows:")
print(df.duplicated().sum())

print("\nDataset information:")
df.info()
