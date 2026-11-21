import { connect } from 'cloudflare:sockets';

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
    catalog = [...meloloList];
  } else if (provider === 'dramabox') {
    catalog = [...dramaboxList];
  } else {
    catalog = [...meloloList, ...dramaboxList];
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

  // Sort descending: Episode terbanyak ke terkecil (Melolo & DramaBox)
  const getEpCount = (d) => {
    const val = d.chapterCount || d.totalEpisodes || d.episode_count || d.episodeCount || 0;
    return parseInt(val, 10) || 0;
  };

  filtered.sort((a, b) => {
    const diff = getEpCount(b) - getEpCount(a);
    if (diff !== 0) return diff;
    const ratingA = parseFloat(a.ratings || a.rating || 0) || 0;
    const ratingB = parseFloat(b.ratings || b.rating || 0) || 0;
    return ratingB - ratingA;
  });

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
async function handleDetail(request, env, ctx) {
  const { searchParams } = new URL(request.url);
  let bookId = searchParams.get('bookId') || '';
  const provider = (searchParams.get('provider') || '').toLowerCase();

  if (!bookId) {
    return new Response(JSON.stringify({ status: 'error', message: 'bookId required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  // Melolo Provider
  const isMelolo = bookId.startsWith('melolo_') || provider === 'melolo';
  const cache = caches.default;
  const cacheKey = new Request(request.url, { method: 'GET' });

  // Melolo has stable static URLs safe for 7-day edge caching
  if (isMelolo) {
    const cachedResp = await cache.match(cacheKey);
    if (cachedResp) {
      return cachedResp;
    }
  }
  if (isMelolo) {
    const slug = bookId.replace(/^melolo_/, '');
    const canonicalBookId = `melolo_${slug}`;
    let meta = {
      bookId: canonicalBookId,
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

      const totalEpCount = parseInt(
        series.episode_num || series.series_total_episode || series.episode_count || meta.chapterCount || 0,
        10
      );
      if (totalEpCount > 0) {
        meta.chapterCount = totalEpCount;
      }
      if (series.series_name) meta.bookName = series.series_name;
      if (series.series_cover || series.cover_url) {
        meta.cover = `/images/cover?provider=melolo&id=${encodeURIComponent(slug)}&url=${encodeURIComponent(series.series_cover || series.cover_url)}`;
      }
      if (series.series_desc || series.desc) meta.introduction = series.series_desc || series.desc;
      if (series.supplier) meta.supplier = series.supplier;

      const epList = series.episode_list || [];
      const seenEps = new Set();
      for (const item of epList) {
        const epNum = parseInt(item.episode_id || item.episode_number || '0', 10);
        if (epNum > 0 && !seenEps.has(epNum)) {
          seenEps.add(epNum);
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

      // Generate all remaining chapters up to total count so all episodes are accessible
      const targetCount = Math.max(meta.chapterCount || 0, chapters.length);
      if (targetCount > chapters.length) {
        for (let i = 1; i <= targetCount; i++) {
          if (!seenEps.has(i)) {
            seenEps.add(i);
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
      }
      chapters.sort((a, b) => a.id - b.id);
      meta.chapterCount = chapters.length;
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

    const detailResp = new Response(JSON.stringify({
      status: 'success',
      bookInfo: meta,
      chapterList: chapters,
      provider: 'melolo'
    }), {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'public, max-age=86400, s-maxage=604800',
        'Access-Control-Allow-Origin': '*'
      }
    });

    if (ctx && ctx.waitUntil && chapters.length > 0) {
      ctx.waitUntil(cache.put(cacheKey, detailResp.clone()));
    }
    return detailResp;
  }

  // DramaBox Provider
  let chapters = [];
  let officialMeta = null;

  try {
    const officialData = await fetchDramaboxOfficialData(bookId);
    if (officialData) {
      officialMeta = officialData.bookInfo || null;
      if (Array.isArray(officialData.chapterList) && officialData.chapterList.length > 0) {
        officialData.chapterList.forEach((ep, idx) => {
          const epNum = idx + 1;
          const hasMp4 = Boolean(ep.mp4);
          const isUnlocked = true;
          chapters.push({
            id: ep.id || epNum,
            name: ep.name || `Part ${epNum}`,
            chapterName: ep.name || `Part ${epNum}`,
            index: idx,
            indexStr: ep.indexStr || `Part ${epNum}`,
            mp4: ep.mp4 || `/media/dramabox/${encodeURIComponent(bookId)}/${epNum}.mp4`,
            directMp4: ep.mp4 || null,
            unlock: true,
            duration: ep.duration ? Math.round(ep.duration / 1000) : 0,
            cover: ep.cover || '',
            provider: 'dramabox'
          });
        });
      }
    }
  } catch (err) {
    console.error('Error fetching DramaBox official data:', err);
  }

  // Autonomous DramaBox Batch API fallback if officialData returned 0 chapters
  if (chapters.length === 0) {
    try {
      const batchData = await fetchDramaboxBatchLoad(bookId, -1, 0);
      if (batchData && Array.isArray(batchData.chapterList) && batchData.chapterList.length > 0) {
        if (!officialMeta && batchData.bookName) {
          officialMeta = {
            bookName: batchData.bookName,
            introduction: batchData.introduction,
            cover: batchData.bookCover
          };
        }
        batchData.chapterList.forEach((ep, idx) => {
          const epNum = (ep.chapterIndex !== undefined ? ep.chapterIndex + 1 : idx + 1);
          const cdn = ep.cdnList && ep.cdnList[0];
          const vpath = cdn?.videoPathList?.[0]?.videoPath || cdn?.videoPath || cdn?.url || null;
          chapters.push({
            id: ep.chapterId || epNum,
            name: ep.chapterName || `Part ${epNum}`,
            chapterName: ep.chapterName || `Part ${epNum}`,
            index: ep.chapterIndex !== undefined ? ep.chapterIndex : idx,
            indexStr: `Part ${epNum}`,
            mp4: `/media/dramabox/${encodeURIComponent(bookId)}/${epNum}.mp4`,
            directMp4: vpath,
            unlock: true,
            provider: 'dramabox'
          });
        });
      }
    } catch (bErr) {
      console.warn('Error fetching DramaBox autonomous batch in handleDetail:', bErr);
    }
  }

  const dramaboxList = await getDramaboxCatalog(env, request.url);
  const found = dramaboxList.find(d => String(d.bookId) === String(bookId));

  // Fallback: If official/batch return 0 chapters, generate chapters from catalog chapterCount so 100+ part dramas are fully navigable
  if (chapters.length === 0 && found && found.chapterCount) {
    const totalCount = found.chapterCount || 80;
    for (let i = 1; i <= totalCount; i++) {
      chapters.push({
        id: i,
        name: `Part ${i}`,
        chapterName: `Part ${i}`,
        index: i - 1,
        indexStr: `Part ${i}`,
        mp4: `/media/dramabox/${encodeURIComponent(bookId)}/${i}.mp4`,
        directMp4: null,
        unlock: true,
        provider: 'dramabox'
      });
    }
  }

  const meta = {
    ...(found || {}),
    ...(officialMeta || {}),
    bookId,
    bookName: (officialMeta && officialMeta.bookName) || (found && found.bookName) || `Drama ${bookId}`,
    introduction: (officialMeta && officialMeta.introduction) || (found && found.introduction) || 'Serial drama pendek DramaBox HD sub Indo.',
    chapterCount: chapters.length || (found && found.chapterCount) || 80,
    cover: (found && found.cover) ? `/images/cover?provider=dramabox&id=${encodeURIComponent(bookId)}&url=${encodeURIComponent(found.cover)}` :
           (officialMeta && officialMeta.cover) ? `/images/cover?provider=dramabox&id=${encodeURIComponent(bookId)}&url=${encodeURIComponent(officialMeta.cover)}` :
           `/images/dramabox/${encodeURIComponent(bookId)}/cover.jpg`,
    provider: 'dramabox'
  };

  const detailResp = new Response(JSON.stringify({
    status: 'success',
    bookInfo: meta,
    chapterList: chapters,
    provider: 'dramabox'
  }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=1800, s-maxage=3600',
      'Access-Control-Allow-Origin': '*'
    }
  });

  if (ctx && ctx.waitUntil && chapters.length > 0) {
    ctx.waitUntil(cache.put(cacheKey, detailResp.clone()));
  }
  return detailResp;
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
    if (resp.ok) {
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

      // If supplier is DramaBox and episode wasn't in Melolo, fallback to DramaBox scraper
      if (series.supplier === 'dramabox' && series.series_name) {
        try {
          const dbData = await fetchDramaboxOfficialData(cleanSlug);
          if (dbData && dbData.chapterList) {
            const target = dbData.chapterList.find(c => (c.index + 1) === epNum || c.id == epNum);
            if (target && target.mp4) return target.mp4;
          }
        } catch (dbErr) {
          console.warn('Melolo supplier dramabox fallback error:', dbErr);
        }
      }

      // Graceful fallback to latest available signed episode if requested episode exceeds third-party preview
      if (epList.length > 0) {
        const lastEpNum = parseInt(epList[epList.length - 1].episode_id || epList.length, 10);
        if (lastEpNum > 0 && lastEpNum !== epNum) {
          const fallbackApiUrl = `https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug=${encodeURIComponent(cleanSlug)}&pageType=play&episode_id=${lastEpNum}&_refresh=${now}`;
          try {
            const fbResp = await fetch(fallbackApiUrl, {
              headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': `https://melolo.com/id/dramas/${cleanSlug}`
              }
            });
            if (fbResp.ok) {
              const fbData = await fbResp.json();
              const fbSeries = (fbData.data && fbData.data[0]) || fbData.series || {};
              for (const item of (fbSeries.episode_list || [])) {
                if (parseInt(item.episode_id || '0', 10) === lastEpNum) {
                  const u = item.url || '';
                  if (u) return u.replace(/\\u0026/g, '&');
                }
              }
            }
          } catch (fbErr) {
            console.warn('Fallback signed episode error:', fbErr);
          }
        }
        const last = epList[epList.length - 1];
        if (last && last.url) {
          return last.url.replace(/\\u0026/g, '&');
        }
      }
    }
  } catch (e) {
    console.error('resolveMeloloEpisodeUrl error:', e);
  }
  return null;
}

// ==========================================
// DRAMABOX AUTONOMOUS TOKEN & BATCH ENGINE
// ==========================================
const DB_JWK = {
  kty: 'RSA',
  n: 'vUOGOUF-Y9PB6522N4q3ynZBJZQFNjjkZwI5Vw8gs3JtmemUaxr7U2VADHpX1OT1kulxhJt3eJCRCm14uAq5fKNhPxN2CT5NZUA9XdCU3a72ZXhEzdVYh2RUkMEty_eFqIdBN0z3m2hGKvPHhMbyrtbQ3Y0qBYwW4DHs8kp2rOTXNsRdvF4T7gvJtebvnXnLbKyZfgCxnEw19y79xVEbsFf3Te1jBJIHLHiClTHScc1AdD3kqgjX7X8ZnQVf1OMlxUcT4Z0hUlwq5I-riY4nJImKtaUNWmX60HtXiw9zAdoSqu3K4THAN5KYIEJZ5stcEUeAQLbZklOHz2_8hfA94Q',
  e: 'AQAB',
  d: 'l2u7qnlEtneH8YsXau53xuq_imIXnV79FZDI8WcwAYGuQHKJhPtsUjdye8kyFiksdGKCqNZ9Sh9Xe2FEMPKbniVUu1NFn3WSFEzGDBXB1G6TwXDsk0V6c7AInFuB2WrqK4Ay5ByXCWXupZSubwOAy_Mf3fF_yjpfXvVynhKHSiDVFrsT0Znft3MGVfZokErxUF9y1me24M_HnZ7vWdp-p9uNfFm4S2m73agl3oD2ZZt3QFlOTvZkdSYNwpyqN9wQfX1JY6mEwkViTFTkVGggSvf_OKzJM7gy3fdmbAQs6tj092XIADJ53tmgf6GVOvtzTblBE69vYuaqBGJRPnq0wQ',
  p: '-jH5m6iMRK6XjiBhSUnlr3DzRybwlQrtIj5sZprWe2my5uYHG3jbViYIO7GtQvMTnDrBCxNhuM6dPrL0cRnbsp_iBMXe3pyjT_aWveBkn4R-UpBsnbtDn28r1MZpCDtr5UNc0TPj4KFJvjnV_e8oGoyYEroECqcw1LqNOGDiLhk',
  q: 'waemNePYrXW-MVX_hatfLQ96tpxwf7yuHdENZ2q5AFw73GJWYvC8VY-TcoKPAmeoCUMltI3TrS6K5Q_GoLd5K2BsoJrSxQNQFd3ehWAtdOuPDvQ5rn_2fsvgvc3rOvJh7uNnwEZCI_45WQg-UFWref4PPc-ArNtp9Xj2y7Lndwk',
  dp: 'EaIyEHl5oWGYxuibUroFmS7hxpMFA8woWHCD3VtuYHZbqJBv0czb0J-Plv13068kI6-0aV5tVcQiKwgb2FjVNiq0mFeF1LS_geRETY-iJ-gDqzgIn7lSE8uXEEEHqA_gE-GCijAZEHztoJ2c6m_PqMdd9Hvtyv5rn6KiT2Xsqwk',
  dq: 'LZ-huPCFC9jBhj4MhSFquuL6tisFFhMNslieH8805rDUKYfBcm3k8QNyaXf42UgyfnwjVfZT-GkOsAiXcyXGlkGRVgUjwuaU55Ht6t5N103n1k4TiNj86cJ-oDjzQl_4Up-gwdvLmU87k44toB-O1p7UWGualR7cR8jH3BW6EoE',
  qi: '8XMcpBlsaGSqbI9bZy1MQhYt1QfI7ft-bx2PVaM3jCNEAjiiE2IpAlGHdATXUTU_MFOX2VlVZPxC0SxKOesD-2kavfvx9xRPtYYGBOYFFoCe_U_Wf9OnRNK-HlekiGEy7FyK0iCuFgwgbcZs_0k0BqvE7-o9boaLTFZoXuKXs6s',
  key_ops: ['sign'],
  ext: true
};

let globalSubtleKey = null;
let globalDramaboxTokenCache = null;
let globalLastBootstrapDiag = null;

async function getDramaboxSubtleKey() {
  if (globalSubtleKey) return globalSubtleKey;
  globalSubtleKey = await crypto.subtle.importKey(
    'jwk',
    DB_JWK,
    { name: 'RSASSA-PKCS1-v1_5', hash: { name: 'SHA-256' } },
    false,
    ['sign']
  );
  return globalSubtleKey;
}

async function signDramaboxPayload(str) {
  const key = await getDramaboxSubtleKey();
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const sig = await crypto.subtle.sign({ name: 'RSASSA-PKCS1-v1_5' }, key, data);
  const sigBytes = new Uint8Array(sig);
  let binary = '';
  for (let i = 0; i < sigBytes.length; i++) {
    binary += String.fromCharCode(sigBytes[i]);
  }
  return btoa(binary);
}

function generateRandomHex(len) {
  const bytes = new Uint8Array(len);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

const EGRESS_PROXIES = [
  { host: '188.166.178.163', port: 3129 },
  { host: '103.237.102.191', port: 11111 }
];

async function fetchViaConnectProxy(targetUrl, options = {}, proxyHost, proxyPort) {
  const debug = [];
  const urlObj = new URL(targetUrl);
  const targetHost = urlObj.hostname;
  const targetPort = urlObj.port ? parseInt(urlObj.port, 10) : (urlObj.protocol === 'https:' ? 443 : 80);

  debug.push(`1. Connecting to ${proxyHost}:${proxyPort}`);
  const socket = connect({ hostname: proxyHost, port: proxyPort }, { secureTransport: 'starttls' });
  const writer = socket.writable.getWriter();
  const reader = socket.readable.getReader();

  try {
    // 2. Send HTTP CONNECT tunnel request
    const connectReq = `CONNECT ${targetHost}:${targetPort} HTTP/1.1\r\nHost: ${targetHost}:${targetPort}\r\nProxy-Connection: Keep-Alive\r\n\r\n`;
    await writer.write(new TextEncoder().encode(connectReq));
    debug.push(`2. CONNECT sent`);

    // 3. Read HTTP/1.1 200 response from proxy
    let connectBuffer = '';
    const decoder = new TextDecoder();
    while (!connectBuffer.includes('\r\n\r\n')) {
      const { value, done } = await reader.read();
      if (done) throw new Error('Proxy closed connection unexpectedly during CONNECT');
      connectBuffer += decoder.decode(value, { stream: true });
    }

    const firstLine = connectBuffer.split('\r\n')[0] || '';
    debug.push(`3. Proxy response: ${firstLine}`);
    if (!firstLine.includes('200')) {
      throw new Error(`Proxy CONNECT failed: ${firstLine}`);
    }

    // Release locks before TLS upgrade
    reader.releaseLock();
    writer.releaseLock();

    // 4. Upgrade to TLS
    debug.push(`4. Starting TLS with expectedServerHostname: ${targetHost}`);
    const tlsRet = socket.startTls({ expectedServerHostname: targetHost });
    debug.push(`4b. tlsRet: ${typeof tlsRet}, isPromise: ${tlsRet instanceof Promise}, isSame: ${tlsRet === socket}`);
    const tlsSocket = (tlsRet instanceof Promise) ? await tlsRet : tlsRet;
    tlsSocket.closed.catch(err => {
      debug.push(`TLS closed error: ${err?.message || err}`);
    });
    const tlsWriter = tlsSocket.writable.getWriter();
    const tlsReader = tlsSocket.readable.getReader();

    try {
      // 5. Construct and send HTTP/1.1 request over TLS tunnel
      const method = options.method || 'GET';
      const path = urlObj.pathname + urlObj.search;
      let rawReq = `${method} ${path} HTTP/1.1\r\nHost: ${targetHost}\r\nUser-Agent: okhttp/4.9.3\r\nConnection: close\r\n`;

      const headers = options.headers || {};
      for (const [k, v] of Object.entries(headers)) {
        if (k.toLowerCase() === 'host' || k.toLowerCase() === 'connection' || k.toLowerCase() === 'user-agent') continue;
        rawReq += `${k}: ${v}\r\n`;
      }

      if (options.body) {
        const bodyBytes = typeof options.body === 'string' ? new TextEncoder().encode(options.body) : options.body;
        rawReq += `Content-Length: ${bodyBytes.byteLength}\r\n\r\n`;
        await tlsWriter.write(new TextEncoder().encode(rawReq));
        await tlsWriter.write(bodyBytes);
      } else {
        rawReq += `\r\n`;
        await tlsWriter.write(new TextEncoder().encode(rawReq));
      }
      debug.push(`5. HTTP request sent over TLS (${rawReq.length} chars)`);

      // 6. Read response chunks until connection close
      const chunks = [];
      let totalLen = 0;
      while (true) {
        const { value, done } = await tlsReader.read();
        if (done) {
          debug.push(`6. Reader done, total bytes: ${totalLen}`);
          break;
        }
        if (value) {
          chunks.push(value);
          totalLen += value.length;
        }
      }

      const merged = new Uint8Array(totalLen);
      let offset = 0;
      for (const ch of chunks) {
        merged.set(ch, offset);
        offset += ch.length;
      }

      const fullText = new TextDecoder().decode(merged);
      const headerEnd = fullText.indexOf('\r\n\r\n');
      debug.push(`7. Decoded text length: ${fullText.length}, headerEnd: ${headerEnd}`);

      if (headerEnd === -1) {
        return { status: 500, text: fullText, json: null, proxy: `${proxyHost}:${proxyPort}`, debug };
      }

      const headPart = fullText.substring(0, headerEnd);
      const bodyPart = fullText.substring(headerEnd + 4);
      const statusLine = headPart.split('\r\n')[0] || '';
      const statusMatch = statusLine.match(/HTTP\/\S+\s+(\d+)/);
      const statusCode = statusMatch ? parseInt(statusMatch[1], 10) : 200;

      let parsedJson = null;
      try {
        parsedJson = JSON.parse(bodyPart);
      } catch (e) {}

      return {
        status: statusCode,
        statusText: statusLine,
        text: bodyPart,
        json: parsedJson,
        proxy: `${proxyHost}:${proxyPort}`,
        debug
      };
    } finally {
      try { tlsReader.releaseLock(); } catch(e) {}
      try { tlsWriter.releaseLock(); } catch(e) {}
      try { tlsSocket.close(); } catch(e) {}
    }
  } catch (err) {
    try { reader.releaseLock(); } catch(e) {}
    try { writer.releaseLock(); } catch(e) {}
    try { socket.close(); } catch(e) {}
    err.debug = debug;
    throw err;
  }
}

async function getOrGenerateDramaboxToken(forceRefresh = false) {
  const now = Date.now();
  if (!forceRefresh && globalDramaboxTokenCache && globalDramaboxTokenCache.expiresAt > now) {
    return globalDramaboxTokenCache;
  }

  const timestamp = String(now);
  const deviceId = crypto.randomUUID();
  const androidId = 'ffffffff' + generateRandomHex(4) + '000000000';
  const body = JSON.stringify({ distinctId: null });

  const toSign = `timestamp=${timestamp}${body}${deviceId}${androidId}`;
  const sn = await signDramaboxPayload(toSign);

  const headers = {
    'User-Agent': 'okhttp/4.9.3',
    'tn': '',
    'version': '470',
    'vn': '4.7.0',
    'cid': 'DAUAF1064291',
    'package-Name': 'com.storymatrix.drama',
    'Apn': '1',
    'device-id': deviceId,
    'language': 'in',
    'current-Language': 'in',
    'p': '48',
    'Time-Zone': '+0700',
    'md': 'Redmi Note 8',
    'ov': '9',
    'over-flow': 'new-fly',
    'android-id': androidId,
    'mf': 'XIAOMI',
    'brand': 'Xiaomi',
    'Content-Type': 'application/json; charset=UTF-8',
    'sn': sn
  };

  const diagList = [];
  const hosts = [
    'api.dramaboxapp.com',
    'api.dramaboxdb.com',
    'sapi.dramaboxapp.com',
    'sapih3.dramaboxdb.com',
    'sapi.dramaboxdb.com',
    'sapih3.dramaboxvideo.com'
  ];
  for (const host of hosts) {
    try {
      const resp = await fetch(`https://${host}/drama-box/ap001/bootstrap?timestamp=${timestamp}`, {
        method: 'POST',
        headers,
        body
      });
      const txt = await resp.text();
      let json = null;
      try { json = JSON.parse(txt); } catch(e) {}
      const user = json?.data?.user;
      if (resp.ok && user && user.token) {
        globalDramaboxTokenCache = {
          token: user.token,
          uid: user.uid,
          deviceId,
          androidId,
          expiresAt: now + (12 * 3600 * 1000)
        };
        globalLastBootstrapDiag = [{ host, status: resp.status, success: true }];
        return globalDramaboxTokenCache;
      }
      diagList.push({ host, status: resp.status, message: json?.message || (txt.length > 100 ? txt.substring(0, 100) : txt) });
    } catch (e) {
      diagList.push({ host, error: e.message });
    }
  }

  // If direct fetch was blocked by Akamai (403 on Cloudflare Datacenter AS13335),
  // route through our non-datacenter TCP CONNECT egress pool
  for (const p of EGRESS_PROXIES) {
    try {
      const pUrl = `https://sapi.dramaboxapp.com/drama-box/ap001/bootstrap?timestamp=${timestamp}`;
      const pResp = await fetchViaConnectProxy(pUrl, { method: 'POST', headers, body }, p.host, p.port);
      const user = pResp.json?.data?.user;
      if (user && user.token) {
        globalDramaboxTokenCache = {
          token: user.token,
          uid: user.uid,
          deviceId,
          androidId,
          expiresAt: now + (12 * 3600 * 1000)
        };
        globalLastBootstrapDiag = [{ host: 'sapi.dramaboxapp.com', proxy: `${p.host}:${p.port}`, status: pResp.status, success: true }];
        return globalDramaboxTokenCache;
      }
      diagList.push({ host: 'sapi.dramaboxapp.com', proxy: `${p.host}:${p.port}`, status: pResp.status, message: pResp.text?.substring(0, 80) });
    } catch (err) {
      diagList.push({ host: 'sapi.dramaboxapp.com', proxy: `${p.host}:${p.port}`, error: err.message });
    }
  }

  globalLastBootstrapDiag = diagList;
  return null;
}

async function fetchDramaboxBatchLoad(bookId, comingPlaySectionId = -1, index = 0) {
  let session = await getOrGenerateDramaboxToken();
  if (!session) return null;

  const doRequest = async (sess) => {
    const timestamp = String(Date.now());
    const bodyObj = {
      boundaryIndex: 0,
      comingPlaySectionId: comingPlaySectionId,
      index: index,
      currencyPlaySource: 'discover_new_rec_new',
      needEndRecommend: 0,
      currencyPlaySourceName: '',
      preLoad: false,
      rid: '',
      pullCid: '',
      loadDirection: 0,
      startUpKey: '',
      bookId: String(bookId).trim()
    };
    const body = JSON.stringify(bodyObj);
    const toSign = `timestamp=${timestamp}${body}${sess.deviceId}${sess.androidId}Bearer ${sess.token}`;
    const sn = await signDramaboxPayload(toSign);

    const headers = {
      'User-Agent': 'okhttp/4.9.3',
      'tn': `Bearer ${sess.token}`,
      'version': '470',
      'vn': '4.7.0',
      'cid': 'DAUAF1064291',
      'package-Name': 'com.storymatrix.drama',
      'Apn': '1',
      'device-id': sess.deviceId,
      'language': 'in',
      'current-Language': 'in',
      'p': '48',
      'Time-Zone': '+0700',
      'md': 'Redmi Note 8',
      'ov': '9',
      'over-flow': 'new-fly',
      'android-id': sess.androidId,
      'mf': 'XIAOMI',
      'brand': 'Xiaomi',
      'Content-Type': 'application/json; charset=UTF-8',
      'sn': sn
    };

    const hosts = [
      'api.dramaboxapp.com',
      'api.dramaboxdb.com',
      'sapi.dramaboxapp.com',
      'sapih3.dramaboxdb.com',
      'sapi.dramaboxdb.com'
    ];
    for (const host of hosts) {
      try {
        const resp = await fetch(`https://${host}/drama-box/chapterv2/batch/load?timestamp=${timestamp}`, {
          method: 'POST',
          headers,
          body
        });
        if (resp.ok) {
          const json = await resp.json();
          if (json.status === 0 && json.data) {
            return json.data;
          }
        }
      } catch (err) {
        console.warn(`Batch load failed on ${host}:`, err);
      }
    }

    // Direct host loop failed -> Try through egress proxy pool
    for (const p of EGRESS_PROXIES) {
      try {
        const pUrl = `https://sapi.dramaboxapp.com/drama-box/chapterv2/batch/load?timestamp=${timestamp}`;
        const pResp = await fetchViaConnectProxy(pUrl, { method: 'POST', headers, body }, p.host, p.port);
        if (pResp.json && pResp.json.status === 0 && pResp.json.data) {
          return pResp.json.data;
        }
      } catch (err) {
        console.warn(`Proxy batch load failed on ${p.host}:${p.port}:`, err.message);
      }
    }

    return null;
  };

  let res = await doRequest(session);
  if (!res) {
    session = await getOrGenerateDramaboxToken(true);
    if (session) {
      res = await doRequest(session);
    }
  }
  return res;
}

// Official DramaBox SSR Next.js Data Scraper
async function fetchDramaboxOfficialData(bookId) {
  try {
    const cleanId = String(bookId).trim();
    if (!cleanId) return null;
    const bucket = Math.floor(Date.now() / 600000);
    const url = `https://www.dramabox.com/drama/${encodeURIComponent(cleanId)}?_b=${bucket}`;
    const resp = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
      },
      redirect: 'follow'
    });
    if (!resp.ok) return null;
    const html = await resp.text();
    const match = html.match(/<script id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);
    if (!match) return null;
    const data = JSON.parse(match[1]);
    return data?.props?.pageProps || null;
  } catch (e) {
    console.error('fetchDramaboxOfficialData error:', e);
    return null;
  }
}

async function resolveDramaboxEpisodeUrl(bookId, epNum, env, requestUrl) {
  // 1. Primary: Autonomous DramaBox Stream Resolver Microservice (Vercel Cloud Egress)
  try {
    const resolverUrl = `https://dramabox-resolver.vercel.app/api/stream?bookId=${encodeURIComponent(bookId)}&ep=${encodeURIComponent(epNum)}&redirect=false`;
    const resp = await fetch(resolverUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      },
      cf: {
        cacheEverything: true,
        cacheTtl: 1800 // Cache resolved stream URL for 30 minutes at Cloudflare Edge
      }
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.success && data.streamUrl) {
        return data.streamUrl;
      }
    }
  } catch (e) {
    console.warn('resolveDramaboxEpisodeUrl vercel resolver error:', e);
  }

  // 2. Secondary: Official DramaBox Web CDN Stream
  try {
    const officialData = await fetchDramaboxOfficialData(bookId);
    if (officialData && Array.isArray(officialData.chapterList)) {
      const idx = epNum - 1;
      const target = officialData.chapterList[idx] ||
                     officialData.chapterList.find(c => (c.index + 1) === epNum || c.id == epNum);
      if (target && target.mp4) {
        return target.mp4;
      }
    }
  } catch (e) {
    console.error('resolveDramaboxEpisodeUrl official error:', e);
  }

  // 3. Fallback: Internal Batch Load (in case host is not blocked)
  try {
    const targetIdx = epNum - 1;
    const batchData = await fetchDramaboxBatchLoad(bookId, -1, targetIdx);
    if (batchData && Array.isArray(batchData.chapterList)) {
      const target = batchData.chapterList.find(c => 
        (c.chapterIndex !== undefined && (c.chapterIndex + 1) === epNum) || 
        (c.chapterNumber !== undefined && c.chapterNumber === epNum) || 
        String(c.chapterId) === String(epNum) ||
        (c.chapterName && (
          c.chapterName === `EP ${epNum}` || 
          c.chapterName === `EP${epNum}` || 
          new RegExp(`\\b${epNum}\\b`).test(c.chapterName)
        ))
      ) || (targetIdx < batchData.chapterList.length ? batchData.chapterList[targetIdx] : batchData.chapterList[0]);

      if (target && Array.isArray(target.cdnList) && target.cdnList.length > 0) {
        for (const cdn of target.cdnList) {
          if (Array.isArray(cdn.videoPathList) && cdn.videoPathList.length > 0) {
            // Pick highest quality (1080p -> 720p -> 540p)
            const sortedQuality = [...cdn.videoPathList].sort((a, b) => (b.quality || 0) - (a.quality || 0));
            const best = sortedQuality.find(v => v.videoPath);
            if (best && best.videoPath) {
              return best.videoPath;
            }
          }
          if (cdn.videoPath) return cdn.videoPath;
          if (cdn.url) return cdn.url;
        }
      }
    }
  } catch (e) {
    console.warn('resolveDramaboxEpisodeUrl batch error:', e);
  }

  // 2. Secondary: Official DramaBox Web CDN Stream
  try {
    const officialData = await fetchDramaboxOfficialData(bookId);
    if (officialData && Array.isArray(officialData.chapterList)) {
      const idx = epNum - 1;
      const target = officialData.chapterList[idx] ||
                     officialData.chapterList.find(c => (c.index + 1) === epNum || c.id == epNum);
      if (target && target.mp4) {
        return target.mp4;
      }
    }
  } catch (e) {
    console.error('resolveDramaboxEpisodeUrl official error:', e);
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

  // DramaBox CDN streams are hosted on CloudFront which blocks Cloudflare datacenter egress,
  // but serves end-user residential/mobile browsers directly with 24h signed URLs.
  // Returning 302 redirect allows browser to stream directly with native byte-range support.
  if (provider === 'dramabox' || targetUrl.includes('dramaboxdb.com') || targetUrl.includes('dramaboxapp.com') || targetUrl.includes('dramaboxvideo.com')) {
    return new Response(null, {
      status: 302,
      headers: {
        'Location': targetUrl,
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
        'Access-Control-Allow-Headers': 'Range, Content-Type, Origin, Accept',
        'Access-Control-Expose-Headers': 'Content-Range, Content-Length, Accept-Ranges',
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=3600'
      }
    });
  }

  // Stream Proxy: Melolo streams require Referer: https://melolo.com/ and are proxied with byte-range masking

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
  async fetch(request, env, ctx) {
    try {
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
      return handleDetail(request, env, ctx);
    }
    if (url.pathname === '/api/dramabox/token-status' || url.pathname === '/api/dramabox/token') {
      const force = url.searchParams.get('refresh') === '1' || url.searchParams.get('force') === 'true';
      const session = await getOrGenerateDramaboxToken(force);
      return new Response(JSON.stringify({
        success: Boolean(session),
        token: session ? (session.token.substring(0, 15) + '...' + session.token.slice(-10)) : null,
        uid: session?.uid || null,
        deviceId: session?.deviceId || null,
        expiresAt: session?.expiresAt || null,
        remainingMinutes: session?.expiresAt ? Math.round((session.expiresAt - Date.now()) / 60000) : 0,
        diagnostic: globalLastBootstrapDiag,
        provider: 'dramabox-autonomous-v1'
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    // 5. Legacy Query Parameter 301 Redirect to SEO .html URL
    const qSlug = url.searchParams.get('slug') || '';
    const qBookId = url.searchParams.get('bookId') || '';
    const qEp = url.searchParams.get('ep') || url.searchParams.get('episode') || '';
    let qProvider = (url.searchParams.get('provider') || (qSlug ? 'melolo' : 'dramabox')).toLowerCase();

    if (qSlug || qBookId) {
      const targetSlug = (qProvider === 'melolo') ? (qSlug || qBookId.replace('melolo_', '')) : qBookId;
      const targetEp = qEp ? parseInt(qEp, 10) : 0;
      const cleanRedirectUrl = targetEp > 0
        ? `${url.origin}/${encodeURIComponent(qProvider)}/${encodeURIComponent(targetSlug)}/episode-${targetEp}.html`
        : `${url.origin}/${encodeURIComponent(qProvider)}/${encodeURIComponent(targetSlug)}.html`;
      return Response.redirect(cleanRedirectUrl, 301);
    }

    // 6. Dynamic SSR HTMLRewriter for Clean SEO .html URLs
    let parsedProvider = '';
    let parsedSlug = '';
    let epNum = 0;

    let cleanPath = url.pathname.replace(/^\/(?:watch|nonton|drama)\//i, '/');

    // Pattern 1: /:provider/:slug/episode-:ep.html or /:provider/:slug/:ep.html
    let m = cleanPath.match(/^\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+?)\/(?:episode-|ep-)?([0-9]+)\.html$/i);
    if (m && !['sitemap', 'robots', 'api', 'images', 'media', 'index'].includes(m[1].toLowerCase())) {
      parsedProvider = m[1].toLowerCase();
      parsedSlug = decodeURIComponent(m[2]);
      epNum = parseInt(m[3], 10);
    } else {
      // Pattern 2: /:provider/:slug-episode-:ep.html
      m = cleanPath.match(/^\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+?)-(?:episode|ep)-([0-9]+)\.html$/i);
      if (m && !['sitemap', 'robots', 'api', 'images', 'media', 'index'].includes(m[1].toLowerCase())) {
        parsedProvider = m[1].toLowerCase();
        parsedSlug = decodeURIComponent(m[2]);
        epNum = parseInt(m[3], 10);
      } else {
        // Pattern 3: /:provider/:slug.html
        m = cleanPath.match(/^\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+?)\.html$/i);
        if (m && !['sitemap', 'robots', 'api', 'images', 'media', 'index'].includes(m[1].toLowerCase())) {
          if (!['melolo', 'dramabox'].includes(m[2].toLowerCase())) {
            parsedProvider = m[1].toLowerCase();
            parsedSlug = decodeURIComponent(m[2]);
            epNum = 0; // Series overview
          }
        }
      }
    }

    if (parsedSlug) {
      const provider = parsedProvider || 'melolo';
      const slug = parsedSlug;
      const bookId = parsedSlug;

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
          const rawCover = drama.cover || drama.thumb || 'https://dramapendek.asia/icon-512.png';
          const dramaEps = drama.chapterCount || drama.totalEpisodes || drama.episode_count || 50;

          const cleanSlug = (provider === 'melolo') ? (slug || bookId.replace('melolo_', '')) : bookId;
          const maskedCover = `${url.origin}/images/cover?provider=${encodeURIComponent(provider)}&id=${encodeURIComponent(cleanSlug)}&url=${encodeURIComponent(rawCover)}`;
          const cleanCover = `${url.origin}/images/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/cover.jpg`;
          const mediaStreamUrl = `${url.origin}/media/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/${epNum || 1}.mp4`;

          const seriesCanonical = `${url.origin}/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}.html`;
          
          let pageTitle = `${dramaTitle} Sub Indo Full Episode (1-${dramaEps}) — DramaBox & Melolo Web`;
          let pageDesc = `Nonton streaming drama pendek ${dramaTitle} sub Indo lengkap full episode gratis tanpa koin di DramaBox & Melolo Web. Sinopsis: ${dramaIntro.slice(0, 110)}... Tonton di HP & PC.`;
          let canonical = seriesCanonical;
          let prevLink = null;
          let nextLink = null;
          let dramaSchema = null;

          if (epNum > 0) {
            canonical = `${url.origin}/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/episode-${epNum}.html`;
            pageTitle = `Nonton ${dramaTitle} Episode ${epNum} Sub Indo Full HD — DramaBox & Melolo`;
            pageDesc = `Streaming ${dramaTitle} Episode ${epNum} sub Indo gratis tanpa koin di DramaBox & Melolo Web. Tonton kelanjutan Part ${epNum} dari total ${dramaEps} episode dengan kualitas HD tanpa iklan.`;
            if (epNum > 1) {
              prevLink = `${url.origin}/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/episode-${epNum - 1}.html`;
            }
            if (epNum < dramaEps) {
              nextLink = `${url.origin}/${encodeURIComponent(provider)}/${encodeURIComponent(cleanSlug)}/episode-${epNum + 1}.html`;
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

    // 7. Fallback: If request is for an .html route (e.g. SPA navigation or direct link), serve root index.html
    if (url.pathname.endsWith('.html') && url.pathname !== '/offline.html') {
      return env.ASSETS.fetch(new URL('/', request.url));
    }

    // 8. Default Static Asset Delivery
    return env.ASSETS.fetch(request);
  } catch (err) {
    return new Response('Edge Worker Exception: ' + (err.stack || err.message), {
      status: 500,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' }
    });
  }
}
};
