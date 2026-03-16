"""Cross-validate prices from two independent sources before newsletter generation.

Resolution strategy (applied before halting):
  1. Date-offset check  — try ±1 trading day on each source.
  2. Majority vote      — if 2 of 3 sources (yfinance, FRED, Stooq) agree within
                          tolerance, trust the majority, mark the outlier, continue.
  3. Genuine ambiguity  — halt only if ALL three sources disagree.  Prints a clear
                          diagnostic table, not a stack trace.

Audit trail written to output/price_resolution_YYYY-MM-DD.txt.
"""

import csv
import io
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# ---------------------------------------------------------------------------
# Asset maps — weekly newsletter
# ---------------------------------------------------------------------------

FRED_MAP = {
    "Gold":         "GOLDAMGBD228NLBM",
    "10Y Treasury": "DGS10",
}

STOOQ_MAP = {
    "S&P 500":    "^spx",
    "Dow Jones":  "^dji",
    "Nasdaq":     "^ndq",
    "Russell 2000": "^rut",
    "USD Index":  "usd",
}

# ---------------------------------------------------------------------------
# Asset maps — daybreak extended coverage
# ---------------------------------------------------------------------------

# Stooq symbols for international indices (best-effort; skip if unavailable)
STOOQ_INTL_MAP = {
    "Nikkei 225":    "^nk225",
    "DAX":           "^dax",
    "FTSE 100":      "^ftse",
    "CAC 40":        "^cac",
    "Euro Stoxx 50": "^stoxx50e",
    "Hang Seng":     "^hsi",
}

# FX pairs — Stooq FX tickers (best-effort)
STOOQ_FX_MAP = {
    "EUR/USD": "eurusd",
    "GBP/USD": "gbpusd",
    "USD/JPY": "usdjpy",
    "AUD/USD": "audusd",
}

# Futures — no secondary source available
FUTURES_NO_SECONDARY = [
    "S&P Futures", "Nasdaq Futures", "Dow Futures",
    "Gold Futures", "10Y T-Note", "WTI Crude Oil",
]


class PriceDiscrepancyError(Exception):
    """Raised when a price cannot be resolved across sources."""


# ---------------------------------------------------------------------------
# Source fetchers
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

    if best_date is not None and (target - best_date).days > 7:
        print(f"  WARNING: FRED {series_id} latest is {best_date.date()} "
              f"({(target - best_date).days}d before {effective}).")
    return best_value


def fetch_stooq_prices(symbol_map: dict, date_str: str,
                       offset_days: int = 0) -> dict:
    """Fetch closing prices from Stooq for all symbols in symbol_map."""
    try:
        import pandas_datareader.data as web
        import pandas as pd
    except ImportError:
        print("  pandas_datareader not installed; skipping Stooq verification.")
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
        except Exception as e:
            print(f"  Stooq fetch failed for {symbol} ({name}): {e}")

    return result


# ---------------------------------------------------------------------------
# Primary data extractors
# ---------------------------------------------------------------------------

def _get_yf_close(primary_data: dict, name: str) -> float | None:
    """Extract most recent close from weekly fixture (list of OHLCV dicts)."""
    asset = primary_data.get(name)
    if not asset or not asset.get("data"):
        return None
    rows = asset["data"]
    return rows[-1]["close"] if rows else None


def _get_daybreak_close(raw: dict, name: str) -> float | None:
    """Extract close from daybreak us_close / intl_overnight / fx data."""
    # us_close: {name: {close, ...}}
    for section in ("us_close", "intl_overnight", "fx"):
        entry = raw.get(section, {}).get(name)
        if entry:
            val = entry.get("close") or entry.get("rate")
            if val is not None:
                return float(val)
    return None


# ---------------------------------------------------------------------------
# Smart resolution helpers
# ---------------------------------------------------------------------------

def _within(a: float, b: float, pct: float) -> bool:
    if b == 0:
        return False
    return abs(a - b) / abs(b) * 100 <= pct


