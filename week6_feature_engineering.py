"""
Week 6 Deliverable - Feature Engineering and Market Metrics (Sold) 
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path

DELIVERABLES_FOLDER = str(Path.home() / "Downloads" / "IDX_Local_Data" / "drive-download-20260623T184602Z-3-001")
INPUT_FILE = "sold_cleaned.csv"
SCHOOL_DISTRICT_PATH = str(Path.home() / "Downloads" / "DistrictAreas2526_-284845464123469011.geojson")

def load_sold_data():
    input_path = Path(DELIVERABLES_FOLDER) / INPUT_FILE
    df = pd.read_csv(input_path, low_memory=False)
    print(f"Loaded {INPUT_FILE}: {len(df):,} rows")
    return df

def engineer_metrics(df):
    """
    Creates the Week 6 metrics: Price Ratio / Close-to-Original-List Ratio (same formula),
    Price Per Sq Ft, Year/Month/YrMo, Listing-to-Contract Days, Contract-to-Close Days.
    """
    print("\nEngineering metrics...")

    df['CloseDate'] = pd.to_datetime(df['CloseDate'], errors='coerce')
    df['ListingContractDate'] = pd.to_datetime(df['ListingContractDate'], errors='coerce')
    df['PurchaseContractDate'] = pd.to_datetime(df['PurchaseContractDate'], errors='coerce')

    close_price = pd.to_numeric(df['ClosePrice'], errors='coerce')
    original_list_price = pd.to_numeric(df['OriginalListPrice'], errors='coerce')
    living_area = pd.to_numeric(df['LivingArea'], errors='coerce')

    # Price Ratio / Close to Original List Ratio (same formula, one column satisfies both)
    df['price_ratio'] = close_price / original_list_price
    print("  price_ratio (also serves as Close-to-Original-List Ratio): created")

    # Price Per Sq Ft
    df['price_per_sqft'] = close_price / living_area
    print("  price_per_sqft: created")

    # Days on Market (raw field, just confirming it's present)
    if 'DaysOnMarket' in df.columns:
        print("  DaysOnMarket: already present (raw field)")

    # Year / Month / YrMo from CloseDate
    df['close_year'] = df['CloseDate'].dt.year
    df['close_month'] = df['CloseDate'].dt.month
    df['close_yrmo'] = df['CloseDate'].dt.to_period('M').astype(str)
    print("  close_year, close_month, close_yrmo: created")

    # Listing to Contract Days
    df['listing_to_contract_days'] = (df['PurchaseContractDate'] - df['ListingContractDate']).dt.days
    print("  listing_to_contract_days: created")

    # Contract to Close Days
    df['contract_to_close_days'] = (df['CloseDate'] - df['PurchaseContractDate']).dt.days
    print("  contract_to_close_days: created")

    return df

def add_school_districts(df):
    """
    Spatially joins each property's Latitude/Longitude against CA school district
    boundaries to assign a SchoolDistrictName.
    """
    print("\nAdding school districts via spatial join...")
    print(f"Fetching school district boundaries from {SCHOOL_DISTRICT_PATH}")

    districts = gpd.read_file(SCHOOL_DISTRICT_PATH)
    print(f"Loaded {len(districts):,} school district boundary records")

    before_filter = len(districts)
    districts = districts[districts['DistrictType'] == 'Unified'].copy()
    print(f"Filtered to Unified districts: {len(districts):,} of {before_filter:,} records")

    if districts.crs is None:
        districts = districts.set_crs("EPSG:4326")
    else:
        districts = districts.to_crs("EPSG:4326")

    lat = pd.to_numeric(df['Latitude'], errors='coerce')
    lon = pd.to_numeric(df['Longitude'], errors='coerce')
    has_coords = lat.notna() & lon.notna()

    print(f"Properties with usable coordinates: {has_coords.sum():,} of {len(df):,}")

    points = gpd.GeoDataFrame(
        df[has_coords].copy(),
        geometry=gpd.points_from_xy(lon[has_coords], lat[has_coords]),
        crs="EPSG:4326"
    )

    district_name_col = 'DistrictName' if 'DistrictName' in districts.columns else districts.columns[0]

    joined = gpd.sjoin(points, districts[[district_name_col, 'geometry']], how='left', predicate='within')
    joined = joined.rename(columns={district_name_col: 'SchoolDistrictName'})
    joined = joined.drop(columns=['geometry', 'index_right'], errors='ignore')

    df = df.merge(
        joined[['ListingKey', 'SchoolDistrictName']] if 'ListingKey' in df.columns else joined[['SchoolDistrictName']],
        left_index=True, right_index=True, how='left'
    ) if 'ListingKey' not in df.columns else df.merge(
        joined[['ListingKey', 'SchoolDistrictName']], on='ListingKey', how='left'
    )
    matched = df['SchoolDistrictName'].notna().sum()
    print(f"Successfully matched {matched:,} of {len(df):,} properties to a school district")

    return df

def segment_analysis(df):
    """
    Generates summary statistics grouped by PropertyType/PropertySubType and CountyOrParish.
    """
    print("\n" + "=" * 70)
    print("SEGMENT ANALYSIS")
    print("=" * 70)

    print("\nBy PropertyType / PropertySubType:")
    if 'PropertySubType' in df.columns:
        summary_type = df.groupby(['PropertyType', 'PropertySubType']).agg(
            count=('ClosePrice', 'count'),
            median_close_price=('ClosePrice', 'median'),
            median_price_per_sqft=('price_per_sqft', 'median'),
            median_days_on_market=('DaysOnMarket', 'median'),
            median_price_ratio=('price_ratio', 'median')
        ).reset_index()
        print(summary_type.to_string(index=False))

    print("\nBy CountyOrParish:")
    if 'CountyOrParish' in df.columns:
        summary_county = df.groupby('CountyOrParish').agg(
            count=('ClosePrice', 'count'),
            median_close_price=('ClosePrice', 'median'),
            median_price_per_sqft=('price_per_sqft', 'median'),
            median_days_on_market=('DaysOnMarket', 'median'),
            median_price_ratio=('price_ratio', 'median')
        ).reset_index().sort_values('median_close_price', ascending=False)
        print(summary_county.to_string(index=False))

    return summary_type if 'PropertySubType' in df.columns else None, summary_county if 'CountyOrParish' in df.columns else None

def main():  
    df = load_sold_data()
    df = engineer_metrics(df)

    print("\nSample output (new columns):")
    sample_cols = ['ClosePrice', 'OriginalListPrice', 'price_ratio', 'LivingArea', 'price_per_sqft',
                    'close_year', 'close_month', 'close_yrmo', 'listing_to_contract_days', 'contract_to_close_days']
    print(df[sample_cols].head())

    df = add_school_districts(df)

    output_path = Path(DELIVERABLES_FOLDER) / "sold_with_metrics.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved dataset with engineered metrics to {output_path} ({len(df):,} rows)")

    segment_analysis(df)

    print("\n" + "=" * 70)
    print("Week 6 Feature Engineering Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()     