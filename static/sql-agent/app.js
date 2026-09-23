const API_BASE = window.__APP_CONFIG__?.apiBase || "";
const SESSION_KEY = "sql_agent_session_id";

const sessionModeSelect = document.getElementById("sessionMode");
const secretKeyWrap = document.getElementById("secretKeyWrap");
const secretKeyInput = document.getElementById("secretKeyInput");
const sessionBtn = document.getElementById("sessionBtn");
const sessionListSelect = document.getElementById("sessionListSelect");
const sessionIdInput = document.getElementById("sessionId");
const schemaSelect = document.getElementById("schemaSelect");
const tableSelect = document.getElementById("tableSelect");
const queryInput = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");
const chatBox = document.getElementById("chatBox");
const adminSessionPanel = document.getElementById("adminSessionPanel");


/* ============================================================
   Session
   ============================================================ */

function getStoredSessionId() {
    return localStorage.getItem(SESSION_KEY);
}

function setStoredSessionId(sessionId) {
    if (sessionId) {
        localStorage.setItem(SESSION_KEY, sessionId);
    }
}

function clearStoredSessionId() {
    localStorage.removeItem(SESSION_KEY);
}

function updateSessionModeUI() {
    const mode = sessionModeSelect.value;

    if (mode === "admin") {
        secretKeyWrap.style.display = "block";
    } else {
        secretKeyWrap.style.display = "none";
        secretKeyInput.value = "";
    }
}

async function startSession() {
    const mode = sessionModeSelect.value;

    const payload = {
        mode,
    };

    if (mode === "admin") {
        const secretKey = secretKeyInput.value.trim();

        if (!secretKey) {
            addAssistantError("Admin secret key is required.");
            return;
        }

        payload.secret_key = secretKey;
    }

    sessionBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/session`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data?.detail || "Failed to start session.");
        }

        const sessionId = data.session_id;

        setStoredSessionId(sessionId);
        sessionIdInput.value = sessionId;

        if (mode === "admin") {
            adminSessionPanel.style.display = "block";
            await loadActiveSessions();
        } else {
            adminSessionPanel.style.display = "none";
        }
    } catch (error) {
        addAssistantError(error.message || "Failed to start session.");
    } finally {
        sessionBtn.disabled = false;
    }
}

function restoreSession() {
    const sessionId = getStoredSessionId();

    if (sessionId) {
        sessionIdInput.value = sessionId;
    }
}


/* ============================================================
   Schema / Table
   ============================================================ */

async function loadSchemas() {
    schemaSelect.innerHTML = `
        <option value="">Loading schemas...</option>
    `;

    try {
        const response = await fetch(`${API_BASE}/api/get_schemas`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data?.detail || "Failed to load schemas.");
        }

        schemaSelect.innerHTML = `
            <option value="">Select schema</option>
        `;

        for (const schema of data) {
            const option = document.createElement("option");
            option.value = schema;
            option.textContent = schema;
            schemaSelect.appendChild(option);
        }
    } catch (error) {
        schemaSelect.innerHTML = `
            <option value="">Failed to load schemas</option>
        `;

        addAssistantError(error.message || "Failed to load schemas.");
    }
}

async function loadTables(schemaName) {
    if (!schemaName) {
        tableSelect.innerHTML = `
            <option value="">Select table</option>
        `;
        return;
    }

    tableSelect.innerHTML = `
        <option value="">Loading tables...</option>
    `;

    try {
        const response = await fetch(
            `${API_BASE}/api/get_table?schema=${encodeURIComponent(schemaName)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data?.detail || "Failed to load tables.");
        }

        tableSelect.innerHTML = `
            <option value="">Select table</option>
        `;

        for (const table of data) {
            const option = document.createElement("option");
            option.value = table;
            option.textContent = table;
            tableSelect.appendChild(option);
        }
    } catch (error) {
        tableSelect.innerHTML = `
            <option value="">Failed to load tables</option>
        `;

        addAssistantError(error.message || "Failed to load tables.");
    }
}

/* ============================================================
   Admin Sessions
   ============================================================ */

