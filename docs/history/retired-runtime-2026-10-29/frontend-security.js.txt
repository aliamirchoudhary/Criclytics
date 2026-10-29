/* Transitional boundary for legacy HTML renderers; no remote sanitizer dependency. */
(function () {
  'use strict';
  const imageHosts = new Set(['cdn.jsdelivr.net', 'h.cricapi.com', 'upload.wikimedia.org',
    'a.espncdn.com', 'img1.hscicdn.com', 'images.icc-cricket.com', 'resources.pulse.icc-cricket.com']);
  window.safeImageUrl = function (value) {
    if (!value) return '';
    try {
      const url = new URL(String(value), location.origin);
      if (url.username || url.password) return '';
      if (url.origin === location.origin && url.pathname.startsWith('/static/')) return url.href;
      return url.protocol === 'https:' && imageHosts.has(url.hostname) ? url.href : '';
    } catch (_) { return ''; }
  };
  const native = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
  const adjacent = Element.prototype.insertAdjacentHTML;
  let cleaning = false;
  function clean(context, value) {
    if (!window.DOMPurify) throw new Error('HTML sanitizer is unavailable');
    cleaning = true;
    try {
      const holder = context.cloneNode(false);
      native.set.call(holder, String(value == null ? '' : value));
      DOMPurify.sanitize(holder, {IN_PLACE: true, FORBID_TAGS: ['script', 'iframe', 'object',
        'embed', 'base', 'form', 'svg', 'math'], ALLOW_UNKNOWN_PROTOCOLS: false});
      holder.querySelectorAll('img[src]').forEach(img => {
        const safe = safeImageUrl(img.getAttribute('src'));
        if (safe) img.setAttribute('src', safe);
        else img.removeAttribute('src');
      });
      return native.get.call(holder);
    } finally { cleaning = false; }
  }
  Object.defineProperty(Element.prototype, 'innerHTML', {
    configurable: true, enumerable: native.enumerable,
    get: native.get,
    set(value) { native.set.call(this, cleaning ? value : clean(this, value)); }
  });
  Element.prototype.insertAdjacentHTML = function (position, value) {
    const context = /^(beforebegin|afterend)$/i.test(position) ? this.parentElement : this;
    return adjacent.call(this, position, clean(context || this, value));
  };
  // Inline event attributes are stripped from dynamic markup. Image errors use
  // one fixed listener, never code constructed from player/country data.
  document.addEventListener('error', event => {
    const image = event.target;
    if (!(image instanceof HTMLImageElement)) return;
    image.style.display = 'none';
    if (image.nextElementSibling) image.nextElementSibling.style.display = 'flex';
  }, true);
})();
