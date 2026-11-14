/**
 * DramaBox & Melolo Flow - Cloudflare Pages Advanced Mode Edge Worker
 * Consolidated API Router, Edge Video Stream Proxy (/media/...), Edge Image Cache Proxy (/images/...),
 * Full Server Masking (Flowork-Media-Core), and Episodic SEO / VideoObject SSR Indexing
 */

let cachedMelolo = null;
let cachedDramabox = null;

async function getMeloloCatalog(env, requestUrl) {
  if (cachedMelolo && cachedMelolo.length > 0) return cachedMelolo;
  try {
    const url = new URL('/melolo_catalog.json', requestUrl);
    const resp = await env.ASSETS.fetch(url);
    const data = await resp.json();
    cachedMelolo = data.dramas || data || [];
    return cachedMelolo;
  } catch (e) {
    console.error('Failed to load melolo catalog:', e);
    return [];
  }
}

async function getDramaboxCatalog(env, requestUrl) {
  if (cachedDramabox && cachedDramabox.length > 0) return cachedDramabox;
  try {
    const url = new URL('/dramabox_catalog.json', requestUrl);
    const resp = await env.ASSETS.fetch(url);
    const data = await resp.json();
    cachedDramabox = data.dramas || data || [];
    return cachedDramabox;
  } catch (e) {
    console.error('Failed to load dramabox catalog:', e);
    return [];
  }
}

// 1. /api/browse
async function handleBrowse(request, env) {
  const { searchParams } = new URL(request.url);
  const provider = searchParams.get('provider') || 'all';
  const catId = parseInt(searchParams.get('cat_id') || '0', 10);
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = parseInt(searchParams.get('page_size') || '24', 10);

  const meloloList = (provider === 'all' || provider === 'melolo') ? await getMeloloCatalog(env, request.url) : [];
  const dramaboxList = (provider === 'all' || provider === 'dramabox') ? await getDramaboxCatalog(env, request.url) : [];

  let catalog = [];
  if (provider === 'melolo') {
    catalog = meloloList;
  } else if (provider === 'dramabox') {
    catalog = dramaboxList;
  } else {
    // Interleave catalogs
    const maxLen = Math.max(meloloList.length, dramaboxList.length);
    for (let i = 0; i < maxLen; i++) {
      if (i < meloloList.length) catalog.push(meloloList[i]);
      if (i < dramaboxList.length) catalog.push(dramaboxList[i]);
    }
  }

  // Category Filtering
  const catMap = {
    1: ['romansa', 'romance'],
    2: ['ceo', 'miliarder', 'billionaire'],
    3: ['balas dendam', 'dendam', 'revenge', 'melawan balik'],
    4: ['fantasi', 'serigala', 'werewolf', 'magic'],
    5: ['drama kehidupan', 'drama', 'kehidupan', 'urban', 'modern']
  };

  let filtered = catalog;
  if (catId in catMap) {
    const keys = catMap[catId];
    filtered = catalog.filter(d => {
      const tags = Array.isArray(d.typeTwoNames) ? d.typeTwoNames.join(' ') : '';
      const labels = Array.isArray(d.tags) ? d.tags.join(' ') : '';
      const text = `${d.category || ''} ${d.bookName || ''} ${d.title || ''} ${tags} ${labels} ${d.introduction || ''}`.toLowerCase();
      return keys.some(k => text.includes(k));
    });
  }

  const total = filtered.length;
  const totalPages = Math.ceil(total / pageSize) || 1;
  const safePage = Math.max(1, Math.min(page, totalPages));
  const start = (safePage - 1) * pageSize;
  const dramas = filtered.slice(start, start + pageSize);

  return new Response(JSON.stringify({
    status: 'success',
    pageNo: safePage,
    pages: totalPages,
    page: safePage,
    page_size: pageSize,
    total_pages: totalPages,
    total,
    provider,
    bookList: dramas,
    dramas
  }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=600'
    }
  });
}

