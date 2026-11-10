(function () {
  try {
    const s = document.createElement('script');
    s.src = chrome.runtime.getURL('stealth.js');
    (document.head || document.documentElement).prepend(s);
  } catch (e) {}
})();
