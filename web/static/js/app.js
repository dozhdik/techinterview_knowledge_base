import { initChat, sendMessage, clearChat } from "./chat.js";
import { debounce, showToast } from "./utils.js";


const htmlEl       = document.documentElement;
const themeToggle  = document.getElementById("theme-toggle");
const clearBtn     = document.getElementById("clear-btn");
const textarea     = document.getElementById("chat-input");
const sendBtn      = document.getElementById("send-btn");
let isSubmitting = false;
const sendIcon     = document.getElementById("send-icon");
const sendSpinner  = document.getElementById("send-spinner");
const messagesArea = document.getElementById("messages-area");
const welcomeEl    = document.getElementById("welcome-screen");


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


const resizeTextarea = debounce(() => {
  textarea.style.height = "auto";
  const maxHeight = 120;
  textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + "px";
}, 10);


function setSubmitState(loading) {
  isSubmitting = loading;
  sendBtn.disabled = loading || !textarea.value.trim();
  sendIcon.style.display    = loading ? "none"  : "block";
  sendSpinner.style.display = loading ? "block" : "none";
}

function updateSendBtn() {
  sendBtn.disabled = isSubmitting || !textarea.value.trim();
}


async function handleSubmit() {
  const question = textarea.value.trim();
  if (!question || isSubmitting) return;

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


function initKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      textarea.focus();
      textarea.select();
    }
  });

  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === "Escape") {
      textarea.value = "";
      resizeTextarea();
      updateSendBtn();
    }
  });
}


document.addEventListener("chat:example-click", (e) => {
  const { question } = e.detail;
  textarea.value = question;
  resizeTextarea();
  updateSendBtn();
  handleSubmit();
});


function init() {
  applyTheme(getStoredTheme());

  initChat(messagesArea, welcomeEl);

  themeToggle?.addEventListener("click", toggleTheme);

  clearBtn?.addEventListener("click", () => {
    clearChat();
    textarea.value = "";
    resizeTextarea();
    updateSendBtn();
    showToast("История очищена", "success");
  });

  sendBtn.addEventListener("click", handleSubmit);

  textarea.addEventListener("input", () => {
    resizeTextarea();
    updateSendBtn();
  });

  initKeyboardShortcuts();

  updateSendBtn();

  textarea.focus();
}

document.addEventListener("DOMContentLoaded", init);
