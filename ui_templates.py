from __future__ import annotations

import re


MAIN_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Simple Todo</title>
  <style>
    :root {
      --bg: #0b0d12;
      --panel: #11151d;
      --panel-2: #171c26;
      --text: #eef2f7;
      --muted: #8b97aa;
      --line: #252c3a;
      --accent: #2563eb;
      --danger: #fb7185;
      --shadow: 0 18px 52px rgba(0, 0, 0, 0.35);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background: var(--bg);
      font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 14px;
    }

    button, input { font: inherit; }

    button {
      border: 1px solid var(--line);
      background: #151a24;
      color: var(--text);
      min-height: 36px;
      padding: 0 12px;
      border-radius: 6px;
      cursor: pointer;
    }

    button:hover { border-color: var(--accent); }
    button.primary { border-color: var(--accent); background: var(--accent); color: #fff; }
    button.danger { color: var(--danger); }
    button:disabled,
    button.primary:disabled {
      border-color: var(--line);
      background: #10141c;
      color: var(--muted);
      cursor: default;
      opacity: 0.72;
    }
    button:disabled:hover { border-color: var(--line); }

    input {
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #0f131b;
      color: var(--text);
      padding: 0 11px;
      outline: none;
    }

    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 25%, transparent);
    }

    .app {
      min-height: 100vh;
      padding: 24px;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 18px;
    }

    .topbar {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: end;
    }

    h1 {
      margin: 0;
      font-size: 30px;
      line-height: 1.1;
      letter-spacing: 0;
    }

    .meta { color: var(--muted); margin-top: 7px; }

    .accent-row {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .swatch {
      width: 26px;
      height: 26px;
      min-height: 26px;
      padding: 0;
      border-radius: 999px;
      border: 2px solid transparent;
      background: var(--swatch);
    }

    .swatch.active {
      border-color: #fff;
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--swatch) 38%, transparent);
    }

    .category-form {
      display: grid;
      grid-template-columns: minmax(180px, 360px) auto;
      gap: 10px;
      align-items: center;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 14px;
      align-content: start;
      overflow: auto;
      padding-bottom: 6px;
    }

    .card {
      min-height: 150px;
      display: grid;
      grid-template-rows: 1fr auto;
      gap: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(145deg, var(--panel), var(--panel-2));
      color: var(--text);
      padding: 16px;
      text-align: left;
      box-shadow: var(--shadow);
    }

    .card:hover {
      border-color: var(--accent);
      transform: translateY(-1px);
    }

    .card-title {
      font-size: 21px;
      font-weight: 700;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }

    .card-counts {
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      margin-top: 10px;
    }

    .progress {
      height: 5px;
      border-radius: 999px;
      overflow: hidden;
      background: #262d3a;
      margin-top: 12px;
    }

    .progress span {
      display: block;
      height: 100%;
      width: var(--done);
      background: var(--accent);
    }

    .card-actions {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
    }

    .empty {
      border: 1px dashed var(--line);
      border-radius: 8px;
      min-height: 220px;
      display: grid;
      place-items: center;
      color: var(--muted);
      background: #10141c;
    }

    .toast {
      position: fixed;
      right: 18px;
      bottom: 18px;
      max-width: 360px;
      border: 1px solid #7f1d1d;
      background: #2a1115;
      color: #fecdd3;
      padding: 12px 14px;
      border-radius: 6px;
      box-shadow: var(--shadow);
      opacity: 0;
      transform: translateY(8px);
      pointer-events: none;
      transition: opacity 140ms ease, transform 140ms ease;
      z-index: 20;
    }

    .toast.visible {
      opacity: 1;
      transform: translateY(0);
    }

    @media (max-width: 720px) {
      .app { padding: 16px; }
      .topbar { grid-template-columns: 1fr; }
      .accent-row { justify-content: flex-start; }
      .category-form { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div>
        <h1>Simple Todo</h1>
        <div id="summary" class="meta">0 categories</div>
      </div>
      <div id="accentRow" class="accent-row"></div>
    </header>

    <form id="categoryForm" class="category-form" onsubmit="return false;">
      <input id="categoryName" autocomplete="off" placeholder="Category name" oninput="document.getElementById('addCategoryButton').disabled = this.value.trim().length === 0">
      <button id="addCategoryButton" class="primary" type="button" onclick="addCategory(event)" disabled>Add Category</button>
    </form>

    <main id="cards" class="cards"></main>
  </div>

  <div id="toast" class="toast"></div>

  <script>
    const ACCENTS = [
      "#2563eb", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e",
      "#8b5cf6", "#d946ef", "#f97316", "#84cc16", "#ef4444"
    ];

    function storedAccent() {
      try {
        return localStorage.getItem("simpleTodoAccent") || ACCENTS[0];
      } catch (_error) {
        return ACCENTS[0];
      }
    }

    const state = {
      categories: [],
      accent: storedAccent(),
      categorySaving: false,
      mainBound: false
    };

    const els = {};

    function cacheElements() {
      for (const id of ["summary", "accentRow", "categoryForm", "categoryName", "addCategoryButton", "cards", "toast"]) {
        els[id] = document.getElementById(id);
      }
    }

    async function callApi(method, ...args) {
      await waitForApi(method);
      const response = await window.pywebview.api[method](...args);
      if (!response.ok) {
        throw new Error(response.error || "Action failed.");
      }
      return response.data;
    }

    function waitForApi(method) {
      if (window.pywebview?.api?.[method]) {
        return Promise.resolve();
      }
      return new Promise((resolve, reject) => {
        const startedAt = Date.now();
        const timer = window.setInterval(() => {
          if (window.pywebview?.api?.[method]) {
            window.clearInterval(timer);
            resolve();
            return;
          }
          if (Date.now() - startedAt > 5000) {
            window.clearInterval(timer);
            reject(new Error("App is still starting. Try again in a moment."));
          }
        }, 50);
      });
    }

    function showError(error) {
      els.toast.textContent = error.message || String(error);
      els.toast.classList.add("visible");
      window.clearTimeout(showError.timer);
      showError.timer = window.setTimeout(() => els.toast.classList.remove("visible"), 3600);
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function setAccent(color) {
      state.accent = color;
      try {
        localStorage.setItem("simpleTodoAccent", color);
      } catch (_error) {}
      document.documentElement.style.setProperty("--accent", color);
      renderAccents();
      if (window.pywebview?.api?.set_accent) {
        window.pywebview.api.set_accent(color);
      }
    }

    function renderAccents() {
      els.accentRow.innerHTML = "";
      for (const color of ACCENTS) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "swatch" + (color === state.accent ? " active" : "");
        button.style.setProperty("--swatch", color);
        button.title = color;
        button.addEventListener("click", () => setAccent(color));
        els.accentRow.appendChild(button);
      }
    }

    async function loadCategories() {
      try {
        state.categories = await callApi("list_categories");
        renderCards();
      } catch (error) {
        showError(error);
      }
    }

    function renderCards() {
      const open = state.categories.reduce((sum, category) => sum + category.pending, 0);
      const total = state.categories.reduce((sum, category) => sum + category.total, 0);
      els.summary.textContent = `${state.categories.length} categories · ${open} open / ${total} total`;

      if (!state.categories.length) {
        els.cards.innerHTML = `<div class="empty">No categories yet.</div>`;
        return;
      }

      els.cards.innerHTML = "";
      for (const category of state.categories) {
        const done = category.total ? Math.round(((category.total - category.pending) / category.total) * 100) : 0;
        const card = document.createElement("article");
        card.className = "card";
        card.tabIndex = 0;
        card.innerHTML = `
          <div>
            <div class="card-title">${escapeHtml(category.name)}</div>
            <div class="card-counts">
              <span>${category.pending} open</span>
              <span>${category.total} total</span>
            </div>
            <div class="progress" style="--done:${done}%"><span></span></div>
          </div>
          <div class="card-actions">
            <button type="button" data-action="rename">Rename</button>
            <button type="button" class="danger" data-action="delete">Delete</button>
          </div>
        `;

        card.addEventListener("click", event => {
          if (event.target.closest("button")) {
            return;
          }
          openCategory(category.id);
        });

        card.addEventListener("keydown", event => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openCategory(category.id);
          }
        });

        card.querySelector('[data-action="rename"]').addEventListener("click", () => renameCategory(category));
        card.querySelector('[data-action="delete"]').addEventListener("click", () => deleteCategory(category));
        els.cards.appendChild(card);
      }
    }

    async function openCategory(categoryId) {
      try {
        await callApi("open_category_window", categoryId, state.accent);
      } catch (error) {
        showError(error);
      }
    }

    async function addCategory(event) {
      if (event) {
        event.preventDefault();
      }
      if (state.categorySaving) {
        return;
      }
      const name = els.categoryName.value.trim();
      if (!name) {
        updateCategoryButtonState();
        els.categoryName.focus();
        return;
      }
      state.categorySaving = true;
      updateCategoryButtonState();
      try {
        await callApi("add_category", name);
        els.categoryName.value = "";
        await loadCategories();
      } catch (error) {
        showError(error);
      } finally {
        state.categorySaving = false;
        updateCategoryButtonState();
      }
    }

    function updateCategoryButtonState() {
      els.addCategoryButton.disabled = state.categorySaving || els.categoryName.value.trim().length === 0;
    }

    async function renameCategory(category) {
      const name = prompt("Category name", category.name);
      if (name === null) {
        return;
      }
      try {
        await callApi("rename_category", category.id, name);
        await loadCategories();
      } catch (error) {
        showError(error);
      }
    }

    async function deleteCategory(category) {
      if (!confirm(`Delete "${category.name}" and its tasks?`)) {
        return;
      }
      try {
        await callApi("delete_category", category.id);
        await loadCategories();
      } catch (error) {
        showError(error);
      }
    }

    async function checkReminders() {
      try {
        const reminders = await callApi("get_due_reminders");
        if (reminders.length) {
          alert(reminders.map(task => `${task.title}${task.category_name ? " · " + task.category_name : ""}`).join("\n"));
          await loadCategories();
        }
      } catch (error) {
        showError(error);
      }
    }

    window.refreshFromNative = loadCategories;

    function bindMainUi() {
      if (state.mainBound) {
        return;
      }
      cacheElements();
      if (!els.addCategoryButton || !els.categoryName || !els.categoryForm) {
        return;
      }
      state.mainBound = true;
      els.addCategoryButton.addEventListener("click", addCategory);
      els.categoryForm.addEventListener("submit", addCategory);
      els.categoryName.addEventListener("input", updateCategoryButtonState);
      els.categoryName.addEventListener("keydown", event => {
        if (event.key === "Enter") {
          event.preventDefault();
          addCategory(event);
        }
      });
      updateCategoryButtonState();
      renderAccents();
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", bindMainUi);
    } else {
      bindMainUi();
    }

    window.addEventListener("pywebviewready", async () => {
      bindMainUi();
      updateCategoryButtonState();
      setAccent(state.accent);
      await loadCategories();
      window.setInterval(checkReminders, 15000);
      checkReminders();
    });
  </script>
