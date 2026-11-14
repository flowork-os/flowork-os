/**
 * DramaBox & Melolo Flow Web - Mobile-First PWA Application Logic
 */

(function () {
  'use strict';

  // --- STATE ---
  const state = {
    currentView: 'viewHome',
    provider: 'all',
    currentCat: 0,
    currentPage: 1,
    totalPages: 1,
    isLoading: false,
    dramas: [],
    searchResults: [],
    currentDrama: null,
    currentEpisodes: [],
    currentEpisodeIndex: 0,
    searchDebounce: null,
    doubleTapTimer: null
  };

  // --- DOM REFS ---
  const $ = (id) => document.getElementById(id);
  const $$ = (sel) => document.querySelectorAll(sel);

  const els = {
    // Nav & Views
    navItems: $$('.nav-item'),
    viewSections: $$('.view-section'),
    catPills: $$('.cat-pill'),
    mainContent: $('mainContent'),

    // Search
    btnSearchToggle: $('btnSearchToggle'),
    searchContainer: $('searchContainer'),
    searchInput: $('searchInput'),
    btnClearSearch: $('btnClearSearch'),
    viewSearch: $('viewSearch'),
    searchGrid: $('searchGrid'),
    searchEmptyState: $('searchEmptyState'),

    // Hero & Catalog
    heroBanner: $('heroBanner'),
    heroTitle: $('heroTitle'),
    heroDesc: $('heroDesc'),
    btnHeroPlay: $('btnHeroPlay'),
    btnHeroFav: $('btnHeroFav'),
    catalogSectionTitle: $('catalogSectionTitle'),
    catalogCountBadge: $('catalogCountBadge'),
    dramaGrid: $('dramaGrid'),
    btnLoadMore: $('btnLoadMore'),

    // History (Lanjutkan Menonton)
    historySection: $('historySection'),
    historyRow: $('historyRow'),
    btnClearHistory: $('btnClearHistory'),
    btnClearHistoryTab: $('btnClearHistoryTab'),
    historyFullGrid: $('historyFullGrid'),
    historyEmptyState: $('historyEmptyState'),

    // Favorites
    favGrid: $('favGrid'),
    favCountBadge: $('favCountBadge'),
    favEmptyState: $('favEmptyState'),

    // Player
    playerView: $('playerView'),
    videoContainer: $('videoContainer'),
    btnPlayerBack: $('btnPlayerBack'),
    btnPlayerFav: $('btnPlayerFav'),
    playerDramaTitle: $('playerDramaTitle'),
    playerPartBadge: $('playerPartBadge'),
    mainVideo: $('mainVideo'),
    gestureLeft: $('gestureLeft'),
    gestureRight: $('gestureRight'),
    playerLoading: $('playerLoading'),
    videoSeek: $('videoSeek'),
    timeCurrent: $('timeCurrent'),
    timeDuration: $('timeDuration'),
    btnPrevPart: $('btnPrevPart'),
    btnNextPart: $('btnNextPart'),
    btnPlayPause: $('btnPlayPause'),
    iconPlay: $('iconPlay'),
    iconPause: $('iconPause'),
    selectPartQuick: $('selectPartQuick'),
    volumeControlWrap: $('volumeControlWrap'),
    btnVolumeMute: $('btnVolumeMute'),
    iconVolHigh: $('iconVolHigh'),
    iconVolMute: $('iconVolMute'),
    videoVolume: $('videoVolume'),
    btnToggleDrawer: $('btnToggleDrawer'),
    btnFullscreen: $('btnFullscreen'),
    playerHud: $('playerHud'),
    playerHudIcon: $('playerHudIcon'),
    playerHudText: $('playerHudText'),

    // Drawer / Bottom Sheet
    episodesBottomSheet: $('episodesBottomSheet'),
    drawerBackdrop: $('drawerBackdrop'),
    sheetHandleBar: $('sheetHandleBar'),
    sheetTitleRow: $('sheetTitleRow'),
    btnCloseDrawer: $('btnCloseDrawer'),
    drawerStats: $('drawerStats'),
    inputQuickJump: $('inputQuickJump'),
    btnQuickJump: $('btnQuickJump'),
    drawerEpisodesGrid: $('drawerEpisodesGrid'),

    // Toast
    toast: $('toast')
  };

  // --- TOAST NOTIFICATION ---
  function showToast(msg, duration = 2500) {
    els.toast.textContent = msg;
    els.toast.classList.remove('hidden');
    clearTimeout(els.toast._timer);
    els.toast._timer = setTimeout(() => {
      els.toast.classList.add('hidden');
    }, duration);
  }

  // --- LOCAL STORAGE HELPERS ---
  const STORAGE_KEYS = {
    HISTORY: 'dramabox_history',
    FAVORITES: 'dramabox_favorites',
    WATCHED_PREFIX: 'dramabox_watched_'
  };

  function getHistory() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEYS.HISTORY) || '[]');
    } catch {
      return [];
    }
  }

  function saveHistoryItem(drama, episodeIndex) {
    if (!drama || !drama.bookId) return;
    let list = getHistory();
    list = list.filter((item) => String(item.bookId) !== String(drama.bookId));
    list.unshift({
      bookId: drama.bookId,
      bookName: drama.bookName || drama.title || 'Serial Drama',
      cover: drama.cover || '',
      provider: drama.provider || 'melolo',
      slug: drama.slug || '',
      lastChapter: episodeIndex + 1,
      totalEpisodes: drama.chapterCount || 0,
      timestamp: Date.now()
    });
    if (list.length > 50) list.pop();
    localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(list));
    renderHistory();
  }

  function clearAllHistory() {
    localStorage.removeItem(STORAGE_KEYS.HISTORY);
    renderHistory();
    showToast('Semua riwayat berhasil dibersihkan');
  }

  function deleteHistoryItem(bookId) {
    let list = getHistory();
    list = list.filter((item) => String(item.bookId) !== String(bookId));
    localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(list));
    renderHistory();
    showToast('Drama dihapus dari riwayat');
  }

  function getWatchedEpisodes(bookId) {
    if (!bookId) return [];
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEYS.WATCHED_PREFIX + bookId) || '[]');
    } catch {
      return [];
    }
  }

  function markEpisodeWatched(bookId, epIndex) {
    if (!bookId) return;
    const key = STORAGE_KEYS.WATCHED_PREFIX + bookId;
    let watched = getWatchedEpisodes(bookId);
    if (!watched.includes(epIndex)) {
      watched.push(epIndex);
      localStorage.setItem(key, JSON.stringify(watched));
    }
  }

  function getFavorites() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEYS.FAVORITES) || '[]');
    } catch {
      return [];
    }
  }

  function isFavorite(bookId) {
    const list = getFavorites();
    return list.some((item) => String(item.bookId) === String(bookId));
  }

  function toggleFavorite(drama) {
    if (!drama || !drama.bookId) return;
    let list = getFavorites();
    const idx = list.findIndex((item) => String(item.bookId) === String(drama.bookId));
    if (idx >= 0) {
      list.splice(idx, 1);
      showToast('Dihapus dari Favorit');
    } else {
      list.unshift({
        bookId: drama.bookId,
        bookName: drama.bookName || drama.title,
        cover: drama.cover || '',
        provider: drama.provider || 'melolo',
        slug: drama.slug || '',
        category: drama.category || 'Drama',
        chapterCount: drama.chapterCount || 0
      });
      showToast('Ditambahkan ke Favorit ⭐');
    }
    localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(list));
    updateFavButtonUI();
    renderFavorites();
  }

  // --- API CALLS ---
  async function fetchBrowse(provider = 'melolo', catId = 0, page = 1) {
    state.isLoading = true;
    els.btnLoadMore.textContent = 'Memuat drama...';
    try {
      const resp = await fetch(`/api/browse?provider=${provider}&cat_id=${catId}&page=${page}&page_size=24`);
      const data = await resp.json();
      if (data.status === 'success') {
        state.totalPages = data.pages || data.total_pages || 1;
        state.currentPage = data.pageNo || data.page || 1;
        const list = data.bookList || data.dramas || [];
        if (page === 1) {
          state.dramas = list;
        } else {
          state.dramas = state.dramas.concat(list);
        }
        renderCatalog();
        if (page === 1 && state.dramas.length > 0) {
          setupHeroBanner(state.dramas[0]);
        }
      }
    } catch (err) {
      console.error('Fetch browse error:', err);
      showToast('Gagal memuat drama. Periksa koneksi.');
    } finally {
      state.isLoading = false;
      els.btnLoadMore.textContent = state.currentPage >= state.totalPages ? 'Semua Drama Dimuat' : 'Muat Lebih Banyak...';
    }
  }

  async function fetchDetail(bookId, provider = 'melolo') {
    els.playerLoading.classList.remove('hidden');
    try {
      const resp = await fetch(`/api/detail?bookId=${encodeURIComponent(bookId)}&provider=${provider}`);
      const data = await resp.json();
      if (data.status === 'success') {
        state.currentDrama = data.bookInfo;
        state.currentEpisodes = data.chapterList || [];
        return data;
      }
    } catch (err) {
      console.error('Fetch detail error:', err);
      showToast('Gagal mengambil detail drama');
    } finally {
      els.playerLoading.classList.add('hidden');
    }
    return null;
  }

  async function searchDramas(query) {
    if (!query.trim()) return;
    try {
      const resp = await fetch(`/api/search?q=${encodeURIComponent(query.trim())}`);
      const data = await resp.json();
      if (data.status === 'success') {
        renderSearchResults(data.results || []);
      }
    } catch (err) {
      console.error('Search error:', err);
    }
  }

  // --- RENDERING ---
  function setupHeroBanner(drama) {
    if (!drama) return;
    els.heroTitle.textContent = drama.bookName || drama.title || 'Serial Drama Pilihan';
    els.heroDesc.textContent = drama.introduction || `Tonton serial drama pendek ${drama.category || ''} full episode sub indo.`;
    if (drama.cover) {
      els.heroBanner.style.backgroundImage = `url("${drama.cover}")`;
    }
    els.btnHeroPlay.onclick = () => openDrama(drama);
    els.btnHeroFav.onclick = () => toggleFavorite(drama);
  }

  function renderCatalog() {
    els.dramaGrid.innerHTML = '';
    state.dramas.forEach((drama) => {
      els.dramaGrid.appendChild(createDramaCard(drama));
    });
    els.catalogCountBadge.textContent = `${state.dramas.length} Judul`;
  }

  function createDramaCard(drama) {
    const card = document.createElement('div');
    card.className = 'drama-card';
    const isMelolo = (drama.provider || '').toLowerCase() === 'melolo' || String(drama.bookId).startsWith('melolo_');
    const badgeClass = isMelolo ? 'melolo' : 'dramabox';
    const badgeText = isMelolo ? 'Melolo' : 'DramaBox';

    card.innerHTML = `
      <div class="poster-wrap">
        <img class="poster-img" src="${drama.cover || 'data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"200\" height=\"300\"><rect width=\"100%\" height=\"100%\" fill=\"%231a162b\"/></svg>'}" alt="${drama.bookName || drama.title}" loading="lazy">
        <span class="provider-badge ${badgeClass}">${badgeText}</span>
        ${drama.chapterCount ? `<span class="ep-badge">${drama.chapterCount} Eps</span>` : ''}
      </div>
      <div class="drama-info">
        <div class="drama-title">${drama.bookName || drama.title || 'Untitled'}</div>
        <div class="drama-cat">${drama.category || 'Sub Indo'}</div>
      </div>
    `;

    card.onclick = () => openDrama(drama);
    return card;
  }

  function renderHistory() {
    const historyList = getHistory();
    // 1. Home row
    if (historyList.length === 0) {
      els.historySection.classList.add('hidden');
      els.historyRow.innerHTML = '';
    } else {
      els.historySection.classList.remove('hidden');
      els.historyRow.innerHTML = '';
      historyList.slice(0, 15).forEach((item) => {
        const card = document.createElement('div');
        card.className = 'history-card';
        card.innerHTML = `
          <div class="history-poster-wrap">
            <img class="history-poster" src="${item.cover || ''}" alt="${item.bookName}" loading="lazy">
            <button class="history-delete-btn" title="Hapus dari riwayat">&times;</button>
            <div class="history-progress-bar">
              <div class="history-progress-fill" style="width: ${Math.min(100, ((item.lastChapter || 1) / (item.totalEpisodes || 40)) * 100)}%"></div>
            </div>
          </div>
          <div class="history-meta">
            <div class="history-title">${item.bookName}</div>
            <div class="history-part-badge">Part ${item.lastChapter || 1}</div>
          </div>
        `;

        card.querySelector('.history-delete-btn').onclick = (e) => {
          e.stopPropagation();
          deleteHistoryItem(item.bookId);
        };

        card.onclick = () => openDrama(item, (item.lastChapter || 1) - 1);
        els.historyRow.appendChild(card);
      });
    }

    // 2. Full History Tab
    els.historyFullGrid.innerHTML = '';
    if (historyList.length === 0) {
      els.historyEmptyState.classList.remove('hidden');
    } else {
      els.historyEmptyState.classList.add('hidden');
      historyList.forEach((item) => {
        const card = createDramaCard(item);
        els.historyFullGrid.appendChild(card);
      });
    }
  }

  function renderFavorites() {
    const favList = getFavorites();
    els.favGrid.innerHTML = '';
    els.favCountBadge.textContent = `${favList.length} Drama`;
    if (favList.length === 0) {
      els.favEmptyState.classList.remove('hidden');
    } else {
      els.favEmptyState.classList.add('hidden');
      favList.forEach((item) => {
        const card = createDramaCard(item);
        els.favGrid.appendChild(card);
      });
    }
  }

  function renderSearchResults(results) {
    els.searchGrid.innerHTML = '';
    if (results.length === 0) {
      els.searchEmptyState.classList.remove('hidden');
    } else {
      els.searchEmptyState.classList.add('hidden');
      results.forEach((item) => {
        els.searchGrid.appendChild(createDramaCard(item));
      });
    }
  }

  function updateFavButtonUI() {
    if (!state.currentDrama) return;
    const fav = isFavorite(state.currentDrama.bookId);
    els.btnPlayerFav.style.color = fav ? '#ff3366' : '#ffffff';
  }

  // --- DRAMA DETAIL & VIDEO PLAYER ---
  async function openDrama(drama, startEpIndex = 0) {
    if (!drama) return;
    state.currentDrama = drama;
    els.playerDramaTitle.textContent = drama.bookName || drama.title || 'Serial Drama';
    els.playerPartBadge.textContent = 'Memuat...';
    els.playerView.classList.remove('hidden');
    updateFavButtonUI();

    const detail = await fetchDetail(drama.bookId, drama.provider || 'melolo');
    if (!detail || !detail.chapterList || detail.chapterList.length === 0) {
      showToast('Episode tidak tersedia');
      return;
    }

    state.currentEpisodes = detail.chapterList;
    populatePartDropdown();
    renderDrawerEpisodes();
    playEpisode(startEpIndex);
  }

  function closePlayer() {
    els.mainVideo.pause();
    els.mainVideo.src = '';
    els.playerView.classList.add('hidden');
    closeDrawer();
  }

  function populatePartDropdown() {
    if (!els.selectPartQuick) return;
    els.selectPartQuick.innerHTML = '';
    state.currentEpisodes.forEach((ep, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      const num = (ep.index !== undefined ? ep.index + 1 : (ep.ep || idx + 1));
      opt.textContent = `Part ${num}`;
      if (idx === state.currentEpisodeIndex) {
        opt.selected = true;
      }
      els.selectPartQuick.appendChild(opt);
    });
    els.selectPartQuick.value = state.currentEpisodeIndex;
  }

  function playEpisode(index) {
    if (index < 0 || index >= state.currentEpisodes.length) return;
    state.currentEpisodeIndex = index;
    const ep = state.currentEpisodes[index];
    const epNumber = (ep.index !== undefined ? ep.index + 1 : (ep.ep || index + 1));
    const total = state.currentEpisodes.length;

    els.playerPartBadge.textContent = `Part ${epNumber} / ${total} ▾`;
    if (els.selectPartQuick) {
      els.selectPartQuick.value = index;
    }

    // Mark as watched
    markEpisodeWatched(state.currentDrama.bookId, index);
    saveHistoryItem(state.currentDrama, index);

    // Determine stream proxy URL
    let streamUrl = ep.mp4 || '';
    const isMelolo = (state.currentDrama && state.currentDrama.provider === 'melolo') ||
                     (state.currentDrama && state.currentDrama.bookId && String(state.currentDrama.bookId).startsWith('melolo_')) ||
                     (ep.provider === 'melolo') ||
                     (streamUrl && streamUrl.includes('melolo.com'));

    if (isMelolo) {
      const slug = (state.currentDrama && state.currentDrama.slug) ||
                   (state.currentDrama && String(state.currentDrama.bookId).replace('melolo_', '')) ||
                   ep.slug || '';
      streamUrl = `/api/stream?provider=melolo&slug=${encodeURIComponent(slug)}&ep=${epNumber}`;
    }

    els.playerLoading.classList.remove('hidden');
    els.mainVideo.pause();
    els.mainVideo.currentTime = 0;
    els.mainVideo.src = streamUrl;
    els.mainVideo.load();
    const playPromise = els.mainVideo.play();
    if (playPromise !== undefined) {
      playPromise.catch((e) => {
        console.warn('Autoplay prevented or video loading:', e);
      });
    }

    updateDrawerActiveEpisode();
  }

  function renderDrawerEpisodes() {
    els.drawerEpisodesGrid.innerHTML = '';
    const bookId = state.currentDrama ? state.currentDrama.bookId : '';
    const watched = getWatchedEpisodes(bookId);

    els.drawerStats.textContent = `${state.currentEpisodes.length} Part`;

    state.currentEpisodes.forEach((ep, idx) => {
      const btn = document.createElement('button');
      btn.className = 'ep-item';
      const epNum = (ep.index !== undefined ? ep.index + 1 : (ep.ep || idx + 1));
      btn.textContent = `P${epNum}`;

      if (watched.includes(idx)) {
        btn.classList.add('watched');
      }
      if (idx === state.currentEpisodeIndex) {
        btn.classList.add('active');
      }

      btn.onclick = (e) => {
        e.stopPropagation();
        playEpisode(idx);
        closeDrawer();
      };

      els.drawerEpisodesGrid.appendChild(btn);
    });
  }

  function updateDrawerActiveEpisode() {
    const items = els.drawerEpisodesGrid.querySelectorAll('.ep-item');
    const bookId = state.currentDrama ? state.currentDrama.bookId : '';
    const watched = getWatchedEpisodes(bookId);

    items.forEach((item, idx) => {
      item.classList.remove('active');
      if (watched.includes(idx)) {
        item.classList.add('watched');
      }
      if (idx === state.currentEpisodeIndex) {
        item.classList.add('active');
      }
    });
  }

  function openDrawer() {
    els.episodesBottomSheet.classList.remove('collapsed');
    if (els.drawerBackdrop) els.drawerBackdrop.classList.remove('hidden');
    if (els.btnToggleDrawer) els.btnToggleDrawer.classList.add('active');
    const hint = els.sheetTitleRow ? els.sheetTitleRow.querySelector('.sheet-toggle-hint') : null;
    if (hint) hint.textContent = '▴';
    setTimeout(() => {
      const activeEl = els.drawerEpisodesGrid.querySelector('.ep-item.active');
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 120);
  }

  function closeDrawer() {
    els.episodesBottomSheet.classList.add('collapsed');
    if (els.drawerBackdrop) els.drawerBackdrop.classList.add('hidden');
    if (els.btnToggleDrawer) els.btnToggleDrawer.classList.remove('active');
    const hint = els.sheetTitleRow ? els.sheetTitleRow.querySelector('.sheet-toggle-hint') : null;
    if (hint) hint.textContent = '▾';
  }

  function toggleDrawer() {
    if (els.episodesBottomSheet.classList.contains('collapsed')) {
      openDrawer();
    } else {
      closeDrawer();
    }
  }

  // --- GESTURE / TAP HANDLERS ---
  function setupGestures() {
    let lastTap = 0;
    let tapTimeout = null;

    els.mainVideo.addEventListener('click', (e) => {
      const now = Date.now();
      const rect = els.mainVideo.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const isLeft = clickX < rect.width / 2;

      if (now - lastTap < 300) {
        // Double tap!
        clearTimeout(tapTimeout);
        if (isLeft) {
          seekRelative(-10);
          showGestureRipple(els.gestureLeft);
        } else {
          seekRelative(10);
          showGestureRipple(els.gestureRight);
        }
      } else {
        // Single tap: toggle play/pause or controls
        tapTimeout = setTimeout(() => {
          togglePlayPause();
        }, 300);
      }
      lastTap = now;
    });
  }

  // --- CENTER PLAYER HUD FEEDBACK ---
  let hudTimer = null;
  function showHud(icon, text) {
    if (!els.playerHud) return;
    els.playerHudIcon.textContent = icon;
    els.playerHudText.textContent = text;
    els.playerHud.classList.remove('hidden');
    clearTimeout(hudTimer);
    hudTimer = setTimeout(() => {
      els.playerHud.classList.add('hidden');
    }, 1100);
  }

  // --- VOLUME CONTROLS ---
  function initVolume() {
    const savedVol = localStorage.getItem('dramabox_volume');
    const savedMuted = localStorage.getItem('dramabox_muted') === 'true';
    const vol = savedVol !== null ? parseFloat(savedVol) : 1.0;

    applyVolume(vol, savedMuted, false);

    if (els.videoVolume) {
      els.videoVolume.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        applyVolume(val, val === 0, true);
      });
    }

    if (els.btnVolumeMute) {
      els.btnVolumeMute.onclick = (e) => {
        e.stopPropagation();
        toggleMute();
      };
    }
  }

  function applyVolume(val, isMuted, showFeedback = true) {
    const clamped = Math.max(0, Math.min(1, val));
    if (els.mainVideo) {
      els.mainVideo.volume = clamped;
      els.mainVideo.muted = isMuted;
    }
    if (els.videoVolume) {
      els.videoVolume.value = clamped;
    }

    if (isMuted || clamped === 0) {
      if (els.iconVolHigh) els.iconVolHigh.classList.add('hidden');
      if (els.iconVolMute) els.iconVolMute.classList.remove('hidden');
      if (showFeedback) showHud('🔇', 'Muted');
    } else {
      if (els.iconVolHigh) els.iconVolHigh.classList.remove('hidden');
      if (els.iconVolMute) els.iconVolMute.classList.add('hidden');
      if (showFeedback) showHud('🔊', `${Math.round(clamped * 100)}%`);
    }

    localStorage.setItem('dramabox_volume', clamped);
    localStorage.setItem('dramabox_muted', isMuted);
  }

  function toggleMute() {
    const willMute = !els.mainVideo.muted;
    applyVolume(els.mainVideo.volume || 1.0, willMute, true);
  }

  function adjustVolumeRelative(delta) {
    const current = els.mainVideo.muted ? 0 : els.mainVideo.volume;
    const next = Math.max(0, Math.min(1, current + delta));
    applyVolume(next, next === 0, true);
  }

  // --- SCROLL & SWIPE EPISODE NAVIGATION ---
  let lastScrollNavTime = 0;
  function setupScrollNavigation() {
    // 1. Mouse Wheel on Video Container (Next / Prev Part)
    if (els.videoContainer) {
      els.videoContainer.addEventListener('wheel', (e) => {
        // If drawer is open and pointer is inside drawer, let drawer scroll normally!
        if (!els.episodesBottomSheet.classList.contains('collapsed') && e.target.closest('#episodesBottomSheet')) {
          return;
        }

        // If hovering over volume wrap, adjust volume instead
        if (e.target.closest('#volumeControlWrap')) {
          e.preventDefault();
          adjustVolumeRelative(e.deltaY < 0 ? 0.05 : -0.05);
          return;
        }

        const now = Date.now();
        if (now - lastScrollNavTime < 450) return;

        if (e.deltaY > 30) {
          // Wheel down -> Next Part
          e.preventDefault();
          if (state.currentEpisodeIndex < state.currentEpisodes.length - 1) {
            lastScrollNavTime = now;
            const nextIdx = state.currentEpisodeIndex + 1;
            showHud('🔽', `Part ${nextIdx + 1}`);
            playEpisode(nextIdx);
          } else {
            showHud('🏁', 'Part Terakhir');
          }
        } else if (e.deltaY < -30) {
          // Wheel up -> Prev Part
          e.preventDefault();
          if (state.currentEpisodeIndex > 0) {
            lastScrollNavTime = now;
            const prevIdx = state.currentEpisodeIndex - 1;
            showHud('🔼', `Part ${prevIdx + 1}`);
            playEpisode(prevIdx);
          } else {
            showHud('⏮️', 'Part Pertama');
          }
        }
      }, { passive: false });

      // 2. Touch Vertical Swipes (TikTok / Reels / DramaBox style)
      let touchStartY = 0;
      let touchStartX = 0;
      let isSwiping = false;

      els.videoContainer.addEventListener('touchstart', (e) => {
        if (!els.episodesBottomSheet.classList.contains('collapsed') && e.target.closest('#episodesBottomSheet')) {
          return;
        }
        if (e.touches.length === 1) {
          touchStartY = e.touches[0].clientY;
          touchStartX = e.touches[0].clientX;
          isSwiping = true;
        }
      }, { passive: true });

      els.videoContainer.addEventListener('touchend', (e) => {
        if (!isSwiping || e.changedTouches.length === 0) return;
        isSwiping = false;
        const touchEndY = e.changedTouches[0].clientY;
        const touchEndX = e.changedTouches[0].clientX;
        const diffY = touchEndY - touchStartY;
        const diffX = touchEndX - touchStartX;

        // Vertical gesture dominates horizontal gesture
        if (Math.abs(diffY) > 55 && Math.abs(diffY) > Math.abs(diffX) * 1.4) {
          const now = Date.now();
          if (now - lastScrollNavTime < 450) return;

          if (diffY < -55) {
            // Swipe Up -> Next Part
            if (state.currentEpisodeIndex < state.currentEpisodes.length - 1) {
              lastScrollNavTime = now;
              const nextIdx = state.currentEpisodeIndex + 1;
              showHud('🔽', `Part ${nextIdx + 1}`);
              playEpisode(nextIdx);
            } else {
              showHud('���', 'Part Terakhir');
            }
          } else if (diffY > 55) {
            // Swipe Down -> Prev Part
            if (state.currentEpisodeIndex > 0) {
              lastScrollNavTime = now;
              const prevIdx = state.currentEpisodeIndex - 1;
              showHud('🔼', `Part ${prevIdx + 1}`);
              playEpisode(prevIdx);
            } else {
              showHud('⏮️', 'Part Pertama');
            }
          }
        }
      }, { passive: true });
    }
  }

  function showGestureRipple(el) {
    el.classList.add('active');
    setTimeout(() => {
      el.classList.remove('active');
    }, 450);
  }

  function seekRelative(seconds) {
    if (!els.mainVideo.duration) return;
    els.mainVideo.currentTime = Math.max(0, Math.min(els.mainVideo.duration, els.mainVideo.currentTime + seconds));
  }

  function togglePlayPause() {
    if (els.mainVideo.paused) {
      els.mainVideo.play();
    } else {
      els.mainVideo.pause();
    }
  }

  function formatTime(secs) {
    if (isNaN(secs)) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  // --- EVENT LISTENERS ---
  function initEvents() {
    // Bottom Nav Tabs
    els.navItems.forEach((btn) => {
      btn.onclick = () => {
        const view = btn.dataset.view;
        switchView(view);
      };
    });

    // Category Tabs
    els.catPills.forEach((pill) => {
      pill.onclick = () => {
        els.catPills.forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        state.currentCat = parseInt(pill.dataset.cat, 10);
        state.currentPage = 1;
        fetchBrowse(state.provider, state.currentCat, 1);
      };
    });

    // Search Toggle
    els.btnSearchToggle.onclick = () => {
      els.searchContainer.classList.toggle('collapsed');
      if (!els.searchContainer.classList.contains('collapsed')) {
        els.searchInput.focus();
      }
    };

    els.btnClearSearch.onclick = () => {
      els.searchInput.value = '';
      switchView('viewHome');
    };

    els.searchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim();
      clearTimeout(state.searchDebounce);
      if (!q) {
        switchView('viewHome');
        return;
      }
      state.searchDebounce = setTimeout(() => {
        switchView('viewSearch');
        searchDramas(q);
      }, 350);
    });

    // Load More Button
    els.btnLoadMore.onclick = () => {
      if (state.currentPage < state.totalPages && !state.isLoading) {
        fetchBrowse(state.provider, state.currentCat, state.currentPage + 1);
      }
    };

    // History Clean Buttons
    els.btnClearHistory.onclick = clearAllHistory;
    els.btnClearHistoryTab.onclick = clearAllHistory;

    // Player Controls
    els.btnPlayerBack.onclick = closePlayer;
    els.btnPlayerFav.onclick = () => toggleFavorite(state.currentDrama);
    els.btnPlayPause.onclick = togglePlayPause;

    // Clickable header part badge opens drawer
    if (els.playerPartBadge) {
      els.playerPartBadge.onclick = (e) => {
        e.stopPropagation();
        toggleDrawer();
      };
    }

    // Quick part select dropdown
    if (els.selectPartQuick) {
      els.selectPartQuick.onchange = (e) => {
        const idx = parseInt(e.target.value, 10);
        if (!isNaN(idx)) {
          playEpisode(idx);
        }
      };
    }

    els.btnPrevPart.onclick = () => {
      if (state.currentEpisodeIndex > 0) {
        const prevIdx = state.currentEpisodeIndex - 1;
        showHud('🔼', `Part ${prevIdx + 1}`);
        playEpisode(prevIdx);
      } else {
        showToast('Sudah di episode pertama');
      }
    };

    els.btnNextPart.onclick = () => {
      if (state.currentEpisodeIndex < state.currentEpisodes.length - 1) {
        const nextIdx = state.currentEpisodeIndex + 1;
        showHud('🔽', `Part ${nextIdx + 1}`);
        playEpisode(nextIdx);
      } else {
        showToast('Sudah di episode terakhir');
      }
    };

    els.btnToggleDrawer.onclick = toggleDrawer;
    if (els.btnCloseDrawer) els.btnCloseDrawer.onclick = closeDrawer;
    if (els.drawerBackdrop) els.drawerBackdrop.onclick = closeDrawer;
    if (els.sheetTitleRow) els.sheetTitleRow.onclick = closeDrawer;
    if (els.sheetHandleBar) {
      els.sheetHandleBar.onclick = closeDrawer;
      let touchStartY = 0;
      els.sheetHandleBar.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
      }, { passive: true });
      els.sheetHandleBar.addEventListener('touchend', (e) => {
        const touchEndY = e.changedTouches[0].clientY;
        if (touchEndY - touchStartY > 35) {
          closeDrawer();
        }
      }, { passive: true });
    }

    // Quick Jump ("Lompat ke Part")
    const handleQuickJump = () => {
      const partNum = parseInt(els.inputQuickJump.value, 10);
      if (!isNaN(partNum) && partNum >= 1 && partNum <= state.currentEpisodes.length) {
        showHud('🎯', `Part ${partNum}`);
        playEpisode(partNum - 1);
        closeDrawer();
        els.inputQuickJump.value = '';
      } else {
        showToast(`Masukkan nomor part antara 1 - ${state.currentEpisodes.length}`);
      }
    };

    els.btnQuickJump.onclick = handleQuickJump;
    els.inputQuickJump.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleQuickJump();
      }
    });

    els.btnFullscreen.onclick = () => {
      if (!document.fullscreenElement) {
        els.playerView.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    };

    // Video Events
    els.mainVideo.addEventListener('play', () => {
      els.iconPlay.classList.add('hidden');
      els.iconPause.classList.remove('hidden');
    });

    els.mainVideo.addEventListener('pause', () => {
      els.iconPlay.classList.remove('hidden');
      els.iconPause.classList.add('hidden');
    });

    els.mainVideo.addEventListener('waiting', () => {
      els.playerLoading.classList.remove('hidden');
    });

    els.mainVideo.addEventListener('loadeddata', () => {
      els.playerLoading.classList.add('hidden');
    });

    els.mainVideo.addEventListener('canplay', () => {
      els.playerLoading.classList.add('hidden');
    });

    els.mainVideo.addEventListener('playing', () => {
      els.playerLoading.classList.add('hidden');
    });

    els.mainVideo.addEventListener('error', () => {
      els.playerLoading.classList.add('hidden');
      const err = els.mainVideo.error;
      console.warn('HTML5 Video error:', err);
      const curr = els.mainVideo.src || '';
      if (curr && !curr.includes('/api/stream')) {
        showToast('Beralih ke stream proxy edge...');
        els.playerLoading.classList.remove('hidden');
        els.mainVideo.src = `/api/stream?url=${encodeURIComponent(curr)}`;
        els.mainVideo.load();
        els.mainVideo.play().catch(() => {});
      } else {
        showToast('Gagal memuat video episode ini');
      }
    });

    els.mainVideo.addEventListener('timeupdate', () => {
      const cur = els.mainVideo.currentTime;
      const dur = els.mainVideo.duration;
      els.timeCurrent.textContent = formatTime(cur);
      if (dur) {
        els.timeDuration.textContent = formatTime(dur);
        els.videoSeek.value = (cur / dur) * 100;
      }
    });

    els.mainVideo.addEventListener('ended', () => {
      // Auto play next episode
      if (state.currentEpisodeIndex < state.currentEpisodes.length - 1) {
        showToast('Memutar episode berikutnya... ⏩');
        setTimeout(() => {
          playEpisode(state.currentEpisodeIndex + 1);
        }, 1000);
      }
    });

    els.videoSeek.addEventListener('input', (e) => {
      if (els.mainVideo.duration) {
        els.mainVideo.currentTime = (e.target.value / 100) * els.mainVideo.duration;
      }
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      if (els.playerView.classList.contains('hidden')) return;
      if (e.target.tagName === 'INPUT') return;

      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        togglePlayPause();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        adjustVolumeRelative(0.08);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        adjustVolumeRelative(-0.08);
      } else if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        toggleMute();
      } else if (e.key === 'e' || e.key === 'E') {
        e.preventDefault();
        toggleDrawer();
      } else if (e.key === 'Escape') {
        if (!els.episodesBottomSheet.classList.contains('collapsed')) {
          closeDrawer();
        } else {
          closePlayer();
        }
      } else if (e.key === 'n' || e.key === 'N') {
        els.btnNextPart.click();
      } else if (e.key === 'p' || e.key === 'P') {
        els.btnPrevPart.click();
      } else if (e.key === 'f' || e.key === 'F') {
        els.btnFullscreen.click();
      }
    });

    initVolume();
    setupScrollNavigation();
    setupGestures();
  }

  function switchView(viewName) {
    const originalRequestedView = viewName;
    if (viewName === 'viewMelolo') {
      state.provider = 'melolo';
      els.catalogSectionTitle.textContent = '✨ Katalog Melolo Sub Indo (1,480 Judul)';
      viewName = 'viewHome';
      fetchBrowse('melolo', state.currentCat, 1);
    } else if (viewName === 'viewDramaBox') {
      state.provider = 'dramabox';
      els.catalogSectionTitle.textContent = '✨ Katalog DramaBox Populer (1,320 Judul)';
      viewName = 'viewHome';
      fetchBrowse('dramabox', state.currentCat, 1);
    } else if (viewName === 'viewHome') {
      state.provider = 'all';
      els.catalogSectionTitle.textContent = '✨ Semua Drama Pendek (2,800+ Judul)';
      fetchBrowse('all', state.currentCat, 1);
    }

    state.currentView = viewName;
    els.viewSections.forEach((s) => s.classList.remove('active'));
    const target = $(viewName);
    if (target) target.classList.add('active');

    els.navItems.forEach((item) => {
      item.classList.toggle('active', item.dataset.view === originalRequestedView);
    });

    if (viewName === 'viewHistory') renderHistory();
    if (viewName === 'viewFavorites') renderFavorites();

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // --- INIT ---
  function init() {
    initEvents();
    renderHistory();
    renderFavorites();
    els.catalogSectionTitle.textContent = '✨ Semua Drama Pendek (2,800+ Judul)';
    fetchBrowse('all', 0, 1);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
