"""
Week 2-3 Deliverable - Mortgage Rate Enrichment (Sold + Listings)
"""

import pandas as pd
from pathlib import Path 

DELIVERABLES_FOLDER = str(Path.home() / "Downloads" / "IDX_Local_Data" / "drive-download-20260623T184602Z-3-001")

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

def fetch_monthly_mortgage_rates():
    """
    Fetches the weekly MORTGAGE30US series from FRED and resamples it to monthly averages.
    """

    print("Fetching mortgage rate data from FRED...")
    mortgage = pd.read_csv(FRED_URL, parse_dates=['observation_date'])
    mortgage.columns = ['date', 'rate_30yr_fixed']

    mortgage['year_month'] = mortgage['date'].dt.to_period('M')

    mortgage_monthly = (
        mortgage.groupby('year_month')['rate_30yr_fixed']
        .mean()
        .reset_index()
    )

    print(f"Fetched and resampled {len(mortgage_monthly)} months of mortgage rate data.")
    return mortgage_monthly

def enrich_dataset(label, filename, date_column, mortgage_monthly):
    """
    Loads a dataset, creates a year_month key from date_column, merges in the mortgage rate, 
    validates the merge, and saves the enriched dataset.
    """

    print("\n" + "=" * 70)
    print(f"{label.upper()} DATASET - MORTGAGE RATE ENRICHMENT")
    print("=" * 70)

    input_path = Path(DELIVERABLES_FOLDER) / filename
    df = pd.read_csv(input_path, low_memory=False)
    print(f"Loaded {filename}: {len(df):,} rows")

    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df['year_month'] = df[date_column].dt.to_period('M')

    enriched = df.merge(mortgage_monthly, on='year_month', how='left')

    null_rates = enriched['rate_30yr_fixed'].isnull().sum()
    print(f"\nValidation check:")
    print(f"Rows with null rate_30yr_fixed after merge: {null_rates:,}")
    if null_rates > 0:
        print("Some rows did not match a mortgage rate - check for missing/invalid dates or months outside FRED's range.")
    else:
        print("No null rate values - merge successful for all rows.")

    print(f"\nPreview:")
    print(enriched[[date_column, 'year_month', 'rate_30yr_fixed']].head())

    output_path = Path(DELIVERABLES_FOLDER) / f"{label.lower()}_with_rates.csv"
    enriched.to_csv(output_path, index=False)
    print(f"\nSaved enriched {label} dataset to {output_path} ({len(enriched):,} rows)")

    return enriched 

def main():
    mortgage_monthly = fetch_monthly_mortgage_rates()

    enrich_dataset(
        label="Sold",
        filename="sold.csv",
        date_column="CloseDate",
        mortgage_monthly=mortgage_monthly
    )

    enrich_dataset(
        label="Listings",
        filename="listings.csv",
        date_column="ListingContractDate",
        mortgage_monthly=mortgage_monthly
    )

    print("\n" + "=" * 70)
    print("Week 2-3 Mortgage Rate Enrichment Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
    


