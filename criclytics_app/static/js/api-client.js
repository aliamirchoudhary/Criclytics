/* Only in-flight GET requests are shared. Failures and completed data are not cached. */
(function () {
  'use strict';
  if (window.CriclyticsAPI) return;
  const config = window.CRICLYTICS_CONFIG;
  const pending = new Map();
  async function request(path) {
    if (!config || typeof config.apiBase !== 'string' || !path.startsWith('/api/') || path.startsWith('//')) throw new Error('API configuration unavailable');
    const key = config.apiBase + path;
    if (pending.has(key)) return pending.get(key);
    const task = (async () => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await fetch(key, {headers: {Accept:'application/json'}, signal:controller.signal, credentials:'omit', cache:'no-store'});
        if (!response.ok) { const error = new Error('Request unavailable'); error.kind = response.status === 404 ? 'not-found' : 'error'; throw error; }
        return await response.json();
      } finally { clearTimeout(timeout); }
    })();
    pending.set(key, task);
    try { return await task; } finally { pending.delete(key); }
  }
  window.CriclyticsAPI = Object.freeze({request});
}());
