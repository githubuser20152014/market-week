"""Append 30 missing cards (07-36) to market_iq.csv."""
import ast
import csv
import json

HEADERS = [
    "category", "term", "definition", "context", "frequency", "trend", "trend_label",
    "featured", "full_name", "formula", "current_value", "current_value_period",
    "current_value_color", "chart_label", "chart_type", "chart_data",
    "stat1_label", "stat1_value", "stat1_sub", "stat1_color",
    "stat2_label", "stat2_value", "stat2_sub", "stat2_color",
    "insight", "source", "back_source_label", "back_title"
]

with open("extracted_cards.py", encoding="utf-8") as f:
    raw = f.read()

cards = ast.literal_eval(raw.strip())

rows = []
for c in cards:
    # Normalise chart_data
    chart_data = c.get("chart_data")
    if chart_data is None:
        chart_data_str = ""
    elif isinstance(chart_data, (list, dict)):
        chart_data_str = json.dumps(chart_data)
    else:
        chart_data_str = str(chart_data)

    row = {
        "category": c.get("category", ""),
        "term": c.get("term", ""),
        "definition": c.get("definition", ""),
        "context": c.get("context", ""),
        "frequency": c.get("frequency", ""),
        "trend": c.get("trend", "flat"),
        "trend_label": c.get("trend_label", ""),
        "featured": "",
        "full_name": c.get("full_name", ""),
        "formula": c.get("formula", ""),
        "current_value": c.get("current_value", ""),
        "current_value_period": c.get("current_value_period", ""),
        "current_value_color": c.get("current_value_color", "gray"),
        "chart_label": c.get("chart_label", ""),
        "chart_type": c.get("chart_type", ""),
        "chart_data": chart_data_str,
        "stat1_label": c.get("stat1_label", ""),
        "stat1_value": c.get("stat1_value", ""),
        "stat1_sub": c.get("stat1_sub", ""),
        "stat1_color": c.get("stat1_color", "gray"),
        "stat2_label": c.get("stat2_label", ""),
        "stat2_value": c.get("stat2_value", ""),
        "stat2_sub": c.get("stat2_sub", ""),
        "stat2_color": c.get("stat2_color", "gray"),
        "insight": c.get("insight", ""),
        "source": c.get("source", ""),
        "back_source_label": c.get("back_source_label", ""),
        "back_title": c.get("back_title", ""),
    }
    rows.append(row)

csv_path = "content/market_iq.csv"
with open(csv_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    for row in rows:
        writer.writerow(row)

print(f"Appended {len(rows)} rows to {csv_path}")

# Verify total rows
with open(csv_path, encoding="utf-8") as f:
    total = sum(1 for _ in f) - 1  # subtract header
print(f"Total card rows in CSV: {total}")
