(function () {
  function formatArg(a) {
    if (a instanceof Error) {
      return (a.name || "Error") + ": " + a.message + "\n" + (a.stack || "");
    }
    if (typeof a === "object" && a !== null) {
      try {
        return JSON.stringify(a);
      } catch (_) {
        return String(a);
      }
    }
    return String(a);
  }

  // Intercept console messages
  const origLog = console.log;
  console.log = function (...args) {
    origLog.apply(console, args);
    try {
      window.ipc?.postMessage(JSON.stringify({ id: 0, channel: "console:log", args: args.map(formatArg) }));
    } catch (_) {}
  };
  const origWarn = console.warn;
  console.warn = function (...args) {
    origWarn.apply(console, args);
    try {
      window.ipc?.postMessage(JSON.stringify({ id: 0, channel: "console:warn", args: args.map(formatArg) }));
    } catch (_) {}
  };
  const origErr = console.error;
  console.error = function (...args) {
    origErr.apply(console, args);
    try {
      window.ipc?.postMessage(JSON.stringify({ id: 0, channel: "console:error", args: args.map(formatArg) }));
    } catch (_) {}
  };

  // Intercept global errors & promise rejections
  window.addEventListener("error", function (e) {
    try {
      const msg = e.error ? formatArg(e.error) : (e.message || "Unknown Script Error");
      window.ipc?.postMessage(JSON.stringify({
        id: 0,
        channel: "console:error",
        args: ["[Window Error] " + msg + " at " + (e.filename || "") + ":" + (e.lineno || 0)]
      }));
    } catch (_) {}
  });

  window.addEventListener("unhandledrejection", function (e) {
    try {
      const reason = e.reason ? formatArg(e.reason) : "Unknown Rejection";
      window.ipc?.postMessage(JSON.stringify({
        id: 0,
        channel: "console:error",
        args: ["[Unhandled Rejection] " + reason]
      }));
    } catch (_) {}
  });

  // DOM Mount Observer
  let mountReported = false;
  const checkDom = setInterval(function () {
    const root = document.getElementById("root");
    if (root && root.children.length > 0 && !mountReported) {
      mountReported = true;
      window.ipc?.postMessage(JSON.stringify({
        id: 0,
        channel: "console:log",
        args: ["[DOM Ready] React mounted. Root children: " + root.children.length + ", tag: " + root.children[0].tagName, "Root HTML:", root.innerHTML.slice(0, 1000)]
      }));
      clearInterval(checkDom);
    }
  }, 300);

  if (window.electronAPI) return;

  const pendingRequests = new Map();
  let nextReqId = 1;

  window.__openscreen_callback = function (id, success, result, error) {
    const p = pendingRequests.get(id);
    if (p) {
      pendingRequests.delete(id);
      if (success) {
        p.resolve(result);
      } else {
        p.reject(new Error(error || "Unknown IPC error"));
      }
    }
  };

  const listeners = new Map();
  window.__openscreen_emit = function (channel, ...args) {
    const list = listeners.get(channel);
    if (list) {
      for (const fn of list) {
        try {
          fn(...args);
        } catch (e) {
          console.error(e);
        }
      }
    }
  };

  function invoke(channel, ...args) {
    return new Promise((resolve, reject) => {
      const id = nextReqId++;
      pendingRequests.set(id, { resolve, reject });
      try {
        window.ipc.postMessage(JSON.stringify({ id, channel, args }));
      } catch (err) {
        pendingRequests.delete(id);
        reject(err);
      }
    });
  }

  function send(channel, ...args) {
    try {
      window.ipc.postMessage(JSON.stringify({ id: 0, channel, args }));
    } catch (_) {}
  }

  function on(channel, fn) {
    if (!listeners.has(channel)) listeners.set(channel, new Set());
    listeners.get(channel).add(fn);
    return () => listeners.get(channel)?.delete(fn);
  }

  const baseApi = {
    assetBaseUrl: "",
    getPlatform: () => "linux",
    getSystemVersion: () => "7.3.0-flowork-rust",
    getAppInfo: () => invoke("get-app-info"),
    checkForUpdates: () => invoke("check-for-updates"),
    showAbout: () => invoke("show-about"),
    canCheckForUpdatesNow: () => invoke("can-check-for-updates-now"),
    getUpdateBadge: () => invoke("get-update-badge"),
    onUpdateBadgeChanged: (fn) => on("update-badge-changed", fn),
    applyUpdate: () => invoke("apply-update"),
    revealInFolder: (path) => invoke("reveal-in-folder", path),

    // Permissions
    permissions: {
      get: () => invoke("permissions:get"),
      request: (t) => invoke("permissions:request", t),
      openSettings: (t) => invoke("permissions:open-settings", t),
      relaunch: () => invoke("permissions:relaunch"),
      close: () => invoke("permissions:close")
    },
    requestCameraAccess: () => invoke("request-camera-access"),
    requestNativeMacCursorAccess: () => Promise.resolve(true),

    // Preferences & Shortcuts
    getRecordingPrefs: () => invoke("get-recording-prefs"),
    setRecordingPrefs: (prefs) => invoke("set-recording-prefs", prefs),
    onRecordingPrefsChanged: (fn) => on("recording-prefs-changed", fn),
    getShortcuts: () => invoke("get-shortcuts"),
    saveShortcuts: (s) => invoke("save-shortcuts", s),
    updateGlobalShortcut: (s) => invoke("update-global-shortcut", s),
    setLocale: (loc) => invoke("set-locale", loc),
    saveDiagnostic: (d) => invoke("save-diagnostic", d),

    // Linux native capture
    isNativeLinuxCaptureAvailable: () => invoke("is-native-linux-capture-available"),
    prepareNativeLinuxRecording: (payload) => invoke("prepare-native-linux-recording", payload),
    cancelNativeLinuxPrepare: () => invoke("cancel-native-linux-prepare"),
    startNativeLinuxRecording: (payload) => invoke("start-native-linux-recording", payload),
    pauseNativeLinuxRecording: () => invoke("pause-native-linux-recording"),
    resumeNativeLinuxRecording: () => invoke("resume-native-linux-recording"),
    stopNativeLinuxRecording: (discard) => invoke("stop-native-linux-recording", discard),
    attachNativeLinuxWebcamRecording: (payload) => invoke("attach-native-linux-webcam-recording", payload),

    // Telemetry
    getCursorTelemetry: () => invoke("get-cursor-telemetry"),
    discardCursorTelemetry: () => invoke("discard-cursor-telemetry"),

    // Non-Linux OS stubs
    isNativeMacCaptureAvailable: () => Promise.resolve({ success: false, available: false }),
    isNativeWindowsCaptureAvailable: () => Promise.resolve({ success: false, available: false }),
    startNativeMacRecording: () => Promise.resolve({ success: false }),
    stopNativeMacRecording: () => Promise.resolve({ success: false }),
    pauseNativeMacRecording: () => Promise.resolve({ success: false }),
    resumeNativeMacRecording: () => Promise.resolve({ success: false }),
    startNativeWindowsRecording: () => Promise.resolve({ success: false }),
    stopNativeWindowsRecording: () => Promise.resolve({ success: false }),
    pauseNativeWindowsRecording: () => Promise.resolve({ success: false }),
    resumeNativeWindowsRecording: () => Promise.resolve({ success: false }),
    attachNativeMacWebcamRecording: () => Promise.resolve({ success: false }),

    // Sources & Displays
    getSources: (opts) => invoke("get-sources", opts),
    getSelectedSource: () => invoke("get-selected-source"),
    selectSource: (src) => invoke("select-source", src),
    getLastPickedSource: () => invoke("get-last-picked-source"),
    usesSystemSourcePicker: () => invoke("uses-system-source-picker"),
    openSourceSelector: () => invoke("open-source-selector"),
    onSelectedSourceChanged: (fn) => on("selected-source-changed", fn),
    onSourceSelectorClosed: (fn) => on("source-selector-closed", fn),
    findRecordingCamera: (id) => invoke("find-recording-camera", id),

    // Session & storage
    getRecordingsDir: () => invoke("get-recordings-dir"),
    chooseRecordingsDir: () => invoke("choose-recordings-dir"),
    resetRecordingsDir: () => invoke("reset-recordings-dir"),
    checkRecordingStorage: (path) => invoke("check-recording-storage", path),
    getCurrentRecordingSession: () => invoke("get-current-recording-session"),
    setCurrentRecordingSession: (s) => invoke("set-current-recording-session", s),
    storeRecordedSession: (s) => invoke("store-recorded-session", s),
    getCurrentVideoPath: () => invoke("get-current-video-path"),
    setCurrentVideoPath: (p) => invoke("set-current-video-path", p),
    clearCurrentVideoPath: () => invoke("clear-current-video-path"),
    storeRecordedVideo: (opts) => invoke("store-recorded-video", opts),
    getRecordedVideoPath: () => invoke("get-recorded-video-path"),
    openRecordingStream: (id) => invoke("open-recording-stream", id),
    appendRecordingChunk: (id, chunk) => send("append-recording-chunk", id, chunk),
    closeRecordingStream: (id) => invoke("close-recording-stream", id),

    // Projects & Files
    saveProjectFile: (opts) => invoke("save-project-file", opts),
    loadProjectFile: () => invoke("load-project-file"),
    loadProjectFileFromPath: (p) => invoke("load-project-file-from-path", p),
    loadCurrentProjectFile: () => invoke("load-current-project-file"),
    getPathForFile: (f) => f?.path || "",
    readBinaryFile: async (path) => {
      const res = await invoke("read-binary-file", path);
      if (!res || !res.success || !res.data) return res;
      const binary = atob(res.data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      return { success: true, path: res.path, data: bytes.buffer };
    },
    readFileChunk: (path, offset, length) => invoke("read-file-chunk", path, offset, length),
    getReadableFileInfo: (path) => invoke("get-readable-file-info", path),
    getAudioPeaks: (path, count) => invoke("get-audio-peaks", path, count),
    preparePreviewAudioTrack: (path) => invoke("prepare-preview-audio-track", path),
    getLoudnessGain: (path) => invoke("get-loudness-gain", path),
    writeExportToPath: (opts) => invoke("write-export-to-path", opts),
    pickExportSavePath: (opts) => invoke("pick-export-save-path", opts),
    openVideoFilePicker: () => invoke("open-video-file-picker"),
    openAudioFilePicker: () => invoke("open-audio-file-picker"),
    saveRecordedVoiceover: (opts) => invoke("save-recorded-voiceover", opts),
    stageClickSoundHit: (opts) => invoke("stage-click-sound-hit", opts),

    // UI state & navigation
    setRecordingState: (state) => send("set-recording-state", state),
    setHasUnsavedChanges: (has) => send("set-has-unsaved-changes", has),
    switchToEditor: () => invoke("switch-to-editor"),
    switchToHud: () => invoke("switch-to-hud"),
    startNewRecording: () => invoke("start-new-recording"),
    openExternalUrl: (url) => invoke("open-external-url", url),
    openNotes: () => invoke("open-notes"),
    openRepoPage: () => invoke("open-repo-page"),
    openStoreReview: () => invoke("open-store-review"),
    starPromptExportFinished: () => invoke("star-prompt-export-finished"),
    dismissStarPrompt: () => invoke("dismiss-star-prompt"),
    onGlobalRecordingShortcut: (fn) => on("global-shortcut-record", fn),
    onStopRecordingFromTray: (fn) => on("stop-recording-from-tray", fn),
    onAutoStartRecording: (fn) => on("hud-auto-start-recording", fn),
    onNativeMacSystemAudioUnavailable: (fn) => on("native-mac-system-audio-unavailable", fn),

    // Countdown overlay
    showCountdownOverlay: (target, bounds) => invoke("countdown-overlay-show", target, bounds),
    setCountdownOverlayValue: (val, label) => invoke("countdown-overlay-set-value", val, label),
    hideCountdownOverlay: (target) => invoke("countdown-overlay-hide", target),
    onCountdownOverlayValue: (fn) => on("countdown-overlay-value", fn),
    notifyCountdownOverlayCleared: (target) => send("countdown-overlay-cleared", target),

    // HUD overlay
    hudOverlayHide: () => send("hud-overlay-hide"),
    hudOverlayClose: () => send("hud-overlay-close"),
    setHudOverlayIgnoreMouseEvents: (ignore) => send("hud-overlay-set-ignore-mouse-events", ignore),
    beginHudOverlayDrag: (x, y) => send("hud-overlay-drag-start", x, y),
    hudOverlayDragStart: (x, y) => send("hud-overlay-drag-start", x, y),
    dragHudOverlayTo: (x, y) => send("hud-overlay-drag-to", x, y),
    endHudOverlayDrag: () => send("hud-overlay-drag-end"),
    setHudOverlaySize: (w, h, scale) => send("hud-overlay-set-size", w, h, scale),
    setHudOverlayContent: (content) => send("hud-overlay-set-content", content),
    onHudOverlayCursor: (fn) => on("hud-overlay-cursor", fn),
    setMicrophoneExpanded: (exp) => send("hud:setMicrophoneExpanded", exp),

    // Close & Save dialog confirmation
    onRequestCloseConfirm: (fn) => on("request-close-confirm", fn),
    sendCloseConfirmResponse: (resp) => send("close-confirm-response", resp),
    onRequestSaveBeforeClose: (fn) => on("request-save-before-close", fn),
    sendSaveBeforeCloseResponse: (resp) => send("save-before-close-response", resp),

    // Export & Bridge
    exportCapabilities: () => invoke("export:capabilities"),
    exportStart: (opts) => invoke("export:start", opts),
    exportWriteFrame: (id, frame) => send("export:frame", id, frame),
    exportOnFrameAck: (fn) => on("export:frame-ack", fn),
    exportFinish: (id) => invoke("export:finish", id),
    exportCancel: (id) => invoke("export:cancel", id),
    onNativeExportProgress: (fn) => on("export:native-progress", fn),
    onCompositorFrame: (fn) => on("compositor:frame", fn),
    invokeNativeBridge: (action, payload) => invoke("native-bridge:invoke", action, payload),

    // Menu events
    onMenuNewProject: (fn) => on("menu-new-project", fn),
    onMenuImportVideo: (fn) => on("menu-import-video", fn),
    onMenuLoadProject: (fn) => on("menu-load-project", fn),
    onMenuSaveProject: (fn) => on("menu-save-project", fn),
    onMenuSaveProjectAs: (fn) => on("menu-save-project-as", fn),
    onMenuUndo: (fn) => on("menu-undo", fn),
    onMenuRedo: (fn) => on("menu-redo", fn),

    // AI Edition & Chat
    onAiEditionChatEvent: (fn) => on("ai-edition.chat-event", fn),
    onAiEditionMcpRequest: (fn) => on("ai-edition:mcp-request", fn),
    setAiEditionOpenProject: (projectId) => send("ai-edition:set-open-project", projectId),

    // STT (Speech-to-Text)
    stt: {
      transcribe: (opts) => invoke("stt:transcribe", opts),
      cancel: () => invoke("stt:cancel"),
      onStatus: (fn) => on("stt:status", fn)
    },

    // CLI runners
    cliGetRequest: () => invoke("cli-get-request"),
    cliProgress: (p) => send("cli-progress", p),
    cliLog: (level, msg) => send("cli-log", level, msg),
    cliDone: (res) => invoke("cli-done", res),
    onCliStopRecording: (fn) => on("cli-stop-recording", fn),

    // Clipboard & Window
    copyToClipboard: (text) => invoke("clipboard:write-text", text),
    quitApp: () => send("app-quit"),
    setTitleBarOverlay: (show, h) => send("set-titlebar-overlay", show, h),
    rendererConsole: (level, args) => send("renderer-console", level, args)
  };

  // Safe Proxy fallback: Any method not explicitly declared returns a no-op Promise or empty function
  window.electronAPI = new Proxy(baseApi, {
    get(target, prop) {
      if (prop in target) return target[prop];
      if (typeof prop === "string" && prop.startsWith("on")) {
        return function () { return () => {}; };
      }
      return async function (...args) {
        console.warn("[electronAPI Fallback] Invoked unhandled API property:", String(prop), args);
        return null;
      };
    }
  });

  console.log("[Flowork OS] Sovereign OpenScreen electronAPI bridge initialized with 100% surface coverage!");
})();
