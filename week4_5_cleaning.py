"""
Weeks 4-5 Deliverable - Data Cleaning and Preparation (Sold + Listings)
"""

import pandas as pd
from pathlib import Path

DELIVERABLES_FOLDER = str(Path.home() / "Downloads" / "IDX_Local_Data" / "drive-download-20260623T184602Z-3-001")

DATE_FIELDS = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate', 'ContractStatusChangeDate']

DATASETS = {
    'Sold': 'sold_with_rates.csv',
    'Listings': 'listings_with_rates.csv',
}

def drop_redundant_columns(df, label):
    """
    Drops duplicate/redundant columns created by the extraction script requesting
    the same field twice (pandas appends '.1' to the second occurrence).
    """
    redundant_cols = [col for col in df.columns if col.endswith('.1')]
    if redundant_cols:
        print(f"Dropping {len(redundant_cols)} redundant column(s) from {label}: {redundant_cols}")
        df = df.drop(columns=redundant_cols)
    else:
        print(f"No redundant '.1' columns found in {label}.")
    return df

def convert_date_fields(df):
    """
    Converts date fields to datetime, coercing invalid values to NaT.
    """
    for field in DATE_FIELDS:
        if field in df.columns:
            before_nulls = df[field].isnull().sum()
            df[field] = pd.to_datetime(df[field], errors='coerce')
            after_nulls = df[field].isnull().sum()
            newly_invalid = after_nulls - before_nulls
            print(f"  {field}: converted to datetime ({newly_invalid:,} values could not be parsed)")
    return df

def flag_invalid_numeric_values(df):
    """
    Flags (does not remove) records with invalid numeric values:
    ClosePrice <= 0, LivingArea <= 0, DaysOnMarket < 0, negative Bedrooms/Bathrooms.
    """
    df['invalid_close_price_flag'] = False
    df['invalid_living_area_flag'] = False
    df['invalid_dom_flag'] = False
    df['invalid_bedrooms_flag'] = False
    df['invalid_bathrooms_flag'] = False

    if 'ClosePrice' in df.columns:
        close_price_numeric = pd.to_numeric(df['ClosePrice'], errors='coerce')
        df['invalid_close_price_flag'] = close_price_numeric <= 0

    if 'LivingArea' in df.columns:
        living_area_numeric = pd.to_numeric(df['LivingArea'], errors='coerce')
        df['invalid_living_area_flag'] = living_area_numeric <= 0

    if 'DaysOnMarket' in df.columns:
        dom_numeric = pd.to_numeric(df['DaysOnMarket'], errors='coerce')
        df['invalid_dom_flag'] = dom_numeric < 0

    if 'BedroomsTotal' in df.columns:
        bedrooms_numeric = pd.to_numeric(df['BedroomsTotal'], errors='coerce')
        df['invalid_bedrooms_flag'] = bedrooms_numeric < 0

    if 'BathroomsTotalInteger' in df.columns:
        bathrooms_numeric = pd.to_numeric(df['BathroomsTotalInteger'], errors='coerce')
        df['invalid_bathrooms_flag'] = bathrooms_numeric < 0

    print(f"  Invalid ClosePrice (<=0): {df['invalid_close_price_flag'].sum():,}")
    print(f"  Invalid LivingArea (<=0): {df['invalid_living_area_flag'].sum():,}")
    print(f"  Invalid DaysOnMarket (<0): {df['invalid_dom_flag'].sum():,}")
    print(f"  Invalid Bedrooms (<0): {df['invalid_bedrooms_flag'].sum():,}")
    print(f"  Invalid Bathrooms (<0): {df['invalid_bathrooms_flag'].sum():,}")

    return df

def flag_date_consistency(df):
    """
    Flags records where date fields are out of logical order:
    ListingContractDate should precede PurchaseContractDate, which should precede CloseDate.
    """
    df['listing_after_close_flag'] = False
    df['purchase_after_close_flag'] = False
    df['negative_timeline_flag'] = False

    has_listing = 'ListingContractDate' in df.columns
    has_purchase = 'PurchaseContractDate' in df.columns
    has_close = 'CloseDate' in df.columns

    if has_listing and has_close:
        df['listing_after_close_flag'] = df['ListingContractDate'] > df['CloseDate']

    if has_purchase and has_close:
        df['purchase_after_close_flag'] = df['PurchaseContractDate'] > df['CloseDate']

    if has_listing and has_purchase and has_close:
        df['negative_timeline_flag'] = (
            df['listing_after_close_flag']
            | df['purchase_after_close_flag']
            | (df['ListingContractDate'] > df['PurchaseContractDate'])
        )

    print(f"  listing_after_close_flag: {df['listing_after_close_flag'].sum():,}")
    print(f"  purchase_after_close_flag: {df['purchase_after_close_flag'].sum():,}")
    print(f"  negative_timeline_flag: {df['negative_timeline_flag'].sum():,}")

    return df

def flag_geographic_issues(df):
    """
    Flags missing, sentinel-zero, and implausible latitude/longitude values.
    California coordinates should have negative longitude.
    """
    df['missing_coords_flag'] = False
    df['zero_coords_flag'] = False
    df['positive_longitude_flag'] = False

    has_lat = 'Latitude' in df.columns
    has_lon = 'Longitude' in df.columns

    if has_lat and has_lon:
        lat_numeric = pd.to_numeric(df['Latitude'], errors='coerce')
        lon_numeric = pd.to_numeric(df['Longitude'], errors='coerce')

        df['missing_coords_flag'] = lat_numeric.isnull() | lon_numeric.isnull()
        df['zero_coords_flag'] = (lat_numeric == 0) | (lon_numeric == 0)
        df['positive_longitude_flag'] = lon_numeric > 0

    print(f"  missing_coords_flag: {df['missing_coords_flag'].sum():,}")
    print(f"  zero_coords_flag (sentinel nulls): {df['zero_coords_flag'].sum():,}")
    print(f"  positive_longitude_flag (should be negative for CA): {df['positive_longitude_flag'].sum():,}")

    return df

def clean_dataset(label, filename):
    print("\n" + "=" * 70)
    print(f"{label.upper()} DATASET - WEEKS 4-5 CLEANING")
    print("=" * 70)

    input_path = Path(DELIVERABLES_FOLDER) / filename
    df = pd.read_csv(input_path, low_memory=False)
    rows_before = len(df)
    print(f"Loaded {filename}: {rows_before:,} rows, {len(df.columns)} columns")

    print("\nStep 1: Removing redundant columns")
    df = drop_redundant_columns(df, label)
    print(f"Columns after redundant column removal: {len(df.columns)}")

    print("\nStep 2: Converting date fields to datetime")
    df = convert_date_fields(df)

    print("\nStep 3: Flagging invalid numeric values")
    df = flag_invalid_numeric_values(df)

    print("\nStep 4: Flagging date consistency issues")
    df = flag_date_consistency(df)

    print("\nStep 5: Flagging geographic data quality issues")
    df = flag_geographic_issues(df)

    rows_after = len(df)
    print(f"\nRow count check: {rows_before:,} before cleaning -> {rows_after:,} after cleaning (no rows removed, only flagged)")

    output_path = Path(DELIVERABLES_FOLDER) / f"{label.lower()}_cleaned.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved cleaned {label} dataset to {output_path} ({len(df):,} rows, {len(df.columns)} columns)")

    return df

def main():
    for label, filename in DATASETS.items():
        clean_dataset(label, filename)

    print("\n" + "=" * 70)
    print("Weeks 4-5 Cleaning Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()