# Context & Activation Scope
Active when designing, generating, or coding charts, plots, graphs, analytical dashboards, SVG diagrams, and metric visualizations (Chart.js, D3, Recharts, Matplotlib, SVG).

# Mandatory Behavioral Invariants
1. **Purpose-Driven Form:** Match visualization form strictly to analytical intent (scatter/bubble for correlation, line for continuous time, ordered horizontal bar for nominal comparisons, small multiples for multidimensional splits).
2. **Scale & Baseline Honesty:** Bar charts MUST start at a zero baseline to prevent misleading magnitude distortion. Use consistent aspect ratios and avoid conflicting dual y-axes.
3. **Direct Data Labeling:** Label trend lines, peaks, and significant bars directly at the data point rather than forcing users to cross-reference distant legends.
4. **Accessible Palette & Typography:** Use colorblind-safe scales (Viridis, ColorBrewer), deliberate contrast tokens, and monospace/tabular lining digits for legend values and axis ticks.

# Strict Prohibitions
- PROHIBITED: Truncating bar chart y-axes to exaggerate negligible variations.
- PROHIBITED: Random or unsorted categorical bar charts; sort by value descending or ascending unless temporal/ordinal order applies.
- PROHIBITED: Using low-contrast neon gradients that reduce legibility on charts.
