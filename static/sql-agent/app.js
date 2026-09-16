const API_BASE = window.__APP_CONFIG__?.apiBase || "";

const sessionIdInput = document.getElementById("sessionId");
const schemaSelect = document.getElementById("schemaSelect");
const tableSelect = document.getElementById("tableSelect");
const queryInput = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");
const chatBox = document.getElementById("chatBox");

function setDefaultTable() {
  const defaultTable = "air_traffic_passenger_statistics_20260718";
  tableSelect.innerHTML = "";

  const option = document.createElement("option");
  option.value = defaultTable;
  option.textContent = defaultTable;
  tableSelect.appendChild(option);
  tableSelect.value = defaultTable;
}

function addUserMessage(text) {
  const message = document.createElement("div");
  message.className = "message user";
  message.innerHTML = `
    <div class="meta">You</div>
    <div>${escapeHtml(text)}</div>
  `;
  chatBox.appendChild(message);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function addAssistantResult(result, promptText) {
  const message = document.createElement("div");
  message.className = "message assistant";

  const status = result?.status || "unknown";
  const sql = result?.sql || "";
  const rows = Array.isArray(result?.rows) ? result.rows : [];
  const error = result?.execution_error || result?.validation_errors?.[0] || "";

  const showSql = sql ? `<button class="sql-toggle" type="button">View SQL</button><div class="sql-box" style="display:none">${escapeHtml(sql)}</div>` : "";

  const errorBox = error ? `<div class="error-box">${escapeHtml(error)}</div>` : "";

  const tableMarkup = rows.length
    ? `
      <div class="table-wrap">
        <table class="result-table">
          <thead>
            <tr>
              ${Object.keys(rows[0]).map((key) => `<th>${escapeHtml(key)}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                ${Object.keys(row).map((key) => `<td>${escapeHtml(String(row[key] ?? ""))}</td>`).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `
    : "<div class=\"empty-state\">No rows returned.</div>";

  message.innerHTML = `
    <div class="meta">Assistant</div>
    <div><strong>Status:</strong> ${escapeHtml(status)}</div>
    <div class="result-card">
      <div class="header">Result</div>
      <div class="body">
        ${status === "success" ? tableMarkup : ""}
        ${errorBox}
        ${showSql}
      </div>
    </div>
  `;

  const sqlToggle = message.querySelector(".sql-toggle");
  const sqlBox = message.querySelector(".sql-box");

  if (sqlToggle && sqlBox) {
    sqlToggle.addEventListener("click", () => {
      const isVisible = sqlBox.style.display !== "none";
      sqlBox.style.display = isVisible ? "none" : "block";
      sqlToggle.textContent = isVisible ? "View SQL" : "Hide SQL";
    });
  }

  chatBox.appendChild(message);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function submitQuery() {
  const sessionId = sessionIdInput.value.trim();
  const schemaName = schemaSelect.value;
  const tableName = tableSelect.value;
  const userInput = queryInput.value.trim();

  if (!sessionId || !tableName || !userInput) {
    alert("Please provide a session ID, select a table, and enter a question.");
    return;
  }

  addUserMessage(userInput);
  queryInput.value = "";

  try {
    const response = await fetch(`${API_BASE}/api/query_agent`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        schema_name: schemaName,
        table_name: tableName,
        user_input: userInput,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data?.detail || "Request failed");
    }

    addAssistantResult(data, userInput);
  } catch (error) {
    const message = document.createElement("div");
    message.className = "message assistant";
    message.innerHTML = `
      <div class="meta">Assistant</div>
      <div class="error-box">${escapeHtml(error.message || "Unknown error")}</div>
    `;
    chatBox.appendChild(message);
  }

  chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.addEventListener("click", submitQuery);
queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitQuery();
  }
});

window.addEventListener("DOMContentLoaded", setDefaultTable);
