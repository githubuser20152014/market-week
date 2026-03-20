Run the Market Day Break generator with review checkpoints before publishing and before sending email.

**Step 0 — Fetch verified prices via Perplexity:**

1. Determine DATE from $ARGUMENTS (or today if empty). Compute YESTERDAY = DATE minus 1 calendar day.
2. Check if `weekly-newsletter/fixtures/daybreak_DATE.json` already exists — if so, skip to Step 1.
3. Load yesterday's fixture (`weekly-newsletter/fixtures/daybreak_YESTERDAY.json`) for `prev_close` values. If it doesn't exist, note that `daily_pct` will be omitted from the fixture.
4. Run three targeted Perplexity queries using the `mcp__perplexity__perplexity_ask` tool:

   **Query 1 — US equities + commodities + bonds:**
   > What were the official closing prices on [DATE] for: S&P 500, Dow Jones, Nasdaq Composite, Russell 2000, Gold spot price, 10-year Treasury yield, USD Index (DXY), WTI Crude Oil, S&P 500 futures, Nasdaq futures, Dow futures, Gold futures, WTI Crude futures? Return JSON only with keys: sp500, dow, nasdaq, russell2000, gold_spot, ten_year_yield, usd_index, wti_crude, sp_futures, nasdaq_futures, dow_futures, gold_futures, wti_futures. Use 4 PM ET close for equities. Yield as percentage (e.g. 4.32). Settlement price for futures.

   **Query 2 — International overnight indices:**
   > What were the most recent closing prices for: Nikkei 225, Hang Seng, KOSPI, Nifty 50, ASX 200, DAX, FTSE 100, CAC 40, Euro Stoxx 50 as of the morning of [DATE] US time? Return JSON only with keys: nikkei, hang_seng, kospi, nifty50, asx200, dax, ftse100, cac40, eurostoxx50.

   **Query 3 — FX rates:**
   > What were the FX closing rates at 5 PM ET on [DATE] for: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CNH, CHF/USD? Return JSON only with keys: eurusd, gbpusd, usdjpy, audusd, usdcnh, chfusd.

5. Apply sanity bounds check on each returned price. Flag any value outside these ranges and ask the user to confirm or correct before proceeding:

   | Asset | Min | Max |
   |-------|-----|-----|
   | S&P 500 | 3,000 | 8,000 |
   | Dow | 20,000 | 55,000 |
   | Nasdaq | 8,000 | 25,000 |
   | Gold spot | 1,500 | 6,000 |
   | WTI Crude | 40 | 200 |
   | 10Y Yield | 0.5 | 8.0 |
   | EUR/USD | 0.80 | 1.50 |
   | USD/JPY | 80 | 200 |
   | Nikkei | 20,000 | 55,000 |

   - If a price is out of bounds: show the flagged value and ask the user to confirm or correct it.
   - If Perplexity can't find a specific price: fall back to yfinance for that asset only (note in fixture).
   - If Perplexity is entirely unavailable: fall through to yfinance for all assets (existing behavior — skip to Step 1 and pass `--live`).

6. For each asset where yesterday's fixture has a `close` value, compute:
   - `daily_pct = (close / prev_close - 1) * 100`
   - For 10Y Treasury: `yield_change_bps = (ten_year_yield - prev_ten_year_yield) * 100`

7. Build the fixture by running:

   ```bash
   python weekly-newsletter/data/build_perplexity_fixture.py \
       --date DATE \
       --prices 'JSON'
   ```

   Where `JSON` is a single-line JSON string with three keys — `"us"`, `"intl"`, `"fx"` — populated from the Perplexity query results above. Use `null` for any price Perplexity could not find, including holiday-closed markets. For holiday markets, also pass a note key (e.g. `"nikkei_note": "Holiday — Vernal Equinox"`).

   Example shape:
   ```json
   {
     "us":   {"sp500": 5500, "dow": 44000, "nasdaq": 18000, "russell2000": 2100,
              "gold_spot": 3200, "ten_year_yield": 4.35, "usd_index": 104.2,
              "wti_crude": 72.5, "sp_futures": 5490, "nasdaq_futures": 17950,
              "dow_futures": 43900, "gold_futures": 3205, "wti_futures": 72.3},
     "intl": {"nikkei": null, "nikkei_note": "Holiday", "hang_seng": 25000,
              "kospi": 2700, "nifty50": 23000, "asx200": 8200,
              "dax": 22000, "ftse100": 9800, "cac40": 7600, "eurostoxx50": 5400},
     "fx":   {"eurusd": 1.08, "gbpusd": 1.27, "usdjpy": 150.5,
              "audusd": 0.63, "usdcnh": 7.25, "chfusd": 1.12}
   }
   ```

   The script automatically loads yesterday's fixture for `prev_close` values, computes `daily_pct`, and fetches `econ_calendar` + `market_news` via FRED/RSS. It sets `meta.generation_source = "perplexity"` in the saved fixture.

**Step 1 — Generate the Markdown only:**

```bash
bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS
```

Because Step 0 already wrote the fixture, the script will detect it and run without `--live`.

After running, read the generated Markdown file and display its full contents to the user for review.

**Step 2 — Review checkpoint (content):**

Ask the user:
> "Here's the newsletter for [date]. Does everything look good, or would you like any changes before I generate the PDF and social posts?"

Wait for the user's response. If they request changes, make the edits to the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Generate PDF + social posts + publish (only after user confirms content):**

Once the user approves the content, run:

```bash
bash weekly-newsletter/publish_daybreak.sh [DATE] --publish
```

This generates the PDF and social posts (LinkedIn, X, Substack) from the approved Markdown, rebuilds the static site, commits, pushes to GitHub Pages, and saves an email preview HTML to `output/email_preview_[DATE].html`.

**Step 4 — Review checkpoint (email):**

Read `weekly-newsletter/output/email_preview_[DATE].html` and display the email subject line and a summary of its contents. Then ask the user:

> "The site is live. Here's a preview of the subscriber email — subject: '[subject]'. Ready to send to subscribers?"

Wait for the user's response. If they request changes, edit the `.md` file, then re-run Step 3 to regenerate all outputs.

**Step 5 — Send email (only after user confirms):**

Once the user approves, run:

```bash
bash weekly-newsletter/publish_daybreak.sh [DATE] --send-email
```

If $ARGUMENTS is empty, use today's date for all steps.
