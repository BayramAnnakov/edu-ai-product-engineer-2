import pandas as pd
from typing import Optional, Tuple


def load_reviews(file_path: str) -> Optional[pd.DataFrame]:
    """
    Reads a CSV or TSV file into a pandas DataFrame, automatically detecting the separator.
    """
    try:
        # Use engine='python' and sep=None to let pandas auto-detect the separator.
        # This is more robust than guessing.
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-16')
        print("Successfully loaded reviews.")
        return df
    except Exception as e:
        print(f"Error loading file with auto-detection: {e}")
        return None


def filter_version(df: pd.DataFrame, version: str) -> pd.DataFrame:
    """Filters DataFrame for a specific version and Russian language reviews."""
    if 'App Version Name' not in df.columns or 'Reviewer Language' not in df.columns:
        raise ValueError("Required columns 'App Version Name' or 'Reviewer Language' not in file.")
    
    version_df = df[
        (df['App Version Name'] == version) & 
        (df['Reviewer Language'] == 'ru')
    ].copy()
    
    return version_df


def calc_share(df_all: pd.DataFrame, df_ver: pd.DataFrame) -> float:
    """Calculates the share of version-specific reviews."""
    if len(df_all) == 0:
        return 0.0
    return len(df_ver) / len(df_all)
