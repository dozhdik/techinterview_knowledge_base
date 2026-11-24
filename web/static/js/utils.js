export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function safeInline(text) {
  return text.split(/(`[^`]*`)/g).map(part => {
    if (part.startsWith("`") && part.endsWith("`")) return `<code>${escapeHtml(part.slice(1, -1))}</code>`;
    return escapeHtml(part).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  }).join("");
}

function localMarkdown(content) {
  const lines = String(content).split("\n");
  const html = [];
  let code = false, list = "", codeLines = [];
  const closeList = () => { if (list) { html.push(`</${list}>`); list = ""; } };
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    if (/^\s*```/.test(line)) {
      closeList();
      if (code) { html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`); codeLines = []; }
      code = !code;
      continue;
    }
    if (code) { codeLines.push(line); continue; }
    if (line.includes("|") && index + 1 < lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[index + 1])) {
      closeList();
      const cells = row => row.trim().replace(/^\||\|$/g, "").split("|").map(cell => safeInline(cell.trim()));
      const headers = cells(line);
      html.push('<div class="table-scroll"><table><thead><tr>' + headers.map(c => `<th>${c}</th>`).join("") + '</tr></thead><tbody>');
      index += 1;
      while (index + 1 < lines.length && lines[index + 1].includes("|") && lines[index + 1].trim()) {
        index += 1;
        html.push('<tr>' + cells(lines[index]).map(c => `<td>${c}</td>`).join("") + '</tr>');
      }
      html.push('</tbody></table></div>');
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) { closeList(); const n = heading[1].length; html.push(`<h${n}>${safeInline(heading[2])}</h${n}>`); continue; }
    const bullet = line.match(/^\s*[-*]\s+(.+)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    const item = bullet || numbered;
    if (item) {
      const kind = bullet ? "ul" : "ol";
      if (list !== kind) { closeList(); html.push(`<${kind}>`); list = kind; }
      html.push(`<li>${safeInline(item[1])}</li>`); continue;
    }
    closeList();
    if (line.trim()) html.push(`<p>${safeInline(line)}</p>`);
  }
  closeList();
  if (code) html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
  return html.join("");
}

export function renderMarkdown(content) {
  if (!window.marked || !window.DOMPurify) return localMarkdown(content);
  return window.DOMPurify.sanitize(window.marked.parse(content));
}

export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
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

export function debounce(fn, ms) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), ms);
  };
}

export function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("toast--exit");
    setTimeout(() => toast.remove(), 200);
  }, 3000);
}

export function formatConfidence(value) {
  return `${Math.round(value * 100)}%`;
}

export function getDomainFromId(id) {
  const match = id.match(/^([A-Z]+)-/);
  if (!match) return "glb";
  const domain = match[1].toLowerCase();
  if (domain === "cs") return "cs";
  if (domain === "arch") return "arch";
  if (domain === "proc") return "proc";
  return "glb";
}

export function scrollToBottom(element, smooth = true) {
  if (!element) return;
  element.scrollTo({
    top: element.scrollHeight,
    behavior: smooth ? "smooth" : "auto",
  });
}

export function generateId() {
  return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function formatTime(timestamp) {
  const date = new Date(timestamp);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}
