import pandas as pd
from darts import TimeSeries, concatenate
from darts.dataprocessing.transformers import MissingValuesFiller
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')


def load_indicator(filepath, value_col, rename, freq='MS', resample_method=None):
    """
    Load a single indicator CSV and convert to Darts TimeSeries
    
    Args:
        filepath: Path to CSV file
        value_col: Column name to use as values
        freq: Frequency (MS = month start)
        resample_method: If not None, resample to this frequency
    """
    print(f"Loading {filepath.name}...")
    
    df = pd.read_csv(filepath, parse_dates=['date'])
    df = df.set_index('date')
    
    # Extract the column
    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found in {filepath.name}")
    
    df = df[[value_col]].rename(columns={value_col: rename})

    # Create TimeSeries
    ts = TimeSeries.from_dataframe(
        df, 
        freq=freq,
        fill_missing_dates=True,
    )
    
    # Resample if needed (quarterly GDP to monthly)
    if resample_method:
        ts = ts.resample(resample_method)
    
    return ts


def load_all_indicators(indicators_dir):
    """
    Load all macro indicators from separate CSV files
    
    Returns:
        dict: {indicator_name: TimeSeries}
    """
    indicators = {}
    
    # CCI - we'll extract target separately
    cci_ts = load_indicator(
        indicators_dir / 'cci.csv',
        value_col='cci_overall',
        rename="cci",
        freq='MS'
    )
    
    # CPI
    indicators['cpi'] = load_indicator(
        indicators_dir / 'cpi.csv',
        value_col='value',
        rename="cpi",
        freq='MS'
    )
    
    # Unemployment Rate
    indicators['unemployment'] = load_indicator(
        indicators_dir / 'unemployment_rate.csv',
        value_col='value',
        rename="umemp",
        freq='MS'
    )
    
    # Policy Rate
    indicators['policy_rate'] = load_indicator(
        indicators_dir / 'policy_rate.csv',
        value_col='value',
        rename="policy_rate",
        freq='MS'
    )
    
    # # Import Price Index
    # indicators['impi'] = load_indicator(
    #     indicators_dir / 'impi.csv',
    #     value_col='value',
    #     rename="impi",
    #     freq='MS'
    # )
    
    # # Export Price Index  
    # indicators['expi'] = load_indicator(
    #     indicators_dir / 'expi.csv',
    #     value_col='value',
    #     rename="expi",
    #     freq='MS'
    # )
    
    # GDP - quarterly, need to resample to monthly
    try:
        gdp_ts = load_indicator(
            indicators_dir / 'gdp.csv',
            value_col='value',
            rename="gdp",
            freq='QS'
        )
        # Forward-fill to monthly (same as your current approach)
        indicators['gdp'] = gdp_ts.resample('MS', method='pad')
        print("  Resampled GDP from quarterly to monthly (forward-fill)")
    except Exception as e:
        print(f"  Could not load GDP: {e}")
        # Try monthly GDP file instead
        try:
            indicators['gdp'] = load_indicator(
                indicators_dir / 'gdp_monthly.csv',
                value_col='gdp',
                rename="gdp",
                freq='MS'
            )
        except:
            print("  GDP not available, continuing without it")
    
    # Optional indicators (skip if not present)
    optional_indicators = {
        'exchange_rate': 'exchange_rate.csv',
        'export_vol': 'export_vol.csv',
        'set': 'set.csv',
        'total_avg_wage': 'total_avg_wage.csv',
        'tourist_arrivals': 'tourist_arrivals.csv',
    }
    
    for name, filename in optional_indicators.items():
        filepath = indicators_dir / filename
        if filepath.exists():
            try:
                indicators[name] = load_indicator(
                    filepath,
                    value_col=name,  # assume column name matches file name
                    freq='MS'
                )
            except Exception as e:
                print(f"  Could not load {filename}: {e}")
    
    return cci_ts, indicators


def load_sentiment_features(absa_features_path):
    """
    Load ABSA sentiment features as multivariate TimeSeries
    All 16 columns (8 aspects × 2 sentiments) become components
    """
    print(f"Loading {absa_features_path.name}...")
    
    df = pd.read_csv(absa_features_path, parse_dates=['date'])
    df = df.set_index('date')
    
    # All sentiment columns
    sentiment_cols = [
        'การเมือง_neg_count',
        'ภัยพิบัติ/โรคระบาด_neg_count',
        'มาตรการของรัฐ_neg_count',
        'ราคาน้ำมันเชื้อเพลิง_neg_count',
        'ราคาสินค้าเกษตร_neg_count',
        'สังคม/ความมั่นคง_neg_count',
        'เศรษฐกิจโลก_neg_count',
        'เศรษฐกิจไทย_neg_count',
        'การเมือง_pos_count',
        'ภัยพิบัติ/โรคระบาด_pos_count',
        'มาตรการของรัฐ_pos_count',
        'ราคาน้ำมันเชื้อเพลิง_pos_count',
        'ราคาสินค้าเกษตร_pos_count',
        'สังคม/ความมั่นคง_pos_count',
        'เศรษฐกิจโลก_pos_count',
        'เศรษฐกิจไทย_pos_count',
    ]
    
    # Create multivariate TimeSeries
    sentiment_ts = TimeSeries.from_dataframe(
        df[sentiment_cols],
        freq='MS',
        fill_missing_dates=True,
        fillna_value=0  # assume 0 articles if missing month
    )
    
    print(f"  Loaded {len(sentiment_cols)} sentiment features")
    
    return sentiment_ts


