/**
 * Cloudflare Pages Function: /api/search
 * Searches across Melolo catalog (1,480), DramaBox catalog (1,320), and Goodbos live API
 */

export async function onRequestGet(context) {
  const { searchParams } = new URL(context.request.url);
  const q = (searchParams.get('q') || '').trim().toLowerCase();

  if (!q) {
    return new Response(JSON.stringify({ status: 'success', results: [] }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  let results = [];
  const seen = new Set();

  const matchSearch = (d) => {
    const name = (d.bookName || d.title || '').toLowerCase();
    const slug = (d.slug || '').toLowerCase();
    const intro = (d.introduction || '').toLowerCase();
    const tags = Array.isArray(d.typeTwoNames) ? d.typeTwoNames.join(' ').toLowerCase() : '';
    return name.includes(q) || slug.includes(q) || intro.includes(q) || tags.includes(q);
  };

  // 1. Search DramaBox Static Catalog
  try {
    const dUrl = new URL('/dramabox_catalog.json', context.request.url);
    const dResp = await context.env.ASSETS.fetch(dUrl);
    const dData = await dResp.json();
    const dCatalog = dData.dramas || dData || [];

    for (const d of dCatalog) {
      const bid = String(d.bookId);
      if (matchSearch(d) && !seen.has(bid)) {
        seen.add(bid);
        d.provider = 'dramabox';
        results.push(d);
        if (results.length >= 40) break;
      }
    }
  } catch (err) {
    console.error('DramaBox catalog search error:', err);
  }

  // 2. Search Melolo Static Catalog
  try {
    const mUrl = new URL('/melolo_catalog.json', context.request.url);
    const mResp = await context.env.ASSETS.fetch(mUrl);
    const mData = await mResp.json();
    const mCatalog = mData.dramas || mData || [];

    for (const d of mCatalog) {
      const bid = String(d.bookId);
      if (matchSearch(d) && !seen.has(bid)) {
        seen.add(bid);
        d.provider = 'melolo';
        results.push(d);
        if (results.length >= 80) break;
      }
    }
  } catch (err) {
    console.error('Melolo catalog search error:', err);
  }

  // 3. Search Goodbos Live DramaBox API
  try {
    const gUrl = `https://dramabox.goodbos.online/api/dramabox/search?query=${encodeURIComponent(q)}`;
    const resp = await fetch(gUrl, {
      headers: {
        'x-token': '6EB57533425BC1D78ADA1F80354161D4',
        'User-Agent': 'Mozilla/5.0'
      }
    });
    const gData = await resp.json();
    const gList = Array.isArray(gData) ? gData : gData.data || [];
    for (const b of gList) {
      const bid = String(b.bookId);
      if (!seen.has(bid)) {
        seen.add(bid);
        b.provider = 'dramabox';
        results.push(b);
      }
    }
  } catch (err) {
    console.error('Goodbos search error:', err);
  }

  return new Response(JSON.stringify({ status: 'success', results }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*'
    }
  });
}