async function loadActiveSessions() {
    try {
        const response = await fetch(`${API_BASE}/api/sessions`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data?.detail || "Failed to load sessions.");
        }

        const sessions = data.sessions || [];

        if (!sessions.length) {
            sessionListSelect.style.display = "none";
            return;
        }

        sessionListSelect.innerHTML = `
            <option value="">Select session</option>
        `;

        for (const session of sessions) {
            const option = document.createElement("option");

            const sessionId = session.session_id || session.id;

            option.value = sessionId;
            option.textContent =
                session.user_id
                    ? `${session.user_id} — ${shortRunId(sessionId)}`
                    : shortRunId(sessionId);

            sessionListSelect.appendChild(option);
        }

        sessionListSelect.style.display = "block";
    } catch (error) {
        sessionListSelect.style.display = "none";
    }
}


/* ============================================================
   Chat Rendering
   ============================================================ */

function addUserMessage(text) {
    const message = document.createElement("div");
    message.className = "message user";

    message.innerHTML = `
        <div class="message-content">
            ${escapeHtml(text)}
        </div>
    `;

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addAssistantError(text) {
    const message = document.createElement("div");
    message.className = "message message-assistant";

    message.innerHTML = `
        <div class="agent-response failed">
            ${escapeHtml(text)}
        </div>
    `;

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}


/* ============================================================
   Query Submission
   ============================================================ */

async function submitQuery() {
    const userInput = queryInput.value.trim();

    if (!userInput) {
        return;
    }

    const sessionId = sessionIdInput.value.trim();
    const schemaName = schemaSelect.value;
    const tableName = tableSelect.value;

    if (!sessionId) {
        addAssistantError("Start a session before sending a query.");
        return;
    }

    if (!schemaName) {
        addAssistantError("Select a schema first.");
        return;
    }

    if (!tableName) {
        addAssistantError("Select a table first.");
        return;
    }

    addUserMessage(userInput);

    queryInput.value = "";
    queryInput.disabled = true;
    sendBtn.disabled = true;

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
            throw new Error(data?.detail || "Request failed.");
        }
        console.log("AGENT RESPONSE:", data);
        renderAgentRun(data);
    } catch (error) {
        addAssistantError(error.message || "Request failed.");
    } finally {
        queryInput.disabled = false;
        sendBtn.disabled = false;
        queryInput.focus();
    }
}


/* ============================================================
   Agent Run Rendering
   ============================================================ */