// 2. /api/search
async function handleSearch(request, env) {
  const { searchParams } = new URL(request.url);
  const query = (searchParams.get('q') || '').trim();

  if (!query) {
    return new Response(JSON.stringify({ status: 'success', total: 0, results: [], dramas: [] }), {
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' }
    });
  }

  const lowerQ = query.toLowerCase();
  const meloloList = await getMeloloCatalog(env, request.url);
  const dramaboxList = await getDramaboxCatalog(env, request.url);

  const meloloMatches = meloloList.filter(d => 
    (d.bookName && d.bookName.toLowerCase().includes(lowerQ)) ||
    (d.introduction && d.introduction.toLowerCase().includes(lowerQ))
  );

  const dramaboxMatches = dramaboxList.filter(d => 
    (d.bookName && d.bookName.toLowerCase().includes(lowerQ)) ||
    (d.introduction && d.introduction.toLowerCase().includes(lowerQ))
  );

  let merged = [];
  const maxLen = Math.max(meloloMatches.length, dramaboxMatches.length);
  for (let i = 0; i < maxLen; i++) {
    if (i < meloloMatches.length) merged.push(meloloMatches[i]);
    if (i < dramaboxMatches.length) merged.push(dramaboxMatches[i]);
  }

  const finalResults = merged.slice(0, 50);

  return new Response(JSON.stringify({
    status: 'success',
    query,
    total: merged.length,
    results: finalResults,
    dramas: finalResults
  }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' }
  });
}

