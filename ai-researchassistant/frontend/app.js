const API_BASE = ""; // Relative to FastAPI host

let currentTab = "chat";
let allMemories = [];

// Initialize Icons & Listeners
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  checkHealth();
  loadInitialData();
});

// Switch Tab
function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active-tab"));

  const targetTab = document.getElementById(`tab-${tab}`);
  const targetNav = document.getElementById(`nav-${tab}`);
  if (targetTab) targetTab.classList.remove("hidden");
  if (targetNav) targetNav.classList.add("active-tab");

  const titles = {
    chat: "Grounded Intelligence Chat",
    ingest: "Ingest Personal Knowledge",
    memories: "Memory Explorer & Provenance",
    profile: "Structured Persona & Goals",
    audit: "Memory Audit Ledger"
  };
  document.getElementById("section-title").innerText = titles[tab] || "Personal AI";

  lucide.createIcons();

  if (tab === "memories") loadMemories();
  if (tab === "profile") renderProfileData();
  if (tab === "audit") loadAuditLogs();
}

// Health Check
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("status-api").innerText = "Online";
      document.getElementById("status-model").innerText = data.embedding_model.split("/").pop();
    }
  } catch (err) {
    document.getElementById("status-api").innerText = "Offline";
    document.getElementById("status-api").classList.replace("text-emerald-400", "text-rose-400");
  }
}

// Initial Data Load
async function loadInitialData() {
  await loadMemories();
  renderProfileData();
}

