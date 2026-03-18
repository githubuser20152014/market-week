"""Fetch global equity, FX, and commodity data for the Global Investor Edition."""

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


def _yfinance_ohlcv(symbol, start, friday, decimals=2):
    """Pull a single ticker from yfinance and return list of daily OHLCV dicts."""
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    hist = ticker.history(
        start=start.strftime("%Y-%m-%d"),
        end=(friday + timedelta(days=1)).strftime("%Y-%m-%d"),
    )
    rows = []
    for idx, row in hist.iterrows():
        if idx.weekday() >= 5:
            continue
        rows.append({
            "date":   idx.strftime("%Y-%m-%d"),
            "open":   round(row["Open"],   decimals),
            "high":   round(row["High"],   decimals),
            "low":    round(row["Low"],    decimals),
            "close":  round(row["Close"],  decimals),
            "volume": int(row["Volume"]),
        })
    return rows[-5:]


def _friday_window(end_date):
    """Return (start, friday) for a ~10-day lookback capped at most-recent Friday."""
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days_since_friday = (end.weekday() - 4) % 7
    friday = end - timedelta(days=days_since_friday) if days_since_friday else end
    start = friday - timedelta(days=10)
    return start, friday


# ── Equity + Fixed Income + FX-hedge indicators ───────────────────────────────

def fetch_global_equity_data(end_date, use_mock=True):
    """Fetch US indices + intl indices + VIX.

    Returns:
        Dict keyed by index name with 'symbol', optional 'region'/'etf_proxy', and 'data' list.
    Fixture name: global_equity_YYYY-MM-DD.json
    """
    if not use_mock:
        try:
            return _fetch_live_global_equity(end_date)
        except Exception as e:
            print(f"Live global equity fetch failed ({e}), falling back to fixtures.")

    fixture_path = _find_closest_fixture("global_equity", end_date)
    if fixture_path is None:
        raise FileNotFoundError(f"No global equity fixture found near {end_date}")
    days_off = abs((datetime.strptime(end_date, "%Y-%m-%d") -
                    datetime.strptime(fixture_path.stem.replace("global_equity_", ""),
                                      "%Y-%m-%d")).days)
    if days_off > 2:
        print(f"WARNING: No global equity fixture for {end_date}. "
              f"Using {fixture_path.name} ({days_off} days off). "
              "Consider running with --live.")
    with open(fixture_path) as f:
        return json.load(f)


def _fetch_live_global_equity(end_date):
    """Pull US indices (indices.json) + intl indices (intl_indices.json) + VIX."""
    start, friday = _friday_window(end_date)

    with open(CONFIG_DIR / "indices.json") as f:
        us_indices = json.load(f)
    with open(CONFIG_DIR / "intl_indices.json") as f:
        intl_indices = json.load(f)

    result = {}

    # US indices
    for name, info in us_indices.items():
        rows = _yfinance_ohlcv(info["symbol"], start, friday)
        result[name] = {
            "symbol":    info["symbol"],
            "region":    "US",
            "etf_proxy": info.get("etf_proxy", ""),
            "data":      rows,
        }

    # International indices
    for name, info in intl_indices.items():
        rows = _yfinance_ohlcv(info["symbol"], start, friday)
        result[name] = {
            "symbol":    info["symbol"],
            "region":    info.get("region", ""),
            "etf_proxy": info.get("etf_proxy", ""),
            "data":      rows,
        }

    # VIX
    rows = _yfinance_ohlcv("^VIX", start, friday)
    result["VIX"] = {"symbol": "^VIX", "region": "US", "etf_proxy": "VIXY", "data": rows}

    return result


# ── FX ────────────────────────────────────────────────────────────────────────

def fetch_global_fx_data(end_date, use_mock=True):
    """Fetch FX pair data (same 5 pairs as intl edition).

    Fixture name: global_fx_YYYY-MM-DD.json
    """
    if not use_mock:
        try:
            return _fetch_live_global_fx(end_date)
        except Exception as e:
            print(f"Live global FX fetch failed ({e}), falling back to fixtures.")

    fixture_path = _find_closest_fixture("global_fx", end_date)
    if fixture_path is None:
        raise FileNotFoundError(f"No global FX fixture found near {end_date}")
    days_off = abs((datetime.strptime(end_date, "%Y-%m-%d") -
                    datetime.strptime(fixture_path.stem.replace("global_fx_", ""),
                                      "%Y-%m-%d")).days)
    if days_off > 2:
        print(f"WARNING: No global FX fixture for {end_date}. "
              f"Using {fixture_path.name} ({days_off} days off). "
              "Consider running with --live.")
    with open(fixture_path) as f:
        return json.load(f)


def _fetch_live_global_fx(end_date):
    """Pull FX pair data from yfinance."""
    start, friday = _friday_window(end_date)

    with open(CONFIG_DIR / "intl_fx.json") as f:
        fx_pairs = json.load(f)

    result = {}
    for name, info in fx_pairs.items():
        rows = _yfinance_ohlcv(info["symbol"], start, friday, decimals=6)
        result[name] = {
            "symbol":    info["symbol"],
            "etf_proxy": info.get("etf_proxy", ""),
            "data":      rows,
        }
    return result


# ── Commodities ───────────────────────────────────────────────────────────────

def fetch_global_commodity_data(end_date, use_mock=True):
    """Fetch commodity futures + US 30Y bond yield.

    Reads config/commodities.json.
    Fixture name: global_commodity_YYYY-MM-DD.json
    """
    if not use_mock:
        try:
            return _fetch_live_global_commodities(end_date)
        except Exception as e:
            print(f"Live global commodity fetch failed ({e}), falling back to fixtures.")

    fixture_path = _find_closest_fixture("global_commodity", end_date)
    if fixture_path is None:
        raise FileNotFoundError(f"No global commodity fixture found near {end_date}")
    days_off = abs((datetime.strptime(end_date, "%Y-%m-%d") -
                    datetime.strptime(fixture_path.stem.replace("global_commodity_", ""),
                                      "%Y-%m-%d")).days)
    if days_off > 2:
        print(f"WARNING: No global commodity fixture for {end_date}. "
              f"Using {fixture_path.name} ({days_off} days off). "
              "Consider running with --live.")
    with open(fixture_path) as f:
        return json.load(f)


def _fetch_live_global_commodities(end_date):
    """Pull commodity futures from yfinance."""
    start, friday = _friday_window(end_date)

    with open(CONFIG_DIR / "commodities.json") as f:
        commodities = json.load(f)

    result = {}
    for name, info in commodities.items():
        rows = _yfinance_ohlcv(info["symbol"], start, friday)
        result[name] = {
            "symbol":    info["symbol"],
            "etf_proxy": info.get("etf_proxy", ""),
            "data":      rows,
        }
    return result
