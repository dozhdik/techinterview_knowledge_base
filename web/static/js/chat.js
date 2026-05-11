/**
 * chat.js — логика чата: история, рендеринг сообщений, fetch
 */

import {
  escapeHtml,
  copyToClipboard,
  showToast,
  formatConfidence,
  getDomainFromId,
  scrollToBottom,
  generateId,
  formatTime,
} from "./utils.js";

// ---------------------------------------------------------------------------
// Константы
// ---------------------------------------------------------------------------

const STORAGE_KEY = "techinterview_chat_history";
const MAX_HISTORY = 50;
const FETCH_TIMEOUT_MS = 15000;

// Примеры для welcome screen
const WELCOME_EXAMPLES = [
  { domain: "cs",   text: "Как устроена хеш-таблица и когда она перестаёт быть O(1)?" },
  { domain: "arch", text: "Спроектируй URL Shortener (TinyURL)" },
  { domain: "proc", text: "Как отвечать на behavioral-вопросы методом STAR?" },
  { domain: "cs",   text: "Чем BFS отличается от DFS и когда выбирать каждый?" },
  { domain: "arch", text: "SQL vs NoSQL — как выбрать для проекта?" },
  { domain: "proc", text: "Как подготовиться к System Design интервью?" },
];

// ---------------------------------------------------------------------------
// Состояние
// ---------------------------------------------------------------------------

let history = [];       // [{id, role, content, sources, confidence, timestamp}]
let isLoading = false;

// ---------------------------------------------------------------------------
// DOM-ссылки (инициализируются в init())
// ---------------------------------------------------------------------------

let messagesArea = null;
let welcomeScreen = null;

// ---------------------------------------------------------------------------
// История (localStorage)
// ---------------------------------------------------------------------------

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) history = JSON.parse(raw).slice(-MAX_HISTORY);
  } catch {
    history = [];
  }
}

function saveHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
  } catch {
    // localStorage может быть недоступен
  }
}

// ---------------------------------------------------------------------------
// Welcome screen
// ---------------------------------------------------------------------------

function renderWelcome() {
  if (!welcomeScreen) return;
  welcomeScreen.innerHTML = `
    <div class="welcome-hero">
      <div class="welcome-icon">📚</div>
      <h2 class="welcome-title">TechInterview Knowledge Base</h2>
      <p class="welcome-desc">
        Задай вопрос по алгоритмам, System Design или процессу собеседования —
        получи структурированный ответ из базы знаний.
      </p>
    </div>
    <div class="welcome-cards">
      ${WELCOME_EXAMPLES.map((ex) => `
        <button class="welcome-card" data-question="${escapeHtml(ex.text)}" type="button">
          <div class="welcome-card-domain domain-${ex.domain}">${domainLabel(ex.domain)}</div>
          <div class="welcome-card-text">${escapeHtml(ex.text)}</div>
        </button>
      `).join("")}
    </div>
  `;
  welcomeScreen.hidden = false;
}

function hideWelcome() {
  if (welcomeScreen) welcomeScreen.hidden = true;
}

function domainLabel(domain) {
  return { cs: "CS", arch: "Architecture", proc: "Process", glb: "Global" }[domain] ?? domain.toUpperCase();
}

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------

function renderSkeleton() {
  const el = document.createElement("div");
  el.className = "skeleton-message";
  el.id = "skeleton-loader";
  el.setAttribute("aria-label", "Загрузка ответа");
  el.innerHTML = `
    <div class="skeleton-avatar"></div>
    <div class="skeleton-body">
      <div class="skeleton-line skeleton-line--long"></div>
      <div class="skeleton-line skeleton-line--medium"></div>
      <div class="skeleton-line skeleton-line--short"></div>
    </div>
  `;
  messagesArea.appendChild(el);
  scrollToBottom(messagesArea);
  return el;
}

function removeSkeleton() {
  document.getElementById("skeleton-loader")?.remove();
}

// ---------------------------------------------------------------------------
// Рендеринг сообщений
// ---------------------------------------------------------------------------

