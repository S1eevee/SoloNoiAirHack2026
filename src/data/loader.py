import pandas as pd
from pathlib import Path


def load_flights(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def load_flights_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    import io
    df = pd.read_csv(io.BytesIO(content))
    df.columns = df.columns.str.strip()
    return df
