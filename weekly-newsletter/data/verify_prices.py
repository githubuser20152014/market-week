"""Cross-validate prices from two independent sources before newsletter generation."""

import csv
import io
import urllib.request
from datetime import datetime, timedelta

FRED_MAP = {
    "Gold": "GOLDAMGBD228NLBM",
    "10Y Treasury": "DGS10",
}

STOOQ_MAP = {
    "S&P 500": "^spx",
    "Dow Jones": "^dji",
    "Nasdaq": "^ndq",
    "Russell 2000": "^rut",
    "USD Index": "usd",
}


class PriceDiscrepancyError(Exception):
    """Raised when a price differs by more than the allowed tolerance between sources."""


def fetch_fred_price(series_id: str, date_str: str) -> float | None:
    """Download FRED CSV for a given series, return value on or before date_str."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  FRED fetch failed for {series_id}: {e}")
        return None

    target = datetime.strptime(date_str, "%Y-%m-%d")
    best_date = None
    best_value = None

    reader = csv.reader(io.StringIO(content))
    next(reader, None)  # skip header
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
                best_date = d
                best_value = v

    if best_date is not None and (target - best_date).days > 7:
        print(f"  WARNING: FRED {series_id} latest date {best_date.date()} is "
              f"{(target - best_date).days} days before {date_str}.")
    return best_value


def fetch_stooq_prices(symbol_map: dict, date_str: str) -> dict:
    """Fetch closing prices from Stooq via pandas_datareader for a given date."""
    try:
        import pandas_datareader.data as web
        import pandas as pd
    except ImportError:
        print("  pandas_datareader not installed; skipping Stooq verification.")
        return {}

    target = datetime.strptime(date_str, "%Y-%m-%d")
    start = target - timedelta(days=7)
    result = {}

    for name, symbol in symbol_map.items():
        try:
            df = web.DataReader(symbol, "stooq",
                                start=start.strftime("%Y-%m-%d"),
                                end=target.strftime("%Y-%m-%d"))
            if df.empty:
                print(f"  Stooq: no data for {symbol} ({name})")
                continue
            # Stooq returns newest-first; find the closest date <= target
            df = df.sort_index()
            df = df[df.index <= pd.Timestamp(date_str)]
            if df.empty:
                continue
            latest = df.iloc[-1]
            result[name] = round(float(latest["Close"]), 2)
        except Exception as e:
            print(f"  Stooq fetch failed for {symbol} ({name}): {e}")

    return result


def _get_yf_close(primary_data: dict, name: str) -> float | None:
    """Extract the most recent close from raw yfinance fixture data."""
    asset = primary_data.get(name)
    if not asset or not asset.get("data"):
        return None
    rows = asset["data"]
    return rows[-1]["close"] if rows else None


def verify_prices(primary_data: dict, date_str: str, tolerance_pct: float = 2.0) -> None:
    """Compare yfinance close prices against FRED/Stooq.

    Prints a side-by-side table: Asset | yfinance | Secondary | Diff%
    Raises PriceDiscrepancyError if any asset exceeds tolerance_pct.
    """
    print(f"\nPrice Verification — week ending {date_str}")
    print(f"{'Asset':<18} {'yfinance':>12} {'FRED/Stooq':>12} {'Diff%':>8}   Status")
    print("-" * 60)

    # Fetch FRED data
    fred_results = {}
    for name, series_id in FRED_MAP.items():
        val = fetch_fred_price(series_id, date_str)
        if val is not None:
            fred_results[name] = val

    # Fetch Stooq data
    stooq_results = fetch_stooq_prices(STOOQ_MAP, date_str)

    secondary = {**fred_results, **stooq_results}

    errors = []
    all_assets = list(FRED_MAP.keys()) + list(STOOQ_MAP.keys())

    for name in all_assets:
        yf_val = _get_yf_close(primary_data, name)
        sec_val = secondary.get(name)

        if yf_val is None:
            print(f"  {name:<16} {'N/A':>12} {'N/A':>12} {'N/A':>8}   - (not in primary data)")
            continue

        if sec_val is None:
            print(f"  {name:<16} {yf_val:>12,.2f} {'N/A':>12} {'N/A':>8}   ? (secondary unavailable)")
            continue

        diff_pct = abs(yf_val - sec_val) / sec_val * 100 if sec_val else 0.0
        status = "OK" if diff_pct <= tolerance_pct else "MISMATCH"
        flag = "  OK" if diff_pct <= tolerance_pct else "  FAIL"

        print(f"  {name:<16} {yf_val:>12,.2f} {sec_val:>12,.2f} {diff_pct:>7.1f}%  {flag}")

        if diff_pct > tolerance_pct:
            errors.append(
                f"  {name}: yfinance={yf_val:,.2f}, secondary={sec_val:,.2f}, diff={diff_pct:.1f}%"
            )

    print()

    if errors:
        msg = (
            f"Price discrepancy exceeds {tolerance_pct}% tolerance:\n"
            + "\n".join(errors)
            + "\nInvestigate the discrepancy and re-run."
        )
        raise PriceDiscrepancyError(msg)

    print(f"All prices verified within {tolerance_pct}% tolerance.\n")