function renderAgentRun(run) {
    const message = document.createElement("div");
    message.className = "message message-assistant";

    const responseHtml =
        Array.isArray(run.result_rows)
            ? `
                <div class="agent-response">
                    ${escapeHtml(JSON.stringify(run.result_rows))}
                </div>
            `
            : `
                <div class="agent-response failed">
                    ${escapeHtml(getRunFailureMessage(run))}
                </div>
            `;

    message.innerHTML = `
        ${buildRunTrace(run)}
        ${responseHtml}
    `;

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function buildRunTrace(run) {
    const runStatusClass =
        run.run_status === "success"
            ? "success"
            : "failed";

    const attempts = Array.isArray(run.attempts)
        ? run.attempts
        : [];

    let repairNumber = 0;

    const attemptHtml = attempts
        .map((attempt, index) => {
            if (attempt.source === "repair") {
                repairNumber++;
            }

            return buildAttempt(
                attempt,
                index,
                attempt.source === "repair"
                    ? repairNumber
                    : null
            );
        })
        .join("");

    return `
        <details class="run-trace">
            <summary>
                <span class="trace-label">RUN</span>

                <span class="trace-run-id">
                    ${escapeHtml(shortRunId(run.run_id))}
                </span>

                <span class="trace-status ${runStatusClass}">
                    ${escapeHtml(formatStatus(run.run_status))}
                </span>
            </summary>

            <div class="trace-body">
                ${attemptHtml}
            </div>
        </details>
    `;
}

function buildAttempt(attempt, index, repairNumber) {
    const title = attempt.source === "repair"
        ? `SQL Repair #${repairNumber}`
        : "SQL Generation";

    const statusClass =
        attempt.status === "success"
            ? "success"
            : "failed";

    const stages = buildAttemptStages(attempt);

    return `
        <details class="attempt">
            <summary>
                <span class="attempt-number">
                    #${index + 1}
                </span>

                <span class="attempt-source">
                    ${escapeHtml(title)}
                </span>

                <span class="attempt-status ${statusClass}">
                    ${escapeHtml(formatStatus(attempt.status))}
                </span>
            </summary>

            <div class="attempt-body">
                <div class="attempt-stages">
                    ${stages.map(buildStage).join("")}
                </div>

                <div class="attempt-detail">
                    <div class="detail-label">SQL</div>

                    <pre class="sql-block">${escapeHtml(
                        attempt.sql || ""
                    )}</pre>
                </div>

                ${
                    attempt.error
                        ? `
                            <div class="attempt-detail">
                                <div class="detail-label">Error</div>

                                <pre class="error-block">${escapeHtml(
                                    attempt.error
                                )}</pre>
                            </div>
                        `
                        : ""
                }
            </div>
        </details>
    `;
}

function buildAttemptStages(attempt) {
    const stages = [];

    /*
     * Generation / Repair
     *
     * If the attempt exists, generation or repair itself succeeded
     * enough to produce SQL that entered the SQL pipeline.
     */
    stages.push({
        name:
            attempt.source === "repair"
                ? "SQL Repair"
                : "SQL Generation",
        status: "success",
    });

    /*
     * Parsing
     */
    if (attempt.status === "parse_failed") {
        stages.push({
            name: "SQL Parsing",
            status: "failed",
        });

        return stages;
    }

    stages.push({
        name: "SQL Parsing",
        status: "success",
    });

    /*
     * Validation
     */
    if (attempt.status === "validation_failed") {
        stages.push({
            name: "SQL Validation",
            status: "failed",
        });

        return stages;
    }

    stages.push({
        name: "SQL Validation",
        status: "success",
    });

    /*
     * Query Policy
     */
    if (attempt.status === "policy_failed") {
        stages.push({
            name: "Query Policy",
            status: "failed",
        });

        return stages;
    }

    stages.push({
        name: "Query Policy",
        status: "success",
    });

    /*
     * Execution
     */
    if (attempt.status === "execution_failed") {
        stages.push({
            name: "SQL Execution",
            status: "failed",
        });

        return stages;
    }

    if (attempt.status === "success") {
        stages.push({
            name: "SQL Execution",
            status: "success",
        });
    }

    return stages;
}

function buildStage(stage) {
    const icon =
        stage.status === "success"
            ? "✓"
            : "✕";

    return `
        <div class="stage ${stage.status}">
            <span class="stage-icon">
                ${icon}
            </span>

            <span class="stage-name">
                ${escapeHtml(stage.name)}
            </span>
        </div>
    `;
}


/* ============================================================
   Run Status / Formatting
   ============================================================ */

function getRunFailureMessage(run) {
    switch (run.run_status) {
        case "out_of_scope":
            return "Request is outside the supported scope.";

        case "retry_exhausted":
            return "SQL generation failed after the available repair attempts.";

        case "failed":
            return "SQL Agent failed to complete the request.";

        default:
            return "SQL Agent did not return a response.";
    }
}

function formatStatus(status) {
    return String(status ?? "")
        .replaceAll("_", " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}

function shortRunId(runId) {
    if (!runId) {
        return "";
    }

    return runId.length > 12
        ? `${runId.slice(0, 8)}...`
        : runId;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ============================================================
   Event Listeners
   ============================================================ */

sessionModeSelect.addEventListener(
    "change",
    updateSessionModeUI
);

sessionBtn.addEventListener(
    "click",
    startSession
);

schemaSelect.addEventListener(
    "change",
    async () => {
        await loadTables(schemaSelect.value);
    }
);

sessionListSelect.addEventListener(
    "change",
    () => {
        const sessionId = sessionListSelect.value;

        if (!sessionId) {
            return;
        }

        sessionIdInput.value = sessionId;
        setStoredSessionId(sessionId);
    }
);

sendBtn.addEventListener(
    "click",
    submitQuery
);

queryInput.addEventListener(
    "keydown",
    event => {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();
            submitQuery();
        }
    }
);


/* ============================================================
   Initialization
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async () => {
        updateSessionModeUI();
        restoreSession();

        await loadSchemas();

        const sessionId = getStoredSessionId();

        if (sessionId) {
            sessionIdInput.value = sessionId;
        }
    }
);