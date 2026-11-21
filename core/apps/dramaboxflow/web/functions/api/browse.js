/**
 * Cloudflare Pages Function: /api/browse
 * Supports multi-provider catalog: Melolo (1,480 titles) & DramaBox (1,320 titles)
 */

export async function onRequestGet(context) {
  const { searchParams } = new URL(context.request.url);
  const provider = searchParams.get('provider') || 'all';
  const catId = parseInt(searchParams.get('cat_id') || '0', 10);
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = parseInt(searchParams.get('page_size') || '24', 10);

  let meloloList = [];
  let dramaboxList = [];

  // 1. Fetch catalogs from Pages ASSETS
  try {
    if (provider === 'all' || provider === 'melolo') {
      const mUrl = new URL('/melolo_catalog.json', context.request.url);
      const mResp = await context.env.ASSETS.fetch(mUrl);
      const mData = await mResp.json();
      meloloList = mData.dramas || mData || [];
    }
  } catch (err) {
    console.error('Error fetching melolo_catalog:', err);
  }

  try {
    if (provider === 'all' || provider === 'dramabox') {
      const dUrl = new URL('/dramabox_catalog.json', context.request.url);
      const dResp = await context.env.ASSETS.fetch(dUrl);
      const dData = await dResp.json();
      dramaboxList = dData.dramas || dData || [];
    }
  } catch (err) {
    console.error('Error fetching dramabox_catalog:', err);
  }

  let catalog = [];
  if (provider === 'melolo') {
    catalog = meloloList;
  } else if (provider === 'dramabox') {
    catalog = dramaboxList;
  } else {
    // Merge & alternate
    const maxLen = Math.max(meloloList.length, dramaboxList.length);
    for (let i = 0; i < maxLen; i++) {
      if (i < meloloList.length) catalog.push(meloloList[i]);
      if (i < dramaboxList.length) catalog.push(dramaboxList[i]);
    }
  }

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
    filtered = catalog.filter((d) => {
      const tags = Array.isArray(d.typeTwoNames) ? d.typeTwoNames.join(' ') : '';
      const labels = Array.isArray(d.tags) ? d.tags.join(' ') : '';
      const text = [
        d.category || '',
        d.bookName || '',
        d.title || '',
        tags,
        labels,
        d.introduction || ''
      ].join(' ').toLowerCase();
      return keys.some((k) => text.includes(k));
    });
  }

  const total = filtered.length;
  const pages = Math.ceil(total / pageSize) || 1;
  const safePage = Math.max(1, Math.min(page, pages));
  const start = (safePage - 1) * pageSize;
  const end = start + pageSize;

  return new Response(
    JSON.stringify({
      status: 'success',
      bookList: filtered.slice(start, end),
      pageNo: safePage,
      pages,
      total,
      provider
    }),
    {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=600'
      }
    }
  );
}
