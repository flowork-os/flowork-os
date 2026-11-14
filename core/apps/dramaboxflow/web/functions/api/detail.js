/**
 * Cloudflare Pages Function: /api/detail
 */

export async function onRequestGet(context) {
  const { searchParams } = new URL(context.request.url);
  const bookId = searchParams.get('bookId') || '';

  if (!bookId) {
    return new Response(JSON.stringify({ status: 'error', message: 'bookId required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }

  // 1. MELOLO PROVIDER
  if (bookId.startsWith('melolo_')) {
    const slug = bookId.replace('melolo_', '');
    let meta = {
      bookId,
      bookName: slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
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
        const targetUrl = (item.url || '').replace(/\\u0026/g, '&');
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

    return new Response(
      JSON.stringify({
        status: 'success',
        bookInfo: meta,
        chapterList: chapters,
        provider: 'melolo'
      }),
      {
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Access-Control-Allow-Origin': '*'
        }
      }
    );
  }

  // 2. DRAMABOX GOODBOS PROVIDER
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
        const chName = ep.chapterName || `Part ${idx + 1}`;
        chapters.push({
          id: ep.chapterId || idx + 1,
          name: chName,
          chapterName: chName,
          index: idx,
          indexStr: `Part ${idx + 1}`,
          mp4,
          unlock: true,
          provider: 'dramabox'
        });
      });
    }
  } catch (err) {
    console.error('Error fetching Goodbos allepisode:', err);
  }

  const meta = {
    bookId,
    bookName: `DramaBox #${bookId}`,
    cover: '',
    chapterCount: chapters.length,
    introduction: 'DramaBox Short Drama Series.',
    provider: 'dramabox'
  };

  return new Response(
    JSON.stringify({
      status: 'success',
      bookInfo: meta,
      chapterList: chapters,
      provider: 'dramabox'
    }),
    {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      }
    }
  );
}
