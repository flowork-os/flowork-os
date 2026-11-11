---
name: founder-suite
description: Comprehensive pre-launch business stress-testing suite based on Hormozi offers, Thiel monopoly, Jobs product lens, 100-buyer swarm simulations, Van Westendorp pricing sensitivity, and CFO unit economics.
domain: code_dev
keywords:
  - business
  - founder
  - startup
  - validation
  - pricing
  - unit_economics
  - cfo
  - hormozi
  - thiel
  - jobs
  - panel
  - simulation
  - break_even
  - cash_runway
  - sensitivity
  - offer_stack
  - marketing
  - competitors
  - planning
  - sovereign
---

# 👑 FLOWORK OS SOVEREIGN SKILL: FOUNDER SUITE

## 1. Objective
Equip Mr. Flow and Flowork OS agents with an autonomous business stress-testing framework to validate business ideas, calculate price sensitivity curves, model consumer swarm objections, and audit unit economics before committing engineering resources or capital.

## 2. Prerequisites
1. Python 3 runtime available at `/usr/bin/python3`.
2. Local calculation engines located in `/opt/floworkos/skills/founder-suite/scripts/`:
   - `panel.py`: 100-buyer persona simulation.
   - `van_westendorp.py`: Microeconomic price sensitivity calculations (PMC, OPP, IDP, PME).
   - `unit_economics.py`: Contribution margin, break-even units/day, cash runway.
   - `compile.py`: Plan assembly and mathematical verdict.
3. Access to `run_shell_command` or native execution instruments.

## 3. Standard Operating Procedure
Execute business modeling and validation following the structured eleven workflows:
1. **Board Evaluation (`/founder-board`)**: Score through Hormozi ($100M Offers), Thiel (Zero to One), and Jobs (Apple product UX) perspectives to vote FUND, FUND IF, or PASS.
2. **Competitor Scouting (`/founder-competitors`)**: Map direct, indirect, and substitute competitors, pricing structures, and consumer friction points.
3. **Consumer Swarm Simulation (`/founder-consumer`)**: Run `panel.py` with 100 demographic buyer agents to extract purchase objections and willingness to pay.
4. **Price Sensitivity Analysis (`/founder-pricing`)**: Execute `van_westendorp.py` to establish Point of Marginal Cheapness, Optimal Price Point, Indifference Price Point, and Point of Marginal Expensiveness.
5. **Offer Architecture (`/founder-offer`)**: Design the offer stack with bonuses, risk-reversal guarantees, and scarcity mechanisms.
6. **CFO Unit Economics (`/founder-cfo`)**: Execute `unit_economics.py` to calculate contribution margin, break-even units per day, and runway.
7. **Marketing & Go-To-Market (`/founder-marketing`)**: Define acquisition channels, 30-day sprint milestones, and maximum allowable CAC.
8. **Brand Architecture (`/founder-brand`)**: Produce naming conventions, positioning statements, tone of voice, and visual design brief.
9. **Operations Blueprint (`/founder-ops`)**: Register suppliers, operational routines, tooling, and risk mitigation registries.
10. **Launch Execution (`/founder-launch`)**: Draft low-cost pilot tests, launch checklists, and initial 30-day execution sheets.
11. **Plan Compilation (`/founder-plan`)**: Assemble outputs via `compile.py` to produce a final empirical verdict (PROFITABLE, NOT YET, or INCOMPLETE).

## 4. Verification
1. Run local scripts to confirm zero-crash operation:
   `python3 /opt/floworkos/skills/founder-suite/scripts/unit_economics.py`
2. Validate output schema and financial metrics for non-negative margins and valid runway calculations.
3. Verify compliance with sovereign skill standards using `/opt/floworkos/skills/lint_skills.js`.

## 5. Failure Modes
1. **Missing Input Parameters**: Financial models fail if price or cost per unit is zero or negative. Ensure all inputs are validated before running calculations.
2. **Infinite Runway or Divide-by-Zero**: If fixed costs or burn rate is zero, handle edge cases gracefully with explicit guards.
3. **Over-Optimistic Conversion**: Synthetic swarms may yield biased results if demographic prompts lack adversarial personas. Always inject skeptic personas.