function renderMessage(msg) {
  const isUser = msg.role === "user";
  const el = document.createElement("div");
  el.className = `message message--${isUser ? "user" : "assistant"}`;
  el.id = msg.id;

  const avatarEmoji = isUser ? "👤" : "📚";

  // Контент: для ассистента — Markdown, для пользователя — plain text
  let contentHtml;
  if (isUser) {
    contentHtml = `<p>${escapeHtml(msg.content)}</p>`;
  } else {
    // marked.parse возвращает HTML — используем его напрямую (контент из нашего API)
    contentHtml = window.marked ? marked.parse(msg.content) : escapeHtml(msg.content);
  }

  // Источники
  const sourcesHtml = (!isUser && msg.sources && msg.sources.length > 0)
    ? `<div class="message-sources">
        ${msg.sources.map((s) => {
          const domain = getDomainFromId(s.id);
          return `<span class="source-badge source-badge--${domain}" title="${escapeHtml(s.id)}">
            ${escapeHtml(s.title)}
            <span class="source-id">${escapeHtml(s.id)}</span>
          </span>`;
        }).join("")}
      </div>`
    : "";

  // Кнопки действий (только для ассистента)
  const actionsHtml = !isUser
    ? `<div class="message-actions" role="group" aria-label="Действия с ответом">
        <button class="action-btn js-copy" type="button" aria-label="Скопировать ответ">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          Копировать
        </button>
        <button class="action-btn js-like" type="button" aria-label="Полезно">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
          </svg>
        </button>
        <button class="action-btn js-dislike" type="button" aria-label="Не полезно">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
          </svg>
        </button>
        ${msg.confidence != null
          ? `<span class="confidence-badge">
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
              ${formatConfidence(msg.confidence)}
            </span>`
          : ""}
      </div>`
    : "";

  el.innerHTML = `
    <div class="message-avatar" aria-hidden="true">${avatarEmoji}</div>
    <div class="message-body">
      <div class="message-bubble">${contentHtml}</div>
      ${sourcesHtml}
      ${actionsHtml}
    </div>
  `;

  // Подсветка кода через Prism
  if (!isUser && window.Prism) {
    requestAnimationFrame(() => Prism.highlightAllUnder(el));
  }

  // Обработчики кнопок
  el.querySelector(".js-copy")?.addEventListener("click", async () => {
    const ok = await copyToClipboard(msg.content);
    showToast(ok ? "Скопировано в буфер обмена" : "Не удалось скопировать", ok ? "success" : "error");
  });

  el.querySelector(".js-like")?.addEventListener("click", (e) => {
    const btn = e.currentTarget;
    btn.classList.toggle("action-btn--liked");
    el.querySelector(".js-dislike")?.classList.remove("action-btn--disliked");
  });

  el.querySelector(".js-dislike")?.addEventListener("click", (e) => {
    const btn = e.currentTarget;
    btn.classList.toggle("action-btn--disliked");
    el.querySelector(".js-like")?.classList.remove("action-btn--liked");
  });

  return el;
}

// ---------------------------------------------------------------------------
// Отправка сообщения
// ---------------------------------------------------------------------------

export async function sendMessage(question) {
  if (isLoading || !question.trim()) return;
  isLoading = true;

  hideWelcome();

  // Добавить user bubble
  const userMsg = {
    id: generateId(),
    role: "user",
    content: question.trim(),
    timestamp: Date.now(),
  };
  history.push(userMsg);
  messagesArea.appendChild(renderMessage(userMsg));
  scrollToBottom(messagesArea);

  // Skeleton
  const skeleton = renderSkeleton();

  try {
    const data = await fetchWithRetry("/api/ask", { question: question.trim() });

    removeSkeleton();

    if (data.status === "error") {
      showToast(data.answer || "Ошибка сервера", "error");
    } else {
      const aiMsg = {
        id: generateId(),
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        confidence: data.confidence,
        timestamp: Date.now(),
      };
      history.push(aiMsg);
      saveHistory();

      const el = renderMessage(aiMsg);
      messagesArea.appendChild(el);
      scrollToBottom(messagesArea);
    }
  } catch (err) {
    removeSkeleton();
    showToast(`Ошибка: ${err.message}`, "error");
  } finally {
    isLoading = false;
  }
}

// ---------------------------------------------------------------------------
// Fetch с retry и timeout
// ---------------------------------------------------------------------------

async function fetchWithRetry(url, body, retries = 1) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (err) {
      clearTimeout(timer);
      if (attempt === retries) {
        if (err.name === "AbortError") throw new Error("Превышено время ожидания (15 сек)");
        throw err;
      }
      // Небольшая пауза перед retry
      await new Promise((r) => setTimeout(r, 800));
    }
  }
}

// ---------------------------------------------------------------------------
// Очистка чата
// ---------------------------------------------------------------------------

export function clearChat() {
  history = [];
  saveHistory();
  messagesArea.innerHTML = "";
  renderWelcome();
}

// ---------------------------------------------------------------------------
// Восстановление истории из localStorage
// ---------------------------------------------------------------------------

function restoreHistory() {
  if (history.length === 0) {
    renderWelcome();
    return;
  }
  hideWelcome();
  history.forEach((msg) => {
    messagesArea.appendChild(renderMessage(msg));
  });
  scrollToBottom(messagesArea, false);
}

// ---------------------------------------------------------------------------
// Инициализация
// ---------------------------------------------------------------------------

export function initChat(messagesEl, welcomeEl) {
  messagesArea = messagesEl;
  welcomeScreen = welcomeEl;

  loadHistory();
  restoreHistory();

  // Клик по карточке welcome screen
  welcomeScreen.addEventListener("click", (e) => {
    const card = e.target.closest(".welcome-card");
    if (!card) return;
    const question = card.dataset.question;
    if (question) {
      // Диспатчим кастомное событие — app.js подставит в textarea и отправит
      document.dispatchEvent(new CustomEvent("chat:example-click", { detail: { question } }));
    }
  });
}