def _diff_pct(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return abs(a - b) / abs(b) * 100


def _try_resolve(name: str, yf_val: float, fred_val: float | None,
                 stooq_val: float | None, date_str: str,
                 fred_series: str | None, stooq_symbol: str | None,
                 tolerance_pct: float) -> tuple[float, str]:
    """Attempt auto-resolution via date-offset check then majority vote.

    Returns (resolved_value, resolution_note).
    Raises PriceDiscrepancyError if no resolution found.
    """
    sources = {"yfinance": yf_val}
    if fred_val  is not None: sources["FRED"]  = fred_val
    if stooq_val is not None: sources["Stooq"] = stooq_val

    # ── Check if already within tolerance ────────────────────────────────────
    secondary_vals = [v for k, v in sources.items() if k != "yfinance"]
    if all(_within(yf_val, sv, tolerance_pct) for sv in secondary_vals):
        return yf_val, "OK"

    # ── Step 1: Date-offset check (±1 trading day on secondaries) ────────────
    for offset in (-1, 1):
        adj_fred  = None
        adj_stooq = None

        if fred_series:
            adj_fred = fetch_fred_price(fred_series, date_str, offset_days=offset)
        if stooq_symbol:
            stooq_adj = fetch_stooq_prices({name: stooq_symbol}, date_str, offset_days=offset)
            adj_stooq = stooq_adj.get(name)

        adj_sources = [v for v in (adj_fred, adj_stooq) if v is not None]
        if adj_sources and all(_within(yf_val, sv, tolerance_pct) for sv in adj_sources):
            note = f"auto-resolved via date offset {offset:+d}d"
            return yf_val, note

    # ── Step 2: Majority vote across all three sources ───────────────────────
    all_vals = {k: v for k, v in sources.items() if v is not None}
    keys = list(all_vals.keys())

    if len(all_vals) >= 3:
        for i, k1 in enumerate(keys):
            for k2 in keys[i + 1:]:
                v1, v2 = all_vals[k1], all_vals[k2]
                if _within(v1, v2, tolerance_pct):
                    # Two sources agree — use their average
                    resolved = (v1 + v2) / 2
                    outlier  = [k for k in keys if k != k1 and k != k2]
                    note = f"majority vote ({k1}+{k2} agree); {outlier[0] if outlier else 'other'} marked as outlier"
                    return resolved, note

    # ── Step 3: Genuine ambiguity — cannot auto-resolve ──────────────────────
    table = [f"  {'Source':<12} {'Value':>12} {'Diff%':>8}"]
    table.append("  " + "-" * 35)
    ref = yf_val
    for k, v in all_vals.items():
        d = _diff_pct(v, ref) if k != "yfinance" else 0.0
        marker = " ← ref" if k == "yfinance" else f"  {d:.1f}%"
        table.append(f"  {k:<12} {v:>12,.2f}{marker}")
    diag = "\n".join(table)

    raise PriceDiscrepancyError(
        f"Cannot auto-resolve {name} — all sources disagree beyond {tolerance_pct}%:\n"
        f"{diag}\n"
        f"Investigate manually and re-run."
    )


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def _write_audit_log(date_str: str, entries: list[dict]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"price_resolution_{date_str}.txt"
    lines = [
        f"Price Resolution Audit — {date_str}",
        "=" * 60,
        "",
    ]
    for e in entries:
        status = e.get("status", "")
        note   = e.get("note", "")
        yf     = e.get("yf_val")
        sec    = e.get("sec_val")

        yf_str  = f"{yf:,.2f}"  if yf  is not None else "N/A"
        sec_str = f"{sec:,.2f}" if sec is not None else "N/A"

        lines.append(f"{e['name']:<20} yfinance={yf_str:<12} secondary={sec_str:<12} "
                     f"status={status:<20} note={note}")
    lines.append("")
    path.write_text("\n".join(lines))
    print(f"  Resolution log -> {path.name}")


# ---------------------------------------------------------------------------
# Main verify function — weekly newsletter
# ---------------------------------------------------------------------------

def verify_prices(primary_data: dict, date_str: str,
                  tolerance_pct: float = 2.0) -> None:
    """Compare yfinance weekly close prices against FRED/Stooq.

    Auto-resolves date-offset and majority-vote cases.
    Halts (raises PriceDiscrepancyError) only for genuine ambiguity.
    Writes audit log to output/price_resolution_YYYY-MM-DD.txt.
    """
    print(f"\nPrice Verification — week ending {date_str}")
    print(f"{'Asset':<18} {'yfinance':>12} {'Secondary':>12} {'Diff%':>8}   Status")
    print("-" * 64)

    fred_results  = {}
    for name, series_id in FRED_MAP.items():
        val = fetch_fred_price(series_id, date_str)
        if val is not None:
            fred_results[name] = val

    stooq_results = fetch_stooq_prices(STOOQ_MAP, date_str)
    secondary     = {**fred_results, **stooq_results}

    audit_entries  = []
    fatal_errors   = []
    all_assets     = list(FRED_MAP.keys()) + list(STOOQ_MAP.keys())

    for name in all_assets:
        yf_val  = _get_yf_close(primary_data, name)
        sec_val = secondary.get(name)

        if yf_val is None:
            print(f"  {name:<16} {'N/A':>12} {'N/A':>12} {'N/A':>8}   - (not in primary)")
            audit_entries.append({"name": name, "yf_val": None, "sec_val": sec_val,
                                   "status": "skipped", "note": "not in primary data"})
            continue

        if sec_val is None:
            print(f"  {name:<16} {yf_val:>12,.2f} {'N/A':>12} {'N/A':>8}   ? secondary unavailable")
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": None,
                                   "status": "unverified", "note": "secondary unavailable"})
            continue

        diff = _diff_pct(yf_val, sec_val)

        if diff <= tolerance_pct:
            print(f"  {name:<16} {yf_val:>12,.2f} {sec_val:>12,.2f} {diff:>7.1f}%   OK")
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": sec_val,
                                   "status": "OK", "note": f"diff {diff:.1f}%"})
            continue

        # Attempt auto-resolution
        fred_series   = FRED_MAP.get(name)
        stooq_symbol  = STOOQ_MAP.get(name)
        fred_val2     = fred_results.get(name) if name in FRED_MAP else None
        stooq_val2    = stooq_results.get(name) if name in STOOQ_MAP else None

        try:
            resolved, note = _try_resolve(
                name, yf_val, fred_val2, stooq_val2,
                date_str, fred_series, stooq_symbol, tolerance_pct,
            )
            print(f"  {name:<16} {yf_val:>12,.2f} {sec_val:>12,.2f} {diff:>7.1f}%   AUTO ({note})")
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": sec_val,
                                   "status": "auto-resolved", "note": note})
        except PriceDiscrepancyError as exc:
            print(f"  {name:<16} {yf_val:>12,.2f} {sec_val:>12,.2f} {diff:>7.1f}%   FAIL")
            fatal_errors.append(str(exc))
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": sec_val,
                                   "status": "FAIL", "note": f"diff {diff:.1f}%"})

    print()
    _write_audit_log(date_str, audit_entries)

    if fatal_errors:
        raise PriceDiscrepancyError(
            "Price verification failed — manual review required:\n\n"
            + "\n\n".join(fatal_errors)
        )

    print(f"All prices verified (tolerance={tolerance_pct}%).\n")


