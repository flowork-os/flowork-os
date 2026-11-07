// MrFlow Sovereign Connector & Account Matrix UI Controller
// Supports auth.floworkos.com login, Cloud Vault sync, and multi-provider switching (Connector, Ollama, 9Router).

(function() {
    'use strict';

    const API_BASE = window.location.origin;

    const state = {
        authenticated: false,
        user: null,
        activeProvider: 'connector',
        providers: {},
        accounts: [],
        totalAccounts: 0,
        maxAccounts: 50,
        activeAccountId: '',
        activeEmail: 'None',
        rotationMode: 'failover',
        healthyCount: 0,
        cooldownCount: 0,
        filter: 'all',
        searchQuery: '',
        isLoading: false,
        authPolling: null,
        oauthPolling: null
    };

    // DOM Elements
    const els = {
        gateLock: document.getElementById('sovereign-gate-lock'),
        btnLockLogin: document.getElementById('btn-lock-login'),
        inputManualToken: document.getElementById('input-manual-token'),
        btnSubmitToken: document.getElementById('btn-submit-token'),
        lockStatusTxt: document.getElementById('lock-status-txt'),

        btnHeaderConnect: document.getElementById('btn-header-connect'),
        userBadge: document.getElementById('user-badge'),
        userName: document.getElementById('user-name'),
        btnLogout: document.getElementById('btn-logout'),

        currentProviderTag: document.getElementById('current-provider-tag'),
        footerActiveProvider: document.getElementById('footer-active-provider'),

        // Provider views
        viewConnector: document.getElementById('view-connector'),
        viewOllama: document.getElementById('view-ollama'),
        view9Router: document.getElementById('view-9router'),

        // Ollama panel
        inputOllamaHost: document.getElementById('input-ollama-host'),
        inputOllamaModel: document.getElementById('input-ollama-model'),
        btnAddOllamaModel: document.getElementById('btn-add-ollama-model'),
        ollamaModelsChips: document.getElementById('ollama-models-chips'),
        btnTestOllama: document.getElementById('btn-test-ollama'),
        btnSaveOllama: document.getElementById('btn-save-ollama'),
        ollamaPingPill: document.getElementById('ollama-ping-pill'),
        ollamaPingTxt: document.getElementById('ollama-ping-txt'),

        // 9Router panel
        input9RouterHost: document.getElementById('input-9router-host'),
        input9RouterKey: document.getElementById('input-9router-key'),
        input9RouterModel: document.getElementById('input-9router-model'),
        btnAdd9RouterModel: document.getElementById('btn-add-9router-model'),
        r9ModelsChips: document.getElementById('9router-models-chips'),
        btnTest9Router: document.getElementById('btn-test-9router'),
        btnSave9Router: document.getElementById('btn-save-9router'),
        r9PingPill: document.getElementById('9router-ping-pill'),
        r9PingTxt: document.getElementById('9router-ping-txt'),

        // Connector metrics & controls
        statTotal: document.getElementById('stat-total'),
        statMax: document.getElementById('stat-max'),
        statActiveEmail: document.getElementById('stat-active-email'),
        statHealth: document.getElementById('stat-health'),
        statCooldownSub: document.getElementById('stat-cooldown-sub'),
        strategySelect: document.getElementById('strategy-select'),

        btnSyncCloud: document.getElementById('btn-sync-cloud'),
        btnAddAccount: document.getElementById('btn-add-account'),
        btnRefreshPool: document.getElementById('btn-refresh-pool'),
        btnClearCooldown: document.getElementById('btn-clear-cooldown'),

        searchInput: document.getElementById('account-search-input'),
        searchClearBtn: document.getElementById('search-clear-btn'),
        accountsList: document.getElementById('accounts-list'),

        tabAll: document.getElementById('tab-cnt-all'),
        tabActive: document.getElementById('tab-cnt-active'),
        tabReady: document.getElementById('tab-cnt-ready'),
        tabCooldown: document.getElementById('tab-cnt-cooldown'),

        toastContainer: document.getElementById('toast-container'),
        systemStatusText: document.getElementById('system-status-text')
    };

    // ── Toast Notifications ──
    function showToast(message, type = 'info') {
        if (!els.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = '⚡';
        if (type === 'success') icon = '🟢';
        if (type === 'error') icon = '⚠️';

        toast.innerHTML = `
            <span>${icon}</span>
            <span>${escapeHtml(message)}</span>
        `;
        els.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'toastOut 0.25s forwards';
            setTimeout(() => toast.remove(), 250);
        }, 3800);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatTimeRemaining(expiresAt) {
        if (!expiresAt) return 'Session active';
        const now = Date.now();
        const diffSec = Math.floor((expiresAt - now) / 1000);
        if (diffSec <= 0) return 'Expired';
        const mins = Math.floor(diffSec / 60);
        const hours = Math.floor(mins / 60);
        if (hours > 0) return `${hours}h ${mins % 60}m left`;
        return `${mins}m left`;
    }

    // ── API Synchronization ──
    async function syncAccounts(silent = false) {
        try {
            if (!silent) state.isLoading = true;
            const res = await fetch(`${API_BASE}/auth/router/status`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            state.authenticated = !!data.authenticated;
            state.user = data.user || null;
            let prov = (data.active_provider || 'connector').toLowerCase();
            if (prov === 'google') prov = 'connector';
            state.activeProvider = prov;
            state.providers = data.providers || {};
            state.accounts = data.accounts || [];
            state.totalAccounts = data.total_accounts || state.accounts.length;
            state.maxAccounts = data.max_accounts || 50;
            state.activeAccountId = data.active_account_id || '';
            state.activeEmail = data.active_email || 'None';
            state.rotationMode = data.rotation_mode || 'failover';
            state.healthyCount = data.healthy_count || state.accounts.filter(a => a.status !== 'cooldown' && a.status !== 'error').length;
            state.cooldownCount = data.cooldown_count || state.accounts.filter(a => a.status === 'cooldown').length;

            updateAuthUI();
            updateProviderView(state.activeProvider);
            updateStatsUI();
            renderAccountsList();
        } catch (err) {
            console.error('Failed to sync router state:', err);
            if (!silent) showToast(`Network error: ${err.message}`, 'error');
            if (els.systemStatusText) {
                els.systemStatusText.textContent = 'MATRIX OFFLINE // RETRYING';
                els.systemStatusText.parentElement.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                els.systemStatusText.style.color = '#f87171';
            }
        } finally {
            state.isLoading = false;
        }
    }

    // ── Update Auth UI ──
    function updateAuthUI() {
        if (!state.authenticated) {
            // Show lock overlay
            if (els.gateLock) els.gateLock.classList.remove('hidden');
            if (els.btnHeaderConnect) els.btnHeaderConnect.style.display = 'flex';
            if (els.userBadge) els.userBadge.style.display = 'none';

            if (els.systemStatusText) {
                els.systemStatusText.textContent = 'ROUTER LOCKED // AUTH REQUIRED';
                els.systemStatusText.parentElement.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                els.systemStatusText.style.color = '#f87171';
            }
        } else {
            // Authenticated: hide lock overlay
            if (els.gateLock) els.gateLock.classList.add('hidden');
            if (els.btnHeaderConnect) els.btnHeaderConnect.style.display = 'none';
            if (els.userBadge) {
                els.userBadge.style.display = 'flex';
                const username = state.user?.username || state.user?.email?.split('@')[0] || 'operator';
                const tier = state.user?.tier ? ` [${state.user.tier.toUpperCase()}]` : '';
                if (els.userName) els.userName.textContent = `@${username}${tier}`;
            }

            if (els.systemStatusText) {
                els.systemStatusText.textContent = `MATRIX ONLINE // :${window.location.port || '9099'}`;
                els.systemStatusText.parentElement.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                els.systemStatusText.style.color = '#10b981';
            }
        }
    }

    // ── Update Provider View Switcher ──
    function updateProviderView(provId) {
        document.querySelectorAll('.provider-tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-provider') === provId);
        });

        // Hide all views first
        if (els.viewConnector) els.viewConnector.classList.toggle('hidden', provId !== 'connector');
        if (els.viewOllama) els.viewOllama.classList.toggle('hidden', provId !== 'ollama');
        if (els.view9Router) els.view9Router.classList.toggle('hidden', provId !== '9router');

        let title = '⚡ SOVEREIGN CONNECTOR';
        let footerText = 'Sovereign Connector (Google Pool)';
        if (provId === 'ollama') {
            title = '🦙 OLLAMA LOCAL ENGINE';
            footerText = 'Ollama Local Engine (Offline GPU)';
        } else if (provId === '9router') {
            title = '🔀 9ROUTER GATEWAY';
            footerText = '9Router Universal Proxy';
        }

        if (els.currentProviderTag) els.currentProviderTag.textContent = title;
        if (els.footerActiveProvider) els.footerActiveProvider.textContent = footerText;

        // Populate provider forms with stored config
        if (provId === 'ollama') {
            const oCfg = state.providers?.ollama || {};
            if (els.inputOllamaHost && oCfg.host) els.inputOllamaHost.value = oCfg.host;
            if (els.inputOllamaModel && oCfg.default_model) els.inputOllamaModel.value = oCfg.default_model;
            renderOllamaModelChips();
        } else if (provId === '9router') {
            const rCfg = state.providers?.['9router'] || {};
            if (els.input9RouterHost && rCfg.host) els.input9RouterHost.value = rCfg.host;
            if (els.input9RouterKey && rCfg.api_key) els.input9RouterKey.value = rCfg.api_key;
            if (els.input9RouterModel && rCfg.default_model) els.input9RouterModel.value = rCfg.default_model;
            render9RouterModelChips();
        }
    }

    async function switchActiveProvider(provId) {
        try {
            state.activeProvider = provId;
            updateProviderView(provId);

            const res = await fetch(`${API_BASE}/auth/router/provider-config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active_provider: provId })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Switched active inference engine to: ${provId.toUpperCase()}`, 'success');
            }
        } catch (err) {
            showToast(`Provider switch error: ${err.message}`, 'error');
        }
    }

    // ── Ollama Preset Model Management ──
    function renderOllamaModelChips() {
        if (!els.ollamaModelsChips) return;
        const oCfg = state.providers?.ollama || {};
        let models = Array.isArray(oCfg.custom_models) ? oCfg.custom_models : ['llama3.3:latest', 'deepseek-r1:14b', 'qwen2.5-coder:32b', 'mistral:latest'];
        const currentActive = (els.inputOllamaModel?.value?.trim() || oCfg.default_model || '').toLowerCase();

        els.ollamaModelsChips.innerHTML = models.map(m => {
            const isActive = m.toLowerCase() === currentActive;
            return `
                <div class="model-chip ${isActive ? 'active' : ''}" data-model="${escapeHtml(m)}">
                    <span class="chip-name">${escapeHtml(m)}</span>
                    <span class="chip-remove" data-remove-model="${escapeHtml(m)}" title="Hapus model dari preset">✕</span>
                </div>
            `;
        }).join('');

        els.ollamaModelsChips.querySelectorAll('.chip-name').forEach(span => {
            span.addEventListener('click', () => {
                const parent = span.closest('.model-chip');
                const model = parent.getAttribute('data-model');
                if (els.inputOllamaModel) {
                    els.inputOllamaModel.value = model;
                    renderOllamaModelChips();
                }
            });
        });

        els.ollamaModelsChips.querySelectorAll('.chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const m = btn.getAttribute('data-remove-model');
                removeOllamaModelPreset(m);
            });
        });
    }

    function removeOllamaModelPreset(modelName) {
        if (!state.providers.ollama) state.providers.ollama = {};
        let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : ['llama3.3:latest', 'deepseek-r1:14b', 'qwen2.5-coder:32b', 'mistral:latest'];
        state.providers.ollama.custom_models = models.filter(m => m !== modelName);
        renderOllamaModelChips();
        saveOllama(true);
        showToast(`Model "${modelName}" dihapus dari preset.`, 'info');
    }

    function addOllamaModelPreset() {
        const val = els.inputOllamaModel?.value?.trim();
        if (!val) {
            showToast('Ketik nama model terlebih dahulu!', 'warning');
            els.inputOllamaModel?.focus();
            return;
        }
        if (!state.providers.ollama) state.providers.ollama = {};
        let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : ['llama3.3:latest', 'deepseek-r1:14b', 'qwen2.5-coder:32b', 'mistral:latest'];
        if (!models.includes(val)) {
            models.push(val);
            state.providers.ollama.custom_models = models;
            renderOllamaModelChips();
            saveOllama(true);
            showToast(`Model "${val}" berhasil ditambahkan ke preset!`, 'success');
        } else {
            showToast(`Model "${val}" sudah ada di preset.`, 'info');
        }
    }

    // ── 9Router Preset Model Management ──
    function render9RouterModelChips() {
        if (!els.r9ModelsChips) return;
        const rCfg = state.providers?.['9router'] || {};
        let models = Array.isArray(rCfg.custom_models) ? rCfg.custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        const currentActive = (els.input9RouterModel?.value?.trim() || rCfg.default_model || '').toLowerCase();

        els.r9ModelsChips.innerHTML = models.map(m => {
            const isActive = m.toLowerCase() === currentActive;
            return `
                <div class="model-chip ${isActive ? 'active' : ''}" data-model="${escapeHtml(m)}">
                    <span class="chip-name">${escapeHtml(m)}</span>
                    <span class="chip-remove" data-remove-model="${escapeHtml(m)}" title="Hapus model dari preset">✕</span>
                </div>
            `;
        }).join('');

        els.r9ModelsChips.querySelectorAll('.chip-name').forEach(span => {
            span.addEventListener('click', () => {
                const parent = span.closest('.model-chip');
                const model = parent.getAttribute('data-model');
                if (els.input9RouterModel) {
                    els.input9RouterModel.value = model;
                    render9RouterModelChips();
                }
            });
        });

        els.r9ModelsChips.querySelectorAll('.chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const m = btn.getAttribute('data-remove-model');
                remove9RouterModelPreset(m);
            });
        });
    }

    function remove9RouterModelPreset(modelName) {
        if (!state.providers['9router']) state.providers['9router'] = {};
        let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        state.providers['9router'].custom_models = models.filter(m => m !== modelName);
        render9RouterModelChips();
        save9Router(true);
        showToast(`Model "${modelName}" dihapus dari preset.`, 'info');
    }

    function add9RouterModelPreset() {
        const val = els.input9RouterModel?.value?.trim();
        if (!val) {
            showToast('Ketik nama model terlebih dahulu!', 'warning');
            els.input9RouterModel?.focus();
            return;
        }
        if (!state.providers['9router']) state.providers['9router'] = {};
        let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        if (!models.includes(val)) {
            models.push(val);
            state.providers['9router'].custom_models = models;
            render9RouterModelChips();
            save9Router(true);
            showToast(`Model "${val}" berhasil ditambahkan ke preset!`, 'success');
        } else {
            showToast(`Model "${val}" sudah ada di preset.`, 'info');
        }
    }

    // ── Test & Save Ollama ──
    async function testOllama() {
        const host = els.inputOllamaHost?.value?.trim() || 'http://127.0.0.1:11434';
        if (els.ollamaPingTxt) els.ollamaPingTxt.textContent = 'Pinging...';
        if (els.ollamaPingPill) els.ollamaPingPill.className = 'panel-status-pill';

        try {
            const res = await fetch(`${API_BASE}/auth/router/test-provider`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: 'ollama', host })
            });
            const data = await res.json();

            if (data.success && data.online) {
                if (els.ollamaPingTxt) els.ollamaPingTxt.textContent = `Online (${data.count} models)`;
                if (els.ollamaPingPill) els.ollamaPingPill.className = 'panel-status-pill online';
                showToast(`Ollama is Online at ${host}! Ditemukan ${data.count} model.`, 'success');

                // Merge detected models
                if (Array.isArray(data.models) && data.models.length > 0) {
                    if (!state.providers.ollama) state.providers.ollama = {};
                    let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : [];
                    data.models.forEach(m => {
                        if (!models.includes(m)) models.push(m);
                    });
                    state.providers.ollama.custom_models = models;
                    if (!els.inputOllamaModel?.value?.trim()) {
                        els.inputOllamaModel.value = data.models[0];
                    }
                    renderOllamaModelChips();
                    saveOllama(true);
                }
            } else {
                if (els.ollamaPingTxt) els.ollamaPingTxt.textContent = 'Offline';
                if (els.ollamaPingPill) els.ollamaPingPill.className = 'panel-status-pill offline';
                showToast(`Ollama unreachable at ${host}: ${data.error || 'Connection failed'}`, 'error');
            }
        } catch (err) {
            showToast(`Ollama test error: ${err.message}`, 'error');
        }
    }

    async function saveOllama(silent = false) {
        const host = els.inputOllamaHost?.value?.trim() || 'http://127.0.0.1:11434';
        const default_model = els.inputOllamaModel?.value?.trim() || 'llama3.3:latest';

        if (!state.providers.ollama) state.providers.ollama = {};
        let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : ['llama3.3:latest', 'deepseek-r1:14b', 'qwen2.5-coder:32b', 'mistral:latest'];
        if (default_model && !models.includes(default_model)) {
            models.push(default_model);
        }
        state.providers.ollama.host = host;
        state.providers.ollama.default_model = default_model;
        state.providers.ollama.custom_models = models;

        try {
            const res = await fetch(`${API_BASE}/auth/router/provider-config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    active_provider: 'ollama',
                    ollama: { host, default_model, custom_models: models }
                })
            });
            const data = await res.json();
            if (data.success) {
                renderOllamaModelChips();
                if (!silent) showToast(`Ollama tersimpan! Model Aktif: ${default_model}`, 'success');
                await syncAccounts(true);
            }
        } catch (err) {
            if (!silent) showToast(`Save error: ${err.message}`, 'error');
        }
    }

    // ── Test & Save 9Router ──
    async function test9Router() {
        const host = els.input9RouterHost?.value?.trim() || 'http://127.0.0.1:20128';
        const api_key = els.input9RouterKey?.value?.trim() || '';

        if (els.r9PingTxt) els.r9PingTxt.textContent = 'Pinging...';
        if (els.r9PingPill) els.r9PingPill.className = 'panel-status-pill';

        try {
            const res = await fetch(`${API_BASE}/auth/router/test-provider`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: '9router', host, api_key })
            });
            const data = await res.json();

            if (data.success && data.online) {
                if (els.r9PingTxt) els.r9PingTxt.textContent = `Online (${data.count} models)`;
                if (els.r9PingPill) els.r9PingPill.className = 'panel-status-pill online';
                showToast(`9Router is Online! Ditemukan ${data.count} model.`, 'success');

                if (Array.isArray(data.models) && data.models.length > 0) {
                    if (!state.providers['9router']) state.providers['9router'] = {};
                    let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : [];
                    data.models.forEach(m => {
                        if (!models.includes(m)) models.push(m);
                    });
                    state.providers['9router'].custom_models = models;
                    if (!els.input9RouterModel?.value?.trim()) {
                        els.input9RouterModel.value = data.models[0];
                    }
                    render9RouterModelChips();
                    save9Router(true);
                }
            } else {
                if (els.r9PingTxt) els.r9PingTxt.textContent = 'Offline';
                if (els.r9PingPill) els.r9PingPill.className = 'panel-status-pill offline';
                showToast(`9Router unreachable at ${host}: ${data.error || 'Connection failed'}`, 'error');
            }
        } catch (err) {
            showToast(`9Router test error: ${err.message}`, 'error');
        }
    }

    async function save9Router(silent = false) {
        const host = els.input9RouterHost?.value?.trim() || 'http://127.0.0.1:20128';
        const api_key = els.input9RouterKey?.value?.trim() || '';
        const default_model = els.input9RouterModel?.value?.trim() || 'clinepass/cline-pass/glm-5.2';

        if (!state.providers['9router']) state.providers['9router'] = {};
        let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        if (default_model && !models.includes(default_model)) {
            models.push(default_model);
        }
        state.providers['9router'].host = host;
        state.providers['9router'].api_key = api_key;
        state.providers['9router'].default_model = default_model;
        state.providers['9router'].custom_models = models;

        try {
            const res = await fetch(`${API_BASE}/auth/router/provider-config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    active_provider: '9router',
                    '9router': { host, api_key, default_model, custom_models: models }
                })
            });
            const data = await res.json();
            if (data.success) {
                render9RouterModelChips();
                if (!silent) showToast(`9Router tersimpan! Model Aktif: ${default_model}`, 'success');
                await syncAccounts(true);
            }
        } catch (err) {
            if (!silent) showToast(`Save error: ${err.message}`, 'error');
        }
    }

    // ── Update Metric Numbers & Badges ──
    function updateStatsUI() {
        if (els.statTotal) els.statTotal.textContent = state.totalAccounts;
        if (els.statMax) els.statMax.textContent = `/ ${state.maxAccounts} max`;
        if (els.statActiveEmail) {
            els.statActiveEmail.textContent = state.activeEmail;
            els.statActiveEmail.title = state.activeEmail;
        }
        if (els.statHealth) els.statHealth.textContent = `${state.healthyCount} Ready`;
        if (els.statCooldownSub) {
            els.statCooldownSub.textContent = state.cooldownCount > 0 ? `${state.cooldownCount} in cooldown` : '0 cooldown';
            els.statCooldownSub.style.color = state.cooldownCount > 0 ? '#f87171' : 'var(--text-muted)';
        }
        if (els.strategySelect) {
            els.strategySelect.value = state.rotationMode;
        }

        // Filter Counts
        const activeCount = state.accounts.filter(a => a.is_active || a.id === state.activeAccountId).length;
        if (els.tabAll) els.tabAll.textContent = state.totalAccounts;
        if (els.tabActive) els.tabActive.textContent = activeCount;
        if (els.tabReady) els.tabReady.textContent = state.healthyCount;
        if (els.tabCooldown) els.tabCooldown.textContent = state.cooldownCount;
    }

    // ── Render Accounts List ──
    function renderAccountsList() {
        if (!els.accountsList) return;

        let filtered = [...state.accounts];
        const now = Date.now();

        if (state.filter === 'active') {
            filtered = filtered.filter(a => a.is_active || a.id === state.activeAccountId);
        } else if (state.filter === 'ready') {
            filtered = filtered.filter(a => !(a.is_active || a.id === state.activeAccountId) && a.status !== 'cooldown');
        } else if (state.filter === 'cooldown') {
            filtered = filtered.filter(a => a.status === 'cooldown' || (a.cooldown_until && a.cooldown_until > now));
        }

        if (state.searchQuery) {
            const q = state.searchQuery.toLowerCase();
            filtered = filtered.filter(a => (a.email && a.email.toLowerCase().includes(q)) || (a.name && a.name.toLowerCase().includes(q)));
        }

        if (filtered.length === 0) {
            if (state.accounts.length === 0) {
                els.accountsList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">☁️</div>
                        <h3>No Accounts in Local Pool</h3>
                        <p>Click <strong>Unduh Akun (Sync Cloud)</strong> to restore accounts from your Cloud Vault, or click <strong>Add Google Account</strong>.</p>
                    </div>
                `;
            } else {
                els.accountsList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <h3>No Matching Accounts</h3>
                        <p>No accounts found matching filter "${state.filter}" or search query.</p>
                    </div>
                `;
            }
            return;
        }

        els.accountsList.innerHTML = filtered.map((acc, idx) => {
            const isActive = acc.is_active || acc.id === state.activeAccountId;
            const isCooldown = acc.status === 'cooldown' || (acc.cooldown_until && acc.cooldown_until > now);
            const remainingSec = isCooldown ? (acc.cooldown_remaining_sec || Math.max(1, Math.ceil((acc.cooldown_until - now) / 1000))) : 0;

            let badgeHtml = '';
            if (isActive) {
                badgeHtml = `<span class="acc-badge badge-active">ACTIVE PRIMARY</span>`;
            } else if (isCooldown) {
                badgeHtml = `<span class="acc-badge badge-limit" data-cd-id="${acc.id}">LIMIT 429 (${remainingSec}s)</span>`;
            } else {
                badgeHtml = `<span class="acc-badge badge-ready">READY</span>`;
            }

            const email = acc.email || 'unknown@google.com';
            const initial = (acc.name || email).charAt(0).toUpperCase();
            const requests = acc.requests_count || 0;
            const errors = acc.errors_count || 0;
            const expires = formatTimeRemaining(acc.expires_at);

            return `
                <div class="account-card ${isActive ? 'is-active' : ''} ${isCooldown ? 'is-cooldown' : ''}">
                    <div class="acc-left">
                        <span class="acc-index">#${idx + 1}</span>
                        <div class="acc-avatar">${initial}</div>
                        <div class="acc-info">
                            <div class="acc-email-row">
                                <span class="acc-email" title="${escapeHtml(email)}">${escapeHtml(email)}</span>
                                ${badgeHtml}
                            </div>
                            <div class="acc-meta">
                                <div class="acc-meta-item">Requests: <span>${requests}</span></div>
                                <div class="acc-meta-item">Errors: <span>${errors}</span></div>
                                <div class="acc-meta-item">Token: <span>${expires}</span></div>
                            </div>
                        </div>
                    </div>
                    <div class="acc-right">
                        ${isActive ? `
                            <button class="btn-card btn-card-active" disabled>Primary</button>
                        ` : `
                            <button class="btn-card btn-card-select" data-action="select" data-id="${acc.id}" data-email="${escapeHtml(email)}">Set Active</button>
                        `}
                        <button class="btn-card btn-card-test" data-action="test" data-id="${acc.id}" data-email="${escapeHtml(email)}">Test Token</button>
                        <button class="btn-card-delete" data-action="delete" data-id="${acc.id}" data-email="${escapeHtml(email)}" title="Delete Account">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Wire Action Buttons
        els.accountsList.querySelectorAll('[data-action="select"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const email = btn.getAttribute('data-email');
                btn.disabled = true;
                btn.textContent = 'Switching...';
                await selectAccount(id, email);
            });
        });

        els.accountsList.querySelectorAll('[data-action="test"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const email = btn.getAttribute('data-email');
                btn.disabled = true;
                btn.textContent = 'Testing...';
                await testAccount(id, email, btn);
            });
        });

        els.accountsList.querySelectorAll('[data-action="delete"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const email = btn.getAttribute('data-email');
                await deleteAccount(id, email);
            });
        });
    }

    // ── Flowork OS Login via auth.floworkos.com ──
    async function startFloworkLogin() {
        try {
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Connecting to auth.floworkos.com portal...';
            showToast('Opening auth.floworkos.com login portal...', 'info');

            const res = await fetch(`${API_BASE}/auth/login-url`);
            const data = await res.json();

            if (data.gate_url) {
                window.open(data.gate_url, '_blank');
                if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Awaiting authorization in browser window...';

                if (state.authPolling) clearInterval(state.authPolling);
                let pollCount = 0;

                state.authPolling = setInterval(async () => {
                    pollCount++;
                    await syncAccounts(true);
                    if (state.authenticated) {
                        clearInterval(state.authPolling);
                        state.authPolling = null;
                        showToast(`🎉 Sovereign Gate Unlocked! Welcome @${state.user?.username || 'operator'}`, 'success');
                    } else if (pollCount > 90) {
                        clearInterval(state.authPolling);
                        state.authPolling = null;
                        if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Authorization session timed out. Click to retry.';
                    }
                }, 1500);
            }
        } catch (err) {
            showToast(`Auth error: ${err.message}`, 'error');
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = `Error: ${err.message}`;
        }
    }

    // ── Submit Flowork Token Manually ──
    async function submitManualToken() {
        const token = (els.inputManualToken?.value || '').trim();
        if (!token) {
            showToast('Please paste a valid session token', 'error');
            return;
        }

        try {
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Verifying token with auth.floworkos.com...';
            const res = await fetch(`${API_BASE}/auth/set-token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });
            const data = await res.json();

            if (data.success) {
                showToast(`Token verified! Loaded ${data.cloud_accounts || 0} Cloud Vault accounts.`, 'success');
                if (els.inputManualToken) els.inputManualToken.value = '';
                await syncAccounts();
            } else {
                showToast(data.error || 'Token verification failed', 'error');
                if (els.lockStatusTxt) els.lockStatusTxt.textContent = `Error: ${data.error || 'Invalid token'}`;
            }
        } catch (err) {
            showToast(`Submit error: ${err.message}`, 'error');
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = `Error: ${err.message}`;
        }
    }

    // ── Download Accounts from Cloud Vault ──
    async function syncCloudVault() {
        if (!state.authenticated) {
            showToast('Connect to Flowork OS first to sync Cloud Vault', 'error');
            return;
        }

        try {
            showToast('☁️ Downloading accounts from auth.floworkos.com Cloud Vault...', 'info');
            if (els.btnSyncCloud) {
                els.btnSyncCloud.disabled = true;
                els.btnSyncCloud.querySelector('span:last-child').textContent = 'Downloading...';
            }

            const res = await fetch(`${API_BASE}/auth/router/sync-cloud`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                showToast(`☁️ Cloud Vault Synced: ${data.count} accounts downloaded!`, 'success');
                await syncAccounts();
            } else {
                showToast(`Cloud Sync failed: ${data.error || 'Unknown error'}`, 'error');
            }
        } catch (err) {
            showToast(`Cloud Sync error: ${err.message}`, 'error');
        } finally {
            if (els.btnSyncCloud) {
                els.btnSyncCloud.disabled = false;
                els.btnSyncCloud.querySelector('span:last-child').textContent = 'Unduh Akun (Sync Cloud)';
            }
        }
    }

    // ── Sign Out ──
    async function logout() {
        if (!confirm('Are you sure you want to sign out from auth.floworkos.com? The router will be locked.')) return;
        try {
            const res = await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Signed out. Sovereign Router locked.', 'info');
                await syncAccounts();
            }
        } catch (err) {
            showToast(`Logout error: ${err.message}`, 'error');
        }
    }

    // ── Account Management Actions ──
    async function addGoogleAccount() {
        if (!state.authenticated) {
            showToast('Please connect to Flowork OS first', 'error');
            return;
        }

        try {
            showToast('Opening Google OAuth in browser...', 'info');
            const res = await fetch(`${API_BASE}/auth/router/login-url?open=1`);
            const data = await res.json();

            if (!data.success || !data.loginUrl) {
                throw new Error(data.error || 'Failed to get authorization URL');
            }

            window.open(data.loginUrl, '_blank');

            if (state.oauthPolling) clearInterval(state.oauthPolling);
            const initialCount = state.totalAccounts;
            let pollTicks = 0;

            state.oauthPolling = setInterval(async () => {
                pollTicks++;
                await syncAccounts(true);
                if (state.totalAccounts > initialCount) {
                    clearInterval(state.oauthPolling);
                    state.oauthPolling = null;
                    showToast('🎉 New Google account linked to matrix pool!', 'success');
                } else if (pollTicks > 60) {
                    clearInterval(state.oauthPolling);
                    state.oauthPolling = null;
                }
            }, 2000);
        } catch (err) {
            showToast(`OAuth Error: ${err.message}`, 'error');
        }
    }

    async function selectAccount(id, email) {
        try {
            const res = await fetch(`${API_BASE}/auth/router/select-account`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Switched active primary to: ${email}`, 'success');
                await syncAccounts(true);
            } else {
                showToast(data.error || 'Failed to switch account', 'error');
            }
        } catch (err) {
            showToast(`Error: ${err.message}`, 'error');
        }
    }

    async function testAccount(id, email, btn) {
        try {
            const res = await fetch(`${API_BASE}/auth/router/test-account`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`⚡ Account ${email}: Token valid & active!`, 'success');
            } else {
                showToast(`⚠️ Account ${email}: ${data.error || 'Token check required'}`, 'error');
            }
            await syncAccounts(true);
        } catch (err) {
            showToast(`Test error: ${err.message}`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Test Token';
            }
        }
    }

    async function deleteAccount(id, email) {
        if (!confirm(`Are you sure you want to remove ${email} from the rotator pool?`)) return;
        try {
            const res = await fetch(`${API_BASE}/auth/router/remove-account`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Removed ${email} from pool`, 'info');
                await syncAccounts(true);
            } else {
                showToast(data.error || 'Failed to remove account', 'error');
            }
        } catch (err) {
            showToast(`Delete error: ${err.message}`, 'error');
        }
    }

    async function clearAllCooldowns() {
        try {
            const res = await fetch(`${API_BASE}/auth/router/clear-cooldown`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast(`Cleared cooldowns for ${data.cleared_count || 0} accounts`, 'success');
                await syncAccounts(true);
            }
        } catch (err) {
            showToast(`Failed: ${err.message}`, 'error');
        }
    }

    async function setRotationMode(mode) {
        try {
            const res = await fetch(`${API_BASE}/auth/router/set-rotation-mode`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            const data = await res.json();
            if (data.success) {
                state.rotationMode = mode;
                showToast(`Rotation strategy set to: ${mode}`, 'info');
            }
        } catch (err) {
            showToast(`Strategy error: ${err.message}`, 'error');
        }
    }

    // ── Setup Event Listeners ──
    function initEvents() {
        // Connect to Flowork OS buttons
        if (els.btnLockLogin) els.btnLockLogin.addEventListener('click', startFloworkLogin);
        if (els.btnHeaderConnect) els.btnHeaderConnect.addEventListener('click', startFloworkLogin);

        // Manual token
        if (els.btnSubmitToken) els.btnSubmitToken.addEventListener('click', submitManualToken);
        if (els.inputManualToken) {
            els.inputManualToken.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') submitManualToken();
            });
        }
        if (els.btnLogout) els.btnLogout.addEventListener('click', logout);

        // Provider Switcher Tabs
        document.querySelectorAll('.provider-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const provId = tab.getAttribute('data-provider');
                if (provId) switchActiveProvider(provId);
            });
        });

        // Ollama panel actions
        if (els.btnTestOllama) els.btnTestOllama.addEventListener('click', testOllama);
        if (els.btnSaveOllama) els.btnSaveOllama.addEventListener('click', () => saveOllama(false));
        if (els.btnAddOllamaModel) els.btnAddOllamaModel.addEventListener('click', addOllamaModelPreset);
        if (els.inputOllamaModel) {
            els.inputOllamaModel.addEventListener('input', () => {
                renderOllamaModelChips();
            });
            els.inputOllamaModel.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    addOllamaModelPreset();
                }
            });
        }

        // 9Router panel actions
        if (els.btnTest9Router) els.btnTest9Router.addEventListener('click', test9Router);
        if (els.btnSave9Router) els.btnSave9Router.addEventListener('click', () => save9Router(false));
        if (els.btnAdd9RouterModel) els.btnAdd9RouterModel.addEventListener('click', add9RouterModelPreset);
        if (els.input9RouterModel) {
            els.input9RouterModel.addEventListener('input', () => {
                render9RouterModelChips();
            });
            els.input9RouterModel.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    add9RouterModelPreset();
                }
            });
        }

        // Toolbar actions
        if (els.btnSyncCloud) els.btnSyncCloud.addEventListener('click', syncCloudVault);
        if (els.btnAddAccount) els.btnAddAccount.addEventListener('click', addGoogleAccount);
        if (els.btnRefreshPool) {
            els.btnRefreshPool.addEventListener('click', () => {
                showToast('Refreshing pool status...', 'info');
                syncAccounts();
            });
        }
        if (els.btnClearCooldown) els.btnClearCooldown.addEventListener('click', clearAllCooldowns);

        if (els.strategySelect) {
            els.strategySelect.addEventListener('change', (e) => {
                setRotationMode(e.target.value);
            });
        }

        // Filter Tabs
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                state.filter = tab.getAttribute('data-filter') || 'all';
                renderAccountsList();
            });
        });

        // Search Input
        if (els.searchInput) {
            els.searchInput.addEventListener('input', (e) => {
                state.searchQuery = e.target.value.trim();
                if (els.searchClearBtn) {
                    els.searchClearBtn.classList.toggle('hidden', state.searchQuery.length === 0);
                }
                renderAccountsList();
            });
        }

        if (els.searchClearBtn) {
            els.searchClearBtn.addEventListener('click', () => {
                if (els.searchInput) els.searchInput.value = '';
                state.searchQuery = '';
                els.searchClearBtn.classList.add('hidden');
                renderAccountsList();
            });
        }

        // Live Cooldown Second-by-Second Countdown
        setInterval(() => {
            const now = Date.now();
            let hasChanged = false;
            document.querySelectorAll('[data-cd-id]').forEach(badge => {
                const id = badge.getAttribute('data-cd-id');
                const acc = state.accounts.find(a => a.id === id);
                if (acc && acc.cooldown_until) {
                    const remaining = Math.max(0, Math.ceil((acc.cooldown_until - now) / 1000));
                    if (remaining > 0) {
                        badge.textContent = `LIMIT 429 (${remaining}s)`;
                    } else {
                        hasChanged = true;
                    }
                }
            });
            if (hasChanged) syncAccounts(true);
        }, 1000);

        // Periodic Background Sync (every 6s)
        setInterval(() => syncAccounts(true), 6000);
    }

    // Initialize
    initEvents();
    syncAccounts();
})();
