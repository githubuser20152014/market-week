"""Fetch global equity, FX, and commodity data for the Global Investor Edition."""

import json
from datetime import datetime, timedelta
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


# ── Perplexity price-key → fixture-name mappings ──────────────────────────────

# Each entry: perplexity_key -> (fixture_name, symbol, region, etf_proxy, is_yield)
# Pass weekly_pct as "{key}_weekly_pct".
# For yields (is_yield=True), pass week-start level as "{key}_week_start" instead.
_GLOBAL_EQUITY_KEY_MAP = {
    "sp500":          ("S&P 500",       "^GSPC",     "US",               "SPY",  False),
    "dow":            ("Dow Jones",     "^DJI",      "US",               "DIA",  False),
    "nasdaq":         ("Nasdaq",        "^IXIC",     "US",               "QQQ",  False),
    "russell2000":    ("Russell 2000",  "^RUT",      "US",               "IWM",  False),
    "ten_year_yield": ("10Y Treasury",  "^TNX",      "US",               "TLT",  True),
    "usd_index":      ("USD Index",     "DX=F",      "US",               "UUP",  False),
    "vix":            ("VIX",           "^VIX",      "US",               "VIXY", False),
    # International
    "dax":            ("DAX",           "^GDAXI",    "Europe",           "EWG",  False),
    "ftse100":        ("FTSE 100",      "^FTSE",     "Europe",           "EWU",  False),
    "cac40":          ("CAC 40",        "^FCHI",     "Europe",           "EWQ",  False),
    "eurostoxx50":    ("Euro Stoxx 50", "^STOXX50E", "Europe",           "FEZ",  False),
    "nikkei":         ("Nikkei 225",    "^N225",     "Asia-Pacific",     "EWJ",  False),
    "hang_seng":      ("Hang Seng",     "^HSI",      "Asia-Pacific",     "EWH",  False),
    "asx200":         ("ASX 200",       "^AXJO",     "Asia-Pacific",     "EWA",  False),
    "msci_em":        ("MSCI EM",       "EEM",       "Emerging Markets", "EEM",  False),
}

# Each entry: perplexity_key -> (fixture_name, symbol, etf_proxy)
# Note: intl_fx.json uses JPY/USD (not USD/JPY) — ask Perplexity for JPY/USD directly.
_GLOBAL_FX_KEY_MAP = {
    "eurusd": ("EUR/USD", "EURUSD=X", "FXE"),
    "gbpusd": ("GBP/USD", "GBPUSD=X", "FXB"),
    "jpyusd": ("JPY/USD", "JPYUSD=X", "FXY"),
    "audusd": ("AUD/USD", "AUDUSD=X", "FXA"),
    "chfusd": ("CHF/USD", "CHFUSD=X", "FXF"),
}

# Each entry: perplexity_key -> (fixture_name, symbol, etf_proxy, is_yield)
_GLOBAL_COMMODITY_KEY_MAP = {
    "wti_crude":    ("WTI Crude Oil", "CL=F", "USO", False),
    "nat_gas":      ("Natural Gas",   "NG=F", "UNG", False),
    "gold":         ("Gold",          "GC=F", "GLD", False),
    "silver":       ("Silver",        "SI=F", "SLV", False),
    "us_30y_yield": ("US 30Y",        "^TYX", "TLT", True),
}


# ── Synthetic OHLCV helper ─────────────────────────────────────────────────────

def _synthetic_ohlcv(close, weekly_pct, week_start_str, week_end_str, decimals=2):
    """Build a 2-entry OHLCV list compatible with _weekly_pct() and _week_range().

    data[0]["open"]  = implied Monday open  (close / (1 + weekly_pct/100))
    data[-1]["close"] = Friday close

    If weekly_pct is None, open == close (0 % weekly change).
    """
    if close is None:
        return []
    if weekly_pct is not None:
        open_implied = round(close / (1 + weekly_pct / 100), decimals)
    else:
        open_implied = round(close, decimals)
    close_r = round(close, decimals)
    return [
        {"date": week_start_str, "open": open_implied, "high": open_implied,
         "low": open_implied, "close": open_implied, "volume": 0},
        {"date": week_end_str,   "open": close_r,      "high": close_r,
         "low": close_r,         "close": close_r,     "volume": 0},
    ]


