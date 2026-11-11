# SimilarWeb Traffic Intelligence Skill

## Purpose
Provides global domain traffic rankings, 30-day velocity, audience estimation, and server infrastructure telemetry without requiring commercial subscriptions or browser extensions.

## CLI Commands
```bash
# Analyze website traffic, global rank, and estimated monthly visits
similarweb detik.com
similarweb https://floworkos.com

# Raw JSON output for programmatic pipelines
similarweb --json detik.com
```

## Features
- **Global Traffic Rank**: Historical and current rank based on verified global web traffic data.
- **Estimated Monthly Visits**: Calibrated power-law model matching official analytics metrics.
- **Weekly Trend**: Pinpoints rank gains (+places) or declines over the trailing 7-day window.
- **Infrastructure Telemetry**: Identifies host IP, CDN proxying (Cloudflare), and underlying server technology.