// 3. /api/detail
async function handleDetail(request, env) {
  const { searchParams } = new URL(request.url);
  const bookId = searchParams.get('bookId') || '';

  if (!bookId) {
    return new Response(JSON.stringify({ status: 'error', message: 'bookId required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  // Melolo Provider
  if (bookId.startsWith('melolo_')) {
    const slug = bookId.replace('melolo_', '');
    let meta = {
      bookId,
      bookName: slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      slug,
      category: 'Drama Melolo',
      chapterCount: 50,
      cover: `/images/melolo/${encodeURIComponent(slug)}/cover.jpg`,
      provider: 'melolo',
      introduction: 'Serial drama pendek Melolo HD sub Indo.'
    };

    let chapters = [];
    try {
      const now = Date.now();
      const apiUrl = `https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug=${encodeURIComponent(slug)}&pageType=play&episode_id=1&_refresh=${now}`;
      const resp = await fetch(apiUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Referer': `https://melolo.com/id/dramas/${slug}`
        }
      });
      const data = await resp.json();
      const series = (data.data && data.data[0]) || (data.series) || {};

      if (series.series_total_episode || series.episode_count) {
        meta.chapterCount = series.series_total_episode || series.episode_count;
      }
      if (series.series_name) meta.bookName = series.series_name;
      if (series.series_cover || series.cover_url) {
        meta.cover = `/images/cover?provider=melolo&id=${encodeURIComponent(slug)}&url=${encodeURIComponent(series.series_cover || series.cover_url)}`;
      }
      if (series.series_desc || series.desc) meta.introduction = series.series_desc || series.desc;

      const epList = series.episode_list || [];
      for (const item of epList) {
        const epNum = parseInt(item.episode_id || '0', 10);
        if (epNum > 0) {
          chapters.push({
            id: epNum,
            name: `Part ${epNum}`,
            chapterName: `Part ${epNum}`,
            index: epNum - 1,
            indexStr: `Part ${epNum}`,
            mp4: `/media/melolo/${encodeURIComponent(slug)}/${epNum}.mp4`,
            unlock: true,
            provider: 'melolo',
            slug,
            ep: epNum
          });
        }
      }
    } catch (err) {
      console.error('Error fetching Melolo live series:', err);
    }

    if (chapters.length === 0) {
      const count = meta.chapterCount || 40;
      for (let i = 1; i <= count; i++) {
        chapters.push({
          id: i,
          name: `Part ${i}`,
          chapterName: `Part ${i}`,
          index: i - 1,
          indexStr: `Part ${i}`,
          mp4: `/media/melolo/${encodeURIComponent(slug)}/${i}.mp4`,
          unlock: true,
          provider: 'melolo',
          slug,
          ep: i
        });
      }
    }

    return new Response(JSON.stringify({
      status: 'success',
      bookInfo: meta,
      chapterList: chapters,
      provider: 'melolo'
    }), {
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' }
    });
  }

  // DramaBox Provider
  let chapters = [];
  try {
    const goodbosUrl = `https://dramabox.goodbos.online/api/dramabox/allepisode?bookId=${encodeURIComponent(bookId)}`;
    const resp = await fetch(goodbosUrl, {
      headers: {
        'x-token': '6EB57533425BC1D78ADA1F80354161D4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
    const data = await resp.json();
    if (Array.isArray(data)) {
      data.forEach((ep, idx) => {
        const epNum = idx + 1;
        chapters.push({
          id: ep.chapterId || epNum,
          name: ep.chapterName || `Part ${epNum}`,
          chapterName: ep.chapterName || `Part ${epNum}`,
          index: idx,
          indexStr: `Part ${epNum}`,
          mp4: `/media/dramabox/${encodeURIComponent(bookId)}/${epNum}.mp4`,
          unlock: true,
          provider: 'dramabox'
        });
      });
    }
  } catch (err) {
    console.error('Error fetching DramaBox goodbos:', err);
  }

  const dramaboxList = await getDramaboxCatalog(env, request.url);
  const found = dramaboxList.find(d => String(d.bookId) === String(bookId));
  const meta = found ? {
    ...found,
    cover: `/images/cover?provider=dramabox&id=${encodeURIComponent(bookId)}&url=${encodeURIComponent(found.cover || '')}`
  } : {
    bookId,
    bookName: `Drama ${bookId}`,
    category: 'DramaBox',
    chapterCount: chapters.length,
    cover: `/images/dramabox/${encodeURIComponent(bookId)}/cover.jpg`,
    provider: 'dramabox',
    introduction: 'Serial drama pendek DramaBox HD sub Indo.'
  };

  return new Response(JSON.stringify({
    status: 'success',
    bookInfo: meta,
    chapterList: chapters,
    provider: 'dramabox'
  }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' }
  });
}

// 4. Upstream Episode Resolvers (Zero Upstream Exposure)
async function resolveMeloloEpisodeUrl(slug, epNum, env, requestUrl) {
  try {
    const cleanSlug = slug.replace(/^melolo_/, '');
    const now = Date.now();
    const apiUrl = `https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug=${encodeURIComponent(cleanSlug)}&pageType=play&episode_id=${epNum}&_refresh=${now}`;
    const resp = await fetch(apiUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': `https://melolo.com/id/dramas/${cleanSlug}`
      }
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    const series = (data.data && data.data[0]) || (data.series) || {};
    const epList = series.episode_list || [];
    for (const item of epList) {
      if (parseInt(item.episode_id || '0', 10) === epNum || parseInt(item.episode_number || '0', 10) === epNum) {
        const u = item.url || '';
        if (u) return u.replace(/\\u0026/g, '&');
      }
    }
    if (epList[epNum - 1] && epList[epNum - 1].url) {
      return epList[epNum - 1].url.replace(/\\u0026/g, '&');
    }
  } catch (e) {
    console.error('resolveMeloloEpisodeUrl error:', e);
  }
  return null;
}

async function resolveDramaboxEpisodeUrl(bookId, epNum, env, requestUrl) {
  try {
    const goodbosUrl = `https://dramabox.goodbos.online/api/dramabox/allepisode?bookId=${encodeURIComponent(bookId)}`;
    const resp = await fetch(goodbosUrl, {
      headers: {
        'x-token': '6EB57533425BC1D78ADA1F80354161D4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      cf: {
        cacheEverything: true,
        cacheTtl: 3600
      }
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    if (Array.isArray(data) && data.length > 0) {
      const idx = epNum - 1;
      const target = data[idx] || data.find(c => (c.chapterIndex + 1) === epNum || c.chapterId === epNum);
      if (target) {
        return target.videoUrl || target.videoUrl720 || target.mp4 || (target.cdnList && target.cdnList[0] && target.cdnList[0].videoUrl) || null;
      }
    }
  } catch (e) {
    console.error('resolveDramaboxEpisodeUrl error:', e);
  }
  return null;
}

// 5. /images/cover & /images/... - Edge Image Caching Proxy (30 Days Edge TTL)
async function handleImageCover(request, env) {
  const url = new URL(request.url);
  const cache = caches.default;
  const cacheKey = new Request(request.url, { method: 'GET' });

  // 1. Check Cloudflare Edge Cache
  let cached = await cache.match(cacheKey);
  if (cached) {
    const cachedHeaders = new Headers(cached.headers);
    cachedHeaders.set('X-Flowork-Cache', 'HIT');
    cachedHeaders.set('Server', 'Flowork-Media-Core/2.4 (Sovereign Linux)');
    return new Response(cached.body, {
      status: cached.status,
      headers: cachedHeaders
    });
  }

  // 2. Resolve image URL
  let targetUrl = url.searchParams.get('url');
  let provider = url.searchParams.get('provider') || '';
  let id = url.searchParams.get('id') || '';

  const pathMatch = url.pathname.match(/^\/images\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_.-]+)\/cover\.(jpg|jpeg|webp|png)$/);
  if (pathMatch) {
    provider = pathMatch[1];
    id = pathMatch[2];
  }

  if (!targetUrl && provider && id) {
    if (provider === 'melolo') {
      const melolo = await getMeloloCatalog(env, request.url);
      const cleanId = id.replace(/^melolo_/, '');
      const d = melolo.find(item => item.slug === cleanId || item.bookId === id || item.bookId === `melolo_${cleanId}`);
      if (d && d.cover) targetUrl = d.cover;
    } else if (provider === 'dramabox') {
      const dramabox = await getDramaboxCatalog(env, request.url);
      const d = dramabox.find(item => String(item.bookId) === String(id));
      if (d && d.cover) targetUrl = d.cover;
    }
  }

  if (!targetUrl) {
    return new Response('Cover image not found', { status: 404 });
  }

  // 3. Upstream Fetch
  const upstreamHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  };
  if (targetUrl.includes('melolo') || targetUrl.includes('edgeone.sg')) {
    upstreamHeaders['Referer'] = 'https://melolo.com/';
  }

  try {
    const upstreamResp = await fetch(targetUrl, {
      headers: upstreamHeaders,
      cf: {
        cacheEverything: true,
        cacheTtl: 2592000 // 30 days at Cloudflare Edge
      }
    });

    if (!upstreamResp.ok) {
      return new Response(`Upstream image failed: ${upstreamResp.status}`, { status: upstreamResp.status });
    }

    const contentType = upstreamResp.headers.get('content-type') || 'image/jpeg';
    const responseHeaders = new Headers({
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=2592000, s-maxage=2592000, immutable',
      'Server': 'Flowork-Media-Core/2.4 (Sovereign Linux)',
      'X-Powered-By': 'Flowork OS Media Edge',
      'X-Flowork-Cache': 'MISS',
      'Access-Control-Allow-Origin': '*'
    });

    const response = new Response(upstreamResp.body, {
      status: 200,
      headers: responseHeaders
    });

    // Store in Cloudflare Edge Cache
    try {
      await cache.put(cacheKey, response.clone());
    } catch (e) {
      console.warn('Image cache.put failed:', e);
    }

    return response;
  } catch (err) {
    return new Response(`Image fetch error: ${err.message}`, { status: 502 });
  }
}

// 6. /media/... & /api/stream - Edge Video Streaming Proxy with Range & Server Masking
async function handleMediaStream(request, env) {
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
        'Access-Control-Allow-Headers': 'Range, Content-Type'
      }
    });
  }

  const url = new URL(request.url);

  // Match /media/:provider/:id/:ep.mp4
  const mediaMatch = url.pathname.match(/^\/media\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_.-]+)\/([0-9]+)\.mp4$/);
  
  let provider = '';
  let id = '';
  let epNum = 1;
  let rawUrl = '';

  if (mediaMatch) {
    provider = mediaMatch[1];
    id = mediaMatch[2];
    epNum = parseInt(mediaMatch[3], 10);
  } else if (url.pathname === '/api/stream') {
    provider = url.searchParams.get('provider') || '';
    id = url.searchParams.get('slug') || url.searchParams.get('bookId') || url.searchParams.get('id') || '';
    epNum = parseInt(url.searchParams.get('ep') || '1', 10);
    rawUrl = url.searchParams.get('url') || '';
  }

  let targetUrl = '';
  if (provider === 'melolo' && id) {
    targetUrl = await resolveMeloloEpisodeUrl(id, epNum, env, request.url);
  } else if (provider === 'dramabox' && id) {
    targetUrl = await resolveDramaboxEpisodeUrl(id, epNum, env, request.url);
  } else if (rawUrl) {
    targetUrl = rawUrl;
  }

  if (!targetUrl) {
    return new Response('Video stream not resolved', { status: 404 });
  }

  // Anti-Hotlink Validation (allow own domain, empty referer for native players, and major search engines)
  const referer = request.headers.get('Referer') || '';
  if (referer) {
    try {
      const refHost = new URL(referer).hostname;
      const allowed = refHost === url.hostname ||
                      refHost.endsWith('pages.dev') ||
                      refHost === 'localhost' ||
                      refHost.includes('flowork') ||
                      refHost.includes('google') ||
                      refHost.includes('bing');
      if (!allowed) {
        return new Response('Forbidden: Cross-site hotlinking disallowed', { status: 403 });
      }
    } catch (e) {}
  }

  const upstreamHeaders = new Headers();
  upstreamHeaders.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
  if (targetUrl.includes('melolo') || targetUrl.includes('edgeone.sg')) {
    upstreamHeaders.set('Referer', 'https://melolo.com/');
  }

  const clientRange = request.headers.get('Range');
  if (clientRange) {
    upstreamHeaders.set('Range', clientRange);
  }

  try {
    const upstreamResp = await fetch(targetUrl, {
      method: request.method,
      headers: upstreamHeaders,
      cf: {
        cacheEverything: true,
        cacheTtl: 86400
      }
    });

    // Sanitized Response Headers with Cloaked Sovereign Server Identity
    const respHeaders = new Headers();
    const forwardHeaders = ['content-type', 'content-length', 'content-range', 'accept-ranges', 'etag', 'last-modified'];
    for (const h of forwardHeaders) {
      const val = upstreamResp.headers.get(h);
      if (val) respHeaders.set(h, val);
    }

    respHeaders.set('Server', 'Flowork-Media-Core/2.4 (Sovereign Linux)');
    respHeaders.set('X-Powered-By', 'Flowork OS Stream Engine');
    respHeaders.set('Access-Control-Allow-Origin', '*');
    respHeaders.set('Access-Control-Allow-Headers', 'Range');
    respHeaders.set('Access-Control-Expose-Headers', 'Content-Range, Content-Length, Accept-Ranges');
    if (!respHeaders.has('Content-Type')) {
      respHeaders.set('Content-Type', 'video/mp4');
    }
    if (!respHeaders.has('Accept-Ranges')) {
      respHeaders.set('Accept-Ranges', 'bytes');
    }
    respHeaders.set('Cache-Control', 'public, max-age=86400');

    return new Response(upstreamResp.body, {
      status: upstreamResp.status,
      statusText: upstreamResp.statusText,
      headers: respHeaders
    });
  } catch (err) {
    return new Response(`Upstream fetch error: ${err.message}`, { status: 502 });
  }
}