</body>
</html>
"""


CATEGORY_HTML_TEMPLATE = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__CATEGORY_NAME__</title>
  <style>
    :root {
      --bg: #0b0d12;
      --panel: #11151d;
      --panel-2: #171c26;
      --text: #eef2f7;
      --muted: #8b97aa;
      --line: #252c3a;
      --accent: __ACCENT__;
      --danger: #fb7185;
      --done: #64748b;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 13px;
    }

    button, input { font: inherit; }

    button {
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #151a24;
      color: var(--text);
      padding: 0 10px;
      cursor: pointer;
    }

    button:hover { border-color: var(--accent); }
    button.primary { border-color: var(--accent); background: var(--accent); color: #fff; }
    button.danger { color: var(--danger); }

    input {
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #0f131b;
      color: var(--text);
      padding: 0 10px;
      outline: none;
    }

    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 25%, transparent);
    }

    .shell {
      width: 100vw;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 12px;
      padding: 14px;
    }

    header {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: start;
    }

    h1 {
      margin: 0;
      font-size: 21px;
      line-height: 1.15;
      letter-spacing: 0;
      overflow-wrap: anywhere;
    }

    .status {
      color: var(--muted);
      margin-top: 4px;
    }

    .top-actions,
    .task-actions {
      display: flex;
      gap: 7px;
      flex-wrap: wrap;
      align-items: center;
    }

    .top-actions { justify-content: flex-end; }

    .composer {
      display: grid;
      gap: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }

    .composer-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
    }

    .time-row {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) 76px;
      gap: 8px;
      align-items: center;
      color: var(--muted);
    }

    .time-row input,
    .time-row select {
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #0f131b;
      color: var(--text);
      padding: 0 9px;
      outline: none;
    }

    .time-row select {
      width: 100%;
      appearance: none;
    }

    .sections {
      min-height: 0;
      overflow: auto;
      display: grid;
      align-content: start;
      gap: 18px;
    }

    .task-section {
      display: grid;
      gap: 8px;
    }

    .section-heading {
      display: flex;
      justify-content: space-between;
      align-items: center;
      min-height: 32px;
      border-bottom: 1px solid var(--line);
      color: var(--text);
      cursor: pointer;
      user-select: none;
    }

    .section-title {
      font-weight: 700;
      display: inline-flex;
      gap: 8px;
      align-items: center;
      color: var(--accent);
    }

    .section-count { color: var(--muted); font-weight: 500; }

    .section-toggle,
    .icon-button {
      width: 30px;
      min-height: 30px;
      padding: 0;
      display: inline-grid;
      place-items: center;
      border-color: transparent;
      background: transparent;
      color: var(--accent);
      font-size: 24px;
      line-height: 1;
    }

    .section-toggle:hover,
    .icon-button:hover {
      border-color: var(--line);
      background: #151a24;
    }

    .list {
      display: grid;
      gap: 0;
    }

    .list.collapsed {
      display: none;
    }

    .task {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      border-bottom: 1px solid rgba(139, 151, 170, 0.18);
      padding: 10px 0;
    }

    .task:last-child {
      border-bottom: 0;
    }

    .task.done .title {
      color: var(--done);
      text-decoration: line-through;
    }

    .task input[type="checkbox"] {
      width: 17px;
      height: 17px;
      min-height: 17px;
      accent-color: var(--accent);
      margin-top: 2px;
    }

    .title {
      font-weight: 650;
      overflow-wrap: anywhere;
    }

    .reminder {
      color: var(--muted);
      margin-top: 4px;
      font-size: 12px;
    }

    .reminder.due {
      color: #f59e0b;
      font-weight: 700;
    }

    .task-actions {
      justify-content: flex-end;
      flex-wrap: nowrap;
    }

    .icon-button svg {
      width: 15px;
      height: 15px;
      stroke: currentColor;
      stroke-width: 2;
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .empty {
      color: var(--muted);
      padding: 9px 0 2px;
    }

    .toast {
      position: fixed;
      left: 12px;
      right: 12px;
      bottom: 12px;
      border: 1px solid #7f1d1d;
      background: #2a1115;
      color: #fecdd3;
      padding: 10px 12px;
      border-radius: 6px;
      opacity: 0;
      transform: translateY(8px);
      pointer-events: none;
      transition: opacity 140ms ease, transform 140ms ease;
      z-index: 20;
    }

    .toast.visible {
      opacity: 1;
      transform: translateY(0);
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1 id="categoryTitle">__CATEGORY_NAME__</h1>
        <div id="status" class="status">0 open / 0 completed</div>
      </div>
      <div class="top-actions">
        <button id="closeButton" type="button">Close</button>
      </div>
    </header>

    <form id="taskForm" class="composer">
      <div class="composer-row">
        <input id="taskTitle" autocomplete="off" placeholder="Add a task">
        <button class="primary" type="submit">Add</button>
      </div>
      <div class="time-row">
        <span>Time</span>
        <input id="taskTime" type="time" min="01:00" max="12:59" step="60" aria-label="Reminder time">
        <select id="taskPeriod" aria-label="AM or PM">
          <option>AM</option>
          <option>PM</option>
        </select>
      </div>
    </form>

    <main class="sections">
      <section id="todoSection" class="task-section">
        <div id="todoHeader" class="section-heading" role="button" tabindex="0" aria-expanded="true">
          <div class="section-title">To Do <span id="todoCount" class="section-count">0</span></div>
          <span id="todoToggle" class="section-toggle" aria-hidden="true">⌄</span>
        </div>
        <div id="todoList" class="list"></div>
      </section>
      <section id="completedSection" class="task-section">
        <div id="completedHeader" class="section-heading" role="button" tabindex="0" aria-expanded="false">
          <div class="section-title">Completed <span id="completedCount" class="section-count">0</span></div>
          <span id="completedToggle" class="section-toggle" aria-hidden="true">›</span>
        </div>
        <div id="completedList" class="list collapsed"></div>
      </section>
    </main>
  </div>

  <div id="toast" class="toast"></div>

  <script>
    const state = {
      tasks: [],
      completedOpen: false
    };
    const els = {};

    function cacheElements() {
      for (const id of [
        "categoryTitle", "status", "closeButton", "taskForm",
        "taskTitle", "taskTime", "taskPeriod", "todoCount", "completedCount",
        "todoHeader", "todoList", "completedHeader", "completedList", "completedToggle", "toast"
      ]) {
        els[id] = document.getElementById(id);
      }
    }

    async function callApi(method, ...args) {
      const response = await window.pywebview.api[method](...args);
      if (!response.ok) {
        throw new Error(response.error || "Action failed.");
      }
      return response.data;
    }

    function showError(error) {
      els.toast.textContent = error.message || String(error);
      els.toast.classList.add("visible");
      window.clearTimeout(showError.timer);
      showError.timer = window.setTimeout(() => els.toast.classList.remove("visible"), 3200);
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function pad(value) {
      return String(value).padStart(2, "0");
    }

    function formatLocalDateTime(date) {
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    function setAccent(color) {
      document.documentElement.style.setProperty("--accent", color);
    }

    async function loadTasks() {
      try {
        const payload = await callApi("window_state");
        state.tasks = payload.tasks;
        els.categoryTitle.textContent = payload.category.name;
        renderTasks();
      } catch (error) {
        showError(error);
      }
    }

    function renderTasks() {
      const todo = state.tasks.filter(task => !task.completed);
      const completed = state.tasks.filter(task => task.completed);
      els.todoCount.textContent = String(todo.length);
      els.completedCount.textContent = String(completed.length);
      els.status.textContent = `${todo.length} open / ${completed.length} completed`;
      renderList(els.todoList, todo, false);
      renderList(els.completedList, completed, true);
      renderCompletedState();
    }

    function renderList(target, tasks, done) {
      target.innerHTML = "";
      if (!tasks.length) {
        target.innerHTML = `<div class="empty">${done ? "Nothing completed yet." : "No open tasks."}</div>`;
        return;
      }

      for (const task of tasks) {
        const row = document.createElement("article");
        row.className = "task" + (task.completed ? " done" : "");
        row.innerHTML = `
          <input type="checkbox" ${task.completed ? "checked" : ""} aria-label="Complete task">
          <div>
            <div class="title">${escapeHtml(task.title)}</div>
            ${task.reminder_label ? `<div class="reminder ${task.due ? "due" : ""}">${escapeHtml(task.reminder_label)}</div>` : ""}
          </div>
          <div class="task-actions">
            <button type="button" class="icon-button" data-action="edit" title="Edit" aria-label="Edit task">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path></svg>
            </button>
            <button type="button" class="icon-button danger" data-action="delete" title="Delete" aria-label="Delete task">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M19 6l-1 14H6L5 6"></path><path d="M10 11v5"></path><path d="M14 11v5"></path></svg>
            </button>
          </div>
        `;

        row.querySelector('input[type="checkbox"]').addEventListener("change", async event => {
          try {
            await callApi("set_completed", task.id, event.target.checked);
            await loadTasks();
          } catch (error) {
            event.target.checked = task.completed;
            showError(error);
          }
        });

        row.querySelector('[data-action="edit"]').addEventListener("click", () => editTask(task));
        row.querySelector('[data-action="delete"]').addEventListener("click", async () => {
          if (!confirm("Delete this task?")) {
            return;
          }
          try {
            await callApi("delete_task", task.id);
            await loadTasks();
          } catch (error) {
            showError(error);
          }
        });

        target.appendChild(row);
      }
    }

    async function addTask(event) {
      event.preventDefault();
      const title = els.taskTitle.value.trim();
      if (!title) {
        return;
      }
      try {
        await callApi("add_task", title, selectedReminderDateTime());
        els.taskTitle.value = "";
        setDefaultReminderTime();
        await loadTasks();
        els.taskTitle.focus();
      } catch (error) {
        showError(error);
      }
    }

    async function editTask(task) {
      const title = prompt("Task", task.title);
      if (title === null) {
        return;
      }
      try {
        await callApi("update_task", task.id, title, task.reminder_at || "");
        await loadTasks();
      } catch (error) {
        showError(error);
      }
    }

    function setDefaultReminderTime() {
      const date = new Date();
      date.setMinutes(date.getMinutes() + 30);
      date.setSeconds(0, 0);
      const period = date.getHours() >= 12 ? "PM" : "AM";
      let hour = date.getHours() % 12;
      if (hour === 0) {
        hour = 12;
      }
      els.taskTime.value = `${pad(hour)}:${pad(date.getMinutes())}`;
      els.taskPeriod.value = period;
    }

    function selectedReminderDateTime() {
      const value = els.taskTime.value;
      if (!value) {
        return "";
      }
      const parts = value.split(":");
      let hour = Number(parts[0]);
      const minute = Number(parts[1]);
      if (!Number.isFinite(hour) || !Number.isFinite(minute)) {
        return "";
      }
      hour = Math.max(1, Math.min(12, hour));
      if (els.taskPeriod.value === "PM" && hour < 12) {
        hour += 12;
      }
      if (els.taskPeriod.value === "AM" && hour === 12) {
        hour = 0;
      }
      const date = new Date();
      date.setHours(hour, minute, 0, 0);
      if (date <= new Date()) {
        date.setDate(date.getDate() + 1);
      }
      return formatLocalDateTime(date);
    }

    function toggleCompleted() {
      state.completedOpen = !state.completedOpen;
      renderCompletedState();
    }

    function keepTodoOpen() {
      els.todoList.classList.remove("collapsed");
      els.todoHeader.setAttribute("aria-expanded", "true");
    }

    function renderCompletedState() {
      els.completedList.classList.toggle("collapsed", !state.completedOpen);
      els.completedToggle.textContent = state.completedOpen ? "⌄" : "›";
      els.completedHeader.setAttribute("aria-expanded", state.completedOpen ? "true" : "false");
    }

    function bindHeaderToggle(header, action) {
      header.addEventListener("click", action);
      header.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          action();
        }
      });
    }

    window.refreshFromNative = loadTasks;
    window.setAccentFromNative = setAccent;

    window.addEventListener("pywebviewready", async () => {
      cacheElements();
      els.taskForm.addEventListener("submit", addTask);
      els.closeButton.addEventListener("click", () => callApi("close_window"));
      bindHeaderToggle(els.todoHeader, keepTodoOpen);
      bindHeaderToggle(els.completedHeader, toggleCompleted);
      setDefaultReminderTime();
      keepTodoOpen();
      renderCompletedState();
      await loadTasks();
    });
  </script>
</body>
</html>
"""


def category_window_html(category_id: int, category_name: str, accent: str) -> str:
    return (
        CATEGORY_HTML_TEMPLATE
        .replace("__CATEGORY_NAME__", html_escape(category_name))
        .replace("__ACCENT__", safe_accent(accent))
    )


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def safe_accent(value: str) -> str:
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value or "") else "#2563eb"
