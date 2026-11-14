/**
 * Cloudflare Pages Function: /api/stream
 * Range-compliant Edge Video Proxy for Melolo & DramaBox CDNs
 */

export async function onRequest(context) {
  const { request } = context;
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

  // Forward range request to upstream CDN
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