// Chat Functionality
async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const query = input.value.trim();
  if (!query) return;

  appendUserMessage(query);
  input.value = "";

  const sendBtn = document.getElementById("chat-send-btn");
  sendBtn.disabled = true;

  const loadingId = appendLoadingMessage();

  try {
    const res = await fetch(`${API_BASE}/api/v1/query/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, max_memories: 6 })
    });

    removeMessage(loadingId);

    if (!res.ok) throw new Error("Failed to generate response");
    const data = await res.json();
    appendAssistantMessage(data);
  } catch (err) {
    removeMessage(loadingId);
    appendErrorMessage(err.message);
  } finally {
    sendBtn.disabled = false;
    lucide.createIcons();
  }
}

function sendQuickPrompt(text) {
  document.getElementById("chat-input").value = text;
  document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

function appendUserMessage(text) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "flex justify-end";
  div.innerHTML = `
    <div class="max-w-xl bg-brand-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm shadow-md">
      ${escapeHtml(text)}
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendLoadingMessage() {
  const container = document.getElementById("chat-messages");
  const id = "msg-loading-" + Date.now();
  const div = document.createElement("div");
  div.id = id;
  div.className = "flex items-start space-x-3";
  div.innerHTML = `
    <div class="h-8 w-8 rounded-lg bg-dark-800 border border-dark-700 flex items-center justify-center text-brand-500">
      <i data-lucide="brain" class="w-4 h-4 animate-spin"></i>
    </div>
    <div class="bg-dark-800 border border-dark-700 rounded-2xl rounded-tl-none p-4 text-xs text-slate-400 flex items-center space-x-2">
      <span>Retrieving grounded memories & formulating response...</span>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
  return id;
}

function appendAssistantMessage(data) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "flex items-start space-x-3";

  // Citations Pills
  let citationsHtml = "";
  if (data.citations && data.citations.length > 0) {
    citationsHtml = `
      <div class="mt-3 pt-3 border-t border-dark-700/60">
        <span class="text-[11px] font-semibold text-slate-400 block mb-1.5 uppercase tracking-wider">Grounding Memories:</span>
        <div class="flex flex-wrap gap-1.5">
          ${data.citations.map(c => `
            <span class="text-[11px] px-2 py-0.5 rounded badge-${c.category}" title="${escapeHtml(c.content_snippet)}">
              [${c.category}] ${escapeHtml(c.content_snippet.slice(0, 45))}...
            </span>
          `).join("")}
        </div>
      </div>
    `;
  }

  // Inferred Recommendations
  let inferencesHtml = "";
  if (data.inferred_recommendations && data.inferred_recommendations.length > 0) {
    inferencesHtml = `
      <div class="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 space-y-1">
        <span class="font-semibold block flex items-center space-x-1.5">
          <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
          <span>Inferred Recommendations</span>
        </span>
        ${data.inferred_recommendations.map(inf => `<div>${escapeHtml(inf)}</div>`).join("")}
      </div>
    `;
  }

  div.innerHTML = `
    <div class="h-8 w-8 rounded-lg bg-dark-800 border border-brand-500/30 flex items-center justify-center text-brand-500 shrink-0">
      <i data-lucide="sparkles" class="w-4 h-4"></i>
    </div>
    <div class="max-w-2xl bg-dark-800 border border-dark-700 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 space-y-2 shadow-lg">
      <div class="prose prose-invert text-sm max-w-none leading-relaxed">
        ${marked.parse(data.answer)}
      </div>
      ${inferencesHtml}
      ${citationsHtml}
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

function appendErrorMessage(errText) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "flex items-start space-x-3";
  div.innerHTML = `
    <div class="h-8 w-8 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-500 shrink-0">
      <i data-lucide="alert-circle" class="w-4 h-4"></i>
    </div>
    <div class="bg-dark-800 border border-rose-500/30 rounded-2xl rounded-tl-none p-3.5 text-xs text-rose-300">
      ${escapeHtml(errText)}
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// Ingestion Functionality
async function handleIngestSubmit() {
  const title = document.getElementById("ingest-title").value.trim() || "Personal Note";
  const status = document.getElementById("ingest-status").value;
  const content = document.getElementById("ingest-content").value.trim();

  if (!content) {
    alert("Please enter some knowledge or content to ingest.");
    return;
  }

  const btn = document.getElementById("ingest-btn");
  btn.disabled = true;
  btn.innerText = "Extracting & Indexing Memories...";

  try {
    const res = await fetch(`${API_BASE}/api/v1/ingest/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        content,
        default_verification_status: status
      })
    });

    if (!res.ok) throw new Error("Ingestion failed");
    const data = await res.json();

    renderIngestResults(data);
    document.getElementById("ingest-content").value = "";
    await loadMemories();
  } catch (err) {
    alert("Error during ingestion: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4"></i><span>Extract & Ingest Memories</span>`;
    lucide.createIcons();
  }
}

function renderIngestResults(data) {
  const container = document.getElementById("ingest-results");
  const cardsBox = document.getElementById("ingest-cards");
  container.classList.remove("hidden");
  cardsBox.innerHTML = "";

  data.memories.forEach(m => {
    const card = document.createElement("div");
    card.className = "p-4 rounded-xl bg-dark-900 border border-dark-700 flex items-start justify-between text-xs";
    card.innerHTML = `
      <div class="space-y-1.5 max-w-xl">
        <div class="flex items-center space-x-2">
          <span class="px-2 py-0.5 rounded font-mono font-medium badge-${m.category}">${m.category}</span>
          <span class="text-slate-400 font-mono text-[11px]">${m.verification_status}</span>
        </div>
        <p class="text-sm text-slate-200">${escapeHtml(m.content)}</p>
      </div>
      <span class="text-[11px] font-mono text-emerald-400">Indexed (100%)</span>
    `;
    cardsBox.appendChild(card);
  });
}

// Memory Explorer Functionality
async function loadMemories() {
  const catFilter = document.getElementById("memory-category-filter")?.value;
  const statusFilter = document.getElementById("memory-status-filter")?.value;

  let url = `${API_BASE}/api/v1/memories/?limit=100`;
  if (catFilter) url += `&category=${catFilter}`;
  if (statusFilter) url += `&verification_status=${statusFilter}`;

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    allMemories = await res.json();
    renderMemoriesGrid(allMemories);
    renderProfileData();
  } catch (err) {
    console.error("Failed to load memories:", err);
  }
}

function renderMemoriesGrid(memories) {
  const container = document.getElementById("memories-container");
  const countEl = document.getElementById("memory-count");
  if (countEl) countEl.innerText = memories.length;

  if (!container) return;
  container.innerHTML = "";

  if (memories.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-12 text-center text-slate-500 text-sm">
        No memories match the active filter. Ingest some knowledge to get started!
      </div>
    `;
    return;
  }

  memories.forEach(m => {
    const card = document.createElement("div");
    card.className = "p-4 rounded-xl bg-dark-800 border border-dark-700 flex flex-col justify-between space-y-3 hover:border-dark-600 transition shadow-sm";
    
    // Status Badge
    let statusClass = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    if (m.verification_status === "AI_INFERRED") statusClass = "text-purple-400 bg-purple-500/10 border-purple-500/20";
    if (m.verification_status === "HISTORICAL") statusClass = "text-slate-400 bg-slate-500/10 border-slate-500/20";

    card.innerHTML = `
      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs">
          <span class="px-2 py-0.5 rounded font-mono font-medium badge-${m.category}">${m.category}</span>
          <span class="px-2 py-0.5 rounded-full border text-[10px] font-mono ${statusClass}">${m.verification_status}</span>
        </div>
        <p class="text-sm text-slate-200 leading-snug">${escapeHtml(m.content)}</p>
      </div>

      <div class="pt-2 border-t border-dark-700/60 flex items-center justify-between text-xs text-slate-400">
        <span class="font-mono text-[10px] truncate max-w-[120px]" title="${m.id}">${m.id.slice(0, 8)}...</span>
        <div class="flex items-center space-x-1.5">
          ${m.verification_status === "AI_INFERRED" ? `
            <button onclick="verifyMemory('${m.id}')" class="px-2 py-0.5 rounded bg-brand-600 hover:bg-brand-500 text-white text-[11px] font-medium transition" title="Approve as Verified Fact">Verify</button>
          ` : ""}
          <button onclick="openEditModal('${m.id}')" class="p-1 rounded hover:bg-dark-700 text-slate-400 hover:text-slate-200 transition" title="Edit">
            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
          </button>
          <button onclick="deleteMemory('${m.id}')" class="p-1 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition" title="Retire/Delete">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });

  lucide.createIcons();
}

// Memory Actions
async function verifyMemory(id) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/memories/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        verification_status: "VERIFIED_FACT",
        confidence_score: 1.0,
        update_reason: "User elevated inference to verified fact"
      })
    });
    if (res.ok) await loadMemories();
  } catch (err) {
    alert("Failed to verify memory: " + err.message);
  }
}

function openEditModal(id) {
  const mem = allMemories.find(m => m.id === id);
  if (!mem) return;

  document.getElementById("edit-memory-id").value = mem.id;
  document.getElementById("edit-memory-content").value = mem.content;
  document.getElementById("edit-memory-status").value = mem.verification_status;
  document.getElementById("edit-memory-reason").value = "";
  document.getElementById("edit-modal").classList.remove("hidden");
}

function closeEditModal() {
  document.getElementById("edit-modal").classList.add("hidden");
}

async function saveMemoryEdit() {
  const id = document.getElementById("edit-memory-id").value;
  const content = document.getElementById("edit-memory-content").value.trim();
  const status = document.getElementById("edit-memory-status").value;
  const reason = document.getElementById("edit-memory-reason").value.trim() || "Manual user edit";

  try {
    const res = await fetch(`${API_BASE}/api/v1/memories/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content,
        verification_status: status,
        update_reason: reason
      })
    });

    if (res.ok) {
      closeEditModal();
      await loadMemories();
    }
  } catch (err) {
    alert("Error updating memory: " + err.message);
  }
}

