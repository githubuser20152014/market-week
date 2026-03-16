"""Patch chart_data column for the 30 new cards in market_iq.csv."""
import csv, json, io

CHART_DATA = {
    "PMI": '[{"label":"Nov \'25","value":48.4,"displayValue":"48.4"},{"label":"Dec \'25","value":49.3,"displayValue":"49.3"},{"label":"Jan \'26","value":50.9,"displayValue":"50.9"},{"label":"Feb \'26","value":49.0,"displayValue":"49.0"}]',
    "PPI": '[{"label":"Oct \'25","value":2.4},{"label":"Nov \'25","value":2.6},{"label":"Dec \'25","value":3.0},{"label":"Jan \'26","value":3.5}]',
    "VIX": '[{"label":"Nov \'25","value":13.5,"displayValue":"13.5"},{"label":"Dec \'25","value":15.2,"displayValue":"15.2"},{"label":"Jan \'26","value":18.7,"displayValue":"18.7"},{"label":"Feb \'26","value":22.3,"displayValue":"22.3"}]',
    "DXY": '[{"label":"Nov \'25","value":104.2,"displayValue":"104.2"},{"label":"Dec \'25","value":102.1,"displayValue":"102.1"},{"label":"Jan \'26","value":101.3,"displayValue":"101.3"},{"label":"Feb \'26","value":98.8,"displayValue":"98.8"}]',
    "JOLTS": '[{"label":"Sep \'25","value":8.1,"displayValue":"8.1M"},{"label":"Oct \'25","value":7.9,"displayValue":"7.9M"},{"label":"Nov \'25","value":7.8,"displayValue":"7.8M"},{"label":"Dec \'25","value":7.7,"displayValue":"7.7M"}]',
    "Claims": '[{"label":"Feb 8","value":215,"displayValue":"215K"},{"label":"Feb 15","value":218,"displayValue":"218K"},{"label":"Feb 22","value":221,"displayValue":"221K"},{"label":"Mar 1","value":220,"displayValue":"220K"}]',
    "Retail Sales": '[{"label":"Oct \'25","value":0.4,"displayValue":"+0.4%"},{"label":"Nov \'25","value":0.8,"displayValue":"+0.8%"},{"label":"Dec \'25","value":-0.9,"displayValue":"-0.9%"},{"label":"Jan \'26","value":0.2,"displayValue":"+0.2%"}]',
    "Housing Starts": '[{"label":"Oct \'25","value":1.31,"displayValue":"1.31M"},{"label":"Nov \'25","value":1.29,"displayValue":"1.29M"},{"label":"Dec \'25","value":1.50,"displayValue":"1.50M"},{"label":"Jan \'26","value":1.37,"displayValue":"1.37M"}]',
    "Credit Spreads": '[{"label":"Nov \'25","value":310,"displayValue":"310"},{"label":"Dec \'25","value":330,"displayValue":"330"},{"label":"Jan \'26","value":355,"displayValue":"355"},{"label":"Feb \'26","value":380,"displayValue":"380"}]',
    "Real Rate": None,
    "Consumer Confidence": '[{"label":"Nov \'25","value":111.7,"displayValue":"111.7"},{"label":"Dec \'25","value":104.7,"displayValue":"104.7"},{"label":"Jan \'26","value":105.3,"displayValue":"105.3"},{"label":"Feb \'26","value":98.3,"displayValue":"98.3"}]',
    "Michigan Sentiment": '[{"label":"Nov \'25","value":71.8,"displayValue":"71.8"},{"label":"Dec \'25","value":74.0,"displayValue":"74.0"},{"label":"Jan \'26","value":71.1,"displayValue":"71.1"},{"label":"Feb \'26","value":64.7,"displayValue":"64.7"}]',
    "Industrial Production": '[{"label":"Oct \'25","value":0.3,"displayValue":"+0.3%"},{"label":"Nov \'25","value":0.2,"displayValue":"+0.2%"},{"label":"Dec \'25","value":0.9,"displayValue":"+0.9%"},{"label":"Jan \'26","value":-0.1,"displayValue":"-0.1%"}]',
    "Durable Goods": '[{"label":"Oct \'25","value":-0.7,"displayValue":"-0.7%"},{"label":"Nov \'25","value":0.9,"displayValue":"+0.9%"},{"label":"Dec \'25","value":0.2,"displayValue":"+0.2%"},{"label":"Jan \'26","value":3.1,"displayValue":"+3.1%"}]',
    "Breakeven Inflation": '[{"label":"Nov \'25","value":2.18},{"label":"Dec \'25","value":2.22},{"label":"Jan \'26","value":2.26},{"label":"Feb \'26","value":2.31}]',
    "Import Prices": '[{"label":"Oct \'25","value":0.1,"displayValue":"+0.1%"},{"label":"Nov \'25","value":-0.1,"displayValue":"-0.1%"},{"label":"Dec \'25","value":0.2,"displayValue":"+0.2%"},{"label":"Jan \'26","value":0.4,"displayValue":"+0.4%"}]',
    "Income & Spending": '[{"label":"Oct \'25","value":0.5,"displayValue":"+0.5%"},{"label":"Nov \'25","value":0.6,"displayValue":"+0.6%"},{"label":"Dec \'25","value":0.7,"displayValue":"+0.7%"},{"label":"Jan \'26","value":0.2,"displayValue":"+0.2%"}]',
    "U-6": '[{"label":"Nov \'25","value":7.5,"displayValue":"7.5%"},{"label":"Dec \'25","value":7.6,"displayValue":"7.6%"},{"label":"Jan \'26","value":7.8,"displayValue":"7.8%"},{"label":"Feb \'26","value":8.0,"displayValue":"8.0%"}]',
    "LFPR": '[{"label":"Nov \'25","value":62.9,"displayValue":"62.9%"},{"label":"Dec \'25","value":62.8,"displayValue":"62.8%"},{"label":"Jan \'26","value":62.7,"displayValue":"62.7%"},{"label":"Feb \'26","value":62.6,"displayValue":"62.6%"}]',
    "Dot Plot": None,
    "QT": '[{"label":"Nov \'25","value":6.95,"displayValue":"$6.95T"},{"label":"Dec \'25","value":6.90,"displayValue":"$6.90T"},{"label":"Jan \'26","value":6.85,"displayValue":"$6.85T"},{"label":"Feb \'26","value":6.80,"displayValue":"$6.80T"}]',
    "M2": '[{"label":"Nov \'25","value":3.5,"displayValue":"+3.5%"},{"label":"Dec \'25","value":3.7,"displayValue":"+3.7%"},{"label":"Jan \'26","value":3.9,"displayValue":"+3.9%"},{"label":"Feb \'26","value":4.1,"displayValue":"+4.1%"}]',
    "SLOOS": '[{"label":"Q1 \'25","value":22.4,"displayValue":"22.4%"},{"label":"Q2 \'25","value":18.3,"displayValue":"18.3%"},{"label":"Q3 \'25","value":16.1,"displayValue":"16.1%"},{"label":"Q4 \'25","value":14.6,"displayValue":"14.6%"}]',
    "CAPE": '[{"label":"Nov \'25","value":36.2,"displayValue":"36.2"},{"label":"Dec \'25","value":35.5,"displayValue":"35.5"},{"label":"Jan \'26","value":35.0,"displayValue":"35.0"},{"label":"Feb \'26","value":34.8,"displayValue":"34.8"}]',
    "Gold": '[{"label":"Dec \'25","value":3800,"displayValue":"$3,800"},{"label":"Jan \'26","value":4350,"displayValue":"$4,350"},{"label":"Feb \'26","value":4850,"displayValue":"$4,850"},{"label":"Mar \'26","value":5204,"displayValue":"$5,204"}]',
    "WTI": '[{"label":"Dec \'25","value":69.2,"displayValue":"$69.2"},{"label":"Jan \'26","value":74.5,"displayValue":"$74.5"},{"label":"Feb \'26","value":72.0,"displayValue":"$72.0"},{"label":"Mar \'26","value":70.1,"displayValue":"$70.1"}]',
    "EPS Growth": '[{"label":"Q1 \'25","value":5.8,"displayValue":"+5.8%"},{"label":"Q2 \'25","value":9.4,"displayValue":"+9.4%"},{"label":"Q3 \'25","value":8.7,"displayValue":"+8.7%"},{"label":"Q4 \'25","value":8.2,"displayValue":"+8.2%"}]',
    "Trade Balance": '[{"label":"Oct \'25","value":-84.4,"displayValue":"-$84B"},{"label":"Nov \'25","value":-78.2,"displayValue":"-$78B"},{"label":"Dec \'25","value":-98.4,"displayValue":"-$98B"},{"label":"Jan \'26","value":-131.4,"displayValue":"-$131B"}]',
    "Tariff Rate": '[{"label":"Pre-2025","value":2.5,"displayValue":"2.5%"},{"label":"Jan 2025","value":5.1,"displayValue":"5.1%"},{"label":"Sep 2025","value":8.3,"displayValue":"8.3%"},{"label":"Mar 2026","value":13.5,"displayValue":"13.5%"}]',
    "USD/CNY": '[{"label":"Nov \'25","value":7.19,"displayValue":"7.19"},{"label":"Dec \'25","value":7.24,"displayValue":"7.24"},{"label":"Jan \'26","value":7.27,"displayValue":"7.27"},{"label":"Feb \'26","value":7.25,"displayValue":"7.25"}]',
}

csv_path = "content/market_iq.csv"
with open(csv_path, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

patched = 0
for row in rows:
    term = row["term"]
    if term in CHART_DATA:
        new_val = CHART_DATA[term]
        row["chart_data"] = new_val if new_val is not None else ""
        patched += 1

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Patched {patched} rows")
# Spot check
for row in rows:
    if row["term"] == "PMI":
        print("PMI chart_data:", row["chart_data"][:60])
    if row["term"] == "Gold":
        print("Gold chart_data:", row["chart_data"][:60])
