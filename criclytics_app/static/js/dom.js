/* Shared text-only DOM helpers. No provider string enters an HTML sink. */
(function () {
  'use strict';
  function node(tag, text, className) {
    const item = document.createElement(tag);
    if (text !== undefined && text !== null) item.textContent = String(text);
    if (className) item.className = className;
    return item;
  }
  function display(value) { return value === null || value === undefined || value === '' ? '\u2014' : String(value); }
  window.CriclyticsDOM = Object.freeze({node, display});
}());
