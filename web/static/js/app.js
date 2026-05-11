/**
 * app.js — инициализация приложения, тема, keyboard shortcuts, auto-resize
 */

import { initChat, sendMessage, clearChat } from "./chat.js";
import { debounce, showToast } from "./utils.js";

// ---------------------------------------------------------------------------
// DOM-элементы
// ---------------------------------------------------------------------------

const htmlEl       = document.documentElement;
const themeToggle  = document.getElementById("theme-toggle");
const clearBtn     = document.getElementById("clear-btn");
const textarea     = document.getElementById("chat-input");
const sendBtn      = document.getElementById("send-btn");
const sendIcon     = document.getElementById("send-icon");
const sendSpinner  = document.getElementById("send-spinner");
const messagesArea = document.getElementById("messages-area");
const welcomeEl    = document.getElementById("welcome-screen");

// ---------------------------------------------------------------------------
// Тема
// ---------------------------------------------------------------------------

function getStoredTheme() {
  return localStorage.getItem("theme") || "light";
}

function applyTheme(theme) {
  htmlEl.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  updateThemeIcon(theme);
  updatePrismTheme(theme);
}

function updateThemeIcon(theme) {
  if (!themeToggle) return;
  // Иконки sun (светлая) и moon (тёмная) — переключаем видимость
  const sunIcon  = themeToggle.querySelector(".icon-sun");
  const moonIcon = themeToggle.querySelector(".icon-moon");
  if (sunIcon)  sunIcon.style.display  = theme === "dark"  ? "block" : "none";
  if (moonIcon) moonIcon.style.display = theme === "light" ? "block" : "none";
}

function updatePrismTheme(theme) {
  const lightLink = document.getElementById("prism-light");
  const darkLink  = document.getElementById("prism-dark");
  if (!lightLink || !darkLink) return;
  lightLink.disabled = theme === "dark";
  darkLink.disabled  = theme === "light";
}

function toggleTheme() {
  const current = htmlEl.getAttribute("data-theme") || "light";
  applyTheme(current === "light" ? "dark" : "light");
}

// ---------------------------------------------------------------------------
// Auto-resize textarea
// ---------------------------------------------------------------------------

const resizeTextarea = debounce(() => {
  textarea.style.height = "auto";
  const maxHeight = 120;
  textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + "px";
}, 10);

// ---------------------------------------------------------------------------
// Кнопка отправки — состояние
// ---------------------------------------------------------------------------

function setSubmitState(loading) {
  sendBtn.disabled = loading || !textarea.value.trim();
  sendIcon.style.display    = loading ? "none"  : "block";
  sendSpinner.style.display = loading ? "block" : "none";
}

function updateSendBtn() {
  sendBtn.disabled = !textarea.value.trim();
}

// ---------------------------------------------------------------------------
// Отправка
// ---------------------------------------------------------------------------

async function handleSubmit() {
  const question = textarea.value.trim();
  if (!question) return;

  textarea.value = "";
  resizeTextarea();
  setSubmitState(true);

  try {
    await sendMessage(question);
  } finally {
    setSubmitState(false);
    updateSendBtn();
    textarea.focus();
  }
}

// ---------------------------------------------------------------------------
// Keyboard shortcuts
// ---------------------------------------------------------------------------

function initKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl+K / Cmd+K — фокус на поле ввода
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      textarea.focus();
      textarea.select();
    }
  });

  textarea.addEventListener("keydown", (e) => {
    // Enter без Shift — отправить
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    // Escape — очистить поле
    if (e.key === "Escape") {
      textarea.value = "";
      resizeTextarea();
      updateSendBtn();
    }
  });
}

// ---------------------------------------------------------------------------
// Обработчик клика по карточке welcome screen
// ---------------------------------------------------------------------------

document.addEventListener("chat:example-click", (e) => {
  const { question } = e.detail;
  textarea.value = question;
  resizeTextarea();
  updateSendBtn();
  handleSubmit();
});

// ---------------------------------------------------------------------------
// Инициализация
// ---------------------------------------------------------------------------

function init() {
  // Применить сохранённую тему
  applyTheme(getStoredTheme());

  // Инициализировать чат
  initChat(messagesArea, welcomeEl);

  // Переключатель темы
  themeToggle?.addEventListener("click", toggleTheme);

  // Кнопка очистки
  clearBtn?.addEventListener("click", () => {
    clearChat();
    textarea.value = "";
    resizeTextarea();
    updateSendBtn();
    showToast("История очищена", "success");
  });

  // Кнопка отправки
  sendBtn.addEventListener("click", handleSubmit);

  // Textarea: resize + обновление кнопки
  textarea.addEventListener("input", () => {
    resizeTextarea();
    updateSendBtn();
  });

  // Keyboard shortcuts
  initKeyboardShortcuts();

  // Начальное состояние кнопки
  updateSendBtn();

  // Фокус на поле ввода
  textarea.focus();
}

// Запуск после загрузки DOM
document.addEventListener("DOMContentLoaded", init);
