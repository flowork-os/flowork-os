---
name: metaphysics-oracle-engine
slash_command: /oracle
description: "Unified sovereign metaphysics, astrology, divination, feng shui, tarot, and classical philosophy oracle engine."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "metaphysics-engine"
  - "bazi-divination"
  - "qimen-dunjia"
  - "ziwei-doushu"
  - "feng-shui"
  - "flying-stars"
  - "bazhai-kanyu"
  - "tarot-divination"
  - "yuelao-lingqian"
  - "zodiac-compatibility"
  - "eastern-philosophy"
  - "heart-sutra"
  - "diamond-sutra"
  - "dao-de-jing"
  - "solar-terms"
  - "ten-gods"
  - "wuxing-elements"
  - "auspicious-selection"
  - "counseling-wisdom"
  - "sovereign-oracle"
---

# 🔮 Sovereign Metaphysics & Oracle Engine: metaphysics-oracle-engine

## Objective
The `metaphysics-oracle-engine` consolidates Eastern and Western metaphysics, astrology, divination, spatial energy analysis, and philosophical wisdom into a unified, deterministic, sovereign computational framework in Flowork OS. It eliminates scattered external dependencies and disparate SaaS divination tools by integrating seven classical subsystems into a single high-performance CLI tool (`flowork-oracle`):
1. **Four Pillars of Destiny (BaZi / 八字命理):** Pure Python astronomical solar-terms engine calculating Year, Month, Day, and Hour GanZhi, Ten Gods (十神), Hidden Stems (藏干), Luck Pillars (大运), and Classical Shen Sha (神煞).
2. **Qi Men Dun Jia (奇门遁甲):** Classical time-space cosmic board calculating Nine Stars (九星), Eight Gates (八门), Eight Deities (八神), Earth/Heaven Plates (天地盘), Xun Shou, Kong Wang, and Yi Ma.
3. **Zi Wei Dou Shu (紫微斗数):** Purple Star astrological chart engine calculating the 12 Palaces (命宫, 财帛, 官禄, 夫妻, etc.), 14 Major Stars with brightness states, Minor Stars, and Four Transformations (化禄, 化权, 化科, 化忌).
4. **Feng Shui & Kanyu (堪舆风水):** Comprehensive spatial energy system computing Eight Mansions (八宅), Period 9 Flying Stars (九运玄空飞星 2024–2043), Sha Qi remedies, and ZeRi auspicious date selection.
5. **Yue Lao & Marriage Affinity (月老灵签与生肖合婚):** Full 100-stick Yue Lao fortune poem engine with deterministic hash generation, Chinese zodiac compatibility (六合, 三合, 六冲, 六害), and Five Elements synastry.
6. **Western Tarot (西方78张塔罗牌阵):** Rider-Waite-Smith 78 cards with Major and Minor Arcana, Single, Three-Card (Past/Present/Future), Celtic Cross, Love, and Decision spreads with psychological archetype interpretation.
7. **Classical Wisdom & Philosophical Counseling (儒释道典籍智慧):** Heart Sutra (心经), Diamond Sutra (金刚经), Platform Sutra (六祖坛经), and Dao De Jing (道德经) meditation and dilemma counseling.

## Prerequisites
- Linux OS with Flowork OS Rust/Kernel environment.
- Python 3.12+ runtime with system standard library and `lunar_python` (installed system-wide).
- Executable binary `/usr/local/bin/flowork-oracle` and `/opt/floworkos/bin/flowork-oracle` symlinked to `/opt/floworkos/skills/metaphysics-oracle-engine/oracle.py`.
- Correct filesystem ownership `awenkaudico:awenkaudico` with permissions `chmod 775` across all skill directories and scripts.

## Standard Operating Procedure

### 1. Four Pillars of Destiny (BaZi) Calculation
Compute natal chart and dynamic luck cycles:
```bash
flowork-oracle bazi --solar 1990-05-15 --hour 10:30 --gender 男
# Or for female:
flowork-oracle bazi --solar 1995-08-20 --hour 14:15 --gender 女
```
Outputs complete Four Pillars table, hidden stems, Ten Gods distribution, Day Master element strength, decadal luck pillars, and auspicious/inauspicious Shen Sha.

