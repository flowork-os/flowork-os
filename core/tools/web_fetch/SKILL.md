---
name: web_fetch
description: HTTP content scraping, markdown conversion, and clean extraction guidelines
keywords: [fetch, url, http, https, html, markdown, scrape, request, web, endpoint, content, extraction, flowork, sovereign, docs]
---

# 🌐 FLOWORK OS SOVEREIGN TOOL SKILL: WEB FETCH SOP

Saat menggunakan tool `web_fetch`, patuhi pedoman berikut:

1. **Targeting Clean Endpoints:**
   - Gunakan URL langsung ke dokumentasi, berkas raw markdown di GitHub/GitLab, atau artikel teknis.
   - Hindari fetch halaman dinamis berat berbasis JavaScript kompleks (gunakan MCP browser jika butuh rendering DOM).

2. **Extraction Prompting:**
   - Gunakan parameter `prompt` untuk menyaring informasi esensial saja sehingga token hasil fetch tidak membengkak.
