/**
 * DramaBox & Melolo Flow - Cloudflare Pages Advanced Mode Edge Worker
 * Consolidated API Router & Edge Video Stream Proxy with HTTP 206 Range Support
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
      cover: '',
      provider: 'melolo',
      introduction: 'Serial drama pendek Melolo HD.'
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
      const series = (data.data && data.data[0]) || {};

      if (series.series_total_episode || series.episode_count) {
        meta.chapterCount = series.series_total_episode || series.episode_count;
      }
      if (series.series_name) meta.bookName = series.series_name;
      if (series.series_cover) meta.cover = series.series_cover;
      if (series.series_desc) meta.introduction = series.series_desc;

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
            mp4: `/api/stream?provider=melolo&slug=${encodeURIComponent(slug)}&ep=${epNum}`,
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
          mp4: `/api/stream?provider=melolo&slug=${encodeURIComponent(slug)}&ep=${i}`,
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

  // DramaBox Goodbos Provider
  let chapters = [];
  try {
    const goodbosUrl = `https://dramabox.goodbos.online/api/dramabox/allepisode?bookId=${encodeURIComponent(bookId)}`;
    const resp = await fetch(goodbosUrl, {
      headers: {
        'x-token': '6EB57533425BC1D78ADA1F80354161D4',
        'User-Agent': 'Mozilla/5.0'
      }
    });
    const data = await resp.json();
    if (Array.isArray(data)) {
      data.forEach((ep, idx) => {
        const mp4 = ep.videoUrl || ep.videoUrl720 || ep.mp4 || '';
        chapters.push({
          id: ep.chapterId || (idx + 1),
          name: ep.chapterName || `Part ${idx + 1}`,
          chapterName: ep.chapterName || `Part ${idx + 1}`,
          index: idx,
          indexStr: `Part ${idx + 1}`,
          mp4: mp4 ? `/api/stream?url=${encodeURIComponent(mp4)}` : '',
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
  const meta = found || {
    bookId,
    bookName: `Drama ${bookId}`,
    category: 'DramaBox',
    chapterCount: chapters.length,
    cover: '',
    provider: 'dramabox',
    introduction: 'Serial drama pendek DramaBox HD.'
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

// 4. /api/stream - Edge Video Streaming Proxy with Range Support
async function handleStream(request, env) {
  const { searchParams } = new URL(request.url);

  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
        'Access-Control-Allow-Headers': 'Range, Content-Type'
      }
    });
  }

  const provider = searchParams.get('provider') || '';
  const slug = searchParams.get('slug') || '';
  const ep = parseInt(searchParams.get('ep') || '1', 10);
  let targetUrl = searchParams.get('url') || '';

  if (provider === 'melolo' && slug) {
    try {
      const now = Date.now();
      const apiUrl = `https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug=${encodeURIComponent(slug)}&pageType=play&episode_id=${ep}&_refresh=${now}`;
      const r = await fetch(apiUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Referer': `https://melolo.com/id/dramas/${slug}`
        }
      });
      const data = await r.json();
      const series = (data.data && data.data[0]) || {};
      for (const item of series.episode_list || []) {
        if (parseInt(item.episode_id || '0', 10) === ep) {
          const u = item.url || '';
          if (u) {
            targetUrl = u.replace(/\\u0026/g, '&');
            break;
          }
        }
      }
    } catch (err) {
      console.error('Error resolving signed URL at edge:', err);
    }
  }

  if (!targetUrl) {
    return new Response('Video URL not resolved', { status: 404 });
  }

  const upstreamHeaders = new Headers();
  upstreamHeaders.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
  upstreamHeaders.set('Referer', 'https://melolo.com/');

  const clientRange = request.headers.get('Range');
  if (clientRange) {
    upstreamHeaders.set('Range', clientRange);
  }

  try {
    const upstreamResp = await fetch(targetUrl, {
      method: request.method,
      headers: upstreamHeaders
    });

    const respHeaders = new Headers();
    const forwardHeaders = ['content-type', 'content-length', 'content-range', 'accept-ranges', 'etag', 'last-modified'];
    for (const h of forwardHeaders) {
      const val = upstreamResp.headers.get(h);
      if (val) respHeaders.set(h, val);
    }

    respHeaders.set('Access-Control-Allow-Origin', '*');
    respHeaders.set('Access-Control-Allow-Headers', 'Range');
    respHeaders.set('Access-Control-Expose-Headers', 'Content-Range, Content-Length, Accept-Ranges');

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

    // Explicit SEO & Crawl Asset Endpoints with strict MIME types
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

    // Core Streaming & Catalog APIs
    if (url.pathname === '/api/browse') {
      return handleBrowse(request, env);
    }
    if (url.pathname === '/api/search') {
      return handleSearch(request, env);
    }
    if (url.pathname === '/api/detail') {
      return handleDetail(request, env);
    }
    if (url.pathname === '/api/stream') {
      return handleStream(request, env);
    }

    // Dynamic Edge SSR SEO Injection for Drama Permalinks
    if (url.pathname === '/' || url.pathname === '/index.html') {
      const provider = url.searchParams.get('provider') || (url.searchParams.has('slug') ? 'melolo' : (url.searchParams.has('bookId') ? 'dramabox' : null));
      const slug = url.searchParams.get('slug');
      const bookId = url.searchParams.get('bookId');
      const epParam = url.searchParams.get('ep') || url.searchParams.get('episode');
      const epNum = epParam ? parseInt(epParam, 10) : 0;

      if (provider && (slug || bookId)) {
        try {
          let drama = null;
          if (provider === 'melolo' && (slug || bookId)) {
            const melolo = await getMeloloCatalog(env, request.url);
            const target = slug || bookId;
            drama = melolo.find(d => d.slug === target || String(d.id) === target || String(d.bookId) === target);
          } else if (provider === 'dramabox' && (bookId || slug)) {
            const dramabox = await getDramaboxCatalog(env, request.url);
            const target = bookId || slug;
            drama = dramabox.find(d => String(d.bookId) === String(target));
          }

          if (drama) {
            const dramaTitle = drama.title || drama.bookName || 'Serial Drama';
            const dramaIntro = (drama.intro || drama.synopsis || drama.introduction || `Streaming drama pendek ${dramaTitle} sub Indo full episode gratis tanpa koin di DramaBox & Melolo Web.`).slice(0, 180);
            const dramaCover = drama.cover || drama.thumb || 'https://dramaboxflow.pages.dev/icon-512.png';
            const dramaEps = drama.chapterCount || drama.totalEpisodes || drama.episode_count || 50;

            const seriesCanonical = `${url.origin}/?provider=${encodeURIComponent(provider)}&${provider === 'melolo' ? 'slug=' + encodeURIComponent(slug || bookId) : 'bookId=' + encodeURIComponent(bookId)}`;
            
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
                    "image": dramaCover,
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
                    "image": dramaCover,
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
                  e.setAttribute('content', dramaCover);
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
                  e.setAttribute('content', dramaCover);
                }
              })
              .on('head', {
                element(e) {
                  if (prevLink) {
                    e.append(`\n  <link rel="prev" href="${prevLink}" />`, { html: true });
                  }
                  if (nextLink) {
                    e.append(`\n  <link rel="next" href="${nextLink}" />`, { html: true });
                  }
                  e.append(`\n  <script type="application/ld+json">${JSON.stringify(dramaSchema)}</script>\n`, { html: true });
                }
              });

            return rewriter.transform(assetResp);
          }
        } catch (err) {
          console.error('SSR metadata injection error:', err);
        }
      }
    }

    // Static assets fallback
    return env.ASSETS.fetch(request);
  }
};