def _week_bounds(date_str):
    """Return (monday_str, friday_str) for the week containing date_str."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    monday  = d - timedelta(days=d.weekday())
    friday  = monday + timedelta(days=4)
    return monday.strftime("%Y-%m-%d"), friday.strftime("%Y-%m-%d")


# ── Perplexity-sourced fixture builders ───────────────────────────────────────

def fetch_from_perplexity_global(date_str, perplexity_data):
    """Build all three global fixture payloads from Perplexity-sourced price data.

    perplexity_data must contain keys:
      "equity"     — dict with keys matching _GLOBAL_EQUITY_KEY_MAP.
                     For each asset: "{key}" = Friday close,
                                     "{key}_weekly_pct" = weekly % change.
                     For yield assets (ten_year_yield): use "{key}_week_start"
                     instead of "{key}_weekly_pct".
      "fx"         — dict with keys matching _GLOBAL_FX_KEY_MAP.
                     Same "{key}" + "{key}_weekly_pct" pattern.
      "commodities"— dict with keys matching _GLOBAL_COMMODITY_KEY_MAP.
                     For us_30y_yield use "{key}_week_start".

    Returns:
        (equity_fixture, fx_fixture, commodity_fixture) — three dicts ready to save.
    """
    monday_str, friday_str = _week_bounds(date_str)

    equity_data     = perplexity_data.get("equity",      {})
    fx_data         = perplexity_data.get("fx",          {})
    commodity_data  = perplexity_data.get("commodities", {})

    equity_fixture    = _build_global_equity(equity_data,    monday_str, friday_str)
    fx_fixture        = _build_global_fx(fx_data,            monday_str, friday_str)
    commodity_fixture = _build_global_commodity(commodity_data, monday_str, friday_str)

    return equity_fixture, fx_fixture, commodity_fixture


def _build_global_equity(equity, monday_str, friday_str):
    result = {}
    for pkey, (name, symbol, region, etf_proxy, is_yield) in _GLOBAL_EQUITY_KEY_MAP.items():
        close = equity.get(pkey)
        if close is None:
            continue

        if is_yield:
            # For yields, use explicit week_start instead of deriving from pct
            week_start = equity.get(pkey + "_week_start")
            if week_start is not None:
                weekly_pct = round((close - week_start) / week_start * 100, 4) \
                             if week_start else None
                # Build synthetic data with exact week_start as open
                data = [
                    {"date": monday_str, "open": round(week_start, 4),
                     "high": round(week_start, 4), "low": round(week_start, 4),
                     "close": round(week_start, 4), "volume": 0},
                    {"date": friday_str, "open": round(close, 4),
                     "high": round(close, 4), "low": round(close, 4),
                     "close": round(close, 4), "volume": 0},
                ]
            else:
                weekly_pct = equity.get(pkey + "_weekly_pct")
                data = _synthetic_ohlcv(close, weekly_pct, monday_str, friday_str, decimals=4)
        else:
            weekly_pct = equity.get(pkey + "_weekly_pct")
            data = _synthetic_ohlcv(close, weekly_pct, monday_str, friday_str)

        result[name] = {
            "symbol":    symbol,
            "region":    region,
            "etf_proxy": etf_proxy,
            "data":      data,
        }
    return result


def _build_global_fx(fx, monday_str, friday_str):
    result = {}
    for pkey, (name, symbol, etf_proxy) in _GLOBAL_FX_KEY_MAP.items():
        rate = fx.get(pkey)
        if rate is None:
            continue
        weekly_pct = fx.get(pkey + "_weekly_pct")
        data = _synthetic_ohlcv(rate, weekly_pct, monday_str, friday_str, decimals=6)
        result[name] = {
            "symbol":    symbol,
            "etf_proxy": etf_proxy,
            "data":      data,
        }
    return result


def _build_global_commodity(commodities, monday_str, friday_str):
    result = {}
    for pkey, (name, symbol, etf_proxy, is_yield) in _GLOBAL_COMMODITY_KEY_MAP.items():
        close = commodities.get(pkey)
        if close is None:
            continue

        if is_yield:
            week_start = commodities.get(pkey + "_week_start")
            if week_start is not None:
                data = [
                    {"date": monday_str, "open": round(week_start, 4),
                     "high": round(week_start, 4), "low": round(week_start, 4),
                     "close": round(week_start, 4), "volume": 0},
                    {"date": friday_str, "open": round(close, 4),
                     "high": round(close, 4), "low": round(close, 4),
                     "close": round(close, 4), "volume": 0},
                ]
            else:
                weekly_pct = commodities.get(pkey + "_weekly_pct")
                data = _synthetic_ohlcv(close, weekly_pct, monday_str, friday_str, decimals=4)
        else:
            weekly_pct = commodities.get(pkey + "_weekly_pct")
            data = _synthetic_ohlcv(close, weekly_pct, monday_str, friday_str)

        result[name] = {
            "symbol":    symbol,
            "etf_proxy": etf_proxy,
            "data":      data,
        }
    return result


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
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(
            start=start.strftime("%Y-%m-%d"),
            end=(friday + timedelta(days=1)).strftime("%Y-%m-%d"),
            auto_adjust=True
        )
        if hist.empty:
            return []
        
        # Clean up column names if MultiIndex
        if isinstance(hist.columns, __import__("pandas").MultiIndex):
            hist.columns = hist.columns.droplevel(1)
            
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
    except Exception as e:
        print(f"  yfinance fetch failed for {symbol} ({e})")
        return []


def _friday_window(end_date):
    """Return (start, friday) for a ~10-day lookback capped at most-recent Friday."""
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days_since_friday = (end.weekday() - 4) % 7
    friday = end - timedelta(days=days_since_friday) if days_since_friday else end
    start = friday - timedelta(days=10)
    return start, friday


# ── Equity + Fixed Income + FX-hedge indicators ───────────────────────────────

def _fetch_secondary_verification_global(date_str):
    """Fetch verification prices from FRED and Stooq for global assets."""
    try:
        from .base_fetchers import (
            FRED_MAP, STOOQ_MAP, STOOQ_INTL_MAP, STOOQ_FX_MAP,
            fetch_fred_price, fetch_stooq_prices
        )
    except ImportError:
        from base_fetchers import (
            FRED_MAP, STOOQ_MAP, STOOQ_INTL_MAP, STOOQ_FX_MAP,
            fetch_fred_price, fetch_stooq_prices
        )
    
    # 1. FRED: Gold, 10Y
    fred_results = {}
    for name, series_id in FRED_MAP.items():
        val = fetch_fred_price(series_id, date_str)
        if val is not None:
            fred_results[name] = val

    # 2. Stooq: S&P, Dow, Nasdaq, Russell, USD Index, Intl, FX
    stooq_results = fetch_stooq_prices(STOOQ_MAP, date_str)
    stooq_intl    = fetch_stooq_prices(STOOQ_INTL_MAP, date_str)
    stooq_fx      = fetch_stooq_prices(STOOQ_FX_MAP, date_str)

    return {
        "fred":  fred_results,
        "stooq": {**stooq_results, **stooq_intl, **stooq_fx}
    }


def _fetch_live_futures_global(date_str):
    """Fetch pre-market or current futures for context in global summary."""
    import yfinance as yf
    
    symbols = {
        "S&P Futures":     "ES=F",
        "Nasdaq Futures":  "NQ=F",
        "Dow Futures":     "YM=F",
        "Gold Futures":    "GC=F",
        "WTI Crude Oil":   "CL=F",
    }
    
    target = datetime.strptime(date_str, "%Y-%m-%d")
    is_today = target.date() == datetime.now().date()
    
    result = {}
    for name, symbol in symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            live_price = None
            if is_today:
                fi = ticker.fast_info
                lp = fi.get("last_price")
                if lp and lp > 0:
                    live_price = float(lp)
                
            # History for settlement
            start = (target - timedelta(days=7)).strftime("%Y-%m-%d")
            end   = (target + timedelta(days=1)).strftime("%Y-%m-%d")
            df = yf.download(symbol, start=start, end=end, progress=False)
            
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            df = df[df.index.dayofweek < 5]
            df_filtered = df[df.index <= target]

            if not df_filtered.empty:
                settlement = float(df_filtered["Close"].iloc[-1])
                prev_settle = float(df_filtered["Close"].iloc[-2]) if len(df_filtered) >= 2 else None
                price = live_price if live_price else settlement
                daily_pct = ((price / settlement) - 1) * 100 if is_today and live_price else \
                            (((price / prev_settle) - 1) * 100 if prev_settle else None)
                
                result[name] = {
                    "price": round(price, 2),
                    "daily_pct": round(daily_pct, 4) if daily_pct is not None else None
                }
        except Exception:
            pass
    return result


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
