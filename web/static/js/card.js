import { renderMarkdown } from "./utils.js";

const content = document.getElementById("card-content");
try {
  document.documentElement.setAttribute("data-theme", localStorage.getItem("theme") || "light");
} catch {}

try {
  const id = decodeURIComponent(window.location.pathname.split("/").pop());
  const response = await fetch(`/api/units/${encodeURIComponent(id)}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Карточка не найдена: она могла быть удалена или ещё не добавлена.");
    }
    if (response.status === 409) {
      throw new Error("Материал этой карточки пока не заполнен. Вернитесь в чат и выберите другую тему.");
    }
    throw new Error("Не удалось загрузить карточку.");
  }
  const unit = await response.json();
  document.title = `${unit.title} — TechInterview KB`;
  document.getElementById("card-meta").textContent = `${unit.id} · ${unit.difficulty} · ${unit.status}`;
  content.innerHTML = renderMarkdown(unit.content);
} catch (error) {
  content.textContent = error.message;
}
