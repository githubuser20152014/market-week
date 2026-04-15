"""Base fetchers and shared asset mappings for market data."""

import csv
import io
import urllib.request
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Asset maps
# ---------------------------------------------------------------------------

FRED_MAP = {
    "Gold":         "GOLDPMGBD228NLBM",
    "10Y Treasury": "DGS10",
}

STOOQ_MAP = {
    "S&P 500":    "^spx",
    "Dow Jones":  "^dji",
    "Nasdaq":     "^ndq",
    "Russell 2000": "^rut",
    "USD Index":  "usd",
}

STOOQ_INTL_MAP = {
    "Nikkei 225":    "^nk225",
    "DAX":           "^dax",
    "FTSE 100":      "^ftse",
    "CAC 40":        "^cac",
    "Euro Stoxx 50": "^stoxx50e",
    "Hang Seng":     "^hsi",
}

STOOQ_FX_MAP = {
    "EUR/USD": "eurusd",
    "GBP/USD": "gbpusd",
    "USD/JPY": "usdjpy",
    "AUD/USD": "audusd",
}

# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def fetch_fred_price(series_id: str, date_str: str,
                     offset_days: int = 0) -> float | None:
    """Return FRED close on or before (date_str + offset_days)."""
    effective = (datetime.strptime(date_str, "%Y-%m-%d")
                 + timedelta(days=offset_days)).strftime("%Y-%m-%d")
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  FRED fetch failed for {series_id}: {e}")
        return None

    target = datetime.strptime(effective, "%Y-%m-%d")
    best_date = best_value = None

    reader = csv.reader(io.StringIO(content))
    next(reader, None)
    for row in reader:
        if len(row) < 2 or row[1].strip() == ".":
            continue
        try:
            d = datetime.strptime(row[0].strip(), "%Y-%m-%d")
            v = float(row[1].strip())
        except ValueError:
            continue
        if d <= target:
            if best_date is None or d > best_date:
                best_date, best_value = d, v

    # Fallback: if best_date is more than 5 days before target, treat as unavailable
    if best_date and (target - best_date).days > 5:
        return None

    return best_value


def fetch_stooq_prices(symbol_map: dict, date_str: str,
                       offset_days: int = 0) -> dict:
    """Fetch closing prices from Stooq for all symbols in symbol_map."""
    try:
        import pandas_datareader.data as web
        import pandas as pd
    except ImportError:
        return {}

    effective = (datetime.strptime(date_str, "%Y-%m-%d")
                 + timedelta(days=offset_days)).strftime("%Y-%m-%d")
    start = (datetime.strptime(effective, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    result = {}

    for name, symbol in symbol_map.items():
        try:
            df = web.DataReader(symbol, "stooq", start=start, end=effective)
            if df.empty:
                continue
            df = df.sort_index()
            df = df[df.index <= pd.Timestamp(effective)]
            if df.empty:
                continue
            result[name] = round(float(df.iloc[-1]["Close"]), 2)
        except Exception:
            pass

    return result
