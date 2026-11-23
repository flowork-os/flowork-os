# Context & Activation Scope
Active when creating, editing, auditing, or parsing spreadsheets (`.xlsx`, `.csv`), financial models, tabular calculations, or balance sheets.

# Mandatory Behavioral Invariants
1. **Formula-First Dynamic Modeling:** Write dynamic formulas for all calculated totals, subtotals, ratios, and aggregations (`SUM`, `AVERAGE`, `XLOOKUP`, `INDEX/MATCH`). Never hardcode calculated numbers in total rows.
2. **Standard Formula Grammar:** Use standard uppercase formula names compatible with Excel and LibreOffice. Avoid localized syntax, volatile functions, or deprecated legacy syntax (`VLOOKUP` where `XLOOKUP` is supported).
3. **Number Formatting & Tabular Typography:** Explicitly format cells by type: currency (`$#,##0.00`), percentages (`0.0%`), dates (`YYYY-MM-DD`), and tabular lining figures (`tabular-nums`) to ensure vertical decimal alignment.
4. **Model Balance Integrity:** Validate double-entry equality, cash flow continuity, and margin sanity. When modifying sheets programmatically (via `openpyxl`), preserve formulas and update cached calculated values or trigger recalculation.

# Strict Prohibitions
- PROHIBITED: Hardcoding static mathematical results in summary rows where a dynamic formula belongs.
- PROHIBITED: Outputting raw unformatted floating point decimals (e.g. `12.345678912`).
- PROHIBITED: Overwriting user formula cells with static values during automated edits.
