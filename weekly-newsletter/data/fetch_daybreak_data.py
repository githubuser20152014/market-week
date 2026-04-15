"""Fetch data for the Market Day Break daily edition.

Fixture schema  fixtures/daybreak_YYYY-MM-DD.json:
{
  "meta":           { "date", "generated_at", "generation_source" },
  "us_close":       { name: { symbol, prev_close, close, daily_pct,
                               is_yield, yield_change_bps } },
  "intl_overnight": { name: { symbol, region, status, close, daily_pct,
                               session_note } },
  "fx":             { name: { symbol, rate, prev_close, daily_pct } },
  "futures":        { name: { symbol, price, prev_close, daily_pct } },
  "econ_calendar":  { "yesterday": [...], "today": [...] },
  "market_news":    [ { headline, source, published, url, summary } ]
}
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
CONFIG_DIR   = Path(__file__).resolve().parent.parent / "config"

# Load API keys from config/api_keys.env if present
_env_file = CONFIG_DIR / "api_keys.env"
if _env_file.exists():
    load_dotenv(_env_file)

# Stale-data threshold: 1 day (tighter than weekly's 2 days)
_STALE_DAYS = 1


def _find_closest_fixture(target_date: str):
    """Return (days_off, path) for the nearest daybreak fixture, or (None, None)."""
    target = datetime.strptime(target_date, "%Y-%m-%d")
    candidates = []
    for f in FIXTURES_DIR.glob("daybreak_*.json"):
        date_str = f.stem.replace("daybreak_", "")
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            candidates.append((abs((d - target).days), f))
        except ValueError:
            continue
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0])
    return candidates[0]


# ── Public entry point ────────────────────────────────────────────────────────

def fetch_daybreak_data(date_str: str, use_mock: bool = True) -> dict:
    """Fetch all daybreak data for *date_str* (the date of the morning brief).

    When use_mock=False, pulls live data from yfinance + Finnhub.
    Falls back to fixture if live fetch fails.

    Args:
        date_str: The brief date in YYYY-MM-DD format (usually today).
        use_mock: If True, load from the nearest fixture.

    Returns:
        Full daybreak payload dict.
    """
    if not use_mock:
        try:
            return _fetch_live(date_str)
        except Exception as e:
            print(f"Live daybreak fetch failed ({e}), falling back to fixture.")

    days_off, fixture_path = _find_closest_fixture(date_str)
    if fixture_path is None:
        raise FileNotFoundError(f"No daybreak fixture found near {date_str}. "
                                "Run with --live to generate one.")
    if days_off > _STALE_DAYS:
        print(f"WARNING: No daybreak fixture for {date_str}. "
              f"Using {fixture_path.name} ({days_off} days off). "
              "Data is stale — run with --live.")
    with open(fixture_path) as f:
        return json.load(f)


# ── Perplexity price-key → fixture-name mappings ──────────────────────────────

# Each entry: perplexity_key -> (fixture_name, yfinance_symbol, is_yield)
_US_KEY_MAP = {
    "sp500":          ("S&P 500",       "^GSPC",     False),
    "dow":            ("Dow Jones",     "^DJI",      False),
    "nasdaq":         ("Nasdaq",        "^IXIC",     False),
    "russell2000":    ("Russell 2000",  "^RUT",      False),
    "gold_spot":      ("Gold",          "GC=F",      False),
    "ten_year_yield": ("10Y Treasury",  "^TNX",      True),
    "usd_index":      ("USD Index",     "DX-Y.NYB",  False),
    "wti_crude":      ("WTI Crude Oil", "CL=F",      False),
}

# Each entry: perplexity_key -> (fixture_name, yfinance_symbol)
_FUTURES_KEY_MAP = {
    "sp_futures":     ("S&P Futures",    "ES=F"),
    "nasdaq_futures": ("Nasdaq Futures", "NQ=F"),
    "dow_futures":    ("Dow Futures",    "YM=F"),
    "gold_futures":   ("Gold Futures",   "GC=F"),
    "wti_futures":    ("WTI Crude Oil",  "CL=F"),
}

# Each entry: perplexity_key -> (fixture_name, yfinance_symbol, region)
_INTL_KEY_MAP = {
    "nikkei":      ("Nikkei 225",    "^N225",     "Asia-Pacific"),
    "hang_seng":   ("Hang Seng",     "^HSI",      "Asia-Pacific"),
    "kospi":       ("KOSPI",         "^KS11",     "Asia-Pacific"),
    "nifty50":     ("Nifty 50",      "^NSEI",     "Asia-Pacific"),
    "asx200":      ("ASX 200",       "^AXJO",     "Asia-Pacific"),
    "dax":         ("DAX",           "^GDAXI",    "Europe"),
    "ftse100":     ("FTSE 100",      "^FTSE",     "Europe"),
    "cac40":       ("CAC 40",        "^FCHI",     "Europe"),
    "eurostoxx50": ("Euro Stoxx 50", "^STOXX50E", "Europe"),
}

# Each entry: perplexity_key -> (fixture_name, yfinance_symbol)
_FX_KEY_MAP = {
    "eurusd": ("EUR/USD", "EURUSD=X"),
    "gbpusd": ("GBP/USD", "GBPUSD=X"),
    "usdjpy": ("USD/JPY", "JPY=X"),
    "audusd": ("AUD/USD", "AUDUSD=X"),
    "usdcnh": ("USD/CNH", "USDCNH=X"),
    "chfusd": ("CHF/USD", "CHFUSD=X"),
}


# ── Perplexity-sourced fixture builder ────────────────────────────────────────

def fetch_from_perplexity(date_str: str, perplexity_data: dict) -> dict:
    """Build a full daybreak fixture from Perplexity-sourced price data.

    perplexity_data must contain keys:
      "us"   — dict with keys matching _US_KEY_MAP + _FUTURES_KEY_MAP
      "intl" — dict with keys matching _INTL_KEY_MAP
                (pass null for holiday/unavailable markets; optionally pass
                 "{key}_note" for a human-readable status, e.g. "nikkei_note")
      "fx"   — dict with keys matching _FX_KEY_MAP

    prev_close values are loaded from yesterday's fixture automatically.
    econ_calendar and market_news are fetched via existing live functions.

    Returns a complete fixture payload ready to save.
    """
    target    = datetime.strptime(date_str, "%Y-%m-%d")
    yesterday = (target - timedelta(days=1)).strftime("%Y-%m-%d")

    # Load yesterday's fixture for prev_close lookups
    prev_fixture = None
    _, prev_path = _find_closest_fixture(yesterday)
    if prev_path:
        with open(prev_path) as f:
            prev_fixture = json.load(f)
        print(f"  prev_close source: {prev_path.name}")
    else:
        print("  No yesterday fixture found — daily_pct will be omitted.")

    us_data   = perplexity_data.get("us",   {})
    intl_data = perplexity_data.get("intl", {})
    fx_data   = perplexity_data.get("fx",   {})

    return {
        "meta": {
            "date":              date_str,
            "generated_at":      datetime.utcnow().isoformat() + "Z",
            "generation_source": "perplexity",
        },
        "us_close":       _build_us_close(us_data,   prev_fixture),
        "intl_overnight": _build_intl(intl_data,     prev_fixture),
        "fx":             _build_fx(fx_data,          prev_fixture),
        "futures":        _build_futures(us_data,     prev_fixture),
        "econ_calendar":  {"yesterday": [], "today": []},
        "market_news":    _fetch_market_news(date_str),
    }


def _build_us_close(us: dict, prev_fixture) -> dict:
    result = {}
    for pkey, (name, symbol, is_yield) in _US_KEY_MAP.items():
        close      = us.get(pkey)
        prev_close = (prev_fixture or {}).get("us_close", {}).get(name, {}).get("close")

        entry = {
            "symbol":     symbol,
            "prev_close": round(prev_close, 4) if prev_close is not None else None,
            "close":      round(close, 4)      if close      is not None else None,
            "daily_pct":  round((close / prev_close - 1) * 100, 4)
                          if close and prev_close else None,
            "table":      True,
        }
        if is_yield:
            entry["is_yield"]         = True
            entry["yield_change_bps"] = round((close - prev_close) * 100, 2) \
                                        if close is not None and prev_close is not None else None
        result[name] = entry
    return result


def _build_intl(intl: dict, prev_fixture) -> dict:
    result = {}
    for pkey, (name, symbol, region) in _INTL_KEY_MAP.items():
        close      = intl.get(pkey)
        prev_close = (prev_fixture or {}).get("intl_overnight", {}).get(name, {}).get("close")
        note       = intl.get(pkey + "_note", "")

        if close is None:
            status = "holiday" if "holiday" in note.lower() else "no_data"
            result[name] = {
                "symbol":       symbol,
                "region":       region,
                "status":       status,
                "close":        None,
                "prev_close":   round(prev_close, 2) if prev_close is not None else None,
                "daily_pct":    None,
                "session_note": note or "No data / holiday",
            }
        else:
            daily_pct  = round((close / prev_close - 1) * 100, 4) if prev_close else None
            status     = "partial" if region == "Europe" else "closed"
            session_note = note or ("Early session" if region == "Europe" else "Previous close")
            result[name] = {
                "symbol":       symbol,
                "region":       region,
                "status":       status,
                "close":        round(close, 2),
                "prev_close":   round(prev_close, 2) if prev_close is not None else None,
                "daily_pct":    daily_pct,
                "session_note": session_note,
            }
    return result


def _build_fx(fx: dict, prev_fixture) -> dict:
    result = {}
    for pkey, (name, symbol) in _FX_KEY_MAP.items():
        rate       = fx.get(pkey)
        prev_close = (prev_fixture or {}).get("fx", {}).get(name, {}).get("rate")

        result[name] = {
            "symbol":     symbol,
            "rate":       round(rate, 5)       if rate       is not None else None,
            "prev_close": round(prev_close, 5) if prev_close is not None else None,
            "daily_pct":  round((rate / prev_close - 1) * 100, 4)
                          if rate and prev_close else None,
        }
    return result


def _build_futures(us: dict, prev_fixture) -> dict:
    result = {}
    for pkey, (name, symbol) in _FUTURES_KEY_MAP.items():
        price      = us.get(pkey)
        prev_close = (prev_fixture or {}).get("futures", {}).get(name, {}).get("price")

        result[name] = {
            "symbol":     symbol,
            "price":      round(price, 2)      if price      is not None else None,
            "prev_close": round(prev_close, 2) if prev_close is not None else None,
            "daily_pct":  round((price / prev_close - 1) * 100, 4)
                          if price and prev_close else None,
        }
    return result


# ── Live fetchers ─────────────────────────────────────────────────────────────

def _fetch_live(date_str: str, include_secondaries: bool = False) -> dict:
    """Assemble the full daybreak payload from live sources.
    
    If include_secondaries=True, also fetches FRED/Stooq prices for verification
    and embeds them in the result dict under a 'verification' key.
    """
    with open(CONFIG_DIR / "daybreak_symbols.json") as f:
        cfg = json.load(f)

    us_close       = _fetch_us_close(date_str, cfg["us_indices"])
    intl_overnight = _fetch_intl_overnight(date_str, cfg["intl_indices"])
    fx             = _fetch_fx(date_str, cfg["fx"])
    futures        = _fetch_futures(date_str, cfg["futures"])
    market_news    = _fetch_market_news(date_str)
    econ_calendar  = _fetch_econ_calendar(date_str)

    payload = {
        "meta": {
            "date": date_str,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generation_source": "live",
        },
        "us_close":       us_close,
        "intl_overnight": intl_overnight,
        "fx":             fx,
        "futures":        futures,
        "econ_calendar":  econ_calendar,
        "market_news":    market_news,
    }

    if include_secondaries:
        payload["verification"] = _fetch_secondary_verification(date_str)

    return payload


def _fetch_secondary_verification(date_str: str) -> dict:
    """Fetch verification prices from FRED and Stooq."""
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
    
    fred_results  = {}
    for name, series_id in FRED_MAP.items():
        val = fetch_fred_price(series_id, date_str)
        if val is not None:
            fred_results[name] = val

    stooq_results = fetch_stooq_prices(STOOQ_MAP, date_str)
    stooq_intl    = fetch_stooq_prices(STOOQ_INTL_MAP, date_str)
    stooq_fx      = fetch_stooq_prices(STOOQ_FX_MAP, date_str)

    return {
        "fred":  fred_results,
        "stooq": {**stooq_results, **stooq_intl, **stooq_fx}
    }


def _fetch_us_close(date_str: str, index_cfg: dict) -> dict:
    """Fetch previous US session closes (yesterday's 4 PM data)."""
    import yfinance as yf

    target = datetime.strptime(date_str, "%Y-%m-%d")
    # Download buffer to ensure we catch the last two sessions
    start = (target - timedelta(days=7)).strftime("%Y-%m-%d")
    end   = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    result = {}
    for name, info in index_cfg.items():
        symbol   = info["symbol"]
        is_yield = info.get("is_yield", False)
        try:
            df = yf.download(symbol, start=start, end=end,
                             progress=False, auto_adjust=True)
            if df.empty:
                result[name] = _empty_us_entry(symbol, is_yield)
                continue
                
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            # Ensure we only have weekday data
            df = df[df.index.dayofweek < 5]
            
            if len(df) < 1:
                result[name] = _empty_us_entry(symbol, is_yield)
                continue

            # Close is the last available day <= date_str
            # prev_close is the day before that
            # We filter for index <= target to be safe if running on weekends/future dates
            df_filtered = df[df.index <= target]
            if len(df_filtered) < 1:
                 result[name] = _empty_us_entry(symbol, is_yield)
                 continue

            close = float(df_filtered["Close"].iloc[-1])
            prev_close = float(df_filtered["Close"].iloc[-2]) if len(df_filtered) >= 2 else None
            
            daily_pct = ((close / prev_close) - 1) * 100 if prev_close else None

            entry = {
                "symbol":    symbol,
                "prev_close": round(prev_close, 4) if prev_close else None,
                "close":      round(close, 4),
                "daily_pct":  round(daily_pct, 4) if daily_pct is not None else None,
                "table":      info.get("table", True),
            }
            if is_yield:
                entry["is_yield"]          = True
                entry["yield_change_bps"]  = round((close - prev_close) * 100, 2) if prev_close else None
            result[name] = entry
        except Exception as e:
            print(f"  US close fetch failed for {name} ({e})")
            result[name] = _empty_us_entry(symbol, is_yield)

    return result


def _fetch_intl_overnight(date_str: str, index_cfg: dict) -> dict:
    """Fetch overnight international index data.

    - APAC: Asia-Pacific markets closed; use last close.
    - Europe: Early session; use intraday price (1m) if current date matches date_str.
    """
    import yfinance as yf

    target = datetime.strptime(date_str, "%Y-%m-%d")
    is_today = target.date() == datetime.now().date()
    
    start = (target - timedelta(days=7)).strftime("%Y-%m-%d")
    end   = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    result = {}
    for name, info in index_cfg.items():
        symbol = info["symbol"]
        region = info.get("region", "")
        try:
            # Daily data for base reference
            df_daily = yf.download(symbol, start=start, end=end,
                                   progress=False, auto_adjust=True)
            if df_daily.empty:
                result[name] = _empty_intl_entry(symbol, region)
                continue

            if isinstance(df_daily.columns, __import__("pandas").MultiIndex):
                df_daily.columns = df_daily.columns.droplevel(1)
            
            df_daily = df_daily[df_daily.index.dayofweek < 5]
            df_filtered = df_daily[df_daily.index <= target]

            if len(df_filtered) < 1:
                result[name] = _empty_intl_entry(symbol, region)
                continue

            last_close = float(df_filtered["Close"].iloc[-1])
            prev_close = float(df_filtered["Close"].iloc[-2]) if len(df_filtered) >= 2 else None

            if region == "Europe" and is_today:
                # Try to get live 1m price for active session
                try:
                    df_1m = yf.download(symbol, period="1d", interval="1m",
                                        progress=False, auto_adjust=True)
                    if not df_1m.empty:
                        if isinstance(df_1m.columns, __import__("pandas").MultiIndex):
                            df_1m.columns = df_1m.columns.droplevel(1)
                        live_price = float(df_1m["Close"].iloc[-1])
                        # For Europe, daily_pct is usually vs YESTERDAY'S close
                        daily_pct = ((live_price / last_close) - 1) * 100
                        result[name] = {
                            "symbol":       symbol,
                            "region":       region,
                            "status":       "partial",
                            "close":        round(live_price, 2),
                            "prev_close":   round(last_close, 2),
                            "daily_pct":    round(daily_pct, 4),
                            "session_note": "Intraday (early session)",
                        }
                        continue
                except Exception:
                    pass

            # Fallback for APAC or Europe (if weekend/non-today/failure)
            daily_pct = ((last_close / prev_close) - 1) * 100 if prev_close else None
            result[name] = {
                "symbol":       symbol,
                "region":       region,
                "status":       "closed",
                "close":        round(last_close, 2),
                "prev_close":   round(prev_close, 2) if prev_close else None,
                "daily_pct":    round(daily_pct, 4) if daily_pct is not None else None,
                "session_note": "Previous close",
            }
        except Exception as e:
            print(f"  Intl overnight fetch failed for {name} ({e})")
            result[name] = _empty_intl_entry(symbol, region)

    return result


def _fetch_fx(date_str: str, fx_cfg: dict) -> dict:
    """Fetch FX rates with robust fallback."""
    import yfinance as yf

    target = datetime.strptime(date_str, "%Y-%m-%d")
    start  = (target - timedelta(days=7)).strftime("%Y-%m-%d")
    end    = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    result = {}
    for name, info in fx_cfg.items():
        symbol = info["symbol"]
        try:
            df = yf.download(symbol, start=start, end=end,
                             progress=False, auto_adjust=True)
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            df = df[df.index.dayofweek < 5]
            df_filtered = df[df.index <= target]

            if len(df_filtered) >= 2:
                rate = float(df_filtered["Close"].iloc[-1])
                prev = float(df_filtered["Close"].iloc[-2])
                result[name] = {
                    "symbol":     symbol,
                    "rate":       round(rate, 5),
                    "prev_close": round(prev, 5),
                    "daily_pct":  round(((rate / prev) - 1) * 100, 4),
                }
            elif not df_filtered.empty:
                 rate = float(df_filtered["Close"].iloc[-1])
                 result[name] = {"symbol": symbol, "rate": round(rate, 5), "prev_close": None, "daily_pct": None}
            else:
                 # Last resort: 1d period
                 ticker = yf.Ticker(symbol)
                 rate = ticker.fast_info.get("last_price")
                 result[name] = {"symbol": symbol, "rate": round(rate, 5) if rate else None, "prev_close": None, "daily_pct": None}
        except Exception as e:
            print(f"  FX fetch failed for {name} ({e})")
            result[name] = {"symbol": symbol, "rate": None, "prev_close": None, "daily_pct": None}
    return result


def _fetch_futures(date_str: str, futures_cfg: dict) -> dict:
    """Fetch pre-market futures with high resolution."""
    import yfinance as yf

    target = datetime.strptime(date_str, "%Y-%m-%d")
    is_today = target.date() == datetime.now().date()

    result = {}
    for name, info in futures_cfg.items():
        symbol = info["symbol"]
        try:
            ticker = yf.Ticker(symbol)
            live_price = None
            
            if is_today:
                # 1. Try fast_info
                try:
                    fi = ticker.fast_info
                    lp = fi.get("last_price")
                    if lp and lp > 0:
                        live_price = float(lp)
                except Exception:
                    pass
                
                # 2. Try 1m download if fast_info fails or to confirm
                if not live_price:
                    try:
                        df_1m = yf.download(symbol, period="1d", interval="1m", progress=False)
                        if not df_1m.empty:
                            live_price = float(df_1m["Close"].iloc[-1])
                    except Exception:
                        pass

            # Get daily history for settlement/prev_close
            start = (target - timedelta(days=7)).strftime("%Y-%m-%d")
            end   = (target + timedelta(days=1)).strftime("%Y-%m-%d")
            df = yf.download(symbol, start=start, end=end, progress=False)
            
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            df = df[df.index.dayofweek < 5]
            df_filtered = df[df.index <= target]

            if df_filtered.empty:
                result[name] = {"symbol": symbol, "price": live_price, "prev_close": None, "daily_pct": None}
                continue

            settlement = float(df_filtered["Close"].iloc[-1])
            prev_settle = float(df_filtered["Close"].iloc[-2]) if len(df_filtered) >= 2 else None

            price = live_price if live_price else settlement
            # daily_pct for futures in morning brief is vs prior settlement
            daily_pct = ((price / settlement) - 1) * 100 if is_today and live_price else \
                        (((price / prev_settle) - 1) * 100 if prev_settle else None)

            result[name] = {
                "symbol":     symbol,
                "price":      round(price, 2),
                "prev_close": round(settlement, 2),
                "daily_pct":  round(daily_pct, 4) if daily_pct is not None else None,
            }
        except Exception as e:
            print(f"  Futures fetch failed for {name} ({e})")
            result[name] = {"symbol": symbol, "price": None, "prev_close": None, "daily_pct": None}
    return result



def _fetch_econ_calendar(date_str: str) -> dict:
    """Fetch economic calendar events for yesterday + today.

    Primary source: FRED releases/dates API (free).
    Fallback: Finnhub /calendar/economic (paid — 403 on free tier).
    Returns empty calendar if both fail.
    """
    target    = datetime.strptime(date_str, "%Y-%m-%d")
    yesterday = (target - timedelta(days=1)).strftime("%Y-%m-%d")
    result    = {"yesterday": [], "today": []}

    fred_key = os.environ.get("FRED_API_KEY", "")
    if fred_key:
        try:
            return _fetch_econ_calendar_fred(yesterday, date_str, fred_key)
        except Exception as e:
            print(f"  FRED econ calendar fetch failed ({e})")
            # Fall through to Finnhub only if FRED errored out

    finnhub_key = os.environ.get("FINNHUB_API_KEY", "")
    if not fred_key and finnhub_key:
        try:
            return _fetch_econ_calendar_finnhub(yesterday, date_str, finnhub_key)
        except Exception as e:
            print(f"  Finnhub econ calendar fetch failed ({e})")

    if not fred_key and not finnhub_key:
        print("  No FRED_API_KEY or FINNHUB_API_KEY — skipping live econ calendar.")

    return result


# FRED series to fetch actual values for releases that landed yesterday.
# Schema: release_id -> (series_id, transform, unit, label_suffix)
#   transform: "mom_pct"        = (curr - prev) / prev * 100  (1 decimal)
#              "mom_and_yoy_pct" = MoM + YoY combined string (14 obs needed)
#              "yoy_pct"        = (curr - year_ago) / year_ago * 100
#              "level"          = raw latest observation value
#              "mom_diff"       = curr - prev  (e.g. thousands of jobs)
# Optional 5th element: separate series_id to use for the YoY leg of mom_and_yoy_pct.
# BLS reports YoY CPI using the NOT seasonally adjusted series (CPIAUCNS),
# while MoM uses the seasonally adjusted series (CPIAUCSL).
_FRED_SERIES = {
    10:  ("CPIAUCSL",  "mom_and_yoy_pct", "%", "", "CPIAUCNS"),  # CPI: SA for MoM, NSA for YoY
    31:  ("PPIACO",    "mom_pct",  "%",  "MoM"),          # PPI
    54:  ("PCE",       "mom_pct",  "%",  "MoM"),          # PCE
    50:  ("PAYEMS",    "mom_diff", "K",  "MoM chg"),      # NFP (thousands)
    44:  ("RSAFS",     "mom_pct",  "%",  "MoM"),          # Retail Sales
    53:  ("A191RL1Q225SBEA", "level", "%", "QoQ SAAR"),   # GDP real growth rate
    17:  ("INDPRO",    "mom_pct",  "%",  "MoM"),          # Industrial Production
    82:  ("BOPGSTB",   "level",    "B",  ""),             # Trade Balance ($B)
    175: ("UMCSENT",   "level",    "",   ""),             # UMich Sentiment
    19:  ("HOUST",     "level",    "K",  "SAAR"),         # Housing Starts
}


def _fetch_fred_observation(series_id: str, api_key: str, n: int = 13,
                            units: str = "lin") -> list:
    """Fetch the last n observations for a FRED series. Returns list of (date, value) tuples.

    units: "lin" = raw level, "pch" = MoM % change, "pc1" = YoY % change from a year ago.
    """
    import requests
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id":   series_id,
        "api_key":     api_key,
        "file_type":   "json",
        "sort_order":  "desc",
        "limit":       n,
        "units":       units,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    result = []
    for o in obs:
        try:
            result.append((o["date"], float(o["value"])))
        except (ValueError, KeyError):
            pass
    return result  # descending order: [0] = latest


def _compute_actual(series_id: str, transform: str, unit: str, label_suffix: str,
                    api_key: str, yoy_series_id: str = "") -> tuple:
    """Returns (actual_str, previous_str, unit_str) by fetching FRED observations."""
    try:
        obs = _fetch_fred_observation(series_id, api_key)
        if not obs:
            return "--", "--", unit
        latest_val = obs[0][1]

        if transform == "level":
            actual = f"{latest_val:,.1f}"
            prev   = f"{obs[1][1]:,.1f}" if len(obs) > 1 else "--"
            return actual, prev, unit  # unit appended by template

        if transform == "mom_and_yoy_pct":
            # Ask FRED to compute MoM and YoY directly — avoids manual index math
            # and lag issues. SA series for MoM (pch), NSA series for YoY (pc1).
            mom_str = "--"
            yoy_str = "--"
            mom_obs = _fetch_fred_observation(series_id, api_key, n=2, units="pch")
            if mom_obs:
                mom_str = f"{mom_obs[0][1]:+.1f}%"
            yoy_series = yoy_series_id or series_id
            yoy_obs = _fetch_fred_observation(yoy_series, api_key, n=2, units="pc1")
            if yoy_obs:
                yoy_str = f"{yoy_obs[0][1]:+.1f}%"
            actual = f"{mom_str} MoM / {yoy_str} YoY" if yoy_str != "--" else mom_str
            return actual, "--", ""

        if transform == "mom_pct" and len(obs) >= 2:
            prev_val = obs[1][1]
            pct      = (latest_val - prev_val) / abs(prev_val) * 100
            return f"{pct:+.1f}%", "--", ""

        if transform == "yoy_pct" and len(obs) >= 5:
            year_ago = obs[4][1]
            pct      = (latest_val - year_ago) / abs(year_ago) * 100
            return f"{pct:+.1f}%", "--", ""

        if transform == "mom_diff" and len(obs) >= 2:
            diff = latest_val - obs[1][1]
            prev = obs[1][1]
            # Embed unit in value strings; pass empty unit to template
            return f"{diff:+,.0f}{unit}", f"{prev:,.0f}{unit}", ""

    except Exception:
        pass
    return "--", "--", unit


# FRED release IDs for key macro events (free tier, no auth tier restriction)
# Schema: release_id -> (description, importance, label)
_FRED_RELEASES = {
    10:  ("Consumer Price Index",         3, "CPI"),
    53:  ("Gross Domestic Product",        3, "GDP"),
    54:  ("Personal Income and Outlays",   3, "PCE / Personal Income"),
    50:  ("Employment Situation",          3, "Nonfarm Payrolls / Unemployment"),
    44:  ("Advance Monthly Sales",         2, "Retail Sales"),
    31:  ("Producer Price Index",          2, "PPI"),
    21:  ("Existing Home Sales",           1, "Existing Home Sales"),
    22:  ("New Residential Sales",         1, "New Home Sales"),
    17:  ("Industrial Production",         2, "Industrial Production"),
    46:  ("Durable Goods",                 2, "Durable Goods Orders"),
    82:  ("Trade Balance",                 2, "Trade Balance"),
    175: ("University of Michigan",        2, "UMich Consumer Sentiment"),
    19:  ("Housing Starts",               1, "Housing Starts"),
    23:  ("Manufacturers' New Orders",     1, "Factory Orders"),
}

# Typical ET release times for each FRED release ID.
# Source: BLS/BEA/Census release schedules (these times rarely change).
_FRED_RELEASE_TIMES = {
    10:  "8:30 AM ET",   # CPI
    53:  "8:30 AM ET",   # GDP
    54:  "8:30 AM ET",   # PCE / Personal Income
    50:  "8:30 AM ET",   # Nonfarm Payrolls / Unemployment
    44:  "8:30 AM ET",   # Retail Sales
    31:  "8:30 AM ET",   # PPI
    21:  "10:00 AM ET",  # Existing Home Sales
    22:  "10:00 AM ET",  # New Home Sales
    17:  "9:15 AM ET",   # Industrial Production
    46:  "8:30 AM ET",   # Durable Goods Orders
    82:  "8:30 AM ET",   # Trade Balance
    175: "10:00 AM ET",  # UMich Consumer Sentiment
    19:  "8:30 AM ET",   # Housing Starts
    23:  "10:00 AM ET",  # Factory Orders
}


def _fetch_econ_calendar_fred(yesterday: str, today: str, api_key: str) -> dict:
    """Fetch upcoming FRED release dates and map to human-readable event names."""
    import requests

    result = {"yesterday": [], "today": []}

    url = "https://api.stlouisfed.org/fred/releases/dates"
    params = {
        "realtime_start":                   yesterday,
        "realtime_end":                     today,
        "include_release_dates_with_no_data": "true",
        "sort_order":                       "asc",
        "api_key":                          api_key,
        "file_type":                        "json",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    release_dates = resp.json().get("release_dates", [])

    for rd in release_dates:
        release_id   = rd.get("release_id")
        release_date = rd.get("date", "")

        # Only include releases explicitly in our allowlist — no keyword fallback
        if release_id not in _FRED_RELEASES:
            continue
        _, importance, label = _FRED_RELEASES[release_id]

        actual   = "--"
        previous = "--"
        unit     = ""
        expected = "See tradingeconomics.com"

        # For releases that landed yesterday, fetch the actual reported value from FRED
        if release_date == yesterday and release_id in _FRED_SERIES:
            fred_entry   = _FRED_SERIES[release_id]
            series_id, transform, unit, label_suffix = fred_entry[:4]
            yoy_series   = fred_entry[4] if len(fred_entry) > 4 else ""
            try:
                actual, previous, unit = _compute_actual(
                    series_id, transform, unit, label_suffix, api_key,
                    yoy_series_id=yoy_series
                )
                print(f"    {label}: actual={actual}, previous={previous}")
            except Exception as e:
                print(f"    {label} observation fetch failed ({e})")

        entry = {
            "event":      label,
            "actual":     actual,
            "expected":   expected,
            "previous":   previous,
            "unit":       unit,
            "importance": importance,
            "time_est":   _FRED_RELEASE_TIMES.get(release_id, ""),
            "source":     "FRED",
        }
        if release_date == yesterday:
            result["yesterday"].append(entry)
        elif release_date == today:
            result["today"].append(entry)

    return result


def _fetch_econ_calendar_finnhub(yesterday: str, today: str, api_key: str) -> dict:
    """Fetch economic calendar from Finnhub (premium endpoint)."""
    import requests

    _KEYWORDS = {"cpi", "gdp", "fomc", "fed", "ecb", "pce", "jobs",
                 "nonfarm", "unemployment", "retail", "payroll", "inflation"}

    result = {"yesterday": [], "today": []}
    url    = "https://finnhub.io/api/v1/calendar/economic"
    params = {"from": yesterday, "to": today, "token": api_key}
    resp   = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    events = resp.json().get("economicCalendar", [])

    for ev in events:
        importance = ev.get("importance", 0)
        event_name = ev.get("event", "")
        if importance < 2:
            continue
        name_lower = event_name.lower()
        if not any(kw in name_lower for kw in _KEYWORDS):
            if importance < 3:
                continue

        entry = {
            "event":      event_name,
            "actual":     ev.get("actual", "--"),
            "expected":   ev.get("estimate", "--"),
            "previous":   ev.get("prev", "--"),
            "unit":       ev.get("unit", ""),
            "importance": importance,
            "time_est":   ev.get("time", ""),
            "source":     "Finnhub",
        }
        ev_date = ev.get("time", "")[:10] if ev.get("time") else ev.get("date", "")
        if ev_date == yesterday:
            result["yesterday"].append(entry)
        elif ev_date == today:
            result["today"].append(entry)

    return result


# ── Market News (RSS) ──────────────────────────────────────────────────────────

_RSS_FEEDS = [
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("AP News", "https://rsshub.app/apnews/topics/apf-topnews"),
    ("CNBC",    "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
]

_MARKET_KEYWORDS = {
    "war", "iran", "sanction", "tariff", "trade war", "trade tension", "trade dispute",
    "trade deficit", "trade deal", "oil", "opec", "fed ", "federal reserve", "rate cut",
    "rate hike", "interest rate", "inflation", "recession", "gdp", "cpi", "pce",
    "payroll", "jobs report", "unemployment", "earnings", "revenue", "guidance",
    "crisis", "ceasefire", "attack", "china", "taiwan", "russia", "ukraine", "nato",
    "g7", "g20", "budget", "debt ceiling", "default", "embargo", "nuclear", "missile",
    "troops", "geopolit", "conflict", "accord", "stock market", "equity", "bond yield",
    "treasury", "dollar", "currency", "etf", "s&p", "nasdaq", "dow jones",
}

# Headlines matching any of these are excluded even if they pass the keyword filter
_MARKET_EXCLUDE_KEYWORDS = {
    "skilled trade", "box office", "movie slate", "film slate", "broadcast license",
    " fcc ", "first amendment", "oscars", "grammy", "emmys", "nfl", "nba", "mlb",
    "recipe", "fashion", "beauty", "wellness", "dating", "parenting",
}


def _fetch_market_news(date_str: str, max_items: int = 8) -> list:
    """Fetch market-relevant headlines from RSS feeds, filtered by keyword."""
    try:
        import feedparser
    except ImportError:
        print("  feedparser not installed — skipping market news.")
        return []

    seen_titles = set()
    results = []

    for source_name, url in _RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title   = entry.get("title", "").strip()
                summary = entry.get("summary", "")
                link    = entry.get("link", "")
                published = entry.get("published", "")

                combined = (title + " " + summary).lower()
                if not any(kw in combined for kw in _MARKET_KEYWORDS):
                    continue
                if any(kw in combined for kw in _MARKET_EXCLUDE_KEYWORDS):
                    continue
                if title in seen_titles:
                    continue

                seen_titles.add(title)
                results.append({
                    "headline":  title,
                    "source":    source_name,
                    "published": published,
                    "url":       link,
                    "summary":   summary[:200] if summary else "",
                })
                if len(results) >= max_items:
                    break
        except Exception as e:
            print(f"  RSS fetch failed for {source_name} ({e})")

        if len(results) >= max_items:
            break

    return results
