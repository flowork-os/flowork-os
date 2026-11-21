# Ubersuggest Headless SEO Intelligence Tool

## 1. Description & Scope
Autonomous keyword research and SEO difficulty evaluator reverse-engineered directly from the official Ubersuggest Chrome extension. Operates 100% headlessly with zero Chrome browser overhead.

## 2. Parameter Schema
- `keyword` (string, required): The target seed search term (e.g. `"sepatu kulit"`, `"cloud hosting"`).
- `country` (string, optional, default `"id"`): ISO 2-letter country code (`"id"`, `"us"`, `"uk"`, `"sg"`, `"my"`, etc.).
- `language` (string, optional, default `"id"` for ID, `"en"` otherwise): 2-letter language code.
- `include_ideas` (boolean, optional, default `true`): Whether to fetch related long-tail keyword ideas.

## 3. Returned Output
- `metrics.monthly_search_volume`: Exact monthly searches.
- `metrics.seo_difficulty_score`: Organic difficulty from 0 to 100.
- `metrics.seo_difficulty_assessment`: Plain English ranking feasibility.
- `metrics.cost_per_click_idr` / `cost_per_click_usd`: CPC values.
- `metrics.search_intent`: Intent categorizations (Informational, Navigational, Commercial, Transactional).
- `related_keyword_ideas`: High-affinity long-tail keyword suggestions.
