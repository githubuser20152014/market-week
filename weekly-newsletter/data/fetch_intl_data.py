"""Fetch international index, FX, and economic calendar data from fixtures or live APIs."""

import json
from datetime import datetime, timedelta
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _find_closest_fixture(prefix, target_date):
    """Find the fixture file closest to target_date."""
    target = datetime.strptime(target_date, "%Y-%m-%d")
    candidates = []
    for f in FIXTURES_DIR.glob(f"{prefix}_*.json"):
        date_str = f.stem.replace(f"{prefix}_", "")
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            candidates.append((abs((d - target).days), f))
        except ValueError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def fetch_intl_index_data(end_date, use_mock=True):
    """Fetch international index OHLCV data.

    Args:
        end_date: Date string YYYY-MM-DD (last trading day of the week).
        use_mock: If True, load from fixtures. If False, try yfinance.

    Returns:
        Dict keyed by index name, each with 'symbol', 'region', 'etf_proxy', and 'data' list.
    """
    if not use_mock:
        try:
            return _fetch_live_intl_indices(end_date)
        except Exception as e:
            print(f"Live fetch failed ({e}), falling back to fixtures.")

    fixture_path = _find_closest_fixture("intl_indices", end_date)
    if fixture_path is None:
        raise FileNotFoundError(f"No international index fixture found near {end_date}")
    with open(fixture_path) as f:
        return json.load(f)


def fetch_intl_fx_data(end_date, use_mock=True):
    """Fetch FX pair OHLCV data for EUR/USD, GBP/USD, JPY/USD, AUD/USD.

    Args:
        end_date: Date string YYYY-MM-DD.
        use_mock: If True, load from fixtures. If False, try yfinance.

    Returns:
        Dict keyed by pair name, each with 'symbol', 'etf_proxy', and 'data' list.
    """
    if not use_mock:
        try:
            return _fetch_live_fx(end_date)
        except Exception as e:
            print(f"Live FX fetch failed ({e}), falling back to fixtures.")

    fixture_path = _find_closest_fixture("intl_fx", end_date)
    if fixture_path is None:
        raise FileNotFoundError(f"No FX fixture found near {end_date}")
    with open(fixture_path) as f:
        return json.load(f)


def fetch_intl_econ_calendar(end_date, use_mock=True):
    """Fetch international economic calendar events.

    Returns:
        Dict with 'past_week' and 'upcoming_week' lists.
    """
    fixture_path = _find_closest_fixture("intl_econ_calendar", end_date)
    if fixture_path is None:
        raise FileNotFoundError(f"No international econ calendar fixture found near {end_date}")
    with open(fixture_path) as f:
        return json.load(f)


def _fetch_live_intl_indices(end_date):
    """Pull international index data from yfinance."""
    import yfinance as yf

    with open(CONFIG_DIR / "intl_indices.json") as f:
        indices = json.load(f)

    end = datetime.strptime(end_date, "%Y-%m-%d")
    days_since_friday = (end.weekday() - 4) % 7
    friday = end - timedelta(days=days_since_friday) if days_since_friday else end
    start = friday - timedelta(days=10)

    result = {}
    for name, info in indices.items():
        ticker = yf.Ticker(info["symbol"])
        hist = ticker.history(start=start.strftime("%Y-%m-%d"),
                              end=(friday + timedelta(days=1)).strftime("%Y-%m-%d"))
        rows = []
        for idx, row in hist.iterrows():
            if idx.weekday() >= 5:
                continue
            rows.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })
        rows = rows[-5:]
        result[name] = {
            "symbol": info["symbol"],
            "region": info.get("region", ""),
            "etf_proxy": info.get("etf_proxy", ""),
            "data": rows,
        }
    return result


def _fetch_live_fx(end_date):
    """Pull FX pair data from yfinance."""
    import yfinance as yf

    with open(CONFIG_DIR / "intl_fx.json") as f:
        fx_pairs = json.load(f)

    end = datetime.strptime(end_date, "%Y-%m-%d")
    days_since_friday = (end.weekday() - 4) % 7
    friday = end - timedelta(days=days_since_friday) if days_since_friday else end
    start = friday - timedelta(days=10)

    result = {}
    for name, info in fx_pairs.items():
        ticker = yf.Ticker(info["symbol"])
        hist = ticker.history(start=start.strftime("%Y-%m-%d"),
                              end=(friday + timedelta(days=1)).strftime("%Y-%m-%d"))
        rows = []
        for idx, row in hist.iterrows():
            if idx.weekday() >= 5:
                continue
            rows.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 6),
                "high": round(row["High"], 6),
                "low": round(row["Low"], 6),
                "close": round(row["Close"], 6),
                "volume": 0,
            })
        rows = rows[-5:]
        result[name] = {
            "symbol": info["symbol"],
            "etf_proxy": info.get("etf_proxy", ""),
            "data": rows,
        }
    return result
