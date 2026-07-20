"""
Week 2-3 Deliverable - Dataset Structuring and Validation (Sold + Listings)
"""

import pandas as pd
import os
from pathlib import Path 

DELIVERABLES_FOLDER = str(Path.home() / "Downloads" / "IDX_Local_Data" / "drive-download-20260623T184602Z-3-001")
NUMERIC_FIELDS = ['ClosePrice','LivingArea','DaysOnMarket']

# 1 label --> (unfiltered filename, filtered filename)
DATASETS = {
    'Sold': ('sold_combined_raw.csv','sold.csv'),
    'Listings':('listings_combined_raw.csv','listings.csv'),
    }

def load_source(unfiltered_filename,filtered_filename):
    """
    Will try unfiltered file first and fallas back to the filtered file. Returns (df, was_unfiltered)
    """
    unfiltered_path = os.path.join(DELIVERABLES_FOLDER,unfiltered_filename)
    filtered_path = os.path.join(DELIVERABLES_FOLDER,filtered_filename)

    if os.path.exists(unfiltered_path):
        print(f"Found unfiltered file: {unfiltered_path}")
        return pd.read_csv(unfiltered_path, low_memory=False), True
    
    print(f"No unfiltered file found at {unfiltered_path}.")
    print(f"Falling back to filtered file:{filtered_path}")
    return pd.read_csv(filtered_path,low_memory=False), False

def validate_dataset(label, unfiltered_filename, filtered_filename):
    print("="*70)
    print(f"{label.upper()} DATASET - WEEK 2-3 VALIDATION")
    print("="*70)

    df,was_unfiltered = load_source(unfiltered_filename, filtered_filename)

    #1. Unique property types + filtering logic
    print(f"\nUnique PropertyType values found: {df['PropertyType'].unique()}")

    rows_before=len(df)
    var_name=label.lower()

    if was_unfiltered:
        df = df[df['PropertyType']=='Residential'].copy()
        rows_after=len(df)
        print("Filtering logic applied:")
        print(f"  {var_name} ={var_name}[{var_name}.PropertyType == 'Residential']")
        print(f"Rows before filter: {rows_before:,}")
        print(f"Rows after filter: {rows_after:,}")
        print(f"Rows removed:   {rows_before - rows_after:,}")

    else:
        print("This dataset was already filtered to Residential in Week 1,")
        print("so only 'Residential' will appear above. The filter was applied here:")
        print(f"    {var_name} = {var_name}[{var_name}.PropertyType == 'Residential']")
        print(f"(Row count at this stage: {rows_before:,})")

    # 2 Null-count summary table
    null_counts = df.isnull().sum()
    print("\nNull-count summary table:")
    print(null_counts.to_string())

    #3 Missing value report - flag columns above 90% null
    missing_pct = (null_counts/len(df)*100).round(2)
    missing_report=pd.DataFrame({
        'column':df.columns,
        'null_count':null_counts.values,
        'null_pct':missing_pct.values
    }).sort_values('null_pct',ascending=False)

    high_missing=missing_report[missing_report['null_pct']>90]
    print(f"\nColumns above 90% null ({len(high_missing)} total):")
    if len(high_missing) > 0:
        print(high_missing[['column','null_pct']].to_string(index=False))
    else:
        print(" None")

    #4 Numeric distribution summary 
    print("\nNumeric distribution summary:")
    for field in NUMERIC_FIELDS:
        if field not in df.columns:
            print(f"    [{field}] not found in {label} dataset - skipping")
            continue 

        series = pd.to_numeric(df[field], errors='coerce').dropna()
        if len(series) == 0:
            print(f"    [{field}] has no usable numeric data - skipping")
            continue 

        print(f"\n  {field}")
        print(f"    min:        {series.min():,.2f}")
        print(f"    max:        {series.max():,.2f}")
        print(f"    mean:        {series.mean():,.2f}")
        print(f"    median:        {series.median():,.2f}")
        print(f"    25th percentile:        {series.quantile(0.25):,.2f}")
        print(f"    75th percentile:        {series.quantile(0.75):,.2f}")
        print(f"    99th percentile:        {series.quantile(0.99):,.2f}")

    #5 Save the filtered dataset 
    output_path=os.path.join(DELIVERABLES_FOLDER, f"{var_name}_validated.csv")
    df.to_csv(output_path,index=False)
    print(f"\nSaved validated {label} dataset to {output_path} ({len(df):,} rows)")
    print()

def main():
    for label, (unfiltered_filename, filtered_filename) in DATASETS.items():
        validate_dataset(label, unfiltered_filename, filtered_filename)

if __name__=="__main__":
    main()



    