# ---------------------------------------------------------------------------
# Extended verify — daybreak (full asset coverage)
# ---------------------------------------------------------------------------

def verify_prices_daybreak(raw: dict, date_str: str,
                            tolerance_pct: float = 2.0) -> None:
    """Verify daybreak prices across US indices, intl, FX, and futures.

    US indices + Gold + 10Y:  FRED + Stooq as secondaries.
    Intl indices:             Stooq best-effort; "secondary unavailable" if not found.
    FX pairs:                 Stooq FX best-effort; flagged if not available.
    Futures:                  Logged as "no secondary source" — yfinance only.
    """
    print(f"\nDaybreak Price Verification — {date_str}")
    print(f"{'Asset':<22} {'yfinance':>12} {'Secondary':>12} {'Diff%':>8}   Status")
    print("-" * 68)

    # Fetch secondaries
    fred_results  = {}
    for name, series_id in FRED_MAP.items():
        val = fetch_fred_price(series_id, date_str)
        if val is not None:
            fred_results[name] = val

    stooq_results    = fetch_stooq_prices(STOOQ_MAP, date_str)
    stooq_intl       = fetch_stooq_prices(STOOQ_INTL_MAP, date_str)
    stooq_fx         = fetch_stooq_prices(STOOQ_FX_MAP, date_str)

    all_secondary = {**fred_results, **stooq_results, **stooq_intl, **stooq_fx}

    audit_entries = []
    fatal_errors  = []

    def _check(name: str, yf_val: float | None, sec_val: float | None,
                category: str = ""):
        """Compare one asset; attempt auto-resolution on mismatch."""
        if yf_val is None:
            print(f"  {name:<20} {'N/A':>12} {'N/A':>12} {'N/A':>8}   - not in data")
            audit_entries.append({"name": name, "yf_val": None, "sec_val": sec_val,
                                   "status": "skipped", "note": "not in primary"})
            return

        if sec_val is None:
            label = "secondary unavailable"
            print(f"  {name:<20} {yf_val:>12,.4f} {'N/A':>12} {'N/A':>8}   ? {label}")
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": None,
                                   "status": "unverified", "note": label})
            return

        diff = _diff_pct(yf_val, sec_val)
        if diff <= tolerance_pct:
            print(f"  {name:<20} {yf_val:>12,.4f} {sec_val:>12,.4f} {diff:>7.1f}%   OK")
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": sec_val,
                                   "status": "OK", "note": f"diff {diff:.1f}%"})
            return

        # Attempt auto-resolution
        fred_s  = FRED_MAP.get(name)
        stooq_s = (STOOQ_MAP.get(name) or STOOQ_INTL_MAP.get(name)
                   or STOOQ_FX_MAP.get(name))
        f_val   = fred_results.get(name)
        sq_val  = (stooq_results.get(name) or stooq_intl.get(name)
                   or stooq_fx.get(name))

        try:
            _, note = _try_resolve(name, yf_val, f_val, sq_val,
                                   date_str, fred_s, stooq_s, tolerance_pct)
            print(f"  {name:<20} {yf_val:>12,.4f} {sec_val:>12,.4f} {diff:>7.1f}%   AUTO ({note})")
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": sec_val,
                                   "status": "auto-resolved", "note": note})
        except PriceDiscrepancyError as exc:
            print(f"  {name:<20} {yf_val:>12,.4f} {sec_val:>12,.4f} {diff:>7.1f}%   FAIL")
            fatal_errors.append(str(exc))
            audit_entries.append({"name": name, "yf_val": yf_val, "sec_val": sec_val,
                                   "status": "FAIL", "note": f"diff {diff:.1f}%"})

    # US indices + Gold + 10Y
    print("  -- US Indices / Rates --")
    us_close = raw.get("us_close", {})
    for name in list(STOOQ_MAP.keys()) + list(FRED_MAP.keys()):
        yf_val = _get_daybreak_close(raw, name)
        _check(name, yf_val, all_secondary.get(name), "us")

    # International indices
    print("  -- International Indices --")
    intl = raw.get("intl_overnight", {})
    for name in intl:
        yf_val  = _get_daybreak_close(raw, name)
        sec_val = stooq_intl.get(name)  # None if Stooq doesn't carry it
        _check(name, yf_val, sec_val, "intl")

    # FX
    print("  -- FX --")
    fx = raw.get("fx", {})
    for name in fx:
        yf_val  = _get_daybreak_close(raw, name)
        sec_val = stooq_fx.get(name)
        _check(name, yf_val, sec_val, "fx")

    # Futures — no secondary available
    print("  -- Futures (no secondary source) --")
    futures = raw.get("futures", {})
    for name in futures:
        entry = futures[name]
        price = entry.get("price")
        if price is not None:
            print(f"  {name:<20} {price:>12,.2f} {'N/A':>12} {'N/A':>8}   - no secondary")
        else:
            print(f"  {name:<20} {'N/A':>12} {'N/A':>12} {'N/A':>8}   - no data")
        audit_entries.append({"name": name, "yf_val": price, "sec_val": None,
                               "status": "no-secondary", "note": "futures — yfinance only"})

    print()
    _write_audit_log(date_str, audit_entries)

    if fatal_errors:
        raise PriceDiscrepancyError(
            "Daybreak price verification failed — manual review required:\n\n"
            + "\n\n".join(fatal_errors)
        )

    print(f"Daybreak prices verified (tolerance={tolerance_pct}%).\n")