### 2. Qi Men Dun Jia Time-Space Board
Cast a dynamic hourly time-space divination plate:
```bash
flowork-oracle qimen --datetime "2026-11-19 12:00"
# Real-time current moment:
flowork-oracle qimen --datetime now
# Output machine-readable JSON:
flowork-oracle qimen --datetime "2026-11-19 12:00" --json
```

### 3. Zi Wei Dou Shu Natal Chart
Generate 12-palace astrological star placement:
```bash
flowork-oracle ziwei --datetime "1990-05-15 10:30" --gender 男
flowork-oracle ziwei --datetime "1995-08-20 14:15" --gender 女 --json
```

### 4. Feng Shui & Flying Stars (Kanyu)
Compute Period 9 (九运) Flying Star chart and Eight Mansions:
```bash
# Calculate Period 9 Flying Star chart for North-South sitting/facing
flowork-oracle fengshui feixing --sit 子 --facing 午 --yun 9

# Calculate Eight Mansions (BaZhai) for resident:
flowork-oracle fengshui bazhai --year 1990 --gender male

# Check Almanac and ZeRi for auspicious dates:
flowork-oracle fengshui zeri --start 2026-12-01 --end 2026-12-10 --purpose 开业
```

### 5. Yue Lao Divination & Zodiac Compatibility
Draw a sacred Yue Lao fortune stick or analyze relationship compatibility:
```bash
# Draw a deterministic fortune stick for an inquiry
flowork-oracle yinyuan --draw --name "张三" --question "何时步入婚姻"

# Inspect specific stick number (1 to 100):
flowork-oracle yinyuan --stick 1

# Evaluate marriage compatibility between two zodiac signs:
flowork-oracle yinyuan --zodiac 龙 鸡
flowork-oracle yinyuan --zodiac 虎 猪
```

### 6. Western Tarot Reading
Perform archetypal Tarot spreads:
```bash
# Three-card spread (Past, Present, Future):
flowork-oracle tarot --spread three --question "Startup launch in 2027"

# Celtic Cross comprehensive spread:
flowork-oracle tarot --spread celtic --question "Long-term trajectory"
```

### 7. Classical Wisdom Counseling
Consult classical scriptures for psychological grounding and discernment:
```bash
# Guidance on anxiety and uncertainty:
flowork-oracle wisdom --query "工作压力巨大，对未来充满不确定感"

# Guidance on dealing with loss or failure:
flowork-oracle wisdom --query "面对事业挫折与失败该如何调伏心境"

# Directly inspect core teachings of a sutra:
flowork-oracle wisdom --sutra heart_sutra
flowork-oracle wisdom --sutra dao_de_jing
```

## Verification
1. Run automated unit test suite:
   ```bash
   python3 /opt/floworkos/skills/metaphysics-oracle-engine/tests/test_oracle.py
   ```
   Must return `Ran 7 tests ... OK` with Exit Code 0.
2. Validate CLI launcher availability:
   ```bash
   flowork-oracle --help
   ```
3. Run Flowork OS Skill Linter:
   ```bash
   /opt/floworkos/bin/flowork-lint-skills /opt/floworkos/skills
   ```
   Must pass all quality gates with 0 failures.

## Failure Modes
1. **Invalid Timezone or Date Format:** Occurs if date/time string is malformed. Ensure ISO `YYYY-MM-DD HH:MM` format is provided.
2. **Missing `lunar_python` Dependency:** If missing on an external host, install via `pip install lunar_python tzdata`.
3. **Compass Degree Out of Range:** When entering degrees for Feng Shui facing, ensure azimuth angle is within `0` to `360`.
4. **Gender Input Ambiguity:** Valid gender values are `男`, `女`, `male`, `female`. Invalid strings default gracefully to standard polarity.
