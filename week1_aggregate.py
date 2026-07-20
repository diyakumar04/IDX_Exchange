import pandas as pd
from pathlib import Path

# IDX Echange Internship 
# Week 1 - Monthly Dataset Aggregation 

# Purpose: Combine monthly CRMLS Listing and Sold CSV files into two Residential-only datasets: 
# 1. listings.csv
# 2. sold.csv 

# Notes: 
# Raw CSV files stored locally 
# Some "_filled" files have two extra columns at the end 
# If a "_filled" file is used, the last two columns are dropped 

# Local data folder on device 
RAW_DATA_DIR = Path.home() / "Downloads" / "IDX_Local_Data" / "drive-download-20260623T184602Z-3-001"

# Output files will save in the same local folder 
LISTINGS_OUTPUT = RAW_DATA_DIR/ "listings.csv"
SOLD_OUTPUT = RAW_DATA_DIR/ "sold.csv"

START_MONTH = "202401"
END_MONTH = "202605"

def extract_month_from_filename(file_path):
    """
    Extract YYYYMM from file names such as: 
    CRMLSListing202401.csv
    CRMLSSold202401_filled.csv
    """
    digits = "".join(char for char in file_path.stem if char.isdigit())
    return digits[-6:]

def get_expected_months():
    """
    Creates a list of expected months from START_MONTH through END_MONTH.
    """
    return pd.period_range(START_MONTH, END_MONTH, freq="M").strftime("%Y%m").tolist()

def choose_monthly_files(file_pattern):
    """
    Selects monthly files within the required date range. If both regular and _filled versions exist for the same month, this function uses regular file. 
    If only the _filled version exists, then that file will be used and extra columns will be dropped
    """
    all_files = list(RAW_DATA_DIR.glob(file_pattern))
    files_by_month = {}

    for file in all_files:
        month = extract_month_from_filename(file)

        if START_MONTH <= month <= END_MONTH:
            if month not in files_by_month:
                files_by_month[month] = file

            else:
                current_file = files_by_month[month]

                # Prefer regular file over _filled file
                if "_filled" in current_file.stem and "_filled" not in file.stem:
                    files_by_month[month] = file

    selected_files = [files_by_month[month] for month in sorted(files_by_month)]
    return selected_files 

def load_csv_file(file):
    """
    Loads one CSV file. If the file name contains _filled, drop the last two columns.
    """

    df = pd.read_csv(file, low_memory=False)

    if "_filled" in file.stem:
        print(f"Dropping last two extra columns from {file.name}")
        df = df.iloc[:, :-2]

    return df 

def combine_and_filter(file_pattern, dataset_name, output_path):
    """
    Combine monthly files into one dataset, filters to Residential, and saves the output CSV.
    """
    print("\n" + "=" * 60)
    print(f"PROCESSING {dataset_name.upper()}DATA")
    print("=" * 60)

    selected_files = choose_monthly_files(file_pattern)

    print(f"\n{dataset_name} files selected:")
    for file in selected_files:
        print(f"- {file.name}")

    found_months = [extract_month_from_filename(file) for file in selected_files]
    expected_months = get_expected_months()
    missing_months = [month for month in expected_months if month not in found_months]

    print("\nMonth check:")
    print(f"Expected range: {START_MONTH} through {END_MONTH}")
    print(f"Found months: {found_months}")

    if missing_months: 
        print(f"Missing months: {missing_months}")
        print("Proceeding with available files only.")
    else:
        print("No missing months.")

    if not selected_files:
        raise FileNotFoundError(f"No files found for pattern: {file_pattern}")
    
    dataframes = []
    total_rows_before_concat = 0 

    print("\nRow counts by file:")

    for file in selected_files:
        df = load_csv_file(file)
        row_count = len(df)
        total_rows_before_concat += row_count 

        print(f"{file.name}: {row_count:,} rows")
        dataframes.append(df)

    combined = pd.concat(dataframes, ignore_index=True)

    print("\nConcatenation check:")
    print(f"Total rows before concatenation: {total_rows_before_concat:,}")
    print(f"Rows after concatenation: {len(combined):,}")

    if "PropertyType" not in combined.columns: 
        raise KeyError(f"PropertyType column not found in {dataset_name} data.")
    
    rows_before_filter =len(combined)

    residential = combined[combined["PropertyType"] == "Residential"].copy()

    rows_after_filter = len(residential)

    print("\nResidential filter check:")
    print(f"Rows before Residential filter: {rows_before_filter:,}")
    print(f"Rows after Residential filter: {rows_after_filter:,}")
    print(f"Rows removed by filter: {rows_before_filter - rows_after_filter:,}")

    residential.to_csv(output_path, index=False)

    print("\nOutput saved:")
    print(output_path)

    return residential

def main():
    listings = combine_and_filter(
        file_pattern="CRMLSListing*.csv",
        dataset_name="Listings",
        output_path=LISTINGS_OUTPUT
    )

    sold = combine_and_filter(
        file_pattern="CRMLSSold*.csv",
        dataset_name="Sold",
        output_path=SOLD_OUTPUT
    )

    print("\n" + "=" * 60)
    print("Week 1 Aggregation Complete")
    print("=" * 60)
    print(f"Final listings rows: {len(listings):,}")
    print(f"Final sold rows: {len(sold):,}")
    print(f"Listings saved to: {LISTINGS_OUTPUT}")
    print(f"Sold saved to: {SOLD_OUTPUT}")

if __name__ == "__main__":
    main()


