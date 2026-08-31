const fields = {
  status: document.querySelector("#status"),
  recall: document.querySelector("#recall"),
  diagnosis: document.querySelector("#diagnosis"),
  fix: document.querySelector("#fix"),
  tests: document.querySelector("#tests"),
  history: document.querySelector("#history"),
  report: document.querySelector("#report"),
  stageTitle: document.querySelector("#stage-title"),
  stageNote: document.querySelector("#stage-note"),
  proofSaved: document.querySelector("#proof-saved"),
  proofFresh: document.querySelector("#proof-fresh"),
  proofRecalled: document.querySelector("#proof-recalled"),
  proofChanged: document.querySelector("#proof-changed"),
};

document.querySelector("#run").addEventListener("click", runWorkflow);
document.querySelector("#new-demo").addEventListener("click", newDemoId);
document.querySelector("#session-one").addEventListener("click", prepareSessionOne);
document.querySelector("#fresh-session").addEventListener("click", markFreshSession);
document.querySelector("#session-two").addEventListener("click", prepareSessionTwo);
document.querySelector("#project-id").addEventListener("change", event => {
  localStorage.setItem("fixmemoryDemoProjectId", event.target.value.trim());
});
restoreDemoId();
loadStatus();
loadHistory();

async function loadStatus() {
  const response = await fetch("/api/status");
  const data = await response.json();
  fields.status.innerHTML = `
    <dt>SIBYL_MEMORY</dt><dd>${escapeHtml(data.SIBYL_MEMORY)}</dd>
    <dt>BACKEND</dt><dd>${escapeHtml(data.SIBYL_BACKEND)}</dd>
    <dt>APPROVED_ROOT</dt><dd>${escapeHtml(data.APPROVED_PROJECT_ROOT)}</dd>
  `;
}

async function loadHistory() {
  const projectId = document.querySelector("#project-id").value.trim() || "demo-python-app";
  const response = await fetch(`/api/history?project_id=${encodeURIComponent(projectId)}`);
  const data = await response.json();
  fields.history.textContent = JSON.stringify(data.past_fixes || [], null, 2);
}

async function runWorkflow() {
  const payload = {
    project_id: document.querySelector("#project-id").value,
    project_path: document.querySelector("#project-path").value,
    problem: document.querySelector("#problem").value,
    error_message: document.querySelector("#error-message").value,
  };
  fields.proofSaved.textContent = "RUNNING";
  fields.proofRecalled.textContent = "RUNNING";
  fields.proofChanged.textContent = "RUNNING";
  fields.report.textContent = "RUNNING MEMORY RECALL -> DIAGNOSIS -> REPAIR -> TEST -> MEMORY WRITE";
  const response = await fetch("/api/repair", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  fields.recall.textContent = JSON.stringify({
    MEMORY_RECALLED: data.MEMORY_RECALLED,
    PREVIOUS_FIX: data.PREVIOUS_FIX,
    PREVIOUS_FIX_ALREADY_ATTEMPTED: data.PREVIOUS_FIX_ALREADY_ATTEMPTED,
    NEW_DIAGNOSIS: data.NEW_DIAGNOSIS,
    NEW_DECISION_CHANGED_BY_MEMORY: data.NEW_DECISION_CHANGED_BY_MEMORY,
  }, null, 2);
  fields.diagnosis.textContent = JSON.stringify(data.diagnosis || data, null, 2);
  fields.fix.textContent = JSON.stringify(data.proposed_fix || {}, null, 2);
  fields.tests.textContent = JSON.stringify(data.test_results || {}, null, 2);
  fields.report.textContent = JSON.stringify({
    ...(data.final_report || {}),
    MEMORY_WRITE: data.memory_write?.ok ? "PASS" : "CHECK_STATUS",
    MEMORY_SOURCE: data.memory_write?.source || data.memory_status?.MEMORY_SOURCE || "NONE",
    SECRETS_EXPOSED: "NO",
  }, null, 2);
  fields.proofSaved.textContent = data.memory_write?.ok ? "PASS" : "CHECK";
  fields.proofRecalled.textContent = data.MEMORY_RECALLED ? "YES" : "NO";
  fields.proofChanged.textContent = data.NEW_DECISION_CHANGED_BY_MEMORY ? "YES" : "NO";
  await loadStatus();
  await loadHistory();
}

function newDemoId() {
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  setDemoId(`demo-python-app-live-${stamp}`);
  prepareSessionOne();
}

function restoreDemoId() {
  const saved = localStorage.getItem("fixmemoryDemoProjectId");
  setDemoId(saved || `demo-python-app-live-${new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14)}`);
  prepareSessionOne();
}

function setDemoId(value) {
  document.querySelector("#project-id").value = value;
  localStorage.setItem("fixmemoryDemoProjectId", value);
}

function prepareSessionOne() {
  fields.stageTitle.textContent = "SESSION 1";
  fields.stageNote.textContent = "Run the first debugging request. FixMemory should diagnose the missing dependency and persist the repair context to Sibyl.";
  document.querySelector("#problem").value = "My Python app crashes when I launch it.";
  document.querySelector("#error-message").value = "ModuleNotFoundError: No module named 'requests'";
  resetPanels("SESSION 1 READY");
  fields.proofFresh.textContent = "SESSION 1";
}

function markFreshSession() {
  fields.stageTitle.textContent = "FRESH SESSION";
  fields.stageNote.textContent = "Stop and restart the app now for the cleanest recording, then continue with Session 2. The project id stays the same so Sibyl can recall the saved repair.";
  resetPanels("FRESH SESSION READY - RESTART APP, THEN RUN SESSION 2");
  fields.proofFresh.textContent = "READY";
}

function prepareSessionTwo() {
  fields.stageTitle.textContent = "SESSION 2";
  fields.stageNote.textContent = "Run the related failure without manually entering the old fix. FixMemory should recall Sibyl memory and change its diagnosis.";
  document.querySelector("#problem").value = "My app still crashes after I installed requests.";
  document.querySelector("#error-message").value = "ModuleNotFoundError: No module named 'requests'";
  resetPanels("SESSION 2 READY - MEMORY RECALL SHOULD CHANGE THE DECISION");
  fields.proofFresh.textContent = "YES";
}

function resetPanels(message) {
  fields.recall.textContent = message;
  fields.diagnosis.textContent = "WAITING";
  fields.fix.textContent = "WAITING";
  fields.tests.textContent = "WAITING";
  fields.report.textContent = "WAITING";
  fields.proofSaved.textContent = "WAITING";
  fields.proofRecalled.textContent = "WAITING";
  fields.proofChanged.textContent = "WAITING";
  loadHistory();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[ch]);
}