// Default Cloudflare Pages Worker Export
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 1. Explicit SEO & Crawl Asset Endpoints with strict MIME types
    if (url.pathname === '/robots.txt') {
      const resp = await env.ASSETS.fetch(request);
      return new Response(resp.body, {
        status: resp.status,
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'public, max-age=86400'
        }
      });
    }

    if (url.pathname === '/sitemap.xml') {
      const resp = await env.ASSETS.fetch(request);
      return new Response(resp.body, {
        status: resp.status,
        headers: {
          'Content-Type': 'application/xml; charset=utf-8',
          'Cache-Control': 'public, max-age=86400'
        }
      });
    }

    if (url.pathname === '/llms.txt' || url.pathname === '/llms-full.txt') {
      const resp = await env.ASSETS.fetch(request);
      return new Response(resp.body, {
        status: resp.status,
        headers: {
          'Content-Type': 'text/markdown; charset=utf-8',
          'Cache-Control': 'public, max-age=86400'
        }
      });
    }

    // 2. First-Party Image Caching Proxy (/images/cover & /images/...)
    if (url.pathname.startsWith('/images/')) {
      return handleImageCover(request, env);
    }

    // 3. First-Party Video Stream Proxy (/media/... & /api/stream)
    if (url.pathname.startsWith('/media/') || url.pathname === '/api/stream') {
      return handleMediaStream(request, env);
    }

    // 4. API Endpoints
    if (url.pathname === '/api/browse') {
      return handleBrowse(request, env);
    }
    if (url.pathname === '/api/search') {
      return handleSearch(request, env);
    }
    if (url.pathname === '/api/detail') {
      return handleDetail(request, env);
    }

    // 5. Dynamic SSR HTMLRewriter for Deep Links & Episodic SEO
    const slug = url.searchParams.get('slug') || '';
    const bookId = url.searchParams.get('bookId') || '';
    const epParam = url.searchParams.get('ep') || url.searchParams.get('episode') || '';
    const epNum = epParam ? parseInt(epParam, 10) : 0;
    let provider = url.searchParams.get('provider') || '';

    if (slug || bookId) {
      if (!provider) {
        provider = slug ? 'melolo' : 'dramabox';
      }

      try {
        let drama = null;
        if (provider === 'melolo') {
          const melolo = await getMeloloCatalog(env, request.url);
          drama = melolo.find(d => d.slug === slug || d.bookId === bookId || d.bookId === `melolo_${slug}`);
        } else {
          const dramabox = await getDramaboxCatalog(env, request.url);
          drama = dramabox.find(d => String(d.bookId) === String(bookId));
        }

        if (drama) {
          const dramaTitle = drama.title || drama.bookName || 'Serial Drama';
          const dramaIntro = (drama.intro || drama.synopsis || drama.introduction || `Streaming drama pendek ${dramaTitle} sub Indo full episode gratis tanpa koin di DramaBox & Melolo Web.`).slice(0, 180);
          const rawCover = drama.cover || drama.thumb || 'https://dramaboxflow.pages.dev/icon-512.png';
          const dramaEps = drama.chapterCount || drama.totalEpisodes || drama.episode_count || 50;

          const cleanSlug = (provider === 'melolo') ? (slug || bookId.replace('melolo_', '')) : bookId;
          const maskedCover = `${url.origin}/images/cover?provider=${encodeURIComponent(provider)}&id=${encodeURIComponent(cleanSlug)}&url=${encodeURIComponent(rawCover)}`;
          const cleanCover = `${url.origin}/images/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/cover.jpg`;
          const mediaStreamUrl = `${url.origin}/media/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/${epNum || 1}.mp4`;

          const seriesCanonical = `${url.origin}/?provider=${encodeURIComponent(provider)}&${provider === 'melolo' ? 'slug=' + encodeURIComponent(cleanSlug) : 'bookId=' + encodeURIComponent(bookId)}`;
          
          let pageTitle = `${dramaTitle} Sub Indo Full Episode (1-${dramaEps}) — DramaBox & Melolo Web`;
          let pageDesc = `Nonton streaming drama pendek ${dramaTitle} sub Indo lengkap full episode gratis tanpa koin di DramaBox & Melolo Web. Sinopsis: ${dramaIntro.slice(0, 110)}... Tonton di HP & PC.`;
          let canonical = seriesCanonical;
          let prevLink = null;
          let nextLink = null;
          let dramaSchema = null;

          if (epNum > 0) {
            canonical = `${seriesCanonical}&ep=${epNum}`;
            pageTitle = `Nonton ${dramaTitle} Episode ${epNum} Sub Indo Full HD — DramaBox & Melolo`;
            pageDesc = `Streaming ${dramaTitle} Episode ${epNum} sub Indo gratis tanpa koin di DramaBox & Melolo Web. Tonton kelanjutan Part ${epNum} dari total ${dramaEps} episode dengan kualitas HD tanpa iklan.`;
            if (epNum > 1) {
              prevLink = `${seriesCanonical}&ep=${epNum - 1}`;
            }
            if (epNum < dramaEps) {
              nextLink = `${seriesCanonical}&ep=${epNum + 1}`;
            }

            dramaSchema = {
              "@context": "https://schema.org",
              "@graph": [
                {
                  "@type": "TVEpisode",
                  "@id": `${canonical}#episode`,
                  "url": canonical,
                  "name": `${dramaTitle} - Episode ${epNum}`,
                  "episodeNumber": epNum,
                  "inLanguage": "id-ID",
                  "description": pageDesc,
                  "image": cleanCover,
                  "partOfSeries": {
                    "@type": "TVSeries",
                    "@id": `${seriesCanonical}#series`,
                    "name": dramaTitle,
                    "numberOfEpisodes": dramaEps,
                    "url": seriesCanonical
                  },
                  "partOfSeason": {
                    "@type": "TVSeason",
                    "seasonNumber": 1,
                    "numberOfEpisodes": dramaEps
                  }
                },
                {
                  "@type": "VideoObject",
                  "@id": `${canonical}#video`,
                  "name": pageTitle,
                  "description": pageDesc,
                  "thumbnailUrl": [cleanCover, maskedCover],
                  "uploadDate": "2026-11-14T08:00:00+07:00",
                  "contentUrl": mediaStreamUrl,
                  "embedUrl": canonical,
                  "inLanguage": "id-ID",
                  "partOfSeries": {
                    "@type": "TVSeries",
                    "@id": `${seriesCanonical}#series`,
                    "name": dramaTitle,
                    "url": seriesCanonical
                  }
                },
                {
                  "@type": "BreadcrumbList",
                  "itemListElement": [
                    {
                      "@type": "ListItem",
                      "position": 1,
                      "name": "Beranda",
                      "item": `${url.origin}/`
                    },
                    {
                      "@type": "ListItem",
                      "position": 2,
                      "name": dramaTitle,
                      "item": seriesCanonical
                    },
                    {
                      "@type": "ListItem",
                      "position": 3,
                      "name": `Episode ${epNum}`,
                      "item": canonical
                    }
                  ]
                }
              ]
            };
          } else {
            dramaSchema = {
              "@context": "https://schema.org",
              "@graph": [
                {
                  "@type": "TVSeries",
                  "@id": `${seriesCanonical}#series`,
                  "name": dramaTitle,
                  "description": dramaIntro,
                  "numberOfEpisodes": dramaEps,
                  "image": cleanCover,
                  "inLanguage": "id-ID",
                  "url": seriesCanonical,
                  "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "IDR",
                    "availability": "https://schema.org/InStock"
                  }
                },
                {
                  "@type": "BreadcrumbList",
                  "itemListElement": [
                    {
                      "@type": "ListItem",
                      "position": 1,
                      "name": "Beranda",
                      "item": `${url.origin}/`
                    },
                    {
                      "@type": "ListItem",
                      "position": 2,
                      "name": dramaTitle,
                      "item": seriesCanonical
                    }
                  ]
                }
              ]
            };
          }

          const assetResp = await env.ASSETS.fetch(new URL('/', request.url));
          let rewriter = new HTMLRewriter()
            .on('title', {
              element(e) {
                e.setInnerContent(pageTitle);
              }
            })
            .on('meta[name="description"]', {
              element(e) {
                e.setAttribute('content', pageDesc);
              }
            })
            .on('link[rel="canonical"]', {
              element(e) {
                e.setAttribute('href', canonical);
              }
            })
            .on('meta[property="og:title"]', {
              element(e) {
                e.setAttribute('content', pageTitle);
              }
            })
            .on('meta[property="og:description"]', {
              element(e) {
                e.setAttribute('content', pageDesc);
              }
            })
            .on('meta[property="og:image"]', {
              element(e) {
                e.setAttribute('content', cleanCover);
              }
            })
            .on('meta[property="og:url"]', {
              element(e) {
                e.setAttribute('content', canonical);
              }
            })
            .on('meta[name="twitter:title"]', {
              element(e) {
                e.setAttribute('content', pageTitle);
              }
            })
            .on('meta[name="twitter:description"]', {
              element(e) {
                e.setAttribute('content', pageDesc);
              }
            })
            .on('meta[name="twitter:image"]', {
              element(e) {
                e.setAttribute('content', cleanCover);
              }
            })
            .on('head', {
              element(e) {
                if (prevLink) {
                  e.append(`<link rel="prev" href="${prevLink}">`, { html: true });
                }
                if (nextLink) {
                  e.append(`<link rel="next" href="${nextLink}">`, { html: true });
                }
                if (dramaSchema) {
                  e.append(`<script type="application/ld+json">${JSON.stringify(dramaSchema)}</script>`, { html: true });
                }
              }
            });

          return rewriter.transform(assetResp);
        }
      } catch (err) {
        console.error('SSR Rewriter error:', err);
      }
    }

    // 6. Default Static Asset Delivery
    return env.ASSETS.fetch(request);
  }
};
