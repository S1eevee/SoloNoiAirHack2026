import pandas as pd
from pathlib import Path


def load_flights(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=None, engine="python", encoding_errors="replace")
    df.columns = df.columns.str.strip().str.lower()
    return df


def load_flights_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    import io
    df = pd.read_csv(io.BytesIO(content), sep=None, engine="python", encoding_errors="replace")
    df.columns = df.columns.str.strip().str.lower()
    return df
