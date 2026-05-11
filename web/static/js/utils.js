/**
 * utils.js — вспомогательные функции
 */

/**
 * Экранирует HTML-спецсимволы для защиты от XSS
 */
export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Копирует текст в буфер обмена
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // Fallback для старых браузеров
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const success = document.execCommand("copy");
    document.body.removeChild(textarea);
    return success;
  } catch (err) {
    console.error("Copy failed:", err);
    return false;
  }
}

/**
 * Debounce — откладывает выполнение функции
 */
export function debounce(fn, ms) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), ms);
  };
}

/**
 * Показывает toast-уведомление
 */
export function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // Авто-удаление через 3 секунды
  setTimeout(() => {
    toast.classList.add("toast--exit");
    setTimeout(() => toast.remove(), 200);
  }, 3000);
}

/**
 * Форматирует confidence (0.92 → "92%")
 */
export function formatConfidence(value) {
  return `${Math.round(value * 100)}%`;
}

/**
 * Извлекает домен из ID карточки ("CS-CONCEPT-009" → "cs")
 */
export function getDomainFromId(id) {
  const match = id.match(/^([A-Z]+)-/);
  if (!match) return "glb";
  const domain = match[1].toLowerCase();
  if (domain === "cs") return "cs";
  if (domain === "arch") return "arch";
  if (domain === "proc") return "proc";
  return "glb";
}

/**
 * Плавный скролл к низу элемента
 */
export function scrollToBottom(element, smooth = true) {
  if (!element) return;
  element.scrollTo({
    top: element.scrollHeight,
    behavior: smooth ? "smooth" : "auto",
  });
}

/**
 * Генерирует уникальный ID для сообщения
 */
export function generateId() {
  return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Форматирует timestamp в читаемый вид
 */
export function formatTime(timestamp) {
  const date = new Date(timestamp);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}
