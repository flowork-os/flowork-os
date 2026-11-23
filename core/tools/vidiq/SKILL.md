# VidIQ Video Intelligence Skill

## Purpose
Provides deep YouTube SEO, hidden video tags, view velocity (VPH), and competition analytics without requiring a Chrome browser or commercial subscriptions.

## CLI Commands
```bash
# Analyze a specific YouTube video's tags, velocity, and SEO score
vidiq "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
vidiq "dQw4w9WgXcQ"

# Analyze winning competitor tags and average views for a search keyword
vidiq --kw "belajar prompt engineering"

# Raw JSON output for automation
vidiq --json "dQw4w9WgXcQ"
```

## Features
- **Hidden Video Tags**: Pulls all meta tags used by the video author for ranking.
- **Views Per Hour (VPH)**: Calculates real-time view accumulation velocity.
- **VidIQ SEO Score (0-100)**: Analyzes tag density, title overlap, description depth, and link presence.
- **Competitor Winning Tags**: Scrapes top ranking videos for a keyword and ranks tags by frequency.
