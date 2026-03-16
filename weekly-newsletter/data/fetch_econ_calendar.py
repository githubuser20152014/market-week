"""Live economic calendar fetch for the weekly newsletter.

Adapts daybreak's FRED/Finnhub calendar logic for a 7-day weekly window.
Produces output matching the existing fixture schema:
  {
    "past_week":     [ { date, event, importance, actual, expected, previous,
                         unit, surprise, impact } ... ],
    "upcoming_week": [ { date, event, importance } ... ]
  }

Falls back to the nearest existing fixture if the live fetch fails.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# ---------------------------------------------------------------------------
# FRED configuration — mirrors daybreak's _FRED_RELEASES / _FRED_SERIES
# ---------------------------------------------------------------------------

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
    19:  ("Housing Starts",                1, "Housing Starts"),
    23:  ("Manufacturers' New Orders",     1, "Factory Orders"),
}

_FRED_SERIES = {
    10:  ("CPIAUCSL",  "mom_and_yoy_pct", "%", "", "CPIAUCNS"),
    31:  ("PPIACO",    "mom_pct",  "%",  "MoM"),
    54:  ("PCE",       "mom_pct",  "%",  "MoM"),
    50:  ("PAYEMS",    "mom_diff", "K",  "MoM chg"),
    44:  ("RSAFS",     "mom_pct",  "%",  "MoM"),
    53:  ("A191RL1Q225SBEA", "level", "%", "QoQ SAAR"),
    17:  ("INDPRO",    "mom_pct",  "%",  "MoM"),
    82:  ("BOPGSTB",   "level",    "B",  ""),
    175: ("UMCSENT",   "level",    "",   ""),
    19:  ("HOUST",     "level",    "K",  "SAAR"),
}

_FRED_RELEASE_TIMES = {
    10:  "8:30 AM ET",
    53:  "8:30 AM ET",
    54:  "8:30 AM ET",
    50:  "8:30 AM ET",
    44:  "8:30 AM ET",
    31:  "8:30 AM ET",
    21:  "10:00 AM ET",
    22:  "10:00 AM ET",
    17:  "9:15 AM ET",
    46:  "8:30 AM ET",
    82:  "8:30 AM ET",
    175: "10:00 AM ET",
    19:  "8:30 AM ET",
    23:  "10:00 AM ET",
}

_FINNHUB_KEYWORDS = {
    "cpi", "gdp", "fomc", "fed", "ecb", "pce", "nonfarm", "payroll",
    "unemployment", "retail", "inflation", "ppi", "jobless", "claims",
}


# ---------------------------------------------------------------------------
# Date range helpers
# ---------------------------------------------------------------------------

def _week_bounds(end_date: str):
    """Compute (past_mon, past_fri, next_mon, next_fri) for a newsletter date.

    For a Saturday newsletter:
      past_week  = Mon-Fri of the week that just ended
      upcoming   = Mon-Fri of the following week
    """
    end = datetime.strptime(end_date, "%Y-%m-%d")
    weekday = end.weekday()  # Mon=0 … Sun=6

    # Most-recent Friday at or before end_date
    days_since_friday = (weekday - 4) % 7
    past_friday = end - timedelta(days=days_since_friday)
    past_monday = past_friday - timedelta(days=4)

    # Next Monday after end_date
    days_to_monday = (7 - weekday) % 7 or 7
    next_monday = end + timedelta(days=days_to_monday)
    next_friday = next_monday + timedelta(days=4)

    return (
        past_monday.strftime("%Y-%m-%d"),
        past_friday.strftime("%Y-%m-%d"),
        next_monday.strftime("%Y-%m-%d"),
        next_friday.strftime("%Y-%m-%d"),
    )


def _date_range(start: str, end: str):
    """Yield each date string from start to end inclusive."""
    d = datetime.strptime(start, "%Y-%m-%d")
    stop = datetime.strptime(end, "%Y-%m-%d")
    while d <= stop:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


# ---------------------------------------------------------------------------
# FRED helpers (adapted from fetch_daybreak_data._fetch_fred_observation)
# ---------------------------------------------------------------------------

def _fetch_fred_observation(series_id: str, api_key: str, n: int = 13,
                            units: str = "lin") -> list:
    import requests
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id":  series_id,
        "api_key":    api_key,
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      n,
        "units":      units,
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
    return result


def _compute_actual(series_id: str, transform: str, unit: str,
                    label_suffix: str, api_key: str,
                    yoy_series_id: str = "") -> tuple:
    """Return (actual_str, previous_str, unit_str) from FRED."""
    try:
        obs = _fetch_fred_observation(series_id, api_key)
        if not obs:
            return "--", "--", unit
        latest_val = obs[0][1]

        if transform == "level":
            actual = f"{latest_val:,.1f}"
            prev   = f"{obs[1][1]:,.1f}" if len(obs) > 1 else "--"
            return actual, prev, unit

        if transform == "mom_and_yoy_pct":
            mom_str = yoy_str = "--"
            mom_obs = _fetch_fred_observation(series_id, api_key, n=2, units="pch")
            if mom_obs:
                mom_str = f"{mom_obs[0][1]:+.1f}%"
            yoy_obs = _fetch_fred_observation(
                yoy_series_id or series_id, api_key, n=2, units="pc1"
            )
            if yoy_obs:
                yoy_str = f"{yoy_obs[0][1]:+.1f}%"
            actual = f"{mom_str} MoM / {yoy_str} YoY" if yoy_str != "--" else mom_str
            return actual, "--", ""

        if transform == "mom_pct" and len(obs) >= 2:
            pct = (latest_val - obs[1][1]) / abs(obs[1][1]) * 100
            return f"{pct:+.1f}%", "--", ""

        if transform == "yoy_pct" and len(obs) >= 5:
            pct = (latest_val - obs[4][1]) / abs(obs[4][1]) * 100
            return f"{pct:+.1f}%", "--", ""

        if transform == "mom_diff" and len(obs) >= 2:
            diff = latest_val - obs[1][1]
            prev = obs[1][1]
            return f"{diff:+,.0f}{unit}", f"{prev:,.0f}{unit}", ""

    except Exception:
        pass
    return "--", "--", unit


# ---------------------------------------------------------------------------
# FRED calendar fetch for a date range
# ---------------------------------------------------------------------------

def _fetch_fred_range(start: str, end: str, api_key: str, fetch_actuals: bool) -> list:
    """Return a list of event dicts for all FRED releases in [start, end]."""
    import requests

    url = "https://api.stlouisfed.org/fred/releases/dates"
    params = {
        "realtime_start":                      start,
        "realtime_end":                        end,
        "include_release_dates_with_no_data":  "true",
        "sort_order":                          "asc",
        "api_key":                             api_key,
        "file_type":                           "json",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    release_dates = resp.json().get("release_dates", [])

    events = []
    for rd in release_dates:
        release_id   = rd.get("release_id")
        release_date = rd.get("date", "")
        if release_id not in _FRED_RELEASES:
            continue
        _, importance, label = _FRED_RELEASES[release_id]

        actual = previous = "--"
        unit   = ""
        expected = "See tradingeconomics.com"
        surprise = ""

        if fetch_actuals and release_id in _FRED_SERIES:
            fred_entry = _FRED_SERIES[release_id]
            series_id, transform, unit, label_suffix = fred_entry[:4]
            yoy_series = fred_entry[4] if len(fred_entry) > 4 else ""
            try:
                actual, previous, unit = _compute_actual(
                    series_id, transform, unit, label_suffix, api_key,
                    yoy_series_id=yoy_series,
                )
                print(f"    {label}: actual={actual}")
            except Exception as e:
                print(f"    {label} fetch failed ({e})")

        events.append({
            "date":       release_date,
            "event":      label,
            "importance": importance,
            "actual":     actual,
            "expected":   expected,
            "previous":   previous,
            "unit":       unit,
            "surprise":   surprise,
            "impact":     "",
            "time_est":   _FRED_RELEASE_TIMES.get(release_id, ""),
            "source":     "FRED",
        })
    return events


# ---------------------------------------------------------------------------
# Finnhub fallback for a date range
# ---------------------------------------------------------------------------

def _fetch_finnhub_range(start: str, end: str, api_key: str, is_past: bool) -> list:
    """Return event dicts from Finnhub for the given date range."""
    import requests

    url    = "https://finnhub.io/api/v1/calendar/economic"
    params = {"from": start, "to": end, "token": api_key}
    resp   = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    raw_events = resp.json().get("economicCalendar", [])

    events = []
    for ev in raw_events:
        importance = ev.get("importance", 0)
        event_name = ev.get("event", "")
        if importance < 2:
            continue
        name_lower = event_name.lower()
        if not any(kw in name_lower for kw in _FINNHUB_KEYWORDS):
            if importance < 3:
                continue

        ev_date = (ev.get("time", "")[:10] if ev.get("time")
                   else ev.get("date", ""))
        if not ev_date:
            continue

        actual_val   = ev.get("actual")
        expected_val = ev.get("estimate")

        actual_str   = str(actual_val)   if actual_val   is not None else "--"
        expected_str = str(expected_val) if expected_val is not None else "--"
        previous_str = str(ev.get("prev", "--"))

        # Derive surprise direction if both values are numeric
        surprise = ""
        if is_past and actual_val is not None and expected_val is not None:
            try:
                if float(actual_val) > float(expected_val):
                    surprise = "above"
                elif float(actual_val) < float(expected_val):
                    surprise = "below"
                else:
                    surprise = "in-line"
            except (TypeError, ValueError):
                pass

        events.append({
            "date":       ev_date,
            "event":      event_name,
            "importance": importance,
            "actual":     actual_str,
            "expected":   expected_str,
            "previous":   previous_str,
            "unit":       ev.get("unit", ""),
            "surprise":   surprise,
            "impact":     "",
            "time_est":   ev.get("time", ""),
            "source":     "Finnhub",
        })
    return events


def _fetch_range(start: str, end: str, fetch_actuals: bool) -> list:
    """Fetch events for a date range, trying FRED first then Finnhub."""
    fred_key    = os.environ.get("FRED_API_KEY", "")
    finnhub_key = os.environ.get("FINNHUB_API_KEY", "")

    if fred_key:
        try:
            return _fetch_fred_range(start, end, fred_key, fetch_actuals)
        except Exception as e:
            print(f"  FRED calendar fetch failed ({e})")

    if finnhub_key:
        try:
            return _fetch_finnhub_range(start, end, finnhub_key, fetch_actuals)
        except Exception as e:
            print(f"  Finnhub calendar fetch failed ({e})")

    if not fred_key and not finnhub_key:
        print("  No FRED_API_KEY or FINNHUB_API_KEY — skipping live econ calendar.")

    return []


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def fetch_econ_calendar_live(end_date: str) -> dict:
    """Fetch the weekly econ calendar live from FRED/Finnhub.

    Args:
        end_date: Newsletter date string YYYY-MM-DD (typically a Saturday).

    Returns:
        Dict with 'past_week' and 'upcoming_week' event lists.
        Writes the result to fixtures/econ_calendar_YYYY-MM-DD.json.
    """
    past_mon, past_fri, next_mon, next_fri = _week_bounds(end_date)
    print(f"  Fetching past-week econ calendar ({past_mon} – {past_fri}) ...")
    past_events = _fetch_range(past_mon, past_fri, fetch_actuals=True)

    print(f"  Fetching upcoming-week econ calendar ({next_mon} – {next_fri}) ...")
    upcoming_events = _fetch_range(next_mon, next_fri, fetch_actuals=False)

    # Strip source/time_est/impact from upcoming events (schema: minimal)
    upcoming_clean = [
        {
            "date":       ev["date"],
            "event":      ev["event"],
            "importance": ev["importance"],
        }
        for ev in upcoming_events
    ]

    # Keep past events with full schema; ensure required keys present
    past_clean = []
    for ev in past_events:
        past_clean.append({
            "date":       ev.get("date", ""),
            "event":      ev.get("event", ""),
            "importance": ev.get("importance", 1),
            "actual":     ev.get("actual", "--"),
            "expected":   ev.get("expected", "--"),
            "previous":   ev.get("previous", "--"),
            "unit":       ev.get("unit", ""),
            "surprise":   ev.get("surprise", ""),
            "impact":     ev.get("impact", ""),
        })

    result = {"past_week": past_clean, "upcoming_week": upcoming_clean}

    # Write fixture
    fixture_path = FIXTURES_DIR / f"econ_calendar_{end_date}.json"
    FIXTURES_DIR.mkdir(exist_ok=True)
    with open(fixture_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Saved econ calendar fixture → {fixture_path.name}")

    return result


def fetch_econ_calendar_with_fallback(end_date: str) -> dict:
    """Try live fetch; fall back to nearest fixture with a warning."""
    try:
        return fetch_econ_calendar_live(end_date)
    except Exception as e:
        print(f"  Live econ calendar fetch failed ({e}). Trying nearest fixture ...")

    # Find closest existing fixture
    target = datetime.strptime(end_date, "%Y-%m-%d")
    candidates = []
    for f in FIXTURES_DIR.glob("econ_calendar_*.json"):
        date_part = f.stem.replace("econ_calendar_", "")
        try:
            d = datetime.strptime(date_part, "%Y-%m-%d")
            candidates.append((abs((d - target).days), f))
        except ValueError:
            continue

    if not candidates:
        raise FileNotFoundError(
            f"No econ calendar fixture found near {end_date} and live fetch failed."
        )

    candidates.sort(key=lambda x: x[0])
    days_off, fixture_path = candidates[0]
    print(f"  WARNING: Using fixture {fixture_path.name} ({days_off} days off — data may be stale).")
    with open(fixture_path) as f:
        return json.load(f)
