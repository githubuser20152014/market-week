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
from datetime import datetime, timedelta
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
CONFIG_DIR   = Path(__file__).resolve().parent.parent / "config"

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


# ── Live fetchers ─────────────────────────────────────────────────────────────

def _fetch_live(date_str: str) -> dict:
    """Assemble the full daybreak payload from live sources."""
    with open(CONFIG_DIR / "daybreak_symbols.json") as f:
        cfg = json.load(f)

    us_close       = _fetch_us_close(date_str, cfg["us_indices"])
    intl_overnight = _fetch_intl_overnight(date_str, cfg["intl_indices"])
    fx             = _fetch_fx(date_str, cfg["fx"])
    futures        = _fetch_futures(date_str, cfg["futures"])
    econ_calendar  = _fetch_econ_calendar(date_str)
    market_news    = _fetch_market_news(date_str)

    return {
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


def _fetch_us_close(date_str: str, index_cfg: dict) -> dict:
    """Fetch previous US session closes (yesterday's 4 PM data).

    Uses a 2-day download to get both yesterday's close and the day before
    (for daily_pct calculation).
    """
    import yfinance as yf
    from pandas import Timestamp

    target = datetime.strptime(date_str, "%Y-%m-%d")
    # Download from 5 days back to catch weekends/holidays
    start = (target - timedelta(days=7)).strftime("%Y-%m-%d")
    end   = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    result = {}
    for name, info in index_cfg.items():
        symbol   = info["symbol"]
        is_yield = info.get("is_yield", False)
        try:
            df = yf.download(symbol, start=start, end=end,
                             progress=False, auto_adjust=True)
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                df.columns = df.columns.droplevel(1)
            df = df[df.index.dayofweek < 5]  # drop weekends
            if len(df) < 2:
                result[name] = _empty_us_entry(symbol, is_yield, table=info.get("table", True))
                continue

            prev_close = float(df["Close"].iloc[-2])
            close      = float(df["Close"].iloc[-1])
            daily_pct  = (close / prev_close - 1) * 100

            entry = {
                "symbol":    symbol,
                "prev_close": round(prev_close, 4),
                "close":      round(close, 4),
                "daily_pct":  round(daily_pct, 4),
                "table":      info.get("table", True),
            }
            if is_yield:
                entry["is_yield"]          = True
                entry["yield_change_bps"]  = round((close - prev_close) * 100, 2)
            result[name] = entry
        except Exception as e:
            print(f"  US close fetch failed for {name} ({e})")
            result[name] = _empty_us_entry(symbol, is_yield, table=info.get("table", True))

    return result


def _empty_us_entry(symbol: str, is_yield: bool = False, table: bool = True) -> dict:
    entry = {"symbol": symbol, "prev_close": None, "close": None, "daily_pct": None, "table": table}
    if is_yield:
        entry["is_yield"] = True
        entry["yield_change_bps"] = None
    return entry


def _fetch_intl_overnight(date_str: str, index_cfg: dict) -> dict:
    """Fetch overnight international index data.

    - APAC (Asia-Pacific): markets have closed by 6 AM EST; use yesterday's close.
    - Europe: markets may be ~2-3h into the session; use intraday price where available.

    Each entry carries status="closed" or status="partial".
    """
    import yfinance as yf

    target = datetime.strptime(date_str, "%Y-%m-%d")
    start  = (target - timedelta(days=7)).strftime("%Y-%m-%d")
    end    = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    result = {}
    for name, info in index_cfg.items():
        symbol = info["symbol"]
        region = info.get("region", "")
        try:
            # First get daily data for prev_close and last available close
            df_daily = yf.download(symbol, start=start, end=end,
                                   progress=False, auto_adjust=True)
            if isinstance(df_daily.columns, __import__("pandas").MultiIndex):
                df_daily.columns = df_daily.columns.droplevel(1)
            df_daily = df_daily[df_daily.index.dayofweek < 5]

            if len(df_daily) < 1:
                result[name] = _empty_intl_entry(symbol, region)
                continue

            prev_close = float(df_daily["Close"].iloc[-2]) if len(df_daily) >= 2 else None
            last_close = float(df_daily["Close"].iloc[-1])

            if region == "Europe":
                # Try to get a live intraday price for European early session
                try:
                    df_1m = yf.download(symbol, period="1d", interval="1m",
                                        progress=False, auto_adjust=True)
                    if isinstance(df_1m.columns, __import__("pandas").MultiIndex):
                        df_1m.columns = df_1m.columns.droplevel(1)
                    if not df_1m.empty:
                        live_price = float(df_1m["Close"].iloc[-1])
                        daily_pct  = ((live_price / prev_close) - 1) * 100 if prev_close else None
                        result[name] = {
                            "symbol":       symbol,
                            "region":       region,
                            "status":       "partial",
                            "close":        round(live_price, 2),
                            "prev_close":   round(prev_close, 2) if prev_close else None,
                            "daily_pct":    round(daily_pct, 4) if daily_pct is not None else None,
                            "session_note": "Early session (~3h in)",
                        }
                        continue
                except Exception:
                    pass  # fall through to daily close

                # Fallback: yesterday's close
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
            else:
                # APAC — always use yesterday's close
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


def _empty_intl_entry(symbol: str, region: str) -> dict:
    return {
        "symbol": symbol, "region": region, "status": "closed",
        "close": None, "prev_close": None, "daily_pct": None,
        "session_note": "No data",
    }


def _fetch_fx(date_str: str, fx_cfg: dict) -> dict:
    """Fetch FX rates (2-day download for daily_pct)."""
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
            if len(df) < 2:
                # Fallback: hourly data over 5 days (handles pairs like CNH=X)
                try:
                    df_h = yf.download(symbol, period="5d", interval="1h",
                                       progress=False, auto_adjust=True)
                    if isinstance(df_h.columns, __import__("pandas").MultiIndex):
                        df_h.columns = df_h.columns.droplevel(1)
                    if len(df_h) >= 2:
                        # ~24h ago as prev_close proxy
                        prev_close = float(df_h["Close"].iloc[-25]) \
                            if len(df_h) > 25 else float(df_h["Close"].iloc[0])
                        rate      = float(df_h["Close"].iloc[-1])
                        daily_pct = (rate / prev_close - 1) * 100
                        result[name] = {
                            "symbol":     symbol,
                            "rate":       round(rate, 5),
                            "prev_close": round(prev_close, 5),
                            "daily_pct":  round(daily_pct, 4),
                        }
                    else:
                        result[name] = {"symbol": symbol, "rate": None,
                                        "prev_close": None, "daily_pct": None}
                except Exception:
                    result[name] = {"symbol": symbol, "rate": None,
                                    "prev_close": None, "daily_pct": None}
                continue

            prev_close = float(df["Close"].iloc[-2])
            rate       = float(df["Close"].iloc[-1])
            daily_pct  = (rate / prev_close - 1) * 100

            result[name] = {
                "symbol":     symbol,
                "rate":       round(rate, 5),
                "prev_close": round(prev_close, 5),
                "daily_pct":  round(daily_pct, 4),
            }
        except Exception as e:
            print(f"  FX fetch failed for {name} ({e})")
            result[name] = {"symbol": symbol, "rate": None,
                            "prev_close": None, "daily_pct": None}
    return result


def _fetch_futures(date_str: str, futures_cfg: dict) -> dict:
    """Fetch pre-market futures prices.

    Uses fast_info["last_price"] for the current price when available,
    falling back to the last available close from a 2-day download.
    """
    import yfinance as yf

    target = datetime.strptime(date_str, "%Y-%m-%d")
    start  = (target - timedelta(days=7)).strftime("%Y-%m-%d")
    end    = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    result = {}
    for name, info in futures_cfg.items():
        symbol = info["symbol"]
        try:
            ticker = yf.Ticker(symbol)
            # Try fast_info for live price
            live_price = None
            try:
                fi = ticker.fast_info
                lp = fi.get("last_price") if hasattr(fi, "get") else getattr(fi, "last_price", None)
                if lp and lp > 0:
                    live_price = float(lp)
            except Exception:
                pass

            # Daily data for prev_close
            df = yf.download(symbol, start=start, end=end,
                             progress=False, auto_adjust=True)
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                df.columns = df.columns.droplevel(1)
            df = df[df.index.dayofweek < 5]

            if len(df) < 2:
                result[name] = {"symbol": symbol, "price": live_price,
                                "prev_close": None, "daily_pct": None}
                continue

            prev_close = float(df["Close"].iloc[-2])
            price      = live_price if live_price else float(df["Close"].iloc[-1])
            daily_pct  = (price / prev_close - 1) * 100

            result[name] = {
                "symbol":     symbol,
                "price":      round(price, 2),
                "prev_close": round(prev_close, 2),
                "daily_pct":  round(daily_pct, 4),
            }
        except Exception as e:
            print(f"  Futures fetch failed for {name} ({e})")
            result[name] = {"symbol": symbol, "price": None,
                            "prev_close": None, "daily_pct": None}
    return result


def _fetch_econ_calendar(date_str: str) -> dict:
    """Fetch economic calendar via Finnhub, split into yesterday/today buckets.

    Falls back to an empty calendar if the API key is missing or the call fails.
    """
    import os
    target = datetime.strptime(date_str, "%Y-%m-%d")
    yesterday = (target - timedelta(days=1)).strftime("%Y-%m-%d")

    result = {"yesterday": [], "today": []}

    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        print("  No FINNHUB_API_KEY — skipping live econ calendar.")
        return result

    try:
        import requests
        url = "https://finnhub.io/api/v1/calendar/economic"
        params = {"from": yesterday, "to": date_str, "token": api_key}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        events = resp.json().get("economicCalendar", [])
    except Exception as e:
        print(f"  Finnhub econ calendar fetch failed ({e})")
        return result

    _HIGH_IMPORTANCE_KEYWORDS = {"cpi", "gdp", "fomc", "fed", "ecb", "pce",
                                 "jobs", "nonfarm", "unemployment", "retail"}

    for ev in events:
        importance = ev.get("importance", 0)
        event_name = ev.get("event", "")
        # Filter to importance > 1 and macro-relevant keywords
        if importance < 2:
            continue
        name_lower = event_name.lower()
        if not any(kw in name_lower for kw in _HIGH_IMPORTANCE_KEYWORDS):
            # Still include if importance is high
            if importance < 3:
                continue

        entry = {
            "event":    event_name,
            "actual":   ev.get("actual", "--"),
            "expected": ev.get("estimate", "--"),
            "previous": ev.get("prev", "--"),
            "unit":     ev.get("unit", ""),
            "importance": importance,
            "time_est": ev.get("time", ""),
        }
        ev_date = ev.get("time", "")[:10] if ev.get("time") else ev.get("date", "")
        if ev_date == yesterday:
            result["yesterday"].append(entry)
        elif ev_date == date_str:
            result["today"].append(entry)

    return result


# ── Market News (RSS) ──────────────────────────────────────────────────────────

_RSS_FEEDS = [
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("AP News", "https://rsshub.app/apnews/topics/apf-topnews"),
    ("CNBC",    "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
]

_MARKET_KEYWORDS = {
    "war", "iran", "sanction", "tariff", "trade", "oil", "opec", "fed", "rate",
    "inflation", "election", "crisis", "ceasefire", "attack", "china", "taiwan",
    "russia", "ukraine", "nato", "g7", "g20", "budget", "debt", "default", "strike",
    "embargo", "nuclear", "missile", "troops", "geopolit", "conflict", "accord",
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