def align_and_merge(cci_ts, indicators, sentiment_ts):
    """
    Align all series to common time range and stack into covariates
    
    Returns:
        cci_aligned: Target TimeSeries
        covariates_aligned: Multivariate covariates TimeSeries
    """
    print("\n=== Aligning Time Series ===")
    
    # Stack all indicators into single multivariate series
    indicator_list = list(indicators.values())
    all_series = [cci_ts] + indicator_list + [sentiment_ts]
    
    # Find common time range
    start_time = max([ts.start_time() for ts in all_series])
    end_time = min([ts.end_time() for ts in all_series])
    
    print(f"Common time range: {start_time} to {end_time}")
    print(f"Total months: {len(pd.date_range(start_time, end_time, freq='MS'))}")
    
    # Slice to common range
    cci_aligned = cci_ts.slice(start_time, end_time)
    indicators_aligned = [ind.slice(start_time, end_time) for ind in indicator_list]
    sentiment_aligned = sentiment_ts.slice(start_time, end_time)
    
    # Stack all covariates (indicators + sentiment)
    all_covariates = indicators_aligned + [sentiment_aligned]
    covariates_aligned = concatenate(all_covariates, axis=1)  # axis=1 for components
    
    print(f"Target shape: {cci_aligned.values().shape}")
    print(f"Covariates shape: {covariates_aligned.values().shape}")
    print(f"  {covariates_aligned.n_components} total features")
    
    return cci_aligned, covariates_aligned


def handle_missing_values(cci_ts, covariates_ts):
    """
    Handle any remaining missing values
    Uses Darts' automatic filling (forward-fill then back-fill)
    """
    print("\n=== Handling Missing Values ===")
    
    filler = MissingValuesFiller(fill='auto')  # ffill then bfill
    
    # Check for missing values
    cci_missing = pd.isna(cci_ts.to_dataframe()).sum().sum()
    cov_missing = pd.isna(covariates_ts.to_dataframe()).sum().sum()
    cci_ts.to_dataframe
    print(f"Missing values - Target: {cci_missing}, Covariates: {cov_missing}")
    
    if cci_missing > 0:
        cci_ts = filler.transform(cci_ts)
        print("  Filled target missing values")
    
    if cov_missing > 0:
        covariates_ts = filler.transform(covariates_ts)
        print("  Filled covariates missing values")
    
    return cci_ts, covariates_ts


def save_dataset(cci_ts, covariates_ts, output_path, save_csv=True):
    """
    Save aligned dataset
    
    Args:
        save_csv: If True, also save as CSV for inspection
    """
    print(f"\n=== Saving Dataset ===")
    
    # Save as pickle (preserves Darts TimeSeries)
    with open(output_path, 'wb') as f:
        pickle.dump({
            'target': cci_ts,
            'covariates': covariates_ts,
            'target_name': 'cci_overall',
            'covariate_names': covariates_ts.components.tolist(),
        }, f)
    
    print(f"✓ Saved Darts dataset to: {output_path}")
    
    # Also save as CSV for inspection
    if save_csv:
        csv_path = output_path.with_suffix('.csv')
        
        # Combine target and covariates
        combined_df = pd.concat([
            cci_ts.to_dataframe(copy=True),
            covariates_ts.to_dataframe(copy=True)
        ], axis=1)
        
        combined_df.to_csv(csv_path)
        print(f"✓ Saved CSV for inspection: {csv_path}")
        
        # Print summary
        print(f"\nDataset Summary:")
        print(f"  Time range: {combined_df.index[0]} to {combined_df.index[-1]}")
        print(f"  Total months: {len(combined_df)}")
        print(f"  Target: cci_overall")
        print(f"  Covariates: {len(covariates_ts.components)} features")
        print(f"\nFirst 5 rows:")
        print(combined_df.head())
        print(f"\nLast 5 rows:")
        print(combined_df.tail())


def main():
    """Main pipeline"""
    
    # Paths
    indicators_dir = Path('data/indicators')
    absa_features_path = Path('data/4_absa_features/aspect_monthly_features.csv')
    output_path = Path('data/darts_dataset.pkl')
    
    print("="*60)
    print("Creating Darts Dataset from Individual Files")
    print("="*60)
    
    # 1. Load data
    print("\n### Step 1: Loading Data ###")
    cci_ts, indicators = load_all_indicators(indicators_dir)
    sentiment_ts = load_sentiment_features(absa_features_path)
    
    # 2. Align and merge
    print("\n### Step 2: Aligning Data ###")
    cci_aligned, covariates_aligned = align_and_merge(cci_ts, indicators, sentiment_ts)
    
    # 3. Handle missing values
    print("\n### Step 3: Handling Missing Values ###")
    cci_final, covariates_final = handle_missing_values(cci_aligned, covariates_aligned)
    
    # 4. Save
    print("\n### Step 4: Saving ###")
    save_dataset(cci_final, covariates_final, output_path)
    
    print("\n" + "="*60)
    print("✓ Dataset Creation Complete!")
    print("="*60)
    print(f"\nNext step: Run 2_train_models.py to train forecasting models")
    
    return cci_final, covariates_final


if __name__ == '__main__':
    cci_ts, covariates_ts = main()
