# The Morning Brief — {{ date }}

*Daily Edition · Market intelligence at the open*

---

## The Brief

{{ narrative }}

{{ plain_summary }}

---
{% if market_news %}
## Market-Moving Headlines

| # | Headline | Source |
|---|----------|--------|
{% for item in market_news -%}
| {{ loop.index }} | [{{ item.headline }}]({{ item.url }}) | {{ item.source }} |
{% endfor %}
---
{% endif %}
## Positioning Notes

{% for tip in tips -%}
- {{ tip }}
{% endfor %}

---

*Framework Foundry — Daily Edition. For informational purposes only. Not investment advice.*
