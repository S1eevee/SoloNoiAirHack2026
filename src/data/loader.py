import pandas as pd
from pathlib import Path


def _read_csv_robust(source) -> pd.DataFrame:
    """Try common separators and encodings until the expected columns appear."""
    REQUIRED = {"flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"}

    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        for sep in (",", ";", "\t", "|"):
            try:
                if isinstance(source, (str, Path)):
                    df = pd.read_csv(source, sep=sep, encoding=enc)
                else:
                    source.seek(0)
                    df = pd.read_csv(source, sep=sep, encoding=enc)
                df.columns = df.columns.str.strip()
                if REQUIRED.issubset(set(df.columns)):
                    return df
            except Exception:
                continue

    # last resort: let pandas sniff the separator
    if isinstance(source, (str, Path)):
        df = pd.read_csv(source, sep=None, engine="python", encoding="utf-8-sig")
    else:
        source.seek(0)
        df = pd.read_csv(source, sep=None, engine="python", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df


def load_flights(path: str | Path) -> pd.DataFrame:
    return _read_csv_robust(path)


def load_flights_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    import io
    return _read_csv_robust(io.BytesIO(content))
