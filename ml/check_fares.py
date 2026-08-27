import pandas as pd
import os

df = pd.read_csv('redbus_fares.csv')
path = os.path.abspath('redbus_fares.csv')
size_kb = os.path.getsize(path) / 1024

print("=== CSV LOCATION ===")
print(path)
print(f"File size: {size_kb:.1f} KB")
print(f"Total rows: {len(df)}")

print("\n=== BUS TYPE BREAKDOWN ===")
print(df['bus_type'].value_counts().head(10).to_string())

print("\n=== SEATER vs SLEEPER vs MIXED ===")
print(df['is_sleeper'].value_counts().to_string())

print("\n=== SAMPLE: Seater vs Sleeper fares ===")
sample = df[['operator_name', 'bus_type', 'is_sleeper', 'is_ac', 'min_fare_inr', 'fare_list']].head(12)
print(sample.to_string())

print("\n=== FARE_LIST DETAIL (what does fare_list actually contain?) ===")
for i, row in df.head(6).iterrows():
    print(f"Operator: {row['operator_name']}")
    print(f"  Bus Type: {row['bus_type']}")
    print(f"  Is Sleeper: {row['is_sleeper']}")
    print(f"  Min Fare: {row['min_fare_inr']}")
    print(f"  All Fares: {row['fare_list']}")
    print()