async function deleteMemory(id) {
  if (!confirm("Are you sure you want to retire this memory? It will be marked inactive.")) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/memories/${id}`, {
      method: "DELETE"
    });
    if (res.ok) await loadMemories();
  } catch (err) {
    alert("Error deleting memory: " + err.message);
  }
}

// Profile & Goals
function renderProfileData() {
  const idList = document.getElementById("profile-identity-list");
  const goalsList = document.getElementById("profile-goals-list");
  const projList = document.getElementById("profile-projects-list");

  if (!idList || !goalsList || !projList) return;

  const identities = allMemories.filter(m => m.category === "IDENTITY" && m.is_current);
  const goals = allMemories.filter(m => m.category === "GOAL_CAREER" && m.is_current);
  const projects = allMemories.filter(m => m.category === "PROJECT" && m.is_current);

  idList.innerHTML = identities.length ? identities.map(m => `
    <div class="p-2.5 rounded-lg bg-dark-900 border border-dark-700/80 text-xs">
      ${escapeHtml(m.content)}
    </div>
  `).join("") : `<p class="text-xs text-slate-500 italic">No identity memories stored yet.</p>`;

  goalsList.innerHTML = goals.length ? goals.map(m => `
    <div class="p-2.5 rounded-lg bg-dark-900 border border-dark-700/80 text-xs flex items-center justify-between">
      <span>${escapeHtml(m.content)}</span>
      <span class="text-[10px] text-amber-400 font-mono">ACTIVE</span>
    </div>
  `).join("") : `<p class="text-xs text-slate-500 italic">No career goals stored yet.</p>`;

  projList.innerHTML = projects.length ? projects.map(m => `
    <div class="p-2.5 rounded-lg bg-dark-900 border border-dark-700/80 text-xs flex items-center justify-between">
      <span>${escapeHtml(m.content)}</span>
      <span class="text-[10px] text-blue-400 font-mono">TRACKED</span>
    </div>
  `).join("") : `<p class="text-xs text-slate-500 italic">No projects recorded yet.</p>`;
}

// Audit Logs
async function loadAuditLogs() {
  const container = document.getElementById("audit-logs-container");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/audit/logs`);
    if (!res.ok) return;
    const logs = await res.json();

    if (logs.length === 0) {
      container.innerHTML = `<div class="text-xs text-slate-500 italic">No audit records yet.</div>`;
      return;
    }

    container.innerHTML = logs.map(l => `
      <div class="p-3.5 rounded-xl bg-dark-800 border border-dark-700 text-xs flex items-center justify-between">
        <div class="space-y-1">
          <div class="flex items-center space-x-2">
            <span class="font-mono font-bold text-brand-400 uppercase">${l.action}</span>
            <span class="text-slate-400 font-mono text-[11px]">${l.memory_id.slice(0, 8)}...</span>
          </div>
          <p class="text-slate-300">${escapeHtml(l.reason || "System event")}</p>
        </div>
        <span class="text-slate-500 font-mono text-[10px]">${new Date(l.timestamp).toLocaleTimeString()}</span>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

// Helper
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}
