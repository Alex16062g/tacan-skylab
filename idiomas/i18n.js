import en from './en.js';
import es from './es.js';

const dictionaries = { en, es };
const storageKey = 'tacana-skylab-language';
const bindings = new WeakMap();
const targets = new Set();
const messages = new Map();
const lookup = new Map();
for (const dictionary of Object.values(dictionaries)) {
  for (const [key, value] of Object.entries(dictionary)) lookup.set(value, key);
}
const valid = value => value === 'en' || value === 'es';
let language = 'en';
try {
  const saved = localStorage.getItem(storageKey);
  if (valid(saved)) language = saved;
} catch { /* Language switching also works when storage is blocked. */ }
try {
  if (window.parent !== window && valid(window.parent.document.documentElement.lang)) {
    language = window.parent.document.documentElement.lang;
  }
} catch { /* A cross-origin host cannot set the embedded language. */ }

export const locale = () => language === 'en' ? 'en-US' : 'es-MX';
export const currentLanguage = () => language;

// Localize display labels received from scientific JSON without changing the data.
export function localize(value, depth = 0) {
  if (typeof value !== 'string' || depth > 5) return value;
  const key = lookup.get(value);
  if (key) return dictionaries[language][key];
  if (Object.hasOwn(dictionaries[language], value)) return dictionaries[language][value];
  const message = messages.get(value);
  return message ? format(message.key, message.values, depth + 1) : value;
}

function format(key, values, depth = 0) {
  const template = dictionaries[language][key] ?? en[key] ?? key;
  return template.replace(/\{(\d+)\}/g, (_, index) => String(localize(values[index] ?? '', depth + 1)));
}

export function t(key, values = []) {
  const result = format(key, values);
  if (values.length) {
    if (messages.size > 10000) messages.clear();
    messages.set(result, { key, values });
  }
  return result;
}

function bind(target, property, read, attribute = false) {
  let fields = bindings.get(target);
  if (!fields) {
    fields = new Map();
    bindings.set(target, fields);
    targets.add(new WeakRef(target));
  }
  const update = () => {
    const value = String(localize(read()) ?? '');
    if (attribute) {
      if (target.getAttribute(property) !== value) target.setAttribute(property, value);
    } else if (target[property] !== value) target[property] = value;
  };
  fields.set(property, update);
  update();
}

export const text = (target, read) => bind(target, 'textContent', read);
export const attr = (target, name, read) => bind(target, name, read, true);
export const title = read => text(document.querySelector('title'), read);
export function node(read) {
  const target = document.createTextNode('');
  text(target, read);
  return target;
}

export function translateTree(root = document) {
  const elements = [...root.querySelectorAll('[data-i18n], [data-i18n-attrs]')];
  if (root.matches?.('[data-i18n], [data-i18n-attrs]')) elements.unshift(root);
  for (const element of elements) {
    if (element.dataset.i18n) text(element, () => t(element.dataset.i18n));
    for (const pair of (element.dataset.i18nAttrs ?? '').split(';').filter(Boolean)) {
      const [attribute, key] = pair.split(':');
      attr(element, attribute, () => t(key));
    }
  }
}

// Markup is owned by the application; translations only fill text/attribute nodes.
export function html(target, markup) {
  target.innerHTML = markup;
  translateTree(target);
}

export function date(value, options = {}) {
  const instant = /^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00Z` : value;
  return new Intl.DateTimeFormat(locale(), { timeZone: 'UTC', ...options }).format(new Date(instant));
}

function updateButtons() {
  document.querySelectorAll('[data-language]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.language === language));
  });
}

export function setLanguage(next, persist = true) {
  if (!valid(next)) return;
  language = next;
  document.documentElement.lang = next;
  if (persist) {
    try { localStorage.setItem(storageKey, next); } catch { /* Optional persistence. */ }
  }
  for (const reference of targets) {
    const target = reference.deref();
    if (!target) { targets.delete(reference); continue; }
    if (!target.isConnected) continue;
    const fields = bindings.get(target);
    for (const update of fields.values()) update();
  }
  updateButtons();
  window.dispatchEvent(new CustomEvent('languagechange', { detail: { language: next } }));
  for (const frame of document.querySelectorAll('iframe')) {
    frame.contentWindow?.postMessage({ type: 'tacana-language', language: next }, location.origin);
  }
}

window.addEventListener('storage', event => {
  if (event.key === storageKey) setLanguage(valid(event.newValue) ? event.newValue : 'en', false);
});
window.addEventListener('message', event => {
  if (event.origin === location.origin && event.source === window.parent && event.data?.type === 'tacana-language') {
    setLanguage(event.data.language, false);
  }
});
document.documentElement.lang = language;
translateTree();
document.querySelectorAll('[data-language]').forEach(button => {
  button.addEventListener('click', () => setLanguage(button.dataset.language));
});
updateButtons();
