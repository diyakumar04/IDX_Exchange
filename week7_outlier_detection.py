"""
Week 7 - Outlier Detection and Data Quality
"""

import pandas as pd 

INPUT_PATH = '/Users/diyakumar/Downloads/IDX_Local_Data/drive-download-20260623T184602Z-3-001/sold_with_metrics.csv'  # Week 6 output
FULL_FLAGGED_OUTPUT = 'sold_with_outlier_flags.csv'
CLEAN_FILTERED_OUTPUT = 'sold_clean_filtered.csv'

OUTLIER_FIELDS = ['ClosePrice', 'LivingArea', 'DaysOnMarket']

def iqr_bounds(series):
    """Return (lower, upper) IQR bounds for a numeric series."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return lower, upper

def main():
    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded {INPUT_PATH}: {len(df)} rows\n")

    df['invalid_flag'] = (
        (df['ClosePrice'] <= 0)
        | (df['LivingArea'] <= 0)
        | (df['DaysOnMarket'] < 0)
    )
    print(f"Business-rule invalid rows: {df['invalid_flag'].sum()}")

    flag_cols = []
    print("\nIQR outlier bounds:")
    for field in OUTLIER_FIELDS:
        lower, upper = iqr_bounds(df[field])
        flag_col = f'{field}_outlier_flag'
        df[flag_col] = (df[field] < lower) | (df[field] > upper)
        flag_cols.append(flag_col)
        print(
            f"  {field}: [{lower:,.2f}, {upper:,.2f}] "
            f"-> {df[flag_col].sum()} flagged ({df[flag_col].sum()/len(df)*100:.2f}%)"
        )

    df['any_outlier_flag'] = df[flag_cols].any(axis=1)

    df.to_csv(FULL_FLAGGED_OUTPUT, index=False)
    print(f"\nSaved full flagged dataset to {FULL_FLAGGED_OUTPUT} ({len(df)} rows)")

    df_clean = df[~df['invalid_flag'] & ~df['any_outlier_flag']].copy()
    df_clean.to_csv(CLEAN_FILTERED_OUTPUT, index=False)
    print(f"Saved clean filtered dataset to {CLEAN_FILTERED_OUTPUT} ({len(df_clean)} rows)")

    removed = len(df) - len(df_clean)
    print("\n" + "=" * 60)
    print("BEFORE vs AFTER COMPARISON")
    print("=" * 60)
    print(f"Row count: {len(df):,} -> {len(df_clean):,}  "
          f"({removed:,} removed, {removed/len(df)*100:.2f}%)")

    for field in OUTLIER_FIELDS:
        before_median = df[field].median()
        after_median = df_clean[field].median()
        pct_change = (after_median - before_median) / before_median * 100 if before_median else float('nan')
        print(
            f"{field} median: {before_median:,.2f} -> {after_median:,.2f} "
            f"({pct_change:+.2f}%)"
        )

    print("=" * 60)
    print("Week 7 Outlier Detection Complete")
    print("=" * 60)

if __name__ == '__main__':
    main()
